"""
Attention head demo — what copies the OID from source to recalled/lookback tokens.

Shows the QK-circuit (who attends to whom) and OV-circuit (what gets copied).
No ML libraries. Uses plain matrix math to show the mechanism.
"""

import math
from dataclasses import dataclass, field
from typing import Literal

OrdinalID = Literal[1, 2]
DIMS = 8   # residual stream width (simplified; real: 4096+)
HEAD_DIM = 4  # each head operates on a subspace (real: 64-128 dims per head)


# =============================================================================
# Types
# =============================================================================

Vector = list[float]
Matrix = list[list[float]]


@dataclass
class ResidualStream:
    token: str
    vec:   Vector = field(default_factory=lambda: [0.0] * DIMS)

    def read(self, start: int, end: int) -> Vector:
        return self.vec[start:end]

    def write(self, incoming: Vector, start: int, end: int) -> None:
        """Residual connection: ADD incoming to current values (never overwrite)."""
        for i, val in enumerate(incoming):
            self.vec[start + i] = round(self.vec[start + i] + val, 4)


@dataclass
class AttentionHead:
    """
    A single attention head with four learned weight matrices.
    W_Q, W_K determine WHO attends to WHOM (QK-circuit).
    W_V, W_O determine WHAT gets copied (OV-circuit).
    """
    name: str
    W_Q:  Matrix   # [DIMS × HEAD_DIM]  query projection
    W_K:  Matrix   # [DIMS × HEAD_DIM]  key projection
    W_V:  Matrix   # [DIMS × HEAD_DIM]  value projection
    W_O:  Matrix   # [HEAD_DIM × DIMS]  output projection back to residual stream


# =============================================================================
# Matrix math
# =============================================================================

def matmul(vec: Vector, mat: Matrix) -> Vector:
    """vec @ mat — project vector through weight matrix."""
    out_dim = len(mat[0])
    return [
        round(sum(vec[i] * mat[i][j] for i in range(len(vec))), 4)
        for j in range(out_dim)
    ]

def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))

def softmax(scores: list[float]) -> list[float]:
    max_s = max(scores)
    exps  = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    return [round(e / total, 4) for e in exps]

def scale(vec: Vector, scalar: float) -> Vector:
    return [round(v * scalar, 4) for v in vec]

def add_vecs(a: Vector, b: Vector) -> Vector:
    return [round(x + y, 4) for x, y in zip(a, b)]


# =============================================================================
# The attention operation — one head, one query token, multiple key/value tokens
# =============================================================================

def attend(
    head:          AttentionHead,
    query_stream:  ResidualStream,
    context:       list[ResidualStream],
    write_start:   int,
    write_end:     int,
) -> None:
    """
    Run one attention head:
      1. Compute query from query_stream
      2. Compute keys and values from all context tokens
      3. Softmax attention weights
      4. Weighted sum of values
      5. Project through W_O and ADD to query_stream (residual connection)

    write_start/end: which subspace slot to write the output into.
    """
    # Step 1: query vector
    Q = matmul(query_stream.vec, head.W_Q)

    # Step 2: keys and values for all context tokens
    keys   = [matmul(s.vec, head.W_K) for s in context]
    values = [matmul(s.vec, head.W_V) for s in context]

    # Step 3: attention scores (Q · K / sqrt(d))
    scale_factor = math.sqrt(HEAD_DIM)
    scores  = [dot(Q, K) / scale_factor for K in keys]
    weights = softmax(scores)

    # Step 4: weighted sum of values
    weighted_value: Vector = [0.0] * HEAD_DIM
    for w, V in zip(weights, values):
        weighted_value = add_vecs(weighted_value, scale(V, w))

    # Step 5: project through W_O and write into residual stream (residual add)
    output = matmul(weighted_value, head.W_O)
    query_stream.write(output[:write_end - write_start], write_start, write_end)

    # Debug: show who was attended to most
    top_idx = weights.index(max(weights))
    print(f"    [{head.name}] attention weights: "
          f"{[(context[i].token, round(w, 3)) for i, w in enumerate(weights)]}")
    print(f"    [{head.name}] strongest attention → '{context[top_idx].token}' "
          f"(weight={weights[top_idx]:.3f})")


# =============================================================================
# Construct learned weight matrices
#
# In a real model these are learned from data. Here we hand-craft them to
# illustrate what each matrix does functionally.
# =============================================================================

