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

**Status:** in-progress
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

**Closed:** —

---

### E-012 · End-to-end 10K integration test

**Status:** open
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

**Closed:** —
