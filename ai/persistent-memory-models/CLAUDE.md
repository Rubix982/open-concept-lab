# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research Knowledge Infrastructure — a system for ingesting research papers, extracting discrete claims and facts, building a typed knowledge graph with epistemic classification, and enabling graph-traversal queries across the research literature. The goal is to capture knowledge at claim-level granularity (not paper-level) so that questions like "what contradicts this claim?" or "has this method been applied to that problem?" become graph traversals.

The authoritative design document is `vision.md`. It describes a four-layer memory model and a phased build sequence.

## Commands

```bash
# Install
pip install -e .

# Infrastructure (Docker)
make up          # Start Temporal, ChromaDB, Postgres, App Worker
make down        # Stop all services

# Tests
pytest tests/ -v                        # All tests
pytest tests/ -v -m unit                # Unit tests only
pytest tests/ -v -m integration         # Integration tests only
pytest tests/benchmarks/ -v             # Benchmarks
pytest tests/test_fact_extractor.py -v  # Single test file
pytest tests/ --cov=src/persistent_memory --cov-report=html  # Coverage

# Code quality
ruff format src/ tests/                 # Format
ruff check src/ tests/ --fix            # Lint + autofix
mypy src/ --ignore-missing-imports      # Type check
make pre-commit                         # All pre-commit hooks
make check                              # Format + lint + unit tests
```

## Architecture

### Vision: Four-Layer Memory Model (see vision.md)

| Layer | Purpose | Query Target | Current Status |
|-------|---------|-------------|----------------|
| **L1 — Raw Chunks** | Exact source text, no interpretation | Grounding a specific claim with primary source | Implemented (ChromaDB vector store) |
| **L2 — Episodic (Paper-level)** | One structured record per paper: what was studied, how, what was found | "Find papers that worked on X" | Not yet separated from L1 — both use the same vector store. Needs its own structured schema. |
| **L3 — Semantic Facts** | Deduplicated claims with confidence, epistemic status, typed edges | Primary query target for factual questions | Partially implemented — `FactExtractor` produces generic SPO triples. Missing: research-specific schema (`claim, evidence, metric, value, source_papers[], confidence`), deduplication, NLI contradiction detection, epistemic classification (`established`/`preliminary`/`contested`/`ungrounded`). |
| **L4 — Conceptual/Meta** | Cross-corpus patterns inferred via clustering | Synthesis questions | Not implemented. Requires HDBSCAN clustering of L3 facts + reasoning LLM. |

### Core Package (`src/persistent_memory/core/`)
- `persistent_context_engine.py` — Central engine: PersistentContextAI, PersistentKVCache, PersistentVectorStore (ChromaDB), PersistentKnowledgeGraph (NetworkX), KnowledgeConsolidator, ContextArchiver
- `context_router.py` — Neural policy network (PyTorch) that routes queries to memory layers. Currently routes to generic layers, not yet aligned with vision's intent-classification (factual/exploratory/grounding/synthesis) with cascading retrieval.
- `hierarchical_attention.py` — Multi-head attention at chunk/sentence levels, PersistentTree for hierarchical summarization, AttentionTrainer
- `fact_extractor.py` — LLM-powered extraction of structured facts (Fact, ExtractionResult); includes MockFactExtractor for testing. Current schema is generic SPO triples — needs redesign to vision's research-specific schema.
- `enhanced_llm.py` — LLM wrapper integrating all memory layers for context-augmented generation
- `attention_retrieval.py` — Attention-weighted consolidation and retrieval from vector store
- `conference_connector.py` — Fetches papers from ML conferences (NeurIPS, ICML, etc.)
- `arxiv_downloader.py` — Downloads and extracts text from arXiv papers
- `context_autoencoder.py` — VAE for embedding compression (complete and trainable)
- `dynamic_context_allocator.py` — Token-budget allocation based on query complexity
- `context_quality_monitor.py` — Evaluates relevance, diversity, coverage, hallucination risk

### Other Packages
- `workflows/` — Temporal durable workflows (`book_ingestion_workflow.py`, `paper_ingestion_workflow.py`)
- `stores/` — Storage abstractions: `data_repository.py` (filesystem paper cache), `query_cache.py` (Redis), `latency_optimizer.py`, `storage_optimizer.py`
- `processors/` — `batch_processor.py` (concurrent doc processing), `streaming_query.py` (SSE streaming)
- `api.py` — FastAPI server (8 endpoints: health, query, stream, cache, ingest, batch ingest, workflow status, metrics)
- `worker.py` — Temporal worker entry point
- `utils/cli.py` — Typer CLI with 10+ commands (ingest, query, search-papers, stats, etc.)

### Infrastructure (Docker Compose — 9 services)
- **Temporal** + Postgres + Elasticsearch + Temporal UI (workflow orchestration)
- **ChromaDB** (vector store, port 8000)
- **Redis** (query cache, port 6379)
- **App worker** + **API server** (port 8080)
- **Prometheus** (9090) + **Grafana** (3000)
- **Ollama** expected on host (`host.docker.internal:11434`)

## Known Issues and Current State

### What works standalone (no Docker needed)
- Core ML modules: hierarchical attention, context autoencoder, quality monitor, dynamic allocator, context router
- `scripts/demo_working.py` exercises these components
- ArxivDownloader and DataRepository (paper fetching + filesystem caching)

### What requires Docker stack
- Full ingestion pipeline (Temporal workflows)
- API server, vector search, knowledge graph queries
- `scripts/chatbot.py` requires Ollama

### Import structure
The package was restructured into subpackages (`core/`, `stores/`, `workflows/`, `processors/`, `utils/`). Many imports have been fixed but some may still reference old flat paths. If you see `persistent_memory.X` failing, check `persistent_memory.core.X`, `persistent_memory.stores.X`, etc. The top-level `__init__.py` re-exports from `core` and `stores`.

### Key gaps relative to vision.md
1. **L2/L1 conflated** — need separate structured per-paper records
2. **L3 fact schema** — needs redesign from generic SPO to research-specific claims with epistemic status
3. **No deduplication or NLI** — claim identity resolution and contradiction detection not implemented
4. **No DuckDB** — vision specifies DuckDB for L3 fact storage; currently NetworkX in-memory
5. **No fine-tuning pipeline** — teacher→student distillation flywheel is absent
6. **L4 not started** — batch clustering + reasoning synthesis

### Data assets
- `data/` — Pride and Prejudice text (test data), mostly empty dirs
- `demo_data/` — 1 paper cached: "Attention Is All You Need" (1706.03762) with PDF, extracted text, metadata

## Tech Stack

Python 3.11+, Temporal, ChromaDB, NetworkX, Ollama/OpenAI, FastAPI, PyTorch (attention modules), Pydantic v2, Ruff + mypy for code quality.

## Test Markers

Tests use pytest markers: `unit`, `integration`, `slow`, `benchmark`. Default run includes coverage via `--cov`.
