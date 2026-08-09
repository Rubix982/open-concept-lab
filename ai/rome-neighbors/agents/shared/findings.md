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

## [E-006] Finding: NNSight `.source` operation-level access on GPT-J-6B

_Date: 2026-08-09_

`.source` reads a module's forward() source and exposes each operation as a
hook point (script 09, run locally — no remote call needed for introspection).
Discovered on GPT-J-6B:

**Attention forward exposes the pattern.** `attn.source.self__attn_0.output`
is the `(attn_output, attn_weights)` tuple from `self._attn(...)`; `[1]` is the
attention-weights tensor `[1, heads, seq, seq]`. This is unreachable at any
module boundary — `.source` is the only way to grab GPT-J attention patterns.

**Architectural finding — GPT-J is PARALLEL.** Block forward line 23:
`hidden_states = attn_outputs + feed_forward_hidden_states + residual`. Attention
and MLP both read the SAME `ln_1` output and are summed with the residual — not
GPT-2's sequential attn→norm→mlp. There is only ONE layernorm per block (`ln_1`),
no `ln_2`. Implication: at the block level we can zero `self_attn_0.output[0]`
(attention contribution) or `self_mlp_0.output` (MLP contribution) independently.

**Useful op names (GPT-J):** attn: self_q/k/v_proj_0, self__split_heads_0/1/2,
apply_rotary_pos_emb_0..3, self__attn_0 (→ attn_output, attn_weights),
self__merge_heads_0, self_out_proj_0. mlp: self_fc_in_0, self_act_0,
self_fc_out_0. Even functional ops are hookable: ln_f → F_layer_norm_0,
lm_head → F_linear_0. Internal (not ops): .source.operations / .accessor /
.interleaver / .path.

**Sanity:** a source-op that IS a submodule call (self_out_proj_0) should equal
that submodule's boundary output (attn.out_proj.output) — verified in script 10.

Confidence: high for the source map (deterministic introspection); the capture /
attention / intervention scripts (10/12/13) are written but not yet run.

**Update (10 run):** `.source` capture confirmed on GPT-J. Shapes:
q_proj `(1,10,4096)`; `_attn.output[1]` = attention weights `(1,16,10,10)`
`[batch,heads,seq,seq]` — the pattern, reachable; `_attn.output[0]` `(1,16,10,256)`
is per-head output BEFORE `_merge_heads`. Two `.source` lessons (→ memory
`reference-nnsight`):
1. Do NOT hook the same op both via `.source` and its module boundary in one
   trace → `MissedProviderError` ("called out of order"). Use separate traces.
2. Grab a tuple-returning op's `.output` ONCE, then index — not `.output[0]` and
   `.output[1]` as two hooks.
Sanity: source-op vs module-boundary differ only by ~3.9e-3 = fp16 run-to-run
nondeterminism (two separate remote jobs), NOT a real disagreement — confirmed
by comparing against a same-op-twice noise floor. `.source` is trustworthy.

## [E-007] Finding: v0.5 raw-distance baseline on real RippleEdits (GPT-J)

_Date: 2026-08-09_

Setup: popular.json, 40 edits → 245 typed pairs; base = `edit.prompt`;
representation = residual at LAST token, layer 15; cosine(base, neighbour) binned
by RippleEdits criterion → our type.

Result — cosine is near-FLAT ~0.6 across types:
  paraphrase 0.612 | 1hop 0.610 | 2hop 0.601 | locality 0.547 | control 0.654
The three propagate-types are indistinguishable (spread 0.011). No hop-decay.
Overlap confound visible only in control (overlap 0.74, highest) — not clean
elsewhere (1hop has lowest overlap 0.44 yet mid-high cosine).

Interpretation: raw last-token cosine is a weak / near-uninformative baseline —
empirically supports demoting raw distance (the design reframe), with real data.

Two caveats (do NOT over-read):
1. Not ripple — unedited model, base = counterfactual prompt string, no causal
   outcome. Measures prompt geometry, not propagation.
2. Last token is the SINK-dominated position (our 03/12 finding: attention sinks
   on token 0; last-token residual ≈ shared template). The flat ~0.6 is exactly
   what a template/sink-dominated vector predicts → flatness may be a POSITION
   artifact suppressing real signal, not a truth about raw distance.

Next (E-008): re-measure at mean-pool / subject-ish position + sweep layers to
test the sink-artifact hypothesis before concluding anything about raw distance.

Confidence: medium for "raw last-token distance is flat"; low for any deeper
claim until position/layer is swept and a causal outcome (IIA) is added.
