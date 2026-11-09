# Documentor Tickets — edit-slice

### D-001 · Write notes/definitions.md

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-09-09
**Updated:** 2026-09-09

**Description:**
Write the definitions page called for in notes/session-2026-09-08.md §2. Four
declarations, one or two sentences each, plus the binding outcome vocabulary
(update / damage / orphan) and the standing language constraints from
CLAUDE.md. Must stay under one page — CLAUDE.md names this the most important
file in the repo and requires it get harder to change over time.

This is the deliverable for the next Natalie/Anna meeting. The advisors are
probing whether the direction can be held still; definitions are the proof that
it can. Results are explicitly NOT the artifact for that meeting.

**Blockers:** none

**Artifacts:**
- notes/definitions.md

**Closed:** 2026-09-09

---

### D-002 · Write up T-054

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-09-13
**Updated:** 2026-09-13

**Description:**
Write the claim the project actually established: CounterFact's possession filter
was calibrated once, in 2022, against its authors' model, and the same fixed
21,919 records are reused on every model since without the guarantee being
re-established.

Draft in agents/documentor/drafts/, publishable as a technical note and as a post
on the Docusaurus site. Must carry, not bury:

- The measurement critique (two-way vs constrained rank vs free generation), with
  the candidate-set size attached to each number, since levels move with it.
- That prompt sensitivity and phrasing-over-knowledge belong to the LAMA line
  [R-006] and are cited, not claimed.
- That R-007 cleared the nearest competitor but the field was searched, not swept.
- The outstanding control (see below), stated as outstanding.

**The control this write-up needs and does not have:** we have not measured
possession on the model CounterFact was calibrated against. Without it a reviewer
can say the drop is our stricter measure rather than failure to transfer. GPT-2-XL
is not on NDIF, so this requires a local run — which conflicts with the standing
NDIF-only preference. Surface as a decision.

**Result:** published. Writing it surfaced that the claim being written up was
wrong — going to the ROME paper's construction appendix, rather than its prose or
another literature search, showed CounterFact has NO possession check. That
reverses [R-006] and restores the stronger framing. The outstanding control the
draft called for turned out unnecessary: the paper reports the number itself
(Table 4, unedited GPT-2-XL, ES = 22.2).

**Artifacts:**
- agents/documentor/drafts/possession-precondition.md (v2, source of record)
- web/blog/2026-09-14-the-check-that-was-never-there.md (published, 1309 words)
- agents/shared/findings.md -> "[D-002] CounterFact has NO possession filter"

**Closed:** 2026-09-14

---

### D-003 · Aggregate retrospective — five days, with figures

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15

**Description:**
Capture the whole arc in one place on the site: threads followed and abandoned,
routes taken, claims tried and their fates, what failed and why, and where the
evidence points. With numbers and figures.

Distinct from the published post (which argues one claim). This is the **record**:
it must be as useful when a claim was wrong as when it was right, because eight of
them were wrong.

Must include, not omit:
- Every superseded claim with what replaced it — use the site's `Claim` component,
  which renders `superseded` struck through, exactly for this.
- Routes abandoned with the reason: DBpedia mined rules, AGM kernels, the P131
  chain family, the diagnostic framing, the structure-map pairing.
- Attrition numbers, since selection is where the artifacts live.
- The pattern: errors were in framings supplied around measurements, never in the
  measurements themselves.

