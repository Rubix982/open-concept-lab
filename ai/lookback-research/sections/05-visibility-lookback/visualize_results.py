"""
Visibility Lookback + Attention Knockout — combined visualization.

Reads from:
  results/causalToM_vis/Meta-Llama-3-70B-Instruct/visibility_lookback/
  results/attn_knockout/

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

VIS_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_vis" / \
    "Meta-Llama-3-70B-Instruct" / "visibility_lookback"

BINDING_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis" / \
    "Meta-Llama-3-70B-Instruct" / "binding_lookback"

ANSWER_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "causalToM_novis" / \
    "Meta-Llama-3-70B-Instruct" / "answer_lookback"

KNOCKOUT_ROOT = Path(__file__).parent.parent.parent / \
    "belief_tracking" / "results" / "attn_knockout"

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
# Loaders
# =============================================================================

def load_iia(root: Path, folder: str, label: str, color: str) -> ExperimentResult:
    path = root / folder
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        scores.append(data["full_rank"]["accuracy"])
    return ExperimentResult(name=folder, label=label, color=color,
                            layers=layers, iia_scores=scores)


def load_knockout(fname: str, label: str, color: str) -> ExperimentResult:
    data: dict[str, float] = json.load(open(KNOCKOUT_ROOT / fname))
    layers = sorted(int(k) for k in data.keys())
    scores = [data[str(l)] for l in layers]
    return ExperimentResult(name=fname, label=label, color=color,
                            layers=layers, iia_scores=scores)


# Visibility lookback experiments
vis_source  = load_iia(VIS_ROOT, "source",
                        "Vis: Source (vis_ID generation)", "#1565C0")
vis_addr    = load_iia(VIS_ROOT, "address_and_pointer",
                        "Vis: Address+Pointer", "#0288D1")
vis_payload = load_iia(VIS_ROOT, "payload",
                        "Vis: Payload (state transfer)", "#4FC3F7")

# Reference: binding and answer lookback
binding     = load_iia(BINDING_ROOT, "address_and_payload",
                        "Binding: address+payload", "#2E7D32")
ans_pointer = load_iia(ANSWER_ROOT, "pointer",
                        "Answer: pointer", "#9C27B0")
ans_payload = load_iia(ANSWER_ROOT, "payload",
                        "Answer: payload", "#E91E63")

# Knockout
ko_s2   = load_knockout("secondSent.json",
                         "Knockout: block → Sentence 2", "#FF9800")
ko_vis1 = load_knockout("firstVisSent.json",
                         "Knockout: block → Vis sentence 1", "#F44336")
ko_both = load_knockout("secondSent_firstVisSent.json",
                         "Knockout: block → both", "#B71C1C")


# =============================================================================
# Plot 1 — Visibility lookback IIA: three phases
# =============================================================================

fig, ax = plt.subplots(figsize=(13, 5))
ax.set_title(
    "Visibility Lookback — Three Phases (IIA by Layer)\n"
    "Source fires earliest; address+pointer spans widest; payload follows",
    fontsize=12
)

for exp in [vis_source, vis_addr, vis_payload]:
    arr = np.array(exp.iia_scores)
    ax.plot(exp.layers, exp.iia_scores,
            marker="o", markersize=3, linewidth=2.5,
            color=exp.color, label=exp.label)
    ax.fill_between(exp.layers, exp.iia_scores, alpha=0.1, color=exp.color)

ax.axhline(0.5, color="lightgray", linestyle=":", linewidth=1)
ax.set_xlabel("Layer", fontsize=10)
ax.set_ylabel("IIA", fontsize=10)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=10)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
out1 = OUT_DIR / "visibility_lookback_phases.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close()


# =============================================================================
# Plot 2 — All five mechanisms together: the full pipeline
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(15, 6))
ax2.set_title(
    "Full Belief-Tracking Pipeline: Visibility → Binding → Answer\n"
    "Five mechanisms, sequential layer windows",
    fontsize=12
)

all_exps = [vis_source, vis_addr, vis_payload, binding, ans_pointer, ans_payload]
all_layers = sorted(set(l for e in all_exps for l in e.layers))
layer_arr  = np.array(all_layers)

for exp in all_exps:
    interp = np.interp(layer_arr, exp.layers, exp.iia_scores)
    ax2.fill_between(layer_arr, interp, alpha=0.25, color=exp.color)
    ax2.plot(layer_arr, interp, linewidth=1.8, color=exp.color, label=exp.label)

# Mark key transitions
for x, label, c in [
    (14, "Vis source\npeak", "#1565C0"),
    (34, "Binding\ncomplete", "#2E7D32"),
    (55, "Answer pointer\nconsumed", "#9C27B0"),
]:
    ax2.axvline(x, color=c, linestyle="--", linewidth=1.2, alpha=0.6)
    ax2.text(x + 0.5, 1.08, label, fontsize=7.5, color=c, va="top")

ax2.set_xlabel("Layer", fontsize=10)
ax2.set_ylabel("IIA", fontsize=10)
ax2.set_ylim(0, 1.2)
ax2.legend(fontsize=8, loc="upper right", ncol=2)
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
out2 = OUT_DIR / "full_pipeline_all_five.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close()


# =============================================================================
# Plot 3 — Timeline: all mechanisms as horizontal bars
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(14, 5))
ax3.set_title(
    "Complete Mechanism Timeline — Active Windows (IIA > 0.5)\n"
    "All five lookback phases + attention knockout criticality",
    fontsize=11
)

timeline_items: list[tuple[str, list[int], list[float], str]] = [
    ("Visibility: Source",            vis_source.layers,  vis_source.iia_scores,  "#1565C0"),
    ("Visibility: Address+Pointer",   vis_addr.layers,    vis_addr.iia_scores,    "#0288D1"),
    ("Visibility: Payload",           vis_payload.layers, vis_payload.iia_scores, "#4FC3F7"),
    ("Binding: Address+Payload",      binding.layers,     binding.iia_scores,     "#2E7D32"),
    ("Answer: Pointer",               ans_pointer.layers, ans_pointer.iia_scores, "#9C27B0"),
    ("Answer: Payload",               ans_payload.layers, ans_payload.iia_scores, "#E91E63"),
    ("Knockout: block → Sent2",       ko_s2.layers,       ko_s2.iia_scores,       "#FF9800"),
    ("Knockout: block → Vis1",        ko_vis1.layers,     ko_vis1.iia_scores,     "#F44336"),
]

for i, (label, layers, scores, color) in enumerate(timeline_items):
    active = [l for l, s in zip(layers, scores) if s > 0.5]
    if active:
        width = max(active) - min(active)
        ax3.barh(i, width, left=min(active),
                 height=0.6, color=color, alpha=0.85)
        ax3.text(min(active) + 0.5, i,
                 f"  L{min(active)}–{max(active)}",
                 va="center", fontsize=8.5, color="white", fontweight="bold")

ax3.set_yticks(range(len(timeline_items)))
ax3.set_yticklabels([t[0] for t in timeline_items], fontsize=9)
ax3.set_xlabel("Layer", fontsize=10)
ax3.set_xlim(0, 80)
ax3.axvline(14, color="#1565C0", linestyle=":", linewidth=1, alpha=0.5)
ax3.axvline(34, color="#2E7D32", linestyle=":", linewidth=1, alpha=0.5)
ax3.axvline(55, color="#9C27B0", linestyle=":", linewidth=1, alpha=0.5)
ax3.grid(axis="x", alpha=0.3)

plt.tight_layout()
out3 = OUT_DIR / "complete_mechanism_timeline.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
print(f"Saved: {out3}")
plt.close()


# =============================================================================
# Summary
# =============================================================================

print("=" * 65)
print("VISIBILITY LOOKBACK — SUMMARY TABLE")
print("=" * 65)

for exp in [vis_source, vis_addr, vis_payload]:
    peak   = max(exp.iia_scores)
    peak_l = exp.layers[exp.iia_scores.index(peak)]
    active = [l for l, s in zip(exp.layers, exp.iia_scores) if s > 0.5]
    rng    = f"L{min(active)}–{max(active)}" if active else "none"
    print(f"  {exp.label:<35} peak={peak:.2f} @ L{peak_l:<3}  active={rng}")

print()
print("=" * 65)
print("FULL PIPELINE SUMMARY")
print("=" * 65)

for exp in [vis_source, vis_addr, vis_payload, binding, ans_pointer, ans_payload]:
    active = [l for l, s in zip(exp.layers, exp.iia_scores) if s > 0.5]
    rng    = f"L{min(active)}–{max(active)}" if active else "none"
    print(f"  {exp.label:<40} active={rng}")
