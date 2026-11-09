# documentor tickets

The effort these track: **turn edit-reach's answer into something a person outside the project can read.** Two artifacts, one body of evidence.

- **A — the notebook section** (`web/notebook/edit-reach/`). Living pages, revised in place. What the instrument does, and what it was like to find out it does less than proposed.
- **B — the paper** (PDF). The same evidence in the shape the field reads, as an orientation piece. A negative result with a working control, not a novelty claim.

No `CARD.md` is opened for this. A card is for a question whose answer is not yet known; every number below is already measured, reviewed and recorded. What is missing is the writing.

Source of every number: `agents/shared/decisions.md` [E-001]–[E-013], `results/*.json`, and `docs/ndif-reproducibility.md`. **No new runs.** If a number cannot be traced to one of those, it does not go in.

---

### D-001 · Notebook section for edit-reach, and the scope statement

**Status:** open
**Type:** document
**Priority:** high
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 2h

**Description:**
edit-reach has no page anywhere on the site and no entry in `web/data/projects.yml`. Create the section and its overview page, whose argument is the scope narrowing recorded in [E-004]: **the coefficient is a contamination detector, not a propagation detector.** That sentence is currently written nowhere a reader can reach.

Files:

- `web/notebook/edit-reach/_category_.json` — label `edit-reach`, position 3, `collapsed: false`.
- `web/notebook/edit-reach/index.md` — front matter per `web/notebook/writing-here.md` (title, sidebar_label `Overview`, sidebar_position 1, description).
- `web/data/projects.yml` — add the entry; `plan: ai/edit-reach/plan.md`, `notebook: /notebook/edit-reach/`, `tone: draft`.
- `ai/edit-reach/plan.md` — rewrite the `## Current Phase` line. The site reads it verbatim and it currently says *"Phase 2 closed. C-002 answered on branch 1: identity is worth ~65x content (paired medians +0.0583 against +0.0009). C-001 closed denied. No card is open."* — internal shorthand that reads badly on a public card. Fix the wording there, do not override it with `what:` in `projects.yml`.

The page carries, in this order:

1. What was proposed — predict an edit's reach from one forward pass through the **unedited** model.
2. What was asked and answered — C-001, **denied** 2026-10-31. 495 probes, 42 subjects, Llama-3.1-8B layer 5.
3. The number that carries the denial — [E-004], MQuAKE-CF-3k, 513 single-edit two-hop instances. Far field (n=900): own `k*` 0.0543, same-relation stranger floor 0.0481, excess **+0.0002**, CI (+0.0001, +0.0004). Near field (n=639): own 0.9334, same floor 0.0506, excess **+0.8439**, CI (+0.8379, +0.8500).
4. What it does detect — that a prompt names the edited subject, and the relation. RippleEdits Compositionality_I **0.982** against a **0.065** stranger floor; MQuAKE names the subject iff the edit is on hop 1, 6,861/6,861 and 0/16,506.
5. Limits — delivery is not effect (2.96× at a fixed coefficient); one layer, one model, two-hop chains; the 42 subjects are cached survivors, not a free draw ([E-047] blocks remote `v*`).

One `<Claim>` block at the top, `superseded` = the proposal that the coefficient can screen propagation items, body = the narrowed scope. Use it once; its force is in being rare.

**Blockers:** none.

**Artifacts:**
- web/notebook/edit-reach/_category_.json
- web/notebook/edit-reach/index.md
- web/data/projects.yml -> edit-reach entry
- ai/edit-reach/plan.md -> Current Phase rewritten; the site reads it verbatim
- web/scripts/draw-art.py -> `edit_reach()`; web/static/img/art/projects/edit-reach.svg

**Closed:** 2026-11-08. `npm run build` succeeds and the page renders. One thing the ticket did not foresee: adding the `projects.yml` entry made the home page reference `art/projects/edit-reach.svg`, which did not exist — a broken image on the front page, found by grepping the built HTML rather than by the build, which does not check static assets. The drawing was added to `draw-art.py` in the same style as the others; regenerating left every other SVG byte-identical.

---

### D-002 · The four diagrams

**Status:** open
**Type:** document
**Priority:** high
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 3h

**Description:**
`web/static/img/edit-slice/` does not exist and `review.md` carries two figures in 1,193 lines. Both D-003 and D-004 need pictures, and the same files serve both — which is why this is its own ticket and runs before them.

Draw to `web/static/img/edit-reach/<slug>.svg`. House style, per `writing-here.md`: hand-drawn-style SVG, an `feTurbulence` wobble over plain strokes, cream paper, ink, one indigo accent. Each must read in both light and dark mode and at phone width. Every number in a caption must appear in `decisions.md`.

