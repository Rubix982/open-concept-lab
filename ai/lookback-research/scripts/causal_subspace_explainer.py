"""
Causal Subspace Analysis Explainer
====================================
Walks through the algorithm in:
  belief_tracking/notebooks/causal_subspace_analysis/lookback.ipynb

No model weights needed. All tensors are synthetic and kept tiny so every
number can be traced by hand.

Run with:
    python scripts/causal_subspace_explainer.py

Dependencies: torch, numpy, matplotlib
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.axes import Axes
from matplotlib.figure import Figure

SEP: str = "=" * 70


def show(label: str, t: torch.Tensor) -> None:
    print(f"\n  {label}  shape={tuple(t.shape)}")
    print(f"  {t}")


# ═════════════════════════════════════════════════════════════════════════════
# BACKGROUND — the big picture before any code
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("BACKGROUND — what this notebook is answering")
print(SEP)
print("""
The paper showed (via IIA experiments) that certain layers causally mediate
the "answer lookback" mechanism — the model reads the answer token back out
of the residual stream at the last position.

But IIA tells you *which layers matter*, not *which attention heads* inside
those layers do the work. This notebook asks:

  "Of the 64 attention heads per layer, which ones are most aligned
   with the causal subspace of the answer lookback mechanism?"

To answer this, it uses three pre-computed artifacts:

  1. Singular vectors  — a set of orthonormal directions that span the
     residual stream space (from SVD of activations).

  2. IIA mask  — a binary vector, one entry per singular vector.
     Entry=1 means "this direction was found to causally mediate the
     mechanism." Together, the masked-in vectors define the CAUSAL SUBSPACE.

  3. Attention weight matrices  — Q, K, V, O projections for every head,
     read directly from the model.

The algorithm then measures: "how much does each head's weight matrix
*reach into* the causal subspace?"

Answer: project the weight matrix onto each subspace direction, then measure
the magnitude (norm) of that projection per head.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — Singular Vectors and the Causal Subspace
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 1 — Singular vectors and the causal subspace")
print(SEP)
print("""
WHAT IS A SINGULAR VECTOR?
--------------------------
Run SVD on the matrix of residual stream activations across all tokens and
stories (shape: n_tokens × hidden_dim):

    A = U Σ Vᵀ

The *right* singular vectors (rows of Vᵀ, columns of V) are orthonormal
directions in hidden_dim space. They capture the principal axes of variation
in the residual stream — think of them as a learned coordinate system for
"what the model represents."

The notebook loads the pre-computed singular vectors from disk (one file per
layer). Each file contains a matrix of shape (hidden_dim, hidden_dim) — all
singular vectors for that layer.

WHAT IS THE IIA MASK?
---------------------
The IIA experiment for the answer-lookback pointer ran DAS (Distributed
Alignment Search) to find the subspace directions that, when swapped between
counterfactual pairs, most reliably change the model's answer.

The result is stored as a binary mask of length hidden_dim:
  mask[i] = 1  → singular vector i is causally active
  mask[i] = 0  → singular vector i is not part of this mechanism

The CAUSAL SUBSPACE for a given layer = the singular vectors where mask == 1.
""")

# Concrete tiny example
HIDDEN_DIM: int = 8
N_SVS: int = 8       # total singular vectors per layer = hidden_dim

torch.manual_seed(42)

# Simulate a set of orthonormal singular vectors (rows = singular vectors)
# In reality these come from SVD; here we use a random orthonormal basis.
raw: torch.Tensor = torch.randn(N_SVS, HIDDEN_DIM)
singular_vecs: torch.Tensor = torch.linalg.qr(raw.T)[0].T   # (N_SVS, HIDDEN_DIM)

# IIA mask: only directions 2 and 5 were found to be causally active
mask: torch.Tensor = torch.zeros(N_SVS)
mask[2] = 1.0
mask[5] = 1.0

causal_subspace: torch.Tensor = singular_vecs[mask == 1]   # (n_active, HIDDEN_DIM)

print("All singular vectors for one layer:")
show("singular_vecs", singular_vecs)

print("\nIIA mask (1 = causally active direction):")
show("mask", mask)

print("\nCausal subspace = singular_vecs filtered by mask:")
show("causal_subspace", causal_subspace)

