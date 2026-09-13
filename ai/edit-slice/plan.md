# Project: edit-slice

_Last updated: 2026-09-10 by O-002 (dry-run appended)_

## Objective

Measure whether weight-level knowledge edits (ROME/MEMIT) leave their own
*grounds* intact and contradictory — the `orphan` category — and show that this
backward failure is worse than the forward propagation these methods were tuned
against. Done looks like a two-panel figure and a number.

## Current Phase

Phase 1 (revised) — Possession filter DELIVERED (E-007). Orphan arc parked on annotators.

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

_Triaged twice on 2026-09-11. 35 threads: 29 answered, 8 parked, 1 active._

| ID | Status | Question |
| --- | --- | --- |
| T-054 | **ACTIVE** | CounterFact has no possession check at all — verified from source [D-002] |
| T-057 | answered | No filter; ROME Table 4 reports ES=22.2 unedited, appendix D confirms |
| T-055 | answered | Coordination lift works set-level (+2.39/+1.61), not per-candidate |

| T-041 | **ACTIVE** | Does contraction ever occur? Un-parked — was misattributed to the annotation study |
| T-058 | **ACTIVE** | Transitive containment as the deductive ground family |

Parked, each with a resume-cold note: T-003 (RippleBench swap), T-011 (orphaning
structural to expansion operators), T-012 (directed intervention), T-043 (dimension
space), T-048 (grain confound), T-052 (star vs chain), T-053 (generic question
generation), T-056 (dual-facet nouns — a candidate *next* project).

**The annotation study blocks the triage tool's `contested` validation only.** It
does not block T-041, which is an existence claim. That misattribution parked an
arc for four days.

The parked set is coherent, not scattered: **all eight serve the orphan arc, which
is blocked on one thing — nobody has been identified for the annotation study.**


## Resume point — 2026-09-14

**E-008 is mid-run.** The chain miner was stopped partway; no
`probes/containment_chains.json` yet. Nothing is lost: the Wikidata snapshot
`2026-09-14` banked 109 links / 187 entities / 217 labels, and the miner reads
through it, so rerunning resumes from cache:

    .venv/bin/python agents/engineer/workspace/mine_chains.py --refresh --seeds 120

Then: report attrition, write `probes/containment_chains.md` as the contestable
artifact, and **possession-filter all three facts per chain** before anything
enters the experiment — a chain whose inner-2 the model does not hold cannot test
contraction [T-058].

## Next Orchestrator Action

**Deliver the possession filter** (design.md lens 9, revised). Two steps:

1. **R-007** — read 2505.18690 "Benchmarking and Rethinking Knowledge Editing", the
   nearest remaining competitor. PDF would not extract and OpenReview is behind a
   verification wall; try the ACL Anthology or a direct request. Blocks the
   write-up, not the tool.
2. **E-007** — package the filter: possession check over an arbitrary edit set,
   local or NDIF, reporting held/not-held by relation with the candidate-set size
   and model recorded alongside.

The orphan arc resumes when an annotator is named. That is the single blocker, and
it is not technical.