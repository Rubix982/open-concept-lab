# Engineer Tickets — research-track-minded

### E-001 · Test the Tier 2 questions against a real draft

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 2h (time-boxed — this is a spike, not a build)
**Spent:** ~1.5h

**Description:**
Before any skill file is written, establish that the Tier 2 structural questions
in `corpus/deletion-list.md` actually change an output. R-003 closed with them
derived from eight exemplar passages and one negative control, and never run.

Procedure:

1. Pick one real draft. Preferred: a section of `ai/edit-slice/design.md` or a
   draft blog post — something Saif wrote *and* something generated, so the
   questions are tested on both.
2. Generate a baseline: ask for a passage on the same topic with no guidance.
3. Generate a treated version: same request, with the eight Tier 2 questions
   supplied as the only instruction. No Tier 1, no voice profile, no exemplars —
   isolating the variable is the point of the spike.
4. Compare on three pre-stated outcomes:
   - **Confirm:** the treated version contains a claim that could be false where
     the baseline did not, and headings gained truth values.
   - **Deny:** the treated version is structurally identical and merely reworded.
   - **Null:** treated version is different but not along the predicted axis —
     record what axis it moved on instead.

Pre-stating the null matters here: the likeliest failure is that the questions
produce *longer* output that is equally unfalsifiable.

**Design change made at execution time.** Step 2 of the description — generate a
baseline myself — was replaced with a **blind baseline**: a real passage of the
AI-generated Deep Research report's own prose, produced by a system with no
knowledge of Tier 2. The original design made me author, reviser and scorer while
knowing the hypothesis. The substitution also turns the spike into a *revision*
test, which is closer to how the skill will actually be used. Recorded rather than
silently changed.

**Blockers:** —

**RCA:** —

**Artifacts:**

- `agents/engineer/workspace/e001/00-preregistration.md` — metrics and outcomes, pre-stated
- `agents/engineer/workspace/e001/01-baseline.md` — blind baseline, 472 words
- `agents/engineer/workspace/e001/02-treated.md` — Tier 2 applied, 558 words
- `agents/engineer/workspace/e001/03-scoring.md` — every counted item enumerated
- `agents/engineer/workspace/e001/score.py` — mechanical scoring for M4, M5
- `agents/shared/decisions.md` → two [E-001] decisions

**Closed:** 2026-09-20 — **CONFIRM.** Falsifiable-as-written claims 1 → 8, length
+18%, negative control flat. The pre-stated null did not fire. Incidental and
decisive: the baseline scores 0.0 on Tier 1 and is still useless, which
demonstrates R-003's finding on a single passage. M6 unchanged at zero — Tier 2
converts missing evidence into a stated gap and cannot conjure evidence.

---

### E-002 · Write the skill

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20

**Description:**
Package the corpus into an installable Claude skill. Everything it needs now
exists and is evidenced; this ticket is assembly, not discovery.

Structure:

- **Primary pass — Tier 2.** The eight structural questions from
  `corpus/deletion-list.md`, with the falsifiability question first. E-001 showed
  these carry the effect.
- **Secondary pass — Tier 1.** The twelve lintable bans, run over the finished
  draft. Framed explicitly as a floor, not a quality gate.
- **Reference — voice profile.** The 21 moves from
  `agents/shared/findings.md` [R-001], especially hedging-quarantine.
- **Reference — exemplar passages.** `corpus/papers/`, including the
  anti-exemplar, which E-001 confirmed is the sharpest teaching artifact.
- **Declared limitation.** Per [E-001] decision 2: the pass improves epistemic
  structure, not the evidential base.

Open questions to settle while writing, not before:

- Is "Limits" exempt from the truth-value heading rule? (E-001 M3 left it open.)
- Does the skill run the Tier 1 lint as a script, or as instructions? A script is
  cheaper and exact; `agents/researcher/findings/negspace.py` already exists.

**Blockers:** —

**Artifacts:**

- `skill/research-writing/SKILL.md` — entry point, 111 lines
- `skill/research-writing/references/{structure,mathematics,voice,exemplars}.md`
- `skill/research-writing/scripts/lint.py` — 13 rules, mention-aware
- `~/.claude/skills/research-writing` — symlink, installed
- `agents/shared/decisions.md` → two [E-002] decisions

**Closed:** 2026-09-20 — both open questions settled ("Limits" is exempt; the lint
is a script). Self-lints clean, with regressions holding in both directions: the
E-001 baseline still fires at 58.9/10k and three hand-written documents stay at
0.0/10k. Untested against a live drafting session — that is E-003.

---

### E-003 · Use the skill on live work

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20

