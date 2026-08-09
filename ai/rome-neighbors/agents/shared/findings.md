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
