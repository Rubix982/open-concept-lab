"""
Cross-model visibility lookback — compare IIA windows across three models.
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

BASE    = Path(__file__).parent.parent.parent / "belief_tracking" / "results" / "causalToM_vis"
OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)

MODELS: dict[str, tuple[str, int, str]] = {
    "Llama-3-70B":    ("Meta-Llama-3-70B-Instruct",          80,  "#1565C0"),
    "Llama-3.1-405B": ("Meta-Llama-3.1-405B-Instruct-8bit",  126, "#2E7D32"),
    "Qwen2.5-14B":    ("Qwen2.5-14B-Instruct",               48,  "#B71C1C"),
}

EXPERIMENTS: list[tuple[str, str]] = [
    ("visibility_lookback/source",             "Vis Source"),
    ("visibility_lookback/address_and_pointer","Vis Addr+Pointer"),
    ("visibility_lookback/payload",            "Vis Payload"),
]


class ModelResult(NamedTuple):
    label:        str
    total_layers: int
    color:        str
    layers:       list[int]
    iia_scores:   list[float]


def load(model_label: str, exp_path: str) -> ModelResult | None:
    model_dir, total, color = MODELS[model_label]
    path = BASE / model_dir / exp_path
    if not path.exists():
        return None
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        scores.append(data["full_rank"]["accuracy"])
    return ModelResult(model_label, total, color, layers, scores)


# =============================================================================
# Plot 1 — IIA curves: three experiments, three models
# =============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("Visibility Lookback — Cross-Model IIA Comparison\n"
             "Source / Address+Pointer / Payload across three architectures",
             fontsize=13)

for ax, (exp_path, exp_label) in zip(axes, EXPERIMENTS):
    for model_label in MODELS:
        r = load(model_label, exp_path)
        if r is None:
            continue
        ax.plot(r.layers, r.iia_scores,
                linewidth=2.5, color=r.color,
                marker="o", markersize=3,
                label=f"{r.label} ({r.total_layers}L)")
        ax.fill_between(r.layers, r.iia_scores, alpha=0.08, color=r.color)
    ax.set_title(exp_label, fontsize=11)
    ax.set_xlabel("Layer", fontsize=9)
    ax.set_ylabel("IIA", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "vis_cross_model_iia.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Timeline: proportional depth, visibility only
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(14, 5))
ax2.set_title(
    "Visibility Lookback — Active Windows (IIA > 0.5), Proportional Depth\n"
    "Solid = Llama-70B | Medium = Llama-405B | Thin = Qwen-14B",
    fontsize=12
)

heights = [0.5, 0.35, 0.2]
model_labels = list(MODELS.keys())

for i, (exp_path, exp_label) in enumerate(EXPERIMENTS):
    y_base = i * 1.2
    for j, model_label in enumerate(model_labels):
        r = load(model_label, exp_path)
        if r is None:
            continue
        _, total, color = MODELS[model_label]
        active = [l for l, s in zip(r.layers, r.iia_scores) if s > 0.5]
        if not active:
            continue
        start_pct = min(active) / total * 100
        end_pct   = max(active) / total * 100
        ax2.barh(y_base + j * 0.35, end_pct - start_pct,
                 left=start_pct, height=0.3,
                 color=color, alpha=0.85)
        ax2.text(start_pct + 0.5, y_base + j * 0.35,
                 f"  {start_pct:.0f}–{end_pct:.0f}%",
                 va="center", fontsize=8, color="white", fontweight="bold")

ax2.set_yticks([i * 1.2 + 0.35 for i in range(len(EXPERIMENTS))])
ax2.set_yticklabels([e[1] for e in EXPERIMENTS], fontsize=10)
ax2.set_xlabel("Proportional Depth (% of total layers)", fontsize=10)
ax2.set_xlim(0, 105)
ax2.axvline(50, color="gray", linestyle="--", linewidth=1, alpha=0.4)

patches = [mpatches.Patch(color=MODELS[m][2], label=m) for m in model_labels]
ax2.legend(handles=patches, fontsize=9, loc="upper right")
ax2.grid(axis="x", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "vis_cross_model_timeline.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Gap width comparison across models
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.set_title("Vulnerability Gap: Layers Between Source End and Payload Start\n"
              "Narrower = more robust transition", fontsize=11)

gap_data: dict[str, tuple[int, float]] = {}
for model_label in model_labels:
    _, total, color = MODELS[model_label]
    src = load(model_label, "visibility_lookback/source")
    pay = load(model_label, "visibility_lookback/payload")
    if src and pay:
        src_active = [l for l, s in zip(src.layers, src.iia_scores) if s > 0.5]
        pay_active = [l for l, s in zip(pay.layers, pay.iia_scores) if s > 0.5]
        if src_active and pay_active:
            gap_abs = min(pay_active) - max(src_active)
            gap_pct = gap_abs / total * 100
            gap_data[model_label] = (gap_abs, gap_pct)

x = np.arange(len(gap_data))
labels = list(gap_data.keys())
abs_gaps = [gap_data[m][0] for m in labels]
pct_gaps = [gap_data[m][1] for m in labels]
colors   = [MODELS[m][2] for m in labels]

bars = ax3.bar(x, abs_gaps, color=colors, alpha=0.85, width=0.4)
for i, (bar, pct) in enumerate(zip(bars, pct_gaps)):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
             f"{pct:.0f}% of depth", ha="center", fontsize=10, fontweight="bold")

ax3.set_xticks(x)
ax3.set_xticklabels(labels, fontsize=10)
ax3.set_ylabel("Gap width (absolute layers)", fontsize=10)
ax3.set_ylim(0, max(abs_gaps) * 1.3)
ax3.grid(axis="y", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "vis_gap_width.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary
# =============================================================================

print("=" * 70)
print("CROSS-MODEL VISIBILITY LOOKBACK SUMMARY")
print("=" * 70)
print(f"  {'Experiment':<22} {'70B':>18} {'405B':>18} {'Qwen':>18}")
print("-" * 70)

for exp_path, exp_label in EXPERIMENTS:
    row = f"  {exp_label:<22}"
    for model_label in model_labels:
        r = load(model_label, exp_path)
        if r is None:
            row += f"{'n/a':>18}"
            continue
        _, total, _ = MODELS[model_label]
        active = [l for l, s in zip(r.layers, r.iia_scores) if s > 0.5]
        s = f"L{min(active)}-{max(active)} ({min(active)/total*100:.0f}-{max(active)/total*100:.0f}%)" if active else "none"
        row += f"{s:>18}"
    print(row)

print()
print("  Vulnerability gaps (source end → payload start):")
for m, (gap_abs, gap_pct) in gap_data.items():
    print(f"    {m:<25}: {gap_abs} layers ({gap_pct:.0f}% of depth)")
