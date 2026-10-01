from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "modified_data").mkdir(exist_ok=True)
(ROOT / "draft").mkdir(exist_ok=True)

import csv
import gzip
import json
import os
import tempfile
from collections import Counter, defaultdict

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "swarm-matplotlib"))
os.environ.setdefault("FS_FONT_CACHE", str(Path(tempfile.gettempdir()) / "swarm-fonts"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

from fs_footer import apply_style, add_footer, AQUA, ORANGE, INK, INK2
from scenarios import BANK

# Restrict the eight-arm group-decision comparison to the original grader task.
# The earlier blog figure pooled four tasks; this grader-only panel has five runs per rule.
# A group decides when at least 20 of all 30 private categorical answers agree.
labels = {"no_board": "No board", "verbatim_audit": "Verbatim-quote audit",
          "outcome_tallies": "Outcome tallies", "skeptic_quota": "Skeptic quota",
          "hierarchy": "Coordinator digest", "skeptic_triggered": "Triggered skepticism",
          "provenance_claims": "Provenance tags", "baseline": "Free-form board"}
scenarios = ("grader",)
chains = defaultdict(dict)
with gzip.open(ROOT / "original_data" / "grader_original.jsonl.gz", "rt") as source:
    for line in source:
        record = json.loads(line)
        if record["spoke"] != "gov" or record["path"] != "adverse":
            continue
        assert record["arm"] in labels and record["scenario"] in scenarios
        assert record["model_key"] == "haiku" and record["N"] == 30
        assert record["tag"] == "gov-haiku" and record["run"] in range(5)
        key = (record["arm"], record["scenario"], record["run"])
        position = record["position"]
        assert position not in chains[key]
        chains[key][position] = record
assert set(chains) == {(arm, scenario, run) for arm in labels for scenario in scenarios for run in range(5)}

counts = defaultdict(Counter)
for (arm, scenario, run), records in chains.items():
    assert set(records) == set(range(30))
    assert all(records[p]["signal"] == BANK[scenario].wrong for p in range(4))
    assert all(r["parsed"]["interpretation"] in (BANK[scenario].truth, BANK[scenario].wrong)
               for r in records.values())
    n_correct = sum(r["parsed"]["interpretation"] == BANK[scenario].truth for r in records.values())
    outcome = "correct" if n_correct >= 20 else "wrong" if n_correct <= 10 else "undecided"
    counts[arm][outcome] += 1

rows = []
for arm, label in labels.items():
    n = sum(counts[arm].values())
    assert n == 5
    rows.append(dict(arm=arm, label=label, n_runs=n, n_agents=30, n_scenarios=1,
                     n_correct=counts[arm]["correct"], n_undecided=counts[arm]["undecided"],
                     n_wrong=counts[arm]["wrong"],
                     share_correct=counts[arm]["correct"] / n,
                     share_undecided=counts[arm]["undecided"] / n,
                     share_wrong=counts[arm]["wrong"] / n,
                     decision_rule="At least 20 of all 30 agents agree"))
stem = "board_rule_outcomes"
with (ROOT / "modified_data" / f"{stem}.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

apply_style()
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white",
                     "savefig.facecolor": "white", "pdf.fonttype": 42, "font.size": 11})
fig, ax = plt.subplots(figsize=(12.6, 8.7))
fig.subplots_adjust(left=.205, right=.965, top=.755, bottom=.22)
RECESSIVE = "#d6d5cf"
ys = [0, 1.55, 2.6, 3.65, 4.7, 5.75, 6.8, 7.85]
for y, row in zip(ys, rows):
    left = 0
    for field, color in (("share_correct", AQUA), ("share_undecided", RECESSIVE), ("share_wrong", ORANGE)):
        value = row[field]
        ax.barh(y, value, left=left, height=.68, color=color, edgecolor="white", linewidth=1.1)
        if value >= .08:
            ax.text(left + value / 2, y, f"{value:.0%}", ha="center", va="center", fontsize=12,
                    color="white" if field == "share_wrong" else INK,
                    fontweight="bold" if field == "share_wrong" else "normal")
        left += value
    assert abs(left - 1) < 1e-12
ax.set_yticks(ys)
ax.set_yticklabels([r["label"] for r in rows], fontsize=12)
ax.set_ylim(8.45, -.65)
ax.set_xlim(0, 1)
ax.set_xticks([0, .25, .5, .75, 1])
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_xlabel("Share of swarms (5 per rule)", fontsize=12, color=INK2, labelpad=9)
ax.tick_params(length=0, pad=8, colors=INK2)
for spine in ax.spines.values():
    spine.set_visible(False)
fig.text(.205, .925, "Group decisions of AI-agent swarms, by board rule",
         fontsize=17, fontweight="bold", color=INK, ha="left", va="center")
fig.text(.205, .88, "Grader scenario · Claude Haiku 4.5 · 30 agents · first four signals wrong",
         fontsize=12, color=INK2, ha="left", va="center")
fig.legend(handles=[Patch(color=AQUA, label="Decides correctly"),
                    Patch(color=RECESSIVE, label="No group decision (no ⅔ majority)"),
                    Patch(color=ORANGE, label="Decides wrongly")],
           loc="upper left", bbox_to_anchor=(.202, .855), frameon=False, ncol=3,
           fontsize=11.5, handlelength=.9, handletextpad=.5, columnspacing=1.8)
add_footer(fig, source="Source: author's experiment. Five grader runs per rule; original governance data collected September 19, 2026.",
           source_y=.13, require_logo=False)
for extension in ("png", "pdf"):
    target = ROOT / "draft" / f"{stem}.{extension}"
    fig.savefig(target, dpi=220, facecolor="white")
    print(target)
plt.close(fig)
print("Verified 40 complete swarms, 1,200 decisions, and 5 grader swarms per board rule.")
