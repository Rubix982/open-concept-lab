# Engineer Tickets

---

### E-001 · GT NNsight routing shift experiment

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-04-04
**Updated:** 2026-04-04

**Description:**
Add `compare_attention_routing_with_nnsight()` to `gt_nnsight.py`. Write and run
`run_routing_shift.py` — trains GT on Cora, then compares block-1 attention weights
baseline vs block-0-zeroed. Answer: does zeroing block 0 change who block 1 attends
to, or only what values it aggregates?

**Artifacts:**
- src/gcn_citation/models/gt_nnsight.py (new function)
- run_routing_shift.py

**Key findings:**
- Overall mean routing shift: 0.0001 (routing barely changes)
- Max routing shift: 0.4394 (some nodes shift dramatically)
- Prediction changes: 2432/2708 nodes (90%)
- Conclusion: block 0 matters for VALUES, not routing; routing anchored by input projection

**Closed:** 2026-04-04

---

### E-002 · GT residual stream isolation experiment

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-04-04
**Updated:** 2026-04-04

**Description:**
Write and run `run_residual_isolation.py` — trains GT on Cora, then zeros block 0
and block 1 independently and measures accuracy drop for each. Answer: which block
does more heavy lifting?

**Artifacts:**
- run_residual_isolation.py

**Key findings:**
- Baseline test accuracy: 63.1%
- Block 0 zeroed: 6.3% (−56.8pp, 2432/2708 predictions changed)
- Block 1 zeroed: 15.5% (−47.5pp, 2293/2708 predictions changed)
- Block importance ratio: 1.19x (block 0 slightly more important)
- Both blocks near random-chance floor when zeroed — model needs both

**Closed:** 2026-04-04

---

### E-003 · Create pipeline directory structure and stub modules

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Create `src/gcn_citation/pipeline/` subpackage with stub implementations for all
Phase 0 modules: config.py, arxiv_bulk.py, embedder.py, citations.py,
graph_builder.py, sampling.py. Correct interfaces, type annotations, Google-style
docstrings, `raise NotImplementedError` bodies. No implementation yet.

**Artifacts:**
- src/gcn_citation/pipeline/ (full subpackage)
- data/ground_truth/.gitkeep

**Closed:** 2026-04-05

---

### E-004 · Fix .gitignore for ground_truth tracking

**Status:** closed
**Type:** implement
**Priority:** low
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
`data/` was fully ignored in .gitignore, preventing `data/ground_truth/` from
being tracked. Fix by replacing `data/` with `data/*` + negation rules for
`data/ground_truth/` and `data/ground_truth/cross_disciplinary_pairs.json`.

**Artifacts:**
- .gitignore (updated)

**Closed:** 2026-04-05

---

### E-005 · Implement pipeline/arxiv_bulk.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-03-29

**Description:**
Implement the arXiv bulk metadata parser. Must handle:
- Stream-parse JSONL line-by-line (file too large to load at once)
- Filter by category list (any match; categories field is space-separated string)
- Handle both old-format IDs (with slashes) and new-format IDs
- Checkpoint/resume: save progress to .parquet alongside snapshot
- Interdisciplinary flag: `is_interdisciplinary = len(categories) >= 2`
- Return `pd.DataFrame` with columns: arxiv_id, title, abstract, categories,
  primary_category, is_interdisciplinary, year, month

Validate against: edge case of papers with single category, papers with 3+
categories, old-format IDs, abstract containing special characters.

See `docs/plans/phase0.md` for detailed validation checklist.

**Blockers:** none

**Artifacts:**
- `src/gcn_citation/pipeline/arxiv_bulk.py` — full implementation
- `agents/engineer/workspace/test_arxiv_sample.jsonl` — 10-record test fixture
- `agents/engineer/workspace/validate_arxiv_bulk.py` — validation script (22/22 PASS)

**Key implementation decisions:**
- `update_date` field is primary year/month source; new-format ID YYMM is fallback only
- Missing/null abstracts produce empty strings (never None)
- Checkpoint path is keyed to snapshot path only; different filter configs need separate snapshot paths
- Resume uses row-count skipping (not ID set), O(1) memory for deterministic streams

**Closed:** 2026-03-29

---

### E-009 · Implement pipeline/sampling.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-03-29
**Updated:** 2026-03-29

**Description:**
Implement `build_neighbor_sampler` and `get_dataloaders` in
`src/gcn_citation/pipeline/sampling.py`. Replace the `NotImplementedError` stub
with a full NeighborLoader wrapper with edge-type filtering, split masks, and the
critical `num_workers=0` MPS constraint.

**Artifacts:**
- `src/gcn_citation/pipeline/sampling.py` — full implementation
- `agents/engineer/workspace/validate_sampling.py` — validation script (1/1 PASS; 5/5 SKIP — torch_geometric not installed in dev env)

**Key implementation decisions:**
- `num_workers` defaults to 0 — PyG NeighborLoader with num_workers > 0 spawns
  sub-processes that cannot share MPS device context on macOS, causing silent hangs
- `edge_types` filtering matches the **relation string** (middle of the triplet), not
  the full triplet, for ergonomic caller API
- `get_dataloaders` builds three independent NeighborLoader instances with the same
  num_neighbors dict; train uses `shuffle=True`, val/test use `shuffle=False`
- Import guard raises `ImportError` with install hint when torch or torch_geometric absent
- `ValueError` raised immediately when `graph` has no `'paper'` node type

**Validation results:** 1 PASS, 5 SKIP (torch_geometric not installed)
- import_guard: PASS
- missing_paper_node: SKIP (torch_geometric absent)
- edge_type_filtering: SKIP (torch_geometric absent)
- get_dataloaders_splits: SKIP (torch_geometric absent)
- num_workers_default: SKIP (torch_geometric absent)
- minimal_iteration: SKIP (torch_geometric absent)

**Closed:** 2026-03-29

---

