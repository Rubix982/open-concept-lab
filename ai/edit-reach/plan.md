# Project: edit-reach

_Last updated: 2026-11-08 by O-002_

## Objective

Establish whether an edit's reach can be predicted before the edit is applied — and if it can, say with what error rates; if it cannot, say so and retire the proposal.

## Current Phase

Answered, and the answer is negative. The coefficient detects contamination rather than propagation: C-001 closed denied, and in the far field a stranger's edit on the same relation reaches a question as much as the real subject's does, excess +0.0002. C-002 closed on branch 1 — identity is worth about 65x content. No card is open; the work now is writing it up, in six documentor tickets that run nothing new.

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| D-001 | Documentor | Notebook section for edit-reach, and the scope statement | closed |
| D-002 | Documentor | The four diagrams | closed |
| D-003 | Documentor | The notebook page: what it was like to be wrong | open |
| D-004 | Documentor | The paper: structure and skeleton, every number in place | closed |
| D-005 | Documentor | The paper: prose | closed |
| D-006 | Documentor | PDF build | blocked |
| O-001 | Orchestrator | Initialise project; extract `editreach` package; shim edit-slice | closed |
| E-001 – E-014 | Engineer | Fourteen tickets, all closed — see `agents/engineer/tickets.md` | closed |

## Blocked

| ID | Blocked By |
| --- | --- |
| D-003 | — (unblocked) |
| D-006 | Saif's decision on installing a PDF toolchain |

## Completed This Session

- D-005 · `paper/note.md` — the draft, 3,131 words. Shape decided first (short arXiv note, general mech-interp reader); §6 written alone, then the rest measured against it.
- D-004 · `paper/skeleton.md` — nine sections, five figure slots, every number carrying its ticket. Found and corrected a conflation of [E-018] with [E-038] that had already reached a figure.
- D-002 · Five figures in `web/static/img/edit-reach/`, four drawn and one reused, placed in the overview. Also added the section on whether the readings reproduce, which the page had been missing.
- D-001 · edit-reach has a page. `web/notebook/edit-reach/` — the scope statement ([E-004]) written where a reader can reach it, plus the project card, its drawing, and a `Current Phase` line that reads as English rather than shorthand.
- O-001 · Project initialised. Six infrastructure modules lifted unchanged from `ai/edit-slice/src` into an installable `editreach` package; `coefficient.py` and `control.py` added; edit-slice's flat names replaced with forwarding shims; 13 tests pass; 24 of 25 distinct consumer import lines verified (the 25th, `apply_delta` in `debug_apply2.py`, was already broken in the committed original).

## Next Orchestrator Action

Run the documentation effort, D-001 first. The project's question has an answer; what it does not have is a reader. Every number the six tickets need is already measured and recorded, so none of them opens a card and none of them runs anything.

Two things carried forward, neither of which blocks the writing.

1. **Tell Natalie and Arnab.** Email 3 said "until I show the estimate predicts measured behaviour, a screen built on it is a proposal, not an instrument." The hedge held; what is owed now is the number, not a retraction. The direct-exposure critique itself is untouched, and saying both plainly is the whole message.
2. **Decide which card opens next.** The honest candidates are T-005 (is the coefficient blind in the far field, where propagation lives) and the post-hoc reading recorded in [E-001] — that subject-keyed movement may be the phenomenon rather than the confound. The second must not be worked on as a rescue of C-001; it needs its own six fields, written before any data is looked at again.
