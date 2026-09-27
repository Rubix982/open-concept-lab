# Project: medicine — visual explainers

_Last updated: 2026-09-26 by O-001_

## Objective

Single-file, offline-capable HTML explainers for medical concepts, in one
consistent house style (DM Mono + Playfair Display, dark panel grid, animated
SVG carrying the mechanism).

## Current Phase

Phase 2 — expanding the set beyond the cardiometabolic piece

## Active Tickets

### E-001 · The Resus Bay — emergency-medicine vocabulary explainer

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-26
**Updated:** 2026-09-26

**Description:**
Build `the-pitt-resus-bay.html`, a single-file explainer decoding the
resuscitation-bay vocabulary heard in the TV series *The Pitt*. Scope is the
resus bay only — airway, arrest, chest decompression, FAST — explicitly NOT
department flow (ESI/boarding/dispo) or mass-casualty triage, which are
deferred to E-002 and E-003.

Must match the house style established by `apob-cardiometabolic.html`: same
embedded DM Mono + Playfair Display woff2 (file works fully offline), same
`:root` palette and panel/nav/TOC/footnote scaffolding, same scrollspy and
back-to-top scripts. Reuse that file's structural CSS; do not carry over its
subject-specific animation classes.

Four animated SVG panels, each carrying a *sequence* rather than a definition:

1. RSI as a seven-segment clock — the 7 P's, ring lighting in order, centre
   label crossfading through each step.
2. The arrest loop — compression artefact vs. rhythm-check trace (the rhythm
   is only legible with hands off), shock, and ETCO₂ rising as the ROSC tell.
3. Tension pneumothorax → needle decompression → tube thoracostomy, with
   tracheal shift and lung re-expansion.
4. FAST — probe moving between the four windows, free fluid reading black in
   the RUQ view.

Plus: drug board (induction / paralytic / pressor / antiarrhythmic / reversal /
blood), a monitor-numbers table, an acronym glossary, and takeaways.

Clinical content must be accurate to current practice (ACLS, ATLS 10th ed.
for needle site). Footnote states it is dramatised-TV decoding, not medical
advice.

**Blockers:** none

**Artifacts:**

- medicine/the-pitt-resus-bay.html
- medicine/README.md → "The Resus Bay"

**Closed:** 2026-09-26

## Completed This Session

- E-001 · The Resus Bay — `medicine/the-pitt-resus-bay.html`
- D-001 · Visual identity — the calibrated strip
- E-002 · Merge re-spine — time-to-harm ruler, part dividers, retitle
- R-001 · Content derivation for the flow half (design-e002-flow.md)
- E-005 · Lung sliding panel — section 05, ultrasound thread complete
- E-004 · Shock taxonomy panel — section 05 of the resus bay piece
- E-003 · RCA fix: TOC rows were missing the name+desc wrapper span, collapsing
  the description into the 26px numeral column. Corrected to match apob markup.

### E-004 · Shock taxonomy panel + tamponade terms

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Add a fifth section to `the-pitt-resus-bay.html`: "Shock — four failures of
the same circuit", inserted between FAST (04) and the drug board. Renumber the
existing drugs/numbers/glossary sections to 06/07/08 and add a Shock entry to
the nav, the TOC, and the scrollspy SECTIONS array.

Rationale: the drug board already names pressors, inotropes, blood and needle
decompression as if the reader knows which failure each one answers. The
taxonomy is the missing spine — without it "why not just give a pressor" has
no answer on the page.

Panel is a 2×2 of mini-circuit diagrams (tank, pump, pipes) with the failing
component drawn in the danger colour, all four legible at once, highlight
rotating on a 16 s cycle with a crossfading "the fix" caption. Deliberately
not a single morphing diagram — the comparison is the point.

Also add tamponade / Beck's triad and inotrope-vs-vasopressor to the
Circulation glossary group.

**Blockers:** none

**Artifacts:**

- medicine/the-pitt-resus-bay.html → section 05, nav/TOC/scrollspy, two
  glossary terms (tamponade, inotrope vs. vasopressor)

**Closed:** 2026-09-27

### E-005 · Lung sliding panel (E-FAST)

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Add "Lung sliding — the pneumothorax you find before the x-ray" as section 05
of `the-pitt-resus-bay.html`, directly after FAST, completing the ultrasound
thread. Renumber shock/drugs/numbers/glossary to 06/07/08/09; update nav, TOC,
header subtitle and the scrollspy SECTIONS array.

