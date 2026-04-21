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

Full write-up: `sections/09-research-insights/belief-revision-and-uncertainty.md`

Confidence: speculative — theoretical, not yet experimentally tested.
Questions for authors documented in the write-up.

---

## [R-002] Finding: Cross-Model Replication

_Date: 2026-04-22_

The lookback mechanism replicates across Llama-3-70B (80L), Llama-3.1-405B
(126L), and Qwen2.5-14B (48L). Four findings:

1. **Answer payload universally occupies the final 30-40% of model depth.**
   70B: 70-99%, 405B: 59-99%, Qwen: 88-98%. IIA=1.00 in all cases.
   The most robust cross-model result — architecture-independent.

2. **Binding mechanisms consistently complete in the first half of the model.**
   All three models show binding active before ~50% of depth, with the
   answer lookback starting after binding ends. Sequential structure preserved.

3. **Source_2 control stays near zero universally.**
   70B: 0.16, 405B: 0.05, Qwen: 0.01. State token as binding destination
   is not model-specific — it is an emergent property of the task structure.

4. **Qwen achieves same peak IIA in significantly narrower windows.**
   Answer pointer: 70B=22 layers, 405B=24 layers, Qwen=5 layers.
   Smaller models compute the same mechanism more compactly but with less
   redundancy — narrower windows mean more brittleness under perturbation.

5. **Scaling is proportional, not absolute.**
   Mechanisms do not fire at the same layer numbers across models.
   When normalised to % of total depth, the active regions are consistent.
   A deeper model has more layers per zone — more redundancy, wider windows.

Full artifacts: `sections/08-cross-model/`

Confidence: high (three model families, consistent pattern)

---

## [R-003] Finding: Synthesis Complete

_Date: 2026-04-22_

`sections/synthesis.md` written. Covers all five mechanisms with layer
windows, every experiment with IIA numbers, BigToM and cross-model findings,
implications for the Research Knowledge Infrastructure L0 layer, and 7 open
questions for future work and author discussion.

Key synthesis insight: the paper's methodology (causal mediation + IIA) is
the flashlight; the space of undiscovered mechanisms is large. The extended
L0 decoder — reading not just belief but process profile — maps directly onto
the paper's framework and extends it toward the knowledge infrastructure vision.

---

## [R-004] Finding: Model Evaluation Landscape

_Date: 2026-04-22_

14 models tested on CausalToM. Four findings:

1. **Instruction tuning is essential.** Base models mostly fail (0.01-0.45 novis).
   Instruct variants of the same models reach 0.72-0.96. Exception: Qwen2.5-14B
   base reaches 0.86 novis — notably high for a base model.

2. **Visibility is harder than no-visibility for almost every model.**
   Gap ranges from -0.03 (70B, nearly immune) to -0.43 (Qwen-14B base, collapses).
   The models selected for mechanistic analysis (70B, Qwen-14B-Instruct) have gaps
   of only -0.03 and -0.05 — outliers.

3. **Scale matters but not uniformly.** Qwen-7B-Instruct matches Llama-3-70B on
   novis (both 0.95). The visibility gap is what requires scale — Qwen-7B drops
   to 0.72 on vis vs Qwen-14B at 0.91.

4. **Model selection funnel is tight.** Only 2 publicly tested models reach ≥0.90
   on both conditions. This is why the mechanistic analysis is limited to those
   specific models — IIA experiments require correct answers to analyze.

Full artifacts: `sections/10-model-evaluations/`
Confidence: high (direct measurement data)

---

## [R-005] Finding: Cross-Model Visibility Lookback

_Date: 2026-04-22_

Visibility lookback compared across 70B, 405B, Qwen — using causalToM_vis.

1. **All three models reach IIA ≥ 0.99** for visibility mechanisms. Strong generalization.

2. **The vulnerability gap exists in all models but narrows with scale.**
   70B: 7 layers (9%), 405B: 2 layers (2%), Qwen: 6 layers (12%).
   Larger models transition more smoothly from vis_ID formation to payload transfer.

3. **Llama models (70B and 405B) are nearly identical proportionally.**
   Despite different depths (80 vs 126 layers), their visibility mechanisms
   occupy the same relative zones. Qwen is systematically later (~38% start vs ~12%).

4. **Sequential ordering preserved in all models.**
   vis source → vis payload → binding → answer pointer → answer payload.
   The mechanism is architecture-independent.

Full artifacts: `sections/11-cross-model-visibility/`
Confidence: high

---

## [R-006] Finding: Related Work Analysis

_Date: 2026-04-22_

Three prior work clusters mapped:

1. **ToM benchmarks** (behavioral): established that models sometimes succeed but
   couldn't explain how. All lack counterfactual structure for causal analysis.

2. **Entity tracking / variable binding**: Dai et al. (2024) OIDs and Feng &
   Steinhardt (2023) Binding IDs are the direct predecessor concepts.
   This paper is the first end-to-end mechanism paper in this lineage.

3. **Mechanistic ToM**: Zhu et al. (2024) showed beliefs are linearly decodable.
   Bortoletto et al. (2024) proposed adequacy criteria for belief-like representations.
   Neither identified the computational mechanism — that's this paper's contribution.

Key papers for Research Knowledge Infrastructure (priority order):
Dai et al. 2024 > Zhu et al. 2024 > Bortoletto et al. 2024 > Li et al. 2021

Ethics note: paper explicitly frames mechanistic interpretability as a safety tool
for detecting deception — directly supports the L0 decoder motivation.

Full artifacts: `sections/12-related-work/`
Confidence: high
