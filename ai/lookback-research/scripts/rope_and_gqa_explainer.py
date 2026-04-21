"""
RoPE (Rotary Position Embedding) and GQA (Grouped Query Attention) Explainer
=============================================================================

Covers three functions from the attention implementation:

    1. rotate_half(x)
    2. apply_rotary_pos_emb(q, k, cos, sin)
    3. repeat_kv(hidden_states, n_rep)

Run with:
    python scripts/rope_and_gqa_explainer.py

Dependencies: torch, matplotlib (numpy comes with torch)
"""

import torch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np

SEP = "=" * 70


# ─────────────────────────────────────────────────────────────────────────────
# Helper: pretty-print a tensor with a label
# ─────────────────────────────────────────────────────────────────────────────
def show(label: str, t: torch.Tensor) -> None:
    print(f"\n  {label}  shape={tuple(t.shape)}")
    print(f"  {t}")


# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — rotate_half
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 1 — rotate_half(x)")
print(SEP)
print("""
PURPOSE
-------
Each attention head works with a vector of size `head_dim`.
RoPE encodes position by *rotating* that vector in 2-D planes.

rotate_half is the mechanical step that builds the "rotated copy":
  Given  x = [x1_0, x1_1, ..., x2_0, x2_1, ...]
             └─── first half ───┘└─── second half ──┘

  Output = [-x2_0, -x2_1, ..., x1_0, x1_1, ...]
            └── negated 2nd half ──┘└── original 1st half ──┘

Then the full rotation is:
  x_rotated = x * cos(θ) + rotate_half(x) * sin(θ)

This is exactly the 2-D rotation formula  [cos θ  -sin θ] applied
                                           [sin θ   cos θ]
to each (x1_i, x2_i) pair across the head dimension.
""")

HEAD_DIM: int = 4  # keep tiny so every number is visible

x: torch.Tensor = torch.tensor([1.0, 2.0, 3.0, 4.0])  # shape (head_dim,)

print("Input x (one head vector, head_dim=4):")
show("x", x)

