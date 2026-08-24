"""
T-022: does the E-014 hop-decay distribution replicate on a second RippleEdits split?
Popular vs Random, side-by-side stacked bars per hop.
Run: .venv/bin/python experiments/edit_propagation/compare_samples.py
Out: results/final/figures/replication.png
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FINAL = Path(__file__).resolve().parent.parent.parent / "results" / "final"
ORDER = ["updated", "stale", "broken"]
COLOR = {"updated": "#6FD39A", "stale": "#F6A96B", "broken": "#F58AA0"}
HOPS = ["paraphrase", "1hop", "2hop"]


def dist(path):
    d = json.loads(Path(path).read_text())
    by = defaultdict(Counter)
    for r in d:
        by[r["type"]][r["outcome"]] += 1
    return by, len(set(r["edit"] for r in d)), len(d)


pop, pe, pn = dist(FINAL / "data" / "scale_study.json")
rnd, re_, rn = dist(FINAL / "data" / "scale_study_random.json")

plt.rcParams.update({"figure.facecolor": "#0F1320", "axes.facecolor": "#0F1320",
                     "text.color": "#EAECF4", "axes.labelcolor": "#EAECF4",
                     "xtick.color": "#EAECF4", "ytick.color": "#8A93A8", "font.size": 11})
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(HOPS)); w = 0.38
for off, (by, lab) in [(-w / 2, (pop, "popular")), (w / 2, (rnd, "random"))]:
    for i, h in enumerate(HOPS):
        c = by[h]; n = sum(c.values()) or 1
        bottom = 0
        for o in ORDER:
            frac = c[o] / n
            ax.bar(x[i] + off, frac, w, bottom=bottom, color=COLOR[o], edgecolor="#0F1320")
            if frac > 0.08:
                ax.text(x[i] + off, bottom + frac / 2, f"{frac:.0%}", ha="center",
                        va="center", color="#0F1320", fontweight="bold", fontsize=8)
            bottom += frac
    for i, h in enumerate(HOPS):
        n = sum((pop if lab == "popular" else rnd)[h].values())
        ax.text(x[i] + off, 1.02, lab, ha="center", color="#8A93A8", fontsize=8, rotation=0)
ax.set_xticks(x); ax.set_xticklabels(HOPS)
ax.set_ylim(0, 1.12); ax.set_ylabel("share of neighbours")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#2A3247")
ax.set_title(f"Does the hop-decay replicate? · popular ({pe} edits, {pn} nbrs) vs "
             f"random ({re_} edits, {rn} nbrs) · gpt2-small\n"
             "same shape both samples: paraphrase updates, 1-hop stalls, 2-hop breaks",
             fontsize=12, pad=14)
handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[o]) for o in ORDER]
ax.legend(handles, ORDER, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1),
          frameon=False, labelcolor="#EAECF4")
plt.tight_layout()
out = FINAL / "figures" / "replication.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"Saved → {out}")
