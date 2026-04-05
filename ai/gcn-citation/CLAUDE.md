# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Graph-learning research sandbox** inspired by the ProG paper and related graph ML concepts. Built primarily with Codex as a hands-on learning environment for exploring graph neural network architectures, aggregation strategies, and interpretability techniques.

Manual graph neural network experiments for node classification on citation graphs (Cora) and arXiv paper similarity graphs. The project implements multiple GNN architectures (GCN, GraphSAGE, GAT, Graph Transformer) with different backends (NumPy, JAX, PyTorch) for research and learning purposes.

**Last meaningful commit**: `8c1488c` — "Add compare-run tooling and GT tracing support"

## Common Commands

### Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

**Note**: Dependencies include `torch` and `nnsight` for Graph Transformer work. Some unrelated environment warnings (airbyte/pydantic/numpy) may appear but can be ignored - the repo functionality is unaffected.

### Run Baseline Experiments

```bash
# Cora GCN baseline
python3 main.py

# GraphSAGE v1 with mean aggregation
python3 main.py --model graphsage --graphsage-variant v1 --graphsage-aggregator mean --mode baseline

# GAT baseline (JAX)
python3 main.py --dataset cora --model gat --mode baseline --skip-tsne

# Graph Transformer baseline (PyTorch)
python3 main.py --dataset cora --model gt --mode baseline --gt-heads 4 --gt-layers 2 --skip-tsne
```

### Run Specific Experiment Modes

```bash
# Feature-only (no graph propagation)
python3 main.py --mode feature-only

# Graph-only (structural features)
python3 main.py --mode graph-only

# Depth ablation (1-layer, 2-layer, 3-layer comparison)
python3 main.py --mode depth-ablation --skip-tsne

# Over-smoothing analysis
python3 main.py --mode over-smoothing

# Embedding separation diagnostics
python3 main.py --mode embedding-separation

# Full experiment suite
python3 main.py --mode full-experiment --skip-tsne
```

### arXiv Dataset Workflow

```bash
# Cache arXiv corpus (fetch once, use repeatedly)
python3 main.py \
  --dataset arxiv \
  --cache-only \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --arxiv-batch-size 50 \
  --arxiv-delay-seconds 8

# Train on cached corpus
python3 main.py \
  --dataset arxiv \
  --mode baseline \
  --arxiv-categories cs.AI cs.LG cs.CL cs.CV \
  --arxiv-max-results 2000 \
  --arxiv-top-k 10

# Refresh cache if needed
python3 main.py --dataset arxiv --mode baseline --refresh-arxiv-cache
```

### Compare Two Configurations

```bash
python3 main.py \
  --mode compare-runs \
  --compare-name graphsage-aggregators \
  --compare-config-a configs/compare/graphsage_mean.json \
  --compare-config-b configs/compare/graphsage_lstm.json
```

## Architecture Overview

### Code Organization

