# Design — showing evidential status

_D-003 · 2026-09-27. Derived from the ten findings in
`agents/shared/findings.md`, not from a generic evidence-grading scheme._

---

## 1 · What the research actually produced

The corrections are not one kind of thing. Sorted by what is really going on:

| # | Kind | Example from findings |
|---|------|----------------------|
| 1 | Authorities openly disagree | Needle site: ATLS says 5th AAL, ETC and RCS Edinburgh say 2nd MCL [R-004] |
| 2 | Standard practice, null primary outcome | 1:1:1 (PROPPR), amiodarone (ALPS) [R-006, R-002] |
| 3 | The page is simply wrong | Ketamine "holds the pressure up" [R-003] |
| 4 | Observational only | Boarding→mortality, ETCO₂→ROSC, GCS-8 [R-008, R-002, R-007] |
| 5 | True only inside a boundary | TXA: RR 0.68 at ≤1 h, **1.44** after 3 h [R-010] |
| 6 | Well supported | MAP 65 as a floor, lung US specificity, ESI kappa [R-006, R-005, R-010] |
| 7 | Never checked | AHA numerics, every quoted dose [R-009, R-011] |
| 8 | Possibly superseded | Document reflects AHA 2020; a 2025 edition exists [R-009] |

Two conclusions fall straight out.

**A single strength scale would destroy the information.** "★★☆☆☆" on the
ketamine claim tells the reader nothing; *"the pooled randomised evidence says
the opposite"* is the entire point. Star ratings compress exactly the axis that
matters here.

**There are three independent axes, not one.**

- **Strength** — what kind of evidence exists (randomised / observational / none).
- **Stance** — where the page's claim sits relative to it (supported /
  contested / conditional / wrong).
- **Currency** — when it was last checked, and against which edition.

Currency is genuinely orthogonal: the AHA numerics could be perfectly well
evidenced *and* a generation out of date. Most badge systems have no slot for
this, which is why reference documents quietly rot.

---

## 2 · Two rules that constrain the whole design

**Rule 1 — the apparatus must not enable cowardice.**
If a badge can be attached to anything, nothing ever has to be rewritten.
Category 3 (the page is wrong) therefore gets **no display state at all**. It is
a workflow state: *fix the sentence*. Badges annotate the evidence behind a
claim that is correct as written. They never launder a claim that is not.

**Rule 2 — prefer prose to apparatus.**
"1:1:1, which cut deaths from exsanguination although its trial was null on
mortality" is better than "1:1:1[badge]". A mark is used only where carrying the
caveat inline would wreck the sentence. Categories 2 and 5 usually belong in
the prose; the mark then points at the detail rather than substituting for it.

This means the finished document should have **fewer** marks than the findings
list has entries. That is the intended direction.

---

## 3 · The visual channel: signal quality, not colour

The palette is already spoken for. Colour names a physiological parameter, and
red/amber carry IEC 60601-1-8 alarm priority. An evidential alarm in red would
collide with a clinical alarm in red — the reader could not tell "this will kill
the patient" from "this rests on a cohort study." **Colour is unavailable.**

The subject supplies the right channel instead. Monitors already have a
convention for "how much do I trust this trace": they degrade the *line itself*.
Poor signal quality is drawn dashed, greyed, or flagged as artifact. That is not
a metaphor — it is literally how instruments express confidence.

So: **evidential status is rendered as the quality of the underline beneath the
claim.** Four styles, the maximum a reader will learn:

```
supported        Amiodarone 300 mg then 150 mg
                 ──────────────────────────────   solid hairline
                 randomised evidence exists

observational    boarding over 12 hours
                 ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄   dashed
                 association only; never "causes"

contested        5th intercostal space
                 ══════════════════════════════   doubled
                 guideline bodies disagree

unverified       compressions 100–120/min
                 ·····························   dotted, low contrast
                 not checked against a source
```

Unmarked prose is the default and carries no claim needing support. Most of the
document stays unmarked.

Each marked claim also takes a superscript reference number pointing into the
evidence layer. The underline says *what kind*; the number says *which source*.

---

## 4 · Where the detail lives

D-002 already defined depth layers: word → mechanism → model → evidence. The
inline mark is a **pointer into the evidence layer**, never a duplicate of it.

- **Inline** — underline style + superscript number. Quiet enough to skim past.
- **On demand** — click or focus opens the evidence layer for that section: the
  finding, the citation with PMID/DOI, the retrieval date, and the caveat.
- **Document level** — the sources section already built.

Accessibility: underline style is a visual-only channel, so every mark carries
a text equivalent on the element (`title` plus an accessible label), and the
expansion is reachable by keyboard. Underline style is *better* than colour for
low-vision and colour-blind readers, which is a happy side effect of the
alarm-palette conflict.

---

## 5 · Currency, at section level

Per-claim currency would be noise. Per-section is right, and it is what real
clinical references do — NICE and UpToDate both stamp "last reviewed".

```
┌──────────────────────────────────────────────────────────────┐
│ Arrest                                                        │
│ Two minutes of compressions, then the few seconds in which…   │
│                                                               │
│ reflects AHA 2020 · a 2025 edition exists and is not yet      │
│ incorporated · numerics unverified              [R-002, R-009]│
└──────────────────────────────────────────────────────────────┘
```

A reference document that cannot say how stale it is, is not a reference. This
stamp is the single most valuable thing in the whole design, and it only exists
because R-009 failed.

---

## 6 · The data flow — the document must not hand-maintain evidence

The entire lesson of the research phase was that presentation drifts from
evidence when the same hand writes both. So they get separated mechanically:

```
agents/shared/findings.md          researcher prose, source of truth
          │
          │  scripted build, committed
          ▼
agents/shared/evidence.json        claim-id → { status, refs, note, retrieved,
          │                                     edition, superseded_by }
          │  inlined at build time
          ▼
the-pitt-resus-bay.html            renders marks, expansions and sources
```

Claims are tagged in the HTML by id only:

```html
<span data-claim="txa-3h">TXA within 3 hours</span>
```

Everything else — style, number, caveat text, citation — comes from the JSON.
Rewriting a finding updates the document; it cannot fall out of step.

**A lint runs with the existing validators:**

1. every `data-claim` in the HTML exists in `evidence.json`
2. every entry has either a `retrieved` date or `status: unverified`
3. no entry carries status `wrong` — that status exists only in the pipeline,
   and its presence means a sentence still needs rewriting (Rule 1, enforced
   rather than promised)
4. every `refs` entry resolves to a PMID or DOI

---

## 7 · What this does not solve

- It cannot make the AHA numerics verified. It makes their absence **visible**,
  which is the honest second-best and arguably more useful to the reader than a
  number they would have trusted.
- Marking is a judgement call and I am the one making it. A claim I never
  thought to question stays unmarked and looks supported. The mark set is
  evidence of what was checked, not a guarantee of what is true.
- Category 3 claims still require someone to notice they are wrong. Nothing
  here finds them; only research does.