### E-008 · Implement pipeline/graph_builder.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-03-29
**Updated:** 2026-03-29

**Description:**
Implement the heterogeneous graph builder for the arXiv corpus pipeline.
Produces a PyG `HeteroData` graph with two node types (paper, category) and
four edge types: `cites`, `similar_to` (k-NN via FAISS), `belongs_to`, and
`co_category`. Includes `validate_graph()` with 6 sanity checks.

**Artifacts:**
- `src/gcn_citation/pipeline/graph_builder.py` — full implementation
- `agents/engineer/workspace/validate_graph_builder.py` — validation script (4 suites, graceful SKIP when faiss/pyg absent)

**Key implementation decisions:**
- `build_knn_edges()`: copies embeddings before L2-normalise (no mutation), queries FAISS in `batch_size` chunks, removes self-loops (src==dst) before returning int64 arrays
- `build_hetero_graph()`: category index derived as `sorted(set(all categories))` for determinism; `paper.y` is multi-hot float32 [N, num_categories]; `co_category` pairs capped at 1000 per category to avoid O(N²) blowup on large categories (e.g. cs.LG)
- `validate_graph()`: six checks — feature shape, duplicate edges (all 4 types), self-loops in `similar_to`, citation index range, category count consistency, `is_interdisciplinary` vs multi-hot y matrix
- `co_category` emits directed half-pairs (a, b) for a<b, then symmetrises and deduplicates with `np.unique`; self-loops removed before dedup (impossible by construction but guarded)
- Import guards follow codebase pattern: `faiss = None` and `torch = None / HeteroData = None` set on ImportError

**Validation results:** 0 PASS / 0 FAIL / 4 SKIP
- All 4 suites skip gracefully: faiss and torch_geometric not installed in this environment
- Torch 2.9.1 is available; pyg and faiss-cpu must be installed before running full validation

**Closed:** 2026-03-29

---

### E-007 · Implement pipeline/citations.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-03-29
**Updated:** 2026-03-29

**Description:**
Implement citation edge loading from OpenAlex S3 bulk data with resume support,
arXiv ID normalisation, two-pass edge resolution, index assignment, and a stub
for the defunct S2ORC source.

**Artifacts:**
- `src/gcn_citation/pipeline/citations.py` — full implementation
- `agents/engineer/workspace/test_citations_sample.jsonl` — 10-record test fixture
- `agents/engineer/workspace/validate_citations.py` — validation script (32/32 PASS)

**Key implementation decisions:**
- boto3 used if available; falls back to `urllib.request` (stdlib) via HTTPS endpoint
- Two logical passes per-shard (URL→arXiv map + raw edges in one physical pass; resolve after all shards done)
- `progress.json` tracks completed shard keys for resume across restarts
- `ids.arxiv` normalised to bare ID (strips `https://arxiv.org/abs/` prefix)
- `build_id_to_index()` sorts IDs lexicographically for deterministic indices
- `assign_indices()` silently drops edges where either endpoint is absent from mapping
- S2ORC stub raises `NotImplementedError` with clear redirect message

**Validation results:** 32/32 checks PASS
- load_s2orc_citations stub: 2/2
- _normalise_arxiv_id: 5/5
- Edge filtering from fixture (3 of 10 records yield edges): 8/8
- build_id_to_index (sorted order, dedup): 5/5
- assign_indices (int64 indices, edge drop): 12/12

**Closed:** 2026-03-29

---

### E-006 · Implement pipeline/embedder.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-03-29

**Description:**
Implement SPECTER2 embedding pipeline with MPS batching and checkpoint/resume.
Hybrid three-path strategy: bulk S3 download → per-paper API gap fill → local
SPECTER2 inference.

**Artifacts:**
- `src/gcn_citation/pipeline/embedder.py` — full implementation
- `agents/engineer/workspace/validate_embedder.py` — validation script (8/8 PASS)

**Key implementation decisions:**
- Three-path hybrid: `download_bulk_embeddings()` → `fetch_embeddings_per_paper()` → `embed_locally()`
- api_key=None skips Paths 1+2 entirely and goes straight to local inference
- Output is a memory-mapped `.npy`; L2 normalisation done in-place with `flush()`, NOT `np.save()` (calling np.save on an open memmap can deadlock on macOS)
- Checkpoint JSON maps `{arxiv_id: row_index}` — shared across all three paths
- Path 1 downloads `papers` shards to build `corpusId → arxiv_id` map, then `embeddings-specter_v2` shards filtered to matching corpusIds
- Path 3 uses `adapters.AutoAdapterModel` + `allenai/specter2` proximity adapter; sets `PYTORCH_ENABLE_MPS_FALLBACK=1` before model load

**Validation results:** 8/8 PASS
- output_shape: (4, 768) confirmed
- l2_normalisation: max_deviation=5.96e-08, zero rows preserved
- checkpoint_roundtrip: JSON save/load preserves dict exactly
- checkpoint_resume: correctly skips 3 pre-embedded papers, calls embed_locally only for 2 remaining
- no_api_key_skips_bulk_and_per_paper: bulk and per-paper mocks not called
- missing_columns_raises_valueerror: correct error on missing 'abstract' column
- load_embeddings_missing_file_raises: FileNotFoundError on nonexistent path
- load_embeddings_returns_correct_shape: (10, 768), dtype=float32

**Closed:** 2026-03-29

---

### E-010 · Add load_openalex_citations_api() to pipeline/citations.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Add an API-based citation fetcher to `src/gcn_citation/pipeline/citations.py` for
use when the corpus is small (≤50K papers) where S3 bulk download is overkill.
OpenAlex REST API requires no auth key and allows 10 RPS.

**Implement this function:**

```python
def load_openalex_citations_api(
    arxiv_ids: list[str],
    *,
    requests_per_second: float = 9.0,
    cache_path: Path | None = None,
) -> CitationEdges:
```

