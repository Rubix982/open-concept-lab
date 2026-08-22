# rome-neighbors — results & demo (for Natalie & Arnab)

_Outcomes first → runnable programs → honest boundaries → next direction._

---

## 0 · The vision (why this matters)

A technique companies can use to **reliably, cheaply, and frequently update a
deployed model's knowledge** — without retraining and without RAG's every-query
overhead. Flagship case: **a medical model kept current with the newest research**
— new trial results, revised guidelines, corrected facts, edited *in* the model so
they propagate through its reasoning, not bolted on as context.

The load-bearing question underneath that vision: **when you edit one fact, does it
correctly propagate to everything it logically implies — and can we predict/guarantee
which related facts stay correct vs. break?** An edit you can't trust to propagate
(or to *not* corrupt neighbours) can't be used in medicine. So this project studies
exactly the reliability gap between "the edit worked" and "the model is still
consistent." That gap is what stands between knowledge-editing and real deployment.

---

## 1 · Outcomes achieved

**The pivotal reframe:** you can't predict which neighbours an edit breaks without
*making the edit first*. Spine flipped: **edit → measure real propagation → then
find the geometry that predicts it.**

1. **Real edit → propagation pipeline (built from scratch).** FT-L weight edits +
   per-neighbour pre/post measurement → **reproduced the ripple-failure phenomenon**
   (Cohen/Zhong) on our own stack: entailed neighbours rarely update, decaying with
   hop distance (paraphrase/1-hop ~20% → **2-hop 0%**).

2. **The 3-way outcome exposed specificity failure (an honest correction).** Naive
   full-matrix FT is a *wrecking ball* — 88% of neighbours BROKEN incl. **94% of
   unrelated locality**. (This corrected an earlier "locality preserved" read that
   was wrong.) Editing without specificity constraints corrupts the model broadly.

3. **Read ROME/MEMIT source → isolated the specificity mechanism.** Specificity =
   **rank-1 update + C⁻¹ covariance orthogonalization + KL locality penalty**. We
   tested adding just KL+weight-decay to our FT → **barely helped (still ~86%
   broken)**, isolating that the **rank-1 (low-rank) constraint is the key** — not
   regularization. A real mechanistic takeaway.

4. **First thesis test against ground truth (T-B).** Does representational closeness
   predict which neighbours the edit reached? Overall **AUC 0.68** (faint signal),
   but cosines ~0.998 both classes (template-saturated) → raw distance too coarse.
   The *method* (predictor → real propagation → AUC/hop) works end-to-end.

5. **Real ROME running** via EasyEdit (isolated venv) — the specificity-preserving
   editor, quarantined from our stack. v-optimization works (P(target) 0.0003→0.99).

6. **T-015 instrument built** — controlled well-known edit set + 3-way classifier
   (updated/stale/broken/fine) + **blast-radius graph** viz. Ready to run the moment
   ROME flips predictions (see boundary below).

7. **Positioning done** — Asta ×3 + full NDIF corpus: the specific lane (hop-resolved
   + causal + predictor comparison) is unclaimed; SLAQ/Kim/Jeong/Huang/Nishi placed.

---

## 2 · Runnable programs (live demo)

| Program | Shows |
|---------|-------|
| `experiments/edit_propagation/edit_ft.py` | FT edit → 3-way outcome (the wrecking-ball baseline) |
| `experiments/edit_propagation/rome_study.py` | real ROME edit → updated/stale/broken/fine |
| `experiments/edit_propagation/viz.py` | blast-radius graph of an edit's effect on neighbours |
| `experiments/edit_propagation/analyze_tb.py` | predictor vs. real propagation (AUC/hop) |
| `experiments/preflight_demo/run.py` | raw-distance vs alignment baseline |
| `scratch/01–13` | NNSight curriculum (logit lens, ablation, causal tracing, attention, `.source`) |

Two-venv architecture: `.venv` (ripplekit + nnsight/NDIF, representations/analysis)
· `.venv-edit` (EasyEdit + ROME/MEMIT/FT, weight editing). They meet through saved data.

---

## 3 · Honest boundaries hit today (tested, not assumed)

- **NDIF is inference-only** — single in-trace weight-set + backward work, but
  *iterative* edits don't (one-forward/job). → real editing is **local**. (Also hit
  a post-outage whitelist regression — reported to NDIF Discord; since fixed.)
- **gpt2-medium NaNs at the logits** on this Mac in *both* stacks (transformers 5.15
  and 5.5.4) — machine/model-specific; gpt2-small is reliable.
- **ROME needs the covariance stats.** With `mom2_adjustment=false` (no stats), the
  v-optimization runs but the applied edit **does not flip the argmax** (rewrite_acc
  1.0 is misleading). Real ROME needs `mom2_adjustment=true` (C⁻¹) — next brick.
- **Mac-local editing is a friction sink** (no CUDA, NaNs, EasyEdit assumes GPU) →
  strategic question below.

---

## 4 · Next direction & questions for you

**Immediate:** enable ROME's covariance (`mom2_adjustment=true`, EasyEdit computes
stats) → a *working* specific edit → run the T-015 3-way study + blast-radius graph.
Then study the stale/broken neighbours: what must be true (position? subject-sharing?
causal routing?) to turn them into "fine"?

**Questions for you:**
1. Does gpt2 ROME need the mom2 covariance stats to actually flip predictions, or is
   our config off? (Arnab — MEMIT.)
2. **Compute substrate:** keep fighting Mac-local, or move editing to a GPU (Colab /
   cloud) so ROME/MEMIT + bigger models "just work"? What do you use?
3. Causal outcome: interchange/IIA vs. actual weight edits for measuring propagation?
4. RAVEL vs RippleEdits as the cleaner hop-resolved substrate?
5. Biggest hole you'd attack in the T-015 / diagnostic design?

**Where it's going:** the 3-way "which facts an edit will break/leave-stale" is the
**pre-flight diagnostic** — the reliability layer a medical-model-updating product
would require. That's the through-line from today's bricks to the vision.