Panel is two ultrasound screens side by side on a 12 s cycle: a B-mode view
(bat sign — two rib shadows with the pleural line slung between them, A-line
reverberations below) and the M-mode strip beside it, crossfading between the
granular "seashore" of a sliding lung and the stacked horizontal lines of the
"barcode" sign when sliding is absent.

Must carry the two honest caveats: absent sliding is sensitive but NOT
specific (bleb, adhesion, ARDS, mainstem intubation all abolish it), and the
lung point is the one finding that is specific. The mainstem-intubation case
cross-links back to section 01 — a tube pushed too far abolishes sliding on
the left, which is a finding about the tube, not the pleura.

**Blockers:** none

**Artifacts:**

- medicine/the-pitt-resus-bay.html → section 05, nav/TOC/scrollspy,
  downstream sections renumbered to 06/07/08/09

**Closed:** 2026-09-27

### R-001 · Derive content for the department-flow piece

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Before opening any implement ticket for E-002, derive the content: find the
organising spine, enumerate the vocabulary, decide which terms earn an
animated panel versus a glossary line, and mark every claim whose evidence is
weaker than the confident register of an infographic implies.

Explicitly a premise dry-run first. The default framing ("a glossary of flow
terms") is flat, and designing around it would produce a correct, inert page.

**Artifacts:**

- medicine/design-e002-flow.md
- medicine/threads.md

**Closed:** 2026-09-27

### E-002 · Merge — re-spine the existing file on the time-to-harm ruler

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Unblocked: T-003 answered, hinge is the time-to-harm ruler (`design-merge.md`).
This ticket is the *structural* half of the merge and touches no new content.

In `the-pitt-resus-bay.html`:
1. Retitle to "The Pitt, Decoded — ranked by how fast it kills".
2. Introduce Part I / Part II / Part III dividers per `design-merge.md`
   section order. Existing sections keep their content; only grouping and
   numbering change.
3. Add the persistent timescale strip beneath the section nav (seconds →
   minutes → hours → days), marking reading position. Supplements the nav,
   does not replace it.
4. Generalise takeaway 1 from "the order is physiology, not ritual" to the
   time-to-harm statement, per `design-merge.md` "What it breaks".

Ship and read this before E-006 adds content. If the re-spined file already
reads as a scroll, T-005 has answered itself and the merge should be
reconsidered before more sections land.

**Blockers:** none

**Artifacts:**

- medicine/the-pitt-resus-bay.html — retitled, Part I/II/Closing dividers,
  fixed time-to-harm ruler with scroll tracking, takeaway 1 generalised

**Closed:** 2026-09-27

### E-006 · Department-flow sections

**Status:** blocked
**Type:** implement
**Priority:** medium
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Build sections 09–14 from `design-e002-flow.md`: the clocks, ESI (hinge,
animated), the door/EMTALA, the board (animated), boarding (animated — the
panel the piece exists for), dispo. Regroup the acronym wall by timescale.

All copy must respect `design-e002-flow.md` §5 — the hedged claims. Boarding
harm is "associated with", never "causes"; discharge-before-noon is not a
solved lever.

**Blockers:**

- T-005 (E-002 has shipped; the read has not happened yet. Do not start until
  the user has actually read the re-spined file and judged whether sixteen
  sections is a document or a scroll.)

**Closed:** —

### D-001 · Visual identity — the calibrated strip

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
The piece reads as a generated dark dashboard, not as something from
emergency medicine. Audited against known generated-design tells it hits
most of them: tinted near-black for black, one bright accent, a Didone
display face, mono reserved for small labels, an all-caps eyebrow above
every heading, middle-dot meta strings, and every section head built as
"Word — fragment".

Redesign on one concept: **the page is a calibrated strip.** The document is
already a ruler of time-to-harm, so the measuring surface becomes the
identity.

1. Type — drop Playfair Display and DM Mono. One superfamily, IBM Plex
   (Condensed 600 display / Sans 400-500 prose / Mono for values only),
   embedded as before so the file stays offline-capable.
2. Colour — replace the single-accent palette with monitor channel
   assignment: ECG green, SpO₂ cyan, arterial red, CO₂ yellow, infusion
   violet, plus IEC 60601-1-8 alarm priority (red = act now, amber =
   advisory). Ground becomes true black.
3. Structure — a fixed left rail calibrated at runtime from real section
   offsets, replacing the horizontal ruler from E-002. Prose loses its box
   entirely; only the SVG viewports keep a frame, treated as screens.
4. Copy — remove the three chrome tells throughout.

**Blockers:** none

**RCA (in-flight, worth recording):** the redesign layer was first inserted
*before* the rules it overrides, so `.pr-t`, `.os-cell`, `.remedy-card` and
`.part-rule` silently kept their original values — the classic CSS ordering
trap. Moved to the end of the stylesheet. Separately, the rail's calibration
put every tick at 0% because the clamp was applied before the division rather
than after: `min(1, px) / span` instead of `min(1, px / span)`.

**Artifacts:**

- medicine/the-pitt-resus-bay.html
- design notes in this ticket; no separate design file

**Closed:** 2026-09-27

### D-002 · Turn the piece into a learning reference

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27

**Description:**
Purpose change: this is now the user's standing reference for learning
medicine as a software engineer, not a viewer's glossary. Depth is wanted;
length is not a constraint (T-005 answered).

Architecture gains a **second axis**. The time-to-harm ruler still orders
sections; inside each section, depth layers run: the word → the mechanism →
the model (the systems-legible abstraction) → the evidence. Progressive
disclosure so it stays skimmable as a lookup and rewards a long read.

This ticket ships the foundation:
1. Part zero, "If you build systems" — the translation table between clinical
   and systems vocabulary, and the cost-asymmetry argument that explains why
   medicine tolerates classifiers no engineer would ship.
2. An interactive diagnostic-reasoning panel: pre-test probability, likelihood
   ratios, post-test probability, and the same numbers shown as a confusion
   matrix over a cohort of 1000 with the recall/precision labels.
3. A references apparatus with numbered, actually-fetched sources.

Standing rule from T-009: every numeric claim carries a source that was
fetched, or is marked unverified. No plausible-looking citations.

**Blockers:** none

**Artifacts:**

- medicine/the-pitt-resus-bay.html — part zero (s-engineer, s-reasoning),
  the reasoning bench, and the sources apparatus (s-refs)

**Verification:** the bench's arithmetic was checked against published
likelihood ratios rather than against itself — paediatric FAST inputs compute
to LR+ 10.66 / LR− 0.459 against the source's 10.63 / 0.46.

**Closed:** 2026-09-27

### E-007 · Depth layers across the existing nine sections

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-09-27

**Description:**
Add the mechanism / model / evidence layers to the six bay sections and the
drug and monitor sections, per the D-002 architecture. Each layer is a
disclosure block, closed by default, so the skim path is unchanged.

**Blockers:** none

**Closed:** —

### E-008 · Correct the chest panel against R-004

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-09-27

**Description:**
R-004 found four substantive errors in the shipped chest section. Do not start
until the rest of the research agenda has run — the section may need rewriting
rather than patching, and R-002/R-006 may hit the same panel.

**RCA:** the section was written from model knowledge and shipped before any
source was retrieved. It presented a contested landmark as settled, named the
anterior axillary line where the pooled evidence favours midaxillary, omitted
laterality entirely, and specified a needle gauge while omitting needle length
— which turns out to be the variable that actually predicts failure. The
process error, not the content error, is the thing to fix: implement ran
before research.

**Blockers:**

- R-002, R-003, R-006 (same panel and neighbouring claims still unsourced)

**Closed:** —

### D-003 · Evidential status display

**Status:** design complete, build not started
**Type:** implement
**Priority:** high
**Created:** 2026-09-27

**Description:**
Design in `design-evidence.md`. Three axes (strength / stance / currency), four
underline styles borrowed from monitor signal-quality convention because the
colour palette is fully committed to alarm priority, a section-level currency
stamp, and a findings.md → evidence.json → HTML pipeline with a lint so the
document cannot drift from the research.

Two constraints are load-bearing and must survive implementation: the apparatus
may not be used to keep a wrong sentence on the page, and prose is preferred to
apparatus wherever the sentence can carry the caveat itself.

**Blockers:** none

**Closed:** —

## Next Orchestrator Action

Research phase. The document is frozen for content edits until the R- agenda
in agents/researcher/tickets.md has run. E-002 shipped 2026-09-27. E-006 opens only after the user reads
the re-spined file and answers T-005.
