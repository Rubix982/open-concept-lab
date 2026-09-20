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

**Status:** open
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

**Artifacts:** —

**Closed:** —
