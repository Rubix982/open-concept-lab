"""
Token matrix demo — sentence length and embedding dimension are independent axes.

No ML libraries. Shows the structure of how a transformer processes a sentence.
"""

import math

# =============================================================================
# Setup
# =============================================================================

D_MODEL = 16  # embedding dimension (real Llama-3-70B: 8192, simplified here)

def fake_embedding(token, d_model):
    """Deterministic fake embedding for a token."""
    seed = sum(ord(c) for c in token)
    return [round(math.sin(seed + i * 0.3), 3) for i in range(d_model)]

def fake_attention_delta(token, context_tokens, d_model):
    """
    Fake attention output: pulls a small signal from context into this token's row.
    In reality this is Q @ K^T softmax @ V — here we just simulate the idea.
    """
    seed = sum(ord(c) for c in token)
    return [round(math.cos(seed + i * 0.1) * 0.05, 4) for i in range(d_model)]

def add(a, b):
    return [x + y for x, y in zip(a, b)]


# =============================================================================
# 1. A sentence becomes a MATRIX — one row per token, NOT one vector
# =============================================================================

sentence = "Bob fills the bottle with beer ."
tokens = sentence.split()

print("=" * 60)
print("Sentence:", sentence)
print(f"Tokens: {tokens}")
print(f"\nMatrix shape: {len(tokens)} tokens × {D_MODEL} dims")
print(f"(sentence length and embedding dim are INDEPENDENT)\n")

# Build initial token matrix (just embeddings, before any layers)
matrix = {token: fake_embedding(token, D_MODEL) for token in tokens}

print("Initial token matrix (first 4 dims shown):")
for token, vec in matrix.items():
    print(f"  '{token:8s}' → {vec[:4]} ...")

# =============================================================================
# 2. Each layer updates every row — shape never changes
# =============================================================================

def run_layer(matrix, tokens, layer_num):
    """
    Simulate one transformer layer:
    - Attention: each token reads from all others (cross-row mixing)
    - MLP: each token transforms independently (per-row, no mixing)
    Returns updated matrix with same shape.
    """
    new_matrix = {}
    for token in tokens:
        row = matrix[token]
        # Attention delta: influenced by context
        attn_delta = fake_attention_delta(token, tokens, D_MODEL)
        row = add(row, attn_delta)
        # MLP delta: per-token transformation (simplified as small perturbation)
        mlp_delta = [round(math.tanh(v) * 0.02, 4) for v in row]
        row = add(row, mlp_delta)
        new_matrix[token] = [round(v, 4) for v in row]
    return new_matrix

print("\nRunning 3 layers...")
for layer in range(1, 4):
    matrix = run_layer(matrix, tokens, layer)
    beer_vec = matrix["beer"]
    print(f"  After layer {layer} — 'beer' row (first 4 dims): {beer_vec[:4]} ...")
    print(f"                       row length still: {len(beer_vec)}")

print("\nMatrix shape after all layers: still", len(tokens), "×", D_MODEL)


# =============================================================================
# 3. Contrast: different sentence lengths, same embedding dimension
# =============================================================================

print("\n" + "=" * 60)
print("Different sentence lengths — embedding dim stays fixed\n")

sentences = [
    "Bob fills the bottle with beer .",           # 7 tokens
    "Carla grabs a cup .",                        # 5 tokens
    "What does Bob believe the bottle contains ?", # 8 tokens
]

for s in sentences:
    toks = s.split()
    mat = {t: fake_embedding(t, D_MODEL) for t in toks}
    print(f"  '{s}'")
    print(f"  → matrix: {len(toks)} tokens × {D_MODEL} dims")
    print()


# =============================================================================
# 4. Co-location: how 'beer' accumulates info from other tokens via attention
# =============================================================================

print("=" * 60)
print("Simulating co-location: 'beer' accumulates Bob's and bottle's OIs\n")

# Simplified: represent OI as a value written into a specific subspace slot
def write_oi(row, oi_value, slot_start, slot_end):
    row = list(row)
    for i in range(slot_start, slot_end):
        row[i] = round(oi_value * math.sin(i - slot_start + 1), 4)
    return row

def read_oi(row, slot_start, slot_end):
    pattern = [math.sin(i - slot_start + 1) for i in range(slot_start, slot_end)]
    dot = sum(row[i] * pattern[i - slot_start] for i in range(slot_start, slot_end))
    norm = sum(p**2 for p in pattern) ** 0.5
    return round(dot / norm, 3) if norm > 0 else 0.0

CHAR_OI_SLOT = (0, 4)
OBJ_OI_SLOT  = (4, 8)

beer_row = fake_embedding("beer", D_MODEL)
print(f"'beer' before attention: char_OI slot = {read_oi(beer_row, *CHAR_OI_SLOT)}")

# Attention from "Bob" writes char_OI=1.0 into beer's row
beer_row = write_oi(beer_row, 1.0, *CHAR_OI_SLOT)
print(f"After Bob attends   →  char_OI slot = {read_oi(beer_row, *CHAR_OI_SLOT)}")

# Attention from "bottle" writes obj_OI=1.0 into beer's row
beer_row = write_oi(beer_row, 1.0, *OBJ_OI_SLOT)
print(f"After bottle attends → obj_OI  slot = {read_oi(beer_row, *OBJ_OI_SLOT)}")

print(f"\n'beer' row now carries BOTH OIs in one {D_MODEL}-dim vector.")
print("This is co-location — one row, two facts, different subspace slots.")
