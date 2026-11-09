# orchestrator tickets

### O-003 · The ticket files and the plan disagreed about what was finished

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09

**Description:**

A survey of the project's state, asked for directly ("are we done with edit-reach, is anything left?"), returned five tickets `open` and one `in-progress`. `plan.md`'s table listed every one of them `closed`. One of the two records was wrong and it was not obvious which.

Every one of the six was checked against its own **Done when**, not against the plan and not against memory:

| Ticket | Checked against | Finished? |
| --- | --- | --- |
| D-001 | `web/notebook/edit-reach/` exists, `projects.yml` entry, `Current Phase` in English | yes, 2026-11-08 |
| D-002 | five SVGs in `web/static/img/edit-reach/`, all referenced and resolving | yes, 2026-11-08 |
| D-004 | `paper/skeleton.md`, nine sections | yes, 2026-11-08 |
| D-005 | `paper/note.md`, 3,131 words | yes, 2026-11-08 |
| E-001 | `results/E-001-predicted-vs-measured.json` with `anchor_gate.passed`, an `[E-001] Result` entry in `agents/shared/decisions.md`, C-001 closed in `CARD.md` | yes, 2026-10-31 |
| E-007 | `docs/ndif-reproducibility.md` and `tools/ndif_conformance.py`, suite run against the document | yes, 2026-11-03 |

All six were finished. Four of them already carried a `**Closed:**` date and an artifact list in their own ticket; only the `**Status:**` line above it had never been changed. `plan.md` was right and the ticket files were stale.

**Two things the survey found that the question did not ask about.**

**D-004's heading was gone.** Its body sat inside D-019's closing notes with no `### D-004` line above it, so a count by heading saw nineteen documentor tickets and a count by status saw twenty. That is why the one genuinely unexplained `open` appeared to belong to D-019, which was itself closed two lines earlier. The heading is restored; the ticket is otherwise untouched.

**O-001 and O-002 are named in `plan.md` and have no tickets behind them.** Both are cited as having done work — O-001 for the project's initialisation, O-002 in the `_Last updated:_ line — and this file held `_(none open)_` until now. They are not written retroactively here, because a ticket invented after the fact is worth less than the record saying plainly that it is missing. What O-001 did is described in `plan.md`'s Completed list and that stands as its record.

**Why this is worth a ticket rather than a quiet fix.** Both records were readable, neither was obviously wrong, and the disagreement survived at least one session in which the project was reported as having no open tickets — a report made from memory rather than from the files, and wrong. The same shape as the conformance faults in D-019: a check that passed because nothing in it could have come out the other way. Reading a status line is not reading a ticket.

**Rule 7 was broken here and is recorded, not excused.** The work was done before this ticket existed. The survey was a question answered, and by the time it was clear it was a coordinate task the files had already been corrected.

**Artifacts:**

- `agents/documentor/tickets.md` — D-001, D-002, D-004, D-005 status lines; D-004 heading restored
- `agents/engineer/tickets.md` — E-001 and E-007 status lines; E-001's artifact list and closing note filled in from the results file
- `plan.md` — Next Orchestrator Action rewritten; it still read *"Run the documentation effort, D-001 first"*, which finished the day before

**Closed:** 2026-11-09. Statuses now read 32 closed, 1 split, 0 open across all four agents, which agrees with `plan.md` row for row.
