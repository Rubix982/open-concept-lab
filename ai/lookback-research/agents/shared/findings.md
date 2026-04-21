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

---

## [Speculative] Finding: Belief Replacement vs Accumulation and the Intrinsic Signal Structure

_Date: 2026-04-22_

Emerged from comparing BigToM and CausalToM vulnerability windows.

The model's vulnerability window (IIA gap during vis_ID processing) is not
measurement noise — it is evidence of a specific architectural limitation:
the model drops tentative context loads rather than using them as directed
queries for guided second retrieval. In human cognition, a pre-linguistic
"mushy feeling" triggers a metacognitive verification pass anchored to the
first answer. The LLM has no equivalent circuit.

What would approximate this is not a scalar confidence score but a structured
RetrievalProfile: a vector of intrinsic process signals (OID coherence, subspace
stability, attention entropy, residual competition, layer of first load, gap width,
load count). A specific pattern across these values — not any single value — is
the structural equivalent of the mushy feeling.

The extended L0 decoder would: (1) read the belief, (2) profile the retrieval
process, (3) detect mushy patterns, (4) trigger a second pass using the tentative
first answer as anchor, (5) output a synthesis not a replacement.

The vulnerability window in BigToM is the measurable shadow of where the model
chose replacement over accumulation and fell briefly silent. A human with the
mushy feeling would not fall silent — they would use the uncertainty as fuel
for a more directed search.

This maps directly onto the epistemic classification system in the Research
Knowledge Infrastructure: RetrievalProfile values correspond to established /
preliminary / contested / ungrounded states.

Full write-up: `sections/07-research-insights/belief-revision-and-uncertainty.md`

Confidence: speculative — theoretical, not yet experimentally tested.
Questions for authors documented in the write-up.
