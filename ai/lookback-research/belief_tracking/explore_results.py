"""
Explore the pre-computed causal mediation analysis results.

Reads the (token_position × layer) causal effect matrices and visualises
which positions in the model carry each entity's OID — reproducing the
logic behind Figure 2 in the paper.

No model or API keys needed — works entirely from saved results.
"""

import json
import os
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")   # non-interactive backend — saves to file
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

ROOT        = Path(__file__).parent
RESULTS_DIR = ROOT / "results" / "causal_mediation_analysis"
OUT_DIR     = ROOT / "explore_output"
OUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Load and summarise
# =============================================================================

def load_causal_matrix(entity: str) -> dict[int, dict[int, float]]:
    """Load (token_pos → layer → causal_effect_score) for one entity type."""
    raw: dict[str, dict[str, float]] = json.load(open(RESULTS_DIR / f"{entity}.json"))
    return {int(tok): {int(lay): v for lay, v in layers.items()}
            for tok, layers in raw.items()}


entities: list[str] = ["character", "object", "state"]
matrices: dict[str, dict[int, dict[int, float]]] = {
    e: load_causal_matrix(e) for e in entities
}

# Get axis ranges (same for all three)
sample     = matrices["character"]
token_pos  = sorted(sample.keys())
layers     = sorted(sample[token_pos[0]].keys())
n_tokens   = len(token_pos)
n_layers   = len(layers)

print("=" * 60)
print("CAUSAL MEDIATION ANALYSIS — result summary")
print("=" * 60)
print(f"  Token positions tracked: {token_pos[0]} → {token_pos[-1]}  ({n_tokens} positions)")
print(f"  Layers:                  {layers[0]} → {layers[-1]}  ({n_layers} layers)")
print(f"  Model:                   Llama-3-70B-Instruct")
print()

# Top causal positions per entity (excluding final answer token)
FINAL_TOKEN = max(token_pos)

print("  Peak causal effect positions (excluding final answer token):")
for entity in entities:
    mat = matrices[entity]
    scores: list[tuple[float, int, int]] = [
        (mat[t][l], t, l)
        for t in token_pos if t != FINAL_TOKEN
        for l in layers
    ]
    scores.sort(reverse=True)
    top = scores[0]
    # Find the layer range where this token is consistently high (>0.5)
    hot_layers = sorted([l for _, t2, l in scores if t2 == top[1] and _ > 0.5])
    print(f"    {entity:10s}: token={top[1]}  "
          f"peak_layer={top[2]}  "
          f"hot_layer_range={hot_layers[0]}–{hot_layers[-1]}  "
          f"score={top[0]:.3f}")

print()


# =============================================================================
# Build numpy matrices for plotting
# =============================================================================

def to_numpy(mat: dict[int, dict[int, float]],
             token_pos: list[int],
             layers: list[int]) -> np.ndarray:
    """Convert nested dict to 2D array [layer × token]."""
    arr = np.zeros((len(layers), len(token_pos)))
    for j, t in enumerate(token_pos):
        for i, l in enumerate(layers):
            arr[i, j] = mat[t].get(l, 0.0)
    return arr


arrays: dict[str, np.ndarray] = {
    e: to_numpy(matrices[e], token_pos, layers) for e in entities
}


# =============================================================================
# Plot 1 — Heatmap per entity (reproduces the data behind Figure 2)
# =============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 8))
fig.suptitle("Causal Mediation Analysis — Llama-3-70B-Instruct\n"
             "Each cell: causal effect of patching (token, layer) on final answer",
             fontsize=13)

colors: dict[str, str] = {
    "character": "#2196F3",   # blue
    "object":    "#FF9800",   # orange
    "state":     "#9C27B0",   # purple
}

for ax, entity in zip(axes, entities):
    arr = arrays[entity]
    cmap = mcolors.LinearSegmentedColormap.from_list(
        entity, ["white", colors[entity]]
    )
    im = ax.imshow(arr, aspect="auto", origin="lower",
                   cmap=cmap, vmin=0, vmax=1,
                   extent=[token_pos[0], token_pos[-1], layers[0], layers[-1]])

    ax.set_title(f"{entity.capitalize()} OI\ncausal effect", fontsize=11)
    ax.set_xlabel("Token position", fontsize=9)
    ax.set_ylabel("Layer" if entity == "character" else "", fontsize=9)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="causal effect")

plt.tight_layout()
out_path = OUT_DIR / "causal_mediation_heatmap.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"  Saved: {out_path}")


# =============================================================================
# Plot 2 — Layer profile at peak token per entity
#          Shows which LAYERS carry each OID — the vertical slices of Figure 2
# =============================================================================

fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.set_title("Causal effect by layer at each entity's peak token position\n"
              "(vertical slice through the heatmap at the hottest token)",
              fontsize=12)

for entity in entities:
    mat = matrices[entity]
    # Find peak token (excluding final)
    scores = [(mat[t][l], t, l)
              for t in token_pos if t != FINAL_TOKEN
              for l in layers]
    peak_token = max(scores, key=lambda x: x[0])[1]

    layer_scores: list[float] = [mat[peak_token].get(l, 0.0) for l in layers]
    ax2.plot(layers, layer_scores,
             color=colors[entity], linewidth=2,
             label=f"{entity} (token {peak_token})")

ax2.set_xlabel("Layer", fontsize=10)
ax2.set_ylabel("Causal effect score", fontsize=10)
ax2.legend(fontsize=10)
ax2.set_xlim(layers[0], layers[-1])
ax2.set_ylim(0, 1.05)
ax2.axhline(0.5, color="gray", linestyle="--", linewidth=1, alpha=0.5,
            label="0.5 threshold")
ax2.grid(axis="y", alpha=0.3)

out_path2 = OUT_DIR / "causal_effect_by_layer.png"
plt.savefig(out_path2, dpi=150, bbox_inches="tight")
print(f"  Saved: {out_path2}")


# =============================================================================
# Print the numbers behind the plots — what do the peaks tell us?
# =============================================================================

print()
print("=" * 60)
print("WHAT THE RESULTS MEAN")
print("=" * 60)
print("""
  Each value in the matrix answers:
    "If I patch the activation at (token T, layer L) with a
     counterfactual, does the model's answer change?"

  Score = 1.0 → patching here ALWAYS changes the answer
  Score = 0.0 → patching here NEVER changes the answer

  A hot region (high scores) at a specific (token, layer)
  means: the information carried at that position IS the
  causal mechanism. The OID lives there.

  What we expect to see (matching Figure 2 in the paper):
    character OID → concentrated at the character token
                    in the question, mid-to-late layers
    object OID    → concentrated at the object token
                    in the question, mid-to-late layers
    state OID     → concentrated at the state token(s)
                    in the story, earlier layers
""")

# Print the raw score matrix for the peak token of each entity
for entity in entities:
    mat = matrices[entity]
    scores = [(mat[t][l], t, l)
              for t in token_pos if t != FINAL_TOKEN
              for l in layers]
    peak_token = max(scores, key=lambda x: x[0])[1]
    print(f"  {entity} peak token={peak_token} — causal effect by layer:")
    layer_profile = [(l, mat[peak_token].get(l, 0.0)) for l in layers]
    hot = [(l, s) for l, s in layer_profile if s > 0.3]
    print(f"    layers with score > 0.3: {[(l, round(s,3)) for l, s in hot]}")
    print()