1. `two-regimes.svg` — why a prompt beginning with the edited subject has a key identical to `k*` under causal attention, so `c = 1` by arithmetic, against 0.082 for a different subject. The foundation of everything else.
2. `near-and-far-field.svg` — **Figure 1 of the paper.** The same control applied twice: +0.8439 in the near field, +0.0002 in the far field. This is the picture that carries the denial.
3. `delivery-is-not-effect.svg` — the 2.96× spread of measured movement at one fixed coefficient.
4. `same-number-twice.svg` — the three layers that decide reproducibility: deployment (dtype, sharding, shape), routing (which replica served you), and inside one trace (0.000e+00 at all fifteen layer-model pairs).

Already drawn and reusable, do not redraw: `ai/edit-slice/notes/img/direct-exposure.svg` (the Leo Arons item). Copy it to `web/static/img/edit-reach/` rather than linking across projects.

**Blockers:** none.

**Artifacts:**
- web/static/img/edit-reach/near-and-far-field.svg
- web/static/img/edit-reach/two-regimes.svg
- web/static/img/edit-reach/delivery-is-not-effect.svg
- web/static/img/edit-reach/same-number-twice.svg
- web/static/img/edit-reach/direct-exposure.svg (copied from edit-slice, not redrawn)
- web/notebook/edit-reach/index.md -> five `<Figure>` blocks, and a new section, "Whether any of it reproduces", which the page had been missing entirely

**Closed:** 2026-11-08. Five figures, `npm run build` succeeds, every file referenced resolves.

Two notes for whoever reads these next.

**The figure goes before the table it illustrates, not after.** In "Where it fails" the near-and-far figure now precedes the numbers it draws. A picture placed after the table it restates reads as decoration; placed first it reads as the finding and the table reads as the record behind it.

**Nothing here was rendered and looked at.** This machine has no rasteriser — no `rsvg-convert`, no headless browser in the loop — so the layouts were reasoned about rather than seen. Collisions were found and fixed by arithmetic on text widths, which catches the gross cases and not the near ones. Four were fixed that way: a provenance line running past the canvas edge, two section labels sitting on top of arrowheads, and a bracket label starting left of the margin. Treat the first look at these in a browser as part of the work, not as a formality.

**A fabrication avoided, recorded because it was tempting.** The delivery-against-effect figure wanted a scatter — a column of points at one coefficient spreading over 2.96x. No such per-item data is in `results/`. Drawing plausible points would have invented a measurement. The figure shows the span as a bracket instead, which is the number that exists.

---

### D-003 · The notebook page: what it was like to be wrong

**Status:** open
**Type:** document
**Priority:** medium
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 3h

**Description:**
The second page of the section (`web/notebook/edit-reach/learning.md`, sidebar_position 2). D-001 says what the instrument does; this says what the work was like, and it is the part no paper has room for.

Ordered by chronology, not by dependency — this is a record, and dependency-ordering it would destroy what it shows.

The material, all of it already recorded:

- A claim written on 2026-11-03 and withdrawn the same week: [E-010] saw the arithmetic-site effect rise monotonically on the 8B and wrote *"grows with depth in bfloat16"*; [E-011] found the 70B falls 53-fold to layer 20 then rises 298-fold to layer 40. The direction was one model's artefact. The prediction written **before** that run — "adds a row, breaks nothing" — was half wrong, and that half was the result.
- `docs/ndif-reproducibility.md` corrected itself four times across five runs of its own conformance suite, with each correction left in place rather than quietly fixed.
- The recurring fault, found five times: *a check evaluated on an input that cannot express the thing it tests.* Every instance was fixed by naming the degenerate case, never by moving a number. The sharpest: `matmul_site` read 0.000e+00 because it ran on anchors, which are analytically pinned to 1.000, and would have reported "the two sites agree" forever.
- [E-004]'s first floor gave the opposite answer. Against all donors the far-field excess is +0.0232 with an interval excluding zero — which reads as real far-field signal. Nearly all donors carry a different relation, so that floor was the different-relation floor wearing another name. Found by asking what else a hop-2 subject is, not by anything in the measurement.
- The logging bug: 124 of 155 committed log files were header-only, and all 79 edit-slice scripts would have crashed on their first line. Latent since the infrastructure move, found by a dry-run written for an unrelated reason.

Hedging is quarantined into one named limits section; the body runs unhedged.

**Blockers:** D-002 (figures 1 and 4).

**Artifacts:** _(fill on close)_

**Closed:** —

---

### D-004 · The paper: structure and skeleton, every number in place

**Status:** open
**Type:** document
**Priority:** medium
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 3h

**Description:**
Section headings, figure slots, tables and every number, with the prose deferred to D-005. Separated so the argument's shape can be judged before any of it is written well.

Structure follows the ticket split, which is the paper's split: E-001–E-004 are the question, E-005–E-013 are whether the measurement can be trusted.

