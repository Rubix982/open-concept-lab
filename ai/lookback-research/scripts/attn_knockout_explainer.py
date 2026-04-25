"""
Attention Knockout Explainer
============================
Walks through the algorithm in:
  belief_tracking/notebooks/attn_knockout/attn_knockout_exp.ipynb

No model, no nnsight, no NDIF key needed. All tensors are synthetic
and kept tiny so every number can be traced by hand.

Run with:
    python scripts/attn_knockout_explainer.py

Dependencies: torch, numpy, matplotlib
"""

from __future__ import annotations

import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from matplotlib.axes import Axes
from matplotlib.figure import Figure

SEP: str = "=" * 70


def show(label: str, t: torch.Tensor) -> None:
    print(f"\n  {label}  shape={tuple(t.shape)}")
    print(f"  {t}")


# ═════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("BACKGROUND — what the notebook is testing")
print(SEP)
print("""
The IIA experiments (binding/answer/visibility lookback) told us WHICH LAYERS
causally mediate the belief-tracking mechanism. But they worked by patching
the residual stream between story variants.

Attention knockout asks a more targeted question:

  "Is the *direct attention edge* from token A to token B
   actually necessary for the mechanism to work?"

Method: surgically block specific (from_token → to_token) attention edges
by setting those entries in the attention weight matrix to -infinity before
softmax. The model cannot gather information from those positions.

Then sweep: apply the block starting from each layer L onward.
  - Block from L=0: very disruptive — blocked early and stays blocked.
  - Block from L=28: accuracy recovers — by L28 the information was
    already propagated elsewhere in the residual stream.

The recovery layer reveals WHEN the information becomes load-bearing.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — Token ranges: what gets blocked
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 1 — Token ranges and what they represent")
print(SEP)
print("""
The notebook tokenizes a CausalToM story. The story looks like:

  [instruction]
  Story: Tony and Nancy are working in a busy restaurant.
         [first_sent]  Tony grabs a dispenser and fills it with stout.
         [second_sent] Nancy grabs a can and fills it with juice.
         [first_vis]   Nancy cannot observe Tony's actions.
         [second_vis]  Tony can observe Nancy's actions.
  Question: What does Tony believe the can contains?
  Answer:

The token ranges map to those sentence spans (pre-computed by inspecting the
tokenizer output for a representative sample):

  first_sent           tokens 146–156  (Tony's action)
  second_sent          tokens 158–168  (Nancy's action)
  first_visibility_sent  tokens 169–175  (Nancy cannot observe Tony)
  second_visibility_sent tokens 176–182  (Tony can observe Nancy)

The three experiments block the second_visibility_sent tokens from
attending to different combinations of other tokens:

  Exp A: second_vis blocked from {second_sent + first_vis}
         → can't see Nancy's action OR the fact that Nancy can't see Tony
  Exp B: second_vis blocked from {first_vis} only
         → can't see "Nancy cannot observe Tony's actions"
  Exp C: second_vis blocked from {second_sent} only
         → can't see Nancy's action directly

The intuition: second_visibility_sent must integrate both WHO did WHAT and
WHO could OBSERVE whom. Blocking different combinations reveals which edge
is the critical information carrier.
""")

# Toy token sequence to make the concept concrete
SEQ_LEN: int = 12
# Give names to token positions
token_labels: dict[int, str] = {
    0: "[BOS]",   1: "Tony",    2: "grabs",   3: "stout",
    4: ".",       5: "Nancy",   6: "grabs",   7: "juice",
    8: ".",       9: "Nancy",   10: "can't",  11: "Tony",
}

# Analogous ranges in toy space
second_sent_range: list[int] = [5, 6, 7, 8]       # "Nancy grabs juice ."
first_vis_range: list[int]   = [9, 10]             # "Nancy can't"
second_vis_range: list[int]  = [11]                # "Tony"  (the query token)

print("Toy token positions:")
for pos, label in token_labels.items():
    tag: str = ""
    if pos in second_sent_range:  tag = "  ← second_sent"
    if pos in first_vis_range:    tag = "  ← first_vis"
    if pos in second_vis_range:   tag = "  ← second_vis (query)"
    print(f"  pos {pos:2d}: {label}{tag}")

print(f"""
Experiment B in toy space:
  Block token {second_vis_range} from attending to {first_vis_range}
  i.e. the "Tony" token cannot look at "Nancy can't"
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — Building the knockout mask
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 2 — Building the knockout mask")
print(SEP)
print("""
The mask is a boolean tensor of shape:
  (batch, n_heads, seq_len, seq_len)

  mask[b, h, from_pos, to_pos] = True
  means: "head h in batch b cannot attend from from_pos to to_pos"

The notebook builds it by collecting (from, to) pairs from the
knockout dict, then setting those positions to True for every head.
""")

BATCH: int   = 1
N_HEADS: int = 2  # tiny

# Build for Experiment B: second_vis → first_vis
knockout_b: dict[int, list[int]] = {
    pos: first_vis_range.copy() for pos in second_vis_range
}
print("Knockout dict (Exp B):")
for from_pos, to_list in knockout_b.items():
    print(f"  from {from_pos} → block attending to {to_list}")

from_indices: list[int] = []
to_indices: list[int]   = []
for from_pos, to_list in knockout_b.items():
    for to_pos in to_list:
        from_indices.append(from_pos)
        to_indices.append(to_pos)

from_t: torch.Tensor = torch.tensor(from_indices)
to_t: torch.Tensor   = torch.tensor(to_indices)

knockout_mask: torch.Tensor = torch.zeros(
    BATCH, N_HEADS, SEQ_LEN, SEQ_LEN, dtype=torch.bool
)
for h in range(N_HEADS):
    knockout_mask[0, h, from_t, to_t] = True

print(f"\nKnockout mask (head 0, shape {tuple(knockout_mask[0, 0].shape)}):")
print("  Rows = from_pos (query), Cols = to_pos (key)")
print("  True = this attention edge is blocked")
print()
mask_np: np.ndarray = knockout_mask[0, 0].numpy().astype(int)
header: str = "     " + "".join(f"{j:2d}" for j in range(SEQ_LEN))
print(header)
for i in range(SEQ_LEN):
    row_str: str = "".join("  X" if mask_np[i, j] else "  ." for j in range(SEQ_LEN))
    tag: str = f"  ← {token_labels[i]}" if i in second_vis_range else ""
    print(f"  {i:2d}{row_str}{tag}")


# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — apply_causal_mask: standard causal + knockout
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 3 — apply_causal_mask: layering knockout on top of causal mask")
print(SEP)
print("""
Every transformer uses a CAUSAL MASK so token at position i cannot attend
to positions j > i (future tokens). This is the upper triangle of the
attention matrix, set to -inf before softmax.

The notebook's apply_causal_mask does two things in sequence:

  Step 1: Standard causal mask — upper triangle → -inf
  Step 2: Knockout mask        — selected (from, to) entries → -inf

After softmax, -inf entries become 0.0: those positions contribute nothing.
The rest of the attention distribution renormalises over the unblocked tokens.
""")

HEAD_DIM: int    = 4
IGNORE: float    = torch.finfo(torch.float16).min   # ≈ -65504

# Simulate raw attention scores for one head: (seq_len, seq_len)
torch.manual_seed(3)
attn_scores: torch.Tensor = torch.randn(1, 1, SEQ_LEN, SEQ_LEN) * 0.5

print("Raw attention scores (one head, clipped to last 5 tokens for readability):")
show("attn_scores[0,0,-5:,-5:]", attn_scores[0, 0, -5:, -5:])

# Step 1: causal mask
causal_mask: torch.Tensor = torch.triu(
    torch.ones(SEQ_LEN, SEQ_LEN), diagonal=1
).bool()
attn_scores_masked: torch.Tensor = attn_scores.clone()
attn_scores_masked.masked_fill_(causal_mask, IGNORE)

print("\nAfter causal mask (upper triangle → IGNORE):")
show("attn_scores[0,0,-5:,-5:]", attn_scores_masked[0, 0, -5:, -5:])

# Step 2: knockout mask (slice to head=0 to match attn_scores which has 1 head)
attn_scores_masked.masked_fill_(knockout_mask[:, :1, :, :].to(attn_scores.device), IGNORE)

print("\nAfter knockout mask (blocked edges also → IGNORE):")
show("attn_scores[0,0,-5:,-5:]", attn_scores_masked[0, 0, -5:, -5:])

# Softmax
attn_weights: torch.Tensor = F.softmax(attn_scores_masked.float(), dim=-1)
print("\nAfter softmax (IGNORE positions → 0.0):")
show("attn_weights[0,0,-5:,-5:]", attn_weights[0, 0, -5:, -5:])

print(f"""
Key observations:
  - The last query token (pos {SEQ_LEN-1}) has zeroed-out weights at positions
    {first_vis_range} (the knockout) and all future positions (causal).
  - The remaining weights sum to 1.0 — they redistribute over unblocked tokens.
  - This is the only modification. Everything else (V, O projection) is unchanged.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 4 — The full recompute-and-inject loop
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 4 — The nnsight intervention: recompute and inject")
print(SEP)
print("""
This is the most complex part of the notebook. Here's what happens inside
the `with model.trace(...) as tracer:` block for each layer L ≥ layer_idx:

  STEP A — Intercept Q, K, V *after* their linear projections
    query_states = model.model.layers[l].self_attn.q_proj.output
    key_states   = model.model.layers[l].self_attn.k_proj.output
    value_states = model.model.layers[l].self_attn.v_proj.output

    These are the raw projected vectors BEFORE RoPE or attention.
    Shape: (batch, seq_len, n_heads * head_dim)  — nnsight gives raw output.

  STEP B — Reshape from flat to per-head
    .view(bsz, q_len, n_heads, head_dim).transpose(1, 2)
    → (batch, n_heads, seq_len, head_dim)

  STEP C — Apply RoPE (position encoding)
    cos, sin = model.model.rotary_emb(value_states, positions)
    query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

  STEP D — Expand KV heads for GQA
    key_states   = repeat_kv(key_states,   n_rep)
    value_states = repeat_kv(value_states, n_rep)

  STEP E — Compute attention weights MANUALLY
    attn_weights = (query_states @ key_states.T) / sqrt(head_dim)
    attn_weights = apply_causal_mask(attn_weights, knockout_mask)  ← the intervention
    attn_weights = softmax(attn_weights)

  STEP F — Compute attention output
    attn_output = attn_weights @ value_states
    attn_output = attn_output.transpose(1, 2).reshape(bsz, q_len, -1)

  STEP G — Inject result back
    model.model.layers[l].self_attn.o_proj.input = attn_output

    This bypasses the model's own attention computation entirely.
    The O projection (output linear) then runs on OUR output, not the model's.

WHY INTERCEPT AT o_proj.INPUT?
-------------------------------
The model's forward pass normally does:
  Q, K, V projections → RoPE → attention → O projection

By writing to o_proj.input, we replace everything between Q/K/V and O.
The model's internal attention (with its default mask) never executes for
these layers — ours does instead, with the knockout applied.
""")

# Concrete trace through STEP E + F with tiny tensors
print("--- Concrete trace: STEP E + F ---")

BATCH_S: int   = 1
N_HEADS_S: int = 2
SEQ_S: int     = 5
HEAD_DIM_S: int = 4

torch.manual_seed(9)
Q: torch.Tensor = torch.randn(BATCH_S, N_HEADS_S, SEQ_S, HEAD_DIM_S)
K: torch.Tensor = torch.randn(BATCH_S, N_HEADS_S, SEQ_S, HEAD_DIM_S)
V: torch.Tensor = torch.randn(BATCH_S, N_HEADS_S, SEQ_S, HEAD_DIM_S)

# Mini knockout: block pos 4 from attending to pos 2
mini_mask: torch.Tensor = torch.zeros(BATCH_S, N_HEADS_S, SEQ_S, SEQ_S, dtype=torch.bool)
mini_mask[0, :, 4, 2] = True

raw_scores: torch.Tensor = torch.matmul(Q, K.transpose(2, 3)) / math.sqrt(HEAD_DIM_S)
show("raw_scores (pre-mask)", raw_scores[0, 0])

causal_m: torch.Tensor = torch.triu(torch.ones(SEQ_S, SEQ_S), diagonal=1).bool()
raw_scores.masked_fill_(causal_m, IGNORE)
raw_scores.masked_fill_(mini_mask, IGNORE)
show("scores after causal + knockout mask", raw_scores[0, 0])

weights: torch.Tensor = F.softmax(raw_scores.float(), dim=-1)
show("attention weights (row 4 = blocked from pos 2)", weights[0, 0])

attn_out: torch.Tensor = torch.matmul(weights, V.float())
show("attn_output", attn_out[0, 0])

print(f"""
Note row 4 (the query token at pos 4):
  weight at col 2 = {weights[0, 0, 4, 2].item():.4f}  ← exactly 0.0 (blocked)
  The remaining mass redistributes over cols 0, 1, 3 (causal + unblocked).
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 5 — The layer sweep: what the accuracy curve means
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 5 — The layer sweep and what the recovery curve reveals")
print(SEP)
print("""
The outer loop sweeps over layer_idx ∈ {0, 2, 4, ..., 30, 40, 50, 60, 70}.

For each layer_idx:
  - Apply the knockout to ALL layers from layer_idx to the last layer
  - Measure accuracy on 20 stories

When layer_idx = 0:  knockout runs from the very first layer. The model
  never gets a chance to propagate the blocked information. Accuracy is low.

When layer_idx = L (some recovery layer):  by the time we start blocking,
  the residual stream has already encoded the critical information from the
  blocked tokens. The block is too late — accuracy returns to baseline.

The RECOVERY LAYER is the answer to: "at what depth does the mechanism
complete its work on this attention edge?"

The three experiments produce three curves with different recovery layers:
  Exp A (block second_sent + first_vis): recovery around L26-28
          Both pieces of information are needed; losing both hurts deepest.
  Exp B (block first_vis only):          recovery around L22
          Visibility info integrates slightly earlier.
  Exp C (block second_sent only):        recovery around L24
          The action info (what Nancy did) integrates a bit later than visibility.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 6 — Synthetic accuracy-vs-layer plot
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 6 — Synthetic accuracy-vs-layer plot")
print(SEP)

# Reproduce the qualitative shape of the three notebook curves
layers_sweep: list[int] = list(range(0, 32, 2)) + [40, 50, 60, 70]

def make_sigmoid_curve(
    recovery_layer: float,
    steepness: float = 0.4,
    noise: float = 0.04,
) -> list[float]:
    """Simulate an accuracy curve that rises from ~0 to ~1 around recovery_layer."""
    torch.manual_seed(int(recovery_layer))
    curve: list[float] = []
    for l in layers_sweep:
        base: float = 1.0 / (1.0 + math.exp(-steepness * (l - recovery_layer)))
        jitter: float = (torch.rand(1).item() - 0.5) * noise
        curve.append(float(np.clip(base + jitter, 0.0, 1.0)))
    return curve

# Approximate the actual notebook results
exp_a: list[float] = make_sigmoid_curve(recovery_layer=27.0, steepness=0.5)
exp_b: list[float] = make_sigmoid_curve(recovery_layer=21.5, steepness=0.6)
exp_c: list[float] = make_sigmoid_curve(recovery_layer=23.5, steepness=0.5)

fig: Figure
ax: Axes
fig, ax = plt.subplots(figsize=(9, 4))

ax.plot(layers_sweep, exp_a, marker="o", linewidth=2, label="Exp A: block second_sent + first_vis", color="#C0392B")
ax.plot(layers_sweep, exp_b, marker="s", linewidth=2, label="Exp B: block first_vis only",          color="#2980B9")
ax.plot(layers_sweep, exp_c, marker="^", linewidth=2, label="Exp C: block second_sent only",        color="#27AE60")

ax.axvline(x=27, color="#C0392B", linestyle="--", alpha=0.5, linewidth=1)
ax.axvline(x=22, color="#2980B9", linestyle="--", alpha=0.5, linewidth=1)
ax.axvline(x=24, color="#27AE60", linestyle="--", alpha=0.5, linewidth=1)

ax.set_xlabel("Layer from which knockout is applied", fontsize=12)
ax.set_ylabel("Accuracy", fontsize=12)
ax.set_title(
    "Attention Knockout: accuracy vs. starting layer\n"
    "(synthetic — qualitatively matches notebook output)",
    fontsize=12,
)
ax.set_xticks(layers_sweep)
ax.set_xticklabels([str(l) for l in layers_sweep], rotation=90, fontsize=8)
ax.set_ylim(-0.05, 1.15)
ax.grid(True, linestyle="--", alpha=0.5)
ax.legend(fontsize=10, loc="upper left")

fig.tight_layout()
fig.savefig("scripts/attn_knockout_layer_sweep.png", dpi=150)
print("  [figure saved: scripts/attn_knockout_layer_sweep.png]")

print("""
Reading the plot:
  - X axis: the layer at which the knockout *begins* (applied to all later layers too)
  - Y axis: accuracy of the model on CausalToM stories

  - LEFT side (small layer_idx):  blocking starts early → accuracy near 0
    The model has no chance to build up the missing information elsewhere.

  - RIGHT side (large layer_idx): blocking starts late → accuracy near 1.0
    The residual stream already encoded what it needed from those tokens by
    that layer. The block is too late to matter.

  - RECOVERY LAYER (where curve crosses ~0.5):
    This is when the attention edge "stops being needed" — the information
    has already been absorbed into the residual stream at deeper layers.

  - Exp A recovers latest (~L27): needs BOTH edges; losing both is hardest.
  - Exp B and C recover earlier: each individual edge carries partial info
    that gets integrated sooner.
""")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("SUMMARY — the full algorithm in one place")
print(SEP)
print("""
  Step 1 — Identify token positions
            Map story sentences to token index ranges (pre-tokenized).

  Step 2 — Define knockout dict
            {from_pos: [to_pos, ...]} — which edges to block per experiment.

  Step 3 — Build knockout mask
            bool tensor (batch, n_heads, seq_len, seq_len).
            True = edge is blocked for all heads.

  Step 4 — For each layer_idx in the sweep:
            a. Intercept Q, K, V outputs via nnsight
            b. Reshape to (batch, n_heads, seq_len, head_dim)
            c. Apply RoPE (positional encoding)
            d. Expand KV heads for GQA (repeat_kv)
            e. Compute attention scores: Q @ Kᵀ / sqrt(head_dim)
            f. Apply causal mask + knockout mask (both → -inf)
            g. Softmax → attention weights
            h. Weighted sum over V → attention output
            i. Inject into o_proj.input (bypasses model's own attention)

  Step 5 — Record accuracy across 20 stories per layer.

  Step 6 — Plot accuracy vs. starting layer.
            Recovery layer = when the attention edge stops being necessary.

  RELATIONSHIP TO THE PAPER'S BROADER CLAIMS
  -------------------------------------------
  IIA showed: binding lookback is causal in layers ~L17-L40.
  Knockout shows: the specific attention edges from visibility/story tokens
  to the question token are necessary in those same layers.

  Together: not only is the layer range causal (IIA), the attention mechanism
  within those layers is the actual carrier — not just the residual stream.
  This is head-level, edge-level causal evidence.
""")