def make_identity_proj(in_dim: int, out_dim: int, scale: float = 1.0) -> Matrix:
    """A projection that roughly preserves the first min(in,out) dimensions."""
    mat = [[0.0] * out_dim for _ in range(in_dim)]
    for i in range(min(in_dim, out_dim)):
        mat[i][i] = scale
    return mat

# ADDRESS-WRITING HEAD: "beer" attends to "Bob" and copies Bob's OID
# W_Q: extracts a query from the recalled token (beer) that matches source tokens
# W_K: extracts a key from source tokens that makes them "findable" by recalled tokens
# W_V: extracts the OID value from the source token's stream
# W_O: routes the OID into the ADDRESS subspace [4:8] of beer's stream

address_head = AttentionHead(
    name="address-writer (Layer 5, Head 3)",
    W_Q=make_identity_proj(DIMS, HEAD_DIM, scale=0.5),
    W_K=make_identity_proj(DIMS, HEAD_DIM, scale=2.0),  # source tokens have strong keys
    W_V=make_identity_proj(DIMS, HEAD_DIM, scale=1.0),  # copies OID from source stream
    W_O=make_identity_proj(HEAD_DIM, DIMS, scale=1.0),  # routes into address slot
)

# POINTER-WRITING HEAD: question token attends to "Bob" and copies Bob's OID
pointer_head = AttentionHead(
    name="pointer-writer (Layer 5, Head 7)",
    W_Q=make_identity_proj(DIMS, HEAD_DIM, scale=0.3),
    W_K=make_identity_proj(DIMS, HEAD_DIM, scale=2.0),
    W_V=make_identity_proj(DIMS, HEAD_DIM, scale=1.0),
    W_O=make_identity_proj(HEAD_DIM, DIMS, scale=1.0),
)


# =============================================================================
# Build initial residual streams
# =============================================================================

# Source tokens: their OID is in dims [0:4]
bob_stream   = ResidualStream(token="Bob",    vec=[1.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
carla_stream = ResidualStream(token="Carla",  vec=[2.0, 1.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

# Recalled tokens: payload (semantic content) is in dims [0:4], address slot [4:8] empty
beer_stream   = ResidualStream(token="beer",   vec=[0.5, 0.4, 0.3, 0.2, 0.0, 0.0, 0.0, 0.0])
coffee_stream = ResidualStream(token="coffee", vec=[0.9, 0.7, 0.5, 0.3, 0.0, 0.0, 0.0, 0.0])

# Lookback token: question token, pointer slot [4:8] empty
question_stream = ResidualStream(token="[question]", vec=[1.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

context_tokens = [bob_stream, carla_stream, beer_stream, coffee_stream]


# =============================================================================
# Run the copy operations
# =============================================================================

ADDRESS_SLOT = (4, 8)
POINTER_SLOT = (4, 8)

print("=" * 60)
print("BEFORE — residual streams (dims 4:8 are address/pointer slots)")
print("=" * 60)
print(f"  beer   address slot: {beer_stream.read(*ADDRESS_SLOT)}   ← empty")
print(f"  [question] pointer slot: {question_stream.read(*POINTER_SLOT)}   ← empty")

print("\n" + "=" * 60)
print("COPY 1 — 'beer' attends to context, address-writer head fires")
print("=" * 60)
attend(address_head, beer_stream, context_tokens, *ADDRESS_SLOT)
print(f"\n  beer address slot after: {beer_stream.read(*ADDRESS_SLOT)}   ← OID written in")

print("\n" + "=" * 60)
print("COPY 2 — '[question]' attends to context, pointer-writer head fires")
print("=" * 60)
attend(pointer_head, question_stream, context_tokens, *POINTER_SLOT)
print(f"\n  [question] pointer slot after: {question_stream.read(*POINTER_SLOT)}   ← OID written in")

print("\n" + "=" * 60)
print("RESULT — address and pointer both derived from same source (Bob)")
print("=" * 60)
beer_addr = beer_stream.read(*ADDRESS_SLOT)
q_ptr     = question_stream.read(*POINTER_SLOT)
similarity = 1.0 - sum(abs(a - b) for a, b in zip(beer_addr, q_ptr)) / len(beer_addr)
print(f"  beer address:      {beer_addr}")
print(f"  question pointer:  {q_ptr}")
print(f"  similarity:        {similarity:.3f}  ← high because both came from Bob")
print()
print("  The attention head IS the copy mechanism.")
print("  W_K tuned to make source tokens findable.")
print("  W_V tuned to extract their OID.")
print("  W_O tuned to route OID into the right subspace slot.")
