# Phase 0 Implementation Plan: 10K-Paper Heterogeneous Graph Pipeline

**Date**: 2026-03-29
**Target**: End-to-end pipeline delivering a 10K-paper heterogeneous PyG graph with SPECTER2 embeddings
**Timeframe**: 2-3 weekends
**Prerequisite reading**: `docs/research/requirements.md`, `docs/plans/gt.md`

---

## Overview

Phase 0 delivers the foundational data infrastructure that every subsequent phase depends on. The goal is a working, validated pipeline that takes raw arXiv metadata as input and produces a PyTorch Geometric `HeteroData` graph as output — with SPECTER2 embeddings as node features, citation edges from S2ORC, and k-NN semantic similarity edges computed via FAISS.

### What Phase 0 Delivers

- A streaming arXiv metadata parser that filters and samples 10K papers from the bulk S3 snapshot without loading the full 3.5GB JSON into memory
- SPECTER2 embeddings for all 10K papers, computed on MPS with checkpointing so the job can be resumed across sessions
- A citation edge list sourced from S2ORC, aligned to arXiv IDs, stored as a flat edge list
- A PyG `HeteroData` graph with four node/edge types: `Paper`, `Category`, `cites`, `similar_to`, `belongs_to`, `co_category`
- A mini-batch neighbor sampler wired up and smoke-tested for training
- A cross-disciplinary ground truth evaluation baseline: SPECTER2 cosine similarity scores on the manually curated pairs in `data/ground_truth/cross_disciplinary_pairs.json`

### Definition of Done

The phase is complete when all of the following are true:

1. `python pipeline/arxiv_bulk.py --output data/phase0/papers.jsonl --limit 10000` completes successfully and produces exactly 10,000 deduplicated paper records
2. `python pipeline/embedder.py --input data/phase0/papers.jsonl --output data/phase0/embeddings.npy` completes with shape `[10000, 768]` and a matching `embeddings_index.json`
3. `python pipeline/graph_builder.py --papers data/phase0/papers.jsonl --embeddings data/phase0/embeddings.npy --citations data/phase0/citations.jsonl --output data/phase0/graph.pt` completes and `torch.load("data/phase0/graph.pt")` returns a valid `HeteroData` object with all four edge types populated
4. A single 2-hop mini-batch passes through the Graph Transformer without error
5. SPECTER2 cosine similarity scores are computed and logged for all pairs in `data/ground_truth/cross_disciplinary_pairs.json` — this is the baseline to beat in later phases

---

## Module Breakdown

---

### Module 1: `pipeline/arxiv_bulk.py`

#### What it does

Streams and parses the arXiv bulk metadata snapshot (`arxiv-metadata-oai-snapshot.json`), filtering records by category and date range, then writes qualifying paper records to a newline-delimited JSON file. The snapshot is ~3.5GB and contains 2M+ papers. This module must never load the entire file into memory.

The module is also responsible for producing a balanced, representative 10K sample: it should include papers from multiple target categories and explicitly oversample papers with 2+ primary categories (interdisciplinary papers), since Goal 2 of the research depends on having enough of them.

#### Inputs

- `--snapshot`: path to `arxiv-metadata-oai-snapshot.json` (the arXiv bulk S3 file, downloaded separately)
- `--categories`: comma-separated list of target arXiv categories (e.g. `cs.LG,cs.AI,cs.CL,cs.CV,stat.ML,math.OC,cond-mat.stat-mech,quant-ph`)
- `--date-from`: ISO date string for earliest submission date (e.g. `2010-01-01`)
- `--date-to`: ISO date string for latest submission date (e.g. `2024-12-31`)
- `--limit`: maximum number of output records (default: 10000)
- `--output`: path to output `.jsonl` file
- `--interdisciplinary-oversample`: float in [0, 1], fraction of the limit to reserve for papers with 2+ categories (default: 0.2)
- `--seed`: random seed for reproducible sampling (default: 42)

#### Outputs

- `{output}.jsonl`: newline-delimited JSON, one record per line, each record containing:
  ```json
  {
    "arxiv_id": "2006.11239",
    "title": "...",
    "abstract": "...",
    "submitted": "2020-06-19",
    "primary_category": "cs.CV",
    "all_categories": ["cs.CV", "cs.LG"],
    "is_interdisciplinary": true,
    "num_categories": 2
  }
  ```
