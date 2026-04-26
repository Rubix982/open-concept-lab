"""
Baseline comparison demo — visualize the specificity-generalization tradeoff
and simulate what each editing method does to a weight matrix.

No model required. Uses synthetic data + actual results from Table 4 of the paper.

Run with: python sections/rome/04-baselines/demo.py
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Actual results from Table 4 (CounterFact, GPT-2 XL)
# =============================================================================

class EditResult(NamedTuple):
    name:        str
    score:       float   # harmonic mean of ES, PS, NS
    efficacy:    float   # ES — did the edit work?
    paraphrase:  float   # PS — does it generalize to rephrasing?
    specificity: float   # NS — are neighboring facts preserved?
    color:       str
    approach:    str     # "fine-tuning" / "hypernetwork" / "algebraic"


results: list[EditResult] = [
    EditResult("GPT-2 XL\n(no edit)", 30.5, 22.2, 24.7, 78.1, "#9E9E9E", "baseline"),
    EditResult("FT",        65.1, 100.0, 87.9, 46.6, "#F44336", "fine-tuning"),
    EditResult("FT+L",      66.9,  99.1, 48.7, 65.7, "#FF7043", "fine-tuning"),
    EditResult("KE",        52.2,  84.3, 75.4, 55.7, "#FF9800", "hypernetwork"),
    EditResult("KE-CF",     18.1,  99.9, 95.8,  9.1, "#FFC107", "hypernetwork"),
    EditResult("MEND",      57.9,  99.1, 65.4, 63.8, "#8BC34A", "hypernetwork"),
    EditResult("MEND-CF",   14.9, 100.0, 97.0,  5.7, "#CDDC39", "hypernetwork"),
    EditResult("ROME",      89.2, 100.0, 96.4, 72.4, "#1565C0", "algebraic"),
]


# =============================================================================
# Plot 1 — The three metrics side by side for every method
# =============================================================================

fig: Figure
axes: np.ndarray
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle(
    "ROME vs Baselines — CounterFact Results (GPT-2 XL)\n"
    "The tradeoff: every method before ROME sacrifices efficacy, paraphrase, or specificity",
    fontsize=13,
)

metrics: list[tuple[str, str]] = [
    ("efficacy",    "Efficacy (ES)\n'Did the edit work?'"),
    ("paraphrase",  "Paraphrase (PS)\n'Does it generalize?'"),
    ("specificity", "Specificity (NS)\n'Are neighbors preserved?'"),
]

names: list[str]   = [r.name for r in results]
colors: list[str]  = [r.color for r in results]
x: np.ndarray      = np.arange(len(results))

for ax, (metric, title) in zip(axes.flat, metrics):
    ax: Axes
    vals: list[float] = [getattr(r, metric) for r in results]
    bars = ax.bar(x, vals, color=colors, alpha=0.85, width=0.6)

    # Annotate ROME bar
    rome_idx: int = names.index("ROME")
    ax.bar(x[rome_idx:rome_idx+1], [vals[rome_idx]],
           color=colors[rome_idx], alpha=0.85, width=0.6,
           edgecolor="black", linewidth=2)

    ax.set_title(title, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=30, ha="right")
    ax.set_ylim(0, 115)
    ax.set_ylabel("Score (%)", fontsize=9)
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.4)
    ax.grid(axis="y", alpha=0.3)

    # Label bars
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val:.0f}", ha="center", va="bottom", fontsize=7.5)

plt.tight_layout()
out1: Path = OUT_DIR / "baseline_metrics.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Specificity vs Paraphrase scatter (the tradeoff)
# =============================================================================

fig2: Figure
ax2: Axes
fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.set_title(
    "The Specificity–Generalization Tradeoff\n"
    "Top-right = ideal. Every method before ROME stays bottom-left.",
    fontsize=12,
)

for r in results:
    ax2.scatter(r.specificity, r.paraphrase,
                s=300 if r.name == "ROME" else 150,
                color=r.color, zorder=3,
                edgecolors="black" if r.name == "ROME" else "none",
                linewidths=2)
    offset_x: float = 1.5
    offset_y: float = 1.5
    if r.name == "KE-CF":
        offset_y = -4
    if r.name == "MEND-CF":
        offset_y = -4
    ax2.annotate(
        r.name,
        (r.specificity, r.paraphrase),
        xytext=(r.specificity + offset_x, r.paraphrase + offset_y),
        fontsize=9,
        color=r.color if r.name != "GPT-2 XL\n(no edit)" else "#555",
        fontweight="bold" if r.name == "ROME" else "normal",
    )

# Draw quadrant lines
ax2.axvline(70, color="gray", linestyle=":", linewidth=1, alpha=0.5)
ax2.axhline(85, color="gray", linestyle=":", linewidth=1, alpha=0.5)
ax2.text(71, 86, "Ideal zone", fontsize=9, color="gray", alpha=0.7)

ax2.set_xlabel("Specificity (NS) — neighboring facts preserved (%)", fontsize=11)
ax2.set_ylabel("Paraphrase (PS) — edit generalizes to rephrasing (%)", fontsize=11)
ax2.set_xlim(0, 105)
ax2.set_ylim(0, 105)
ax2.grid(alpha=0.3)

# Legend for approach types
legend_patches: list[mpatches.Patch] = [
    mpatches.Patch(color="#9E9E9E", label="Baseline (no edit)"),
    mpatches.Patch(color="#F44336", label="Fine-tuning (FT, FT+L)"),
    mpatches.Patch(color="#FF9800", label="Hypernetwork (KE, MEND)"),
    mpatches.Patch(color="#1565C0", label="ROME (algebraic)"),
]
ax2.legend(handles=legend_patches, fontsize=9, loc="lower right")

plt.tight_layout()
out2: Path = OUT_DIR / "specificity_generalization_tradeoff.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Simulate what each method does to the weight matrix
# =============================================================================

np.random.seed(42)
D_OUT, D_IN = 8, 12   # toy W shape

# Simulate W with "fact directions" for different subjects
W: np.ndarray = np.random.randn(D_OUT, D_IN) * 0.3

# Subject key directions
k_steve:  np.ndarray = np.array([1.0, 0.2, -0.3, 0.8, 0.1, -0.1, 0.4, 0.2, -0.2, 0.5, 0.1, 0.0])
k_bill:   np.ndarray = np.array([0.1, 0.9,  0.2, 0.1, 0.8,  0.3, 0.1, 0.7, -0.1, 0.1, 0.6, 0.2])
k_paris:  np.ndarray = np.array([-0.2, 0.1, 0.9, 0.0, -0.1, 0.8, 0.0, 0.1, 0.7, -0.2, 0.0, 0.9])

k_steve  /= np.linalg.norm(k_steve)
k_bill   /= np.linalg.norm(k_bill)
k_paris  /= np.linalg.norm(k_paris)

def ft_update(W: np.ndarray, k: np.ndarray, lr: float = 0.8) -> np.ndarray:
    """FT: gradient-based, touches everything."""
    # Simulate gradient: outer product of target residual and key
    target_residual: np.ndarray = np.random.randn(D_OUT) * 0.5
    gradient: np.ndarray = np.outer(target_residual, k)  # (D_OUT, D_IN)
    return W + lr * gradient

def rome_update(W: np.ndarray, k: np.ndarray,
                C_inv: np.ndarray) -> np.ndarray:
    """ROME: rank-one update along whitened key direction."""
    u: np.ndarray = C_inv @ k
    u /= np.linalg.norm(u)
    # Desired output change
    delta: np.ndarray = np.random.randn(D_OUT) * 0.5
    cur_out: np.ndarray = W @ k
    Lambda: np.ndarray  = (cur_out + delta - cur_out) / (k @ u)
    return W + np.outer(Lambda, u)

# Compute toy inverse covariance from many random keys
random_keys: np.ndarray = np.random.randn(D_IN, 300)
C: np.ndarray     = random_keys @ random_keys.T / 300
C_inv: np.ndarray = np.linalg.inv(C + 1e-3 * np.eye(D_IN))

W_ft:   np.ndarray = ft_update(W.copy(),   k_steve, lr=0.5)
W_rome: np.ndarray = rome_update(W.copy(), k_steve, C_inv)

def output_change(W_orig: np.ndarray,
                  W_new: np.ndarray,
                  k: np.ndarray) -> float:
    return float(np.linalg.norm(W_new @ k - W_orig @ k))

fig3: Figure
axes3: np.ndarray
fig3, axes3 = plt.subplots(1, 3, figsize=(15, 5))
fig3.suptitle(
    "What Each Method Does to the Weight Matrix\n"
    "Columns = input dimensions. Rows = output dimensions. Color = magnitude of change.",
    fontsize=12,
)

for ax, (W_new, title) in zip(axes3.flat, [
    (W,       "Original W\n(no edit)"),
    (W_ft,    "W after FT\n(gradient-based)"),
    (W_rome,  "W after ROME\n(rank-one update)"),
]):
    ax: Axes
    diff: np.ndarray = np.abs(W_new - W)
    im = ax.imshow(diff, cmap="Reds", aspect="auto",
                   vmin=0, vmax=np.abs(W_ft - W).max())
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="|ΔW|")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Input dim (key space)", fontsize=8)
    ax.set_ylabel("Output dim (value space)", fontsize=8)

# Annotate change magnitudes for each subject
for ax, W_new in [(axes3[1], W_ft), (axes3[2], W_rome)]:
    ax: Axes
    for k, label, y in [(k_steve, "Steve", 0.5),
                         (k_bill,  "Bill",  1.5),
                         (k_paris, "Paris", 2.5)]:
        change: float = output_change(W, W_new, k)
        ax.text(D_IN + 0.3, y, f"{label}: Δ={change:.3f}",
                fontsize=8, va="center", color="black")

plt.tight_layout()
out3: Path = OUT_DIR / "weight_matrix_comparison.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Print summary table
# =============================================================================

print("\n" + "=" * 70)
print("RESULTS TABLE (CounterFact, GPT-2 XL)")
print("=" * 70)
print(f"  {'Method':<14} {'Score':>7} {'Efficacy':>10} {'Paraphrase':>12} {'Specificity':>13}")
print("-" * 70)
for r in results:
    flag: str = " ← BEST" if r.name == "ROME" else ""
    print(f"  {r.name:<14} {r.score:>7.1f} {r.efficacy:>10.1f} {r.paraphrase:>12.1f} {r.specificity:>13.1f}{flag}")

print("""
Key observations:
  FT:      100% efficacy but specificity drops to 46.6% — bleeds badly
  KE-CF:   99.9% efficacy, 95.8% paraphrase BUT specificity = 9.1% (destroyed)
  MEND-CF: same story — distribution training = aggressive editing = no specificity
  ROME:    100% efficacy, 96.4% paraphrase, 72.4% specificity — best score by far
""")
