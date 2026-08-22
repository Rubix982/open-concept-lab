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

## [E-011] Finding: local backend unblock + gpt2-small is flat

_Date: 2026-08-22_

**Infra:** NDIF regressed post-outage (rejects nnsight 0.7.0 traces server-side:
`intervention.batching not whitelisted`; reported to NDIF Discord). Pivoted to a
LOCAL transformers backend (config.BACKEND=local) — full pipeline now runs on-
machine via `output_hidden_states` on MPS, no NDIF. gpt2-large fp32 stalls
loading on M2 (memory); gpt2 / gpt2-medium work.

**Result (gpt2-small, mean-pool, RippleEdits popular, 30 edits, 171 pairs):**
BOTH predictors flat — cosine ≈ 0.99 for EVERY neighbour type incl. locality/
control. sep(raw)≈+0.006, sep(align)≈-0.001. Neither raw distance nor alignment
separates types.

**Interpretation:** not a thesis result — a model/representation artifact. On
short templated prompts ("The X is in the city of"), gpt2-small's mean-pooled
residual is dominated by the SHARED TEMPLATE, washing out entity/fact signal
(even unrelated locality facts look identical). Consistent with the lookback
finding that gpt2-small is too weak. Two implications for method (design.md §5
construct validity): (a) need a capable model (gpt2-medium+ / GPT-J); (b) mean-
pool over templated prompts may be the wrong readout — consider subject-token
or last-token reps. The pipeline + figures work end-to-end locally; the signal
needs a stronger substrate.

Confidence: high for "pipeline works locally + gpt2-small flat"; the thesis
comparison (does structure beat raw distance) is UNTESTED until a capable model.

## [E-011b] Finding: pooling + capacity both matter; alignment doesn't win yet

_Date: 2026-08-22 · local backend, gpt2-medium fp16, RippleEdits popular, 171 pairs_

Ran the predictor comparison across pooling × layer on a capable-ish local model:

**Mean-pool:** cosine ≈ 0.99 for EVERY type, both predictors. sep ≈ 0. Confirmed
across gpt2-small AND gpt2-medium → mean-pool over templated RippleEdits prompts
is template-dominated; washes out entity signal. Mean-pool is the WRONG readout.

**Last-token (gpt2-medium):** raw cosine ~0.80 with a faint, layer-increasing
signal in the RIGHT direction — sep(raw) +0.007→+0.019 (L12→L18), propagate-types
above locality. Alignment sep ≈ 0 (does NOT beat raw distance here).

**Cross-ref E-007 (GPT-J last-token):** sep ~+0.06 — larger than gpt2-medium's
+0.019. So both CAPACITY and READOUT matter, both in the expected direction.

**Honest state of the thesis:** on a modest local model neither predictor STRONGLY
separates; last-token raw distance is weakly informative; structured alignment (as
implemented — small answer-string anchors) does not win. This is a weak/negative
result, consistent with design.md's pre-stated "deny" branch. Caveats: (1) needs
the capable model (GPT-J/NDIF) — capacity clearly helps; (2) alignment impl may be
under-powered (anchor quality); (3) the real test is the CAUSAL outcome (E-010 IIA),
not prompt-geometry separation. Motivates E-010, not abandons the thesis.

Confidence: high for "mean-pool washes out / last-token + capacity help / alignment
doesn't win on gpt2-medium"; the thesis verdict needs GPT-J + the causal outcome.

## [E-012] Finding: NDIF editing-capability boundary (empirical)

_Date: 2026-08-22 · verified against GPT-J-6B on NDIF (whitelist regression fixed)_

Tested whether Path A (actual weight edit) is doable on NDIF's remote GPT-J:
- Single in-trace weight SET: WORKS (zeroing fc_out[8] moved logP(Paris) 18.5→17.25).
- Single in-trace BACKWARD/gradient: WORKS (grad-norm 236544 on fc_out[8].weight).
- MULTI-STEP iterative edit: FAILS — one nnsight trace = ONE forward pass; the
  graph frees after the first backward (retain_graph), and weights don't persist
  across separate remote traces (shared model). FT/ROME need iterative optimization
  → don't fit NDIF's one-forward-per-job inference model.
