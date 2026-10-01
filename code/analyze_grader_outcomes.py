from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import csv
import gzip
import json
from collections import defaultdict

# Retain collection waves as separate samples. In particular, the original
# five-run baseline is not added to the later 40-run baseline comparison.
FILES = (
    "grader_original.jsonl.gz",
    "grader_baseline_initial.jsonl.gz",
    "grader_baseline_expansion.jsonl.gz",
    "grader_final_five_pay.jsonl.gz",
    "grader_final_five_information.jsonl.gz",
    "grader_verbatim_expansion.jsonl.gz",
)
EXPECTED_RECORDS = (6480, 600, 1800, 1200, 1200, 1050)
MODELS = ("haiku", "sonnet", "gpt5mini", "gemini", "opus")
ARMS = ("no_board", "baseline", "verbatim_audit", "outcome_tallies",
        "skeptic_quota", "hierarchy", "skeptic_triggered", "provenance_claims")
LABELS = {
    "haiku": "Claude Haiku 4.5", "sonnet": "Claude Sonnet 4.6",
    "gpt5mini": "GPT-5 mini", "gemini": "Gemini 2.5 Flash", "opus": "Claude Opus 4.6",
    "no_board": "No board", "baseline": "Free-form board",
    "verbatim_audit": "Verbatim-quote audit", "outcome_tallies": "Outcome tallies",
    "skeptic_quota": "Skeptic quota", "hierarchy": "Coordinator digest",
    "skeptic_triggered": "Triggered skepticism", "provenance_claims": "Provenance tags",
    "final_five_pay": "Final-five pay", "final_five_information": "Final-five pay + information planning",
}
chains = defaultdict(dict)
sources = defaultdict(set)
for filename, expected in zip(FILES, EXPECTED_RECORDS):
    n_records = 0
    with gzip.open(ROOT / "original_data" / filename, "rt") as handle:
        for line in handle:
            record = json.loads(line)
            assert record["scenario"] == "grader" and record["N"] == 30
            assert record["signal"] in ("output_only", "reads_transcript")
            assert record["parsed"]["interpretation"] in ("output_only", "reads_transcript")
            key = tuple(record[field] for field in
                        ("spoke", "arm", "model_key", "path", "run", "tag", "N"))
            position = record["position"]
            assert position not in chains[key], (filename, key, position)
            chains[key][position] = record
            sources[key].add(filename)
            n_records += 1
    assert n_records == expected, (filename, n_records, expected)
assert len(chains) == 411

# Each cell contains complete independent runs; the audit's expanded cell
# intentionally reuses the original five audit runs plus 35 later runs.
cells = defaultdict(list)
for key, records in chains.items():
    assert set(records) == set(range(30)), key
    sequence = [records[position] for position in range(30)]
    first = sequence[0]
    if first["path"] == "adverse":
        assert all(record["signal"] == "reads_transcript" for record in sequence[:4])
    spoke, arm, model, path = key[:4]
    if spoke in ("gov", "model"):
        cells["original", arm, model, arm, path].append(key)
        if spoke == "gov" and arm == "verbatim_audit" and path == "adverse":
            cells["expanded", "verbatim_audit", model, arm, path].append(key)
    else:
        condition = arm if spoke in ("flip", "verbatim_expansion") else spoke
        cells["expanded", condition, model, arm, path].append(key)
assert len(cells) == 53
assert sum(len(keys) for cell, keys in cells.items() if cell[0] == "original") == 216

rows = []
for cell, keys in sorted(cells.items()):
    scope, condition, model, arm, path = cell
    expected = 40 if scope == "expanded" else 2 if model == "opus" else 5
    assert len(keys) == expected, (cell, len(keys), expected)
    n_wrong = n_last10_wrong = n_final5_wrong = 0
    n_false_consensus = n_correct_consensus = 0
    n_group_wrong = n_group_correct = 0
    dates, filenames = set(), set()
    for key in keys:
        sequence = [chains[key][position] for position in range(30)]
        wrong = [record["parsed"]["interpretation"] == "reads_transcript" for record in sequence]
        total_wrong, tail_wrong = sum(wrong), sum(wrong[-10:])
        n_wrong += total_wrong
        n_last10_wrong += tail_wrong
        n_final5_wrong += sum(wrong[-5:])
        n_false_consensus += tail_wrong >= 8
        n_correct_consensus += tail_wrong <= 2
        n_group_wrong += total_wrong >= 20
        n_group_correct += total_wrong <= 10
        dates.update(record["timestamp"][:10] for record in sequence)
        filenames.update(sources[key])
    n = len(keys)
    row = dict(scope=scope, condition=condition, model=model, arm=arm, path=path,
               n_agents=30, n_runs=n, n_decisions=30 * n,
               n_wrong_decisions=n_wrong, share_wrong_decisions=n_wrong / (30 * n),
               share_last10_wrong=n_last10_wrong / (10 * n),
               share_final5_wrong=n_final5_wrong / (5 * n),
               n_false_consensus=n_false_consensus, n_correct_consensus=n_correct_consensus,
               n_mixed_consensus=n - n_false_consensus - n_correct_consensus,
               p_false_consensus=n_false_consensus / n, p_correct_consensus=n_correct_consensus / n,
               p_mixed_consensus=(n - n_false_consensus - n_correct_consensus) / n,
               n_group_correct=n_group_correct, n_group_wrong=n_group_wrong,
               n_group_undecided=n - n_group_correct - n_group_wrong,
               p_group_correct=n_group_correct / n, p_group_wrong=n_group_wrong / n,
               p_group_undecided=(n - n_group_correct - n_group_wrong) / n,
               collection_dates=";".join(sorted(dates)), source_files=";".join(sorted(filenames)))
    rows.append(row)

