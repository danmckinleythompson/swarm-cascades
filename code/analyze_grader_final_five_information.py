from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import csv
import gzip
import json
import random
from collections import defaultdict

from _metrics import wilson

# Compare the information-planning instruction with completed pay-only runs.
# This script is offline: it never imports the API client or runs model calls.
FINAL_FIVE_PAY = (
    "Your pay depends on the share of the final five workers in this 30-worker "
    "shift whose submissions are ACCEPTED."
)
INFORMATION_INSTRUCTION = (
    "Before writing your board post, think about what information the final five "
    "workers will need to make a good decision and how your message can help "
    "ensure they have it."
)
N_RUNS, N_AGENTS = 40, 30
BOOTSTRAP_DRAWS, BOOTSTRAP_SEED = 20000, 20260930
conditions = ("final_five_pay", "final_five_information")
new_plain = ROOT / "original_data/grader_final_five_information.jsonl"
new_gzip = new_plain.with_suffix(".jsonl.gz")
if not new_plain.exists() and not new_gzip.exists():
    raise SystemExit("New run data not found; collect all 40 runs before analysis.")

# Prefer the live plain log if both forms exist; never concatenate duplicate copies.
new_source = new_plain if new_plain.exists() else new_gzip
display_source = new_gzip if new_gzip.exists() else new_source
sources = (
    (conditions[0], ROOT / "original_data/grader_final_five_pay.jsonl.gz", range(40), "grader-final-five-pay-haiku"),
    (conditions[1], new_source, range(40), "grader-final-five-information-haiku"),
)
chains = defaultdict(dict)
timestamps = defaultdict(list)
for condition, source, expected_runs, expected_tag in sources:
    opener = gzip.open if source.suffix == ".gz" else open
    selected = 0
    with opener(source, "rt") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            eligible = (
                record.get("scenario") == "grader"
                and record.get("arm") == "baseline"
                and record.get("path") == "adverse"
                and record.get("model_key") == "haiku"
                and record.get("N") == N_AGENTS
            )
            if not eligible:
                raise ValueError(f"Unexpected {condition} record: {source}:{line_number}")
            assert record["run"] in expected_runs, (source, line_number, record["run"])
            assert record["tag"] == expected_tag, (source, line_number, record["tag"])
            assert record["spoke"] == condition
            key, position = (condition, record["run"]), record["position"]
            assert position not in chains[key], f"Duplicate decision: {key}, {position}"
            assert 0 <= position < N_AGENTS
            assert record["signal"] in {"output_only", "reads_transcript"}
            parsed = record["parsed"]
            assert set(parsed) == {"board_post", "interpretation", "confidence", "rationale"}
            assert parsed["interpretation"] in {"output_only", "reads_transcript"}
            assert type(parsed["confidence"]) is int and 0 <= parsed["confidence"] <= 100
            assert isinstance(parsed["board_post"], str) and isinstance(parsed["rationale"], str)
            assert record["is_skeptic"] is False and record["coordinator_summary"] is None
            assert isinstance(record["usage"]["cost"], (float, int))
            assert record["usage"]["cost"] >= 0
            chains[key][position] = record
            timestamps[condition].append(record["timestamp"])
            selected += 1
    expected_decisions = len(expected_runs) * N_AGENTS
    if selected != expected_decisions:
        raise SystemExit(
            f"Refusing incomplete analysis: {source.name} has {selected} eligible "
            f"decisions; expected {expected_decisions}. No outputs written."
        )

