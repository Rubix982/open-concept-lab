"""
BigToM Generalization — visualize IIA results and compare to CausalToM.

Reads from:
  results/bigToM/Meta-Llama-3-70B-Instruct/causal_model/
  results/causalToM_novis/Meta-Llama-3-70B-Instruct/ (for comparison)

No model or API keys needed.
"""

import json
import os
from pathlib import Path
from typing import NamedTuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BIGTOM_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "bigToM" / \
    "Meta-Llama-3-70B-Instruct" / "causal_model"

CAUSAL_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis" / \
    "Meta-Llama-3-70B-Instruct"

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Types
# =============================================================================

class ExperimentResult(NamedTuple):
    name:       str
    label:      str
    color:      str
    layers:     list[int]
    iia_scores: list[float]


# =============================================================================
# Loader
# =============================================================================

def load_iia(root: Path, folder: str, label: str, color: str) -> ExperimentResult:
    path = root / folder
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        if isinstance(data, dict) and "full_rank" in data:
            acc = data["full_rank"]["accuracy"]
        elif isinstance(data, dict) and "accuracy" in data:
            acc = data["accuracy"]
        else:
            acc = float(list(data.values())[0]) if data else 0.0
        layers.append(int(fname.replace(".json", "")))
        scores.append(float(acc))
    return ExperimentResult(name=folder, label=label, color=color,
                            layers=layers, iia_scores=scores)


# BigToM experiments
bt_binding  = load_iia(BIGTOM_ROOT, "binding_lookback/pointer",
                        "BigToM: Binding Pointer", "#FF6F00")
bt_ans_ptr  = load_iia(BIGTOM_ROOT, "answer_lookback/pointer",
                        "BigToM: Answer Pointer", "#7B1FA2")
bt_ans_pay  = load_iia(BIGTOM_ROOT, "answer_lookback/payload",
                        "BigToM: Answer Payload", "#C2185B")
bt_vis_src  = load_iia(BIGTOM_ROOT, "visibility_lookback/source",
                        "BigToM: Vis Source", "#0277BD")
bt_vis_ap   = load_iia(BIGTOM_ROOT, "visibility_lookback/address_and_pointer",
                        "BigToM: Vis Addr+Ptr", "#0288D1")
bt_vis_pay  = load_iia(BIGTOM_ROOT, "visibility_lookback/payload",
                        "BigToM: Vis Payload", "#4FC3F7")

# CausalToM reference experiments
ct_ans_ptr  = load_iia(CAUSAL_ROOT / "answer_lookback", "pointer",
                        "CausalToM: Answer Pointer", "#9C27B0")
ct_ans_pay  = load_iia(CAUSAL_ROOT / "answer_lookback", "payload",
                        "CausalToM: Answer Payload", "#E91E63")
ct_vis_src  = load_iia(CAUSAL_ROOT / "../../causalToM_vis/Meta-Llama-3-70B-Instruct/visibility_lookback",
                        "source", "CausalToM: Vis Source", "#1565C0")
ct_vis_ap   = load_iia(CAUSAL_ROOT / "../../causalToM_vis/Meta-Llama-3-70B-Instruct/visibility_lookback",
                        "address_and_pointer", "CausalToM: Vis Addr+Ptr", "#0288D1")
ct_vis_pay  = load_iia(CAUSAL_ROOT / "../../causalToM_vis/Meta-Llama-3-70B-Instruct/visibility_lookback",
                        "payload", "CausalToM: Vis Payload", "#81D4FA")


# =============================================================================
# Plot 1 — Answer lookback: BigToM vs CausalToM (the strongest claim)
# =============================================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Answer Lookback — BigToM vs CausalToM\n"
             "The mechanism transfers cleanly to real text", fontsize=12)

for ax, (bt, ct, title) in zip(axes, [
    (bt_ans_ptr, ct_ans_ptr, "Answer Pointer"),
    (bt_ans_pay, ct_ans_pay, "Answer Payload"),
]):
    ax.plot(bt.layers, bt.iia_scores, linewidth=2.5, color=bt.color,
            marker="o", markersize=3, label=bt.label)
    ax.plot(ct.layers, ct.iia_scores, linewidth=2.5, color=ct.color,
            linestyle="--", marker="s", markersize=3, label=ct.label)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Layer", fontsize=9)
    ax.set_ylabel("IIA", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "bigtom_answer_lookback_comparison.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Visibility lookback: where BigToM differs most
# =============================================================================

fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))
fig2.suptitle("Visibility Lookback — BigToM vs CausalToM\n"
              "Source and addr+ptr differ significantly; payload similar",
              fontsize=12)

