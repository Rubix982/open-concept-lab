"""
Model evaluation landscape — behavioral accuracy across 14 models.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT    = Path(__file__).parent.parent.parent / "belief_tracking" / "results" / "model_evaluations"
OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


@dataclass
class ModelResult:
    name:       str
    family:     str
    is_instruct: bool
    novis_mean: float
    novis_std:  float
    vis_mean:   float
    vis_std:    float

    @property
    def vis_gap(self) -> float:
        return self.novis_mean - self.vis_mean

    @property
    def label(self) -> str:
        tag = "Instruct" if self.is_instruct else "Base"
        return f"{self.name} ({tag})"


def load_all() -> list[ModelResult]:
    files = sorted(os.listdir(ROOT))
    raw: dict[str, dict] = {}
    for f in files:
        data = json.load(open(ROOT / f))
        name = f.replace(".json", "")
        is_vis = name.endswith("_vis")
        model  = name.replace("_vis", "")
        raw.setdefault(model, {})[("vis" if is_vis else "novis")] = data

    results = []
    family_map = {
        "Llama-2":    "Llama-2",
        "Llama-3.1":  "Llama-3.x",
        "Meta-Llama-3": "Llama-3.x",
        "Qwen2.5":    "Qwen2.5",
        "OLMo":       "OLMo",
        "gemma":      "Gemma",
    }

    for model, conds in raw.items():
        if "novis" not in conds or "vis" not in conds:
            continue
        family = "Other"
        for prefix, fam in family_map.items():
            if model.startswith(prefix):
                family = fam
                break
        is_instruct = any(k in model for k in ["Instruct", "instruct", "-it"])
        results.append(ModelResult(
            name=model, family=family, is_instruct=is_instruct,
            novis_mean=conds["novis"]["mean"], novis_std=conds["novis"]["std"],
            vis_mean=conds["vis"]["mean"],     vis_std=conds["vis"]["std"],
        ))

    return sorted(results, key=lambda r: r.novis_mean)


results = load_all()
selected = {"Meta-Llama-3-70B-Instruct", "Qwen2.5-14B-Instruct"}


# =============================================================================
# Plot 1 — Grouped bar: no-vis vs vis for all models
# =============================================================================

fig, ax = plt.subplots(figsize=(14, 7))
ax.set_title("CausalToM Behavioral Accuracy — 14 Models\n"
             "No-visibility vs Visibility condition", fontsize=13)

x     = np.arange(len(results))
w     = 0.35
colors_nv = ["#1565C0" if r.is_instruct else "#90CAF9" for r in results]
colors_v  = ["#B71C1C" if r.is_instruct else "#EF9A9A" for r in results]

bars_nv = ax.bar(x - w/2, [r.novis_mean for r in results], w,
                 yerr=[r.novis_std for r in results],
                 color=colors_nv, alpha=0.85, capsize=3,
                 label="No-visibility (dark=instruct)")
bars_v  = ax.bar(x + w/2, [r.vis_mean for r in results], w,
                 yerr=[r.vis_std for r in results],
                 color=colors_v, alpha=0.85, capsize=3,
                 label="Visibility (dark=instruct)")

# Highlight selected models
for i, r in enumerate(results):
    if r.name in selected:
        ax.annotate("★ selected", (x[i], max(r.novis_mean, r.vis_mean) + 0.05),
                    ha="center", fontsize=7.5, color="#2E7D32", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([r.name.replace("Meta-Llama-3-", "Llama-3-")
                    .replace("-Instruct", "\n-Instruct")
                    .replace("Qwen2.5-", "Qwen-")
                    for r in results],
                   rotation=45, ha="right", fontsize=7.5)
ax.set_ylabel("Accuracy (mean ± std)", fontsize=10)
ax.set_ylim(0, 1.15)
ax.axhline(0.90, color="gray", linestyle="--", linewidth=1, alpha=0.5,
           label="0.90 selection threshold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "model_eval_all.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Visibility gap: no-vis minus vis for each model
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(13, 5))
ax2.set_title("Visibility Gap (No-Vis − Vis Accuracy)\n"
              "How much harder is the visibility condition?", fontsize=12)

gap_sorted = sorted(results, key=lambda r: r.vis_gap)
colors_gap = ["#2E7D32" if r.name in selected else
              ("#1565C0" if r.is_instruct else "#90CAF9")
              for r in gap_sorted]

ax2.barh([r.name.replace("Meta-Llama-3-", "Llama-3-").replace("Qwen2.5-", "Qwen-")
          for r in gap_sorted],
         [r.vis_gap for r in gap_sorted],
         color=colors_gap, alpha=0.85)

ax2.axvline(0.10, color="gray", linestyle=":", linewidth=1, alpha=0.5)
ax2.set_xlabel("Accuracy drop (no-vis → vis)", fontsize=10)
ax2.set_xlim(0, 0.55)
ax2.grid(axis="x", alpha=0.3)

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#2E7D32", label="Selected for mechanistic analysis"),
    Patch(facecolor="#1565C0", label="Instruction-tuned"),
    Patch(facecolor="#90CAF9", label="Base model"),
]
ax2.legend(handles=legend_elements, fontsize=9)

plt.tight_layout()
out2 = OUT_DIR / "model_eval_vis_gap.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Scale vs accuracy scatter (instruct models only)
# =============================================================================

scale_map: dict[str, int] = {
    "Llama-2-7b-hf": 7, "Llama-2-13b-hf": 13,
    "Meta-Llama-3-8B": 8, "Meta-Llama-3-8B-Instruct": 8,
    "Llama-3.1-8B": 8, "Llama-3.1-8B-Instruct": 8,
    "Meta-Llama-3-70B-Instruct": 70,
    "Qwen2.5-7B": 7, "Qwen2.5-7B-Instruct": 7,
    "Qwen2.5-14B": 14, "Qwen2.5-14B-Instruct": 14,
    "OLMo-2-1124-13B-Instruct": 13, "OLMo-2-0325-32B-Instruct": 32,
    "gemma-3-27b-it": 27,
}

fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5))
fig3.suptitle("Model Scale vs Accuracy — Does size predict ToM capability?",
              fontsize=12)

family_colors = {"Llama-2": "#795548", "Llama-3.x": "#1565C0",
                 "Qwen2.5": "#B71C1C", "OLMo": "#2E7D32", "Gemma": "#6A1B9A"}

for ax, cond, title in zip(axes3, ["novis_mean", "vis_mean"],
                            ["No-Visibility", "Visibility"]):
    for r in results:
        if r.name not in scale_map:
            continue
        scale  = scale_map[r.name]
        acc    = getattr(r, cond)
        color  = family_colors.get(r.family, "gray")
        marker = "^" if r.is_instruct else "o"
        size   = 120 if r.name in selected else 60
        ax.scatter(scale, acc, c=color, marker=marker, s=size,
                   alpha=0.85, zorder=3)
        ax.annotate(r.name.split("-")[-1].replace("Instruct","I").replace("hf",""),
                    (scale, acc), textcoords="offset points",
                    xytext=(4, 2), fontsize=6.5)

    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Model size (B parameters)", fontsize=9)
    ax.set_ylabel("Accuracy", fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.axhline(0.90, color="gray", linestyle="--", linewidth=1, alpha=0.4)
    ax.grid(alpha=0.3)

# Shared legend
from matplotlib.lines import Line2D
legend_items = [
    Line2D([0],[0], marker="^", color="w", markerfacecolor="gray",
           markersize=9, label="Instruct"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="gray",
           markersize=9, label="Base"),
] + [Patch(facecolor=c, label=f) for f, c in family_colors.items()]
axes3[1].legend(handles=legend_items, fontsize=8, loc="lower right")

plt.tight_layout()
out3 = OUT_DIR / "model_eval_scale_scatter.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary
# =============================================================================

print("=" * 65)
print("MODEL EVALUATION SUMMARY")
print("=" * 65)
print(f"  {'Model':<35} {'No-Vis':>8} {'Vis':>8} {'Gap':>8}")
print("-" * 65)
for r in sorted(results, key=lambda r: -r.novis_mean):
    star = " ★" if r.name in selected else ""
    print(f"  {r.name:<35} {r.novis_mean:>8.2f} {r.vis_mean:>8.2f} "
          f"{r.vis_gap:>8.2f}{star}")
