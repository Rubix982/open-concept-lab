# Citation Graph Node Classifier

Manual 2-layer Graph Convolutional Network (GCN) for node classification on graph datasets built from Cora and arXiv.

## What this project does

- Downloads and parses the Cora citation graph
- Fetches arXiv papers by category and builds a similarity graph from title + abstract TF-IDF features
- Stores nodes, sparse features, and citation edges in DuckDB
- Trains a manual NumPy GCN with the normalized adjacency formula
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

Artifacts are written to mode-specific folders under `artifacts/`:

- `artifacts/baseline/report.json`
- `artifacts/baseline/cora.duckdb`
- `artifacts/baseline/baseline_metrics.json`
- `artifacts/baseline/baseline_embeddings.npy`
- `artifacts/baseline/baseline_tsne.png`
- `artifacts/baseline/accuracy_comparison.png`
- `artifacts/baseline/history_comparison.png`

## Research roadmap

- `docs/research_questions.md`: structured research questions and experiment backlog for future analysis modes
- `docs/arxiv_pipeline_plan.md`: implementation roadmap for the cached arXiv corpus pipeline

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
- `src/gcn_citation/model.py`: manual 2-layer NumPy GCN and training loop
- `src/gcn_citation/experiments.py`: model behavior experiment runners
- `src/gcn_citation/arxiv_data.py`: arXiv fetching, parsing, TF-IDF feature building, and similarity graph construction
- `src/gcn_citation/visualize.py`: t-SNE plot generation
- `docs/research_questions.md`: research questions grouped by theme
- `docs/arxiv_pipeline_plan.md`: staged plan for caching and scaling arXiv experiments