**Figures (inline SVG, via the site's `Figure` component):** possession vs scale;
three measures disagreeing; claim fates; star vs chain; the entailment family;
attrition funnels.

**Palette:** validated with the dataviz validator against the site's own hues —
light `#3d72a8` / `#a8503f`, dark `#5596d4` / `#c87c62`, both all-pass. Identity is
never colour-alone; every series is direct-labelled.

**Result:** published. ~4,260 words, five inline-SVG figures, nine Claim blocks.
Sections: charter vs reality; the claims ledger; six abandoned routes with what
killed each; four structural findings; attrition funnels; the current entailment
family; infrastructure; the pattern in the errors; where the evidence points; what
is open.

Palette validated rather than eyeballed — light `#3d72a8`/`#a8503f` and dark
`#5596d4`/`#c87c62`, both all-pass on the six checks, both drawn from the site's
own hues. Identity is never colour-alone: every series is direct-labelled and
every mark carries a `<title>`.

Two layout bugs caught by inspecting rather than trusting the build: a broken link
(the blog's routeBasePath is `writing`, not `blog`) and label overflow in the
claims timeline, where a 205px label rendered leftward from x=144 and ran off the
canvas. Rebuilt with a dedicated label column.

**Artifacts:**
- web/blog/2026-09-15-five-days.mdx (published)
- verified: yarn build passes with onBrokenLinks: throw; all five figures and
  their data points confirmed present in the rendered HTML

**Closed:** 2026-09-15

---

### D-004 · Plain-language deck: what we found, for a non-specialist

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-09-21
**Updated:** 2026-09-21
**Estimated:** 2h

**Description:**

`web/notebook/edit-slice/review.md` is written to be judged by someone who knows the
field. It is the wrong artifact for explaining the work to anyone else, and the call with
Natalie needs a version that opens with the problem rather than with the mechanism.

Build a deck that states **what goes wrong**, in words a non-specialist reads without
stopping. Constraints, all of which the paper satisfies and a deck easily fails:

- **No jargon without a concrete referent.** No "coefficient", "delivery", "nats",
  "rank-one". If a term must appear, it appears after the thing it names.
- **Every claim on a slide traces to a record.** Speaker notes carry the id so a question
  can be answered from the ledger live. The slide itself stays clean.
- **The withdrawn claims are on a slide, not in a footnote.** Eleven claims, eight
  withdrawn or narrowed, is the most credible thing here and the easiest to bury.
- **No prescription.** CLAUDE.md scopes this project to measuring what existing editors
  do; a deck is where "so you should edit deeper" would slip in. It must not.

**Reuse.** `ai/rome-neighbors/presentation/build_deck.py` already renders a themed PPTX
from a declarative `Slide` list. Copy the renderer rather than importing across projects —
the two have separate venvs and a cross-project import is a dependency neither declares.
Record the copy in the docstring so a fix to one is known to need porting.

**Result (2026-09-21).** Nine slides, ~10 minutes, structured as five problems rather
than as a result. Two of the five are our own errors, placed deliberately — the gate that
passed and was worthless, and the prediction that did not predict — because they are what
makes the other three credible.

Three leaks from the copied renderer, each of which would have rendered the other
project's identity into this deck: a hard-coded title slide, a hard-coded running footer,
and the title slide's speaker notes. All three are now module constants.

python-pptx added to the venv and pinned. The renderer's 16 pre-existing `E702` lint hits
were left alone deliberately: the file is a hand-ported copy, and keeping it diffable
against its source is worth more than the style fix.

**Status:** closed
**Artifacts:** presentation/DECK.md, presentation/build_deck.py, presentation/DECK.pptx
**Closed:** 2026-09-21

---

### D-005 · The paper tab becomes a template, and this page conforms to it

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 3h
**Spent:** 3h

**Description:**
Saif: "the way we structured edit-reach is different from how we had structured edit-slice, there must be a uniform template all paper tabs must follow." Then, correcting a first attempt that wrote the template down as a convention: "Template se matlab aik web component jo fill ho ... and each paper is one entry, no?"

**Blockers:** —

**Artifacts:**
- web/src/components/Paper.tsx — the `Paper` component
- web/scripts/check-papers.mjs — the order check, wired into `prebuild`
- web/src/components/References.tsx — the `project` prop
- web/notebook/edit-slice/review.md — converted
- web/notebook/edit-reach/paper.md — converted
- web/notebook/writing-here.md

**Closed:** 2026-11-09. Both paper pages conform; the check runs on every build.

**The first attempt was a convention and the correction was right.** A written-down section order is a thing to remember. `<Paper>` reads the page's own front matter and renders the identifier line, the title block, the author, the dates, the reading guide, the abstract's label, the keyword line, the contributions and the figure index. The page writes `<Paper>` once with its abstract inside. Nothing in the scaffolding is typed twice, and two papers cannot drift apart by accident.

**The sections could not go into the component, and the reason is worth keeping.** Docusaurus builds the contents rail from the markdown syntax tree; a heading emitted by React never reaches it. The page would render correctly with an empty rail. So the headings stay markdown and `check-papers.mjs` enforces the order at build time instead.

**The template is not edit-reach's.** Three things came the other way. The **figure and table index** is this project's and is now in the template past about eight figures. The **reading guide** — *section 7 is the attack surface; if you are deciding whether to spend time on this, read the abstract and then section 7* — is this project's and is now a front-matter field. And §7 keeps the plain name *Limitations* rather than this project's *What to attack*, because an adversarial heading collects what a reviewer would attack and silently loses the third category: how the result may not be used. Nobody attacks a constraint on use.

**A silent defect, found while converting.** This page ended with `<References project="edit-slice" />`, and the component has no `project` prop — it has `ids`, `items` and `children`. So the reference list has rendered **empty since the page was written**, while twenty-six papers sit tagged `edit-slice` in `data/papers.yml`. The prop now exists and the list has twenty-six entries. A component that ignores an unknown prop fails exactly this quietly.

**What was converted and what was not.** Structure, front matter, section names and numbers, every `§` cross-reference, Artifacts moved into §4 Implementation, and three appendices added — the derivation stated on its own, the provenance pointing at the generated evidence ledger, and a readiness table. **§6 keeps its existing claim-status table rather than becoming a `<Ledger>`**, because `<Finding>` requires a falsifier per row and that table does not carry them. They exist in `agents/shared/decisions.md`, which states falsification before each run; pulling twelve of them onto the page is a content job and is not done here. Rendering "no falsifier stated" twelve times would have been honest and useless.

---

### D-006 · The overview on the template, and the counts that had drifted

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1.5h
**Spent:** 1.5h

**Description:**
`web/notebook/edit-slice/index.md` predated the overview template. It had a State table, Three ways in, What would change our mind and Scope — good material, none of it on the shape every project's overview now takes.

**Blockers:** —

**Artifacts:**
- web/notebook/edit-slice/index.md
- web/notebook/edit-slice/review.md — the counts in Appendix B

**Closed:** 2026-11-09.

**Every count on both pages was stale, and by a lot.** The overview said 22 decisions, 16 findings and 57 threads. The paper said 33, 18 and 67. The repository says **56, 33 and 85**. The paper also described itself as *~3,000 words* while being 12,600. Nobody had been wrong on purpose; the numbers were written once, by hand, and the work kept going. **A figure that is written by hand into prose has a half-life**, and these two pages are the argument for the evidence ledger being generated rather than typed.

**The chain figure is this project's story and it reads as a sequence of denials.** How big is the contradiction an edit leaves in its grounds — there is none, the grounds are evidential. Does the model revise the premise — no, a work-country edit relocates a birthplace just as often. Then what is moving — arithmetic. Do published benchmarks test on such prompts — one does. The thing the project was built to measure does not exist, and what it found instead was in neither of the first two boxes.

**Three of the old sections survived unchanged**, because the template does not have them and should: *Three ways in* (the paper, the narrative, the ledger, each with who it is for and how long it is), *What would change our mind*, and *Scope, deliberately*. The first of those is better than anything in the template and belongs in it.

**What this ticket did not foresee:** that fixing the counts would trip the PDF staleness check twice in a row. Editing the page makes its PDF older than it, which is exactly what that check is for; it is mildly annoying and it is working.
