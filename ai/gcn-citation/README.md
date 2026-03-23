# Citation Graph Node Classifier

Manual 2-layer Graph Convolutional Network (GCN) for node classification on the Cora citation dataset.

## What this project does

- Downloads and parses the Cora citation graph
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
- `src/gcn_citation/visualize.py`: t-SNE plot generation
- `docs/research_questions.md`: research questions grouped by theme