- Abstract.
- 1 · The proposal and why it is attractive — one forward pass, no edit applied, a quantity defined for any prompt instead of a hand-written item set.
- 2 · Related work. Nearest is He et al., arXiv 2601.04600. Cite nothing from memory; `TODO(cite)` or look it up.
- 3 · Method — the coefficient, the regimes, and the control that makes a reading exist at all.
- 4 · The near field: it works, and the reason is arithmetic rather than inference.
- 5 · The far field: it does not work. [E-004] is this section.
- 6 · Whether the measurement can be trusted — the conformance work, 15 layer-model pairs, structure exact and no magnitude portable.
- 7 · Limits.
- 8 · What this is not. **State plainly that this is a negative result with a working control and not a novelty claim**, and that the positive direction is blocked on [E-047].

Every own-claim gets its falsifier stated in the sentence. Analytic claims are flagged and ship their derivation.

**Blockers:** D-002, cleared.

**Artifacts:**
- ai/edit-reach/paper/skeleton.md

**Closed:** 2026-11-08. Nine sections, five figure slots, every number carrying its ticket.

Three things the ticket did not anticipate.

**A number was wrong, and it was wrong in the record this skeleton was built from.** `notes/where-this-stands.md` says the two coefficient groups "do not overlap across 23,505 readings". The non-overlap is [E-018] — 16 chains, highest different-subject 0.153 below lowest same-subject 0.483, gap 0.877. The 23,505 readings are [E-038]'s RippleEdits re-run, a different experiment. Two results had been welded into one sentence, and the welded version had already reached a figure drawn earlier today. Corrected in `two-regimes.svg` and in the skeleton. **`ai/edit-slice/notes/where-this-stands.md` still carries it** and is Saif's file to change.

**[E-003] earns a section the ticket did not plan for.** Destruction and destination separate in opposite directions on the same probes — destination real-minus-control +0.2828 with discordant pairs 142 to 2, destruction the other way round. It is the strongest thing in the project that is not a denial, and a paper that goes straight from the mechanism to the denial throws it away. It is now §5.

**The format decision has an input now.** Every figure is an SVG. Typst includes SVG natively; LaTeX does not, so each figure would need a conversion step and an owner. Recorded at the top of the skeleton so [D-006] does not decide this by habit.

---

### D-005 · The paper: prose

**Status:** open
**Type:** document
**Priority:** low
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 4h

**Description:**
Write D-004's skeleton out. Run the claim audit over it: every paragraph gets one sentence saying what observation would make it false, and any row with an empty fourth column is sharpened, demoted to an explicit attribution, or cut.

**Blockers:** D-004, cleared.

**Artifacts:**
- ai/edit-reach/paper/note.md
- ai/edit-reach/paper/skeleton.md -> the "Shape" section, decided 2026-11-08

**Closed:** 2026-11-08. Nine sections and an abstract, 3,131 words. Shape decided first: a short arXiv note, four to six pages, for a general mechanistic-interpretability reader rather than for people who already know the editing benchmarks.

**That pair of choices is the whole writing constraint and it is written into the skeleton.** A reader who needs the benchmarks explained, in a document with no room to explain them, is how a short note becomes a long one. Three rules settle it: no benchmark primer in §1; each benchmark introduced in the clause that uses it; Figure 1 carries §3's explanation, so if §3 still reads whole with the figure removed, too much prose has been written.

**Written §6 first, alone, and only then the rest.** §6 is the paper; the other eight sections are measured against it. Writing them in order would have produced eight sections that each seemed fine and a §6 with no room left.

**The claim audit moved three things in §6, and one of them was an overclaim of ours.** The draft said a question naming the edited subject "is not testing propagation; it is testing the edit" — which our own delivery-is-not-effect limit forbids. Now: it cannot *separate* propagation from delivery. Also cut a derived multiplier ("two thousand times smaller") that the rounding does not support, for "more than three orders of magnitude", true at both ends of the interval. And gave the sentence a reader will carry away — that an editor could score on that test while generalising nothing — its own falsifier.

**Two sections run over budget and are left there.** §6 at 1,016 words against 840, and §7 at 234 against 120. §7's overage is the withdrawn depth claim, which is the kind of thing a short note is tempted to drop and should not: a reader who finds it later in the repository should find it conceded here first.

**Unresolved and visible in the file:** four `TODO(cite)` markers. Every one is a citation nobody has verified against the paper itself, and this project's rule is that a description read off a search result is not a verified citation even when the identifier is right.

---

### D-006 · PDF build

**Status:** blocked
**Type:** implement
**Priority:** low
**Created:** 2026-11-08
**Updated:** 2026-11-08
**Estimated:** 2h

**Description:**
This machine has no PDF toolchain — `pdflatex`, `xelatex`, `tectonic`, `typst`, `pandoc`, `latexmk` and `weasyprint` are all absent. Proposed: `brew install tectonic` (self-contained LaTeX, ~50MB, fetches packages on demand) with a standard ACL or NeurIPS style, because that shape is recognised on sight.

