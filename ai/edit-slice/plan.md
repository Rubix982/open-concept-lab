# Project: edit-slice

_Last updated: 2026-10-14 — E-037 closed, E-038 running_

## Objective

Measure whether weight-level knowledge edits (ROME/MEMIT) leave their own
*grounds* intact and contradictory — the `orphan` category — and show that this
backward failure is worse than the forward propagation these methods were tuned
against. Done looks like a two-panel figure and a number.

## Current Phase

Phase 3 — the measurement moved onto a published benchmark's own materials. The orphan arc
remains parked on annotators and is not the blocker on anything currently moving.

## Where the work stands, 2026-10-14

The central result is established and now **controlled on materials nobody here designed**.
ROME's `u·k*` normalisation pins the update coefficient to 1 on any prompt sharing the edit
prompt's prefix to the subject's last token — analytically ([E-016]), unconstructed
([E-017]), at every layer ([E-019]/[T-075]), across four models over a 68x parameter range
([E-032]), and causally ([E-021]).

**[E-037] is the first time that measurement ran on a published benchmark with a floor built
from the same prompts.** On RippleEdits' own edits and own test prompts at layer 5:

| | own `k*` | permuted `k*` |
| --- | --- | --- |
| same-entity criteria (n=2,267) | 0.969-1.000 | 0.070 |
| Compositionality I (n=1,981) | 0.982 | 0.065 |

Separation 0.900, floor IQR under 0.05. The pre-stated outcome that would have withdrawn
the headline — templated prompts giving a near-1 coefficient for any pairing — did not
occur.

**The sharpest and least expected row is Compositionality I.** Their *different-entity*
tests name the edited subject verbatim, so a prompt designed to probe another entity
receives essentially the whole update. Whether that is a fact about RippleEdits or about
how the field builds propagation tests is **[T-088]**, and it is the cheapest open item in
the ledger.

**What delivery still does not buy.** [E-028d] put delivery and effect 2.96x apart, and
[E-029] showed displacement and efficacy explain ~18% of propagation between them. Nothing
in the record predicts the other 82% — [T-086].

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| O-003 | Orchestrator | Ten-lens design pass — discretion triage | in-progress |
| R-005b | Researcher | Read 2605.28839 + 2606.10554 bodies | open |
| E-038 | Engineer | Entity or string? the aliasing arm at power | **running** |

## Blocked

_None._

## Open Threads (the resume point)

| ID | Status | Question |
| --- | --- | --- |
| T-088 | **open** | Do other benchmarks also name the edited subject in different-entity tests? **Cheapest open item; decides what §4.6 may claim.** |
| T-087 | open | Is the alias drop graded by surface distance, or binary? Pending [E-038] |
| T-086 | open | What sets how far a layer-5 edit travels? Nothing in the record predicts 82% of it |
| T-078 | open | What reorients the subject key with depth? "cos fell" is not "context was mixed in" |
| T-081 | open | Is the floor-plus-displacement structure a *birthplace* fact? |
| T-082 | open | Is GPT-J's higher floor real, or unfamiliarity? |
| T-083 | open | Why is the floor lowest near the layer ROME edits? |
| T-041 | **ACTIVE** | Does contraction ever occur? |
| T-054 | **ACTIVE** | CounterFact has no possession check — needs re-reading, not running |
| T-058 | **ACTIVE** | Transitive containment as the deductive ground family |

Parked, each resumable cold: T-003, T-011, T-012, T-043, T-048, T-052, T-053, T-056.
**All eight serve the orphan arc, blocked on one non-technical thing — nobody has been
identified for the annotation study.**

## Completed This Session — 2026-10-14

- [R-013] RippleEdits is already subject-final: 44 of 46,754 prompts begin with their
  subject. Killed a priced week by killing its premise, in twenty minutes.
- [E-036] The coefficient on RippleEdits' own materials. Shipped a withdrawn aliasing
  conclusion and a misdiagnosed Compositionality reading; both corrected in the record.
- [E-037] The floor, measured on those same materials. 0.070 against 0.969-1.000. Arm B
  refused its own conclusion at n=9 under a pre-registered threshold of 30.
- Harness: `triage.py` taught the two-arm verdict form; `dryrun_e037.py`'s cleanup no
  longer able to name a real artifact; `preflight.py`'s cache gate accepts a per-entry
  length test.

## Next Orchestrator Action

1. **[E-038] is running** (~4.1h, 2,578 entries, all three subsets). On close it answers
   T-087 as well, since the runner records surface distance per alias.
2. **[T-088] is the next thing worth doing and needs no compute.** Read MQuAKE,
   EditPropBench and RippleBench's released prompts; count how many of their
   different-entity tests contain the edited subject's string. [R-013]-shaped, hours not
   days, and it decides whether §4.6 is a finding about the field or a note about one
   dataset.
3. **Nothing has been externally judged.** That remains the standing item and the packet —
   `web/notebook/edit-slice/review.md`, now with §4.6 — is ready for the call.
