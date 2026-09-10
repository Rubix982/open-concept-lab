# Project: edit-slice

_Last updated: 2026-09-10 by O-002 (dry-run appended)_

## Objective

Measure whether weight-level knowledge edits (ROME/MEMIT) leave their own
*grounds* intact and contradictory — the `orphan` category — and show that this
backward failure is worse than the forward propagation these methods were tuned
against. Done looks like a two-panel figure and a number.

## Current Phase

Phase 2 — Existence test. Possession re-opened (E-005): first measure could not separate knowledge from surface plausibility.

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| O-001 | Orchestrator | Initialize project structure | closed |
| D-001 | Documentor | Write notes/definitions.md | closed |
| O-002 | Orchestrator | Resolve edit-slice / rome-neighbors scope collision | closed |
| R-001 | Researcher | Read Cohen et al. RippleEdits test types directly | closed |
| O-003 | Orchestrator | Ten-lens design pass — discretion triage | in-progress |
| R-002 | Researcher | Lens 2 prior-art search (WHY gate) | closed |
| R-003 | Researcher | CounterFact relation inventory (T-023) | closed |
| R-005a | Researcher | Mined-rule artifact obtainable? | closed |
| R-005b | Researcher | Read 2605.28839 + 2606.10554 bodies | open |

## Blocked

_None._

## Completed This Session

- O-001 · Initialized project structure
- D-001 · notes/definitions.md written — the meeting artifact
- O-002 · Scope collision resolved: reuse code, not scope
- R-001 · RippleEdits LG is not a grounds probe; claim 1 narrowed, declaration 5 added
- O-003 · design.md written — project reframed as reusable discretion triage
- R-002 · Lens 2 cleared — not scooped; positioning revised against intra-memory
  conflict and uncertainty-based deferral

## Open Threads (the resume point)

| ID | Status | Question |
| --- | --- | --- |
| T-003 | open | Can RippleBench-Maker's distance function take a code dependency graph? |
| T-004 | open | Does the backward-probe pilot survive the ten design lenses? |
| T-005 | open | Which rome-neighbors modules may edit-slice import? |
| T-006 | open | Is the grounds relation decidable in the CounterFact setting at all? |
| T-007 | active | Is forward/backward really expansion/contraction? (AGM + kernels) |
| T-008 | open | Does backward terminate without `k`? |
| T-009 | open | Kernel count as the backward out-degree variable |
| T-010 | open | Metric sign error — should grounds fall or hold? |
| T-011 | open | Is orphaning structural to expansion operators as a class? |
| T-012 | **active** | Grounds by intervention — design.md §0 gate, load-bearing, no data |
| T-013 | open | Do kernels survive transfer to a graded setting? |
| T-014 | open | Salvage from the cut material |
| T-035 | superseded | Mined Horn rules — dead over DBpedia [E-001], reframed by [E-002] |
| T-038 | open | Is a plausibility threshold better than an arbitrary `k`, or just renamed? |
| T-039 | answered | Possession measured: gpt2 61% vs Llama-70B 93% [E-003] |
| T-045 | **active** | Possession of the EDIT target (GPT-J), not just the audited model |
| E-003 | **superseded** | Possession numbers — random distractors admit surface-cue scoring |
| E-004 | **superseded** | Joint possession — measure did not discriminate (top-3 = 100%) |
| E-005 | open | Re-measure possession against hard negatives mined from the model's prior |
| T-046 | open | Reframe deliverable as the possession/structure map |
| T-047 | open | Lens 2 second pass — factual probing, not editing |
| T-048 | open | Grain confound in head-vs-ground comparison |
| T-041 | **active** | Does contraction ever occur on hand-built deductive grounds? |
| T-043 | open | Dimension space of a knowledge bit — entrenchment undefined |

## Next Orchestrator Action

**E-001 — the §0 spike.** Lens 2 cleared 2026-09-10, so the WHY gate is passed.
The gate is now whether **mined Horn rule bodies** recover grounds (design.md
§0 method e, roles flipped v0.5) — with directed intervention demoted to
validation. Time-boxed; ~20 hand-labelled edits as the agreement check, plus the
fraction of mined bodies passing the direction test. Then R-003 (T-023 relation inventory), then R-004 to close
the residual scoop surface (EasyEdit, T-003).

Opens as a **spike**, not an implementation: R-001 is medium confidence and §0
has no data.

R-003 closed: 35.4% of CounterFact (7,770 edits) uses a rigid relation, so the
edit-selection gate passes with large headroom. The binding constraint has moved
to whether those rigid edits have *mined grounds* in DBpedia — E-001's job.

R-005a closed: the artifact is MIT-licensed with rules included, so method (e) is
feasible. Two corrections it forced — the KG is **DBpedia** not Wikidata, and
their edit sets are **MQuAKE/MLaKE** not CounterFact. E-001 must decide whether
to re-run their pipeline over CounterFact entities (preferred) or switch edit
sets. This partially reopens T-023, whose vocabulary is now likely DBpedia.

Non-technical risk with no technical fix: the annotation study (design.md lens 8)
needs 2-3 real annotators and none are identified.