Installing is Saif's decision and is not done without it. If he declines, the fallback is to keep the LaTeX source in the repo and compile it on Overleaf, which costs nothing here.

Deliver a one-command build and a `README` line saying how to run it.

**Blockers:** Saif's decision on installing a toolchain.

**Artifacts:** _(fill on close)_

**Closed:** —

---

### D-007 · The notebook sidebar says nothing, and the page is one slab

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1h
**Spent:** 1h

**Description:**
Raised by Saif on sight of the live page, twice. Two separate faults, both in D-001's artifact.

1. `web/notebook/edit-reach/index.md` was given `sidebar_label: Overview`, copied from edit-slice. edit-slice has three pages, so "Overview" there means *this project's overview*. edit-reach had one page, and Docusaurus absorbs a lone `index.md` into its category — so the entry rendered as a bare "Overview" sitting between edit-slice and rome-neighbors, naming nothing. The `_category_.json` also carried `position: 3`, tied with rome-neighbors; the order that resulted was luck.
2. The page was 1,916 words under seven `h2` headings and no `h3`, so the in-page table of contents offered seven navigation labels — "Where it fails", "What is in the package" — none of which states what was found.

Fix all three layers: subsection headings so the in-page contents has depth; split the page so the project has pages rather than one slab; and replace the autogenerated notebook sidebar with a written one.

**Artifacts:**
- web/sidebars.ts — rewritten by hand, with the reason in a comment
- web/notebook/edit-reach/{index,result,reproducibility,package}.md — one page split into four
- web/notebook/*/index.md — `sidebar_label: Overview` throughout
- web/notebook/*/_category_.json — deleted, all five; the written sidebar replaces them

**Closed:** 2026-11-09.

**Ten `h3` headings added, and two of them ate a paragraph's opening.** Where the new heading and the paragraph's bolded lead said the same thing, the lead moved into the heading rather than being repeated. No other prose changed.

**The split is four pages: Overview, The result, Does it reproduce, The package.** The overview keeps the claim block and what was proposed, and ends with a table pointing at the other three. The result page carries the near field, the far field, the limits and what would overturn it — those four belong together because the limits are limits *on that result*, and a reader who finds the result without them has the wrong impression.

**Autogeneration was the root cause, not a bad label.** It derives the sidebar from the file tree, and the file tree does not know that a project with one page and a project with three are the same kind of thing. So the shape of the sidebar tracked how much had been written rather than what existed, and the labels were project directory names, which tell a reader nothing. The written sidebar gives every project the same shape and a few words saying what it is. The cost is that a new page must now be added to `sidebars.ts` by hand — which is the trade, and it is recorded here so the next person does not "fix" it back.

**What this ticket did not foresee:** that frontmatter `sidebar_label` overrides a hand-written sidebar item's `label`. Setting `label: "Overview"` in `sidebars.ts` did nothing for rome-neighbors, claim-graph and opz until their frontmatter was changed too. The sidebar file is therefore not the single source it looks like.

---

### D-008 · The notebook page, shaped as a paper

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 4h
**Spent:** 4h

**Description:**
Saif's verdict on the first prototype: "Abhi decoration zyada aur content kam lag raha hai ... conference mei share kerne ke laiq nahi abhi ye." He named the standard to work to — `~/code/tq-assignments/tq/m5`, a design document he wrote for his brother: running head on every page, justified prose at 12pt, inline author-year citations on nearly every claim, figures floated into the column, bordered tables with a shaded header, numbered equations, bold run-in leads, code listings. A second prototype was built to that standard and approved ("the styling is ... okay for now") with two removals.

Bring that to the site. Three parts.

1. **Components.** `PaperHead` (running head and title block), `Eq` (numbered equation), `Ledger`/`Finding` (the findings table, with a falsifier on every row), `Runs`/`Run` (provenance for every number), `Revisions`/`Rev`, `Readiness`/`Check`. Extend `Figure` with a `float` prop. Register all in `src/theme/MDXComponents.tsx` and document in `notebook/writing-here.md`.
2. **Paper mode CSS.** Applied by `~` sibling selector from `PaperHead`, so a page opts in by using the component and nothing wraps the content — the table of contents keeps working because the headings stay top-level nodes.
3. **Apply it.** `web/notebook/edit-reach/note-01.md`, carrying §§1–10, three appendices and the reference list.

**Two things are forbidden on the page, by instruction:** no email address anywhere, and no cite-this-page or BibTeX block. Saif has not started university; a page inviting citation asserts a standing he does not hold. The byline names Open Concept Lab, which is his own.

**Blockers:** —