- `{output}_manifest.json`: summary statistics — total scanned, total matching filter, sampled count, per-category counts, interdisciplinary count, date range

#### Key Design Decisions

- **Streaming parse**: use `ijson` for incremental JSON parsing, or fall back to line-by-line iteration if the snapshot is actually one-JSON-object-per-line (the arXiv snapshot format). Check the first 5 lines of the file before writing the parser to confirm the format.
- **Two-pass sampling**: first pass collects candidate IDs and category information without storing full text; second pass writes full records for the selected IDs. This keeps peak memory bounded to the index structure (~100 bytes per paper × 2M papers ≈ 200MB), not the full text.
- **Interdisciplinary oversampling**: after filling the regular quota, top up with additional papers that have 2+ primary categories from the target set, up to `interdisciplinary_oversample × limit` slots. This ensures Goal 2 experiments have enough boundary cases.
- **Reproducibility**: sampling uses a seeded RNG. The manifest records the seed. The same seed always produces the same 10K.
- **No arXiv API**: this module reads the local bulk snapshot only. The existing `arxiv_data.py` (which uses the arXiv API) is kept for small experiments but is not used in the new pipeline.
- **Category matching rule**: a paper qualifies if its `primary_category` is in the target set, OR if any category in `all_categories` is in the target set and that category is listed first. This matches arXiv's own convention.

#### How it connects to the next module

The output `.jsonl` is the sole input to `pipeline/embedder.py`. Each line contains `arxiv_id`, `title`, and `abstract` — exactly what SPECTER2 needs. The `arxiv_id` becomes the primary key used to align embeddings, citations, and graph indices across all subsequent modules.

---

### Module 2: `pipeline/embedder.py`

#### What it does

Reads the paper records from `arxiv_bulk.py`, constructs the SPECTER2 input string (`title + " [SEP] " + abstract`, truncated to 512 tokens), runs inference in batches on MPS, and writes embeddings to a memory-mapped `.npy` file. Supports checkpoint/resume: if a run is interrupted, it picks up from the last completed arXiv ID without re-embedding already-processed papers.

#### Inputs

- `--input`: path to `.jsonl` file from `arxiv_bulk.py`
- `--output`: path to output `.npy` embedding file (shape `[N, 768]`, float32)
- `--index-output`: path to output index JSON file (maps `arxiv_id` → row index in the `.npy`)
- `--checkpoint`: path to checkpoint file for resume (default: `{output}.checkpoint.json`)
- `--batch-size`: number of papers per MPS batch (default: 32; tune based on memory)
- `--model-name`: HuggingFace model ID (default: `allenai/specter2`)
- `--device`: compute device (default: `mps`; fallback: `cpu`)

#### Outputs

- `{output}.npy`: float32 array of shape `[N, 768]`, memory-mapped during training. Written incrementally: the file is pre-allocated at the start using `np.memmap` in write mode, then filled row-by-row as batches complete.
- `{output}_index.json`: ordered mapping from `arxiv_id` to integer row index:
  ```json
  {
    "version": 1,
    "model": "allenai/specter2",
    "num_papers": 10000,
    "embedding_dim": 768,
    "arxiv_id_to_row": {
      "2006.11239": 0,
      "1706.03762": 1,
      ...
    }
  }
  ```
- `{output}.checkpoint.json`: list of `arxiv_id`s already processed; updated after each batch completes. On resume, rows already in the checkpoint are skipped and their pre-existing `.npy` rows are preserved.

#### Key Design Decisions

- **Memory-mapped output**: pre-allocate the full `[N, 768]` `.npy` at the start using `np.memmap(path, dtype='float32', mode='w+', shape=(N, 768))`. Write rows in-place as batches complete. This avoids accumulating all embeddings in RAM before writing.
- **Checkpoint granularity**: checkpoint after every batch (every 32 papers). On a 10K run, this means ~313 checkpoint saves. Each save is a small JSON write — negligible overhead.
- **Resume logic**: on startup, read the checkpoint file (if it exists), skip all `arxiv_id`s already in it, but keep their rows in the `.npy` intact. The index file is only written at the end when all papers are processed, so it can serve as a completion signal.
- **SPECTER2 tokenization**: use the `AutoTokenizer` from HuggingFace with `padding=True`, `truncation=True`, `max_length=512`, `return_tensors='pt'`. Move input tensors to the target device before inference.
- **L2 normalization**: after embedding, L2-normalize each vector in-place before writing to the `.npy`. This is required for FAISS `IndexFlatIP` (cosine similarity) in `graph_builder.py`. Store a flag in the index JSON: `"l2_normalized": true`.
- **No gradient computation**: wrap inference in `torch.no_grad()`. On MPS, also disable `torch.autocast` unless needed — test whether it helps throughput.
- **Batch size tuning**: 32 papers at 512 tokens each is the safe default. If MPS memory allows, 64 roughly doubles throughput. Add a `--batch-size` flag; the checkpoint means a failed run at batch size 64 can be resumed at batch size 32 without losing work.

