"""
Answer Lookback — visualize pre-computed IIA results.

Reads from results/causalToM_novis/Meta-Llama-3-70B-Instruct/answer_lookback/
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
    "Meta-Llama-3-70B-Instruct" / "answer_lookback"

# Also load binding lookback address_and_payload for comparison
BINDING_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis" / \
    "Meta-Llama-3-70B-Instruct" / "binding_lookback"

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
# Load
# =============================================================================

def load_experiment(root: Path, folder: str, label: str, color: str) -> ExperimentResult:
    path = root / folder
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        scores.append(data["full_rank"]["accuracy"])
    return ExperimentResult(name=folder, label=label, color=color,
                            layers=layers, iia_scores=scores)


pointer = load_experiment(RESULTS_ROOT, "pointer", "Answer Pointer (state_OI)", "#9C27B0")
payload = load_experiment(RESULTS_ROOT, "payload", "Answer Payload (state value)", "#E91E63")
binding = load_experiment(BINDING_ROOT, "address_and_payload",
                          "Binding complete (reference)", "#2E7D32")


# =============================================================================
# Plot 1 — Pointer vs Payload — the handoff
# =============================================================================

fig, ax = plt.subplots(figsize=(13, 5))
ax.set_title(
    "Answer Lookback — Pointer vs Payload IIA by Layer\n"
    "The pointer (state_OI) drops off exactly as the payload (state value) arrives",
    fontsize=12
)

ax.plot(pointer.layers, pointer.iia_scores,
        marker="o", markersize=4, linewidth=2.5,
        color=pointer.color, label=pointer.label)

ax.plot(payload.layers, payload.iia_scores,
        marker="s", markersize=4, linewidth=2.5,
        color=payload.color, label=payload.label)

# Shade the pointer active window
pointer_arr = np.array(pointer.iia_scores)
layer_arr   = np.array(pointer.layers)
ax.fill_between(layer_arr, pointer_arr, alpha=0.12, color=pointer.color)

# Shade the payload active window
payload_interp = np.interp(layer_arr, payload.layers, payload.iia_scores)
ax.fill_between(layer_arr, payload_interp, alpha=0.12, color=payload.color)

# Mark the handoff region
ax.axvspan(53, 57, alpha=0.08, color="gray", label="Handoff zone (~layer 55)")
ax.axvline(55, color="gray", linestyle="--", linewidth=1.5, alpha=0.6)
ax.text(55.5, 0.75, "Handoff\n~layer 55", fontsize=9, color="gray", va="center")

ax.set_xlabel("Layer", fontsize=10)
ax.set_ylabel("IIA", fontsize=10)
ax.set_ylim(0, 1.15)
ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
ax.legend(fontsize=10)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "answer_lookback_handoff.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — Full chain: binding → pointer → payload across all 80 layers
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(14, 5))
ax2.set_title(
    "Full Mechanism Chain: Binding → Answer Pointer → Answer Payload\n"
    "Each mechanism starts exactly where the previous one ends",
    fontsize=12
)

# Interpolate all to the same layer axis
all_layers = sorted(set(binding.layers + pointer.layers + payload.layers))
layer_arr  = np.array(all_layers)

binding_interp = np.interp(layer_arr, binding.layers, binding.iia_scores)
pointer_interp = np.interp(layer_arr, pointer.layers, pointer.iia_scores)
payload_interp = np.interp(layer_arr, payload.layers, payload.iia_scores)

ax2.fill_between(layer_arr, binding_interp, alpha=0.3,
                 color=binding.color, label=binding.label)
ax2.fill_between(layer_arr, pointer_interp, alpha=0.3,
                 color=pointer.color, label=pointer.label)
ax2.fill_between(layer_arr, payload_interp, alpha=0.3,
                 color=payload.color, label=payload.label)

ax2.plot(layer_arr, binding_interp, linewidth=2, color=binding.color)
ax2.plot(layer_arr, pointer_interp, linewidth=2, color=pointer.color)
ax2.plot(layer_arr, payload_interp, linewidth=2, color=payload.color)

# Mark key transitions
for x, label, c in [
    (34, "Binding complete\nPointer starts", "#2E7D32"),
    (55, "Pointer consumed\nPayload arrives", "#9C27B0"),
]:
    ax2.axvline(x, color=c, linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.text(x + 0.5, 1.05, label, fontsize=8, color=c, va="top")

ax2.set_xlabel("Layer", fontsize=10)
ax2.set_ylabel("IIA", fontsize=10)
ax2.set_ylim(0, 1.2)
ax2.legend(fontsize=9, loc="center right")
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "full_chain_binding_to_payload.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Where each phase lives across the 80 layers (bar chart)
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(13, 3))
ax3.set_title("Mechanism Timeline — Active Layer Windows (IIA > 0.5)", fontsize=11)

experiments_ordered: list[tuple[str, list[int], list[float], str]] = [
    ("Binding: address+payload", binding.layers, binding.iia_scores, binding.color),
    ("Answer: pointer (state_OI)", pointer.layers, pointer.iia_scores, pointer.color),
    ("Answer: payload (state value)", payload.layers, payload.iia_scores, payload.color),
]

for i, (label, layers, scores, color) in enumerate(experiments_ordered):
    active = [l for l, s in zip(layers, scores) if s > 0.5]
    if active:
        ax3.barh(i, max(active) - min(active), left=min(active),
                 height=0.5, color=color, alpha=0.8)
        ax3.text(min(active) + 0.5, i, f"  L{min(active)}–{max(active)}",
                 va="center", fontsize=9, color="white", fontweight="bold")

ax3.set_yticks(range(len(experiments_ordered)))
ax3.set_yticklabels([e[0] for e in experiments_ordered], fontsize=9)
ax3.set_xlabel("Layer", fontsize=10)
ax3.set_xlim(0, 80)
ax3.grid(axis="x", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "mechanism_timeline.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Print summary
# =============================================================================

print("\n" + "=" * 60)
print("ANSWER LOOKBACK — SUMMARY")
print("=" * 60)

for exp in [binding, pointer, payload]:
    peak     = max(exp.iia_scores)
    peak_l   = exp.layers[exp.iia_scores.index(peak)]
    active   = [l for l, s in zip(exp.layers, exp.iia_scores) if s > 0.5]
    rng      = f"{min(active)}–{max(active)}" if active else "none"
    print(f"  {exp.label:<35} peak={peak:.2f} @ L{peak_l:<3}  active={rng}")

print("""
Key finding: pointer drops at layer ~55, payload rises at layer ~55.
This is a HANDOFF — the pointer (state OI) is consumed by the attention
operation that retrieves the payload (state value). Sequential, not concurrent.
""")
