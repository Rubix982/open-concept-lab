# Project: edit-slice

_Last updated: 2026-09-20 — E-026/E-027 opened_

## Objective

Measure whether weight-level knowledge edits (ROME/MEMIT) leave their own
*grounds* intact and contradictory — the `orphan` category — and show that this
backward failure is worse than the forward propagation these methods were tuned
against. Done looks like a two-panel figure and a number.

## Current Phase

Phase 2 — the coefficient arc. The orphan arc remains parked on annotators; it is not
the blocker on anything currently moving.

## Where the work stands, 2026-09-20

The project's central result is established across seven experiments: ROME's `u·k*`
normalisation pins the update coefficient to exactly 1 on any prompt beginning with the
edited subject — analytically ([E-016]), on an unconstructed case ([E-017]), at every layer
([E-019]/[T-075]), against a measured different-subject floor of 0.082 ([E-018]), and
causally ([E-021]).

**Everything in that arc measures DELIVERY.** How much of the edit vector arrives at a
position. Nothing measures whether delivery predicts EFFECT, and [E-016]'s scale test is
the reason it cannot be assumed. [T-075] wrote the gap into its own scope paragraph and
nobody has run it.

[T-065]'s meta-analysis of this project's own 17 results named the generative move —
*ask what a design holds fixed, and vary that* — and named the three dimensions never
varied anywhere in the record: **model**, **edit layer**, and **edited relation**. The two
tickets now open take the first two.

| ID | Thread | What it varies | Why it is decisive |
| --- | --- | --- | --- |
| E-026 | T-079 | edit layer (5 vs 20) | the coefficient predicts a DISSOCIATION nothing else predicts: subject-initial probes pinned at 1.000 and damaged identically, reordered probes at 0.615 and damaged less. A uniform reduction refutes it as surely as no reduction does. |
| E-027 | T-080 | model (Llama-3.1-8B vs GPT-J-6B) | one other architecture is the difference between "a fact about ROME" and "a fact about this model", and it is the first thing an external reader asks. |

T-081 (edited relation) is opened and unstarted — it is the third never-varied dimension.

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
| E-026 | Engineer | Does the coefficient predict displacement, or only bound it? | open |
| E-027 | Engineer | Is the pinning a ROME fact or a Llama fact? | open |

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


## Resume point — see TODO.md

_Full checklist at `TODO.md`. Summary below._

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

---

## Next Orchestrator Action — 2026-09-20

1. **E-026** — efficacy gate first (4 chains at layer 20), then the full 2x2. The gate is
   not optional: a deep edit that does not take cannot dissociate anything, and reading
   that as a Deny would be the [E-025] mistake in a new costume.
2. **E-027** — runs concurrently; independent of E-026.
3. On close, both feed §6 "What to attack" of `web/notebook/edit-slice/review.md`, which
   currently lists delivery-vs-effect as an open hole. Nothing is externally judged yet —
   that remains the standing item, and the packet is ready for the call.

**Ledger hygiene, 2026-09-20.** T-077 and T-078 were referenced in `decisions.md` and had
no entries in `threads.md` — a silent drop, fixed by backfilling both. Thread rule 1 holds:
a branch that surfaces gets an id even when nobody follows it.