# Check every complete chain, matched private signal, and exact system-prompt edit.
expected_keys = {(condition, run) for condition in conditions for run in range(N_RUNS)}
assert set(chains) == expected_keys
for run in range(N_RUNS):
    for condition in conditions:
        assert set(chains[condition, run]) == set(range(N_AGENTS))
        assert all(chains[condition, run][p]["signal"] == "reads_transcript" for p in range(4))
    for position in range(N_AGENTS):
        old = chains[conditions[0], run][position]
        new = chains[conditions[1], run][position]
        assert old["signal"] == new["signal"], (run, position, "unmatched signal")
        assert old["system_prompt"].count(FINAL_FIVE_PAY) == 1
        assert INFORMATION_INSTRUCTION not in old["system_prompt"]
        assert new["system_prompt"] == old["system_prompt"].replace(
            FINAL_FIVE_PAY, FINAL_FIVE_PAY + " " + INFORMATION_INSTRUCTION)
        assert old["agent_id"] == new["agent_id"] == f"W{position:02d}"
        assert "SHARED WORKER BOARD" in old["user_prompt"] and "SHARED WORKER BOARD" in new["user_prompt"]
        assert old["user_prompt"].split("SHARED WORKER BOARD", 1)[0] == new["user_prompt"].split("SHARED WORKER BOARD", 1)[0]
        assert old["user_prompt"].rsplit("\n\nQUESTION:", 1)[1] == new["user_prompt"].rsplit("\n\nQUESTION:", 1)[1]

# Calculate outcomes once per swarm, using integer thresholds at the boundaries.
run_rows = []
for condition in conditions:
    for run in range(N_RUNS):
        records = [chains[condition, run][position] for position in range(N_AGENTS)]
        wrong = [r["parsed"]["interpretation"] == "reads_transcript" for r in records]
        true_probe = [r["signal"] == "output_only" for r in records]
        n_wrong = sum(wrong)
        n_tail_wrong = sum(wrong[-10:])
        n_true_probe = sum(true_probe)
        n_abandoned = sum(w and t for w, t in zip(wrong, true_probe))
        assert n_true_probe > 0, (condition, run, "undefined abandonment rate")
        row = {
            "condition": condition,
            "run": run,
            "n_agents": N_AGENTS,
            "n_wrong": n_wrong,
            "n_wrong_last10": n_tail_wrong,
            "n_wrong_last5": sum(wrong[-5:]),
            "false_consensus": int(n_tail_wrong >= 8),
            "correct_consensus": int(n_tail_wrong <= 2),
            "mixed_consensus": int(3 <= n_tail_wrong <= 7),
            "all30_false_share": n_wrong / N_AGENTS,
            "last5_false_share": sum(wrong[-5:]) / 5,
            "n_true_probe": n_true_probe,
            "n_true_probe_abandoned": n_abandoned,
            "true_probe_abandonment": n_abandoned / n_true_probe,
            "group_decision_wrong": int(n_wrong >= 20),
            "group_decision_correct": int(n_wrong <= 10),
            "group_decision_none": int(11 <= n_wrong <= 19),
            "cost_usd": sum(r["usage"]["cost"] for r in records),
            "input_tokens": sum(r["usage"]["in"] for r in records),
            "output_tokens": sum(r["usage"]["out"] for r in records),
        }
        assert row["false_consensus"] + row["correct_consensus"] + row["mixed_consensus"] == 1
        assert row["group_decision_wrong"] + row["group_decision_correct"] + row["group_decision_none"] == 1
        run_rows.append(row)

# Weight swarms equally, including the secondary private-signal abandonment rate.
metrics = (
    "false_consensus", "correct_consensus", "mixed_consensus",
    "all30_false_share", "last5_false_share", "true_probe_abandonment",
    "group_decision_wrong", "group_decision_correct", "group_decision_none",
)
summary_rows = []
by_condition = {}
for condition in conditions:
    rows = [row for row in run_rows if row["condition"] == condition]
    by_condition[condition] = rows
    summary = {"condition": condition, "n_runs": len(rows), "n_decisions": len(rows) * N_AGENTS}
    summary.update({metric: sum(row[metric] for row in rows) / len(rows) for metric in metrics})
    false_count = sum(row["false_consensus"] for row in rows)
    low, high = wilson(false_count, len(rows))
    summary.update({
        "n_false_consensus": false_count,
        "primary_ci_low": low,
        "primary_ci_high": high,
        "primary_ci_method": "95% Wilson score",
        "total_cost_usd": sum(row["cost_usd"] for row in rows),
        "mean_cost_per_run_usd": sum(row["cost_usd"] for row in rows) / len(rows),
        "first_record_timestamp": min(timestamps[condition]),
        "last_record_timestamp": max(timestamps[condition]),
    })
    summary_rows.append(summary)