output = ROOT / "modified_data/grader_outcomes.csv"
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
lookup = {(r["scope"], r["condition"], r["model"], r["path"]): r for r in rows}

# Make the scope and denominator visible alongside every displayed estimate.
lines = [
    "# Grader findings", "",
    "Generated from the saved worker records by `code/analyze_grader_outcomes.py`. "
    "All runs here use 30 agents and the original grader truth: **output only**. "
    "`reads_transcript` is the false interpretation. No flipped grader or other scenario is included.", "",
    "The complete [CSV](../modified_data/grader_outcomes.csv) has 48 original model/rule/path "
    "cells and five expanded comparison cells. It covers 411 distinct swarms and 12,330 "
    "decisions. Five original audit swarms also appear in the expanded audit cell; "
    "the two scopes are separate summaries and must not be added together.", "",
    "## Measures", "",
    "- **Wrong-agent share:** fraction of all 30 private categorical interpretations that are false. "
    "It is not a confidence-score threshold.",
    "- **False consensus:** at least 8 of the final 10 agents choose the false interpretation. "
    "Correct consensus means at least 8 of the final 10 choose the true interpretation; other runs are mixed.",
    "- **Group decision:** at least 20 of all 30 agents agree. The group is wrong if at least "
    "20 choose the false interpretation, correct if at least 20 choose the true interpretation, "
    "and otherwise undecided. This is the rule in the governance bar plot.", "",
    "Adverse paths deliberately start with four misleading private signals; later signals "
    "are 70% reliable. The normal-path cells are retained in the CSV but the tables below "
    "focus on the adverse stress test. These are descriptive estimates; agents within a "
    "swarm are not independent observations.", "",
    "## Original cross-model comparison", "",
    "These are the original governance/model collections, using five runs per condition "
    "for Haiku, Sonnet, GPT-5 mini, and Gemini, and two for Opus. They are not the later "
    "40-run Haiku baseline sample.", "",
    "| Model | Runs per condition | Wrong-agent share: no board → board | False consensus: no board → board |",
    "| --- | ---: | ---: | ---: |",
]
for model in MODELS:
    no = lookup["original", "no_board", model, "adverse"]
    board = lookup["original", "baseline", model, "adverse"]
    assert no["n_runs"] == board["n_runs"]
    n = no["n_runs"]
    lines.append(f"| {LABELS[model]} | {n} | {no['share_wrong_decisions']:.1%} → "
                 f"{board['share_wrong_decisions']:.1%} | {no['n_false_consensus']}/{n} → "
                 f"{board['n_false_consensus']}/{n} |")
lines += ["", "The grader-only pattern differs from the earlier four-scenario pooled wording. "
          "Gemini has a higher error share and more false consensuses with the board in "
          "this grader sample. GPT-5 mini's false-consensus rate is already 5/5 without "
          "the board, although its agent-level error share rises. Every model's wrong-agent "
          "share rises here, but these small original samples do not establish a precise "
          "effect for every model.", "",
          "## Original governance rules", "",
          "Haiku, adverse paths, **five swarms per rule**. This grader-only table and bar "
          "plot replace the earlier plot that pooled 20 swarms per rule across four scenarios.", "",
          "| Rule | Correct group decision | No group decision | Wrong group decision | False consensus |",
          "| --- | ---: | ---: | ---: | ---: |"]
for arm in ARMS:
    row = lookup["original", arm, "haiku", "adverse"]
    n = row["n_runs"]
    lines.append(f"| {LABELS[arm]} | {row['n_group_correct']}/{n} | "
                 f"{row['n_group_undecided']}/{n} | {row['n_group_wrong']}/{n} | "
                 f"{row['n_false_consensus']}/{n} |")
lines += ["", "## Expanded Haiku grader comparison", "",
          "Each condition has 40 adverse-path swarms. The baseline board/no-board sample "
          "combines its initial 10 runs with 30 additional runs, without adding the five "
          "older governance controls. The audit combines its original five runs with 35 "
          "additional runs. Pay and information planning each have their own 40 new runs.", "",
          "| Condition | Wrong-agent share | False consensus | Correct consensus | Mixed | Logged collection dates |",
          "| --- | ---: | ---: | ---: | ---: | --- |"]
for condition in ("no_board", "baseline", "final_five_pay", "final_five_information", "verbatim_audit"):
    row = lookup["expanded", condition, "haiku", "adverse"]
    n = row["n_runs"]
    lines.append(f"| {LABELS[condition]} | {row['share_wrong_decisions']:.1%} | "
                 f"{row['n_false_consensus']}/{n} | {row['n_correct_consensus']}/{n} | "
                 f"{row['n_mixed_consensus']}/{n} | {row['collection_dates'].replace(';', ', ')} |")
lines += ["", "The pay/information experiments use historical controls collected on earlier "
          "dates, and the audit pools two collection waves. These comparisons should not "
          "be described as a single contemporaneous randomized five-arm trial. The most "
          "recent four-line figure shows the four board conditions; the original two-line "
          "figure compares the paired board and no-board signal paths.", "",
          "The CSV supplies both consensus definitions, final-ten and final-five error "
          "shares, denominators, dates, and source filenames. Normal-path and original "
          "small-sample results remain separate from the expanded comparisons.", ""]
note = ROOT / "notes/grader-findings.md"
note.parent.mkdir(parents=True, exist_ok=True)
note.write_text("\n".join(lines))
print(f"Wrote {output.relative_to(ROOT)} and {note.relative_to(ROOT)}: "
      "53 cells from 411 distinct complete grader swarms.")