#### Estimated runtime

At ~11 minutes for 100K papers on M2 MPS (from the requirements doc), 10K should take approximately 1 minute. The first run includes model download time (~1GB).

#### How it connects to the next module

The `.npy` file and `_index.json` are passed directly to `graph_builder.py`. The index maps arXiv IDs to row positions, which the graph builder uses to look up embedding vectors when constructing node features and when running FAISS for k-NN edges.

---

### Module 3: `pipeline/citations.py`

#### What it does

Loads citation data from S2ORC (Semantic Scholar Open Research Corpus), resolves both endpoints to arXiv IDs, filters to the working paper set, deduplicates, and writes a flat edge list. S2ORC bulk data is distributed as gzipped JSONL shards; this module processes them shard by shard without loading all shards into memory simultaneously.

**License note**: before building the full pipeline on S2ORC, verify the license terms for personal research use. If S2ORC is unavailable, this module falls back to the Semantic Scholar API (`api.semanticscholar.org/graph/v1`) for the working paper set only — slower, but rate-limit-safe for 10K papers.

#### Inputs

- `--papers`: path to `.jsonl` file from `arxiv_bulk.py` (provides the target arXiv ID set)
- `--s2orc-dir`: directory containing S2ORC gzipped JSONL shards (e.g. `data/s2orc/`)
- `--output`: path to output citation edge list (`.jsonl`)
- `--api-fallback`: flag to use Semantic Scholar API instead of S2ORC bulk (for testing or if S2ORC unavailable)
- `--api-key`: Semantic Scholar API key (optional, increases rate limit)

#### Outputs

- `{output}.jsonl`: newline-delimited JSON, one directed citation edge per line:
  ```json
  {"src": "1706.03762", "dst": "1409.1556", "source": "s2orc"}
  ```
  Only edges where both `src` and `dst` are in the working paper set are included.
- `{output}_stats.json`: edge count, coverage (fraction of working papers with at least one citation edge), in-degree and out-degree distributions

#### Key Design Decisions

- **S2ORC shard processing**: iterate over shards one at a time. For each paper record in a shard, check if the S2ORC `externalIds.ArXiv` field maps to a paper in the working set. If so, iterate over its `outboundCitations` and `inboundCitations` fields, resolving each to an arXiv ID when available. Write qualifying edges immediately; do not buffer shard-level results.
- **ID alignment**: S2ORC uses its own `corpusId` as primary key. The `externalIds` field contains optional arXiv, DOI, PubMed, etc. IDs. Use `externalIds.ArXiv` for alignment; strip any `arxiv:` prefix or URL prefix to get the bare arXiv ID (e.g. `2006.11239`).
- **Deduplication**: use a `set` of `(src, dst)` tuples to deduplicate while writing. Since edge lists can be large, flush to disk every 100K edges and reset the dedup set — tolerate rare duplicates rather than holding the full set in memory.
- **API fallback mode**: if `--api-fallback` is set, query the Semantic Scholar API in batches of 500 paper IDs using the `/paper/batch` endpoint with `fields=references`. Rate limit: respect the 1 req/sec unauthenticated limit. Cache responses per paper ID in `data/phase0/s2_api_cache/` so reruns are cheap.
- **Directed storage**: store edges as directed (`src` cites `dst`). The graph builder decides how to interpret direction per edge type.

#### How it connects to the next module

The `.jsonl` citation edge list is consumed by `graph_builder.py`, which loads it, converts arXiv IDs to integer node indices, and adds it as the `('paper', 'cites', 'paper')` edge type in the `HeteroData` object.

---

### Module 4: `pipeline/graph_builder.py`

#### What it does

Assembles all pipeline outputs into a single PyTorch Geometric `HeteroData` graph. This is the integration point: it reads papers, embeddings, and citations; builds the k-NN similarity graph using FAISS; constructs category nodes and edges; flags interdisciplinary papers; and serializes the result to a `.pt` file.

