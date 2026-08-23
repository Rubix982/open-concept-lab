"""
E-016 figure: causal IIA (subject-site interchange) vs control, by hop.
Run in analysis venv after iia_scale.py:
    .venv/bin/python experiments/edit_propagation/iia_fig.py
Out: results/final/figures/iia_by_hop.png
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FINAL = Path(__file__).resolve().parent.parent.parent / "results" / "final"
rows = json.loads((FINAL / "data" / "iia_scale.json").read_text())
LAYERS = sorted({int(m.group(1)) for r in rows for k in r
                 if (m := re.match(r"mediated_L(\d+)$", k))})
HOPS = ["paraphrase", "1hop", "2hop"]
aff = [r for r in rows if r["affected"]]

# pick the layer with the highest overall IIA
best_L = max(LAYERS, key=lambda L: sum(r[f"mediated_L{L}"] for r in aff) / max(len(aff), 1))


def rate(sub, key):
    return sum(sub) / len(sub) if sub else 0.0


plt.rcParams.update({"figure.facecolor": "#0F1320", "axes.facecolor": "#0F1320",
                     "text.color": "#EAECF4", "axes.labelcolor": "#EAECF4",
                     "xtick.color": "#EAECF4", "ytick.color": "#8A93A8", "font.size": 11})
present = [h for h in HOPS if any(r["type"] == h for r in aff)]
x = np.arange(len(present)); w = 0.38
fig, ax = plt.subplots(figsize=(8.5, 4.8))
iia = [rate([r[f"mediated_L{best_L}"] for r in aff if r["type"] == h], None) for h in present]
ctl = [rate([r[f"ctrl_repro_L{best_L}"] for r in aff if r["type"] == h], None) for h in present]
ns = [sum(1 for r in aff if r["type"] == h) for h in present]
ax.bar(x - w / 2, iia, w, color="#6FD39A", edgecolor="#0F1320",
       label=f"subject-site patch (IIA, L{best_L})")
ax.bar(x + w / 2, ctl, w, color="#8A93A8", edgecolor="#0F1320",
       label="random-position control")
for xi, (a, c, n) in enumerate(zip(iia, ctl, ns)):
    ax.text(xi - w / 2, a + 0.02, f"{a:.0%}", ha="center", color="#EAECF4", fontweight="bold")
    ax.text(xi + w / 2, c + 0.02, f"{c:.0%}", ha="center", color="#8A93A8")
    ax.text(xi, -0.07, f"n={n}", ha="center", color="#8A93A8", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(present)
ax.set_ylim(0, 1); ax.set_ylabel("P(patch reproduces edited answer | affected)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#2A3247")
ax.set_title(f"Causal mediation of propagation by the subject site · gpt2-small (L{best_L})\n"
             f"is edit propagation caused by reading the edited subject representation?",
             fontsize=12, pad=12)
ax.legend(frameon=False, labelcolor="#EAECF4")
fig.text(0.5, 0.005, "IIA ≫ control = propagation is mediated by the subject site; "
         "IIA ≈ control = not localized there.", ha="center", color="#8A93A8",
         fontsize=8, style="italic")
plt.tight_layout(rect=(0, 0.04, 1, 1))
out = FINAL / "figures" / "iia_by_hop.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"best layer L{best_L} · affected n={len(aff)}")
print(f"Saved → {out}")
