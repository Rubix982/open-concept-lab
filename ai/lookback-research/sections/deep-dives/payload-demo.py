"""
Payload demo — what it is, who populates it, and how the lookback retrieves it.

The payload is the natural content of the Recalled Token's residual stream.
It is NOT constructed specially. The OID (address) is written alongside it.
"""

import math
from dataclasses import dataclass, field
from typing import Literal, Optional

# =============================================================================
# Types
# =============================================================================

OrdinalID  = Literal[1, 2]
TokenName  = str
LayerIndex = int

DIMS = 24  # residual stream width (real: 4096+)

# Subspace slots within the DIMS-wide residual stream
PAYLOAD_SLOT  = (0,  8)   # semantic content of the token
ADDRESS_SLOT  = (8,  16)  # OID written by source token (address)
POINTER_SLOT  = (16, 24)  # OID written by source token (pointer)


@dataclass
class ResidualStream:
    """
    The residual stream for one token at one layer.
    A single fixed-width vector. Multiple facts coexist in different subspace slots.
    """
    token:    TokenName
    layer:    LayerIndex
    dims:     int
    _vec:     list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self._vec:
            self._vec = [0.0] * self.dims

    def write_slot(self, value: float, start: int, end: int) -> None:
        """Write a value into a subspace slot (simulates attention head output)."""
        for i in range(start, end):
            self._vec[i] = round(value * math.sin(i - start + 1), 4)

    def read_slot(self, start: int, end: int) -> float:
        """Read (decode) a value from a subspace slot."""
        pattern = [math.sin(i - start + 1) for i in range(start, end)]
        dot  = sum(self._vec[i] * pattern[i - start] for i in range(start, end))
        norm = sum(p ** 2 for p in pattern) ** 0.5
        return round(dot / norm, 3) if norm > 0 else 0.0

    def summary(self) -> dict[str, float]:
        return {
            "payload":  self.read_slot(*PAYLOAD_SLOT),
            "address":  self.read_slot(*ADDRESS_SLOT),
            "pointer":  self.read_slot(*POINTER_SLOT),
        }


@dataclass
class StoryEvent:
    character: str
    obj:       str
    state:     str
    ordinal:   OrdinalID


# =============================================================================
# Phase 1 — Payload forms naturally (before any OID is involved)
# =============================================================================

def build_payload(state_token: str, ordinal: OrdinalID, dims: int) -> ResidualStream:
    """
    The payload forms through the normal forward pass — word embedding +
    context from surrounding tokens. No OID involved yet.

    Here we simulate this as: the token's own semantic content
    (ordinal used only to differentiate beer vs coffee, as real embeddings would).
    """
    stream = ResidualStream(token=state_token, layer=0, dims=dims)

    # Simulate word embedding — "beer" and "coffee" have distinct base content
    # In reality this is a learned embedding lookup, not ordinal math
    semantic_value = float(ordinal) * 0.7 + 0.1   # beer=0.8, coffee=1.5
    stream.write_slot(semantic_value, *PAYLOAD_SLOT)

    return stream


# =============================================================================
# Phase 2 — Source token writes OID as Address into Recalled Token
#           AND as Pointer into Lookback Token
# =============================================================================

def write_address(
    recalled_stream: ResidualStream,
    source_oid: OrdinalID,
) -> ResidualStream:
    """
    Attention from Source Token writes OID into Recalled Token's ADDRESS slot.
    The payload in PAYLOAD_SLOT is untouched — address lands in a different subspace.
    """
    recalled_stream.write_slot(float(source_oid), *ADDRESS_SLOT)
    return recalled_stream


def write_pointer(
    lookback_stream: ResidualStream,
    source_oid: OrdinalID,
) -> ResidualStream:
    """
    Attention from Source Token also writes OID into Lookback Token's POINTER slot.
    Same value as address — derived from the same source.
    """
    lookback_stream.write_slot(float(source_oid), *POINTER_SLOT)
    return lookback_stream


# =============================================================================
# Phase 3 — Lookback: Pointer finds Address, retrieves Payload
# =============================================================================