#### Inputs

- `--papers`: path to `.jsonl` from `arxiv_bulk.py`
- `--embeddings`: path to `.npy` embedding file from `embedder.py`
- `--embedding-index`: path to `_index.json` from `embedder.py`
- `--citations`: path to `.jsonl` citation edge list from `citations.py`
- `--output`: path to output `.pt` file (PyG `HeteroData`)
- `--knn-k`: number of nearest neighbors for `similar_to` edges (default: 10)
- `--knn-batch-size`: FAISS batch size (default: 1000; FAISS runs on CPU)
- `--skip-co-category`: flag to omit `co_category` edges (saves construction time; can add later)

#### Outputs

- `{output}.pt`: PyTorch Geometric `HeteroData` object containing:
  - `data['paper'].x`: float32 tensor of shape `[N_papers, 768]` — SPECTER2 embeddings
  - `data['paper'].arxiv_id`: list of arXiv IDs, index-aligned with `x`
  - `data['paper'].primary_category`: list of primary category strings
  - `data['paper'].all_categories`: list of lists — all category tags per paper
  - `data['paper'].is_interdisciplinary`: bool tensor, True if 2+ primary categories
  - `data['paper'].num_categories`: int tensor, count of primary categories
  - `data['category'].name`: list of category strings (one node per unique category)
  - `data['paper', 'cites', 'paper'].edge_index`: COO tensor, shape `[2, E_cite]`
  - `data['paper', 'similar_to', 'paper'].edge_index`: COO tensor, shape `[2, E_sim]`
  - `data['paper', 'belongs_to', 'category'].edge_index`: COO tensor, shape `[2, E_belongs]`
  - `data['paper', 'co_category', 'paper'].edge_index`: COO tensor, shape `[2, E_cocat]` (omitted if `--skip-co-category`)
- `{output}_stats.json`: node counts, edge counts per type, degree distributions, fraction of interdisciplinary papers, FAISS construction time

#### Key Design Decisions

- **Paper node ordering**: establish a canonical `arxiv_id → node_index` mapping at the start by iterating the `.jsonl` in order. All subsequent index lookups (embeddings, citations, category edges) use this mapping.
- **Embedding loading**: load the `.npy` as a read-only `np.memmap`, then convert only the rows needed for the working paper set to a `torch.FloatTensor`. Since phase 0 is 10K papers, a full in-memory load is fine; at 100K, the memmap avoids a 300MB RAM spike.
- **FAISS k-NN**: use `faiss.IndexFlatIP` (inner product on L2-normalized vectors = cosine similarity). Add all paper embedding vectors; then query in batches of `--knn-batch-size` to avoid constructing a full N×N matrix. Store results as COO (source, destination) pairs, making each undirected pair bidirectional (add both `(i, j)` and `(j, i)`).
- **Category nodes**: collect all unique category strings from `all_categories` across all papers. Assign integer indices. Build `belongs_to` edges from each paper to each of its categories. Mark the "primary" category with an edge attribute if needed for ablations.
- **`co_category` edges**: two papers share a `co_category` edge if they share at least one category in `all_categories`. Compute via an inverted index: category → list of paper node indices. For each category, add all pairs. Deduplicate. This can be slow for large categories (e.g. `cs.LG`); cap at a per-category limit (e.g. 500 pairs) to avoid quadratic blowup at 100K scale.
- **Interdisciplinary flag**: `is_interdisciplinary` is True if `num_categories >= 2`, where `num_categories` counts only categories in the target set (not cross-listed to unrelated fields like `physics.bio-ph`).
- **Edge index format**: all edge indices are `torch.long` tensors in COO format `[2, E]`, compatible with PyG's standard. Use `torch.tensor(np.array(edge_list).T, dtype=torch.long)`.
- **Validation before write**: before serializing, run the sanity checks listed in the Validation Checklist below. If any check fails, raise a `ValueError` with a descriptive message rather than writing a corrupt graph.

#### How it connects to the next module

The `.pt` graph is loaded directly by `pipeline/sampling.py` and by all training scripts. It is the single source of truth for the graph structure during Phase 0 and Phase 1.

---

### Module 5: `pipeline/sampling.py`

#### What it does

