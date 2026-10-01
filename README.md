# Swarm cascades

A small reproduction package for the **TaskBench grader experiment** in [the blog draft](https://docs.google.com/document/d/1Qp7YnSbOVAD9i2JhjyQFnBaSLUmdccnZgeFxWXwdgdU/edit?tab=t.0), plus its recent incentive and quote-audit extensions. In every included run, the grader checks **output only**; `reads_transcript` is the false belief. No other scenarios or reversed-truth runs are included.

## Rebuild

Use Python 3.12+ (tested: 3.14.4):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python code/master.py
```

Dependency installation needs internet access. The ten-step rebuild runs offline from saved responses, with network requests blocked and no API credentials or paid collectors. It validates every prompt and signal, then regenerates figures, tables, and source/prompt notes. Font or optional logo availability can affect appearance, not estimates.

## Figures

| Figure | Data and scope | Code |
| --- | --- | --- |
| [Shared board vs. no board](draft/grader_beliefs_by_position.png) | Haiku, 30 agents, first four signals misleading; **40 runs each**. Reproduces the position-plot estimates in the current draft. | [Generator](code/make_grader_beliefs_by_position.py) |
| [Board rules, grader only](draft/board_rule_outcomes.png) | Eight original rules, **5 grader runs per rule**; at least 20 of all 30 agents agree. **Replaces the draft's chart that pooled four scenarios.** | [Generator](code/make_board_rule_outcomes.py) |
| [Pay, information planning, and quote audit](draft/grader_beliefs_by_position_information.png) | Four shared-board conditions, **40 runs each**; recent extension, not yet embedded in the draft as checked October 1. | [Generator](code/make_grader_beliefs_by_position_information.py) |

Each generator also writes a PDF and a same-named CSV in `modified_data/`. Three grader illustrations from the draft are retained with [source details](draft/illustrations/README.md). The original overview image mentions four tasks and is excluded from this grader-only package.

## Data and prompts

The six compressed logs contain **12,330 decisions in 411 distinct 30-agent swarms**, preserving the complete original record for each retained decision. [Provenance](original_data/provenance.json) gives source hashes, filters, and counts. Historical labels such as `spoke="flip"` identify a collection batch that also ran other conditions; **every record shipped here has `scenario="grader"`, never `grader_flip`**.

- Original grader study: 216 swarms across rules, five worker models, and normal/adverse paths.
- Expanded Haiku baseline/no-board comparison: 80 swarms.
- Final-five pay and final-five pay plus information planning: 40 swarms each.
- Quote-audit expansion: 35 new swarms, pooled with five original swarms for the 40-run comparison. Those five are not new observations.

[The instrument](code/scenarios.py) defines the document and test outcomes; [board rules](code/arms.py) define how agents communicate. [The prompt comparison](notes/grader-worker-0-prompts-three-way.md) shows the full system and user messages. [Illustration sources](modified_data/blog_illustration_sources.md) includes the complete example board and private rationales.

## Interpretation

**Belief** is the categorical `interpretation`, not a threshold on confidence. **False consensus** means at least eight of the last ten agents choose `reads_transcript`; the governance bars instead use two-thirds agreement among all 30 agents. Adverse starts force the first four signals wrong; later signals are sampled with 70% reliability. The agents receive simulated test results; these studies measure beliefs, not actual payments or submission success.

See [grader-only findings](notes/grader-findings.md) for model/rule results and [reproduction limits](notes/reproduction.md) before transferring claims from the pooled experiments. In particular, the grader-only model results differ from the draft's cross-scenario wording, and the missing judge-extraction logs prevent reproducing its rationale-citation prevalence claim. No pooled mechanism summaries are included.

Source research: [andybhall/swarm-governance](https://github.com/andybhall/swarm-governance), original and baseline data at `cea4017edefa1106e2662dbb445d4ec9813c0ca4`; extensions collected September 29–30, 2026. This repo is the focused publication package, not a replacement for the research archive.
