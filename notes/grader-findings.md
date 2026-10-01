# Grader findings

Generated from the saved worker records by `code/analyze_grader_outcomes.py`. All runs here use 30 agents and the original grader truth: **output only**. `reads_transcript` is the false interpretation. No flipped grader or other scenario is included.

The complete [CSV](../modified_data/grader_outcomes.csv) has 48 original model/rule/path cells and five expanded comparison cells. It covers 411 distinct swarms and 12,330 decisions. Five original audit swarms also appear in the expanded audit cell; the two scopes are separate summaries and must not be added together.

## Measures

- **Wrong-agent share:** fraction of all 30 private categorical interpretations that are false. It is not a confidence-score threshold.
- **False consensus:** at least 8 of the final 10 agents choose the false interpretation. Correct consensus means at least 8 of the final 10 choose the true interpretation; other runs are mixed.
- **Group decision:** at least 20 of all 30 agents agree. The group is wrong if at least 20 choose the false interpretation, correct if at least 20 choose the true interpretation, and otherwise undecided. This is the rule in the governance bar plot.

Adverse paths deliberately start with four misleading private signals; later signals are 70% reliable. The normal-path cells are retained in the CSV but the tables below focus on the adverse stress test. These are descriptive estimates; agents within a swarm are not independent observations.

## Original cross-model comparison

These are the original governance/model collections, using five runs per condition for Haiku, Sonnet, GPT-5 mini, and Gemini, and two for Opus. They are not the later 40-run Haiku baseline sample.

| Model | Runs per condition | Wrong-agent share: no board → board | False consensus: no board → board |
| --- | ---: | ---: | ---: |
| Claude Haiku 4.5 | 5 | 40.0% → 100.0% | 0/5 → 5/5 |
| Claude Sonnet 4.6 | 5 | 44.0% → 72.7% | 0/5 → 2/5 |
| GPT-5 mini | 5 | 86.0% → 100.0% | 5/5 → 5/5 |
| Gemini 2.5 Flash | 5 | 40.7% → 68.7% | 0/5 → 3/5 |
| Claude Opus 4.6 | 2 | 43.3% → 100.0% | 0/2 → 2/2 |

The grader-only pattern differs from the earlier four-scenario pooled wording. Gemini has a higher error share and more false consensuses with the board in this grader sample. GPT-5 mini's false-consensus rate is already 5/5 without the board, although its agent-level error share rises. Every model's wrong-agent share rises here, but these small original samples do not establish a precise effect for every model.

## Original governance rules

Haiku, adverse paths, **five swarms per rule**. This grader-only table and bar plot replace the earlier plot that pooled 20 swarms per rule across four scenarios.

| Rule | Correct group decision | No group decision | Wrong group decision | False consensus |
| --- | ---: | ---: | ---: | ---: |
| No board | 2/5 | 3/5 | 0/5 | 0/5 |
| Free-form board | 0/5 | 0/5 | 5/5 | 5/5 |
| Verbatim-quote audit | 4/5 | 1/5 | 0/5 | 0/5 |
| Outcome tallies | 2/5 | 2/5 | 1/5 | 1/5 |
| Skeptic quota | 2/5 | 2/5 | 1/5 | 0/5 |
| Coordinator digest | 2/5 | 3/5 | 0/5 | 0/5 |
| Triggered skepticism | 1/5 | 0/5 | 4/5 | 3/5 |
| Provenance tags | 0/5 | 0/5 | 5/5 | 5/5 |

## Expanded Haiku grader comparison

Each condition has 40 adverse-path swarms. The baseline board/no-board sample combines its initial 10 runs with 30 additional runs, without adding the five older governance controls. The audit combines its original five runs with 35 additional runs. Pay and information planning each have their own 40 new runs.

| Condition | Wrong-agent share | False consensus | Correct consensus | Mixed | Logged collection dates |
| --- | ---: | ---: | ---: | ---: | --- |
| No board | 41.5% | 0/40 | 12/40 | 28/40 | 2026-09-22 |
| Free-form board | 94.3% | 37/40 | 3/40 | 0/40 | 2026-09-22 |
| Final-five pay | 74.6% | 27/40 | 13/40 | 0/40 | 2026-09-29 |
| Final-five pay + information planning | 69.5% | 24/40 | 16/40 | 0/40 | 2026-09-30 |
| Verbatim-quote audit | 30.5% | 3/40 | 37/40 | 0/40 | 2026-09-19, 2026-09-30 |

The pay/information experiments use historical controls collected on earlier dates, and the audit pools two collection waves. These comparisons should not be described as a single contemporaneous randomized five-arm trial. The most recent four-line figure shows the four board conditions; the original two-line figure compares the paired board and no-board signal paths.

The CSV supplies both consensus definitions, final-ten and final-five error shares, denominators, dates, and source filenames. Normal-path and original small-sample results remain separate from the expanded comparisons.
