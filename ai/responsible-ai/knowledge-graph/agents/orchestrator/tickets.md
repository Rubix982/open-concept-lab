# Orchestrator Tickets (O-)

### O-001 · Initialize knowledge-graph subproject

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14

**Description:**
Stand up the claim-knowledge-graph vertical-slice subproject: agentic directory
structure, `plan.md`, shared surfaces, confirm venv, install + pin the graph DB.
Sequence the first wave of tickets (R-001, E-001 in parallel; E-002/E-003/E-004 blocked).

**Artifacts:**

- knowledge-graph/plan.md
- knowledge-graph/agents/** (shared surfaces + per-role ticket files)
- knowledge-graph/agents/shared/decisions.md → [E-000] Kùzu storage decision
- kuzu==0.11.3 installed in ai/responsible-ai/.venv, pinned in requirements.txt

**Closed:** 2026-06-14

---

### O-002 · Sequence Phase 2 once R-001 closes

**Status:** closed
**Type:** coordinate
**Priority:** medium
**Created:** 2026-06-14
**Updated:** 2026-06-14

**Description:**
When R-001 closes with a corpus choice + confidence, apply confidence-gated
sequencing: `high` → open E-002 as `implement`; `medium` → open E-002 as a `spike`
first; `low` → open a follow-up R- ticket before any implementation.

**Outcome:** R-001 closed at HIGH confidence (PubMed-RCT 20k). Per the gate, E-002
opens as a normal `implement` ticket (status: blocked → open). The documented OOD
risk does not downgrade the gate — it is folded into E-002's acceptance criteria
(must include an out-of-distribution eval on real CS sentences).

**Closed:** 2026-06-14

---

### O-004 · Sequence the LLM edge-typer effort

**Status:** in-progress
**Type:** coordinate
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14

**Description:**
Coordinate the edge-typer tree (docs/llm-edge-typer-plan.md). Taxonomy confirmed by user
as the RICH set (R-004 closed). Dependency order: R-004 (done) → build R-005 eval gold set
+ E-006 typer in parallel → E-008 integrate/rebuild after both. E-007 (candidate review)
runs alongside. Confidence gate: R-004 is HIGH (user-confirmed) → E-006 opens as a normal
implement ticket.

**Artifacts:**

- docs/llm-edge-typer-plan.md (the plan tree)

---

### O-005 · Sequence the hybrid full-text edge-typer arc

**Status:** in-progress
**Type:** coordinate
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16

**Description:**
Sequence the architecture evolution (docs/llm-edge-typer-plan.md → Architecture Evolution;
findings.md [R-006]). Order: R-007 (source) → E-009 (full-text) → E-010 (citation linking) →
E-011 (citance typer) → E-012 (hybrid merge). E-006 (semantic typer, abstracts) runs in
parallel and feeds E-012. E-008 (abstract-only ship) remains an OPTIONAL interim win.
Confidence-gate: R-007 HIGH → open E-009/E-010 as implement; if R-007 finds S2 covers our
papers well, E-010 shrinks to reuse rather than build.

**Next action:** run R-007 (source strategy) — it decides build-vs-reuse for the whole arc.

**Artifacts:** docs/llm-edge-typer-plan.md → Architecture Evolution
