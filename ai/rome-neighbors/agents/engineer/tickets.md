# Engineer Tickets

### E-001 · Baseline fact recall on GPT-J-6B (NDIF)

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Description:**
Before editing anything, establish which facts GPT-J-6B already knows and
can recall reliably. Pick 10 subject-relation-object triples from CounterFact,
probe the model's recall at baseline (unedited), record accuracy.

This is the prerequisite for all editing experiments — you can only measure
the ripple effect if you know what the model knew before the edit.

**Implementation steps:**
1. Pick 10 triples from CounterFact where GPT-J-6B answers correctly
2. For each triple, format as a cloze prompt: "The Eiffel Tower is located in"
3. Run via NNSight remote trace on NDIF (GPT-J-6B)
4. Record: top-1 token, logit of correct token, rank of correct token
5. Filter to triples with rank ≤ 5 (model knows the fact)

**Success criterion:** ≥8/10 triples recalled correctly (rank ≤ 5).

**Artifacts:**
- `experiments/baseline_recall/recall.py`
- `experiments/baseline_recall/data/triples.json`
- `experiments/baseline_recall/output/recall_results.json`

**Closed:** —

---

### E-002 · Single ROME edit on GPT-J-6B

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Blockers:**
- E-001 (need confirmed-recalled triples before editing)

**Description:**
Apply a single ROME edit to GPT-J-6B using the `rome` Python library.
Edit one fact from E-001's confirmed set. Verify the edit worked (model now
answers the new object). This is infrastructure — we need the edit machinery
working before probing neighbors.

**Implementation steps:**
1. Install `rome` library (or implement rank-1 update manually using NDIF)
2. Pick one triple: subject=S, relation=R, old_object=O, new_object=O*
3. Apply ROME edit to GPT-J-6B
4. Verify: cloze prompt now returns O* at rank 1
5. Verify: unrelated facts unchanged (specificity check)

**Artifacts:**
- `experiments/single_edit/edit.py`
- `experiments/single_edit/output/edit_verification.json`

**Closed:** —

---

### E-003 · Neighbor probe after ROME edit

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Blockers:**
- E-002 (need working edit before probing neighbors)

**Description:**
After the E-002 edit, probe all neighbor fact types (N0–N4) for the edited
subject. Measure how many update correctly, how many stay at the old value,
and how many become incoherent.

This is the core experiment — the gap between N0 accuracy and N2+ accuracy
is the ripple effect failure we are studying.

**Neighbor queries to probe:**
- N0: Paraphrase of the edited fact
- N1: One-hop consequence (e.g. city → country)
- N2: Two-hop consequence (city → country → language)
- N4: Reverse (what is now at the new location?)

**Artifacts:**
- `experiments/neighbor_probe/probe.py`
- `experiments/neighbor_probe/data/neighbor_queries.json`
- `experiments/neighbor_probe/output/neighbor_accuracy.json`
- `experiments/neighbor_probe/output/neighbor_accuracy.png`

**Closed:** —

---

### E-004 · Ripple sweep — 10 edits, all neighbor types

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Blockers:**
- E-003 (validate neighbor probing on one edit first)

**Description:**
Scale E-003 to all 10 triples from E-001. For each edit, measure N0–N4
accuracy. Produce a summary table and plot showing where ripple propagation
fails systematically.

**Artifacts:**
- `experiments/ripple_sweep/sweep.py`
- `experiments/ripple_sweep/output/ripple_matrix.png`

**Closed:** —

---

### E-005 · Spike: NNSight localization curriculum on GPT-J-6B

**Status:** closed
**Type:** spike
**Priority:** medium
**Created:** 2026-08-04 (logged retroactively — work was exploratory)
**Updated:** 2026-08-04

