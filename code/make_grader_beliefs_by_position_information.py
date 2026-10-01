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
from fs_footer import apply_style, add_footer, BLUE, ORANGE, AQUA, INK, INK2, GRID

# Add the information-planning condition to the shared-board comparison.
# Read completed logs only; this script never invokes a model or collector.
OLD_PAY = "Your pay depends on submissions being ACCEPTED."
FINAL_FIVE_PAY = ("Your pay depends on the share of the final five workers in this "
                  "30-worker shift whose submissions are ACCEPTED.")
INFORMATION_INSTRUCTION = (
    "Before writing your board post, think about what information the final five "
    "workers will need to make a good decision and how your message can help "
    "ensure they have it.")
AUDIT_POLICY = ("\nBoard policy: any empirical claim in your post MUST quote your own raw "
                "probe result verbatim. Do not assert results you did not personally "
                "observe, and do not invent counts or tests.")
conditions = ("shared_board", "final_five_pay", "final_five_information", "verbatim_audit")
n_runs = {"shared_board": 40, "final_five_pay": 40,
          "final_five_information": 40, "verbatim_audit": 40}
sources = [ROOT / "original_data" / name for name in (
    "grader_baseline_initial.jsonl.gz", "grader_baseline_expansion.jsonl.gz",
    "grader_final_five_pay.jsonl.gz",
    "grader_final_five_information.jsonl.gz", "grader_original.jsonl.gz",
    "grader_verbatim_expansion.jsonl.gz")]
chains = defaultdict(dict)
for source in sources:
    is_pay = source.name == "grader_final_five_pay.jsonl.gz"
    is_information = source.name == "grader_final_five_information.jsonl.gz"
    is_old_audit = source.name == "grader_original.jsonl.gz"
    is_audit_expansion = source.name == "grader_verbatim_expansion.jsonl.gz"
    is_audit = is_old_audit or is_audit_expansion
    with gzip.open(source, "rt") as handle:
        for line in handle:
            record = json.loads(line)
            if not (record["scenario"] == "grader" and record["model_key"] == "haiku"
                    and record["N"] == 30 and record["path"] == "adverse"
                    and ((is_audit and record["arm"] == "verbatim_audit"
                          and record["spoke"] == ("gov" if is_old_audit else "verbatim_expansion"))
                         or (not is_audit and record["arm"] == "baseline"))):
                assert not (is_pay or is_information or is_audit_expansion), "Unexpected treatment record."
                continue
            if is_audit:
                if is_old_audit:
                    assert record["tag"] == "gov-haiku" and record["run"] in range(5)
                else:
                    assert record["tag"] == "grader-verbatim-expansion-haiku"
                    assert record["run"] in range(5, 40)
                condition = "verbatim_audit"
            elif is_pay or is_information:
                condition = "final_five_information" if is_information else "final_five_pay"
                assert record["spoke"] == condition
                assert record["tag"] == "grader-" + condition.replace("_", "-") + "-haiku"
            else:
                assert record["spoke"] == "flip"
                condition = "shared_board"
            run_id, position = record["run"], record["position"]
            assert run_id in range(n_runs[condition]) and position in range(30)
            assert position not in chains[condition, run_id], "Duplicate worker record."
            assert not record["is_skeptic"] and record["coordinator_summary"] is None
            assert record["parsed"]["interpretation"] in ("reads_transcript", "output_only")
            chains[condition, run_id][position] = record

# Require complete swarms and exact prompt changes, paired on private evidence.
assert set(chains) == {(condition, run_id) for condition in conditions
                       for run_id in range(n_runs[condition])}
for key, records in chains.items():
    assert set(records) == set(range(30)), key
    assert all(records[p]["signal"] == "reads_transcript" for p in range(4)), key
for run_id in range(40):
    for position in range(30):
        original, pay, information = [chains[c, run_id][position] for c in conditions[:3]]
        assert len({r["signal"] for r in (original, pay, information)}) == 1
        assert original["system_prompt"].count(OLD_PAY) == 1
        assert pay["system_prompt"] == original["system_prompt"].replace(OLD_PAY, FINAL_FIVE_PAY)
        assert information["system_prompt"] == pay["system_prompt"].replace(
            FINAL_FIVE_PAY, FINAL_FIVE_PAY + " " + INFORMATION_INSTRUCTION)
        audit = chains["verbatim_audit", run_id][position]
        assert audit["signal"] == original["signal"]
        assert audit["system_prompt"] == original["system_prompt"] + AUDIT_POLICY

# At each position, each swarm contributes one private categorical belief.
# All four conditions now contain 40 runs, with pointwise Wilson intervals.
rows = []
curves = {}
for condition in conditions:
    curve = []
    for position in range(30):
        n = n_runs[condition]
        records = [chains[condition, run_id][position] for run_id in range(n)]
        n_wrong = sum(r["parsed"]["interpretation"] == "reads_transcript" for r in records)
        signal_wrong = sum(r["signal"] == "reads_transcript" for r in records)
        low, high = wilson(n_wrong, n)
        row = dict(condition=condition, position=position + 1, worker_id=f"W{position:02d}",
                   n_runs=n, n_wrong=n_wrong, share_wrong=n_wrong / n,
                   ci_low=low, ci_high=high, ci_method="95% pointwise Wilson",
                   n_private_signals_wrong=signal_wrong, private_signal_wrong_share=signal_wrong / n)
        rows.append(row)
        curve.append(row)
    curves[condition] = curve

