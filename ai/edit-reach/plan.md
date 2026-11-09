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
| D-003 | Documentor | The notebook page: what it was like to be wrong | split |
| D-004 | Documentor | The paper: structure and skeleton, every number in place | closed |
| D-005 | Documentor | The paper: prose | closed |
| D-006 | Documentor | PDF build | closed |
| D-007 | Documentor | The notebook sidebar says nothing, and the page is one slab | closed |
| D-008 | Documentor | The notebook page, shaped as a paper | closed |
| D-009 | Documentor | The front matter a paper actually has | closed |
| D-010 | Documentor | The sections a reviewer expects | closed |
| D-011 | Documentor | The column was wider than anything in it | closed |
| D-012 | Documentor | "Note 01", three left edges, and equations set as text | closed |
| D-013 | Documentor | Two thirds of the project was not on the page | closed |
| D-014 | Documentor | Outputs, charts, and two columns | closed |
| D-015 | Documentor | The body set in two columns | closed |
| D-016 | Documentor | A class name that was already taken | closed |
| D-017 | Documentor | The overview was a short version of the paper | closed |
| D-018 | Documentor | Written for the people who already knew | closed |
| D-019 | Documentor | The fault that kept coming back in different clothes | closed |
| O-001 | Orchestrator | Initialise project; extract `editreach` package; shim edit-slice | closed |
| O-003 | Orchestrator | The ticket files and the plan disagreed about what was finished | closed |
| E-001 – E-016 | Engineer | Sixteen tickets, all closed — see `agents/engineer/tickets.md` | closed |

## Blocked

| ID | Blocked By |
| --- | --- |

## Completed This Session

- E-016 · C-008 closed on branch 3 and T-002 answered. Neither a subject's prominence (+0.005, CI −0.315 to +0.314) nor its dependent count (−0.053, −0.366 to +0.270) predicts how hard an edit hits, over 41 subjects, with all six partials and both covariate controls also spanning zero. The limit is part of the result: n=41 excludes roughly |ρ| > 0.37 and nothing smaller.
- T-004 · Parked rather than dropped. `style` aims at capturing humanistic styles in AI art; the elicitation observation fell out of it sideways and has no venue. Parked with what resuming needs, which is a venue, not evidence.
- R-001, R-002 · T-011 and T-012 answered by reading, not running. A deterministic behavioural bound through a transformer is **not** unavailable in principle — Kim et al. say a compact domain makes dot-product self-attention Lipschitz and decline that route only as non-trivial work — so "no usable constant exists" is defensible and "no constant exists" is not. And weight-space certification exists but certifies an **ℓ∞ ball**: Weng et al. never consider rank-one, and evaluate MLPs on MNIST/SVHN/CIFAR-10. The positioning claim is **unclaimed in this setting**, no stronger.
- `tools/dryruns/dryrun_record.py` · three times in one session an entry was given its answer and left reading `open`. It is checked now rather than remembered. On its first run it also found E-003 and E-004 closed with no `**Artifacts:**` field at all, which is Discipline rule 1 and had stood since 2026-11-01.
- E-015 · C-007 closed on branch 2. The Cauchy–Schwarz upper bound on an edit's reach is tight in the near field (median looseness 1.05) and vacuous in the far field (21.12, 95% CI 20.16–22.14): its median far-field value of 1.1456 permits a question that never names the edited subject to receive more than the near field actually receives. Offline over cached keys, no NDIF.
- T-001 · Premise Dry-Run. The upper bound was the *easy* direction all along — one line of Cauchy–Schwarz, no enumeration, no forward pass. Spawned T-010 (measured, answered same day), T-011 (does it cross into behaviour) and T-012 (is weight-space certification the easy case, and is it taken).
- O-003 · The ticket files and `plan.md` disagreed about what was finished. All six disputed tickets were checked against their own Done-when and all six were finished; the stale `**Status:**` lines are corrected. D-004's `###` heading had been lost inside D-019's closing notes, which is why a count by heading and a count by status disagreed by one.
- D-019 · `web/blog/2026-11-09-three-checks-that-could-not-have-failed.md` — three conformance checks that could not have failed, and the count verified down from five to three.
- D-018 · A legibility pass with the research-writing skill: everything named in English before it takes a symbol, the six probe families defined from the probe file, and ticket identifiers out of the prose.
- D-017 · The overview rebuilt as the state of the work: the chain of four questions, six cards, eight threads, a figures row, and what is still missing.
- D-016 · `ocl-abstract` was already edit-slice/review's class. The paper component had been inheriting its panel and silently restyling that page.
- D-015 · The paper body set in two columns, balanced per section by spanning the headings, as a submitted paper is set.
- D-014 · Two charts drawn from the measured numbers, two run outputs copied from `results/`, and the front matter set in two columns. Seven figures, nine tables, three listings.
- D-013 · The paper filled out from the record: E-001's real result, E-002's sixty-five-to-one, E-003's destruction/destination separation, and the nine reproducibility decisions. Five findings and six runs became fourteen and fourteen.
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

