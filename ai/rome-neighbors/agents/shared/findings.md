# Shared Findings

_Owned by: Researcher. Append-only._

## [E-005] Finding: Where "Eiffel Tower → Paris" lives in GPT-J-6B

_Date: 2026-08-04_

Localization of a single factual association via logit lens, residual-stream
analysis, and position-specific ablation on GPT-J-6B (28 layers, remote/NDIF).
Prompt: "The Eiffel Tower is in the city of" → "Paris" (baseline P = 0.82).

**Readout (logit lens, last token):** "Paris" is not top-1 until layer 12
(commit), then saturates to ~1.0 at layers 16–17 (consolidation), holds to
layer 24, relaxes slightly to 0.82 by layer 27.

**Storage (relative change at subject token "Tower"):** subject representation
is rewritten most in the EARLY layers (peak rel-change layers 1–5), tapering
through the mid layers. NB: raw ||Δ|| is confounded by residual-norm growth
(~7× over depth) — relative change is the honest metric.

**Ablation (position-specific zeroing, the causal test):**
- Zeroing the SUBJECT token ("Tower") destroys "Paris" only in EARLY-MID layers:
  drop 0.46–0.70 at layers 0–8, fading through 9–12, ≈0 from layer 13 onward.
  → The fact depends on the subject token only until ~layer 12, then the subject
    is dispensable (info already extracted). This is the ROME storage band.
- Zeroing the LAST token ("of") is catastrophic at EVERY layer (drop ≈0.82).
  → Uninformative: the last position is the readout channel; destroying it is
    fatal regardless of layer (like zeroing the whole cumulative stream).

**Synthesis — the handoff:** the fact is stored/read at the subject token in
early-mid layers (~2–12), then carried by attention to the last token where it
crystallises into the prediction (~12–17). Storage precedes readout in depth.
This matches the ROME picture and predicts the causal-tracing (AIE) peak should
land around layers ~2–9 at the subject position (to be confirmed in E-004/04).

Confidence: medium-high (single prompt, single fact; deterministic runs, three
independent methods agree). Needs replication across the E-001 triple set.

**Caveat:** zeroing is a blunt, destructive tool. The clean localization is the
corrupt-restore AIE / interchange IIA (see `readings/metrics/notes.md`), which
adds correct information back rather than destroying it — pending in causal
tracing. Localization ≠ editability (Hase et al.); flag in any write-up.
