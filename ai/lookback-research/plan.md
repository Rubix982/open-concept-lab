# Project: Lookback Research — Paper Dissection

_Last updated: 2026-04-25 by O-001_

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

_(none — all Phase 2 research tickets closed)_

## Blocked

_(none)_

## Completed (Phase 2)

| ID    | Agent      | Title                                        | Closed     |
| ----- | ---------- | -------------------------------------------- | ---------- |
| R-001 | Researcher | BigToM generalization analysis               | 2026-04-22 |
| R-002 | Researcher | Cross-model replication analysis             | 2026-04-22 |
| R-003 | Researcher | Synthesis document                           | 2026-04-22 |
| R-004 | Researcher | Model evaluation landscape                   | 2026-04-22 |
| R-005 | Researcher | Cross-model visibility lookback              | 2026-04-22 |
| R-006 | Researcher | Related work — paper sections 7 and 8        | 2026-04-22 |
| E-001 | Engineer   | RoPE and repeat_kv annotated explainer       | 2026-04-22 |
| E-002 | Engineer   | RetrievalProfile prototype                   | 2026-04-22 |

## Current Phase

Phase 3 — Code Understanding (scripting track)

Generating annotated explainer scripts in `scripts/` to walk through the
paper's core algorithms and attention implementation in detail.

## Next Orchestrator Action

Open next E- ticket when user identifies the next piece of code to explain.
