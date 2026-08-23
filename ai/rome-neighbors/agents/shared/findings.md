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

## [T-015] ROME set up & running, but no-covariance config doesn't flip predictions

_Date: 2026-08-23 · EasyEdit isolated venv, gpt2-small_

Real ROME runs via EasyEdit (v-optimization works: P(target) 0.0003→0.99 in value
space; deltas computed + inserted). BUT with mom2_adjustment=false (the shortcut
to skip covariance stats), the applied rank-1 update does NOT change the model's
next-token argmax (POST still " Paris" for Eiffel→Rome), even though EasyEdit's
teacher-forcing rewrite_acc reports 1.0 (misleading — argmax unchanged). Confirmed
`edited is editor.model` (in-place), POST argmax = PRE argmax.

**Diagnosis:** without the C^-1 covariance term (mom2_adjustment=true), the update
direction uses raw k instead of C^-1 k → misdirected/ineffective. The no-stats
shortcut doesn't produce working edits. Also possible: gpt2-xl config params
(clamp_norm_factor, v_loss_layer, layer) don't transfer cleanly to gpt2-small.
Next: enable mom2_adjustment=true (EasyEdit computes stats from wikitext) — the
real ROME — and/or tune the gpt2 config. Good Arnab question: does gpt2 ROME need
the mom2 stats to flip argmax, or is this a config issue?

T-015 instrument is BUILT and ready (controlled_edits.json, rome_study.py 3-way,
viz.py blast-radius) — it produces the graph the moment a working edit exists.

Confidence: high (argmax directly checked PRE/POST on the in-place edited model).

## [T-015] RESULT: real ROME 3-way — over-propagation + target-bleed (26 records)

_Date: 2026-08-23 · gpt2-small, ROME (mom2 covariance ON), 5 controlled edits, all efficacy=YES_