**Artifacts:**
- web/src/components/Paper.tsx — PaperHead, Eq, Lead, Prov, Ledger/Finding, Runs/Run, Revisions/Rev, Readiness/Check, Data
- web/src/components/Figure.tsx — `float` prop
- web/src/theme/MDXComponents.tsx — all registered
- web/src/css/custom.css — the "Paper mode" block at the end
- web/notebook/edit-reach/note-01.md — the paper
- web/notebook/edit-reach/index.md — rewritten as a short landing
- web/notebook/writing-here.md — the "Paper mode" section
- web/sidebars.ts — Overview + Note 01
- ai/edit-reach/paper/note.md — the four `TODO(cite)` resolved

**Closed:** 2026-11-09.

**Paper mode is applied by a sibling selector, not a wrapper.** `<PaperHead>` emits one element and the stylesheet reaches the rest of the page with `.ocl-paperhead ~ *`. The alternative — a `<Paper>` component wrapping the body — was rejected because it moves the headings inside a JSX node, and the table of contents is built from top-level heading nodes. The page would have rendered correctly with an empty contents rail, which is the kind of failure nobody notices for a month.

**`hide_title: true` is required and is easy to forget.** Docusaurus injects its own `h1` when the markdown has none, and a JSX `h1` does not count as one. Without the flag the page carries two titles.

**This reversed part of D-007, and the reversal is the right call.** D-007 split the overview into four pages; three of them are now one paper. The split was a fix for a sidebar that could not distinguish a one-page project from a three-page one, and that fix holds — the sidebar is still written by hand and still gives every project the same shape. What changed is the content's own shape: Limits belong beside the result they limit, and the reproducibility and package sections are §7 of an argument rather than two thin pages. Four thin pages were not more navigable than one dense one; they were the same text with more clicks.

**A `Finding` with no falsifier renders a line saying so.** It would have been easier to render a blank cell. A blank reads as "nothing to say here"; the sentence reads as an omission, which is what it is. This is the project's own claim-audit rule moved into a place where it cannot be skipped.

**Two of the four `TODO(cite)` markers were never open.** `he2026romelimits` and `zhong2023mquake` are both in `web/data/papers.yml` with `verified: true` — checked on 2026-10-03 by R-011b. The markers had been written into `note.md` from memory of what was unverified, rather than from the file. The lesson is narrower than the citation rule it belongs to: the rule says never generate a citation from memory, and this was the mirror of that — recording a citation as *un*verified from memory. Both directions cost work.

