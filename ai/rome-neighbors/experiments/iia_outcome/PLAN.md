# E-010 — Causal outcome: does the predictor predict *propagation*?

_The thesis-closing brick. Design first — for Arnab's review before building._
_Companion to `design.md`; this pins the causal-outcome specifics that design.md
left open._

## Why this exists

E-007→E-009 measure **representation geometry** of prompts on the *unedited*
model — raw distance (flat) vs. structured alignment (candidate). But separating
neighbour types is **not** the claim. The claim is:

> geometry predicts whether an edit **propagates** to a neighbour.

That needs a per-neighbour **propagation label** with a **causal** basis. This
plan defines it, and surfaces the one methodological fork only an expert should
settle.

## The fork (the question for Arnab)

**How do we obtain a causal "did it propagate?" signal per neighbour?**

**Option A — actual edit.** ROME/MEMIT-edit the fact (EasyEdit), then query each
neighbour; propagation = neighbour answer changed to the edit-consistent value.
- Pro: the real thing; directly the deployment quantity; comparable to RippleEdits.
- Con: needs **local weight access** — NDIF is inference-only, can't edit remotely.
  Means a local GPT-J (or smaller) + GPU, a different compute path than everything
  built so far.

**Option B — interchange / IIA (no weight edit).** Via `nnpatch`: run the neighbour
prompt in a *base* (old-fact) and a *counterfactual* (new-fact) context; patch the
edited attribute's representation at the causal site from counterfactual→base;
propagation = the neighbour's answer flips to the counterfactual value.
- Pro: **NDIF-doable**; reuses our whole stack; a clean causal handle.
- Con: it's a **proxy** for editing — "would this neighbour read a changed
  attribute?" not "does ROME's rank-1 update reach it." Construct-validity risk.

**Ask Arnab:** is interchange-IIA a defensible proxy for edit propagation, or does
the claim require actual ROME edits? (He co-wrote MEMIT — this is his exact turf.)
His answer decides A vs. B, i.e., the whole compute path.

## Design lenses (the parts specific to the causal outcome)

- **Hypothesis / falsification:** predictor (alignment/bilinear) correlates with
  per-neighbour propagation (IIA), and the correlation is strongest at the hops
  where editing is known to fail (1-hop/2-hop). Null: predictor ⟂ propagation →
  geometry doesn't forecast propagation (redirect to circuit-level).
- **Confound — pre-edit knowledge:** propagation is undefined if the model never
  knew the neighbour. **Control:** filter to neighbours the unedited model answers
  correctly pre-edit (the E-001 competence filter), before scoring propagation.
- **Confound — edit success:** only score propagation on edits that *took* (target
  fact actually changed). Filter to successful edits first.
- **Baseline:** predictor must beat (a) hop-count alone and (b) raw distance, via
  partial correlation. Real claim = "structure predicts propagation *after*
  removing hop-count + raw-distance."
- **Deliverable:** AUC (predictor → propagation) **per hop bin** — one bar/line
  group per predictor. The headline figure.

## Build (once A/B settled)

- `experiments/iia_outcome/run.py` on `jkminder/nnpatch` (Option B) or EasyEdit
  (Option A).
- Reuse `ripplekit` reps/predictors for the geometry side; add an `outcome.py`
  for the causal label.
- Start tiny (5–10 edits) to validate the interchange mechanics before scaling.

## Status

Design only. Do not build until the A/B fork is settled with Arnab (Monday).
This is the "no experiment before the question passes the lenses" rule — the
lens that's still open here is **construct validity of the outcome**, and the
right reviewer for it is the MEMIT co-author.