Wraps the Phase 0 graph in a PyG mini-batch neighbor sampler for training. Implements a GraphSAGE-style 2-hop neighborhood sampler with configurable fanouts, edge type masking (to support training on subsets of edge types), and split masking. Provides a `get_dataloaders()` function that returns train, val, and test `NeighborLoader` instances ready for use in a training loop.

#### Inputs

- `graph`: a `HeteroData` object loaded from `graph_builder.py` output
- `edge_types`: list of edge type tuples to include in sampling (e.g. `[('paper', 'cites', 'paper'), ('paper', 'similar_to', 'paper')]`)
- `fanouts`: list of neighbor counts per hop (default: `[10, 5]`, 2-hop)
- `batch_size`: number of seed nodes per mini-batch (default: 256)
- `num_workers`: DataLoader workers (default: 0 on MPS to avoid multiprocessing issues)
- `train_mask`, `val_mask`, `test_mask`: boolean index tensors over paper nodes

#### Outputs

This module exports a function, not a standalone script:

```python
# pipeline/sampling.py
def get_dataloaders(
    graph: HeteroData,
    edge_types: list[tuple[str, str, str]],
    fanouts: list[int],
    batch_size: int = 256,
    num_workers: int = 0,
    seed: int = 42,
) -> tuple[NeighborLoader, NeighborLoader, NeighborLoader]:
    ...
```

Returns `(train_loader, val_loader, test_loader)`.

During training, each batch from the loader is a `HeteroData` subgraph containing:
- The seed paper nodes (batch nodes)
- Their multi-hop neighborhoods sampled according to `fanouts`
- All edge indices within the subgraph
- A `batch_size` attribute on the seed node type for loss masking

#### Key Design Decisions

- **PyG `NeighborLoader`**: use `torch_geometric.loader.NeighborLoader` with `num_neighbors` specified per edge type as a dict, e.g.:
  ```python
  num_neighbors = {
      ('paper', 'cites', 'paper'): [10, 5],
      ('paper', 'similar_to', 'paper'): [10, 5],
  }
  ```
  This is the standard PyG API for heterogeneous mini-batch sampling.
- **Edge type masking for ablations**: the `edge_types` parameter controls which edge types are included in neighborhood sampling. This directly supports Goal 3 experiments (edge type sensitivity). Excluded edge types are simply not passed to `NeighborLoader`.
- **`num_workers=0` on MPS**: PyG's `NeighborLoader` with `num_workers > 0` uses multiprocessing. On macOS MPS, this can cause CUDA context issues or memory sharing errors. Default to 0 for safety; allow override.
- **Split masks**: use `input_nodes=('paper', train_mask)` to restrict seed node selection to training nodes. The sampler still expands neighborhoods into the full graph (including val/test nodes as context), which is the standard inductive setting.
- **Fanout defaults**: `[10, 5]` means sample 10 neighbors in hop 1 and 5 neighbors in hop 2. This gives batches of ~500–1000 nodes at 10K scale, fitting comfortably in MPS memory. At 100K scale, consider reducing to `[5, 3]`.

#### How it connects to the next module

`get_dataloaders()` is called at the start of every training script. The training loop iterates over `train_loader`, moves each batch to MPS, runs the forward pass, computes loss, and backpropagates. The val and test loaders are used for evaluation at the end of each epoch.

---

## Validation Checklist

### Module 1 (`arxiv_bulk.py`)

1. `len(records) == limit` — output has exactly the requested number of records
2. No duplicate `arxiv_id` values in the output (check with a set)
3. All records have `primary_category` in the requested category set
4. `interdisciplinary_fraction >= interdisciplinary_oversample - 0.02` — oversampling worked
5. `manifest.json` date range matches `--date-from` and `--date-to` arguments

### Module 2 (`embedder.py`)

1. `embeddings.shape == (N, 768)` where N equals the number of records in the input `.jsonl`
2. `len(index['arxiv_id_to_row']) == N` — index covers all papers
3. `np.linalg.norm(embeddings[i]) ≈ 1.0` for several random rows (L2 normalization check)
4. No all-zero rows in the embedding matrix (indicates a failed inference call)
5. Resume test: interrupt after 5 batches, restart, verify final output is identical to a full run

### Module 3 (`citations.py`)

