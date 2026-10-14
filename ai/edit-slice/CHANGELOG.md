# Changelog

## 2026-09-10 · Session 1

- [O-001] Initialized edit-slice project structure — plan.md, threads.md, agents/**, notes/refs/probes/src/results
- [D-001] Definitions page written — notes/definitions.md (five declarations + outcome vocabulary)
- [O-002] Scope collision with rome-neighbors resolved: reuse code, not scope — threads.md T-001, spawned T-005
- [R-001] RippleEdits' Logical Generalization confirmed NOT a grounds probe; core claim 1 narrowed to justification-order backwardness — agents/shared/findings.md, definitions.md declaration 5

## 2026-09-11 → 2026-10-13 · NOT LOGGED

This file records Session 1 and then stops. The work between — roughly [E-002] through
[E-035], [R-002] through [R-013], and the thread ledger's growth to 86 — happened and is
recorded, but **not here**. The entries were never written at the time.

**They are not being reconstructed.** Session boundaries are not recoverable from the git
history, and a changelog whose sessions were inferred afterwards is a changelog that lies
about when things were known. The record that *is* trustworthy for this period:
`agents/shared/decisions.md` and `findings.md` (dated, append-only, each with its
falsification stated before the run), `threads.md`, `logs/`, and the git history itself.
The generated [evidence ledger](../../web/notebook/edit-slice/ledger) reads from those.

Noted rather than quietly left blank, because an empty month reads as an idle one.

## 2026-10-14 · Session — the benchmark arc

- [R-013] RippleEdits is already subject-final — 44 of 46,754 prompts begin with their
  subject. Killed a priced week by killing its premise, in twenty minutes —
  `results/R-013-ripple-forms.json`
- [E-036] The coefficient on RippleEdits' own edits and prompts. Shipped two defects: a
  withdrawn aliasing conclusion drawn from 8 near-identical strings, and a Compositionality
  reading misdiagnosed as a measurement error when the prediction was what failed. Both
  corrected in the record — `agents/shared/decisions.md`
- [E-037] The floor, built from those same prompts: **0.070** against same-entity
  0.969–1.000, separation 0.900. Arm B refused its own conclusion at n=9 under a
  pre-registered threshold of 30 — `results/E-037-ripple-floor-recent.json`
- [R-014] MQuAKE names the edited subject **iff** the edit is on hop 1 — 6,861 of 6,861,
  and 0 of 16,506. Makes MQuAKE a within-benchmark control nobody has to construct —
  `results/R-014-mquake-forms.json`
- [R-014b] The other two benchmarks cannot be counted: RippleBench has no findable public
  release (blocked); EditPropBench edits manuscripts, not weights (dropped, out of scope)
- [E-038] opened and running — the aliasing arm over all three subsets, 371 different-surface
  aliases against the threshold of 30
- [E-039] opened, built and queued — MQuAKE hop-1 against hop-2+, with a relation-matched
  sub-comparison (P495, 34 vs 58) the ticket did not anticipate
- [T-087], [T-088] opened; [T-088] answered by [R-014]
- Harness: `triage.py` taught the two-arm verdict form after it stopped a healthy queue;
  `dryrun_e037.py`'s cleanup deleted a 40-minute result and no longer can; `preflight.py`'s
  cache gate accepts a per-entry length test
- `bearing`: four bugs in two checks, one of which penalised the fix it existed to ask for
- Write-up: §4.6 added (Tables 11 and 12), abstract rewritten to carry it, §7 item 2's
  question answered and replaced with a narrower one — `web/notebook/edit-slice/review.md`