**Algorithm:**
1. Batch arxiv_ids into groups of 50
2. For each batch: `GET https://api.openalex.org/works?filter=ids.arxiv:{id1}|{id2}|...&select=id,ids,referenced_works&per-page=50`
3. Parse response: extract `ids.arxiv` (source) and `referenced_works` (list of OpenAlex URLs)
4. Collect all unique referenced OpenAlex URLs
5. Batch-fetch those referenced works (groups of 50) to get their `ids.arxiv` fields
6. Filter to pairs where both source AND target arXiv IDs are in the input set
7. Return `CitationEdges` with string arXiv IDs

**Rate limiting — MANDATORY per O-004 in agents/shared/decisions.md:**
- Hard cap: `requests_per_second <= 9.0`
- Exponential backoff on 429/5xx: `min(2^attempt * 1.0, 60.0)` seconds, max 5 retries
- Add jitter: `random.uniform(0, 0.5) * delay`
- Respect `Retry-After` header if present
- After 5 consecutive failures on a single batch: log warning, skip batch, continue

**Caching:**
- If `cache_path` provided: save progress as JSON after each batch (resume support)
- On resume: skip arxiv_ids already in cache

**Validation — `agents/engineer/workspace/validate_openalex_api.py`:**
1. Batching: 120 IDs → 3 batches of 50 (mock HTTP)
2. Backoff triggered on 429 (mock)
3. Retry-After header respected (mock)
4. Batch skipped after 5 failures (mock)
5. Output CitationEdges only contains pairs where both endpoints are in known set
All checks PASS before closing.

**Blockers:** none

**Artifacts:**
- `src/gcn_citation/pipeline/citations.py` (updated — new function + helpers added)
- `agents/engineer/workspace/validate_openalex_api.py` — validation script (6/6 PASS)

**Key implementation decisions:**
- `_api_get()` helper centralises rate limiting, retries, backoff, and Retry-After support
- Pass 2 (resolve referenced works) batches unique referenced OpenAlex URLs in groups of 50
- Full OpenAlex URLs stripped to bare ID part (e.g. "W123456") for the Pass 2 filter query
- Cache JSON keyed on arXiv ID: `{arxiv_id: {"openalex_id": str, "referenced_openalex_ids": [str]}}`
- Cache written after EACH batch in Pass 1 (not after full pass) for crash-safe resume
- `requests_per_second` clamped to `min(rps, 9.0)` to enforce O-004 rate limit rule
- Jitter formula: `delay += random.uniform(0, 0.5) * delay` (i.e. up to 50% of computed delay)

**Validation results:** 6/6 PASS
- Batching (120 IDs → 3 Pass-1 calls): PASS
- 429 backoff (2 retries, increasing delay): PASS
- Retry-After header (sleep(5.0) called): PASS
- Max retries exceeded (batch skipped, no exception): PASS
- Edge filtering (only in-corpus edges): PASS
- Cache resume (cached IDs skipped in Pass 1): PASS

**Closed:** 2026-03-29

---

### E-011 · Download 10K arXiv papers and embed with local SPECTER2

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-04-12

**Description:**
Produce two artifacts for E-012: a 10K paper DataFrame and a SPECTER2 embedding array.

**Step 1 — Stream 10K papers via HuggingFace:**
```python
from datasets import load_dataset
ds = load_dataset("Cornell-University/arxiv", split="train", streaming=True)
```
Filter to papers where categories contains any of: cs.AI, cs.LG, cs.CL, cs.CV, stat.ML.
Stop after 10,000 papers. Save to `data/pipeline/arxiv_10k.parquet`.

Map fields to our schema: arxiv_id, title, abstract, categories (list), primary_category,
is_interdisciplinary, year, month.

**Step 2 — Embed with local SPECTER2:**
```python
from src.gcn_citation.pipeline.embedder import embed_papers
embeddings = embed_papers(
    papers=df,
    output_path=Path("data/pipeline/embeddings_10k.npy"),
    checkpoint_path=Path("data/pipeline/embeddings_10k_checkpoint.json"),
    api_key=None,
    device="mps",
    batch_size=32,
)
```
Set `PYTORCH_ENABLE_MPS_FALLBACK=1` and `KMP_DUPLICATE_LIB_OK=TRUE` before any torch import.
Expected time: ~60-90 seconds for 10K papers on M2 MPS.

**Step 3 — Validate:**
- parquet: 10K rows, correct columns
- npy: shape [10000, 768], dtype float32
- L2 norm of 5 random rows ≈ 1.0
- Print count of interdisciplinary papers
Write to `agents/engineer/workspace/validate_10k_data.py`. All checks PASS before closing.

**Environment:** Always activate `.venv` first: `source .venv/bin/activate`

**Blockers:** none

**Artifacts:**
- `data/pipeline/arxiv_10k.parquet`
- `data/pipeline/embeddings_10k.npy`
- `data/pipeline/embeddings_10k_checkpoint.json`
- `agents/engineer/workspace/download_and_embed_10k.py`
- `agents/engineer/workspace/validate_10k_data.py`

**Closed:** 2026-04-12

---

### E-012 · End-to-end 10K integration test

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-04-12

**Description:**
Assemble and validate the full Phase 0 pipeline on real 10K arXiv data.
Proves all five pipeline modules work together correctly end-to-end.

**Inputs:** data/pipeline/arxiv_10k.parquet, embeddings_10k.npy, citations from OpenAlex API

**Steps:**
1. Load parquet + mmap embeddings
2. `load_openalex_citations_api(arxiv_ids)` → CitationEdges
3. `assign_indices(edges, id_to_index)` → integer indices
4. `build_hetero_graph(papers, embeddings, citation_edges, knn_k=10)`
5. `validate_graph(graph)` → must return empty warnings list
6. `get_dataloaders(graph, train_mask, val_mask, test_mask)` → 70/15/15 split
7. Iterate one batch → verify valid HeteroData
8. Train 10-epoch GT on train split, run forward pass → verify logits shape