- GPT-J MLP down-proj is `mlp.fc_out` (not GPT-2's `c_proj`).

**Conclusion (resolves the A/B fork with evidence):** actual iterative weight
editing is fundamentally LOCAL (NDIF is shared inference infra). On NDIF the
capable model is available for INFERENCE + single-step/activation interventions,
not clean weight edits. So:
- Path A (real weight edit) → LOCAL (fix FT-L NaN: lower lr + grad-clip, on
  gpt2-medium; or ROME via EasyEdit in an isolated venv).
- Path B (causal outcome on the CAPABLE model) → interchange/activation patching
  on GPT-J via NDIF — fits the one-forward model, uses the model that knows the facts.

This is the exact NDIF-editing question for Arnab (he fixed NDIF today; co-wrote MEMIT).

Confidence: high (each capability directly tested on NDIF today).

## [E-012] RESULT: first real edit→propagation table — ripple failure reproduced

_Date: 2026-08-22 · gpt2-small, FT-L edits (layer 4 mlp.c_proj), 15 edits (7 flipped), RippleEdits popular_

The T-A deliverable: real weight edits → ground-truth per-neighbour propagation.
  paraphrase  18.8% (n=32)
  1hop        20.0% (n=5)
  2hop         0.0% (n=21)
  locality     4.0% (n=25)  ← mostly preserved (good specificity)
  control      0.0% (n=2)

**Propagation DECAYS with hop distance** (paraphrase/1hop ~19-20% → 2hop 0%) while
locality is largely intact. This reproduces the ripple-failure phenomenon (Cohen
RippleEdits, Zhong MQuAKE) on our own stack, with our own FT-L pipeline — the
foundation that was missing. This table is the TARGET T-B predictors correlate against.

Caveats: gpt2-small is weak (only 7/15 edits flip; small per-type n, esp. 1hop n=5);
absolute rates low partly from model capacity. The PATTERN (hop-decay + locality
preserved) is the right shape and matches the literature. Next: stronger model
(gpt2-medium blocked by a stack-specific logits-NaN — body finite, NaN at
ln_f/lm_head in torch2.13/transformers5.15/CPU-fp32; or GPT-J interchange), then
T-B: do geometry predictors predict this per-neighbour propagation?

Confidence: high for "pipeline works + ripple-decay reproduced"; per-type rates
are indicative only (small n, weak model).

## [E-013] RESULT: T-B — does geometry predict REAL propagation? (weak signal)

_Date: 2026-08-22 · gpt2-small, 85 neighbour rows (8 propagated), predictor = pre-edit cos(edited-fact, neighbour) @ layer 6_

First test of the actual thesis against GROUND TRUTH (not a proxy): does a
neighbour's representational closeness predict whether the edit reached it?

  ALL         AUC=0.683  (mean pred propagated 0.998 vs missed 0.998)
  paraphrase  AUC=0.660  (6/32)
  1hop        AUC=1.000  (1/5  — single positive, unreliable)
  2hop        AUC=nan    (0/21 propagated — nothing to rank)
  locality    AUC=0.958  (1/25 — single positive)

**Read:** overall AUC 0.68 > 0.5 → a faint real signal (closer neighbours
propagate more). BUT the cosines are ~0.998 for BOTH classes (template-saturated);
the AUC rides on 4th-decimal gaps → razor-thin. n tiny (8 propagated); per-hop
AUCs are single-positive artifacts; 2hop/control undefined.

**Verdict:** the METHOD works end-to-end (predictor → real propagation → AUC/hop).
Raw closeness carries only a faint, fragile signal — too coarse, as expected.
Directly motivates (now against real labels): structured predictors (bilinear /
edit-difference vector) + a stronger model + more edits for power. This is the
honest first answer to the project's core question, with the full pipeline in place.

Confidence: method high; the 0.68 is suggestive only (tiny n, template-saturated cos).

## [E-013/T-015] RESULT + CORRECTION: naive FT-L is destructive (breaks ~90%)

_Date: 2026-08-22 · gpt2-small, 155 neighbour rows, 3-way outcome_

3-way outcome (updated/stale/broken):
  ALL        updated 14  stale 4  BROKEN 137 (88%)
  paraphrase updated 10  stale 0  broken 39
  2hop       updated  0  stale 0  broken 32
  locality   updated  2  stale 2  BROKEN 60 (94%)

**CORRECTION of E-012 read:** E-012 reported "locality 4% → mostly preserved" —
that 4% was "% matching the expected UNCHANGED value", i.e. 96% of locality facts
CHANGED = a SPECIFICITY FAILURE. The 3-way confirms locality is 94% broken. The
earlier "preserved ✓" gloss was WRONG.

**Finding:** naive full-weight FT-L lacks specificity — it corrupts ~90% of
neighbours (incl. unrelated locality), not just the target. This is exactly why
ROME/MEMIT add locality/KL constraints. Implication: we CANNOT cleanly study
stale-vs-broken until the edit is specific enough that not everything breaks →
need constrained FT (KL/locality term) or ROME.

**Bug:** subject_shared = 0 for all 155 rows (subject_id intersection never hit)
— format mismatch (edit subject_id str vs neighbour subject_id list, possibly
different entity). Fix before testing the subject-sharing hypothesis (T-015).

AUC(predictor vs updated) overall 0.72 but cosines ~0.998 both classes (still
template-saturated) — unchanged conclusion: raw distance too coarse.

Confidence: high (destructiveness is stark and corrects a prior overclaim).
Next: (1) add specificity to the edit; (2) fix subject_id matching; (3) then T-015.

## [T-015] RESULT: KL+weight-decay does NOT fix specificity → rank-1 is the key

_Date: 2026-08-22 · gpt2-small, FT+L (KL locality + weight decay), 243 neighbour rows_

FT+L 3-way: ALL updated 18 / stale 15 / BROKEN 210 (86%); locality 113/127 broken
(89%). Vs plain FT (94% locality broken) — only MARGINAL improvement.

**Finding:** adding ROME's KL-locality + weight-decay penalty to a FULL-MATRIX FT
does NOT restore specificity. Isolates that ROME's specificity comes primarily
from the RANK-1 constraint (optimize one direction), not the KL regularizer:
full c_proj (~4M params) has too much freedom for a 5-prompt KL to constrain.
Compounding factor: gpt2-small is tiny (little redundancy → any mid-layer edit
perturbs broadly). → Next brick: RANK-1 constrained edit (ΔW = a⊗b, optimize
two vectors — the ROME core) and/or a bigger model. Specificity ≈ low-rank, not
regularization — a real mechanistic takeaway.

Confidence: high for "KL alone insufficient on full-matrix FT"; small-model +
basic-KL caveats noted. Full ROME (rank-1 + C^-1) would be the clean comparison.