**What this ticket did not foresee:** that the five existing SVGs under `static/img/edit-reach/` carry hardcoded cream paper and ink, so they sit as light rectangles on a dark page. The one figure drawn inside the MDX (F-08's timeline) uses the site's tokens and follows the theme. Converting the other five is not in this ticket and is not yet open as one.

**RCA (re-open and re-close: 2026-11-09):**

> Saif opened §3 and the figure was a broken-image glyph. Two faults, one of them a day old.
>
> **The image never loaded, and nothing said so.** `Figure` rendered `<img src="/img/edit-reach/two-regimes.svg">` with no base path. The site is served under `/open-concept-lab/`, so the request fell through to the single-page handler, which answers **200 with `text/html`**. Every check that would have caught it passed: the file exists, `curl` returns 200, `npm run build` reports no broken link, because Docusaurus checks links and routes rather than static assets. The component now resolves `src` through `useBaseUrl`. The bug is older than this ticket — it came in with D-002's figures on 8 November and was never seen, because the figures were never looked at in a browser. `writing-here.md` asserted that `/img/…` "resolves correctly in development and on the deployed site"; that sentence was wrong and is now the warning in its place.
>
> **Floating the wide figures was wrong on its own.** All five SVGs under `static/img/edit-reach/` are 1000px wide carrying 12–19px type. At `float="right"` they render about 330px wide, which puts their labels near 5px. The float rule also set `--ocl-figure-floor: 0`, disabling the readability floor that existed precisely to stop this. The three wide figures now take `wide`; `float` is kept for the one figure drawn inside the MDX at 400×150, which is the size it is floated at. Documented as a constraint on the prop rather than left as a judgement call.
>
> **What was misunderstood:** that a passing build says anything about whether a page's images load. It does not, and neither does `curl`, because the SPA fallback returns success for every path. The only check that works is opening the page — which is the check that was skipped on both days.

**Re-closed:** 2026-11-09. `web/src/components/Figure.tsx`, `web/notebook/edit-reach/note-01.md`, `web/notebook/writing-here.md`.

---

### D-009 · The front matter a paper actually has

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 2h
**Spent:** 2h

**Description:**
Saif generated a competing design in Lovable and said plainly which parts he preferred: the left rail, and the centre's type and size. He was right on both, and the gap is worth naming rather than defended against.

Port what is better:

1. **The rail.** Each project carries its stage, right-aligned in mono, and its few words sit on their own line in italic rather than being joined to the name with a `·` — which wrapped badly at sidebar width.
2. **The front matter.** An identifier line (`WORKING PAPER · OCL-2026-07 · V0.3`), a display-size title, the author on one line with the affiliation in italic beneath, and a mono metadata row — started, updated, what it builds on.
3. **The abstract and contributions.** The abstract takes a letterspaced label rather than a numbered heading, because a paper's abstract is not section 1. A contributions box, numbered, which this page did not have at all.
4. **Larger body type**, 1rem at 1.62, against the 0.9375/1.5 that was set from a print reference.

**Blockers:** —

**Artifacts:**
- web/sidebars.ts — reads the stage from `data/projects.yml`
- web/src/theme/DocSidebarItem/Category/index.tsx — renders name, stage and blurb
- web/src/components/Paper.tsx — PaperHead rewritten; Abstract and Contributions added
- web/src/css/custom.css — front matter, abstract, contributions, rail
- web/notebook/edit-reach/note-01.md — renumbered, sections 1–9 after the abstract
- web/notebook/writing-here.md

**Closed:** 2026-11-09.

**The stage is read from `data/projects.yml`, not written into the sidebar.** There was already a `tone` field there feeding the home page's status dot, and adding a second status vocabulary for the sidebar would have let the two disagree within a week. The cost is that the words are the ones that file already uses — draft, provisional, standing — rather than the richer set the competing design showed. Changing them means changing one file, and both surfaces follow.

**Renumbering was not cosmetic.** Taking the abstract out of the numbered run moved every section by one, and nine section headings, eleven in-text `§` references, seven `where=` cells and one anchor had to move with it. Done by a single mapped substitution over headings and references together, so the two could not drift apart.

**What this ticket did not foresee:** that the competing design merged the page's sections *into* the project rail, so there is one navigation surface instead of two. That was not ported. Docusaurus builds the sidebar from the document tree and the contents rail from the page's headings, in different parts of the theme, and joining them needs two swizzles and a shared store. It is a real improvement and it is not free; it is not open as a ticket yet.

---

### D-010 · The sections a reviewer expects

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1.5h
**Spent:** 1.5h

**Description:**
Saif: "mujhe woh Paper section wala option chaiye, from introduction, to implementation, to methodology, conclusion, references."

The page was organised under names this project invented — Problem space, The control, Reproducing the readings, The record, Open questions. Each says more in isolation than its conventional counterpart, and together they cost a reader the map they already hold. Reorganise under Introduction, Related work, Methods, Implementation, Results, Findings and claims, Limitations, Conclusion, References, appendices.

**Blockers:** —

**Artifacts:**
- web/notebook/edit-reach/note-01.md
- web/notebook/writing-here.md — the section-name rule

**Closed:** 2026-11-09.

**The restructure produced a section that did not exist: Related work.** Under the old names there was nowhere for it, so the positioning lived in one clause of the limits list — "could not be found stated, on one search pass and one neighbouring paper read in full." It is now §2, with He et al. (2026) as the nearest work and three propagation papers distinguished on what they measure: all of them score outcomes after an edit is applied, and none screens an item before it runs. Three references were added to carry it. **A missing section had been hiding a missing argument**, which is the case for conventional names rather than good ones.

**Two names were kept non-standard, deliberately.** "Findings and claims" holds the ledger, and Appendix C holds the readiness checklist. Those are the parts a paper does not have and a page revised in place does; giving them conventional names would have meant cutting them.

**Rebuilt by extracting the existing blocks and reassembling, rather than editing in place.** Two extractions over-ran their section and carried the next heading with them, which showed up as a duplicated `## 4. Results` and a whole orphaned reproducibility section. Caught by listing the headings after the write. The lesson is that a slice taken by "from this marker to that marker" is only as good as the assumption that nothing else lives between them, and that assumption was wrong twice in one script.

**The prototype artifact was retired rather than re-synced.** It had been rewritten twice to match the site and had drifted again within the hour. Two hand-maintained copies of one page is the duplication this project keeps writing rules against; the site is the page now.

---

### D-011 · The column was wider than anything in it

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 0.5h
**Spent:** 0.5h

**Description:**
Saif, on the rendered page: "mujhe ye beech mei space bauhat zyada lag rahi hai, too much estate not used." The text sat at 42rem inside a column of roughly 77rem, left-aligned, leaving about 380px dead on the right at desktop width.

**Blockers:** —

**Artifacts:**
- web/src/css/custom.css — the paper-mode layout
- web/src/components/Figure.tsx — the `float` prop removed
- web/notebook/edit-reach/note-01.md, web/notebook/writing-here.md

**Closed:** 2026-11-09.

**Widening the text would have been the wrong fix.** At 1rem the measure already runs about 78 characters, which is the upper end for justified prose; filling the column would have traded a real cost for an apparent one. The container now takes the full column and each text block is capped at the measure and centred, so the estate goes to the things that want width: a figure takes the whole column, a table sits between the two at 54rem — wider than the text, because a ledger row carries a claim and its falsifier, and not stretched to the column, where a seven-column results table would read as gaps.

**That change killed the `float` prop, and it is gone rather than guarded.** With the container at column width and each block centred inside it, a floated figure sits at the column edge while the paragraphs beside it are centred in the full column, so the text does not wrap around it predictably. The prop had already caused one defect — the 1000px SVGs rendered their labels at about 5px when floated to 47% — and it existed to use space the layout now uses properly. Removed from the component, the stylesheet, the page and the conventions, rather than left with a warning on it.

**A side effect worth naming:** the five hand-drawn SVGs now render at roughly their drawn size for the first time. They were authored at 1000px and had been displayed at 672px or less since the day they were made.

---

### D-012 · "Note 01", three left edges, and equations set as text

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1h
**Spent:** 1h

**Description:**
Four faults Saif found on the rendered page. "I don't like 'Note 01', what even is 'note 01'", an alignment problem between a figure and the text beside it, and: "we are not rendering as LaTeX render mathematical equations?"

**Blockers:** —

**Artifacts:**
- web/notebook/edit-reach/paper.md — renamed from note-01.md
- web/notebook/edit-reach/index.md, web/sidebars.ts
- web/src/css/custom.css
- web/notebook/writing-here.md

**Closed:** 2026-11-09.

**"Note 01" named a series that does not exist.** It was invented when the page was going to be one of several, and the second never arrived. The page is the project's paper, so it is called Paper — which is also what edit-slice calls its own, so the two projects now read the same way in the rail. The file and the URL moved with it: `notebook/edit-reach/paper`.

**The alignment fault was mine, in one declaration.** Figures carried `margin-inline: 0` while every other block carried `margin-inline: auto`, so a figure started at the column's left edge and everything else was centred. The page had three widths and only two of them shared a centre. It is now two widths on one centre line: prose at the measure, figures and tables at 54rem, and a figure caption pulled back to the measure so it lines up with the body text beneath it. Each selector is scoped as a direct child, because mixing scoped and unscoped rules is what let one block centre and its neighbour sit flush left.

**The equations had been set as monospace text, and the site has had KaTeX the whole time.** `remark-math` and `rehype-katex` are configured for both the docs and the blog, and `writing-here.md` has documented `$$` since before this project started. The `<Eq>` component was written with a mono font and `white-space: nowrap`, which is what you write when you have decided the renderer is not available — without checking that it was. Three display equations and the whole of Appendix A are now real mathematics; the appendix reads as a derivation rather than as a transcript of one.

**What this ticket did not foresee:** that `<Eq>`'s own styling would fight the renderer once the content changed. The mono font and the nowrap had to come out, and a `.katex-display` margin reset had to go in, or the numbered row would have carried two sets of vertical spacing.

---

### D-013 · Two thirds of the project was not on the page

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 2h
**Spent:** 2h

**Description:**
Saif: "Is this ALL that we got with edit-reach? I don't think so, lets commit and improve the content."

He was right, and the gap was measurable: `agents/shared/decisions.md` holds fifteen decisions and the page carried four. Everything in E-001, E-002, E-003 and the E-005…E-013 reproducibility cluster reached the page as, at most, a clause.

**Blockers:** —

**Artifacts:**
- web/notebook/edit-reach/paper.md — §3.4, §4.1, §4.2, §5.1, §5.3, §5.4, five new ledger rows, eight new provenance rows

**Closed:** 2026-11-09. The page went from five findings and six runs to fourteen and fourteen.

**The largest omission was the project's strongest positive result.** [E-003] separates destruction from destination inside one rank-one update — it breaks the pre-edit answer because it touched that subject's key, and supplies the new answer because of what it said — measured on one probe set, under one metric, separating in opposite directions, discordant pairs 142 to 2. None of it was on the page. The page had been written around the question the project set out to answer, and that question came back negative, so a positive result that arrived from a different direction had nowhere to sit. §5 is now ordered by what was run rather than by what was asked.

**[E-001] had been reduced to its weakest sentence.** The page said 495 probes and a 2.96× spread. What it did not say is that the raw correlation is ρ = 0.522 and falls to an excess of 0.085 once a same-subject control is removed, or that the quantity being predicted is *this probe is sensitive to an edit on this subject* rather than *this edit reaches this probe*. The second is the sentence a reader can use.

**[E-002]'s methods lesson is now on the page as a result in its own right.** The per-arm medians read as the real edit being 56% above its control; the paired median of differences is +0.0009. The unpaired form overstates the content effect roughly sixtyfold. That is worth more to a reader than the number it corrects.

**The reproducibility cluster was nine decisions compressed into two paragraphs.** It is now §4.1 with the split that makes it usable — structure holds everywhere, every magnitude belongs to a deployment — plus the three things that were missing entirely: the variation is routing and is bit-exact, so device-matched readings need no tolerance at all; the partition is a property of a deployment on a day, present on 1 November and absent on 3 November; and the batch-composition claim was ours, was too broad, and was narrowed to 2.6% of raw key magnitude.

**§4.2 is new and is about the record rather than the result.** 124 of 155 committed log files were a single line naming themselves, because one module called `logs.setup()` at import scope and five scripts imported it as a library. Eighty per cent of the kept record was content-free. It belongs on the page because every number above is defended by that record.

**What this ticket did not foresee:** that the ledger would need a *withdrawn* row for a claim withdrawn by its own follow-up (F-14, the depth direction). The ledger had held claims this project retired under external pressure; this is the first retired by the next run of the same experiment.

---

### D-014 · Outputs, charts, and two columns

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 2h
**Spent:** 2h

**Description:**
Saif: "I feel we haven't really shown the actual code outputs, result comparisons, numbers, charts, diagrams ... any paper has a two column layout which it uses to explain the abstract."

Three things, and each was true. The page asserted numbers without showing a run producing them; the new §5 results arrived as tables with no picture; and the front matter ran down one column while the page had room for two.

**Blockers:** —

**Artifacts:**
- web/src/components/Paper.tsx — `Frontmatter`
- web/src/css/custom.css — the two-column grid
- web/notebook/edit-reach/paper.md — two charts, two run outputs

**Closed:** 2026-11-09. Seven figures, nine tables, three code listings.

**The outputs are copied from `results/*-summary.md`, not written to look like outputs.** Both blocks are what the run printed: [E-006]'s sixteen readings partitioning by content hash across two GPUs, and [E-003]'s base/real/control/stranger row at 1% / 29% / 1% / 1%. The second was not on the page in any form, and it is the cleanest single line in the project — the control and the stranger both sit at the base rate, so the real edit is the only arm that puts the new answer anywhere.

**The chart for §5.4 is the one the page most needed.** Four paired differences on one shared scale, coloured by *which* difference rather than by size: content against identity. Destination puts its mass in content and nothing in identity; destruction does the reverse. The claim "they separate in opposite directions on the same probes" is a sentence a reader has to take on trust and a picture they can check in a second.

**§5.1's chart is a dumbbell, and the form is the argument.** Six families ordered by coefficient, each with movement under the real edit and under the same-subject control. Where the marks nearly touch, the coefficient predicted nothing the control did not — which is five families out of six. A bar chart of movement alone would have shown the opposite, because the high-coefficient families do move more.

**Two columns for the front matter and nowhere else.** A printed paper sets two columns because the page is wider than its measure, which is also true here — but two columns of running text on a screen makes a reader scroll down one and back up the other. The abstract and the contributions are both short and self-contained, so they are the one place the idiom works without that cost. The component says so in its own comment, so the next page does not take it as a licence.

**What this ticket did not foresee:** that `<Abstract>` and `<Contributions>` carry their own rules and padding, which read as a separation from what follows and as a seam between columns once they sit side by side. Both drop their borders inside the grid and the grid carries one rule beneath.

---

### D-015 · The body set in two columns

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1h
**Spent:** 1h

**Description:**
Saif: "mei chahta hoon ke aik section ke paper wale tab per hum wahi two column format apply karein jo conferences, journals, jese NEURIPS mei submit hote hain." The previous ticket had set only the front matter in two columns; he wants the body.

**Blockers:** —

**Artifacts:**
- web/src/css/custom.css — the two-column paper layout
- web/notebook/writing-here.md

**Closed:** 2026-11-09.

**The objection to two columns on a screen is real, and the layout answers it rather than ignoring it.** Set naively, a reader scrolls down the left column for the length of the article and back up for the right. CSS multicol has the mechanism to avoid that: a `column-span: all` element ends the current multicol segment and starts a new one, so content between two section headings balances into two columns *within that section*. Nothing balances across the article, and each section reads the way one page of a printed paper reads. No JavaScript, no pagination engine, no wrapper per section.

**Spanning follows the printed idiom.** Section headings, the title block, the front matter, every table, every `wide` figure and every code listing span both columns — which is `figure*` and `table*`. A figure drawn small stays in its column. `break-inside: avoid` on equations, figures, list items and subheadings stops anything read as one object being cut down the middle, and `break-after: avoid` keeps a subheading with the paragraph under it.

**The column is now the measure, so the old variable went.** `--ocl-paper-measure` capped each block when the layout was one wide column of narrow text; with two columns the column width *is* the measure and the variable had nothing left to do. The body drops to 0.9rem and the spread caps at 52rem, which puts a column near 55 characters.

**One correction worth recording, because it was in the request.** NeurIPS is single-column. The two-column format is ACL, EMNLP, IEEE and AAAI. What was built is that one, which is what the request described; the name attached to it was wrong and nothing follows from the error.

**Below 1000px it falls back to one column.** Two columns of justified text at phone width is unreadable, and no amount of hyphenation fixes it.
