# Grader illustrations

These three assets are exact exports from the authoring document for [the Free Systems post](https://freesystems.substack.com/p/extraordinary-multi-agent-delusions), checked September 30–October 1, 2026. Their original artwork generators were not available. `code/extract_blog_examples.py` regenerates [their source text](../../modified_data/blog_illustration_sources.md) from the included logs.

| Asset | Source |
| --- | --- |
| [Worker prompt](grader_worker_0_prompt.png) | `grader_baseline_initial.jsonl.gz`, baseline/adverse, run 0/W00. The instrument and board builder are in `code/scenarios.py` and `code/arms.py`. |
| [Signal-reporting animation](grader_run_15_signal_reporting.gif) | `grader_baseline_expansion.jsonl.gz`, baseline/adverse, run 15. The GIF stops at W20; the source document contains all 30 board posts. The first frame is nearly black; view as an animation. |
| [Rationale excerpts](grader_rationale_excerpts.png) | `grader_original.jsonl.gz`, gov/baseline/normal, run 4/W10 and run 0/W15. These are private rationales, not public board posts. |

The prior overview illustration refers to four scenarios and is excluded. Through W20 in the animation, the actual private probes contain 13 ACCEPTED and eight REJECTED results. Agents' claimed tallies can differ. The generated source document also verifies the overview's grader-specific fact: 33 of 40 private-signal paths have a strict correct majority, four tie, and three have a wrong majority.