**Report:**
```
=== Phase 0 Integration Test: 10K arXiv ===
Papers:          10,000
Citation edges:  XXXX
k-NN edges:      XXXX
belongs_to:      XXXX
co_category:     XXXX
Graph valid:     PASS
GT forward:      PASS
ALL CHECKS PASSED
```

**Blockers:** E-010, E-011

**Artifacts:**
- `agents/engineer/workspace/integration_test_10k.py`

**Closed:** 2026-04-12

---

### E-013 · DuckDB schema for knowledge infrastructure (L1 + L2)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Create `src/knowledge/schema.py` — the DuckDB schema for the four-layer knowledge
infrastructure. Phase 1 needs L1 (chunks) and L2 (paper summaries) tables only.

**Tables to create:**

```sql
-- L1: raw chunks from papers
CREATE TABLE chunks (
    chunk_id       VARCHAR PRIMARY KEY,
    arxiv_id       VARCHAR NOT NULL,
    chunk_index    INTEGER NOT NULL,
    text           TEXT NOT NULL,
    char_start     INTEGER,
    char_end       INTEGER,
    embedding_row  INTEGER,  -- row index in embeddings_l1.npy
    created_at     TIMESTAMP DEFAULT NOW()
);

-- L2: paper-level summaries
CREATE TABLE paper_summaries (
    arxiv_id          VARCHAR PRIMARY KEY,
    title             TEXT,
    contribution      TEXT,
    method            TEXT,
    datasets          JSON,   -- list of strings
    key_findings      JSON,   -- list of strings
    limitations       TEXT,
    domain_tags       JSON,   -- list of strings
    related_methods   JSON,   -- list of strings
    extraction_model  VARCHAR,
    extracted_at      TIMESTAMP DEFAULT NOW()
);

-- L3: claim nodes (Phase 2 — create table now, populate later)
CREATE TABLE claims (
    claim_id         VARCHAR PRIMARY KEY,
    claim_type       VARCHAR,  -- empirical|theoretical|architectural|comparative|observation
    assertion        TEXT NOT NULL,
    domain           VARCHAR,
    method           VARCHAR,
    dataset          VARCHAR,
    metric           VARCHAR,
    value            VARCHAR,
    conditions       TEXT,
    epistemic_status VARCHAR DEFAULT 'preliminary',
    confidence       FLOAT DEFAULT 0.5,
    embedding_row    INTEGER,
    created_at       TIMESTAMP DEFAULT NOW(),
    last_updated     TIMESTAMP DEFAULT NOW()
);

-- L3: which papers support each claim
CREATE TABLE claim_sources (
    claim_id    VARCHAR REFERENCES claims(claim_id),
    arxiv_id    VARCHAR NOT NULL,
    excerpt     TEXT,
    PRIMARY KEY (claim_id, arxiv_id)
);

-- L3: typed edges between claims
CREATE TABLE claim_edges (
    edge_id      VARCHAR PRIMARY KEY,
    source_id    VARCHAR REFERENCES claims(claim_id),
    target_id    VARCHAR REFERENCES claims(claim_id),
    edge_type    VARCHAR,  -- supports|contradicts|extends|replicates_in_domain|requires|refines
    confidence   FLOAT DEFAULT 0.5,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

Also create `src/knowledge/__init__.py` and `src/knowledge/schema.py` with:
- `init_database(db_path: Path) -> duckdb.DuckDBPyConnection` — creates all tables
- `get_connection(db_path: Path) -> duckdb.DuckDBPyConnection` — returns connection

Validate with a small test: create the DB, insert one dummy paper summary, query it back.

**Artifacts:**
- `src/knowledge/__init__.py`
- `src/knowledge/schema.py`
- `agents/engineer/workspace/validate_schema.py`

**Blockers:** none

**Key implementation decisions:**
- All L3 tables (claims, claim_sources, claim_edges) are created now with CHECK constraints fully defined, even though Phase 1 only populates L1/L2. Schema is forward-compatible.
- `claim_sources` uses NO foreign key reference to `claims` (DuckDB FK enforcement is limited); referential integrity is enforced at application layer.
- `INSERT OR REPLACE INTO _meta` is used (DuckDB syntax) rather than SQL standard `INSERT OR REPLACE` — `ON CONFLICT DO UPDATE` also works but the former is more concise and matches DuckDB idioms.
- `get_connection` does not call `init_database` — callers must ensure the DB was already initialized. This keeps the two responsibilities separate.

**Validation results:** 8/8 PASS
- init_database_creates_6_tables: PASS — all 6 tables found
- init_database_idempotent: PASS — second call raised no error
- paper_summary_round_trip: PASS — all 10 fields verified
- claim_valid_type_round_trip: PASS — claim_type='empirical' accepted and retrieved
- invalid_claim_type_raises: PASS — ConstraintException raised as expected
- invalid_epistemic_status_raises: PASS — ConstraintException raised as expected
- invalid_edge_type_raises: PASS — ConstraintException raised as expected
- get_connection_works: PASS — paper_summaries=1, version='1.0.0'

**Closed:** 2026-03-29

---

### E-014 · L1 paper ingest pipeline

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Implement `src/knowledge/ingest.py` — takes arXiv papers from the existing
DataFrame and ingests them into L1 (chunks) in DuckDB.

For Phase 1, use **abstract-only** (not full PDF). The abstract is already in
`data/pipeline/arxiv_10k.parquet`. Full PDF extraction is a Phase 2+ concern.

**Chunking strategy for abstract-only:**
- Abstract is typically 150-250 words — treat as a single chunk
- chunk_id: f"{arxiv_id}_abstract"
- Embed using existing SPECTER2 embeddings from `data/pipeline/embeddings_10k.npy`
  (each paper already has one embedding = the abstract embedding)
- Store embedding_row = row index in the existing .npy file

**Implement:**
```python
def ingest_papers(
    papers: pd.DataFrame,           # arxiv_10k.parquet schema
    embeddings_path: Path,          # embeddings_10k.npy
    db_path: Path,
    *,
    batch_size: int = 100,
    skip_existing: bool = True,     # resume support
) -> dict[str, int]:                # {"ingested": N, "skipped": N, "errors": N}
```

**Validation:** ingest 50 papers, verify:
- chunk count = 50 (one per abstract)
- all arxiv_ids unique in chunks table
- embedding_row indices are valid (< len(embeddings))
- resume: run again, all 50 skipped

**Artifacts:**
- `src/knowledge/ingest.py` — full implementation
- `agents/engineer/workspace/validate_ingest.py` — validation script (8/8 PASS)

**Key implementation decisions:**
- `embedding_row` = DataFrame `iloc` index (same ordering as `embeddings_10k.npy`)
- `INSERT OR IGNORE` used so concurrent callers never raise an integrity error
- `skip_existing` pre-fetches all existing `chunk_id` values in one query and uses an in-memory set for O(1) per-row lookup — avoids N round-trips to SQLite
- `conn.commit()` called after every batch flush per O-005 rule
- Abstract null/NaN handled with `pd.notna()` guard, producing empty string (never None)
- Embeddings loaded with `mmap_mode="r"` to validate shape without fully loading 10K×768 floats into RAM

**Validation results:** 8/8 PASS
- ingested_50_papers: PASS — ingested=50
- chunks_count_50: PASS — got 50
- arxiv_ids_unique: PASS — unique=50
- chunk_id_pattern: PASS — bad patterns=0
- embedding_row_in_range: PASS — max_row=49, n_embeddings=10000
- no_null_text: PASS — nulls=0
- resume_skips_all: PASS — skipped=50, ingested=0
- count_unchanged_after_resume: PASS — got 50

**Blockers:** E-013

**Closed:** 2026-03-29

---

### E-015 · L2 extraction pipeline (Ollama local model)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Implement `src/knowledge/extract_l2.py` — uses local Ollama model to extract a
structured L2 paper summary for each paper and stores it in DuckDB.

**Model:** `qwen2.5-coder:7b` via Ollama (already installed, strong at structured JSON).
**API:** Ollama HTTP API at `http://localhost:11434` — no auth, no API key needed.

