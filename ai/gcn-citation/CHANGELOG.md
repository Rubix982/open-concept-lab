# Changelog

_Append-only. One entry per session. Written by orchestrator at session end._

---

## 2026-04-12 · Session 6

### Knowledge Infrastructure Phase 1 — COMPLETE

**Core pipeline:**
- [E-013] SQLite schema (WAL mode, 6 tables) — src/knowledge/schema.py
- [E-014] L1 abstract ingest — src/knowledge/ingest.py
- [E-015] L2 extraction via Ollama qwen2.5-coder:7b (6.3s/paper) — src/knowledge/extract_l2.py
- [E-017] Quality corpus filter (abstract length, year, dedup, stratified sample) — src/knowledge/filter_corpus.py
- [E-018] Bulk L2 extraction — 500 papers in data/knowledge/knowledge.db
- [E-020] L3 claim extraction pipeline + bulk run (500 claim nodes) — src/knowledge/extract_l3.py
- [E-022] L2-derived relational edges (321 edges: shares_method + co_domain) — src/knowledge/derive_edges.py

**Search + retrieval:**
- [E-016] Hybrid FTS5 + SPECTER2 query interface — src/knowledge/query.py
- [E-024] FTS5 key-term extraction fix (AND-join top-2 tokens, not all 5+)
- [E-025] Re-embed with SPECTER2 adhoc_query adapter — score std 0.03 vs 0.01 before

**Validation:**
- [E-019] Phase 1 end-to-end validation PASSES — 8/10 queries topically relevant

**Research:**
- [R-004] NLI model eval: cross-encoder/nli-deberta-v3-small recommended (190ms/pair MPS)
- [R-005] L3 claim prompt: high quality on 5 papers, all atomic + self-contained
- [R-006] Semantic Scholar /references endpoint: 80% preprint coverage
- [R-007] SPECTER2 adhoc_query fixes concept search; no model switch needed
- [R-008] FTS5 alone 9/10 coverage; text_weight=0.7 for hybrid

**Data committed (reproducible from clone):**
- data/knowledge/knowledge.db — 500 L2 summaries + 500 L3 claims + 321 edges
- data/pipeline/embeddings_10k.npy — adhoc_query embeddings [10000, 768]
- data/pipeline/arxiv_10k.parquet — 500 filtered papers

## 2026-04-05 · Session 5

- [E-008] Implemented pipeline/graph_builder.py — 4 edge types, co_category capped at 1K pairs/category — src/gcn_citation/pipeline/graph_builder.py
- [E-009] Implemented pipeline/sampling.py — NeighborLoader wrapper, num_workers=0 MPS constraint — src/gcn_citation/pipeline/sampling.py

## 2026-04-05 · Session 4

- [O-001] Initialized agentic project structure — plan.md, shared/, agents/ fully populated
- [O-002] Defined research requirements and phase plan — docs/research/requirements.md
- [O-003] Coordinated Phase 0 parallel agent work — unblocked E-005, opened R-002
- [R-001] Researched arXiv S3, OpenAlex, SPECTER2 MPS — docs/research/phase0_research.md + agents/shared/findings.md
- [E-001] GT NNsight routing shift experiment — run_routing_shift.py + src/gcn_citation/models/gt_nnsight.py
- [E-002] GT residual stream isolation experiment — run_residual_isolation.py
- [E-003] Pipeline directory structure and stub modules — src/gcn_citation/pipeline/
- [E-004] Fixed .gitignore for ground_truth tracking — .gitignore
- [D-001] Session documentation — docs/sessions/2026-04-04.md
- [D-002] Research requirements document — docs/research/requirements.md
- [D-003] Phase 0 plan + ground truth pairs — docs/plans/phase0.md + data/ground_truth/cross_disciplinary_pairs.json
- [D-004] Reorganized docs/ into three-tier structure — docs/sessions/, docs/plans/, docs/research/, docs/README.md

## 2026-03-29 · Session 3

_Agentic structure not yet in place for this session. Backfilled from session notes._

- Discussed transformer architecture: residual stream, content-dependent routing, why interventions don't compose
- Identified three experiments: routing shift, residual isolation, composition test
- Added `compare_attention_routing_with_nnsight()` to gt_nnsight.py
- Ran routing shift experiment: mean shift 0.0001, 90% prediction changes
- Ran residual isolation: block 0 more important (−56.8pp vs −47.5pp for block 1)
- Added black PostToolUse hook to .claude/settings.json

## 2026-03-29 · Session 2

_Agentic structure not yet in place. Backfilled from session_2026_03_29.md._

- Created comprehensive CLAUDE.md (492 lines) for project onboarding
- Updated .claude/settings.json for Python ML research configuration
- Analyzed artifacts/ folder — identified GAT and GT as implemented but never run
- Documented performance table: JAX GraphSAGE LSTM best at 60.71% test accuracy

## 2026-03-24 · Session 1

_Agentic structure not yet in place. Backfilled from session_2026_03_24.md._

- GraphSAGE progress across multiple backends and aggregators
- arXiv 7.8K corpus milestone achieved
- Compare-runs infrastructure verified working
