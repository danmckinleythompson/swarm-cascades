# Swarm cascades

A reproduction package for the **TaskBench grader experiment** in [Extraordinary Multi-Agent Delusions and the Madness of Crowds](https://freesystems.substack.com/p/extraordinary-multi-agent-delusions), published on **Free Systems**, plus the recent reward-prompt and quote-audit extensions. In every included run, the grader checks **output only**; `reads_transcript` is the false belief. No other scenarios or reversed-truth runs are included.

## Included experiments

### Grader experiment across models

All swarms have **30 agents**. Each original model/rule combination has both normal paths and adverse paths (the first four private signals are misleading).

| Model | Board rules | Runs per rule per path | Total swarms |
| --- | --- | ---: | ---: |
| Claude Haiku 4.5 | All eight original rules | 5 | 80 |
| Claude Sonnet 4.6 | No board, free-form board, skeptic quota, triggered skepticism | 5 | 40 |
| GPT-5 mini | Same four rules | 5 | 40 |
| Gemini 2.5 Flash | Same four rules | 5 | 40 |
| Claude Opus 4.6 | Same four rules | 2 | 16 |

These **216 swarms / 6,480 decisions** are in [grader_original.jsonl.gz](original_data/grader_original.jsonl.gz). See the [cross-model results](notes/grader-findings.md#original-cross-model-comparison), [complete model/rule/path table](modified_data/grader_outcomes.csv), and [analysis code](code/analyze_grader_outcomes.py). The later 40-run Haiku comparison is a separate collection, not added to the original five-run cells.

### Reward based on the final five agents

Both extensions use **Claude Haiku 4.5, 30 agents, a free-form shared board, and 40 adverse-path runs**. The final five workers are W25–W29 (positions 26–30).

The pay-only extension replaces the original individual-pay sentence with:

> Your pay depends on the share of the final five workers in this 30-worker shift whose submissions are ACCEPTED.

The information-planning extension keeps that sentence and adds:

> Before writing your board post, think about what information the final five workers will need to make a good decision and how your message can help ensure they have it.

| Extension | Complete raw responses | Results | Analysis |
| --- | --- | --- | --- |
| Final-five pay — 40 swarms / 1,200 decisions | [Data](original_data/grader_final_five_pay.jsonl.gz) | [Results and uncertainty](notes/results-grader-final-five-pay-2026-09-29.md) | [Code](code/analyze_grader_final_five_pay.py) |
| Final-five pay + information planning — 40 swarms / 1,200 decisions | [Data](original_data/grader_final_five_information.jsonl.gz) | [Results and uncertainty](notes/results-grader-final-five-information-2026-09-30.md) | [Code](code/analyze_grader_final_five_information.py) |

All 30 agents receive the treatment's system prompt. The added instruction concerns the **final five**, not just the last agent. [Compare the complete system and user prompts side by side](notes/grader-worker-0-prompts-three-way.md). Signals are matched across conditions, but the historical control and treatments were collected on different dates. These are prompt-based incentives and belief outcomes; no actual payments or submission strategies are implemented.

The package also retains the expanded Haiku board/no-board comparison (**40 swarms each**) and the verbatim-quote audit (**40 swarms: five original plus 35 new**). The [combined results](notes/grader-findings.md#expanded-haiku-grader-comparison) keep those collection waves explicit.

## Figures

| Figure | Data and scope | Code |
| --- | --- | --- |
| [Shared board vs. no board](draft/grader_beliefs_by_position.png) | Haiku, 30 agents, first four signals misleading; **40 runs each**. Reproduces the post's position-plot estimates. | [Generator](code/make_grader_beliefs_by_position.py) |
| [Board rules, grader only](draft/board_rule_outcomes.png) | Eight original rules, **5 grader runs per rule**; at least 20 of all 30 agents agree. A grader-only counterpart to the post's chart, which pools four scenarios. | [Generator](code/make_board_rule_outcomes.py) |
| [Pay, information planning, and quote audit](draft/grader_beliefs_by_position_information.png) | Four shared-board conditions, **40 runs each**. Supplementary extensions; not shown in the published post as checked October 1, 2026. | [Generator](code/make_grader_beliefs_by_position_information.py) |

Each generator also writes a PDF and a same-named CSV in `modified_data/`. Three grader illustrations from the post's authoring document are retained with [source details](draft/illustrations/README.md). The overview image mentions four tasks and is excluded from this grader-only package.

## Rebuild

Use Python 3.12+ (tested: 3.14.4):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python code/master.py
```

Dependency installation needs internet access. The ten-step rebuild runs offline from saved responses, with network requests blocked and no API credentials or paid collectors. It validates every prompt and signal, then regenerates figures, tables, and source/prompt notes. Font or optional logo availability can affect appearance, not estimates.

## Data and interpretation

The six compressed logs contain **12,330 decisions in 411 distinct 30-agent swarms**, preserving the complete original record for each retained decision. [Provenance](original_data/provenance.json) gives source hashes, filters, and counts. Historical labels such as `spoke="flip"` identify a collection batch that also ran other conditions; **every record shipped here has `scenario="grader"`, never `grader_flip`**. The five original audit swarms are reused in the expanded comparison, not counted as new observations.

[The instrument](code/scenarios.py) defines the document and test outcomes; [board rules](code/arms.py) define how agents communicate. [Illustration sources](modified_data/blog_illustration_sources.md) include the complete example board and private rationales.

**Belief** is the categorical `interpretation`, not a threshold on confidence. **False consensus** means at least eight of the last ten agents choose `reads_transcript`; governance bars instead use two-thirds agreement among all 30 agents. Adverse starts force the first four signals wrong; later signals are sampled with 70% reliability. Agents receive simulated test results.

See [grader-only findings](notes/grader-findings.md) and [reproduction limits](notes/reproduction.md) before transferring claims from pooled experiments. The grader-only model results differ from the post's cross-scenario wording, and missing judge-extraction logs prevent reproducing its rationale-citation prevalence claim. No pooled mechanism summaries are included.

Source research: [andybhall/swarm-governance](https://github.com/andybhall/swarm-governance), original and baseline data at `cea4017edefa1106e2662dbb445d4ec9813c0ca4`; extensions collected September 29–30, 2026. This repo is the focused publication package, not a replacement for the research archive.
