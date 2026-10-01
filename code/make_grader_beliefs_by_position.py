from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "modified_data").mkdir(exist_ok=True)
(ROOT / "draft").mkdir(exist_ok=True)

import csv
import gzip
import json
import os
import tempfile
from collections import defaultdict

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "swarm-matplotlib"))
os.environ.setdefault("FS_FONT_CACHE", str(Path(tempfile.gettempdir()) / "swarm-fonts"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from _metrics import wilson
from fs_footer import apply_style, add_footer, BLUE, ORANGE, INK, INK2, GRID

# Reconstruct the two-condition position figure in the September 30 blog draft.
# Inputs are the original-grader runs, not the flipped-truth scenario.
chains = defaultdict(dict)
for name in ("grader_baseline_initial.jsonl.gz", "grader_baseline_expansion.jsonl.gz"):
    with gzip.open(ROOT / "original_data" / name, "rt") as source:
        for line in source:
            record = json.loads(line)
            if (record["scenario"], record["model_key"], record["N"], record["path"]) != (
                    "grader", "haiku", 30, "adverse"):
                continue
            if record["arm"] not in ("baseline", "no_board"):
                continue
            condition = "shared_board" if record["arm"] == "baseline" else "no_board"
            key, position = (condition, record["run"]), record["position"]
            assert record["spoke"] == "flip" and record["run"] in range(40)
            assert position not in chains[key], "Duplicate worker record."
            assert record["parsed"]["interpretation"] in ("reads_transcript", "output_only")
            chains[key][position] = record

conditions = ("no_board", "shared_board")
assert set(chains) == {(condition, run) for condition in conditions for run in range(40)}
for key, records in chains.items():
    assert set(records) == set(range(30)), key
    assert all(records[p]["signal"] == "reads_transcript" for p in range(4))
for run in range(40):
    for position in range(30):
        assert chains["no_board", run][position]["signal"] == chains["shared_board", run][position]["signal"]

rows, curves = [], {}
for condition in conditions:
    curve = []
    for position in range(30):
        records = [chains[condition, run][position] for run in range(40)]
        n_wrong = sum(r["parsed"]["interpretation"] == "reads_transcript" for r in records)
        n_signal_wrong = sum(r["signal"] == "reads_transcript" for r in records)
        low, high = wilson(n_wrong, len(records))
        row = dict(condition=condition, position=position + 1, worker_id=f"W{position:02d}",
                   n_runs=len(records), n_wrong=n_wrong, share_wrong=n_wrong / len(records),
                   ci_low=low, ci_high=high, ci_method="95% pointwise Wilson",
                   n_private_signals_wrong=n_signal_wrong,
                   private_signal_wrong_share=n_signal_wrong / len(records))
        rows.append(row)
        curve.append(row)
    curves[condition] = curve

stem = "grader_beliefs_by_position"
with (ROOT / "modified_data" / f"{stem}.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

apply_style()
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white",
                     "savefig.facecolor": "white", "pdf.fonttype": 42, "font.size": 11})
fig, ax = plt.subplots(figsize=(12.6, 8.0))
fig.subplots_adjust(left=0.105, right=0.80, top=0.82, bottom=0.245)
x = list(range(1, 31))
colors = {"no_board": BLUE, "shared_board": ORANGE}
ax.axvspan(0.5, 4.5, color="#eeede8", zorder=0)
for condition in conditions:
    curve = curves[condition]
    ax.fill_between(x, [r["ci_low"] for r in curve], [r["ci_high"] for r in curve],
                    color=colors[condition], alpha=0.13, linewidth=0, zorder=1)
private_wrong = [r["private_signal_wrong_share"] for r in curves["shared_board"]]
ax.plot(x, private_wrong, color=INK2, linewidth=1.5, linestyle=(0, (2, 2)), zorder=2)
for condition in conditions:
    ax.plot(x, [r["share_wrong"] for r in curves[condition]],
            color=colors[condition], linewidth=2.7, solid_capstyle="round", zorder=3)

ax.set_xlim(0.5, 30.5)
ax.set_ylim(0, 1.03)
ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
ax.set_yticks([0, .2, .4, .6, .8, 1])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.tick_params(length=0, colors=INK2, labelsize=11.5, pad=6)
ax.set_xlabel("Agent's position in the sequence", fontsize=12, color=INK2, labelpad=9)
ax.set_ylabel("Share of agents believing the wrong answer", fontsize=12, color=INK2, labelpad=9)
ax.set_axisbelow(True)
ax.grid(axis="y", color=GRID, linewidth=0.8)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color("#c3c2bd")
    ax.spines[side].set_linewidth(0.8)
ax.text(0.7, 0.03, "First four signals\nall misleading", ha="left", va="bottom", fontsize=10, color=INK2)
ax.text(30.7, curves["shared_board"][-1]["share_wrong"], "Shared board",
        color=ORANGE, fontsize=12, fontweight="bold", ha="left", va="center", clip_on=False)
ax.annotate("No shared board", xy=(30, curves["no_board"][-1]["share_wrong"]),
            xytext=(30.7, .40), color=BLUE, fontsize=12, fontweight="bold",
            ha="left", va="center", annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=BLUE, linewidth=1, shrinkA=3, shrinkB=3))
ax.annotate("Private signal\npoints to wrong answer", xy=(30, private_wrong[-1]),
            xytext=(30.7, .215), color=INK2, fontsize=10, ha="left", va="center",
            annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=INK2, linewidth=1, linestyle=(0, (2, 2)),
                            shrinkA=3, shrinkB=3))
fig.text(.105, .925, "Share of agents believing the wrong answer, by position in the swarm",
         fontsize=17, fontweight="bold", color=INK, ha="left", va="center")
fig.text(.105, .88, "Grader scenario, Claude Haiku 4.5, 30-agent swarms, 40 runs per condition",
         fontsize=12.5, color=INK2, ha="left", va="center")
add_footer(fig, source=("Source: author's experiment. Identical private signals across conditions; first four misleading, later signals 70% reliable.\n"
                        "Bands: pointwise 95% Wilson intervals. Raw runs collected September 22, 2026."),
           source_y=.143, require_logo=False)
for extension in ("png", "pdf"):
    target = ROOT / "draft" / f"{stem}.{extension}"
    fig.savefig(target, dpi=220, facecolor="white")
    print(target)
plt.close(fig)
print("Verified 80 complete swarms, 2,400 decisions, and identical signal paths.")
