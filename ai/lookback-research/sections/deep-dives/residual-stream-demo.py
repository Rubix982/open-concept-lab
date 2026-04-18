"""
Residual stream and co-location — minimal Python demos.

No ML libraries. Expresses the logic using plain numpy-style math.
"""

import math

# =============================================================================
# 1. Residual stream: fixed-length accumulation
# =============================================================================

def make_vector(size, seed=0):
    """Deterministic fake vector for illustration."""
    return [math.sin(seed + i * 0.1) for i in range(size)]

def add_vectors(a, b):
    return [x + y for x, y in zip(a, b)]

DIM = 16  # small for illustration (real: 4096)

# Token starts as an embedding
residual = make_vector(DIM, seed=0)
print(f"After embedding:  {[round(x, 2) for x in residual[:4]]} ...")

# Layer 1 adds its output (attention + MLP delta)
layer1_delta = make_vector(DIM, seed=1)
residual = add_vectors(residual, layer1_delta)
print(f"After layer 1:    {[round(x, 2) for x in residual[:4]]} ...")

# Layer 2 adds its output
layer2_delta = make_vector(DIM, seed=2)
residual = add_vectors(residual, layer2_delta)
print(f"After layer 2:    {[round(x, 2) for x in residual[:4]]} ...")

print(f"Vector length stays: {len(residual)}")  # always DIM


# =============================================================================
# 2. Superposition: storing multiple facts in separate subspace "slots"
# =============================================================================

def zero_vector(size):
    return [0.0] * size

def write_to_subspace(vector, value, start, end):
    """Write a scalar value as a pattern into a subspace slice."""
    v = list(vector)
    for i in range(start, end):
        v[i] = value * math.sin(i - start)  # encode value as a pattern
    return v

def read_from_subspace(vector, start, end):
    """Recover the encoded value from a subspace slice (simple dot product decode)."""
    pattern = [math.sin(i - start) for i in range(start, end)]
    dot = sum(vector[i] * pattern[i - start] for i in range(start, end))
    norm = sum(p ** 2 for p in pattern) ** 0.5
    return dot / norm if norm > 0 else 0.0

# Define subspace slots in a 16-dim vector
CHAR_OI_SLICE  = (0, 4)   # dims 0-3:  char ordering ID
OBJ_OI_SLICE   = (4, 8)   # dims 4-7:  object ordering ID
VALUE_SLICE    = (8, 12)  # dims 8-11: state value encoding

# Simulate writing to "beer" token's residual stream
beer_stream = zero_vector(DIM)

# Attention from "Bob" token writes char_OI=1.0 (first) into beer's stream
beer_stream = write_to_subspace(beer_stream, 1.0, *CHAR_OI_SLICE)

# Attention from "bottle" token writes obj_OI=1.0 (first) into beer's stream
beer_stream = write_to_subspace(beer_stream, 1.0, *OBJ_OI_SLICE)

# The state value itself is also encoded
beer_stream = write_to_subspace(beer_stream, 0.8, *VALUE_SLICE)  # 0.8 = "beer"

print("\n=== Superposition in 'beer' token stream ===")
print(f"char_OI encoded: {read_from_subspace(beer_stream, *CHAR_OI_SLICE):.2f}  (1.0 = first)")
print(f"obj_OI encoded:  {read_from_subspace(beer_stream, *OBJ_OI_SLICE):.2f}  (1.0 = first)")
print(f"value encoded:   {read_from_subspace(beer_stream, *VALUE_SLICE):.2f}")
print(f"All in one vector of length {DIM} — three facts, no interference")


# =============================================================================
# 3. Co-location as a composite key for attention lookup
# =============================================================================

# Simulate two state token streams: "beer" (first char, first obj)
# and "coffee" (second char, second obj)

coffee_stream = zero_vector(DIM)
coffee_stream = write_to_subspace(coffee_stream, 2.0, *CHAR_OI_SLICE)  # second
coffee_stream = write_to_subspace(coffee_stream, 2.0, *OBJ_OI_SLICE)  # second
coffee_stream = write_to_subspace(coffee_stream, 0.3, *VALUE_SLICE)   # "coffee"

state_tokens = {
    "beer":   beer_stream,
    "coffee": coffee_stream,
}

def lookup(query_char_oi, query_obj_oi, state_tokens):
    """
    Co-location lookup: find the state token that matches BOTH OIs.
    This is what a single attention operation achieves when OIs are co-located.
    """
    for name, stream in state_tokens.items():
        c_oi = read_from_subspace(stream, *CHAR_OI_SLICE)
        o_oi = read_from_subspace(stream, *OBJ_OI_SLICE)
        # Match within tolerance
        if abs(c_oi - query_char_oi) < 0.5 and abs(o_oi - query_obj_oi) < 0.5:
            value = read_from_subspace(stream, *VALUE_SLICE)
            return name, value
    return None, None

print("\n=== Co-location lookup ===")
print("Question: 'What does Bob (first) believe the bottle (first) contains?'")
name, val = lookup(query_char_oi=1.0, query_obj_oi=1.0, state_tokens=state_tokens)
print(f"  → Found state token '{name}' (value encoding: {val:.2f})")

print("\nQuestion: 'What does Carla (second) believe the cup (second) contains?'")
name, val = lookup(query_char_oi=2.0, query_obj_oi=2.0, state_tokens=state_tokens)
print(f"  → Found state token '{name}' (value encoding: {val:.2f})")

print("\n[One lookup, two constraints matched simultaneously — that's co-location's value]")
