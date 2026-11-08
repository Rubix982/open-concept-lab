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