**Description:**
The skill is validated on one revision of one blind baseline. It has never been
used while actually drafting, which is most of what it is for. Do not extend it
further until it has been.

Use it on the next piece of writing that needs doing anyway — an `edit-slice` or
`rome-neighbors` section, or the next blog post. Then record, in this ticket:

- Which pass produced the most change, and which was skipped as not worth it.
- Any rule that fired and was wrong (a false positive in the claim audit matters
  more than one in the lint).
- Whether the Limits section wrote itself or had to be forced.
- Whether `SKILL.md` was actually read end to end, or whether it is already too
  long. The project's own first finding was that extra instruction layers change
  nothing; this skill is subject to that finding.

**Blockers:** —

**Artifacts:**

- `agents/engineer/workspace/e003/01-pass1-claim-audit.md` — ten claims audited
- `agents/engineer/workspace/e003/02-draft.mdx` — the section, 1,371 words
- `agents/engineer/workspace/e003/03-skill-test-record.md` — the defect list
- `web/blog/2026-09-15-five-days.mdx` — section inserted, gap statement retracted
  and replaced, standfirst updated

**Closed:** 2026-09-20 — used on a real section covering [E-016]/[E-017]. Pass 1
produced the most change, but by **reordering** the section rather than by catching
unfalsifiable claims (it caught none — `decisions.md` is already written to that
standard). Five defects found, none fixed; E-004 opened. n=1 and the author is the
skill's author, so the list is to be tested rather than acted on.

---

### E-004 · Fix the defects E-003 found

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-20
**Updated:** 2026-09-20

**Description:**
Five defects from the first live use, in `e003/03-skill-test-record.md`, ranked:

1. **Pass 1 assumes a draft exists.** "For each paragraph of the draft" — add a
   drafting mode that audits available claims before prose exists.
2. **The audit's ranking use is undocumented.** It put the analytic claim above the
   empirical one and restructured the section; the skill describes it only as a
   filter.
3. **No rule separates a number-backed qualifier from a hedge.** "Largely
   determined" summarising a measured 7% is not the same as "largely" standing in
   for a number.
4. **The Limits section needs a use-constraint category** — "do not read this as a
   method proposal" is a limit on how the result may be used, not on what it shows,
   and no Pass 2 question generates it.
5. **`voice.md` went unused.** Decide whether it is drafting-only and say so, or
   cut it.

**Blockers:** — (cleared by E-005)

**Artifacts:**

- `skill/research-writing/SKILL.md` — 111 → 171 lines; mode table, ranking section,
  three-category Limits, scope boundary
- `skill/research-writing/references/voice.md` — rescoped and shortened
- `agents/shared/decisions.md` → four [E-004] decisions

**Closed:** 2026-09-20 — 1–4 fixed, 5 decided, 6 held. Defect 1's fix changed from
what E-003 proposed: three modes, not two, because design mode asks a different
question rather than the same one earlier. Feasibility (defect 5) absorbed as a
design-mode assumption row rather than a new pass, which is where it landed
unprompted in E-005. Self-lints clean; the E-001 baseline regression holds at
58.9/10k.

**Watch:** SKILL.md grew 54%. E-003 judged 111 lines readable end to end; 171 is
untested. If a third use skips sections, cut before adding.

---

### E-005 · Second live use — a design document

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20

**Description:**
E-004 was blocked on a second live use on a structurally different document. A
design was chosen deliberately: it has **no results**, which is the axis most
likely to break a pass built around auditing claims.

Target: `edit-slice/design.md` Part IV — the [T-075] layer sweep design.

**Blockers:** —

**Artifacts:**

- `agents/engineer/workspace/e005/01-pass1-audit.md` — five assumptions audited
- `agents/engineer/workspace/e005/02-draft.md` — the design, 1,355 words
- `agents/engineer/workspace/e005/03-skill-test-record.md` — recurrence table
- `edit-slice/design.md` Part IV — appended
- `edit-slice/threads.md` — T-075 set active, T-076 spawned

**Closed:** 2026-09-20 — three of five E-003 defects recurred (2, 4, 5) and are
safe to fix. Defect 1 recurred in a form that changes the fix: on a design Pass 1
is not mis-ordered, it is a category error, so the mode count goes to three
(revise / draft / design). One new defect: nothing in the skill asks whether the
work can be run, and it overlaps `CLAUDE.md`'s design protocol without referencing
it.

The pass produced a **research** finding rather than a writing improvement — every
control behind [E-017]'s published claim is same-subject, and the matched
different-subject control has never been run. Spawned T-076 and reordered the work.
