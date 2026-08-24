"""
T-024: the two-graphs schematic (thesis diagram) — draft for review.
Logical entailment graph vs the model's causal-read graph: align near the edit,
diverge with hop. Ripple fails where they diverge (logical neighbours = representational
strangers). Run: .venv/bin/python experiments/edit_propagation/two_graphs_fig.py
Out: results/final/figures/two_graphs.png
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

FINAL = Path(__file__).resolve().parent.parent.parent / "results" / "final"
BG, FG, MUTE = "#0F1320", "#EAECF4", "#8A93A8"
GOOD, BAD, ACC = "#6FD39A", "#F58AA0", "#7C9CFF"

# nodes: (label, radius, angle_deg, hop)   hop 0=edit,1=paraphrase,2=1hop,3=2hop
NODES = [
    ("EDIT\n(subject)", 0.0, 0, 0),
    ("paraphrase", 1.15, 90, 1),
    ("1-hop", 1.15, 210, 2),
    ("1-hop", 1.15, 330, 2),
    ("2-hop", 2.15, 150, 3),
    ("2-hop", 2.15, 30, 3),
    ("2-hop", 2.15, 270, 3),
]


def pos(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def draw(ax, title, causal):
    ax.set_facecolor(BG)
    ax.set_xlim(-2.9, 2.9); ax.set_ylim(-2.9, 2.9); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, color=FG, fontsize=13, pad=10)
    cx, cy = pos(*NODES[0][1:3])
    # edges centre → each node
    for lab, r, a, hop in NODES[1:]:
        x, y = pos(r, a)
        if not causal:                                  # logical: uniform, present
            col, lw, ls, alpha = MUTE, 1.6, (0, (4, 3)), 0.9
        else:                                           # causal-read: strong near → weak/broken far
            if hop == 1:
                col, lw, ls, alpha = GOOD, 3.2, "solid", 1.0
            elif hop == 2:
                col, lw, ls, alpha = GOOD, 2.0, "solid", 0.9
            else:                                       # 2-hop: broken / mis-routed
                col, lw, ls, alpha = BAD, 1.2, (0, (2, 3)), 0.85
        ax.add_patch(FancyArrowPatch((cx, cy), (x, y), arrowstyle="-", color=col,
                                     lw=lw, linestyle=ls, alpha=alpha,
                                     shrinkA=22, shrinkB=22))
    # nodes
    for lab, r, a, hop in NODES:
        x, y = pos(r, a)
        if hop == 0:
            fc, ec, tc = ACC, ACC, BG
        elif not causal:
            fc, ec, tc = "#1E2540", MUTE, FG
        elif hop <= 2:
            fc, ec, tc = "#143A2E", GOOD, GOOD
        else:
            fc, ec, tc = "#3A1622", BAD, BAD
        ax.add_patch(Circle((x, y), 0.42 if hop == 0 else 0.34, facecolor=fc,
                            edgecolor=ec, lw=1.6, zorder=3))
        ax.text(x, y, lab, ha="center", va="center", color=tc,
                fontsize=8.5 if hop == 0 else 8, fontweight="bold", zorder=4)


plt.rcParams.update({"figure.facecolor": BG})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 5.6))
draw(a1, "Logical entailment graph\n(model-independent — all hops connected)", causal=False)
draw(a2, "Model's causal-read graph\n(strong near · weak / mis-routed far)", causal=True)
fig.suptitle("Two graphs: logical neighbours are representational strangers at distance",
             color=FG, fontsize=14, y=0.99)
fig.text(0.5, 0.02,
         "Ripple succeeds where the graphs ALIGN (near the edit) and fails where they "
         "DIVERGE (far): stale = edit can't reach · over-propagation = mis-routed.",
         ha="center", color=MUTE, fontsize=9, style="italic")
# legend
from matplotlib.lines import Line2D
leg = [Line2D([0], [0], color=MUTE, lw=1.6, ls=(0, (4, 3)), label="logical entailment"),
       Line2D([0], [0], color=GOOD, lw=3, label="causal read (reaches)"),
       Line2D([0], [0], color=BAD, lw=1.2, ls=(0, (2, 3)), label="causal read (broken / mis-routed)")]
fig.legend(handles=leg, loc="lower center", ncol=3, frameon=False,
           labelcolor=FG, fontsize=9, bbox_to_anchor=(0.5, 0.06))
plt.tight_layout(rect=(0, 0.09, 1, 0.96))
out = FINAL / "figures" / "two_graphs.png"
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"Saved → {out}")
