# Project: Lookback Research — Paper Dissection

_Last updated: 2026-04-22 by O-001_

## Objective

Fully understand "Language Models Use Lookbacks to Track Beliefs" (ICLR 2026)
through section-by-section dissection, connecting every paper figure to
reproducible experiments and documented artifacts — and relating findings
to the Research Knowledge Infrastructure vision.

## Current Phase

Phase 2 — Generalization, Replication, and Synthesis

## Completed (Phase 1)

All core mechanism sections documented with notes, diagrams, and
visualizations grounded in pre-computed IIA results:

| Section | Content |
| --- | --- |
| `00-abstract/` | Concepts: ToM, causal mediation, OIDs, co-location |
| `01-causal-mediation/` | Figure 2 heatmaps from tracing experiments |
| `02-binding-lookback/` | 8 experiments, IIA pipeline, temporal windows |
| `03-answer-lookback/` | Pointer/payload handoff at layer 55 |
| `04-attention-knockout/` | Attention path criticality by layer |
| `05-visibility-lookback/` | Vis_ID, full 5-mechanism pipeline |
| `06-paper-figures/` | Every figure mapped to artifact + reproduced numbers |
| `deep-dives/` | Residual stream, token matrix, OIDs, attention heads |

## Active Tickets

| ID    | Agent      | Title                                    | Status      |
| ----- | ---------- | ---------------------------------------- | ----------- |
| S-001 | Scholar    | ROME — Abstract and Introduction         | open        |
| S-002 | Scholar    | ROME — Causal Tracing (Section 3)        | open        |
| S-003 | Scholar    | ROME — Editing Method (Section 4)        | open        |
| S-004 | Scholar    | ROME — Results and Comparison            | open        |

## Blocked

_(none)_

## Next Orchestrator Action

R-001 is highest priority. Begin immediately after this plan is written.
R-002 depends on R-001 completing (same analysis pattern, builds on findings).
R-003 depends on R-001 and R-002 (synthesis needs all findings in hand).
