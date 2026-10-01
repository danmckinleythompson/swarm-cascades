# Scope and reproduction limits

This package was prepared October 1, 2026. It contains only the original-truth grader scenario at 30 agents, including recent pay/information and quote-audit experiments. The other three scenarios, reversed-truth grader, pilot studies, aggregator studies, old papers, and unused pipelines are excluded.

## What the data reproduce

Every selected raw JSONL line is preserved byte-for-byte from the source logs; gzip wrappers were repacked deterministically. The source filenames, hashes, filters, record counts, and package hashes are recorded in `original_data/provenance.json`. The files are complete swarm selections, not selections based on their outcomes. All 12,330 prompts and signals are reconstructed by `code/check_records.py`; every included swarm has all 30 positions.

The master rebuilds three numerical figures, original grader model/rule summaries, the three extension comparisons, full worker-0 prompts, and the example board/rationales. The original master archive remains in the source repository; this package does not collect fresh model responses. New calls would be a new realization, not a reproduction of saved responses.

## Changes needed when making the post grader-only

- The live document's governance chart pools five runs in each of four scenarios. The replacement here uses **five original grader runs per rule**. Its percentages therefore differ; the additional 35 grader audit runs appear in the separate 40-run extension comparison, not in the balanced original-rule chart.
- The live overview image also says “four tasks / 20 groups per rule.” It is excluded. Three purely grader illustrations remain.
- Cross-model conclusions must use the grader-only table. Gemini worsens with a board in these grader runs. GPT-5 mini already has false consensus in all five original adverse no-board runs. The draft's pooled “Gemini exception” does not describe this subgroup. Small cell sizes—especially two original Opus runs per arm/path—limit precision.
- The draft's rationale-citation percentages were computed with model-coded extraction logs that have not been recovered. Saved pooled summaries cannot substitute for grader-only estimates. We therefore include neither those pooled tables nor a claimed reproduced percentage. Needed files in the research archive are `extraction_gemini.jsonl` and `extraction_sonnet.jsonl`.
- The broad Bayesian-behavior claim is not established by these plots or examples. Private commitments are not identical to public posts, and comparisons depend on priors, the observation model, and whether an observer knows the adverse prefix was forced. No generic claim of irrational Bayesian updating is reproduced here.

## Design qualifications

The first four forced errors make the adverse paths stress tests, not estimates of ordinary-run prevalence. Historical baseline controls and recent treatments were collected on different dates. Matched signal paths remove one source of variation but do not eliminate provider/model changes over time. Audit results pool five September 19 runs with 35 September 30 runs.

The quoting policy is an instruction, not a software-enforced constraint. Outcome tallies count agent-reported outcomes. Triggered skepticism is scheduled from private commitments, not coded public-post stances. For the coordinator condition, prompt checks reuse the saved coordinator message; they do not call a model again.

Rationales are privately elicited text, not direct evidence of a causal reasoning process. The two quote-card examples come from normal paths: one favors the correct interpretation and one the wrong interpretation. Claimed counts inside the animation and quotes are the agents' claims, not verified statistics.

Original illustration artwork generators are unavailable. The three exported image assets are preserved; the text and data that support them are regenerated. Figure fonts and footer logos have portable fallbacks, so numerical reproduction does not imply identical pixels on every platform.

## Package validation

The ten-step rebuild completed in a fresh export with generated outputs removed, no Git metadata or credentials, and network requests blocked. All 23 compared CSV/PNG/Markdown files matched the prepared package exactly; all three PDFs regenerated. Every retained raw record passed the grader-only restriction and prompt/signal checks. No model calls were made while assembling or validating this package.