Uses the prompt designed and validated in R-003.

**Artifacts:**
- `src/knowledge/extract_l2.py` — full implementation
- `agents/engineer/workspace/validate_extract_l2.py` — validation script (7/7 PASS)

**Key implementation decisions:**
- `_validate_summary()` fills all missing fields with safe defaults before DB insert;
  also coerces list fields that the model occasionally returns as strings
- `extract_paper_summary()` retries once on `json.JSONDecodeError` by prepending an
  explicit JSON-only instruction (`_RETRY_PREFIX`) to the original prompt
- `extract_batch()` pre-fetches existing `arxiv_id` values in a single query for O(1)
  skip checks — avoids N round-trips per paper
- `conn.commit()` is called after EACH successful paper insert (Ollama is slow;
  commit-per-paper ensures partial progress is never lost on crash)
- `INSERT OR REPLACE` used so re-running with `skip_existing=False` is idempotent
- `timeout=90` (vs 60 in ticket stub) — first paper consistently takes 10-12s on cold
  model load; 90s gives headroom for heavy abstracts without hanging

**Validation results:** 7/7 PASS
- paper_summaries has exactly 10 rows: PASS
- all contribution fields non-empty: PASS
- all domain_tags parseable as JSON lists: PASS
- all key_findings have >= 1 item: PASS
- extraction_model == "qwen2.5-coder:7b" for all rows: PASS
- skip_existing=True: result["skipped"] == 10: PASS
- skip_existing=True: result["extracted"] == 0: PASS

**Performance:** 63.3s for 10 papers; avg 6.3s/paper (first paper ~11s cold load,
subsequent 4-7s warm). For 50 papers: ~5 min; 500 papers: ~52 min.

**Quality notes observed:**
- Model produces 2 findings (not 3) when abstract has only 2 distinct quantitative
  claims — correct behavior per R-003 (not hallucinating numbers)
- Domain tags plausible and specific across all 10 papers
- Contribution sentences accurate and one-sentence for all 10 papers

**Blockers:** E-013, R-003

**Closed:** 2026-03-29

---

### E-016 · Basic query interface (L1 + L2)

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-04-12

**Description:**
Implement `src/knowledge/query.py` — a simple query interface over L1 + L2.
No LLM at query time. Pure semantic search + DuckDB lookup.

```python
def search_papers(
    query: str,
    db_path: Path,
    embeddings_path: Path,
    *,
    top_k: int = 10,
    model_name: str = "allenai/specter2_base",
) -> list[dict]:
    """
    1. Embed the query using SPECTER2
    2. Cosine similarity against embeddings_l1.npy
    3. Return top_k papers with their L2 summaries from DuckDB
    """
```

Also implement a CLI entry point:
```bash
python -m src.knowledge.query "batch normalization in transformers"
```

Output format:
```
[1] arxiv:2208.02389 — Risk-Aware Linear Bandits...
    Contribution: ...
    Method: ...
    Key findings: ...
    Domain: [optimization, bandits]

[2] arxiv:2305.13936 — ...
```

**Validation:** run 5 queries, verify results are topically relevant.
Example queries to test:
- "attention mechanism improvements"
- "contrastive learning self-supervised"
- "batch normalization regularization"
- "graph neural network over-smoothing"
- "diffusion model image generation"

**Blockers:** E-014, E-015

**Closed:** 2026-04-12

---

### E-016 · Query interface (L1 + L2 semantic search)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Closed:** 2026-03-29

**Description:**
Implement `src/knowledge/query.py` — semantic search over L1 chunks + L2 summaries.
No LLM at query time. Pure cosine similarity + DuckDB lookup.

