# Citation Graph Node Classifier

Manual graph neural network experiments for node classification on graph datasets built from Cora and arXiv.

## What this project does

- Downloads and parses the Cora citation graph
- Fetches arXiv papers by category and builds a similarity graph from title + abstract TF-IDF features
- Stores nodes, sparse features, and citation edges in DuckDB
- Trains manual NumPy GCN and GraphSAGE variants
- Trains a first JAX GAT baseline
- Evaluates the model in a semi-supervised setting with 140 labeled nodes
- Produces a t-SNE plot of learned node embeddings

## Quickstart

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Run a specific model-behavior experiment mode:

```bash
python3 main.py --mode feature-only
python3 main.py --mode graph-only
python3 main.py --mode depth-ablation --skip-tsne
python3 main.py --model graphsage --mode depth-ablation --skip-tsne
python3 main.py --model gat --mode baseline --skip-tsne
```

Run on a small arXiv slice:

```bash
python3 main.py --dataset arxiv --mode baseline --arxiv-categories cs.AI cs.LG cs.CL cs.CV
```

Sample arXiv workflow with cached data and a GCN run:

1. Fetch and cache a local arXiv corpus:

```bash
python3 main.py \
  --dataset arxiv \
  --cache-only \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --arxiv-batch-size 50 \
  --arxiv-delay-seconds 8
```

2. Train the baseline GCN on the cached corpus:

```bash
python3 main.py \
  --dataset arxiv \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --arxiv-top-k 10
```

This reuses the cached raw metadata and processed snapshot under `data/arxiv/` instead of refetching the corpus every run.

Train GraphSAGE with mean aggregation on the same cached corpus:

```bash
python3 main.py \
  --dataset arxiv \
  --model graphsage \
  --graphsage-variant v1 \
  --graphsage-aggregator mean \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --graphsage-fanouts 10 5
```

Try the mini-batch GraphSAGE v2 path:

```bash
python3 main.py \
  --dataset arxiv \
  --model graphsage \
  --graphsage-variant v2 \
  --graphsage-aggregator mean \
  --graphsage-batch-size 64 \
  --graphsage-sampler uniform \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --graphsage-fanouts 10 5
```

Try the first JAX GraphSAGE backend path:

```bash
python3 main.py \
  --dataset cora \
  --model graphsage \
  --graphsage-backend jax \
  --graphsage-variant v1 \
  --graphsage-aggregator mean \
  --graphsage-sampler uniform \
  --mode baseline \
  --skip-tsne
```

Try the first GAT baseline:

```bash
python3 main.py \
  --dataset cora \
  --model gat \
  --mode baseline \
  --skip-tsne
```

Try the JAX LSTM GraphSAGE path:

```bash
python3 main.py \
  --dataset cora \
  --model graphsage \
  --graphsage-backend jax \
  --graphsage-variant v1 \
  --graphsage-aggregator lstm \
  --graphsage-sampler uniform \
  --mode baseline \
  --skip-tsne
```

Run the full experiment suite in one command:

```bash
python3 main.py \
  --dataset arxiv \
  --mode full-experiment \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --density-top-k-values 5 10 20 40
```

This suite mode runs:

- baseline
- feature-only
- graph-only
- depth-ablation
- over-smoothing
- embedding-separation
- baseline density sweeps across the requested `top_k` values

Supported models:

- `gcn`: full-graph degree-normalized message passing
- `gat`: first JAX graph-attention baseline with dense adjacency masking
- `graphsage`: sampled-neighborhood mean aggregation with self/neighbor concatenation
  - backend variants: `numpy`, `jax`
  - `v1`: full-batch sampled-neighborhood baseline
  - `v2`: first mini-batch mean-aggregation path
  - aggregator variants: `mean`, `pool`, `lstm`
  - sampler variants: `uniform`, `with-replacement`, `degree-weighted`

Artifact layout is namespaced by model configuration:

- `artifacts/gcn/<mode>/...`
- `artifacts/graphsage/<backend>/<variant>/<aggregator>/<sampler>/<mode>/...`

Fetch and cache a larger arXiv corpus without training:

```bash
python3 main.py \
  --dataset arxiv \
  --cache-only \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --arxiv-batch-size 100
```

Then train repeatedly from the local cache:

```bash
python3 main.py \
  --dataset arxiv \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000
```

Run the V1 version of the GraphSAGE model,

```bash
python3 main.py \
  --model graphsage \
  --graphsage-variant v1 \
  --graphsage-aggregator mean \
  --dataset arxiv \
  --mode depth-ablation \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --graphsage-fanouts 10 5
```

Run the V2 version of the GraphSAHE model,

```bash
python3 main.py \
  --model graphsage \
  --graphsage-variant v2 \
  --graphsage-aggregator mean \
  --graphsage-batch-size 64 \
  --dataset arxiv \
  --mode depth-ablation \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --graphsage-fanouts 10 5
```

Running with a custom sampler for GraphSAGE,

```bash
python3 main.py \
  --model graphsage \
  --graphsage-variant v2 \
  --graphsage-aggregator mean \
  --graphsage-sampler uniform \
  --graphsage-batch-size 64 \
  --dataset arxiv \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 10000 \
  --graphsage-fanouts 10 5
```

Artifacts are written to model-specific and mode-specific folders under `artifacts/`:

