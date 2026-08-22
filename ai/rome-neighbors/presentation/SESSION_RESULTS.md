# rome-neighbors — session results & demo

_For Natalie & Arnab · outcomes first, then live programs, then direction._

---

## 1 · Outcomes achieved

**The pivotal reframe:** you can't predict which neighbours an edit breaks without
*making the edit first*. So the project spine flipped from "score geometry, hope it
predicts propagation" → **edit → measure real propagation → then find the geometry
that predicts it.** Everything below follows from that.

1. **Real edit → propagation pipeline (from scratch).** FT-L weight edits (gradient
   steps on the MLP down-projection — the weights ROME edits) + per-neighbour
   pre/post measurement. → **First propagation table reproduces the ripple-failure
   phenomenon** (Cohen/Zhong) on our own stack:

   Entailed neighbours rarely *update* — propagation **decays with hop distance**:
   paraphrase/1-hop ~20% → **2-hop 0%** (the ripple-failure phenomenon).

   BUT the 3-way outcome (updated / stale / **broken**) exposed a second, honest
   finding: **naive FT-L is destructive** — it *breaks* ~88% of neighbours,
   **including 94% of unrelated locality facts**. Naive full-weight fine-tuning
   lacks specificity (this is exactly why ROME/MEMIT add locality constraints).
   *(This corrects an earlier read that locality was "preserved" — it wasn't.)*
   → we need a specificity-constrained edit before stale-vs-broken is separable.

2. **First thesis test against ground truth (T-B).** Does representational closeness
   predict which neighbours the edit reached? **Overall AUC 0.68** — a faint real
   signal — but cosines are ~0.998 for both classes (template-saturated), so raw
   distance is too coarse. The *method* (predictor → real propagation → AUC/hop)
   works end-to-end.

3. **Predictor baseline mapped (E-007/E-011).** Raw distance is a weak/flat baseline
   across gpt2-small/medium × mean/last pooling; capacity + readout both matter
   (GPT-J sep 0.06 > gpt2-medium 0.019). Structured alignment didn't beat it yet.

4. **Infrastructure, tested not assumed.** (a) NDIF remote GPT-J working; (b) mapped
   NDIF's editing boundary — single in-trace weight-set + backward work, but
   *iterative* edits don't (one-forward/job) → **real editing is local**; (c) built a
   local transformers backend so the whole pipeline is NDIF-independent.

5. **Reproducible codebase** — `ripplekit/` package (config/data/reps/predictors/
   analysis) + thin experiment runners; verified RippleEdits loader.

6. **Positioning done** — Asta ×3 + full NDIF corpus: the specific lane (hop-resolved
   + causal + predictor comparison) is unclaimed; nearest work SLAQ / Kim / Jeong /
   Huang / Nishi identified and differentiated.

---

## 2 · Runnable programs (live demo)

| Program | Shows | Output |
|---------|-------|--------|
| `experiments/edit_propagation/edit_ft.py` | real FT-L edit → propagation | `results/propagation_table.txt` |
| `experiments/edit_propagation/analyze_tb.py` | predictor vs REAL propagation | AUC per hop |
| `experiments/preflight_demo/run.py` | raw-distance vs alignment baseline | `results/predictor_arc.png` |
| `scratch/01–13` | NNSight curriculum (logit lens, ablation, causal tracing, attention, `.source`) | figures/tables |

All run locally (transformers/MPS) or remote (NDIF/GPT-J) via one config switch.

---

## 3 · Next direction

**T-015 — what makes a neighbour go stale/broken vs. fine after an edit?** Reframe to
the 3-way outcome (updated / stale / broken; locality flips polarity) and find which
*features* separate them: hop distance, representational proximity, **subject-sharing**
(Liu et al.: shared-subject facts get over-written), **causal routing** (does the
neighbour read the edited MLP site?), pre-edit competence. This 3-way "will this edit
*break* these facts" is the **pre-flight-diagnostic** vision, and it operationalizes
the deep thread (does the model's causal-read graph mirror the entailment graph?).

**Questions for you:**
1. Causal outcome: is interchange/IIA a valid stand-in for edit-propagation, or must
   it be actual weight edits? (We mapped that NDIF can't do iterative edits.)
2. RAVEL vs RippleEdits as the cleaner substrate for hop-resolved geometry?
3. Best capable-model path given local-editing constraint (gpt2-xl local? GPT-J?).
4. Biggest hole you'd attack in the T-015 design.
