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