```python
def search_papers(
    query: str,
    db_path: Path,
    embeddings_path: Path,
    *,
    top_k: int = 10,
    model_name: str = "allenai/specter2_base",
    ollama_base_url: str = "http://localhost:11434",
) -> list[dict]:
    """
    1. Embed query using SPECTER2 (local MPS inference, one vector)
    2. Cosine similarity against embeddings_10k.npy (mmap)
    3. Look up top_k arxiv_ids in paper_summaries table
    4. Return list of dicts with: arxiv_id, title, contribution, method,
       key_findings, domain_tags, similarity_score
    """
```

Also implement a CLI:
```bash
python -m src.knowledge.query "batch normalization in transformers"
```

Output format (one paper per result):
```
[1] 0.923 — arxiv:2208.02389
    Contribution: ...
    Method: ...
    Key findings: ...
    Domain: [optimization, deep_learning]
```

Note: SPECTER2 embedding of the query uses the same MPS path as embedder.py.
Set PYTORCH_ENABLE_MPS_FALLBACK=1 and KMP_DUPLICATE_LIB_OK=TRUE.
Do NOT import faiss in this module (OpenMP conflict — see E-012 decisions).

Validation: run 5 test queries, verify results are topically relevant:
- "attention mechanism improvements"
- "contrastive learning self-supervised"
- "batch normalization regularization"
- "graph neural network over-smoothing"
- "diffusion model image generation"

**Blockers:** E-015

**Closed:** —

---

### E-017 · Filter corpus for quality papers

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-04-12

**Description:**
Before bulk extraction (E-018), filter the 10K paper corpus to a higher-quality
subset. R-003 found that thin/recent abstracts produce empty key_findings.

Implement `src/knowledge/filter_corpus.py`:

```python
def filter_quality_papers(
    papers: pd.DataFrame,
    *,
    min_abstract_words: int = 80,
    year_min: int = 2018,
    year_max: int = 2024,
    max_papers: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Filter and sample papers for high-quality L2 extraction.
    
    Criteria:
    - abstract word count >= min_abstract_words (filters thin abstracts)
    - year in [year_min, year_max] (avoids too-recent/too-old papers)
    - deduplicate by title (remove near-duplicates from versioned preprints)
    - sample max_papers from result, balanced across top categories
    """
```

Validate: from 10K papers, filtered set should have:
- 100% abstracts >= 80 words
- 100% year in [2018, 2024]
- No duplicate titles
- Balanced category distribution (no single category > 40%)

**Blockers:** none

**Closed:** 2026-04-12

---

### E-018 · Bulk L2 extraction run on 500 papers

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12

**Description:**
Run L2 extraction on the filtered 500-paper corpus. This is the "build the corpus"
step — without enough papers extracted, queries return too few results to be useful.

Script: `agents/engineer/workspace/run_bulk_extraction.py`

Steps:
1. Load arxiv_10k.parquet
2. Apply filter_quality_papers() → ~500 papers
3. Ingest to L1 first (ingest_papers)
4. Run extract_batch() for L2
5. Print progress and final count

Expected runtime: ~52 minutes at 6.3s/paper.
Checkpoint/resume: extract_batch already supports skip_existing=True.

Output DB: `data/knowledge/knowledge.db`

**Blockers:** E-015, E-017

**Closed:** 2026-04-12

---

### E-019 · Phase 1 end-to-end validation

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12

**Description:**
Prove Phase 1 works: fire 10 real queries against the populated DB and verify
results are meaningful.

Script: `agents/engineer/workspace/validate_phase1.py`

Test queries:
1. "batch normalization in deep networks"
2. "self-supervised contrastive learning"
3. "transformer attention mechanism"
4. "graph neural network message passing"
5. "diffusion probabilistic models"
6. "vision transformer image classification"
7. "reinforcement learning policy gradient"
8. "neural network optimization Adam SGD"
9. "knowledge distillation model compression"
10. "overparameterization generalization deep learning"

For each query:
- Run search_papers(), get top 5
- Print: query, top result arxiv_id + contribution + similarity score
- Check: top result similarity > 0.5 (sanity threshold)
- Check: top result domain_tags not empty

Phase 1 is DONE when: ≥ 8/10 queries return at least one topically relevant paper
in the top 3 results (manual review required — print results for human judgment).

**Blockers:** E-016, E-018

**Closed:** 2026-04-12

---

### E-020 · Implement L3 claim extraction pipeline (extract_l3.py)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Implement `src/knowledge/extract_l3.py` — the core of the knowledge
infrastructure. Extracts discrete claim nodes from L2 summaries and stores
them in the `claims` and `claim_sources` tables.

**Implement these functions:**

```python
def extract_claims_for_paper(
    arxiv_id: str,
    title: str,
    abstract: str,
    key_findings: list[str],
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> list[dict] | None:
    """Extract 1-5 claim dicts from a paper's L2 summary.
    Uses the prompt designed in R-005.
    Returns list of claim dicts or None on failure.
    """

def extract_claims_batch(
    db_path: Path,
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    skip_existing: bool = True,
    limit: int | None = None,    # for staged rollout
) -> dict[str, int]:   # {"papers_processed": N, "claims_extracted": N, "errors": N}
    """Extract claims for all papers in paper_summaries table.
    Reads from paper_summaries, writes to claims + claim_sources.
    """
```

Each claim gets a deterministic ID: `f"{arxiv_id}_{claim_index:02d}"`.
Use `json_dumps()` from schema.py — claims table stores TEXT not JSON.
Commit after each paper. Log: `[extract_l3] 1/500: 2208.02389 — 3 claims`.

**Use the prompt from R-005** (in agents/shared/findings.md [R-005]).

**Validation:** extract claims for 10 papers, verify:
- claims table has 10-50 rows (1-5 per paper)
- All claim_type values are valid enum values
- All assertion fields non-empty, no "this paper" / "we" references
- All claim_ids follow the pattern

**Blockers:** R-005 (need validated prompt), E-018 (need L2 summaries)

