# Project: ROME Neighbors — Neighborhood Consistency in Model Editing

_Last updated: 2026-07-22 by O-001_

## Objective

When a fact is edited in a language model (e.g. "The Eiffel Tower is in Paris"
→ "The Eiffel Tower is in Rome"), the logically entailed *neighbor* facts should
also update. They usually don't. Understand why, measure the gap precisely, and
explore what would be needed to fix it.

Greenlit by Natalie (Bau Lab) — 2026-07-22.

## The Core Problem

A single factual edit carries **implicit logical consequences** — neighbors:

  F  : "The Eiffel Tower is in Rome"         ← the edit
  N1 : "What city is the Eiffel Tower in?"   → Rome      (direct paraphrase)
  N2 : "What country is the Eiffel Tower in?" → Italy    (one hop: Rome → Italy)
  N3 : "What language is spoken near the Eiffel Tower?" → Italian (two hops)
  N4 : "What is in Rome?" → [includes Eiffel Tower]     (reverse lookup)

ROME edits F correctly. N1 sometimes follows. N2–N4 almost never do.
This is the **ripple effect gap**: edits are local, but facts are relational.

## Research Questions

1. **How far does a ROME edit propagate?** Measure accuracy at N1, N2, N3, N4
   hops from the edited fact on GPT-J-6B via NDIF.
2. **Where does propagation fail?** Is it an attention failure, an MLP storage
   failure, or a retrieval failure?
3. **What does the residual stream look like at neighbor queries?** Do the
   activations at the edited subject position change after the edit?
4. **Can a second targeted edit fix a neighbor?** Manual cascade editing —
   does editing N2 explicitly after editing F restore consistency?

## Current Phase

Phase 2 — Implementation (reframed project: does structured geometry predict edit
propagation? See `design.md`). Positioning done (Asta ×3 + full NDIF corpus →
`readings/MAP.md`); codebase established (`ripplekit/`).

## Active Tickets

| ID    | Agent      | Title                                      | Status      |
| ----- | ---------- | ------------------------------------------ | ----------- |
| O-002 | Orchestrat | Establish `ripplekit/` codebase structure  | closed      |
| E-007 | Engineer   | v0.5 raw-distance baseline (RippleEdits)   | done (flat) |
| E-008 | Engineer   | Position/layer sweep (sink-artifact test)  | built       |
| E-009 | Engineer   | Structured predictor: alignment            | built       |
| E-010 | Engineer   | Causal outcome: IIA (build on `nnpatch`)   | open        |

## Blocked

_(none)_

## Completed This Session

- O-002 · `ripplekit/` package (config, data, reps, predictors, analysis) +
  README, pyproject, .gitignore; pure-Python modules verified against real data
- E-005 · Spike closed — storage band ~2–12 (subject), readout ~12–17 (last tok)
- E-007 · baseline done — raw last-token cosine near-flat ~0.6 (findings.md)
- Positioning · lane confirmed open (combination-novelty); Arnab = verifier

## Experiment Sequence (reframed)

1. E-007 baseline (done — raw distance flat) → 2. E-008 position/layer sweep
(is flatness a sink artifact?) → 3. E-009 structured/alignment predictor
(does structure separate where distance didn't?) → 4. **E-010 causal outcome
(IIA on `nnpatch`)** — turns "separates types" into "predicts propagation".
Migrate demo scripts onto `ripplekit/` as each is revisited.
Human gate: confirm lane + coordinate with **Arnab** before scaling.

## North Star

> See the gap yourself: edit one fact on GPT-J-6B, watch the neighbors fail,
> understand mechanistically *where* the failure lives.

## Morning resume (2026-08-24)

**Vision (added):** reliable, frequent, cheap model knowledge-updates for research —
flagship: a medical model kept current with newest research. The pre-flight
diagnostic (which facts an edit breaks/leaves-stale) is the reliability layer.

**Where we stopped:** real ROME runs (EasyEdit, .venv-edit) but the no-covariance
config (mom2_adjustment=false) doesn't flip argmax. T-015 instrument (controlled
edits + 3-way study + blast-radius viz) is BUILT and waiting on a working edit.

**First brick tomorrow:** run the mom2_adjustment=true ROME test (config already
written: `experiments/edit_propagation/rome_gpt2_mom2.yaml`, 3000-sample stats):
    source .venv-edit/bin/activate
    ROME_CFG=rome_gpt2_mom2.yaml python experiments/edit_propagation/rome_study.py
    python experiments/edit_propagation/viz.py        # blast-radius graph
If it flips → real T-015 data + the graph. If not → tune config / ask Arnab / move
to GPU substrate.

**For Monday:** presentation/SESSION_RESULTS.md (vision → outcomes → programs →
boundaries → questions for Arnab).