# Resample 40 matched run pairs, not 2,400 individual agent decisions.
old_rows, new_rows = (by_condition[condition] for condition in conditions)
paired_differences = [new["false_consensus"] - old["false_consensus"] for old, new in zip(old_rows, new_rows)]
rng = random.Random(BOOTSTRAP_SEED)
bootstrap_differences = sorted(
    sum(rng.choices(paired_differences, k=N_RUNS)) / N_RUNS
    for _ in range(BOOTSTRAP_DRAWS)
)
diff_low = bootstrap_differences[int(0.025 * BOOTSTRAP_DRAWS)]
diff_high = bootstrap_differences[int(0.975 * BOOTSTRAP_DRAWS)]
comparison = {key: "" for key in summary_rows[0]}
comparison.update({
    "condition": "final_five_information_minus_pay",
    "n_runs": N_RUNS,
    **{metric: summary_rows[1][metric] - summary_rows[0][metric] for metric in metrics},
    "primary_ci_low": diff_low,
    "primary_ci_high": diff_high,
    "primary_ci_method": f"95% paired run bootstrap percentile; {BOOTSTRAP_DRAWS} draws; seed {BOOTSTRAP_SEED}",
})
summary_rows.append(comparison)

# Write only after the complete sample and all matching checks have passed.
run_output = ROOT / "modified_data/grader_final_five_information_runs.csv"
summary_output = ROOT / "modified_data/grader_final_five_information_summary.csv"
note_output = ROOT / "notes/results-grader-final-five-information-2026-09-30.md"
for target, rows in ((run_output, run_rows), (summary_output, summary_rows)):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

old_summary, new_summary = summary_rows[:2]
outcome_table = [
    "| Outcome | Final-five pay only | Final-five pay + information planning |",
    "|---|---:|---:|",
]
for metric, label in (
    ("false_consensus", "False consensus: at least 8 of the final 10 wrong"),
    ("correct_consensus", "Correct consensus: at least 8 of the final 10 correct"),
    ("mixed_consensus", "Mixed final 10"),
    ("all30_false_share", "Mean false-belief share across all 30 agents"),
    ("last5_false_share", "Mean false-belief share among final 5 agents"),
    ("true_probe_abandonment", "Mean within-swarm share of truth-pointing probes followed by a false belief"),
    ("group_decision_wrong", "Wrong group decision: at least 20 of all 30 wrong"),
    ("group_decision_correct", "Correct group decision: at least 20 of all 30 correct"),
    ("group_decision_none", "No group decision under the 20-of-30 rule"),
):
    outcome_table.append(f"| {label} | {old_summary[metric]:.1%} | {new_summary[metric]:.1%} |")
