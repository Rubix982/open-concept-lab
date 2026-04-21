"""
Binding Lookback — visualize pre-computed IIA results.

Reads from results/causalToM_novis/Meta-Llama-3-70B-Instruct/binding_lookback/
No model or API keys needed.
"""

import json
import os
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RESULTS_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis" / \
    "Meta-Llama-3-70B-Instruct" / "binding_lookback"

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Types
# =============================================================================

class ExperimentResult(NamedTuple):
    name:        str
    label:       str
    color:       str
    group:       str       # source / pointer / binding / control
    layers:      list[int]
    iia_scores:  list[float]


# =============================================================================
# Load
# =============================================================================

EXPERIMENT_META: dict[str, dict[str, str]] = {
    "character_oi":           {"label": "Source: Char OI",        "color": "#2196F3", "group": "source"},
    "object_oi":              {"label": "Source: Obj OI",         "color": "#FF9800", "group": "source"},
    "pointer_character":      {"label": "Pointer: Char (Q)",      "color": "#1565C0", "group": "pointer"},
    "pointer_object":         {"label": "Pointer: Obj (Q)",       "color": "#E65100", "group": "pointer"},
    "pointer_charac_and_object": {"label": "Pointer: Both (Q)",   "color": "#6A1B9A", "group": "pointer"},
    "address_and_payload":    {"label": "Address+Payload (State)","color": "#2E7D32", "group": "binding"},
    "source_1":               {"label": "Source w/ frozen state", "color": "#00796B", "group": "source"},
    "source_2":               {"label": "Source w/o frozen state","color": "#B71C1C", "group": "control"},
}


def load_experiment(folder: str) -> ExperimentResult:
    path = RESULTS_ROOT / folder
    meta = EXPERIMENT_META[folder]
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        scores.append(data["full_rank"]["accuracy"])
    return ExperimentResult(
        name=folder, label=meta["label"], color=meta["color"],
        group=meta["group"], layers=layers, iia_scores=scores,
    )


experiments: dict[str, ExperimentResult] = {
    name: load_experiment(name) for name in EXPERIMENT_META
}


# =============================================================================
# Plot 1 — All experiments on one canvas (overview)
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle("Binding Lookback — IIA by Layer (Llama-3-70B-Instruct)", fontsize=14)

groups: dict[str, list[str]] = {
    "Source OIDs (story tokens)":      ["character_oi", "object_oi", "source_1", "source_2"],
    "Pointers (question tokens)":      ["pointer_character", "pointer_object", "pointer_charac_and_object"],
    "Binding (state token)":           ["address_and_payload"],
    "All experiments together":        list(EXPERIMENT_META.keys()),
}

for ax, (title, names) in zip(axes.flat, groups.items()):
    for name in names:
        exp = experiments[name]
        ax.plot(exp.layers, exp.iia_scores,
                marker="o", markersize=3, linewidth=2,
                color=exp.color, label=exp.label)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Layer", fontsize=9)
    ax.set_ylabel("IIA", fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1, alpha=0.4)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out = OUT_DIR / "binding_lookback_iia_overview.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"Saved: {out}")
plt.close()


# =============================================================================
# Plot 2 — Temporal pipeline: stacked area showing WHEN each mechanism is live
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(14, 5))
ax2.set_title(
    "Binding Lookback — Temporal Pipeline\n"
    "When is each component causally active? (IIA > 0.5 = active)",
    fontsize=12
)

pipeline_order: list[str] = [
    "character_oi",
    "pointer_character",
    "object_oi",
    "pointer_object",
    "source_1",
    "address_and_payload",
]

all_layers = sorted({l for exp in experiments.values() for l in exp.layers})
layer_arr = np.array(all_layers)

for i, name in enumerate(pipeline_order):
    exp = experiments[name]
    # Interpolate to common layer axis
    iia_interp = np.interp(layer_arr, exp.layers, exp.iia_scores)
    # Draw filled region where IIA > 0.5
    active = iia_interp.copy()
    active[active < 0.5] = 0
    ax2.fill_between(layer_arr, i, i + active * 0.8,
                     alpha=0.7, color=exp.color, label=exp.label)
    ax2.axhline(i, color="lightgray", linewidth=0.5)

ax2.set_xlabel("Layer", fontsize=10)
ax2.set_yticks(range(len(pipeline_order)))
ax2.set_yticklabels([experiments[n].label for n in pipeline_order], fontsize=9)
ax2.set_xlim(layer_arr[0], layer_arr[-1])
ax2.legend(loc="upper right", fontsize=8)
ax2.grid(axis="x", alpha=0.3)

# Mark the key layer regions
for x, label, c in [(17, "Char OID\nassigned", "#2196F3"),
                     (27, "Obj OID\nassigned", "#FF9800"),
                     (34, "Binding\ncomplete", "#2E7D32")]:
    ax2.axvline(x, color=c, linestyle=":", linewidth=1.5, alpha=0.8)
    ax2.text(x + 0.3, len(pipeline_order) - 0.3, label,
             fontsize=7, color=c, va="top")

plt.tight_layout()
out2 = OUT_DIR / "binding_lookback_pipeline.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — source_1 vs source_2: the control comparison
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.set_title(
    "source_1 vs source_2 — Why the State Token is the Binding Destination\n"
    "source_1: state tokens frozen (clean) | source_2: state tokens free to update",
    fontsize=11
)

for name, style in [("source_1", "-"), ("source_2", "--")]:
    exp = experiments[name]
    ax3.plot(exp.layers, exp.iia_scores,
             linestyle=style, marker="o", markersize=4,
             linewidth=2, color=exp.color, label=exp.label)

ax3.fill_between(
    experiments["source_1"].layers,
    experiments["source_1"].iia_scores,
    experiments["source_2"].iia_scores,
    alpha=0.15, color="#2E7D32",
    label="Gap = causal contribution of state token binding"
)

ax3.set_xlabel("Layer", fontsize=10)
ax3.set_ylabel("IIA", fontsize=10)
ax3.set_ylim(0, 1.1)
ax3.axhline(0.5, color="gray", linestyle=":", linewidth=1, alpha=0.4)
ax3.legend(fontsize=9)
ax3.grid(axis="y", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "binding_lookback_source_comparison.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Print summary table
# =============================================================================

print("\n" + "=" * 65)
print("BINDING LOOKBACK — SUMMARY TABLE")
print("=" * 65)
print(f"{'Experiment':<30} {'Peak IIA':>9} {'Peak Layer':>11} {'Active Range':>15}")
print("-" * 65)

for name, exp in experiments.items():
    peak_iia   = max(exp.iia_scores)
    peak_layer = exp.layers[exp.iia_scores.index(peak_iia)]
    active     = [l for l, s in zip(exp.layers, exp.iia_scores) if s > 0.5]
    rng        = f"{min(active)}–{max(active)}" if active else "none"
    print(f"  {exp.label:<28} {peak_iia:>9.2f} {peak_layer:>11} {rng:>15}")
