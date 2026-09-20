# Engineer Tickets — research-track-minded

### E-001 · Test the Tier 2 questions against a real draft

**Status:** open
**Type:** spike
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 2h (time-boxed — this is a spike, not a build)

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

**Blockers:** —

**RCA:** —

**Artifacts:** —

**Closed:** —