table = "\n".join(outcome_table)
new_only_false = sum(new["false_consensus"] and not old["false_consensus"] for old, new in zip(old_rows, new_rows))
old_only_false = sum(old["false_consensus"] and not new["false_consensus"] for old, new in zip(old_rows, new_rows))
note = f"""# Grader final-five pay plus information planning

Generated by [the offline analysis script](../code/analyze_grader_final_five_information.py). The treatment consists of {N_RUNS} new swarms of {N_AGENTS} Claude Haiku 4.5 workers, using the original grader scenario, free-form board, and adverse start (the first four private probes point to the false interpretation). The correct interpretation is `output_only`; the false interpretation is `reads_transcript`.

## Prompt change

Both conditions use the same pay sentence:

> {FINAL_FIVE_PAY}

The new condition adds this sentence immediately afterward:

> {INFORMATION_INSTRUCTION}

All 30 workers receive the added sentence; the final five are W25–W29 (positions 26–30). The instruction asks agents to plan what information to convey but adds no planning response field or requirement to quote their private probe. This is the only system-prompt change. The documentation, private-probe text, and board rule are unchanged. The supplied private probes match the historical runs exactly at every position, including the four misleading initial probes. Subsequent public messages are endogenous and can differ between conditions.

The experiment adds an information-planning instruction while holding the stated incentive fixed. Probe acceptance outcomes are preset; agents' beliefs or posts do not determine submission acceptance or an actual payout. The final-five false-belief share below measures beliefs, not the fraction of submissions accepted.

## Results

{table}

The primary outcome is false consensus among the final ten workers. It occurs in **{int(old_summary['n_false_consensus'])}/{N_RUNS} pay-only swarms ({old_summary['false_consensus']:.1%})** and **{int(new_summary['n_false_consensus'])}/{N_RUNS} pay-plus-information swarms ({new_summary['false_consensus']:.1%})**. The respective 95% Wilson intervals are **{old_summary['primary_ci_low']:.1%}–{old_summary['primary_ci_high']:.1%}** and **{new_summary['primary_ci_low']:.1%}–{new_summary['primary_ci_high']:.1%}**.

The information-planning-minus-pay-only difference is **{100 * comparison['false_consensus']:+.1f} percentage points**, with a **95% paired run bootstrap interval of [{100 * diff_low:+.1f}, {100 * diff_high:+.1f}] percentage points**. There are {old_only_false} matched paths with false consensus only under the pay-only prompt and {new_only_false} with false consensus only under the new prompt. The bootstrap resamples {N_RUNS} complete run pairs, uses {BOOTSTRAP_DRAWS:,} draws, and fixes the random seed at {BOOTSTRAP_SEED}; it does not treat agents within a swarm as independent observations.

All means weight swarms equally. In particular, true-probe abandonment first divides each swarm's number of wrong beliefs following an `output_only` private signal by that swarm's total number of `output_only` private signals, then averages those {N_RUNS} rates. Reporting that an individual agent contradicts a truth-pointing signal does not establish irrationality: agents also see prior public messages.

## Interpretation and cost

This is a **historical, noncontemporaneous comparison**, not a randomized comparison collected at the same time. Matching the private signal paths improves comparability but cannot separate the added instruction from changes in the model, provider, or collection date. The recorded timestamps span {old_summary['first_record_timestamp']} to {old_summary['last_record_timestamp']} for the pay-only condition and {new_summary['first_record_timestamp']} to {new_summary['last_record_timestamp']} for the treatment; the logs do not specify a timezone.

The new {N_RUNS} runs have **${new_summary['total_cost_usd']:.4f} in logged API costs** (${new_summary['mean_cost_per_run_usd']:.4f} per swarm). The completed pay-only comparison has ${old_summary['total_cost_usd']:.4f} in logged costs; those are existing runs, not new charges. Logged record costs may omit failed requests or retries that produced no saved decision.

## Files and reproduction

- New raw decisions: [{display_source.name}](<../original_data/{display_source.name}>).
- Completed pay-only comparison: [grader_final_five_pay.jsonl.gz](<../original_data/grader_final_five_pay.jsonl.gz>).
- [Exact prompts and matched design](grader-final-five-information-prompts-side-by-side.md).
- [Run-level results](<../modified_data/grader_final_five_information_runs.csv>) and [condition means, uncertainty, and costs](<../modified_data/grader_final_five_information_summary.csv>).
- Rebuild offline with `python3 code/analyze_grader_final_five_information.py` from the project root. The script prefers the treatment's plain JSONL when present, otherwise its gzip copy; it never combines the two. It refuses incomplete or duplicate samples and verifies all {N_RUNS * N_AGENTS:,} paired private signals and the exact added system-prompt sentence before writing outputs.
"""
note_output.parent.mkdir(parents=True, exist_ok=True)
note_output.write_text(note)
print(f"Validated {N_RUNS} complete matched pairs ({2 * N_RUNS * N_AGENTS} decisions).")
print(f"False consensus: pay only {int(old_summary['n_false_consensus'])}/{N_RUNS}; pay + information {int(new_summary['n_false_consensus'])}/{N_RUNS}.")
print(f"Difference: {100 * comparison['false_consensus']:+.1f} pp; paired bootstrap 95% CI [{100 * diff_low:+.1f}, {100 * diff_high:+.1f}] pp.")
print(f"New logged cost: ${new_summary['total_cost_usd']:.4f}.")
for target in (run_output, summary_output, note_output):
    print(target.relative_to(ROOT))
