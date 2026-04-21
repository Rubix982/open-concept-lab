# Shared Findings

Owned by: Researcher
Append-only. No edits to prior entries.

---

## [R-001] Finding: BigToM Generalization

_Date: 2026-04-22_

The lookback mechanism generalizes to BigToM (real-world ToM benchmark) but
the transfer is not uniform across mechanism types.

**Answer lookback transfers cleanly.** Pointer active L31-52 (vs L33-55 in
CausalToM) and payload active L56-79 (identical). Same shape, same handoff
point, 2-layer shift at most. This is the paper's strongest generalization claim
and it holds.

**Visibility lookback transfers with differences.** Source and address+pointer
are causal from layer 0 in BigToM — unlike CausalToM where they build up from
layer 10. In real text, visibility information appears to be encoded in token
embeddings directly rather than being constructed through mid-layer attention.
The visibility payload arrives at L26 (vs L31 in CausalToM) and persists through
all 80 layers rather than dropping at layer 55. In real text, visibility is
integrated more deeply and never fully consumed.

**Key implication:** The answer lookback is architecture-level general. The
visibility lookback is general in *what* it computes but differs in *how early*
the input is represented — suggesting real-world language encodes social
visibility more immediately at the token level than synthetic text does.

Confidence: high (data matches paper's reported BigToM figures 21-24)
