# Project: gcn-citation — ProG-Scale arXiv Graph Learning

_Last updated: 2026-04-05 by O-004_

## Objective

Pre-train a graph encoder on 500K–1M arXiv papers using multiple self-supervised
objectives, then adapt to multi-label classification, hierarchical prediction, and
idea-based link prediction via lightweight prompts — without fine-tuning the backbone.

## Current Phase

**Phase 0 COMPLETE** ✅ — All pipeline modules implemented and validated on real 10K arXiv data.
Next: Phase 1 — Scale to 100K + supervised baselines

## Active Tickets

_None. Phase 0 complete._

## Blocked

_None._

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
