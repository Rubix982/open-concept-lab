# Shared Decisions

Owned by: Engineer
Append-only. No edits to prior entries.

---

## [Phase 1] Decision: Artifact Structure

_Date: 2026-04-22_

**Decision:** Each paper section gets a folder under `sections/` with
`notes.md`, `diagram.md`, `visualize_results.py`, and `output/`.

**Rationale:** Consistent structure makes sections independently navigable.
Every artifact is grounded in pre-computed result data — no model required.

**Alternatives rejected:** Single flat notes file (not navigable at scale).

**Revisit if:** Section count exceeds 10 and navigation becomes unwieldy.
