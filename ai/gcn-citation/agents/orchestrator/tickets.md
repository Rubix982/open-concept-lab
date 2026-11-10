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

---

### O-004 · Scope and plan Research Knowledge Infrastructure

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-04-12

**Description:**
Established the research knowledge infrastructure vision as the primary goal of this
project. The GNN/arXiv pipeline work was the technical foundation. The actual system
builds a four-layer claim-level knowledge graph over AI/ML literature.

Domain selected: AI, Machine Learning, Deep Learning, Computer Vision, Statistics.
Data source: existing 10K arXiv papers + arXiv pipeline already built.
New module: src/knowledge/

**Artifacts:**
- docs/research/knowledge_infra_requirements.md
- agents/orchestrator/tickets.md (this)

**Closed:** 2026-04-12

---

### O-005 · Coordinate Phase 1: L1 + L2 pipeline

**Status:** open
**Type:** coordinate
**Priority:** high
**Created:** 2026-04-12

**Description:**
Coordinate implementation of Phase 1 of the knowledge infrastructure:
DuckDB schema, paper ingest (L1), and paper-level extraction (L2).

Sequence:
1. E-013 (DuckDB schema) — no dependencies
2. E-014 (L1 ingest) — depends on E-013
3. R-003 (L2 extraction prompt design) — no dependencies, runs parallel to E-013
4. E-015 (L2 extraction pipeline) — depends on E-013 + R-003
5. E-016 (basic query interface) — depends on E-014 + E-015

Done when: can answer "what papers studied batch normalization in transformers?"
with citations and brief summaries.

**Blockers:** none

**Closed:** —

---

### O-006 · Reconcile the engineer's ticket record against itself

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-11-10
**Updated:** 2026-11-10

**Description:**
`ai/tools/check_record.py` reports fourteen faults in this project's record, and
one of them is structural: `E-016` names two separate ticket entries. An id that
names two things makes every reference to it ambiguous — the CHANGELOG line, the
plan's completed list, the `decisions.md` entry and `E-019`'s blocker all say
`E-016` and none of them can say which.

Close that one first, and close it on evidence rather than on which entry reads
better: the deliverable on disk, the decisions entry, the CHANGELOG line, and the
commit that landed the file.

**Open after this:** the rest of the checker's list for this project. Seven
tickets are closed with no artifacts recorded (`E-017`, `E-018`, `E-019`,
`E-025`, `R-005`, `R-006`, `R-008`); `E-025` says closed with an empty `Closed`;
`E-022` carries a close date while its status reads `open`; `E-023` carries a
close date and a status of `cancelled`, which the lifecycle does not define. Also
noted while reading, and not caught by the checker because it contradicts nothing
on its own: `O-005` still reads `open` although the phase it coordinates is
recorded complete.

**Blockers:** none

**Artifacts:**

- agents/engineer/tickets.md → `E-016` merged from two entries into one, and
  `E-017`, `E-018`, `E-019`, `E-022`, `E-023`, `E-025` given their artifacts,
  their statuses, or both
- agents/researcher/tickets.md → `R-005`, `R-006`, `R-008` given their artifacts
- `python3 ai/tools/check_record.py` reports nothing for this project; it
  reported fourteen faults before

**What the fixes rest on:** no status was changed on the strength of how an entry
reads. Each one was settled against something outside the ticket — the module on
disk, its `decisions.md` entry, the commit that landed it, the CHANGELOG line, or
the absence of the file it claimed. Two entries lost a claim that way: `E-025`
closes on the corpus re-embedding and explicitly not on the claims index it also
describes, because `data/knowledge/embeddings_claims.npy` is not there; `E-023`
closes as superseded rather than complete, because no code of its own was ever
written.

**Still standing, and deliberately not touched:** `O-005` reads `open` although
the phase it coordinates is recorded complete. The checker cannot see it — an
entry with no close date contradicts nothing — and closing a coordination ticket
is a judgement about whether the phase is done, which is not a record repair.

**Closed:** 2026-11-10