- `artifacts/gcn/baseline/report.json`
- `artifacts/gcn/baseline/cora.duckdb`
- `artifacts/gcn/baseline/baseline_metrics.json`
- `artifacts/gcn/baseline/baseline_embeddings.npy`
- `artifacts/gcn/baseline/baseline_tsne.png`
- `artifacts/gcn/baseline/accuracy_comparison.png`
- `artifacts/gcn/baseline/history_comparison.png`
- `artifacts/graphsage/v2/mean/uniform/baseline/report.json`

## Research roadmap

- `docs/research_questions.md`: structured research questions and experiment backlog for future analysis modes
- `docs/arxiv_pipeline_plan.md`: implementation roadmap for the cached arXiv corpus pipeline
- `docs/prog_learning_roadmap.md`: staged learning roadmap inspired by the ProG benchmark paper
- `docs/graphsage_v2_plan.md`: development plan for mini-batch GraphSAGE v2
- `docs/graphsage_v2_1_plan.md`: refinement plan for GraphSAGE v2 mini-batching diagnostics and scaling readiness
- `docs/graphsage_sampler_plan.md`: next-step plan for GraphSAGE sampler variants
- `docs/graphsage_aggregator_plan.md`: staged plan for expanding GraphSAGE aggregators from `mean` to `pool` and later `lstm`
- `docs/graphsage_jax_plan.md`: additive plan for introducing a JAX backend for future GraphSAGE `lstm` work
- `docs/gat_plan.md`: staged plan for the first GAT implementation
- `docs/session_2026_03_24.md`: session summary capturing today's implementation progress, findings, and next steps

## What We Learned

- We built intuition for GCNs as degree-normalized neighbor aggregation over graph-structured data.
- We clarified how the normalized adjacency matrix stabilizes message passing.
- We revisited gradient descent and manual backpropagation in a NumPy-based neural network.
- We used t-SNE to inspect learned node embeddings and compare representation quality across runs.
- We introduced experiment modes for feature-only, graph-only, depth ablation, over-smoothing, and embedding separation.
- We extended the project from the fixed Cora benchmark to a cached local arXiv corpus.
- We built a reusable arXiv fetch/cache/build workflow so experiments can run repeatedly on local data.
- We added a single-command full experiment suite for orchestrated runs across multiple modes.
- Our first strong result on the cached arXiv corpus is that a 1-layer GCN currently outperforms deeper variants, both in the t-SNE plots and in validation/test accuracy.

## Dataset support

- `cora`: standard citation-network benchmark
- `arxiv`: live metadata fetch from arXiv API, TF-IDF features from title + abstract, and a k-NN similarity graph

The first arXiv pipeline is intentionally simple:

- Labels come from the selected primary arXiv categories
- Node features come from TF-IDF text features
- Edges come from top-k cosine similarity neighbors, not citations yet

Caching behavior:

- raw arXiv metadata is cached under `data/arxiv/raw/...`
- processed graph snapshots are cached under `data/arxiv/processed/...`
- repeated training runs reuse the local cache by default
- use `--refresh-arxiv-cache` to rebuild the cached corpus and processed snapshot
- raw batch downloads are resumable, so interrupted long fetches can continue from cached `batch_*.xml` files
- larger corpus builds are fetched one category at a time to reduce arXiv API pressure
- for larger corpus builds, prefer smaller `--arxiv-batch-size` and larger `--arxiv-delay-seconds`

## Model behavior modes

- `baseline`: standard 2-layer GCN reference run
- `feature-only`: disables graph propagation with identity adjacency
- `graph-only`: removes lexical features and uses structural identity features
- `depth-ablation`: compares 1-layer, 2-layer, and 3-layer GCNs
- `over-smoothing`: uses the depth sweep and reports representation collapse signals
- `embedding-separation`: measures class centroid distance and within-class spread

Visualization outputs:

- Every mode writes per-run t-SNE plots unless `--skip-tsne` is passed
- Every mode writes an accuracy comparison chart and a training-history chart
- Multi-run modes write a combined t-SNE grid
- `over-smoothing` writes a dedicated diagnostic plot
- `embedding-separation` writes a dedicated separation summary plot

## Project layout

- `main.py`: CLI entrypoint for the full pipeline
- `src/gcn_citation/data.py`: dataset download, parsing, DuckDB persistence, graph prep
- `src/gcn_citation/models/`: graph model implementations such as GCN and GraphSAGE
- `src/gcn_citation/pretraining/`: scaffolding for graph pre-training methods
- `src/gcn_citation/prompting/`: scaffolding for graph prompt-learning methods
- `src/gcn_citation/experiments.py`: model behavior experiment runners
- `src/gcn_citation/arxiv_data.py`: arXiv fetching, parsing, TF-IDF feature building, and similarity graph construction
- `src/gcn_citation/visualize.py`: t-SNE plot generation
- `docs/research_questions.md`: research questions grouped by theme
- `docs/arxiv_pipeline_plan.md`: staged plan for caching and scaling arXiv experiments
- `docs/prog_learning_roadmap.md`: staged concept-to-implementation roadmap inspired by ProG
- `docs/graphsage_v2_plan.md`: implementation plan for GraphSAGE v2
- `docs/graphsage_v2_1_plan.md`: cleanup and diagnostics plan for GraphSAGE v2.1
- `docs/graphsage_sampler_plan.md`: sampler-variant plan for GraphSAGE
- `docs/graphsage_aggregator_plan.md`: aggregator expansion plan for GraphSAGE
- `docs/graphsage_jax_plan.md`: JAX backend plan for future GraphSAGE LSTM work
- `docs/gat_plan.md`: GAT implementation plan
