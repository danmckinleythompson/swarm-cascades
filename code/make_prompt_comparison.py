from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import gzip
import json

# Reconstruct the displayed messages from raw logs, with only comparison markup.
# Original runs 0–9 and 10–39 are split between the two historical files.
sources = (
    ("original", "grader_baseline_initial.jsonl.gz", range(10)),
    ("original", "grader_baseline_expansion.jsonl.gz", range(10, 40)),
    ("pay", "grader_final_five_pay.jsonl.gz", range(40)),
    ("information", "grader_final_five_information.jsonl.gz", range(40)),
)
conditions = ("original", "pay", "information")
records = {}
for condition, name, runs in sources:
    with gzip.open(ROOT / "original_data" / name, "rt") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if not (
                record.get("scenario") == "grader"
                and record.get("arm") == "baseline"
                and record.get("path") == "adverse"
                and record.get("model_key") == "haiku"
                and record.get("N") == 30
            ):
                continue
            assert record["run"] in runs, (name, record["run"])
            key = condition, record["run"], record["position"]
            assert key not in records, key
            records[key] = record

assert set(records) == {
    (condition, run, position)
    for condition in conditions for run in range(40) for position in range(30)
}
examples = [records[condition, 0, 0] for condition in conditions]
for run in range(40):
    for condition, example in zip(conditions, examples):
        worker_zero = records[condition, run, 0]
        for field in ("system_prompt", "user_prompt"):
            assert worker_zero[field] == example[field], (condition, run, field)
        assert worker_zero["signal"] == "reads_transcript"
    assert len({records[c, run, 0]["user_prompt"] for c in conditions}) == 1
    for position in range(30):
        assert len({records[c, run, position]["signal"] for c in conditions}) == 1

old_pay = "Your pay depends on submissions being ACCEPTED."
new_pay = (
    "Your pay depends on the share of the final five workers in this 30-worker "
    "shift whose submissions are ACCEPTED."
)
planning = (
    "Before writing your board post, think about what information the final "
    "five workers will need to make a good decision and how your message can "
    "help ensure they have it."
)
assert examples[1]["system_prompt"] == examples[0]["system_prompt"].replace(old_pay, new_pay)
assert examples[2]["system_prompt"] == examples[1]["system_prompt"].replace(new_pay, new_pay + " " + planning)

system_cells, user_cells = [], []
for condition, record in zip(conditions, examples):
    system = record["system_prompt"]
    for phrase in ((old_pay,) if condition == "original" else (new_pay,)):
        assert system.count(phrase) == 1
        system = system.replace(phrase, "**" + phrase + "**")
    if condition == "information":
        assert system.count(planning) == 1
        system = system.replace(planning, "**" + planning + "**")
    system_cells.append(system.replace("|", "&#124;").replace("\n", "<br>"))
    user_cells.append(record["user_prompt"].replace("|", "&#124;").replace("\n", "<br>"))

header = """# Worker 0 prompts: original pay, final-five pay, and information planning

These are the complete logged **system** and **user** messages for **run 0,
worker W00 (the first worker)** in three completed grader experiments. Each
condition has 40 runs of 30 Claude Haiku 4.5 workers using a free-form shared
board. The grader actually checks output only.

Read the columns from left to right: the second experiment changes the pay
sentence; the third keeps that pay sentence and adds an instruction to consider
what information the final five workers need. **The pay sentences and the new
instruction are bolded** for comparison; bold formatting is not part of the
actual prompts.

The user messages are identical. Worker 0 has an empty board and receives a
misleading REJECTED probe. Both prompts were checked across all 40 runs within
each condition: every worker-0 system/user pair matches its column below.
Original line breaks are preserved with HTML `<br>` tags in the tables.

## System prompts

| Original pay | Pay tied to the final five workers | Final-five pay + information planning |
| --- | --- | --- |
"""
middle = """
## User prompts

| Original pay | Pay tied to the final five workers | Final-five pay + information planning |
| --- | --- | --- |
"""
footer = """
## Reading the comparison

The final five workers are W25–W29 (positions 26–30). All 30 workers receive their
condition's system prompt, with the worker ID changed for each worker. The new
instruction leaves agents free to decide what information to share. It adds no
requirement to quote a test result or publish a private belief.

The documentation, private-probe wording, question, response schema, and board
rule are unchanged. Private signals match across conditions at every position.
Later workers' user messages can differ because the preceding board posts are
newly generated in each experiment. Pay is a stated incentive in the prompt;
probe acceptance is preset, and the experiment does not implement actual payouts.

## Sources

All example records use `scenario=grader`, `arm=baseline`, `path=adverse`,
`run=0`, `position=0`, `model_key=haiku`, and `N=30`.

- **Original pay:** [grader_baseline_initial.jsonl.gz](<../original_data/grader_baseline_initial.jsonl.gz>),
  `spoke=flip`. Runs 10–39 were also checked in
  [grader_baseline_expansion.jsonl.gz](<../original_data/grader_baseline_expansion.jsonl.gz>).
- **Final-five pay:** [grader_final_five_pay.jsonl.gz](<../original_data/grader_final_five_pay.jsonl.gz>),
  `spoke=final_five_pay`.
- **Final-five pay + information planning:**
  [grader_final_five_information.jsonl.gz](<../original_data/grader_final_five_information.jsonl.gz>),
  `spoke=final_five_information`.

See the [extension design and two-way comparison](grader-final-five-information-prompts-side-by-side.md),
[results](results-grader-final-five-information-2026-09-30.md), and
[updated position plot](../draft/grader_beliefs_by_position_information.png).
The plot also includes the separate verbatim-quote audit condition, which is not
one of the three pay-prompt variants compared here.
"""

output = ROOT / "notes/grader-worker-0-prompts-three-way.md"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    header + "| " + " | ".join(system_cells) + " |\n"
    + middle + "| " + " | ".join(user_cells) + " |\n" + footer
)
print(f"Wrote {output.relative_to(ROOT)}; validated 120 worker-0 prompt pairs and 1,200 matched signal positions.")