- **main.py**: CLI entrypoint that delegates to `src/gcn_citation/cli.py`
- **src/gcn_citation/cli.py**: Argument parsing, orchestration, subprocess management for compare-runs mode
- **src/gcn_citation/data.py**: Cora dataset download, parsing, DuckDB persistence, graph preprocessing
- **src/gcn_citation/arxiv_data.py**: arXiv API fetching, caching, TF-IDF feature extraction, k-NN similarity graph construction
- **src/gcn_citation/experiments.py**: Experiment mode runners (baseline, feature-only, graph-only, depth-ablation, etc.)
- **src/gcn_citation/visualize.py**: t-SNE, accuracy charts, training history plots
- **src/gcn_citation/models/**: Model implementations
  - `gcn.py`: NumPy GCN with manual backpropagation
  - `graphsage.py`: NumPy GraphSAGE (v1 full-batch, v2 mini-batch with uniform/degree-weighted sampling)
  - `graphsage_jax.py`: JAX GraphSAGE with mean/pool/lstm aggregators
  - `gat_jax.py`: JAX Graph Attention Network
  - `gt_torch.py`: PyTorch Graph Transformer
  - `gt_nnsight.py`: NNsight-based tracing and intervention utilities for Graph Transformer
- **src/gcn_citation/pretraining/**: Scaffolding for future graph pre-training methods
- **src/gcn_citation/prompting/**: Scaffolding for future graph prompt-learning methods

### Model Variants and Backends

**GCN**: NumPy-based degree-normalized message passing with manual backprop

**GraphSAGE**:

- Backends: `numpy`, `jax`
- Variants: `v1` (full-batch sampled-neighborhood), `v2` (mini-batch)
- Aggregators: `mean`, `pool`, `lstm`
- Samplers: `uniform`, `with-replacement`, `degree-weighted`

**GAT**: JAX-based with dense adjacency masking, multi-head attention, configurable dropout

**Graph Transformer (GT)**: PyTorch-based with graph-aware masked attention, optional NNsight tracing for interpretability

### Data Flow

1. **Dataset Loading**:
   - Cora: `data.py::ensure_cora_dataset()` → `load_graph_data()`
   - arXiv: `arxiv_data.py::build_cached_arxiv_dataset()` with resumable batch fetching

2. **Graph Preprocessing**: Returns `GraphData` object with:
   - `features`: Node feature matrix
   - `labels`: Integer class labels
   - `adjacency_hat`: Normalized adjacency matrix (with self-loops)
   - `train_mask`, `val_mask`, `test_mask`: Split masks
   - `edges`: Edge list for GraphSAGE sampling

3. **Experiment Execution**: `experiments.py::MODE_TO_RUNNER` maps mode names to runner functions

4. **Training**: Model-specific `train_*()` functions return `TrainingResult` with embeddings, logits, metrics, history

5. **Output**: Each run saves:
   - `report.json`: Full experiment metadata
   - `*_metrics.json`, `*_history.json`, `*_details.json`
   - `*_embeddings.npy`, `*_logits.npy`
   - `*_tsne.png` (unless `--skip-tsne`)
   - Comparison charts: `accuracy_comparison.png`, `history_comparison.png`, `tsne_grid.png`

### Artifact Layout

Model-specific and mode-specific artifact directories:

```
artifacts/
├── gcn/
│   ├── baseline/
│   ├── depth_ablation/
│   └── ...
├── graphsage/
│   └── {backend}/{variant}/{aggregator}/{sampler}/{mode}/
├── gat/{mode}/
└── gt/{mode}/
```

Compare-runs artifacts:

```
artifacts/compare_runs/{name}/
├── report.json
├── comparison.md
├── run_a/...
└── run_b/...
```

### DuckDB Persistence

Graph data is persisted to DuckDB for reproducibility:

- Tables: `nodes`, `features`, `edges`
- Each mode directory contains its own `.duckdb` file
- Cora: downloaded from LINQS, cached under `data/raw/cora/`
- arXiv: cached under `data/arxiv/raw/` (resumable batch XMLs) and `data/arxiv/processed/` (TF-IDF + graph snapshots)

### Experiment Modes

- **baseline**: Standard 2-layer GCN reference
- **feature-only**: Identity adjacency (no graph propagation)
- **graph-only**: Structural identity features (no lexical features)
- **depth-ablation**: Compares 1-layer, 2-layer, 3-layer models
- **over-smoothing**: Reports representation collapse signals across depths
- **embedding-separation**: Measures class centroid distances and within-class spread
- **compare-runs**: Parallel execution of two configs with winner summary table
- **full-experiment**: Orchestrated suite across multiple modes plus density sweeps

### GraphSAGE Sampling

- **Uniform**: Fixed-size neighborhoods sampled uniformly per layer
- **With-replacement**: Allows duplicate neighbors in samples
- **Degree-weighted**: Neighbors sampled proportional to their degree
- **Fanouts**: List of neighbor counts per layer (e.g., `[10, 5]` for 2-layer)

### NNsight Integration (Graph Transformer)

Enable tracing with `--gt-trace-with-nnsight`:

- Captures activations at: input projection, transformer block outputs, classifier, final logits
- Supports intervention workflows: `ablate_gt_head_with_nnsight()`, `patch_gt_block_output_with_nnsight()`
- See `docs/plans/gt_nnsight.md` for roadmap

## Development Notes

### Adding a New Model

1. Implement `train_{model}()` in `src/gcn_citation/models/{model}.py`
2. Return `TrainingResult` with `embeddings`, `logits`, `metrics`, `history`, `details`
3. Add model choice to `cli.py::build_parser()` and update `_artifact_root_dir()` if needed
4. Update `experiments.py::_train_selected_model()` to dispatch to new model

### Adding a New Experiment Mode

1. Define runner function in `experiments.py` that accepts `(GraphData, ExperimentArgs)` and returns `list[ExperimentArtifact]`
2. Add to `MODE_TO_RUNNER` mapping
3. Mode will automatically appear in `--mode` choices and `full-experiment` suite

### Compare-Runs Configs

JSON configs in `configs/compare/` should include:

- All CLI flags as snake_case keys (e.g., `graphsage_aggregator`)
- Optional `compare_label` for friendly display names
- Do NOT include `mode: "compare-runs"` (nested compare-runs not allowed)

Example:

```json
{
  "compare_label": "numpy-mean",
  "model": "graphsage",
  "graphsage_backend": "numpy",
  "graphsage_variant": "v1",
  "graphsage_aggregator": "mean",
  "dataset": "cora",
  "mode": "baseline",
  "epochs": 250,
  "skip_tsne": true
}
```

### Research Roadmap

This project is evolving into a **ProG-inspired graph learning lab** with a staged learning path:

**Stage 1: End-to-End Graph Models** (Current Focus)

1. ✅ **GCN** - Degree-normalized message passing, over-smoothing
2. ✅ **GraphSAGE** - Neighborhood sampling, inductive learning
3. ❌ **GAT** - Attention over neighborhoods (implemented but not run)
4. ❌ **GT** - Transformer-style global attention (implemented but not run)

**Stage 2: Graph Pre-Training** (Future)

- DGI (self-supervised mutual information)
- GraphCL (contrastive learning)
- GraphMAE (masked autoencoding)
- SimGRACE (self-supervised without augmentations)

**Stage 3: Graph Prompt Learning** (Future)

- GPF, GPF-plus, GPPT, Gprompt, All-in-one

**Research Questions**: `docs/research/research_questions.md` contains structured backlog organized by:

- Model Behavior (ablations, depth, over-smoothing, embedding separation)
- Data Questions (class difficulty, homophily, degree effects)
- Training Setup (hyperparameters, stability, convergence)
- Evaluation (per-class metrics, confusion patterns, calibration)
- Representation Learning (t-SNE alignment, downstream tasks)
- Baselines and Comparisons (logistic regression, MLP, label propagation)
- Robustness (edge removal, noise injection, generalization)

**Detailed Implementation Plans** in `docs/plans/`:

- `prog_learning_roadmap.md`: ProG-inspired learning roadmap
- `arxiv_pipeline.md`: arXiv corpus caching strategy
- `graphsage_v2.md`, `graphsage_v2_1.md`: Mini-batch GraphSAGE evolution
- `graphsage_sampler.md`, `graphsage_aggregator.md`: Sampling and aggregation variants
- `graphsage_jax.md`: JAX backend for LSTM aggregators
- `gat.md`: GAT implementation stages
- `gt.md`, `gt_nnsight.md`: Graph Transformer and interpretability roadmap

**Session Notes** in `docs/sessions/`:

- `2026-03-24.md`: Session notes (GraphSAGE progress, arXiv 7.8K corpus milestone)

**Working Style**: For each new method - implement minimal version, run on Cora for sanity check, test on arXiv corpus, compare against prior methods, document findings.

### Key Findings

- On the arXiv corpus, 1-layer GCN currently outperforms deeper variants (see t-SNE and validation accuracy)
- GraphSAGE v2 mini-batching diagnostics confirm correct neighborhood sampling across depths
- GAT attention diagnostics include entropy, self-attention, and strongest-neighbor patterns
- Graph Transformer with NNsight enables tracing at: input projection, transformer blocks, classifier, final logits

## Recent Work and Verified Behaviors

### Compare-Runs Mode (in `src/gcn_citation/cli.py`)

- Accepts two JSON configs via `--compare-config-a` and `--compare-config-b`
- Runs them in parallel using ThreadPoolExecutor
- Outputs:
  - `artifacts/compare_runs/<name>/report.json`: Full comparison metadata
  - `artifacts/compare_runs/<name>/comparison.md`: Winner summary + comparison table
  - `artifacts/compare_runs/<name>/run_a/`: First config's artifacts
  - `artifacts/compare_runs/<name>/run_b/`: Second config's artifacts
- Supports `compare_label` inside each JSON config for friendly display names
- Many starter configs available under `configs/compare/`:
  - arXiv and arXiv_10k variants
  - GraphSAGE mean/pool/lstm comparisons
  - GraphSAGE v2 sampler comparisons
  - GAT and debug Cora configs

### GAT Improvements (in `src/gcn_citation/models/gat_jax.py`)

- Real multi-head hidden attention (not just output concatenation)
- Separate feature dropout and attention dropout controls
- CLI arg: `--gat-attention-dropout` (default: 0.5)
- Enhanced diagnostics now report:
  - Layer head counts
  - Mean attention entropy (measuring uncertainty across neighbors)
  - Mean self-attention weight
  - Mean strongest-neighbor attention weight
  - Sample top-attended neighbors for inspection

### Graph Transformer Implementation (in `src/gcn_citation/models/gt_torch.py`)

- First PyTorch Graph Transformer baseline with graph-aware masked self-attention
- Residual transformer blocks with layer norm
- Custom per-head attention implementation for fine-grained interventions
- CLI args:
  - `--model gt`
  - `--gt-heads` (default: 4)
  - `--gt-layers` (default: 2)
  - `--gt-trace-with-nnsight` (enables NNsight tracing)
- Attention diagnostics similar to GAT (entropy, self-attention, max attention)
- Same reporting pipeline as other models (metrics, embeddings, logits, t-SNE)

### NNsight Integration for GT (in `src/gcn_citation/models/gt_nnsight.py`)

**Tracing helper**:

- `trace_gt_modules_with_nnsight(model, graph, ...)` captures activations at:
  - `input_projection`
  - Each transformer block output
  - `classifier`
  - Final `model_logits`

**Intervention helpers**:

1. `patch_gt_block_output_with_nnsight(model, graph, block_idx, mode, ...)`
   - Modes: `"zero"` (ablate block output), `"scale"` (multiply by scalar)
   - Verified to produce real logit shifts

2. `ablate_gt_head_with_nnsight(model, graph, block_idx, head_idx, ...)`
   - Zeros out specific attention head's contribution
   - Verified with measured example:
     - `mean_abs_logit_shift: 0.2439`
     - `num_prediction_changes: 731` (out of 2708 nodes on Cora)

**Verified smoke tests**:

- ✅ GT baseline on Cora succeeded
- ✅ GT + NNsight tracing succeeded
- ✅ Block output patching produced real logit shifts
- ✅ Head ablation produced real prediction changes

## Open Next Steps

### Graph Transformer Intervention Experiments

The GT intervention helpers (`patch_gt_block_output_with_nnsight`, `ablate_gt_head_with_nnsight`) currently exist as utility functions but are not integrated into the experiment framework. To make them first-class experiments:

1. **Create intervention experiment modes**:
   - Add `ablate-gt-head` mode to `experiments.py`
   - Add `patch-gt-block-output` mode to `experiments.py`
   - Each mode should sweep across blocks/heads and measure impact

2. **Artifact outputs**:
   - Save intervention results under `artifacts/gt/ablate_head/` or `artifacts/gt/patch_block/`
   - Include per-intervention metrics: `mean_abs_logit_shift`, `num_prediction_changes`, `accuracy_delta`
   - Generate visualization showing which heads/blocks matter most

3. **Cross-model comparisons**:
   - Compare GT against GAT and GraphSAGE on Cora and arXiv
   - Use `--mode compare-runs` with GT configs vs GAT/GraphSAGE configs

## Recommended Starting Point for GT Work

If continuing GT intervention development, start by reading:

1. `README.md` (understand overall project structure)
2. `docs/plans/gt.md` (GT baseline implementation roadmap)
3. `docs/plans/gt_nnsight.md` (intervention roadmap and future work)
4. Inspect code:
   - `src/gcn_citation/models/gt_torch.py` (model architecture)
   - `src/gcn_citation/models/gt_nnsight.py` (tracing and intervention utilities)
5. Review `docs/sessions/2026-03-24.md` for recent session notes

## Current Experiment Status

> The `artifacts/` folder contains data from all previous executions. Check reports and metrics there to understand what has been run and the results.

### Completed Experiments

#### GCN (NumPy Baseline)

**Dataset**: arXiv (1565 papers from cs.AI, cs.LG, cs.CL, cs.CV)

**All experiment modes completed**:

- ✅ `baseline` - Standard 2-layer GCN
  - Performance (k=5): Train 86.25% | Val 61.62% | Test 58.18%
- ✅ `feature-only` - No graph propagation (identity adjacency)
- ✅ `graph-only` - Structural features only
- ✅ `depth-ablation` - 1, 2, 3 layer comparison
- ✅ `over-smoothing` - Representation collapse analysis
- ✅ `embedding-separation` - Class centroid analysis
- ✅ `full-experiment` - Complete suite with density sweeps (top_k: 5, 10, 20, 40)

**Artifacts**: `artifacts/baseline/`, `artifacts/full_experiment/`, `artifacts/depth_ablation/`, etc.

#### GraphSAGE (Multiple Backends and Variants)

**Well-tested** with comprehensive coverage across backends, aggregators, and samplers.

**NumPy Backend (v1)**:

- ✅ Mean aggregator (arXiv k=10): Train 95.0% | Val 61.21% | Test 59.49%
  - Artifacts: `artifacts/graphsage/numpy/v1/mean/uniform/baseline/`
- ✅ Pool aggregator: Multiple runs including depth ablation
  - Artifacts: `artifacts/graphsage/numpy/v1/pool/uniform/baseline/`

**JAX Backend (v1)**:

- ✅ **LSTM aggregator** (arXiv k=10): Train 98.75% | Val 62.63% | **Test 60.71%**
  - **Best test accuracy achieved so far!**
  - Artifacts: `artifacts/graphsage/jax/v1/lstm/uniform/baseline/`

**v2 Mini-batch**:

- ✅ Baseline and depth ablation runs
- ✅ Degree-weighted sampler tested
- Artifacts: `artifacts/graphsage/v2/`

**Compare-runs verified**:

- ✅ Pool vs LSTM (arXiv 10k): LSTM wins on test accuracy (61.29% vs 60.94%)
- Artifacts: `artifacts/compare_runs/arxiv10k-pool-vs-lstm/`

### Critical Gaps - Models Not Yet Tested

#### GAT (Graph Attention Network)

**Status**: ❌ **IMPLEMENTED BUT NEVER RUN**

- Full JAX implementation exists: `src/gcn_citation/models/gat_jax.py`
- Features: multi-head attention, attention diagnostics, entropy analysis
- Config ready: `configs/compare/arxiv_gat_jax.json`
- **No artifacts exist** - has never been executed
- **Action needed**: Run first GAT baseline to establish attention-based performance

#### Graph Transformer (GT)

**Status**: ❌ **IMPLEMENTED BUT NEVER RUN**

- Full PyTorch implementation exists: `src/gcn_citation/models/gt_torch.py`
- NNsight integration ready: `src/gcn_citation/models/gt_nnsight.py`
- Features: graph-aware masked attention, NNsight tracing, intervention helpers
- **No configs exist yet**
- **No artifacts exist** - has never been executed
- **Action needed**:
  1. Create GT configs
  2. Run GT baseline on Cora/arXiv
  3. Test NNsight tracing
  4. Integrate intervention experiments into framework

### Performance Summary Table

| Model     | Backend | Aggregator | Dataset      | Train      | Val        | Test       | Artifacts Path                       |
| --------- | ------- | ---------- | ------------ | ---------- | ---------- | ---------- | ------------------------------------ |
| GCN       | NumPy   | N/A        | arXiv (k=5)  | 86.25%     | 61.62%     | 58.18%     | `artifacts/baseline/`                |
| GraphSAGE | NumPy   | Mean       | arXiv (k=10) | 95.0%      | 61.21%     | 59.49%     | `artifacts/graphsage/numpy/v1/mean/` |
| GraphSAGE | NumPy   | Pool       | arXiv 10k    | 100.0%     | 62.2%      | 60.94%     | `artifacts/compare_runs/.../run_a/`  |
| GraphSAGE | JAX     | **LSTM**   | arXiv (k=10) | 98.75%     | 62.63%     | **60.71%** | `artifacts/graphsage/jax/v1/lstm/`   |
| GAT       | JAX     | N/A        | —            | ❌ Not run | ❌ Not run | ❌ Not run | None                                 |
| GT        | PyTorch | N/A        | —            | ❌ Not run | ❌ Not run | ❌ Not run | None                                 |

### Key Findings from Artifact Analysis

1. **JAX GraphSAGE with LSTM aggregator** currently has the best test performance (60.71%)
2. **Full experiment infrastructure is working**: compare-runs, density sweeps, all experiment modes verified
3. **arXiv caching pipeline is stable**: 1565 papers cached and reused across runs
4. **GraphSAGE ecosystem is mature** but **attention-based models (GAT, GT) completely untested**
5. **No cross-architecture comparisons** have been run (GCN vs GraphSAGE vs GAT vs GT)
6. **GT intervention helpers exist** but are not integrated into the experiment framework

### Available Resources Not Yet Used

**Ready-to-run configs**:

- `configs/compare/arxiv_gat_jax.json` - GAT comparison ready
- Various GraphSAGE v2 sampler configs exist but haven't all been tested

**Missing configs**:

- No GT configs created yet (needed for baseline and compare-runs)

**Code waiting for integration**:

- `gt_nnsight.py` intervention helpers need experiment mode integration
- Head ablation and block patching exist as utilities but not as experiment modes

### Recommended Next Actions

Based on the current state, prioritize:

1. **Run first GAT baseline** to establish attention mechanism performance

   ```bash
   python3 main.py --model gat --dataset cora --mode baseline --skip-tsne
   ```

2. **Run first GT baseline** to establish transformer baseline

   ```bash
   python3 main.py --model gt --dataset cora --mode baseline --gt-heads 4 --gt-layers 2 --skip-tsne
   ```

3. **Test GT with NNsight tracing** to verify interpretability pipeline works end-to-end

4. **Create cross-model comparison** using existing compare-runs infrastructure:
   - GCN vs GraphSAGE (mean) vs GAT vs GT on same arXiv corpus

5. **Integrate GT intervention experiments** into the experiment framework as proper modes