**Nothing is open.** Thirty-two tickets closed, one split, none open, across all four agents — and as of O-003 the ticket files say that too, which they did not before. The question has an answer, the answer is written up, and both the page and the PDF are built from the same source.

Three things are carried forward. None of them blocks anything, and none of them is a ticket yet.

1. **Tell Natalie and Arnab.** Email 3 said *"until I show the estimate predicts measured behaviour, a screen built on it is a proposal, not an instrument."* The hedge held. What is owed now is the number — raw 0.522, excess 0.085 with an interval straddling zero — not a retraction. The direct-exposure critique is untouched. Email 1 has been unanswered since 2026-10-31, so 2 and 3 stay queued.

2. **Decide which card opens next, and the two candidates this line used to name are both spent.** It read *"T-005, or the post-hoc reading in [E-001]"*. T-005 was **answered on 2026-11-01** by [E-004] / C-004 — the coefficient is blind to the subject and sighted only on the relation, far-field excess +0.0002 against the near field's +0.8439 — and the scope sentence it was meant to license is written, in the paper's abstract and on the overview page. The post-hoc reading was **run as C-002 on 2026-10-31** on a pre-stated test: identity is worth 0.0583 against content's 0.0009, sixty-five to one. *Corrected 2026-11-09 [O-003]: this item was carried forward verbatim when the section was rewritten, without checking either candidate. Both had been closed for over a week.*

   What is actually open is five threads, and only one of them is a candidate for a card. **T-001 — can any screen bound an edit's damage from above, or only from below?** It is load-bearing: the project's result is *we can say which facts an edit touches, not how hard*, and that sentence implies an upper bound is unavailable without ever saying so. T-001 says to state it once and loudly or to find the construction. **It is not card-shaped yet** — field 2 wants one action a second person could carry out, and the question as written has none. That is the flatness signal, so the first move on it is a Premise Dry-Run, not a card.

   The other four are not next. T-002's gate has been run [R-003] and cleared: KnowledgeSmith never tested out-degree and uses no frequency variable, so both arms of T-002's falsifier are unrun by anyone. It is now a measurement, not a reading. T-003 and T-004 are positioning and a cross-project observation, neither of which closes with a number. T-009 has mostly dissolved — [E-012] found the quantity discrete rather than drifting — and its own field 6 says so: 2.2e-04 sits below every tolerance here and the anchor gate is immune by construction. It continues as a daily reading, not as a card.

3. **Two threads are open** — T-003 and T-009 — with T-004 parked — and they are the resume point, not a menu to browse during a card.

**One thing E-001 would change if it came back.** [E-047] in edit-slice blocks remote optimisation of the edit vector, so the 42 subjects are survivors rather than a sample. If NDIF answers the reproducer, E-001 should be re-run on a free draw. That is a re-open with an RCA, not a new ticket.