**Artifacts:**
- `src/knowledge/extract_l3.py` — full implementation
- `agents/engineer/workspace/validate_extract_l3.py` — validation script (10/10 PASS)

**Key implementation decisions:**
- Handles both bare array `[{...}]` and dict-wrapped `{"claims": [...]}` responses
- `claim_type` clamped to valid enum; defaults to "empirical" if invalid
- First-person prefixes ("This paper", "we ", "our ") stripped from assertions
- Deterministic `claim_id`: `f"{arxiv_id}_{index:02d}"` (e.g. `2208.02389_00`)
- `skip_existing` uses pre-fetched in-memory set (suffix-based arxiv_id extraction)
- Retries once with explicit JSON-array instruction on parse failure
- Commits after each paper; errors never block subsequent papers

**Validation results:** 10/10 checks PASS
- papers_processed: 10/10, errors: 0
- Avg claims/paper: 1.00 (model returns 1 claim — known R-005 behavior; prompt includes
  "extract exactly 3 if possible" instruction as required by ticket)
- All claim_type values valid (mix of empirical/theoretical)
- All assertions non-empty, no first-person prefixes
- All claim_ids match `{arxiv_id}_NN` pattern
- claim_sources: 1 row per claim, no orphans
- Resume (skip_existing=True): 0 new claims on second run

**Closed:** 2026-03-29

---

### E-021 · Build L3 typed edges between claims

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-04-12

**Description:**
Implement `src/knowledge/edge_classifier.py` — takes pairs of claim nodes and
classifies the relationship between them as one of:
supports | contradicts | extends | refines | replicates_in_domain | requires

**Two-phase approach:**

**Phase A — candidate generation (embedding similarity)**
```python
def find_candidate_pairs(
    db_path: Path,
    embeddings_path: Path,   # L3 claim embeddings (to be built)
    *,
    similarity_threshold: float = 0.75,
    max_pairs: int = 1000,
) -> list[tuple[str, str, float]]:
    """Return (claim_id_a, claim_id_b, similarity) pairs above threshold.
    Only pairs from DIFFERENT papers — same-paper pairs are trivially related.
    """
```

For now, use SPECTER2 paper-level embeddings as proxy for claim embeddings
(same paper → similar claim embeddings). In Phase 4, train dedicated claim
embeddings.

**Phase B — edge classification (Ollama)**
```python
def classify_edge(
    claim_a: str,    # assertion text
    claim_b: str,    # assertion text
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
) -> str | None:
    """Classify relationship between two claims.
    Returns one of the 6 edge types, or None if unrelated.
    
    Prompt: given claim A and claim B from AI/ML papers, classify their
    relationship. Return JSON: {"relationship": "supports|contradicts|...|none"}
    """
```

**Important for `replicates_in_domain`:**
This edge type is the cross-disciplinary connection — Goal 1 of the research.
Classify as `replicates_in_domain` when the same idea appears in two different
domain_tags (e.g. claim from NLP paper and CV paper assert structurally
identical ideas with different vocabulary).

**Validation:** classify 10 known pairs including:
- 2 pairs you know support each other
- 1 pair that contradicts
- 1 cross-domain pair (NLP ↔ CV, same architectural idea)
Verify edge_type assignments are sensible.

**Blockers:** E-020 (need claims in DB), R-005 (need validated classification prompt)

**Closed:** —

---

### E-022 · L2-derived relational edges (shares_method, co_domain)

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Mine `related_methods` and `domain_tags` from L2 summaries to create two new
edge types in the claim graph — without requiring additional Ollama inference.

**New edge types to add to claim_edges:**

| Edge type | Definition | Source |
|---|---|---|
| `shares_method` | Two papers both list the same method in `related_methods` | L2 summaries |
| `co_domain` | Two papers share ≥1 domain_tag and the shared tag is specific (not generic like "deep_learning") | L2 summaries |

**Implement `src/knowledge/derive_edges.py`:**

```python
def build_method_edges(
    db_path: Path,
    *,
    min_papers_per_method: int = 2,   # ignore methods mentioned only once
    max_pairs_per_method: int = 50,   # cap to avoid cs.LG explosion
) -> int:   # number of edges inserted

def build_domain_edges(
    db_path: Path,
    *,
    exclude_generic: set[str] | None = None,   # tags too broad to be useful
    max_pairs_per_domain: int = 50,
) -> int:
```

Generic domain tags to exclude (too broad): `{"deep_learning", "machine_learning",
"neural_network", "AI", "artificial_intelligence"}` — these connect everything to
everything.

Specific domain tags worth keeping: `{"transformers", "BERT", "ResNet", "GAN",
"diffusion", "LSTM", "attention", "reinforcement_learning", "graph_neural_network"}`

These edges go into the existing `claim_edges` table using paper-level IDs
(before L3 is fully built, edges connect paper nodes not claim nodes).

**Validation:** after building edges on 500-paper corpus:
- Report how many `shares_method` edges were created
- Report top 5 methods by edge count
- Report top 5 domain tags by edge count
- Spot-check 3 method edges: are the two papers actually methodologically related?

**Blockers:** E-018 (need 500 L2 summaries)

**Closed:** 2026-03-29

**Key findings (296 papers with related_methods, 353 with domain_tags):**
- shares_method: 15 edges from 13 distinct methods
- co_domain: 306 edges from 55 distinct tags (321 total in paper_edges)
- Top methods: diffusion models (3 edges), transformers (1), pinns (1)
- Top domain tags: transformers (50 capped), optimization (50 capped), language_modeling (50 capped)
- Spot-check confirmed: CLIP, curriculum learning, and diffusion model paper pairs are methodologically related
- paper_edges uses new dedicated table (not claim_edges) due to SQLite CHECK constraint limitations

---

### E-023 · Semantic Scholar citation edges once API key arrives

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-04-12

**Description:**
Once the Semantic Scholar API key is approved (still pending) and R-006 confirms
coverage, implement real citation edge fetching to replace the 0-edge OpenAlex
result for preprints.

