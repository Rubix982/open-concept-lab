# Project: edit-reach

_Last updated: 2026-11-09 by O-002_

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
| D-007 | Documentor | The notebook sidebar says nothing, and the page is one slab | closed |
| D-008 | Documentor | The notebook page, shaped as a paper | closed |
| D-009 | Documentor | The front matter a paper actually has | closed |
| D-010 | Documentor | The sections a reviewer expects | closed |
| D-011 | Documentor | The column was wider than anything in it | closed |
| D-012 | Documentor | "Note 01", three left edges, and equations set as text | closed |
| O-001 | Orchestrator | Initialise project; extract `editreach` package; shim edit-slice | closed |
| E-001 – E-014 | Engineer | Fourteen tickets, all closed — see `agents/engineer/tickets.md` | closed |

## Blocked

| ID | Blocked By |
| --- | --- |
| D-003 | — (unblocked) |
| D-006 | Saif's decision on installing a PDF toolchain |

## Completed This Session

- D-012 · The page renamed to Paper, the layout reduced to two widths on one centre line, and the equations rendered with KaTeX, which the site had been configured for all along.
- D-011 · Paper-mode layout: a full-width container with the text capped at the measure, so figures take the column and tables sit between. The `float` prop removed.
- D-010 · Note 01 reorganised under Introduction / Related work / Methods / Implementation / Results / Findings and claims / Limitations / Conclusion. The restructure produced a Related work section the page did not have, and three references to carry it.
- D-009 · Front matter, abstract and contributions, and a notebook rail that shows each project's stage. Ported from a competing design Saif generated in Lovable, which was better on the rail and on type size.
- D-008 · `web/notebook/edit-reach/note-01.md` — the notebook page as a paper: running head, numbered sections, inline citations, floated figures, bordered tables, a findings ledger carrying a falsifier on every row, and a provenance table behind every number. Nine new MDX components in `web/src/components/Paper.tsx`, documented in `notebook/writing-here.md`. Also closed the four `TODO(cite)` in `paper/note.md` — all four were already `verified: true` in `web/data/papers.yml`.
- D-007 · The notebook sidebar rewritten by hand (`web/sidebars.ts`) and the edit-reach page split into four. Raised by Saif on sight of the live page: autogeneration made a one-page project and a three-page project render as different kinds of thing, and the labels were directory names.
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