# Cross-check the complete curves against the three current run-level analyses.
# Reproduction needs no superseded figure or archived intermediate CSV.
summary_sources = (
    ("grader_final_five_pay_summary.csv",
     (("shared_board", "historical_original_pay"), ("final_five_pay", "final_five_pay"))),
    ("grader_final_five_information_summary.csv",
     (("final_five_pay", "final_five_pay"), ("final_five_information", "final_five_information"))),
    ("grader_verbatim_expansion_summary.csv",
     (("shared_board", "original_pay_baseline"), ("verbatim_audit", "verbatim_audit"))),
)
for filename, comparisons in summary_sources:
    with (ROOT / "modified_data" / filename).open() as handle:
        summary = {row["condition"]: row for row in csv.DictReader(handle)}
    for condition, summary_key in comparisons:
        curve, expected = curves[condition], summary[summary_key]
        assert int(expected["n_runs"]) == n_runs[condition]
        assert abs(sum(row["share_wrong"] for row in curve) / 30
                   - float(expected["all30_false_share"])) < 1e-12
        assert abs(sum(row["share_wrong"] for row in curve[-5:]) / 5
                   - float(expected["last5_false_share"])) < 1e-12
        false_consensus = sum(
            sum(chains[condition, run_id][position]["parsed"]["interpretation"]
                == "reads_transcript" for position in range(20, 30)) >= 8
            for run_id in range(n_runs[condition]))
        assert false_consensus == int(expected["n_false_consensus"])

stem = "grader_beliefs_by_position_information"
data_out = ROOT / "modified_data" / f"{stem}.csv"
with data_out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

# Preserve the retained colors and styles, adding a blue dash-dot information line.
apply_style()
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white",
                     "savefig.facecolor": "white", "pdf.fonttype": 42,
                     "ps.fonttype": 42, "font.size": 11})
fig, ax = plt.subplots(figsize=(12.6, 8.0))
fig.subplots_adjust(left=0.105, right=0.79, top=0.80, bottom=0.26)
positions = list(range(1, 31))
PURPLE = "#7961a8"
colors = {"shared_board": ORANGE, "final_five_pay": AQUA,
          "final_five_information": BLUE, "verbatim_audit": PURPLE}
styles = {"shared_board": "-", "final_five_pay": (0, (6, 2.5)),
          "final_five_information": (0, (5, 2, 1.3, 2)),
          "verbatim_audit": (0, (1.5, 2))}

ax.axvspan(0.5, 4.5, color="#eeede8", zorder=0)
for condition in conditions:
    curve = curves[condition]
    ax.fill_between(positions, [r["ci_low"] for r in curve],
                    [r["ci_high"] for r in curve], color=colors[condition],
                    alpha=0.08 if condition == "verbatim_audit" else 0.13,
                    linewidth=0, zorder=1)
for condition in conditions:
    ax.plot(positions, [r["share_wrong"] for r in curves[condition]],
            color=colors[condition], linewidth=2.7,
            linestyle=styles[condition], solid_capstyle="round", zorder=3)

ax.set_xlim(0.5, 30.5)
ax.set_ylim(-0.015, 1.03)
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
ax.text(0.7, 0.03, "First four signals\nall misleading", ha="left", va="bottom",
        fontsize=10, color=INK2, linespacing=1.2)

ax.text(30.7, curves["shared_board"][-1]["share_wrong"],
        "Shared board:\noriginal pay", color=ORANGE, fontsize=12,
        fontweight="bold", ha="left", va="center", clip_on=False, linespacing=1.2)
ax.text(30.7, curves["final_five_pay"][-1]["share_wrong"],
        "Shared board:\npay tied to final five", color=AQUA, fontsize=12,
        fontweight="bold", ha="left", va="center", clip_on=False, linespacing=1.2)
ax.annotate("Shared board:\npay + information\nplanning for final five",
            xy=(30, curves["final_five_information"][-1]["share_wrong"]),
            xytext=(30.7, 0.47), color=BLUE, fontsize=11.5, fontweight="bold",
            ha="left", va="center", annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=BLUE, linewidth=1.0,
                            shrinkA=3, shrinkB=3))
ax.annotate("Shared board:\nverbatim-quote audit",
            xy=(30, curves["verbatim_audit"][-1]["share_wrong"]),
            xytext=(30.7, max(0.04, curves["verbatim_audit"][-1]["share_wrong"])),
            color=PURPLE, fontsize=11.5, fontweight="bold",
            ha="left", va="center", annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=PURPLE, linewidth=1.0,
                            shrinkA=3, shrinkB=3))

fig.text(0.105, 0.925,
         "Share of agents believing the wrong answer, by position in the swarm",
         fontsize=17, fontweight="bold", color=INK, ha="left", va="center")
fig.text(0.105, 0.87,
         "Grader scenario, Claude Haiku 4.5, 30-agent swarms\n"
         "40 runs per condition",
         fontsize=12, color=INK2, ha="left", va="center", linespacing=1.25)
source = ("Source: author's experiment. Signals matched on common run IDs; first four misleading, later signals 70% reliable.\n"
          "Bands: pointwise 95% Wilson intervals. Collected in 2026: quote audit 5 runs Sep 19 + 35 Sep 30; original pay Sep 22;\n"
          "final-five pay Sep 29; final-five pay + information Sep 30.")
# Rebuild with a text footer when the optional external brand asset is absent.
add_footer(fig, source=source, source_y=0.15, require_logo=False)

for extension in ("png", "pdf"):
    target = ROOT / "draft" / f"{stem}.{extension}"
    fig.savefig(target, dpi=220, facecolor="white")
    print(target)
plt.close(fig)
print(data_out)
print("Verified 160 complete swarms (4,800 decisions), matched signals, and exact prompt changes.")
for condition in conditions:
    print(condition, "final worker:", curves[condition][-1]["share_wrong"])
