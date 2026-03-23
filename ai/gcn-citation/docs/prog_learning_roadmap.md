# ProG-Inspired Learning Roadmap

This document captures a practical learning and implementation roadmap inspired by the terminology and method families referenced in the ProG benchmark paper.

The goal is not to implement everything at once. The goal is to build a steady sequence of projects that deepen understanding of graph learning while also producing reusable engineering artifacts and research-style findings.

## Why this roadmap exists

This repository is evolving into a graph-learning lab, not just a single-model demo.

The intended progression is:

- learn one concept at a time
- implement it carefully
- run it on shared datasets
- compare it against earlier methods
- write down what was learned

This is meant to support a longer-term transition into research and research engineering.

## Core working style

For each concept or method:

1. Read enough of the paper to understand the core idea.
2. Implement a minimal working version.
3. Run it on `Cora` as a benchmark sanity check.
4. Run it on the cached local `arXiv` corpus.
5. Compare it against prior methods in the same repo.
6. Record one or two concrete findings.

This keeps learning grounded in both theory and practice.

## Stage 1: End-to-End Graph Models

These are the first models to implement because they teach the main graph encoder families.

### 1. GCN

Status:

- Implemented

What it teaches:

- graph convolution as normalized neighbor aggregation
- degree normalization
- message passing
- over-smoothing when depth increases

Current finding:

- On the cached arXiv similarity graph, a 1-layer GCN currently outperforms deeper variants.

### 2. GraphSAGE

Status:

- Next target

What it teaches:

- neighborhood sampling
- inductive graph learning
- sample-and-aggregate mechanics
- why GraphSAGE scales better than dense full-graph GCN

Why it comes next:

- it is the most natural conceptual extension from GCN
- it directly addresses scaling concerns already visible in the arXiv experiments

### 3. GAT

What it teaches:

- attention over graph neighborhoods
- learned weighting of neighbors
- when all neighbors should not contribute equally

Why it comes after GraphSAGE:

- it is easier to appreciate once basic message passing and aggregation are already clear

### 4. GT

What it teaches:

- transformer-style graph modeling
- global attention
- structural encoding challenges in graphs

Why it comes later:

- it is a larger engineering and conceptual jump

## Stage 2: Graph Pre-Training

These methods teach how to learn graph representations before task-specific supervision.

Recommended order:

1. DGI
2. GraphCL
3. GraphMAE
4. SimGRACE
5. edge-based pre-training variants after the above are stable

### DGI

What it teaches:

- self-supervised graph representation learning
- local-global mutual information ideas
- pretraining without class labels

### GraphCL

What it teaches:

- graph contrastive learning
- augmentation-based representation learning
- invariance and augmentation design

### GraphMAE

What it teaches:

- masked graph autoencoding
- reconstruction objectives
- pretrain-then-finetune style graph learning

### SimGRACE

What it teaches:

- self-supervised graph contrast without heavy manual augmentations
- robustness in graph representation learning

## Stage 3: Graph Prompt Learning

These methods should come after the basic model and pre-training families are understood.

Recommended order:

1. GPF
2. GPF-plus
3. GPPT
4. Gprompt
5. All-in-one

Why this stage is later:

- graph prompting is easier to understand once the underlying encoder and pretraining ideas are already familiar

### Prompt as token

Includes examples like:

- GPPT
- Gprompt
- GPF
- GPF-plus

What this family teaches:

- how prompts can modify node- or graph-level representations
- how prompting differs from retraining a full encoder

### Prompt as graph

Includes examples like:

- All-in-one

What this family teaches:

- how prompting can be represented structurally instead of only as added tokens or vectors

## Related Work Themes To Keep In Mind

Two broader themes from the paper should remain visible throughout the project:

### Graph pre-training

Questions to keep asking:

- when do pretrained graph representations help?
- how well do self-supervised objectives transfer across datasets?
- which pretraining objective is best aligned with downstream graph tasks?

### Graph prompt learning

Questions to keep asking:

- when is prompting sufficient instead of full fine-tuning?
- how does prompt design affect graph representation quality?
- are prompts helping with transfer, efficiency, or both?

## Shared dataset strategy

All methods should use the same shared dataset infrastructure when possible:

- `Cora` for sanity-check benchmarking
- cached local `arXiv` corpus for more realistic experimentation

This matters because comparisons are only useful when the data pipeline is shared.

## Shared engineering strategy

The repository should gradually support:

- shared caching
- shared dataset building
- shared reporting
- shared visualizations
- shared experiment orchestration

This allows the focus to stay on the differences between methods rather than rewriting infrastructure every time.

## Recommended next implementation order

1. GraphSAGE
2. GAT
3. DGI
4. GraphCL
5. GraphMAE
6. SimGRACE
7. graph prompt methods
8. GT after the rest of the stack is mature

## Definition of progress

Progress on this roadmap is not measured only by code quantity.

It is measured by:

- whether the concept became understandable
- whether the method was implemented cleanly
- whether the experiments are reproducible
- whether the findings were documented
- whether the project is becoming a better graph-learning lab over time

## Current snapshot

What is already true today:

- GCN is implemented
- model behavior modes exist
- arXiv caching exists
- full experiment orchestration exists
- an initial research finding has emerged: shallow GCN depth performs best on the current arXiv similarity graph

That is a strong starting point. The next step is GraphSAGE.
