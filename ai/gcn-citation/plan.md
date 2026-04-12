# Project: gcn-citation — ProG-Scale arXiv Graph Learning

_Last updated: 2026-04-05 by O-004_

## Objective

Pre-train a graph encoder on 500K–1M arXiv papers using multiple self-supervised
objectives, then adapt to multi-label classification, hierarchical prediction, and
idea-based link prediction via lightweight prompts — without fine-tuning the backbone.

## Current Phase

**Knowledge Infrastructure — Phase 1: L1 + L2 Pipeline**

GNN/arXiv work (Phase 0) is complete and serves as the technical foundation.
The primary goal is now the Research Knowledge Infrastructure: a four-layer
claim-level knowledge graph over AI/ML/DL/CV/Statistics literature.

See: `docs/research/knowledge_infra_requirements.md`

## Active Tickets

| ID    | Agent      | Title                                                    | Status |
| ----- | ---------- | -------------------------------------------------------- | ------ |
| E-021 | Engineer   | Build L3 typed edges (supports/contradicts/etc.)         | open   |
| E-026 | Engineer   | L3 claim embedding index for idea-level search           | open   |
| E-023 | Engineer   | Semantic Scholar citation edges (needs API key)          | open   |

## Blocked

| ID    | Blocked By                                        |
| ----- | ------------------------------------------------- |
| E-026 | E-020 ✅ (bulk L3 complete), R-007 ✅ (adhoc_query confirmed) — **unblocked** |
| E-023 | Semantic Scholar API key (external, still pending) |

## Phase 1 Status — COMPLETE ✅

Phase 1 end-to-end validation passed (2026-04-12):
- 500 L2 paper summaries extracted via Ollama qwen2.5-coder:7b
- 500 L3 claim nodes extracted
- 321 L2-derived relational edges (shares_method + co_domain)
- Hybrid FTS5 + SPECTER2 adhoc_query search: 8/10 queries topically relevant
- knowledge.db committed — clone and query immediately

## Completed This Session (2026-04-12)

Knowledge Infrastructure Phase 1 + improvements:
- E-013 SQLite schema (WAL mode, 6 tables)
- E-014 L1 ingest pipeline
- E-015 L2 extraction (Ollama, 6.3s/paper)
- E-016 Query interface (hybrid FTS5 + embedding)
- E-017 Corpus quality filter
- E-018 Bulk L2 extraction (500 papers)
- E-019 Phase 1 end-to-end validation — PASSES (8/10)
- E-020 L3 claim extraction pipeline + bulk run (500 claims)
- E-022 L2-derived relational edges (321 edges)
- E-024 Hybrid FTS5 + embedding re-ranking (FTS5 key-term fix)
- E-025 Re-embed with SPECTER2 adhoc_query adapter
- R-004 NLI model research (DeBERTa recommended)
- R-005 L3 claim prompt design (validated on 5 papers)
- R-006 Semantic Scholar API research (80% coverage, /references endpoint)
- R-007 Embedding model research (adhoc_query fixes concept search)
- R-008 Hybrid retrieval research (FTS5 alone 9/10, text_weight=0.7)

## Next Orchestrator Action

E-026 is now unblocked — start L3 claim embedding index.
E-021 (typed edges via DeBERTa NLI) can also start — R-004 recommends
cross-encoder/nli-deberta-v3-small at 190ms/pair on MPS.

## Blocked

| ID    | Blocked By                        |
| ----- | --------------------------------- |
| E-019 | E-016 ✅, E-018                   |
| R-005 | E-018 (need L2 summaries)         |
| E-020 | R-005, E-018                      |
| E-021 | E-020, R-005                      |
| E-022 | E-018                             |
| E-023 | R-006, Semantic Scholar API key   |

## Completed (Knowledge Infra Phase 1)

- E-013 · SQLite schema — 8/8 pass
- R-003 · L2 extraction prompt (qwen2.5-coder:7b) — medium-high quality
- E-014 · L1 ingest pipeline — 8/8 pass
- E-015 · L2 extraction pipeline (Ollama) — 7/7 pass, 6.3s/paper

## Completed This Session (2026-04-05)

- O-001 · Initialize agentic project structure
- O-002 · Define research requirements and phase plan
- O-003 · Coordinate Phase 0 agent work
- R-001 · Research arXiv S3, OpenAlex citations, SPECTER2 MPS setup
- R-002 · Verify Semantic Scholar precomputed SPECTER2 coverage — downloader confirmed
- E-001 · GT NNsight routing shift experiment
- E-002 · GT residual stream isolation experiment
- E-003 · Create pipeline directory structure and stub modules
- E-004 · Fix .gitignore for ground_truth tracking
- E-005 · Implement pipeline/arxiv_bulk.py — 22/22 checks pass
- E-006 · Implement pipeline/embedder.py — 8/8 checks pass
- E-007 · Implement pipeline/citations.py — 32/32 checks pass
- E-008 · Implement pipeline/graph_builder.py — skipped (faiss + pyg not installed)
- E-009 · Implement pipeline/sampling.py — skipped (pyg not installed)
- D-001 · Write session 2026-04-04
- D-002 · Write research_requirements.md
- D-003 · Write phase0_plan.md + ground truth pairs
- D-004 · Reorganize docs/ into sessions/, plans/, research/

## Next Orchestrator Action

E-011 is quick and unblocked — install faiss-cpu and torch_geometric, re-run
all skipped validation suites to confirm 0 failures before E-010 begins.
E-010 then runs the full pipeline end-to-end on a 10K arXiv subset.
E-010 also needs a Semantic Scholar API key (free) for the embedder downloader path.