pairs = [
    (bt_vis_src,  ct_vis_src,  "Vis Source"),
    (bt_vis_ap,   ct_vis_ap,   "Vis Address+Pointer"),
    (bt_vis_pay,  ct_vis_pay,  "Vis Payload"),
]

for ax, (bt, ct, title) in zip(axes2, pairs):
    ax.plot(bt.layers, bt.iia_scores, linewidth=2.5, color="#FF6F00",
            marker="o", markersize=3, label=f"BigToM")
    ax.plot(ct.layers, ct.iia_scores, linewidth=2.5, color="#1565C0",
            linestyle="--", marker="s", markersize=3, label=f"CausalToM")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Layer", fontsize=9)
    ax.set_ylabel("IIA", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "bigtom_visibility_comparison.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Timeline: BigToM vs CausalToM active windows
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(14, 6))
ax3.set_title(
    "BigToM vs CausalToM — Active Layer Windows (IIA > 0.5)\n"
    "Solid = BigToM | Dashed outline = CausalToM",
    fontsize=12
)

comparisons: list[tuple[ExperimentResult, ExperimentResult, str]] = [
    (bt_binding,  None,         "Binding Pointer"),
    (bt_ans_ptr,  ct_ans_ptr,   "Answer Pointer"),
    (bt_ans_pay,  ct_ans_pay,   "Answer Payload"),
    (bt_vis_src,  ct_vis_src,   "Vis Source"),
    (bt_vis_ap,   ct_vis_ap,    "Vis Addr+Pointer"),
    (bt_vis_pay,  ct_vis_pay,   "Vis Payload"),
]

colors = ["#FF6F00", "#7B1FA2", "#C2185B", "#0277BD", "#0288D1", "#4FC3F7"]

for i, (bt, ct, label) in enumerate(comparisons):
    bt_active = [l for l, s in zip(bt.layers, bt.iia_scores) if s > 0.5]
    if bt_active:
        ax3.barh(i, max(bt_active) - min(bt_active), left=min(bt_active),
                 height=0.4, color=colors[i], alpha=0.85)
        ax3.text(min(bt_active) + 0.3, i + 0.05,
                 f"  BT: L{min(bt_active)}–{max(bt_active)}",
                 va="center", fontsize=8, color="white", fontweight="bold")

    if ct is not None:
        ct_active = [l for l, s in zip(ct.layers, ct.iia_scores) if s > 0.5]
        if ct_active:
            ax3.barh(i - 0.45, max(ct_active) - min(ct_active),
                     left=min(ct_active), height=0.35,
                     color=colors[i], alpha=0.25,
                     edgecolor=colors[i], linewidth=1.5)
            ax3.text(min(ct_active) + 0.3, i - 0.45,
                     f"  CT: L{min(ct_active)}–{max(ct_active)}",
                     va="center", fontsize=7.5, color=colors[i])

ax3.set_yticks(range(len(comparisons)))
ax3.set_yticklabels([c[2] for c in comparisons], fontsize=9)
ax3.set_xlabel("Layer", fontsize=10)
ax3.set_xlim(0, 80)
ax3.grid(axis="x", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "bigtom_timeline_comparison.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary
# =============================================================================

print("=" * 65)
print("BIGTOM GENERALIZATION — SUMMARY")
print("=" * 65)
print(f"{'Mechanism':<30} {'BigToM':>15} {'CausalToM':>15} {'Match'}")
print("-" * 65)

for bt, ct, label in comparisons:
    bt_active = [l for l, s in zip(bt.layers, bt.iia_scores) if s > 0.5]
    bt_rng = f"L{min(bt_active)}–{max(bt_active)}" if bt_active else "none"
    if ct:
        ct_active = [l for l, s in zip(ct.layers, ct.iia_scores) if s > 0.5]
        ct_rng = f"L{min(ct_active)}–{max(ct_active)}" if ct_active else "none"
        overlap = len(set(bt_active) & set(ct_active))
        match = "✓" if overlap > 5 else "△"
    else:
        ct_rng = "n/a"
        match = "—"
    print(f"  {label:<28} {bt_rng:>15} {ct_rng:>15}  {match}")
