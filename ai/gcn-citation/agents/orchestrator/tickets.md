# Orchestrator Tickets

---

### O-001 · Initialize agentic project structure

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Create the full agentic directory structure for the gcn-citation project.
Initialize plan.md, shared/, agents/ subdirectories, and backfill all work
done in prior sessions into the ticket/changelog format.

**Artifacts:**
- plan.md
- agents/shared/findings.md, agents/shared/decisions.md, agents/shared/glossary.md
- agents/orchestrator/tickets.md (this file)
- agents/researcher/tickets.md
- agents/engineer/tickets.md
- agents/documentor/tickets.md
- CHANGELOG.md

**Closed:** 2026-04-05

---

### O-002 · Define research requirements and phase plan

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-04-04
**Updated:** 2026-04-05

**Description:**
Work with user to define the full project vision, exploratory goals, compute
constraints, data pipeline, pre-training and prompting method comparisons,
phased implementation plan, and scale targets (500K working, 1M Phase 4).

**Artifacts:**
- docs/research/requirements.md

**Closed:** 2026-04-05

---

### O-003 · Coordinate Phase 0 agent work

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Launch and coordinate three parallel agents for Phase 0:
- Researcher (R-001): technical dependency research
- Documentor (D-003): phase0_plan.md + ground truth pairs
- Engineer (E-003): pipeline directory structure + stubs

Update research_requirements.md with researcher findings (S2ORC → OpenAlex,
SPECTER2 MPS details). Open next tickets after all three closed.

**Artifacts:**
- plan.md (updated)
- agents/shared/decisions.md (updated with S2ORC → OpenAlex decision)

**Closed:** 2026-04-05
