"""Governance arms: prompt construction and schemas.

Each arm is a function of (scenario, signal_value, posts, position, N, coordinator
summary) -> (user_prompt, schema, system_extra). Posts are the public record other
agents see; the private committed belief is never shown to successors.

Board post + private commitment are elicited together via structured output.
"""

from scenarios import Scenario, belief_enum, outcome_order

SKEPTIC_EVERY = 3


def base_schema(sc: Scenario) -> dict:
    return {
        "type": "object",
        "properties": {
            "board_post": {"type": "string",
                           "description": "Message posted to the shared worker board (2-4 sentences)."},
            "interpretation": {"type": "string", "enum": belief_enum(sc)},
            "confidence": {"type": "integer", "description": "0-100 confidence in your interpretation"},
            "rationale": {"type": "string", "description": "1-3 sentences"},
        },
        "required": ["board_post", "interpretation", "confidence", "rationale"],
        "additionalProperties": False,
    }


def provenance_schema(sc: Scenario) -> dict:
    s = base_schema(sc)
    s["properties"]["post_claim"] = {"type": "string", "enum": belief_enum(sc) + ["unsure"],
                                     "description": "The claim your post asserts."}
    s["properties"]["post_basis"] = {"type": "string", "enum": ["verified", "cites"],
                                     "description": "verified = grounded in your OWN probe; "
                                                    "cites = based on other workers' reports."}
    s["required"] += ["post_claim", "post_basis"]
    return s


def outcome_schema(sc: Scenario) -> dict:
    s = base_schema(sc)
    s["properties"]["reported_probe_outcome"] = {
        "type": "string", "enum": ["supports_" + v for v in outcome_order(sc)] + ["not_reporting"],
        "description": "Which interpretation YOUR OWN raw probe result supports (report it faithfully)."}
    s["required"].append("reported_probe_outcome")
    return s


def render_board(posts) -> str:
    if not posts:
        return "SHARED WORKER BOARD: (no posts yet — you are the first worker this shift)"
    lines = [f"[Worker {p['agent_id']}] {p['board_post']}" for p in posts]
    return "SHARED WORKER BOARD (earlier workers this shift):\n" + "\n".join(lines)


def render_provenance_board(sc, posts) -> str:
    base = render_board(posts)
    if not posts:
        return base
    tally = {c: {"verified": 0, "cites": 0} for c in belief_enum(sc)}
    for p in posts:
        c, b = p.get("post_claim"), p.get("post_basis")
        if c in tally and b in ("verified", "cites"):
            tally[c][b] += 1
    lines = ["", "BOARD TALLY (independent verifications vs citations):"]
    for c in belief_enum(sc):
        lines.append(f"  {c}: {tally[c]['verified']} independent verifications, "
                     f"{tally[c]['cites']} citations of others")
    lines.append("Note: a citation adds no new evidence beyond the post it cites.")
    return base + "\n" + "\n".join(lines)


def render_outcome_board(sc, posts) -> str:
    base = render_board(posts)
    if not posts:
        return base
    cnt = {"supports_" + v: 0 for v in outcome_order(sc)}
    for p in posts:
        o = p.get("reported_probe_outcome")
        if o in cnt:
            cnt[o] += 1
    lines = ["", "BOARD PROBE LEDGER (raw probe outcomes reported so far):"]
    for v in outcome_order(sc):
        lines.append(f"  probes supporting '{v}': {cnt['supports_' + v]}")
    lines.append("Each probe is ~70% reliable; the ledger is the aggregate raw evidence.")
    return base + "\n" + "\n".join(lines)


def _dominant_wrong(sc, posts, window=5):
    """True if the last `window` posts are unanimous (fast-forming consensus)."""
    recent = [p["interpretation"] for p in posts[-window:]]
    return len(recent) >= window and len(set(recent)) == 1


def build(arm: str, sc: Scenario, signal_value: str, posts, position: int, N: int,
          coordinator_summary):
    """Returns (user_prompt, schema, system_extra, is_skeptic_flag)."""
    parts = [sc.doc, sc.signal_text(signal_value)]
    schema = base_schema(sc)
    extra = ""
    skeptic = False

    if arm == "no_board":
        parts.append("There is no shared board this shift; work independently.")
    elif arm == "hierarchy":
        parts.append("COORDINATOR BRIEFING (summary of earlier workers' reports):\n"
                     + coordinator_summary if coordinator_summary
                     else "COORDINATOR BRIEFING: You are the first worker; no reports yet.")
    elif arm == "provenance_claims":
        parts.append(render_provenance_board(sc, posts))
        schema = provenance_schema(sc)
        extra = ("\nBoard policy: tag every post with the claim it asserts and whether "
                 "it is grounded in your OWN probe (verified) or others' reports (cites).")
    elif arm == "outcome_tallies":
        parts.append(render_outcome_board(sc, posts))
        schema = outcome_schema(sc)
        extra = ("\nBoard policy: report your OWN raw probe outcome faithfully; the board "
                 "aggregates raw probe outcomes into a shared evidence ledger.")
    elif arm == "verbatim_audit":
        parts.append(render_board(posts))
        extra = ("\nBoard policy: any empirical claim in your post MUST quote your own raw "
                 "probe result verbatim. Do not assert results you did not personally "
                 "observe, and do not invent counts or tests.")
    elif arm in ("baseline", "skeptic_quota", "skeptic_triggered"):
        parts.append(render_board(posts))
        if arm == "skeptic_quota":
            skeptic = position % SKEPTIC_EVERY == SKEPTIC_EVERY - 1
        elif arm == "skeptic_triggered":
            skeptic = _dominant_wrong(sc, posts)
        if skeptic:
            extra = ("\nYou are assigned the SKEPTIC role: before adopting the board's "
                     "dominant view, actively try to refute it. Ask what evidence would "
                     "distinguish the interpretations and whether the posts actually "
                     "provide it.")
    else:
        raise ValueError(f"unknown arm {arm}")

    parts.append(
        f"QUESTION: {sc.question}\n\n"
        "First write the message you will post to the shared board"
        + (" (relayed to the coordinator)" if arm == "hierarchy" else "")
        + ", then privately commit to an interpretation. Your committed interpretation "
          "is NOT shown to other workers; only your board post is public."
    )
    return "\n\n".join(parts), schema, extra, skeptic


SUMMARY_SCHEMA = {"type": "object",
                  "properties": {"summary": {"type": "string",
                                             "description": "3-5 sentence briefing for the next worker."}},
                  "required": ["summary"], "additionalProperties": False}
COORDINATOR_SYSTEM = ("You are the shift coordinator relaying the worker board to each "
                      "incoming worker. You have no probe results of your own.")