Two EasyEdit fixes needed (external ~/code/EasyEdit): (1) layer_stats.py num_workers
2→0 (macOS spawn can't pickle nested collate_fn); (2) edit() calls restore_after_edit
(editor.py:295) → returned model is UN-edited; disabled via monkeypatch in rome_study.py
(our own snapshot/restore isolates edits). THEN all edits flip (efficacy=YES).

3-way outcome by type:
  paraphrase  updated 5/5      (edit generalizes to rephrasings — clean)
  1hop        broken 4, stale 1 (country rarely survives)
  2hop        updated 3, broken 2 (language propagates OFTEN — non-monotone!)
  reverse     stale 1/1
  locality    fine 4, broken 6  (ROME leaks ~60% — better than FT's 94%, not clean)

**Non-obvious findings (the special cases to study — T-015's point):**
1. NON-MONOTONE: 1hop (country) breaks MORE than 2hop (language). Naive hop-decay
   is wrong here.
2. OVER-PROPAGATION w/ WRONG GRANULARITY: edit pushes the target CITY into the 1hop
   COUNTRY slot (Louvre→Madrid ⇒ "country of Louvre" = "Madrid" not "Spain";
   Colosseum→Athens ⇒ country "Athens"). Edit reaches neighbour, wrong value-type.
3. TARGET-BLEED into locality: edit target appears in unrelated facts (BigBen→Berlin
   ⇒ "Eiffel Tower is in" = "Berlin"). The real specificity failure.
4. MEASUREMENT REFINEMENT NEEDED: locality the model never knew (pre==post=="P")
   is mislabelled "broken" — should exclude pre-edit-unknown facts / compare to pre.

Artifacts: results/rome_study.json (26 rows), results/rome_blast_radius.png.
Next: refine outcome logic (exclude pre-unknown; separate over-propagation from
incoherent-broken); then per-case study of WHY country breaks but language survives.

Confidence: high (edits verified efficacy=YES; patterns clear even at n=5 edits).
gpt2-small caveat; scale with a bigger model on GPU.

## [T-016] Prior-art / scoop check (Asta): KEEP is not greenfield — predictor partly scooped

_Date: 2026-08-23 · source: Asta literature search, PDF+txt in experiments/edit_propagation/_

Ran the WHY-gate prior-art lens (lens 2) via Asta on the KEEP framing
(predict→edit→evaluate→repair→certify wrapper for ripple/portability). Doc is
legitimate: real papers, quoted abstracts. Per-box honest status:

- **Predict (box 1) — PARTIALLY SCOOPED.** GradSim (Qin et al. 2024, "Why Does New
  Knowledge Create Messy Ripple Effects") predicts ripple success from gradient
  cosine-sim between edited fact & related facts, validated across models/editors/
  metrics. We cannot claim "first predictor." Whitespace to beat it: per-neighbour
  (vs aggregate/correlational), representation-based & cheaper (no backward pass),
  wired into repair (GradSim is diagnostic only). Our cosine/bilinear/Jeong-STEAM
  predictors must now ALSO beat GradSim as incumbent baseline. THIS IS THE MAIN EXPOSURE.
- **Repair (box 4) — OPEN but crowded.** No detect→targeted-repair→re-test loop, but
  many propagation-improvers exist: KEDAS, RippleCOT, Bidirectional-Edit, ChainEdit,
  CaKE, MeLLo. "First repair" is FALSE; "first reactive/targeted/detection-driven
  repair" is defensible — must benchmark against these.
- **Certification — cleanest open gap.** No editor-agnostic layer certifies a bounded
  neighbourhood of consequences. Field explicitly names it missing.
- **Benchmarks/metrics to adopt** (comparability): RippleEdits, MQuAKE-CF-3k/2002/
  HARD, CRAFT, KEBench, KnowGIC, BidirectionalCounterfact; STEAM Edit Score, Jeong
  entity-level errors (Persistence/Mismatch/Distortion), IFR (leakage).

**Positioning shift (applied to design_system.md §0/§1/§2):** lead with the SYSTEM +
CERTIFICATION (the whitespace, and the infra-engineer edge); demote predictor to
"cheaper/per-neighbour vs GradSim"; reframe repair as reactive/targeted.

**Honesty flag:** Asta's "full stack is unclaimed" is tagged (Model-Generated) — its
own synthesis, NOT a cited claim. Component facts are citation-backed; the "therefore
first" inference is not. Do NOT write "first" in a title until independently confirmed.
Question for Arnab: is the predict+repair+certify wrapper genuinely unclaimed?

Scoop risk: MODERATE-HIGH overall (Zhejiang/Zhang-Yao, Tel Aviv/Geva, Princeton-
Stanford/Zhong-Chen, Heng Ji, Tang/Baser/Jeong 2025). LOW on certification specifically.

Confidence: high on component prior art (quoted abstracts); medium on the
"full-stack unclaimed" conclusion (Asta synthesis, needs human confirm).

## [T-017] The category correction: editing and RAG are different functions, not competitors

_Date: 2026-08-24 · settled framing (design_system.md §0.5)_

**The error we were making:** treating editing and RAG as competitors on one scale,
and reading editing's weak multi-hop/ripple numbers as a defeat. They are not
competitors — different functions. Grading editing on multi-hop = grading it on RAG's
exam. This also reconciles the MEMIT figure that opened this thread: MEMIT holding ~90
at 10K edits is editing SUCCEEDING at its job (belief); the multi-hop collapse is
editing being asked to do RAG's job (composition).

**Axiom (settled):** Editing changes what the model BELIEVES (persistent, always-on,
on-device, removable — reasons *from*). RAG supplies what the model REASONS OVER at
inference (fresh, retrievable, citable, reversible). Different functions → different
metrics. Honor both; engineer the seam, not the winner.

**Belief vs composition:** belief = direct assertion (editing does well, MEMIT ~90);
composition = use in a reasoning chain / multi-hop (RAG does better — fact-in-context
reasoned over natively; why in-context beats parametric on RippleEdits, MeLLo on MQuAKE).

**Boundary (avoids "editing = patch table" collapse):** editing owns belief + its
REPRESENTATIONALLY-LOCAL neighbourhood (fact, paraphrases, tightly-entailed facts
sharing the representation); RAG owns composition needing CHAINING to other facts.
Sharp test: an edit must carry to what SHARES its representation, not to what requires
reasoning to reach. Where the line falls = empirical = T-006 (re-centred).

**Why editing not just RAG (Q1 deepened):** RAG structurally CANNOT (1) remove
weight-knowledge (unlearning: privacy/copyright/safety), (2) make an update pervasive/
always-on, (3) work with no retrieval infra (on-device/frozen/latency). = editing's
irreducible territory. = the Manifesto bet (persistent layer, not re-feed layer).

**Honesty flag (Manifesto Q2):** the principle (both matter) is TRUE but NOT novel —
surveys gesture at complementarity. Clears Q1 (true?) not Q2 (one step further?). The
step-further is what we BUILD AT THE SEAM, not the stance.

**Open fork (one real decision left):**
- Fork A — editing-side reliability, teeth = removal/unlearning (RAG can't do it).
- Fork B — the edit/RAG seam: route updates to the right store + certify the
  parametric belief and retrieval store don't contradict. New, infra-shaped, honors
  both. CURRENT LEAN: B.
Gate: Asta scoop-check on B (edit/RAG routing/consistency layer) and on removal-
reliability BEFORE picking. See design_system.md "Verification queued".

**Consequence for the doc:** §0/§1 (ripple-repair framing) PARTLY SUPERSEDED; rewrite
after the fork is picked. Retired: "make editing pass the multi-hop exam."

Confidence: high on the category correction (settled in discussion, reconciles all
evidence incl. MEMIT figure); the fork choice is pending prior-art verification.

## [T-018] Fork resolved → B (edit/RAG seam), but claim repositioned (Asta round-2, verified)

_Date: 2026-08-24 · source: Asta round-2, "Knowledge Edit Propagation, Locality,
Multi-Hop Chaining, and Complementary RAG.{pdf,txt}" — VERIFIED against source doc_

Asta's headline: B (edit/RAG seam) UNCLAIMED/LOW scoop, "claim first to route+certify";
A (removal-reliability) PARTIALLY-CLAIMED/MODERATE-HIGH. Recommends B.

**Verification against the source (discipline: don't trust the summary):**
- CONFIRMED: complementary editing+RAG framing is citation-backed (Liu et al. 2025
  "edit skipping"; field treats them as different jobs). §0.5 axiom well-supported.
- CONFIRMED: parametric↔retrieval consistency-certification appears genuinely unbuilt.
- **CORRECTION (important): Asta UNDERSOLD the closest competitor.** Zhang et al. 2025
  "Memory in LLMs" proposes **DMM Gov** — a NAMED governance framework that already
  SPECIFIES B: "coordinating DAPT/PEFT/editing (ROME/MEND/MEMIT/SERAC)/RAG into an
  auditable loop covering admission thresholds, rollout, monitoring, rollback, audits,
  with specs for conflict handling and long-horizon consistency." So "first to
  route/certify" is FALSE — the architecture is published as a spec. Genuine gap is
  narrower: nobody has BUILT + EMPIRICALLY CERTIFIED the parametric↔retrieval
  consistency mechanism DMM Gov only describes.
- **CORRECTION: Direction-A verdict under-evidenced by THIS doc** — TOFU/WMDP/SalUn/
  MUSE/"Harry Potter" (the unlearning citations Asta leaned on) are NOT in the
  retrieved document; pulled from general knowledge. A's scoop verdict unverified here.
- CORRECTION: scoop risk is NOT "LOW" — the doc's Open-Challenges section explicitly
  names hybrid edit/RAG as THE future direction ⇒ active frontier, move with speed.

**Decision: Fork B, with repositioned claim.**
NOT "first hybrid memory router" (Zhang DMM Gov specs it). INSTEAD:
> "First to BUILD and EMPIRICALLY CERTIFY the parametric↔retrieval consistency
> mechanism that DMM Gov specifies but leaves unimplemented."
Manifesto-Q2 clean: one verifiable step past a named prior framework. Anchor on the
concrete buildable piece (the consistency-certifier: detect when edited parametric
belief contradicts the retrieval store), not the grand router.

**Next:** rewrite design §0/§1 around B + the repositioned claim; re-pass lenses
3 (claim), 4 (completeness), 9 (deliverable = the consistency-certification figure).

Confidence: high on the correction (verified against source doc, DMM Gov quote is
direct); B chosen over A partly because A's scoop verdict is unverified by this search.

## [E-014] RESULT: scaled ripple study on RANDOM RippleEdits — landmarks were optimistic

_Date: 2026-08-24 · gpt2-small · ROME(mom2) · popular.json random sample (seed 1538)_

Anti-cherry-pick: replaced the 5 hand-picked landmarks with 100 RANDOM RippleEdits
edits. 97% efficacy (subject = last " of "-chunk heuristic + efficacy filter → 97/100
flipped; heuristic validated by efficacy). 90 flipped edits produced 397 neighbour rows.

4-way distribution (updated/stale/broken/fine):
  paraphrase  n=178  updated 57%  stale 23%  broken 20%
  1hop        n= 46  updated  4%  stale 61%  broken 35%
  2hop        n=170  updated  8%  stale 11%  broken 81%
  locality    n=  3  broken 100%   ← UNMEASURABLE (see caveat)

**KEY (the honesty correction):** the landmark set [T-015] showed paraphrase 5/5=100%
updated; at random scale it is **57%**. Cherry-picking confirmed; the clean story does
NOT fully generalize. Also REVISES a landmark finding: on 5 landmarks 1hop *broke*
(4/5); at scale 1hop is predominantly **stale** (61%) — the edit doesn't reach it.
2hop overwhelmingly breaks (81%).

**Caveats (must state):**
1. Locality UNMEASURABLE at this scale (n=3): the competence filter correctly drops
   locality neighbours the model can't answer pre-edit, and gpt2-small knows almost
   none → cannot report specificity here. Needs a capable model / facts-model-knows.
2. gpt2-small weak → absolute rates capacity-bound; the SHAPE transfers, not the %.
3. "broken" is generate-substring based; subject heuristic imperfect (but 97% efficacy).

Artifacts: scale_study.py, aggregate_scale.py, results/scale_study.json (397),
scale_distribution.png (the anti-cherry-pick figure), scale_summary.txt, scale_run.log.
Next: E-015 NDIF inference data (predictor/geometry on GPT-J); bigger model for locality.

Confidence: high (n=397, random sample); locality inconclusive; rates gpt2-small-bound.

## [E-014 addendum] Over-propagation rises with hop; run is deterministic

_Date: 2026-08-24 · rigor pass on the 397-row scale study_

**Mechanism (quantified, ±95% Wilson CI).** Of BROKEN neighbours, the fraction that
are TARGET-BLEED (the edit's new value injected into the neighbour's slot) rises
monotonically with hop distance:
  paraphrase  0% [0,10]   ·  1hop 25% [10,49]  ·  2hop 58% [50,66]
→ at 2 hops the MAJORITY of breakage is the edited value spilling, not random noise.
This is the concrete "over-propagation" finding at scale (was anecdotal in [T-015]).

**Reproducibility verified.** N=6 smoke and the first 6 edits of the N=100 run give
IDENTICAL rows/outcomes (23 rows: para u4/s3/b4, 1hop s3/b1, 2hop b8). Seeded sampling
+ greedy decode + cached ROME templates/stats → deterministic.

**Shareable package (results/):** scale_distribution.png (figure), scale_summary.txt
(rates ± CI + bleed), scale_examples.txt (concrete cases), scale_study.json (397 rows),
scale_run.log, README.md (full repro: env, data, seed, commands, caveats).

Confidence: high. Locality still needs a capable model (n=3 here).
