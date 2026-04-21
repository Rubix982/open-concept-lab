"""
Cross-model replication — compare IIA windows across three models.

Reads from results/causalToM_novis/ for all three models.
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

BASE = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis"

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# Model definitions
# =============================================================================

MODELS: dict[str, tuple[str, int, str]] = {
    "Llama-3-70B":    ("Meta-Llama-3-70B-Instruct",          80,  "#1565C0"),
    "Llama-3.1-405B": ("Meta-Llama-3.1-405B-Instruct-8bit",  126, "#2E7D32"),
    "Qwen2.5-14B":    ("Qwen2.5-14B-Instruct",               48,  "#B71C1C"),
}

EXPERIMENTS: list[tuple[str, str]] = [
    ("binding_lookback/address_and_payload", "Binding: addr+payload"),
    ("binding_lookback/character_oi",        "Binding: char OI"),
    ("binding_lookback/object_oi",           "Binding: obj OI"),
    ("binding_lookback/pointer_character",   "Pointer: char (Q)"),
    ("binding_lookback/source_1",            "Source (frozen state)"),
    ("answer_lookback/pointer",              "Answer: pointer"),
    ("answer_lookback/payload",              "Answer: payload"),
]


# =============================================================================
# Types + loader
# =============================================================================

class ModelResult(NamedTuple):
    model_label:  str
    total_layers: int
    color:        str
    layers:       list[int]
    iia_scores:   list[float]


def load(model_label: str, exp_path: str) -> ModelResult | None:
    model_dir, total_layers, color = MODELS[model_label]
    path = BASE / model_dir / exp_path
    if not path.exists():
        return None
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        scores.append(data["full_rank"]["accuracy"])
    return ModelResult(model_label, total_layers, color, layers, scores)


# =============================================================================
# Plot 1 — IIA side-by-side for all experiments (absolute layers)
# =============================================================================

fig, axes = plt.subplots(3, 3, figsize=(18, 14))
fig.suptitle("Cross-Model IIA Comparison — Absolute Layer Positions\n"
             "Llama-3-70B (80L) | Llama-3.1-405B (126L) | Qwen2.5-14B (48L)",
             fontsize=13)

for ax, (exp_path, exp_label) in zip(axes.flat, EXPERIMENTS):
    for model_label in MODELS:
        result = load(model_label, exp_path)
        if result is None:
            continue
        ax.plot(result.layers, result.iia_scores,
                linewidth=2, color=result.color,
                marker="o", markersize=2,
                label=f"{model_label} ({result.total_layers}L)")
        ax.fill_between(result.layers, result.iia_scores,
                        alpha=0.06, color=result.color)
    ax.set_title(exp_label, fontsize=10)
    ax.set_xlabel("Layer", fontsize=8)
    ax.set_ylabel("IIA", fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.3)

# Hide the last unused subplot
axes.flat[-1].set_visible(False)

plt.tight_layout()
out1 = OUT_DIR / "cross_model_iia_absolute.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Proportional depth: normalise layer to 0-100%
# =============================================================================

fig2, axes2 = plt.subplots(2, 3, figsize=(18, 10))
fig2.suptitle("Cross-Model IIA — Proportional Depth (layer / total_layers)\n"
              "Do mechanisms fire at the same relative position?",
              fontsize=13)

key_experiments = [
    ("binding_lookback/character_oi",        "Binding: char OI"),
    ("binding_lookback/object_oi",           "Binding: obj OI"),
    ("binding_lookback/address_and_payload", "Binding: addr+payload"),
    ("binding_lookback/source_1",            "Source (frozen state)"),
    ("answer_lookback/pointer",              "Answer: pointer"),
    ("answer_lookback/payload",              "Answer: payload"),
]

for ax, (exp_path, exp_label) in zip(axes2.flat, key_experiments):
    for model_label in MODELS:
        result = load(model_label, exp_path)
        if result is None:
            continue
        # Normalise to 0-100%
        pct_layers = [l / result.total_layers * 100 for l in result.layers]
        ax.plot(pct_layers, result.iia_scores,
                linewidth=2.5, color=result.color,
                marker="o", markersize=3,
                label=f"{model_label} ({result.total_layers}L)")
        ax.fill_between(pct_layers, result.iia_scores,
                        alpha=0.08, color=result.color)
    ax.set_title(exp_label, fontsize=10)
    ax.set_xlabel("Depth (% of total layers)", fontsize=8)
    ax.set_ylabel("IIA", fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "cross_model_iia_proportional.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Timeline: active windows as bars, three models side by side
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(16, 8))
ax3.set_title(
    "Cross-Model Active Windows (IIA > 0.5) — Proportional Depth\n"
    "Each experiment: three bars, one per model",
    fontsize=12
)

n_exp    = len(EXPERIMENTS)
n_models = len(MODELS)
bar_h    = 0.25
gap      = 0.05

model_labels = list(MODELS.keys())
model_colors = [MODELS[m][2] for m in model_labels]

for i, (exp_path, exp_label) in enumerate(EXPERIMENTS):
    y_base = i * (n_models * bar_h + gap * 2)
    for j, model_label in enumerate(model_labels):
        result = load(model_label, exp_path)
        if result is None:
            continue
        _, total_layers, color = MODELS[model_label]
        active = [l for l, s in zip(result.layers, result.iia_scores) if s > 0.5]
        if not active:
            continue
        start_pct = min(active) / total_layers * 100
        end_pct   = max(active) / total_layers * 100
        width_pct = end_pct - start_pct
        y_pos = y_base + j * bar_h
        ax3.barh(y_pos, width_pct, left=start_pct,
                 height=bar_h * 0.85, color=color, alpha=0.85)
        ax3.text(start_pct + 0.5, y_pos,
                 f"  {start_pct:.0f}–{end_pct:.0f}%",
                 va="center", fontsize=7, color="white", fontweight="bold")

# Y axis labels
ytick_positions = [i * (n_models * bar_h + gap * 2) + bar_h
                   for i in range(n_exp)]
ax3.set_yticks(ytick_positions)
ax3.set_yticklabels([e[1] for e in EXPERIMENTS], fontsize=9)

# Legend
patches = [mpatches.Patch(color=c, label=m)
           for m, (_, _, c) in MODELS.items()]
ax3.legend(handles=patches, fontsize=9, loc="lower right")

ax3.set_xlabel("Proportional Depth (% of total layers)", fontsize=10)
ax3.set_xlim(0, 105)
ax3.axvline(50, color="gray", linestyle="--", linewidth=1, alpha=0.4,
            label="50% depth")
ax3.grid(axis="x", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "cross_model_timeline_proportional.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary table
# =============================================================================

print("=" * 90)
print("CROSS-MODEL SUMMARY — Active windows as % of model depth")
print("=" * 90)
print(f"  {'Experiment':<28} {'70B':>18} {'405B':>18} {'Qwen':>18}")
print("-" * 90)

for exp_path, exp_label in EXPERIMENTS:
    row = f"  {exp_label:<28}"
    for model_label in model_labels:
        result = load(model_label, exp_path)
        if result is None:
            row += f"{'n/a':>18}"
            continue
        _, total_layers, _ = MODELS[model_label]
        active = [l for l, s in zip(result.layers, result.iia_scores) if s > 0.5]
        if active:
            s = f"{min(active)/total_layers*100:.0f}%-{max(active)/total_layers*100:.0f}%"
        else:
            s = "none"
        row += f"{s:>18}"
    print(row)

print()
print("Source_2 control (should be near 0 in all models):")
for model_label in model_labels:
    result = load(model_label, "binding_lookback/source_2")
    if result:
        peak = max(result.iia_scores)
        print(f"  {model_label:<25}: max IIA = {peak:.3f}  "
              f"{'✓ near zero' if peak < 0.2 else '✗ above threshold'}")