x1: torch.Tensor = x[: HEAD_DIM // 2]   # [1, 2]
x2: torch.Tensor = x[HEAD_DIM // 2 :]   # [3, 4]

print("\nSplit into two halves:")
show("x1  (first half)", x1)
show("x2  (second half)", x2)

rotated: torch.Tensor = torch.cat((-x2, x1), dim=-1)
print("\nrotate_half(x)  =  cat(-x2, x1):")
show("rotate_half(x)", rotated)

print("""
Trace:
  x        = [ 1,  2,  3,  4]
  -x2      = [-3, -4]
  x1       = [ 1,  2]
  result   = [-3, -4,  1,  2]

The pairs are:  (x[0], x[2]) = (1, 3)  and  (x[1], x[3]) = (2, 4)
After rotation: (-3, 1) and (-4, 2)  → the standard 90° CCW rotation of each pair.
""")

# Visual: show the 2-D rotation geometry
fig_p1: Figure
axes_p1: np.ndarray
fig_p1, axes_p1 = plt.subplots(1, 2, figsize=(10, 4))
fig_p1.suptitle("rotate_half — 2D rotation geometry (one pair per plot)", fontsize=13)

for i, (ax, pair_idx) in enumerate(zip(axes_p1, [0, 1])):
    ax: Axes
    orig: tuple[float, float] = (x[pair_idx].item(), x[pair_idx + HEAD_DIM // 2].item())
    rot_vec: tuple[float, float] = (rotated[pair_idx].item(), rotated[pair_idx + HEAD_DIM // 2].item())

    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_aspect("equal")

    ax.annotate(
        "", xy=orig, xytext=(0, 0),
        arrowprops=dict(arrowstyle="->", color="steelblue", lw=2),
    )
    ax.annotate(
        "", xy=rot_vec, xytext=(0, 0),
        arrowprops=dict(arrowstyle="->", color="tomato", lw=2),
    )
    ax.text(orig[0] + 0.15, orig[1] + 0.15, f"x  ({orig[0]:.0f},{orig[1]:.0f})", color="steelblue", fontsize=10)
    ax.text(rot_vec[0] + 0.15, rot_vec[1] + 0.15, f"rot ({rot_vec[0]:.0f},{rot_vec[1]:.0f})", color="tomato", fontsize=10)
    ax.set_title(f"Pair {i}: (x[{pair_idx}], x[{pair_idx+HEAD_DIM//2}])")
    ax.set_xlabel("first-half dim")
    ax.set_ylabel("second-half dim")

fig_p1.tight_layout()
fig_p1.savefig("scripts/rotate_half_geometry.png", dpi=120)
print("  [figure saved: scripts/rotate_half_geometry.png]")


# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — apply_rotary_pos_emb
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + SEP)
print("PART 2 — apply_rotary_pos_emb(q, k, cos, sin)")
print(SEP)
print("""
PURPOSE
-------
Standard positional encoding adds a fixed vector to each token embedding.
RoPE instead *rotates* each query/key vector by an angle that depends on
the token's position.

  q_rotated[pos] = q[pos] * cos(pos·θ) + rotate_half(q[pos]) * sin(pos·θ)

Key property: dot(q_rotated[p], k_rotated[q]) depends only on (p - q),
i.e. the *relative* distance between tokens, not their absolute positions.
This is what makes RoPE so powerful for length generalisation.

TENSOR SHAPES (what the code handles)
--------------------------------------
  q, k  : (batch, n_heads, seq_len, head_dim)
  cos   : (seq_len, head_dim)  ← precomputed for all positions
  sin   : (seq_len, head_dim)

  After unsqueeze(1):
  cos   : (1, 1, seq_len, head_dim)  ← broadcasts over batch & heads
  sin   : (1, 1, seq_len, head_dim)
""")

# Minimal concrete example
BATCH: int
N_HEADS: int
SEQ_LEN: int
BATCH, N_HEADS, SEQ_LEN, HEAD_DIM = 1, 2, 3, 4

torch.manual_seed(0)
q: torch.Tensor = torch.randn(BATCH, N_HEADS, SEQ_LEN, HEAD_DIM)
k: torch.Tensor = torch.randn(BATCH, N_HEADS, SEQ_LEN, HEAD_DIM)

# Build cos/sin the same way LLaMA does:
# θ_i = 1 / (10000^(2i/head_dim))  for i in 0..head_dim//2
base: float = 10000.0
inv_freq: torch.Tensor = 1.0 / (base ** (torch.arange(0, HEAD_DIM, 2).float() / HEAD_DIM))
# inv_freq shape: (head_dim//2,)

positions: torch.Tensor = torch.arange(SEQ_LEN).float()
# freqs shape: (seq_len, head_dim//2)
freqs: torch.Tensor = torch.outer(positions, inv_freq)
# cos/sin shape: (seq_len, head_dim)  — duplicate for both halves
cos: torch.Tensor = torch.cat([freqs.cos(), freqs.cos()], dim=-1)
sin: torch.Tensor = torch.cat([freqs.sin(), freqs.sin()], dim=-1)

print("Shapes before application:")
show("q", q)
show("cos (pre-unsqueeze)", cos)

def rotate_half(x: torch.Tensor) -> torch.Tensor:
    hd = x.shape[-1]
    x1 = x[..., : hd // 2]
    x2 = x[..., hd // 2 :]
    return torch.cat((-x2, x1), dim=-1)

# The actual application
cos_b: torch.Tensor = cos.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, head_dim)
sin_b: torch.Tensor = sin.unsqueeze(0).unsqueeze(0)

q_embed: torch.Tensor = q * cos_b + rotate_half(q) * sin_b
k_embed: torch.Tensor = k * cos_b + rotate_half(k) * sin_b

print("\nShapes after application:")
show("q_embed", q_embed)

print("""
Per-token breakdown (position 0, position 1, position 2):
  pos=0 → angle=0  → cos=1, sin=0  → q unchanged (no rotation at origin)
  pos=1 → angle=θ  → q rotated by θ
  pos=2 → angle=2θ → q rotated by 2θ

The attention score q·k then encodes relative distance because:
  q_rotated[p] · k_rotated[q]  =  q[p] · R(p-q) · k[q]
where R(Δ) is a rotation matrix depending only on Δ = p - q.
""")

# Visual: show how the angle of one head vector changes with position
fig_p2: Figure
ax_p2: Axes
fig_p2, ax_p2 = plt.subplots(figsize=(8, 4))
ax_p2.set_title("RoPE: how a single (dim-0, dim-2) pair rotates across positions", fontsize=12)
colors: list[str] = ["steelblue", "tomato", "seagreen"]
for pos in range(SEQ_LEN):
    vec: torch.Tensor = q_embed[0, 0, pos, :]   # head 0
    orig: tuple[float, float] = (vec[0].item(), vec[HEAD_DIM // 2].item())
    ax_p2.annotate(
        "", xy=orig, xytext=(0, 0),
        arrowprops=dict(arrowstyle="->", color=colors[pos], lw=2),
    )
    ax_p2.text(orig[0] + 0.05, orig[1] + 0.05, f"pos={pos}", color=colors[pos], fontsize=10)

ax_p2.axhline(0, color="grey", lw=0.5)
ax_p2.axvline(0, color="grey", lw=0.5)
ax_p2.set_aspect("equal")
ax_p2.set_xlabel("dim 0")
ax_p2.set_ylabel("dim 2  (its RoPE pair)")
fig_p2.tight_layout()
fig_p2.savefig("scripts/rope_rotation_by_position.png", dpi=120)
print("  [figure saved: scripts/rope_rotation_by_position.png]")


# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — repeat_kv
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + SEP)
print("PART 3 — repeat_kv(hidden_states, n_rep)")
print(SEP)
print("""
PURPOSE — Grouped Query Attention (GQA)
---------------------------------------
In standard Multi-Head Attention (MHA):
  n_heads_q == n_heads_k == n_heads_v    (e.g. 32 heads each)

In GQA (used by Llama 3, Mistral, etc.):
  n_heads_q  > n_heads_kv                (e.g. 32 query heads, 8 KV heads)

Each "group" of query heads shares one KV head.
  n_rep = n_heads_q / n_heads_kv         (e.g. 32 / 8 = 4)

repeat_kv tiles each KV head n_rep times so the matmul
  scores = q @ k.transpose(-2,-1)
can broadcast normally with q's shape.

SHAPE JOURNEY
-------------
  Input:  (batch, n_kv_heads, seq_len, head_dim)
  Step 1: (batch, n_kv_heads,   1,    seq_len, head_dim)  ← insert dim
  Step 2: (batch, n_kv_heads, n_rep,  seq_len, head_dim)  ← expand (no copy yet)
  Step 3: (batch, n_kv_heads * n_rep, seq_len, head_dim)  ← reshape (copies now)
""")

N_KV_HEADS: int
N_REP: int
BATCH, N_KV_HEADS, SEQ_LEN, HEAD_DIM = 1, 2, 3, 4
N_REP = 2  # each KV head is shared by 2 query heads → 4 total Q heads

kv: torch.Tensor = torch.arange(float(BATCH * N_KV_HEADS * SEQ_LEN * HEAD_DIM)).reshape(
    BATCH, N_KV_HEADS, SEQ_LEN, HEAD_DIM
)

print("Input KV tensor (values are just indices so you can track them):")
show("kv", kv)

# Step-by-step
step1: torch.Tensor = kv[:, :, None, :, :]
print("\nStep 1 — insert dim at position 2 with [:, :, None, :, :]:")
show("step1", step1)

step2: torch.Tensor = step1.expand(BATCH, N_KV_HEADS, N_REP, SEQ_LEN, HEAD_DIM)
print(f"\nStep 2 — expand along the new dim to n_rep={N_REP} (no memory copy yet):")
show("step2", step2)

step3: torch.Tensor = step2.reshape(BATCH, N_KV_HEADS * N_REP, SEQ_LEN, HEAD_DIM)
print(f"\nStep 3 — reshape to merge (n_kv_heads * n_rep) = {N_KV_HEADS * N_REP} heads:")
show("step3", step3)

print(f"""
Verification:
  kv head 0 rows  = {kv[0, 0, :, 0].tolist()}   (position, dim-0 values)
  kv head 1 rows  = {kv[0, 1, :, 0].tolist()}

  After repeat_kv with n_rep=2:
  output head 0   = {step3[0, 0, :, 0].tolist()}  ← copy of KV head 0
  output head 1   = {step3[0, 1, :, 0].tolist()}  ← copy of KV head 0  (same!)
  output head 2   = {step3[0, 2, :, 0].tolist()}  ← copy of KV head 1
  output head 3   = {step3[0, 3, :, 0].tolist()}  ← copy of KV head 1  (same!)

Each pair of query heads shares exactly one KV head.
""")

# Visual: head assignment diagram
fig_p3: Figure
ax_p3: Axes
fig_p3, ax_p3 = plt.subplots(figsize=(9, 3))
ax_p3.set_title(f"GQA head assignment: {N_KV_HEADS} KV heads × n_rep={N_REP} → {N_KV_HEADS*N_REP} Q heads", fontsize=12)
ax_p3.set_xlim(-0.5, N_KV_HEADS * N_REP - 0.5)
ax_p3.set_ylim(-0.5, 2.5)
ax_p3.set_yticks([0.5, 1.5])
ax_p3.set_yticklabels(["KV heads", "Q heads"], fontsize=11)
ax_p3.set_xticks([])
ax_p3.axis("off")

kv_colors: list[str] = ["#4C72B0", "#DD8452"]

# Draw KV heads (centred over their group)
for kv_i in range(N_KV_HEADS):
    cx: float = kv_i * N_REP + (N_REP - 1) / 2
    rect: mpatches.FancyBboxPatch = mpatches.FancyBboxPatch(
        (cx - 0.4, 1.2), 0.8, 0.6,
        boxstyle="round,pad=0.05",
        facecolor=kv_colors[kv_i], edgecolor="white", linewidth=2,
    )
    ax_p3.add_patch(rect)
    ax_p3.text(cx, 1.5, f"KV {kv_i}", ha="center", va="center", color="white", fontsize=10, fontweight="bold")

# Draw Q heads and arrows
for q_i in range(N_KV_HEADS * N_REP):
    kv_owner: int = q_i // N_REP
    cx_q: float = float(q_i)
    cx_kv: float = kv_owner * N_REP + (N_REP - 1) / 2
    rect = mpatches.FancyBboxPatch(
        (cx_q - 0.35, 0.2), 0.7, 0.6,
        boxstyle="round,pad=0.05",
        facecolor=kv_colors[kv_owner], edgecolor="white", linewidth=2, alpha=0.6,
    )
    ax_p3.add_patch(rect)
    ax_p3.text(cx_q, 0.5, f"Q {q_i}", ha="center", va="center", color="white", fontsize=10)
    ax_p3.annotate(
        "", xy=(cx_q, 0.8), xytext=(cx_kv, 1.2),
        arrowprops=dict(arrowstyle="->", color=kv_colors[kv_owner], lw=1.5, alpha=0.8),
    )

fig_p3.tight_layout()
fig_p3.savefig("scripts/gqa_head_assignment.png", dpi=120)
print("  [figure saved: scripts/gqa_head_assignment.png]")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + SEP)
print("SUMMARY — how all three fit together in the attention forward pass")
print(SEP)
print("""
  1. Model loads weights for Q projection (n_heads × head_dim)
     and KV projections (n_kv_heads × head_dim).  n_kv_heads < n_heads in GQA.

  2. rotate_half + apply_rotary_pos_emb
     → Encode position into Q and K by rotating each head vector.
        Each token's Q/K lives at a different angle in head_dim-space.
        Dot products will automatically reflect relative distance.

  3. repeat_kv
     → Tile K and V so they have n_heads (not n_kv_heads) along head axis.
        This makes the  scores = Q @ K^T  matmul shape-compatible.
        Memory cost: KV cache stays small (n_kv_heads), copies only happen
        during the forward pass.

  4. scores = (Q @ K^T) / sqrt(head_dim)    ← attention weights
     out    = softmax(scores) @ V
     → Standard scaled dot-product attention, now with positional awareness.
""")

print("All figures saved to scripts/  — open them to see the geometry.\n")