**What to implement in `src/knowledge/citations_s2.py`:**

```python
def fetch_s2_citations(
    arxiv_ids: list[str],
    db_path: Path,
    *,
    api_key: str,         # from SEMANTIC_SCHOLAR_API_KEY env var
    requests_per_second: float = 0.9,
    cache_path: Path | None = None,
) -> dict[str, int]:   # {"fetched": N, "citation_edges": N, "errors": N}
```

For each paper:
- `GET /graph/v1/paper/ArXiv:{id}?fields=references`
- For each reference that has an arXiv ID: check if it's in our 500-paper corpus
- If both source and target are in corpus: insert `cites` edge into `claim_edges`

Rate limiting per O-004 in agents/shared/decisions.md (backoff, jitter, Retry-After).
Store API key in environment variable only — never hardcode.

**Expected outcome per R-006 research:**
Semantic Scholar extracts references from PDF text, so preprints WILL have data.
Expected: significantly more citation edges than the 0 from OpenAlex.

**Blockers:** R-006 (coverage research), Semantic Scholar API key (external)

**Closed:** —

---

### E-024 · Hybrid BM25/FTS5 + embedding re-ranking in query.py

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-03-29

**Description:**
Replace the pure embedding search in `src/knowledge/query.py` with a hybrid
retrieval that combines SQLite FTS5 text search (high precision for keywords)
with embedding re-ranking (semantic broadening).

**What to build:**

**Step 1: FTS5 index** (add to `schema.py`):
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    arxiv_id UNINDEXED,
    text,                -- contribution + ' ' + key_findings joined
    content='paper_summaries',
    tokenize='porter ascii'
);
```
Populate by: `INSERT INTO search_index SELECT arxiv_id, contribution || ' ' || key_findings FROM paper_summaries`

Add `build_search_index(db_path)` function to `src/knowledge/ingest.py` that creates and populates the FTS5 index.

**Step 2: Update search_papers() in query.py:**
```python
def search_papers(
    query: str,
    db_path: Path,
    embeddings_path: Path,
    *,
    top_k: int = 10,
    text_weight: float = 0.6,    # weight for BM25 score
    embed_weight: float = 0.4,   # weight for cosine similarity
    model_name: str = "allenai/specter2_base",
    device: str = "mps",
) -> list[dict]:
```

Algorithm:
1. FTS5 text search → top 50 candidates with BM25 scores
2. Embed query → cosine search over those 50 candidates only
3. Hybrid score = text_weight × normalized_bm25 + embed_weight × cosine_score
4. Re-rank and return top_k

If FTS5 returns 0 results (query too specific): fall back to pure embedding.

**Validation:** run the 10 Phase 1 queries, verify:
- "batch normalization" now returns papers mentioning batch normalization
- "graph neural network" returns papers mentioning GNNs
- "diffusion" returns diffusion model papers
- All 10 queries return topically relevant top-1 result

**Blockers:** R-008 (for optimal text_weight / embed_weight values)
Can implement with default weights before R-008 closes.

**Artifacts:**
- `src/knowledge/schema.py` — added `_DDL_SEARCH_INDEX` (FTS5 virtual table) and appended to `_ALL_DDL`
- `src/knowledge/ingest.py` — added `build_search_index(db_path)` function
- `src/knowledge/query.py` — replaced `search_papers()` with hybrid FTS5 + embedding re-ranking; new params `text_weight` / `embed_weight`; fallback to pure embedding on FTS5 miss
- `agents/engineer/workspace/validate_hybrid_query.py` — validation script

**Closed:** 2026-03-29

---

### E-025 · Re-embed corpus with best model from R-007

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-12

**Description:**
Replace `data/pipeline/embeddings_10k.npy` with embeddings from the model
recommended in R-007. This makes semantic search over ideas and concepts work
correctly.

**What to update:**
- `src/gcn_citation/pipeline/embedder.py` — add support for the new model
- Re-run embedding for the 10K corpus
- Update `data/pipeline/embeddings_10k.npy` and checkpoint
- Re-run `build_method_edges` (similarity edges will change with new embeddings)

**Also embed L3 claims** (when available):
- Create `data/knowledge/embeddings_claims.npy` — one vector per claim assertion
- Claim assertions are short sentences (50-150 tokens) — verify new model handles these well
- Update `query.py` to optionally search over claim embeddings

**Blockers:** R-007 (must know which model to use)

**Closed:** —

---

### E-026 · L3 claim embedding index for idea-level search

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-04-12

**Description:**
Once L3 claims are extracted (E-020 batch run) and the embedding model is chosen
(R-007), build a dedicated embedding index over claim assertions.

This is the "ideas as nodes" layer — claims are the atomic units the vision
document describes, and they need to be semantically searchable.

**What to build:**
- `src/knowledge/embed_claims.py`:
  ```python
  def embed_claims(
      db_path: Path,
      output_path: Path,  # data/knowledge/embeddings_claims.npy
      *,
      model_name: str,   # from R-007 recommendation
      device: str = "mps",
      batch_size: int = 64,
  ) -> np.ndarray:
      """Embed all claim assertions in the claims table.
      Returns [N_claims, D] array aligned with claim_id order.
      """
  ```
- Add `search_claims()` to `query.py`:
  ```python
  def search_claims(
      query: str,
      db_path: Path,
      claims_embeddings_path: Path,
      *,
      top_k: int = 10,
  ) -> list[dict]:
      """Search claim nodes by concept.
      Returns claims with: claim_id, assertion, claim_type, domain,
      source_arxiv_ids, similarity_score
      """
  ```

**Why this matters:** searching claims instead of papers gives you answers at
the idea level. "batch normalization" → returns the specific claim "Batch
normalization stabilizes training by normalizing layer inputs" with its source
papers — not just "here are papers that mention batch normalization."

**Blockers:** E-020 (bulk L3 extraction), R-007 (embedding model choice)

**Closed:** —
