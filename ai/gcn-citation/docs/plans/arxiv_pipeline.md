# arXiv Pipeline Plan

This document captures the plan for evolving the project from a benchmark-only Cora experiment into a reusable local arXiv graph-learning pipeline.

## Why this plan exists

The goal is to move beyond a fixed benchmark and build a repeatable workflow for:

- fetching real arXiv paper metadata in batches
- caching that data locally and aggressively
- building reusable graph datasets from the cache
- running multiple graph-learning models on the same local corpus
- studying how graph density and graph size affect model behavior

This is the bridge from a small GCN demo to a more serious graph research sandbox.

## High-level direction

Keep two paths in the repository:

- `Cora` remains the sanity-check benchmark
- `arXiv` becomes the growing local corpus for real-data experiments

The arXiv path should be split into three explicit stages:

1. Fetch
2. Build
3. Train

That separation keeps network access, dataset construction, and model experimentation cleanly decoupled.

## Phase 1: Aggressive raw caching

Build a raw arXiv corpus fetcher that:

- fetches papers by category in batches
- supports medium and large local corpora, eventually up to around 10K papers
- caches raw metadata locally so repeated experiments do not re-query the API
- uses local cache by default unless the user explicitly refreshes it

Expected controls:

- `--cache-only`
- `--refresh-arxiv-cache`
- `--arxiv-batch-size`
- `--arxiv-max-results`
- `--arxiv-categories`

Suggested raw cache contents:

- arXiv id
- title
- abstract
- published date
- updated date if available
- primary category
- all categories if available

## Phase 2: Corpus manifest and inspection

Every fetched corpus should carry its own metadata summary.

Persist:

- categories requested
- papers fetched
- fetch timestamp
- batch count
- duplicate handling stats
- label counts by category
- date range of papers

This should be written to:

- a manifest JSON for quick human inspection
- DuckDB tables for SQL analysis

The corpus should be inspectable without training.

## Phase 3: Processed dataset snapshots

Raw arXiv metadata should be converted into reusable processed datasets.

Each processed snapshot should contain:

- node labels from selected primary categories
- text features from title + abstract
- graph edges from a graph builder strategy
- split masks for train, validation, and test
- summary stats for node count, edge count, and density

The point is to avoid rebuilding features and edges every time we want to train a model.

Suggested processed outputs:

- DuckDB tables
- JSON summary report
- matrix or array artifacts for features, labels, edges, and masks

## Phase 4: Graph-building controls

The first arXiv graph should stay simple:

- TF-IDF features from title + abstract
- top-k cosine similarity graph

Then expose graph-density controls such as:

- `top_k`
- similarity threshold

Persist graph diagnostics:

- number of nodes
- number of edges
- average degree
- graph density
- connected component stats when feasible

This is important because graph density itself is part of the research story.

## Phase 5: Training on cached corpora

Training should consume processed datasets repeatedly without touching the network.

That enables:

- repeated ablations
- multiple model comparisons
- controlled graph-density experiments
- stable benchmarking across runs

The same cached corpus should support:

- GCN
- GraphSAGE
- GAT
- later self-supervised or transformer-based graph models

## Phase 6: Scaling experiments

Once the corpus pipeline is stable, add scaling studies across:

- corpus size
- graph density

Example sweeps:

- node count: `500`, `1000`, `2500`, `5000`, `10000`
- graph density via `top_k`: `5`, `10`, `20`, `40`

Record:

- train, validation, and test accuracy
- runtime
- graph statistics
- artifact paths

This supports a concrete research claim:

- dense manual GCNs work for smaller graphs
- denser and larger graphs stress dense adjacency approaches
- this motivates sparse and sampling-based methods such as GraphSAGE

## Phase 7: Model roadmap after the pipeline is stable

Recommended order:

1. GraphSAGE
2. GAT
3. DGI
4. GraphMAE
5. Graph Transformer

Rationale:

- GraphSAGE is the most natural next step for scaling
- GAT adds a different message-weighting mechanism
- DGI and GraphMAE open the self-supervised path
- Graph Transformers are powerful but introduce a larger engineering jump

## Immediate implementation scope

The next milestone should stay disciplined.

Implement only:

- aggressive raw arXiv caching
- processed dataset reuse
- manifest and summary reporting
- CLI support for separated fetch/build/train stages

Do not expand to new models until the corpus pipeline is reliable.

## Definition of success for the next milestone

We should be able to:

1. fetch and cache a medium arXiv corpus locally
2. inspect what was fetched without training
3. build a processed graph snapshot from that cache
4. train multiple times from the processed snapshot without re-fetching
5. vary graph density and corpus size in a controlled way
