# Design — the merge

_Decided 2026-09-27. Resolves T-003, T-004, T-006. Supersedes
`design-e002-flow.md` §7._

---

## The hinge

**One ruler: how fast does the failure kill?**

The bay piece already runs on this ruler and calls it physiology. But A-before-
B-before-C is not a claim about anatomy — it is a ranking by time-to-harm, and
anatomy is merely where the fastest failures happen to live. Extending the same
ruler outward past the patient's skin is not a change of subject:

| | failure | clock |
|---|---|---|
| body | blocked airway | minutes |
| body | tension pneumothorax | minutes |
| body | haemorrhagic shock | minutes–hours |
| room | missed door-to-balloon window | hours |
| department | boarded patient deteriorating unnoticed | hours |
| department | LWBS patient returning septic | days |

Same ruler throughout. The document becomes a single axis, and the two halves
are its ends.

## What this buys that the queueing spine did not

The queueing frame (`design-e002-flow.md` §0) explained *that* crowding is an
output problem. It could not explain why a department full of people who are
excellent at the four-minute problem is reliably bad at the four-hour one.

The time-to-harm frame does: **an emergency department is built, trained and
staffed to detect failures on a fast clock, and is correspondingly blind to
failures on a slow one.** Boarding is not neglected because anyone is
careless. It is neglected because it fails on a timescale no one in the room
can feel, in a place whose every instinct is calibrated to minutes.

Little's Law survives — demoted from spine to *mechanism of the slow failure*,
which is where it belongs.

## What it breaks (move 8)

- `design-e002-flow.md` §0 named the spine as "one constraint, every word
  downstream of it." That is now the mechanism of Part III, not the spine of
  the document. The content survives intact; only its justification moves.
- The flow piece's §4 takeaway 1 ("crowding is an output problem") must be
  rewritten to sit under the ruler rather than stand alone.
- The bay piece's takeaway 1 must be generalised from "the order is
  physiology" to "the order is time-to-harm, and physiology is the fast end."

## T-006 resolved — the asymmetry is a feature

Half the merged vocabulary is universal (biology) and half is one country's
policy (EMTALA, observation status, the two-midnight rule). Under this spine
that stops being awkward and becomes a statement worth making: **the fast
failures are the same everywhere because they are physics; the slow ones
differ by country because they are design choices.** Say it in the piece.

## The hinge section

ESI is placed at the seam, and it is the reveal: the document's organising
principle turns out to be a real algorithm that hospitals already run.
Triage *is* time-to-harm ranking, written down and made auditable.

---

## Section order

**Part I — seconds to minutes · the body**
1. Airway — RSI on a clock
2. Arrest — the two-minute loop
3. Chest — needle, then tube
4. FAST — four windows
5. Lung sliding — before the x-ray
6. Shock — four failures of one circuit

**Part II — minutes to hours · the room**
7. The drug board
8. What the monitor is saying
9. The clocks — door-to-balloon, door-to-needle, the sepsis bundle
   _(where time-to-harm stops being physiology and becomes logistics)_

**Hinge**
10. ESI — the ranking, written down

**Part III — hours to days · the department**
11. The door — EMTALA, and why the ED absorbs everything
12. The board — where the time actually goes
13. Boarding — the failure on the slow clock
14. Dispo — where everyone terminates

**Closing**
15. The acronym wall — regrouped by timescale, not by topic
16. Takeaways — restated across the whole ruler

## Navigation

The ruler becomes visible furniture: a persistent timescale strip under the
existing section nav, marking where the reader is on the seconds→days axis.
It *supplements* the section nav rather than replacing it — replacing it would
trade usability for a concept.

## T-005 — length, still the real risk

Sixteen sections and nine animated panels. Current file is 265 KB, of which
158 KB is embedded fonts; merged content lands around 330 KB. Size is not the
problem, attention is. The mitigation is that the axis gives the reader a map,
so length becomes navigable rather than endless.

This is a mitigation, not a proof. If the merged piece reads as a scroll
rather than a document, splitting back into two cross-linked files is a
legitimate retreat and not a failure. Decide by reading it, not in advance.

## Title

Working: **"The Pitt, Decoded — ranked by how fast it kills."**
Alternatives considered: "Four Minutes and Four Hours"; "The Two Clocks"
(rejected — there are not two clocks, there is one ruler, and the whole point
is that it is continuous).