**Description:**
Time-boxed exploratory spike to build fluency with NNSight's read/write API on
GPT-J-6B via NDIF, and to observe where a factual association ("Eiffel Tower →
Paris") is stored vs. read out. Foundation/warm-up for the causal-tracing work
that E-002/E-003 depend on. Ran as a learning curriculum, not a scoped
experiment — hence a spike, logged after the fact per ticket discipline.

**What was built (scratch/):**
- `01_logit_lens.py` — logit lens across all 28 layers (readout crystallisation)
- `02_residual_stream.py` — residual norm + relative change at the subject token
- `03_ablation.py` — position-specific zeroing sweeps (subject vs. last token)
- `04_causal_tracing.py` — corrupt-restore AIE (not yet run; has known fixes pending)
- `06_lm_head_explore.py` — full logits / top-k / per-position predictions
- `08_readout_vs_storage.py` — combined readout-vs-storage plot (+ PNG)
- `05_gptj_healthcheck.py`, `07_*` — NDIF connectivity / scratch

**NNSight lessons learned (also in memory `reference-nnsight`):**
- nnsight 0.7: appending individual `.save()` proxies in a loop returns empty —
  stack into one tensor and save that instead.
- remote=True: locally-built mask tensors are on CPU while activations are on
  cuda:0 → device-mismatch error. Use direct indexed assignment, not mask-multiply.
- `h[L].output[0]` is the CUMULATIVE residual stream, not a layer's marginal
  contribution — zeroing it is catastrophic at every layer (does not localize).

**Findings:** logged to `agents/shared/findings.md` → E-005.

**Artifacts:**
- `scratch/01`–`08` exploration scripts
- `scratch/08_readout_vs_storage.png`
- `readings/metrics/notes.md` (IIA + metric-families reference)

**Closed:** 2026-08-04

---

### E-006 · Spike: explore what NNSight `.source` exposes on GPT-J-6B

**Status:** in-progress
**Type:** spike
**Priority:** medium
**Created:** 2026-08-09
**Updated:** 2026-08-09

**Description:**
`.source` reads a module's `forward()` source and exposes each operation inside
it as a hook point — a level finer than the module-boundary `.output`/`.input`
we have used so far. Map what it actually gives us on GPT-J-6B, since operation
names are model-specific and must be discovered, not guessed.

**Planned experiment set (each a scratch script):**
1. `09_source_discovery.py` — print `.source` for block / attn / mlp / ln_f /
   lm_head. LOCAL (source introspection, no remote). Reveals the real op names.
   ← THIS SESSION; the rest are gated on its output.
2. `10_source_capture.py` — remote: grab several intermediate op outputs, print
   their shapes; confirm we can reach non-boundary intermediates.
3. `11_source_sanity.py` — verify a source-op output equals the matching
   submodule `.output` where they coincide (trust check).
4. `12_source_attention.py` — extract the attention weights (softmax output
   inside attn.forward) and plot which tokens the answer position attends to.
   Serves the deferred attention-maps thread.
5. `13_source_intervene.py` — zero/patch an intermediate op (e.g. one head's
   contribution), measure the effect on P('Paris'). Operation-level ablation.

**Success criterion:** `09` prints usable operation names for GPT-J's attention
and MLP; we can then reach at least one non-boundary intermediate (`10`).

**Artifacts:**
- `scratch/09`–`13` (09 this session; 10–13 grounded in 09's output)
- findings → `agents/shared/findings.md` → E-006

**Closed:** —

---

### E-007 · v0.1 demo: raw representation similarity by neighbour type (GPT-J)

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-08-09
**Updated:** 2026-08-09

**Description:**
Smallest end-to-end slice of the design (design.md) that runs on GPT-J via NDIF
and produces real numbers. Computes the BASELINE predictor only — raw cosine
similarity between a base fact's representation and each of its typed neighbours
(paraphrase / 1-hop / 2-hop / locality-control) — aggregated by neighbour type,
alongside a token-overlap readout that EXPOSES the surface-form confound.

This is deliberately the confounded baseline: the demo's honest point is that raw
last-token similarity tracks template overlap more than fact-relatedness, which
is exactly why the design adds structured (Kim) + alignment (Jeong) predictors.
So the demo both produces a first figure AND motivates the reframe.

**Scope:** ~6 hand-curated base facts × 4 typed neighbours; residual at last
token, one mid layer (15); cosine similarity; per-type means; token-overlap
(Jaccard) confound readout; one bar plot. NOT the full study (no editing, no IIA,
no hop-resolved propagation — those are v1).

**Maps to design.md:** experiments step 3 (baseline predictor), secondary
deliverable ("does even raw distance track neighbour type?").

**Artifacts:**
- `experiments/demo_distance_by_type/demo.py`
- `experiments/demo_distance_by_type/data/demo_facts.json`
- `experiments/demo_distance_by_type/output/similarity_by_type.png`

**Closed:** —
