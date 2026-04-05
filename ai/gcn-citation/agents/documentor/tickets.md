# Documentor Tickets

---

### D-001 · Write session_2026_04_04.md

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Write session documentation for the 2026-03-29/04-04 session covering:
GT architecture discussion, routing shift experiment and results, residual stream
isolation experiment and results, key findings about block importance and routing
stability. Include next session checklist.

**Artifacts:**
- docs/sessions/2026-04-04.md

**Closed:** 2026-04-05

---

### D-002 · Write research_requirements.md

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-04-04
**Updated:** 2026-04-05

**Description:**
Write and maintain the full project requirements document covering: vision,
compute constraints, data pipeline, downstream tasks, three exploratory goals
(cross-disciplinary ideas, interdisciplinary nodes, prompting at scale),
pre-training methods, prompting methods, architecture overview, phased plan,
and open questions. Updated multiple times to incorporate research findings
(OpenAlex, SPECTER2 MPS) and scale decisions (500K/1M).

**Artifacts:**
- docs/research/requirements.md

**Closed:** 2026-04-05

---

### D-003 · Write phase0_plan.md and ground truth pairs

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Write a detailed 533-line Phase 0 implementation plan covering all 5 modules
with full specs, validation checklists, integration test script, and risk table.
Also create initial cross-disciplinary ground truth pairs dataset with 20 curated
pairs covering physics↔ML, math↔ML, neuroscience↔ML, network science↔ML,
statistics↔ML, economics↔ML.

**Artifacts:**
- docs/plans/phase0.md
- data/ground_truth/cross_disciplinary_pairs.json (20 pairs)

**Closed:** 2026-04-05

---

### D-004 · Reorganize docs/ into three-tier structure

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-03-29
**Updated:** 2026-03-29

**Description:**
Reorganize the flat docs/ folder (17 files) into a three-tier structure with
subdirectories for sessions/, plans/, and research/. Use git mv for tracked files
and regular mv for untracked files. Create docs/README.md as a clean index.
Update all external references across CLAUDE.md, README.md, agent ticket files,
and cross-linking session notes. Append new directory terms to agents/shared/glossary.md.

**Artifacts:**
- docs/README.md (new index)
- docs/sessions/2026-03-24.md (was docs/session_2026_03_24.md)
- docs/sessions/2026-03-29.md (was docs/session_2026_03_29.md)
- docs/sessions/2026-04-04.md (was docs/session_2026_04_04.md)
- docs/plans/phase0.md (was docs/phase0_plan.md)
- docs/plans/prog_learning_roadmap.md (unchanged name)
- docs/plans/arxiv_pipeline.md (was docs/arxiv_pipeline_plan.md)
- docs/plans/graphsage_v2.md (was docs/graphsage_v2_plan.md)
- docs/plans/graphsage_v2_1.md (was docs/graphsage_v2_1_plan.md)
- docs/plans/graphsage_jax.md (was docs/graphsage_jax_plan.md)
- docs/plans/graphsage_aggregator.md (was docs/graphsage_aggregator_plan.md)
- docs/plans/graphsage_sampler.md (was docs/graphsage_sampler_plan.md)
- docs/plans/gat.md (was docs/gat_plan.md)
- docs/plans/gt.md (was docs/gt_plan.md)
- docs/plans/gt_nnsight.md (was docs/gt_nnsight_plan.md)
- docs/research/requirements.md (was docs/research_requirements.md)
- docs/research/phase0_research.md (was docs/phase0_research.md)
- docs/research/research_questions.md (was docs/research_questions.md)

**Closed:** 2026-03-29