def lookback(
    lookback_stream: ResidualStream,
    candidate_recalled_streams: list[ResidualStream],
) -> Optional[tuple[ResidualStream, float]]:
    """
    The Lookback Token uses its POINTER to find the Recalled Token whose
    ADDRESS matches. Then it reads the PAYLOAD from that token.

    This is one attention operation: pointer forms the query,
    address forms the key, payload forms the value.
    """
    pointer_val = lookback_stream.read_slot(*POINTER_SLOT)

    best_match:  Optional[ResidualStream] = None
    best_score:  float = -999.0

    for candidate in candidate_recalled_streams:
        address_val = candidate.read_slot(*ADDRESS_SLOT)
        # Match score: how close is pointer to address?
        score = 1.0 - abs(pointer_val - address_val)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match is None or best_score < 0.8:
        return None

    # Retrieve payload from matched recalled token
    payload_val = best_match.read_slot(*PAYLOAD_SLOT)
    return best_match, payload_val


# =============================================================================
# Run the full sequence
# =============================================================================

story_events: list[StoryEvent] = [
    StoryEvent("Bob",   "bottle", "beer",   ordinal=1),
    StoryEvent("Carla", "cup",    "coffee", ordinal=2),
]

print("=" * 60)
print("PHASE 1 — Payload forms naturally in each state token")
print("=" * 60)

recalled_streams: list[ResidualStream] = []

for event in story_events:
    stream = build_payload(event.state, event.ordinal, DIMS)
    print(f"\n  '{event.state}' residual stream after word embedding + context:")
    print(f"    payload  = {stream.read_slot(*PAYLOAD_SLOT):.3f}  ← semantic content, populated naturally")
    print(f"    address  = {stream.read_slot(*ADDRESS_SLOT):.3f}  ← empty, OID not written yet")
    print(f"    pointer  = {stream.read_slot(*POINTER_SLOT):.3f}  ← not applicable to recalled token")
    recalled_streams.append(stream)


print("\n" + "=" * 60)
print("PHASE 2 — Source writes OID as Address (recalled) and Pointer (lookback)")
print("=" * 60)

# Simulate: question asks about Bob (ordinal=1) and bottle (ordinal=1)
# Source token = "Bob" with char_OID=1
source_oid: OrdinalID = 1

# Write address into each recalled stream
for stream, event in zip(recalled_streams, story_events):
    write_address(stream, source_oid=event.ordinal)
    print(f"\n  '{event.state}' after address written (from char_OID={event.ordinal}):")
    print(f"    payload  = {stream.read_slot(*PAYLOAD_SLOT):.3f}  ← unchanged, still semantic content")
    print(f"    address  = {stream.read_slot(*ADDRESS_SLOT):.3f}  ← OID now co-located alongside payload")

# Lookback Token (question token) gets the pointer
lookback_stream = ResidualStream(token="[question]", layer=0, dims=DIMS)
write_pointer(lookback_stream, source_oid=source_oid)
print(f"\n  '[question]' lookback token after pointer written (OID=1):")
print(f"    pointer  = {lookback_stream.read_slot(*POINTER_SLOT):.3f}  ← looking for address=1.0")


print("\n" + "=" * 60)
print("PHASE 3 — Lookback: pointer finds address, retrieves payload")
print("=" * 60)

result = lookback(lookback_stream, recalled_streams)

if result:
    matched_stream, payload = result
    print(f"\n  Pointer ({source_oid}) matched recalled token: '{matched_stream.token}'")
    print(f"  Payload retrieved: {payload:.3f}")
    print(f"\n  Interpretation: the question token now holds the answer")
    print(f"  in its residual stream — retrieved in one attention operation.")
else:
    print("  No match found.")


print("\n" + "=" * 60)
print("KEY POINT")
print("=" * 60)
print("""
  The payload was always in 'beer' — it came from the word embedding
  and surrounding context. Nobody placed it there for the lookback.

  The OID (address) was written alongside the payload, in a different
  subspace slot of the same vector. Two separate writes, same token.

  The lookback just needed to find the right token (via pointer→address
  match) and then read the payload that was already sitting there.
""")