print(f"""
Interpretation:
  We have {N_SVS} singular vectors total.
  The IIA mask selected {int(mask.sum().item())} of them (indices 2 and 5).
  Those 2 directions form the causal subspace for this layer.

  Geometrically: the causal subspace is a {int(mask.sum().item())}-dimensional
  plane inside the {HIDDEN_DIM}-dimensional residual stream.
  The mechanism "lives" in this plane.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — Projecting the Weight Matrix onto the Subspace
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 2 — Projecting the weight matrix onto each subspace direction")
print(SEP)
print("""
The notebook does this for the Q projection (pointer subspace)
and V projection (payload subspace). We'll walk through Q.

Q PROJECTION SHAPE
------------------
  q_proj.weight  shape: (n_heads * head_dim,  hidden_dim)
                      = (output_dim,           input_dim)

  Each row of q_proj is one output dimension.
  The first head_dim rows belong to head 0, the next to head 1, etc.

THE PROJECTION STEP
-------------------
  q_proj_normalized = q_proj / ||q_proj||_cols   (column-normalize)
  q_proj_sv         = q_proj_normalized @ sv       shape: (n_heads * head_dim,)

  This is a standard projection: for every output dimension i,
  "how much does this output direction point along sv?"

  sv is a unit vector in hidden_dim space (input space).
  q_proj @ sv answers: "if the input is sv, what output does this projection
  produce?" — a vector of length n_heads * head_dim.

CHUNKING BY HEAD
----------------
  Reshape (n_heads * head_dim,) → (n_heads, head_dim)
  then norm(dim=1) → (n_heads,)  scalar per head

  head_norm[h] = ||q_proj_sv[h*head_dim : (h+1)*head_dim]||

  This measures how strongly head h's Q projection responds to the subspace
  direction sv. A large norm means head h actively reads from that direction.

ACCUMULATE OVER ALL CAUSAL DIRECTIONS
--------------------------------------
  Repeat for every sv in the causal subspace, summing the per-head norms.
  The total = "how aligned is head h with the full causal subspace?"
""")

# Toy dimensions
N_HEADS: int = 4
HEAD_DIM: int = 2      # tiny: 4 heads × 2 dims = 8 = HIDDEN_DIM
OUTPUT_DIM: int = N_HEADS * HEAD_DIM   # must equal HIDDEN_DIM here for simplicity

torch.manual_seed(7)
q_proj: torch.Tensor = torch.randn(OUTPUT_DIM, HIDDEN_DIM)

print("Q projection weight matrix:")
show("q_proj  (output_dim × hidden_dim)", q_proj)

# Column-normalise (as the notebook does)
q_proj_norm: torch.Tensor = q_proj / torch.norm(q_proj, dim=0)
print("\nAfter column-normalisation:")
show("q_proj_norm", q_proj_norm)

print("\n--- Now iterate over each causal singular vector ---")

head_norm_total: torch.Tensor = torch.zeros(N_HEADS)

for i, sv in enumerate(causal_subspace):
    sv_unit: torch.Tensor = sv / sv.norm()   # ensure unit length

    # Projection: (output_dim,)
    q_proj_sv: torch.Tensor = q_proj_norm @ sv_unit
    print(f"\n  sv index {i} (shape {tuple(sv_unit.shape)}):")
    show(f"  q_proj_norm @ sv[{i}]", q_proj_sv)

    # Reshape into (n_heads, head_dim)
    head_out: torch.Tensor = q_proj_sv.reshape(N_HEADS, HEAD_DIM)
    print(f"  Reshaped to (n_heads={N_HEADS}, head_dim={HEAD_DIM}):")
    show("  head_out", head_out)

    # Per-head norm
    per_head: torch.Tensor = torch.norm(head_out, dim=1)
    show("  per-head norm", per_head)

    head_norm_total += per_head

print("\nFinal accumulated head norms (summed over all causal directions):")
show("head_norm_total", head_norm_total)

print(f"""
Reading the result:
  head 0 norm = {head_norm_total[0]:.3f}
  head 1 norm = {head_norm_total[1]:.3f}
  head 2 norm = {head_norm_total[2]:.3f}
  head 3 norm = {head_norm_total[3]:.3f}

  The head with the highest norm is most aligned with the causal subspace.
  In the full model (64 heads × 80 layers), this produces a 2D heatmap
  that shows which heads, in which layers, "implement" the mechanism.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — Q vs V: pointer vs payload
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 3 — Why Q for pointer, V for payload?")
print(SEP)
print("""
The notebook runs the same pipeline twice with a key difference:

  POINTER subspace  →  project Q_proj
  PAYLOAD subspace  →  project V_proj

This is deliberate and reflects what the two mechanisms do:

  Q (query) projection:
    Determines WHAT the head ATTENDS TO.
    If a head's Q aligns with the pointer subspace, it actively searches
    for the "who is asking the question" token in the sequence.
    → "Which heads are doing the looking-up?"

  V (value) projection:
    Determines WHAT INFORMATION is READ OUT once attention weights are set.
    If a head's V aligns with the payload subspace, it carries the answer
    content (the belief) into the output.
    → "Which heads are carrying the answer?"

So the two heatmaps answer complementary questions:
  Q heatmap: heads that locate the pointer (where to look)
  V heatmap: heads that read the payload (what to bring back)
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 4 — Synthetic heatmap (mimics the notebook figure)
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 4 — Synthetic heatmap visualisation")
print(SEP)

# Simulate a realistic-looking result: a few heads light up in middle layers
N_LAYERS_VIS: int = 20
N_HEADS_VIS: int = 16

torch.manual_seed(0)
# Base: low random noise everywhere
heatmap_data: np.ndarray = torch.rand(N_LAYERS_VIS, N_HEADS_VIS).numpy() * 0.3

# Simulate "hot" heads: 2-3 heads that are consistently active in layers 8-14
for layer in range(8, 15):
    heatmap_data[layer, 3] += 2.5 + torch.rand(1).item() * 0.5
    heatmap_data[layer, 7] += 1.8 + torch.rand(1).item() * 0.4
    heatmap_data[layer, 11] += 1.2 + torch.rand(1).item() * 0.3

layer_labels: list[int] = list(range(N_LAYERS_VIS))
head_labels: list[int] = list(range(N_HEADS_VIS))

fig: Figure
ax: Axes
fig, ax = plt.subplots(figsize=(10, 5))

im = ax.imshow(
    heatmap_data,
    cmap="Blues",
    interpolation="nearest",
    aspect="auto",
    vmin=0,
    vmax=float(np.max(heatmap_data)) + 0.5,
)
fig.colorbar(im, ax=ax, label="Accumulated Q-proj norm on causal subspace")

ax.set_title("Q_proj norms on Answer lookback pointer subspace\n(synthetic — same shape as notebook figure)", fontsize=13)
ax.set_xlabel("Attention Head", fontsize=12)
ax.set_ylabel("Layer", fontsize=12)

ax.set_xticks(range(0, N_HEADS_VIS, 2))
ax.set_xticklabels(range(0, N_HEADS_VIS, 2), rotation=90, fontsize=9)
ax.set_yticks(range(0, N_LAYERS_VIS, 3))
ax.set_yticklabels(layer_labels[::3], fontsize=9)
ax.invert_yaxis()

fig.tight_layout()
fig.savefig("scripts/causal_subspace_heatmap.png", dpi=150)
print("  [figure saved: scripts/causal_subspace_heatmap.png]")

print("""
How to read the real notebook heatmap:
  - Each row = one layer of the model
  - Each column = one attention head (0 to 63 in the 70B model)
  - Color intensity = accumulated norm across all causal singular vectors
  - Dark blue = head strongly aligned with the causal subspace
  - Pale = head does not participate in this mechanism

  In the paper's actual results, only a small number of heads light up
  in the layers where IIA was already high (L50-L60 for the pointer,
  L55-L65 for the payload). This confirms the mechanism is head-sparse:
  a handful of heads do the work, not all 64.
""")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("SUMMARY — the full pipeline in one place")
print(SEP)
print("""
  Step 1 — SVD of residual stream activations
            → orthonormal directions spanning hidden_dim space

  Step 2 — IIA (DAS) finds the causal subspace
            → binary mask: which directions mediate the mechanism

  Step 3 — For each causally-active singular vector sv:
            a. Column-normalise the weight matrix (q_proj or v_proj)
            b. Project: weight @ sv  →  (n_heads * head_dim,)
            c. Reshape: (n_heads, head_dim)
            d. Per-head norm  →  (n_heads,)
            e. Accumulate across all active svs

  Step 4 — Heatmap: rows=layers, cols=heads, intensity=accumulated norm
            → visually identifies WHICH heads implement the mechanism

  The key insight: IIA tells you WHERE (which layers, which subspace).
  This analysis tells you WHO (which attention heads inside those layers).
  Together: full mechanistic attribution from macro (layer) to micro (head).
""")
