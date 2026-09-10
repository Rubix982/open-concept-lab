# Project: edit-slice

_Last updated: 2026-09-10 by O-002 (dry-run appended)_

## Objective

Measure whether weight-level knowledge edits (ROME/MEMIT) leave their own
*grounds* intact and contradictory — the `orphan` category — and show that this
backward failure is worse than the forward propagation these methods were tuned
against. Done looks like a two-panel figure and a number.

## Current Phase

Phase 0 — Definitions & scope resolution (near complete)

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| O-001 | Orchestrator | Initialize project structure | closed |
| D-001 | Documentor | Write notes/definitions.md | closed |
| O-002 | Orchestrator | Resolve edit-slice / rome-neighbors scope collision | closed |
| R-001 | Researcher | Read Cohen et al. RippleEdits test types directly | closed |

## Blocked

_None._

## Completed This Session

- O-001 · Initialized project structure
- D-001 · notes/definitions.md written — the meeting artifact
- O-002 · Scope collision resolved: reuse code, not scope
- R-001 · RippleEdits LG is not a grounds probe; claim 1 narrowed, declaration 5 added

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
| T-012 | open | Grounds by intervention, not enumeration (may kill T-006) |
| T-013 | open | Do kernels survive transfer to a graded setting? |
| T-014 | open | Salvage from the cut material |

## Next Orchestrator Action

**T-012 and T-010 first** — they change what gets built. T-012 decides whether
the pilot needs the compiler at all; T-010 decides which sign counts as success,
and no figure can exist until it is settled. T-004 (design-lens pass) remains the
gate on any implement ticket, and R-001's **medium** confidence means dependents
open as **spikes**, not implementations.
