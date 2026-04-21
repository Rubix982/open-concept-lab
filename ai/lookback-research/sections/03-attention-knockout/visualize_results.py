"""
Attention Knockout — visualize pre-computed accuracy drop results.

Reads from results/attn_knockout/
No model or API keys needed.
"""

import json
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "attn_knockout"

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Types
# =============================================================================

class KnockoutResult(NamedTuple):
    name:         str
    label:        str
    color:        str
    layers:       list[int]
    acc_drops:    list[float]


# =============================================================================
# Load
# =============================================================================

EXPERIMENTS: dict[str, dict[str, str]] = {
    "secondSent.json": {
        "label": "Block → Sentence 2 tokens",
        "color": "#FF9800",
    },
    "firstVisSent.json": {
        "label": "Block → First visibility sentence",
        "color": "#2196F3",
    },
    "secondSent_firstVisSent.json": {
        "label": "Block → BOTH (Sent 2 + Vis 1)",
        "color": "#9C27B0",
    },
}


def load_knockout(fname: str) -> KnockoutResult:
    meta  = EXPERIMENTS[fname]
    data: dict[str, float] = json.load(open(RESULTS_ROOT / fname))
    layers = sorted(int(k) for k in data.keys())
    drops  = [data[str(l)] for l in layers]
    return KnockoutResult(
        name=fname, label=meta["label"], color=meta["color"],
        layers=layers, acc_drops=drops,
    )


results: list[KnockoutResult] = [load_knockout(f) for f in EXPERIMENTS]


# =============================================================================
# Plot 1 — Accuracy drop by layer, all three experiments
# =============================================================================

fig, ax = plt.subplots(figsize=(13, 5))
ax.set_title(
    "Attention Knockout — Accuracy Drop by Layer\n"
    "How much does model accuracy fall when specific attention paths are blocked?",
    fontsize=12
)

for r in results:
    ax.plot(r.layers, r.acc_drops,
            marker="o", markersize=4, linewidth=2.5,
            color=r.color, label=r.label)
    ax.fill_between(r.layers, r.acc_drops, alpha=0.08, color=r.color)

# Mark the critical transition region
ax.axvspan(22, 34, alpha=0.07, color="red", label="Critical window (L22–34)")
ax.axhline(0.5, color="gray", linestyle=":", linewidth=1, alpha=0.5)
ax.text(22.3, 1.06, "Critical\nwindow", fontsize=8, color="red", alpha=0.7)

ax.set_xlabel("Layer (knockout applied at this layer)", fontsize=10)
ax.set_ylabel("Accuracy Drop", fontsize=10)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "attn_knockout_drop_by_layer.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Early vs combined: the redundancy effect
# =============================================================================

fig2, axes = plt.subplots(1, 2, figsize=(14, 5))
fig2.suptitle("Attention Knockout — Redundancy and Early Effects", fontsize=12)

# Left: early layers zoom (0-30)
ax_l = axes[0]
ax_l.set_title("Early layers (0–30): first vis sentence has early effect", fontsize=10)
for r in results:
    early_idx  = [i for i, l in enumerate(r.layers) if l <= 30]
    layers_e   = [r.layers[i] for i in early_idx]
    drops_e    = [r.acc_drops[i] for i in early_idx]
    ax_l.plot(layers_e, drops_e,
              marker="o", markersize=5, linewidth=2,
              color=r.color, label=r.label)

ax_l.axvspan(1, 6, alpha=0.1, color="#2196F3",
             label="Early vis effect (layers 1-6)")
ax_l.set_xlabel("Layer", fontsize=9)
ax_l.set_ylabel("Accuracy Drop", fontsize=9)
ax_l.set_ylim(0, 1.1)
ax_l.legend(fontsize=8)
ax_l.grid(axis="y", alpha=0.3)

# Right: combined vs individual — redundancy gap
ax_r = axes[1]
ax_r.set_title("Combined knockout delayed — evidence of path redundancy", fontsize=10)

r_s2    = results[0]  # secondSent
r_vis   = results[1]  # firstVisSent
r_both  = results[2]  # combined

# Interpolate to common grid
all_layers = sorted(set(r_s2.layers + r_vis.layers + r_both.layers))
layer_arr  = np.array(all_layers)

s2_interp   = np.interp(layer_arr, r_s2.layers, r_s2.acc_drops)
vis_interp  = np.interp(layer_arr, r_vis.layers, r_vis.acc_drops)
both_interp = np.interp(layer_arr, r_both.layers, r_both.acc_drops)

ax_r.plot(layer_arr, s2_interp,   color=r_s2.color,   linewidth=2, label=r_s2.label)
ax_r.plot(layer_arr, vis_interp,  color=r_vis.color,  linewidth=2, label=r_vis.label)
ax_r.plot(layer_arr, both_interp, color=r_both.color, linewidth=2,
          linestyle="--", label=r_both.label)

# Show where combined lags behind each individual
ax_r.fill_between(layer_arr,
                  np.maximum(s2_interp, vis_interp),
                  both_interp,
                  where=np.maximum(s2_interp, vis_interp) > both_interp,
                  alpha=0.15, color="gray",
                  label="Gap = redundancy (combined < individual)")

ax_r.set_xlabel("Layer", fontsize=9)
ax_r.set_ylabel("Accuracy Drop", fontsize=9)
ax_r.set_ylim(0, 1.1)
ax_r.legend(fontsize=8)
ax_r.grid(axis="y", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "attn_knockout_redundancy.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Timeline: when each path becomes critical (drop > 0.5)
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(13, 3))
ax3.set_title("Attention Path Criticality — When Drop Exceeds 0.5", fontsize=11)

for i, r in enumerate(results):
    critical = [l for l, d in zip(r.layers, r.acc_drops) if d > 0.5]
    if critical:
        ax3.barh(i, max(critical) - min(critical), left=min(critical),
                 height=0.5, color=r.color, alpha=0.8)
        ax3.text(min(critical) + 0.5, i,
                 f"  L{min(critical)}–{max(critical)}",
                 va="center", fontsize=9, color="white", fontweight="bold")

ax3.set_yticks(range(len(results)))
ax3.set_yticklabels([r.label for r in results], fontsize=9)
ax3.set_xlabel("Layer", fontsize=10)
ax3.set_xlim(0, 80)
ax3.grid(axis="x", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "attn_knockout_timeline.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary
# =============================================================================

print("=" * 60)
print("ATTENTION KNOCKOUT — SUMMARY")
print("=" * 60)

for r in results:
    peak      = max(r.acc_drops)
    peak_l    = r.layers[r.acc_drops.index(peak)]
    critical  = [l for l, d in zip(r.layers, r.acc_drops) if d > 0.5]
    rng       = f"L{min(critical)}–{max(critical)}" if critical else "none"
    print(f"  {r.label}")
    print(f"    peak drop={peak:.2f} @ layer {peak_l}  |  critical={rng}")
    print()