1. All `src` and `dst` arXiv IDs in the output are in the working paper set
2. No self-loops (`src != dst` for all edges)
3. Edge count is in the expected range: 10K papers with ~200K total citation edges is plausible; fewer than 1K or more than 2M suggests a parsing bug
4. Coverage stat: at least 30% of papers have at least one citation edge (if lower, check ID alignment)
5. Directed edges only: for any `(src, dst)` pair, the reverse `(dst, src)` should not be present unless separately cited

### Module 4 (`graph_builder.py`)

1. `data['paper'].x.shape == (10000, 768)` and no NaN or Inf values
2. `data['paper', 'cites', 'paper'].edge_index.max() < 10000` — no out-of-bounds indices
3. `data['paper', 'similar_to', 'paper'].edge_index.shape[1] ≈ 10000 * 10 * 2` — approximately 2×k edges per paper (bidirectional)
4. `data['paper'].is_interdisciplinary.sum() >= 200` at 10K scale with 20% oversampling target
5. `data.validate()` returns True (PyG's built-in HeteroData validation)

### Module 5 (`sampling.py`)

1. First batch from `train_loader` has `batch['paper'].x.shape[1] == 768`
2. `batch['paper'].batch_size <= 256` (seed nodes fit in batch)
3. Total nodes in a 2-hop batch is in range `[256, 5000]` — not exploding
4. Running one full epoch over `train_loader` covers all training node indices at least once
5. No CUDA/MPS device mismatch errors when running a forward pass on the batch

---

## Integration Test

Before scaling to 10K, run a single end-to-end test on 1K papers to validate the full pipeline. This test should complete in under 5 minutes.

### Setup

```bash
# Step 1: sample 1K papers
python pipeline/arxiv_bulk.py \
  --snapshot data/arxiv-metadata-oai-snapshot.json \
  --categories cs.LG,cs.AI,stat.ML,cond-mat.stat-mech \
  --limit 1000 \
  --output data/integration_test/papers.jsonl \
  --interdisciplinary-oversample 0.2 \
  --seed 42

# Step 2: embed
python pipeline/embedder.py \
  --input data/integration_test/papers.jsonl \
  --output data/integration_test/embeddings.npy \
  --batch-size 32

# Step 3: citations (use API fallback for 1K test)
python pipeline/citations.py \
  --papers data/integration_test/papers.jsonl \
  --output data/integration_test/citations.jsonl \
  --api-fallback

# Step 4: build graph
python pipeline/graph_builder.py \
  --papers data/integration_test/papers.jsonl \
  --embeddings data/integration_test/embeddings.npy \
  --citations data/integration_test/citations.jsonl \
  --output data/integration_test/graph.pt \
  --knn-k 10

# Step 5: smoke test sampler
python - <<'EOF'
import torch
from torch_geometric.data import HeteroData
from pipeline.sampling import get_dataloaders

graph = torch.load("data/integration_test/graph.pt")
N = graph['paper'].x.shape[0]
train_mask = torch.zeros(N, dtype=torch.bool)
train_mask[:int(0.6 * N)] = True
val_mask = torch.zeros(N, dtype=torch.bool)
val_mask[int(0.6 * N):int(0.8 * N)] = True
test_mask = ~(train_mask | val_mask)

train_loader, val_loader, test_loader = get_dataloaders(
    graph,
    edge_types=[('paper', 'cites', 'paper'), ('paper', 'similar_to', 'paper')],
    fanouts=[10, 5],
    batch_size=64,
)

batch = next(iter(train_loader))
print(f"Batch paper nodes: {batch['paper'].x.shape[0]}")
print(f"Batch seed nodes: {batch['paper'].batch_size}")
print("Integration test passed.")
EOF
```

### Expected Output

```
Batch paper nodes: <some number between 64 and 800>
Batch seed nodes: 64
Integration test passed.
```

### What This Tests

- The full chain from raw metadata to a trainable graph runs without error
- SPECTER2 embeddings are valid (not NaN, correct shape)
- FAISS k-NN completes on a small embedding matrix
- PyG `HeteroData` is correctly constructed and passes internal validation
- The `NeighborLoader` produces correctly shaped mini-batches
- MPS device compatibility (if available; falls back to CPU gracefully)

### Cross-Disciplinary Baseline

After the integration test passes, run the SPECTER2 baseline evaluation on the ground truth pairs:

```bash
python pipeline/eval_cross_disciplinary.py \
  --embeddings data/integration_test/embeddings.npy \
  --embedding-index data/integration_test/embeddings_index.json \
  --ground-truth data/ground_truth/cross_disciplinary_pairs.json \
  --output data/integration_test/baseline_scores.json
```

This script looks up any ground truth pairs where both papers are in the 1K integration test set (coverage will be low at 1K; this is expected). For covered pairs, it computes the SPECTER2 cosine similarity and the rank of the correct paper among all 1K candidates. Log the results to establish what random-chance baseline looks like before scaling.

---

## File/Directory Structure

```
gcn-citation/
├── pipeline/                          # New Phase 0 pipeline code
│   ├── __init__.py
│   ├── arxiv_bulk.py                  # Module 1: stream-parse arXiv snapshot
│   ├── embedder.py                    # Module 2: SPECTER2 MPS inference
│   ├── citations.py                   # Module 3: S2ORC citation loading
│   ├── graph_builder.py               # Module 4: PyG HeteroData construction
│   ├── sampling.py                    # Module 5: NeighborLoader setup
│   └── eval_cross_disciplinary.py    # Utility: SPECTER2 baseline on ground truth pairs
│
├── data/
│   ├── arxiv-metadata-oai-snapshot.json   # Download separately from arXiv S3
│   ├── s2orc/                             # S2ORC bulk shards (download separately)
│   │   ├── s2orc_shard_00.jsonl.gz
│   │   └── ...
│   ├── ground_truth/
│   │   └── cross_disciplinary_pairs.json  # Manually curated evaluation pairs
│   ├── integration_test/                  # Outputs from 1K integration test
│   │   ├── papers.jsonl
│   │   ├── embeddings.npy
│   │   ├── embeddings_index.json
│   │   ├── embeddings.checkpoint.json
│   │   ├── citations.jsonl
│   │   ├── citations_stats.json
│   │   ├── graph.pt
│   │   ├── graph_stats.json
│   │   └── baseline_scores.json
│   └── phase0/                            # Outputs from full 10K run
│       ├── papers.jsonl
│       ├── papers_manifest.json
│       ├── embeddings.npy
│       ├── embeddings_index.json
│       ├── embeddings.checkpoint.json
│       ├── citations.jsonl
│       ├── citations_stats.json
│       ├── graph.pt
│       └── graph_stats.json
│
├── src/gcn_citation/                  # Existing codebase (unchanged)
│   ├── models/
│   │   ├── gcn.py
│   │   ├── graphsage.py
│   │   ├── graphsage_jax.py
│   │   ├── gat_jax.py
│   │   ├── gt_torch.py
│   │   └── gt_nnsight.py
│   ├── data.py
│   ├── arxiv_data.py
│   ├── experiments.py
│   ├── visualize.py
│   └── cli.py
│
├── docs/
│   ├── research_requirements.md
│   ├── phase0_plan.md                 # This document
│   └── ...
│
├── configs/
│   └── compare/
│       └── ...
│
└── main.py
```

### Notes on Coexistence

The new `pipeline/` code is intentionally separate from `src/gcn_citation/`. The existing codebase (GCN, GraphSAGE, GAT, GT on small arXiv/Cora via the API) continues to work unchanged. Phase 0 adds a parallel pipeline for the larger-scale work. The two share nothing except the `data/` directory layout convention.

---

## Dependencies to Add

The following packages are needed for Phase 0 and should be added to `requirements.txt`:

```
torch-geometric          # PyG HeteroData, NeighborLoader
transformers             # SPECTER2 via HuggingFace
faiss-cpu                # k-NN graph construction (CPU only, no CUDA needed)
ijson                    # Streaming JSON parsing for arXiv bulk snapshot
```

Existing dependencies already present: `torch`, `numpy`, `duckdb`.

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| S2ORC license restricts personal research use | Medium | API fallback mode already designed; 10K papers take ~2 hrs at 1 req/sec |
| SPECTER2 MPS inference fails or is very slow | Low | `--device cpu` fallback; 10K on CPU is ~5 min |
| arXiv snapshot format changes | Low | Check first 5 lines before parsing; add format version detection |
| FAISS k-NN is too slow at 10K | Very low | 10K × 768 in-memory FAISS takes ~2 seconds; no risk at this scale |
| PyG `NeighborLoader` multiprocessing issues on macOS | Medium | Default `num_workers=0`; document in module header |
| Integration test 1K has too few ground truth pair matches | Expected | Noted; score at 10K scale is the real baseline; 1K test just validates the pipeline runs |
