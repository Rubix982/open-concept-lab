"""
Visualize the E-012 FT-L baseline (propagation_table.txt) as a propagation-by-hop bar.
Run: .venv/bin/python experiments/edit_propagation/ft_baseline_fig.py
Out: results/final/figures/ft_propagation_by_hop.png
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FINAL = Path(__file__).resolve().parent.parent.parent / "results" / "final"
txt = (FINAL / "tables" / "propagation_table.txt").read_text()

vals = {}
for line in txt.splitlines():
    m = re.match(r"\s*(\w+):\s*n=(\d+)\s*propagated=([\d.]+)%", line)
    if m:
        vals[m.group(1)] = (int(m.group(2)), float(m.group(3)))

HOPS = ["paraphrase", "1hop", "2hop"]           # the hop-decay story
present = [t for t in HOPS if t in vals]

plt.rcParams.update({"figure.facecolor": "#0F1320", "axes.facecolor": "#0F1320",
                     "text.color": "#EAECF4", "axes.labelcolor": "#EAECF4",
                     "xtick.color": "#EAECF4", "ytick.color": "#8A93A8", "font.size": 12})
fig, ax = plt.subplots(figsize=(7.5, 4.4))
xs = range(len(present))
ys = [vals[t][1] for t in present]
ax.bar(xs, ys, color="#6FD39A", width=0.6, edgecolor="#0F1320")
for x, t in zip(xs, present):
    n, p = vals[t]
    ax.text(x, p + 1.2, f"{p:.0f}%", ha="center", color="#EAECF4", fontweight="bold")
    ax.text(x, -3.2, f"n={n}", ha="center", color="#8A93A8", fontsize=10)
ax.set_xticks(list(xs)); ax.set_xticklabels(present)
ax.set_ylim(0, max(ys) * 1.35 + 3)
ax.set_ylabel("% of neighbours correctly propagated")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#2A3247")
ax.set_title("FT-L baseline: propagation decays with hop distance\n"
             "gpt2-small · 20 edits (E-012)", fontsize=12, pad=12)
loc = vals.get("locality")
foot = ("locality omitted: FT-L run had NO competence filter, so 'preserved' conflates "
        "true specificity with unchanged garbage — not a clean specificity measure.")
fig.text(0.5, 0.01, foot, ha="center", color="#8A93A8", fontsize=8, style="italic", wrap=True)
plt.tight_layout(rect=(0, 0.06, 1, 1))
out = FINAL / "figures" / "ft_propagation_by_hop.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"parsed {vals}\nSaved → {out}")
