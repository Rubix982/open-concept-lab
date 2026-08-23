"""
Visualize ROME edit blast radius: which related neighbours go updated / stale /
broken / fine. Two panels:
  (left)  outcome breakdown by neighbour type (stacked bars)
  (right) blast-radius graph — each edit at a hub, neighbours placed by hop
          distance (ring) and coloured by outcome; the special cases (stale/broken)
          are what we study to learn what must be true to make them "fine".

Reads results/rome_study.json. Run in any venv with matplotlib:
    python experiments/edit_propagation/viz.py
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RES = HERE.parent.parent / "results" / "final"
records = json.loads((RES / "data" / "rome_study.json").read_text())

OUTCOME_COLOR = {"updated": "#6fcf97", "fine": "#4fc3f7",
                 "stale": "#ffb74d", "broken": "#e57373"}
HOP_RING = {"paraphrase": 1, "1hop": 2, "2hop": 3, "reverse": 3.6, "locality": 4.4}
TYPES = ["paraphrase", "1hop", "2hop", "reverse", "locality"]

fig = plt.figure(figsize=(14, 6.5), facecolor="#0a0c0f")

# ── panel 1: stacked outcome bars by type ─────────────────────────────────────
ax1 = fig.add_subplot(1, 2, 1)
ax1.set_facecolor("#0f1318")
order = ["updated", "fine", "stale", "broken"]
present = [t for t in TYPES if any(r["type"] == t for r in records)]
bottoms = np.zeros(len(present))
for oc in order:
    vals = [sum(1 for r in records if r["type"] == t and r["outcome"] == oc) for t in present]
    ax1.barh(present, vals, left=bottoms, color=OUTCOME_COLOR[oc], label=oc, edgecolor="#0a0c0f")
    bottoms += np.array(vals)
ax1.set_title("Neighbour outcome by type (ROME edit)", color="#c8d4e0", fontsize=12)
ax1.tick_params(colors="#8a97a8")
for s in ax1.spines.values():
    s.set_color("#1e2530")
ax1.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0", fontsize=9)

# ── panel 2: blast-radius graph ────────────────────────────────────────────────
ax2 = fig.add_subplot(1, 2, 2, projection="polar")
ax2.set_facecolor("#0f1318")
cases = sorted({r["case"] for r in records})
case_angle = {c: 2 * math.pi * i / max(len(cases), 1) for i, c in enumerate(cases)}
# hub
ax2.scatter([0], [0], s=260, c="#e8dcc8", marker="*", zorder=5)
# spread neighbours of a case around its angle
by_case = defaultdict(list)
for r in records:
    by_case[r["case"]].append(r)
for c, recs in by_case.items():
    base = case_angle[c]
    for j, r in enumerate(recs):
        ang = base + (j - len(recs) / 2) * 0.05
        rad = HOP_RING.get(r["type"], 4)
        ax2.scatter([ang], [rad], s=90, c=OUTCOME_COLOR[r["outcome"]],
                    edgecolors="#0a0c0f", linewidths=0.6, zorder=3)
ax2.set_ylim(0, 5)
ax2.set_yticks([1, 2, 3, 4.4])
ax2.set_yticklabels(["paraphrase", "1-hop", "2-hop", "locality"], color="#8a97a8", fontsize=8)
ax2.set_xticks([])
ax2.set_title("Edit blast radius — ✦ = edit, rings = hop distance\n"
              "green=updated blue=fine amber=stale red=broken",
              color="#c8d4e0", fontsize=11, pad=18)
ax2.grid(color="#1e2530")

fig.suptitle("ROME edit: effect on related neighbours (stale/broken = what to study)",
             color="#e8dcc8", fontsize=13)
out = RES / "figures" / "rome_blast_radius.png"
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
print(f"Saved → {out}")

# ── the special cases to study ────────────────────────────────────────────────
print("\n── STALE / BROKEN neighbours (the cases to turn 'fine') ──")
for r in records:
    if r["outcome"] in ("stale", "broken"):
        print(f"  [{r['outcome']:6s}] {r['type']:10s} {r['prompt'][:48]!r}")
        print(f"           wanted {r['new']!r}, got {r['post'][:24]!r} (was {r['pre'][:16]!r})")
