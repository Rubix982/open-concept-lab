# GraphSAGE v2 Plan

This document captures the next development phase for GraphSAGE in this repository.

## Why v2 exists

The current GraphSAGE implementation is a useful learning-oriented `v1`:

- mean aggregation
- fixed fanout sampling
- full-batch sampled neighborhoods

That version is good enough for conceptual understanding and early comparisons against GCN, but it does not yet reflect the more practical mini-batch workflow that makes GraphSAGE especially valuable on larger graphs.

GraphSAGE `v2` focuses on that next step.

## v1 baseline

Preserve the current version as the baseline reference.

Current assumptions:

- mean aggregator
- uniform random neighbor sampling
- fixed fanout
- full-batch sampled neighborhoods

This version should remain available for comparison while `v2` is being built.

## v2 target

GraphSAGE `v2` will introduce:

- mini-batch training
- mean aggregation
- fixed-fanout neighbor sampling

And it will intentionally *not* introduce yet:

- new aggregators
- advanced sampling strategies
- architectural changes unrelated to batching

The point is to isolate the effect of mini-batching and make the learning progression clear.

## Core idea

Instead of computing embeddings for the whole graph in one forward pass, `v2` should:

1. choose a batch of target nodes
2. sample their neighbors
3. sample neighbors-of-neighbors for deeper layers
4. build the local computation subgraph
5. run forward and backward only on that local subgraph

This is closer to the authentic GraphSAGE workflow and is the main educational goal of `v2`.

## Implementation phases

### Phase 1: Preserve v1

- Keep the current GraphSAGE behavior stable
- make it selectable as a version or variant
- avoid silently mutating it while `v2` is under development

### Phase 2: Introduce GraphSAGE variants

Add a variant distinction such as:

- `graphsage-v1`
- `graphsage-v2`

Or a shared `graphsage` model with a variant flag.

The key requirement is that `v1` and `v2` can be compared directly in the same CLI and reporting flow.

### Phase 3: Mini-batch data flow

Build the batching infrastructure:

- batch target nodes
- sample per-layer neighborhoods
- collect the nodes needed for the local subgraph
- maintain index mappings between:
  - global node ids
  - local batch/subgraph ids

This is the main engineering challenge.

### Phase 4: Mini-batch forward pass

Implement a forward pass that:

- operates only on the sampled local subgraph
- computes hidden states layer by layer
- returns logits only for the batch target nodes

The aggregator should remain:

- mean aggregation

### Phase 5: Mini-batch backward pass and training loop

Implement training with:

- mini-batch target nodes
- repeated steps per epoch
- validation/testing still supported in a clear way

For early versions, evaluation can remain simpler than training if needed.

### Phase 6: v1 vs v2 comparison

Run direct comparisons on:

- Cora
- cached arXiv corpus

Compare:

- train/val/test accuracy
- runtime
- embedding quality
- scaling behavior

## What comes after v2

Only after mini-batching is stable should the next two improvement axes be added:

### Sampler variants

Suggested order:

1. uniform random
2. full-neighbor fallback
3. degree-aware sampling later

### Aggregator variants

Suggested order:

1. mean
2. pool / max-pool
3. LSTM later

These should be added one axis at a time, not all at once.

## Immediate next milestone

Implement:

- GraphSAGE `v2`
- mini-batch mean aggregation
- fixed fanout
- shared CLI/reporting support

Keep the current GraphSAGE as `v1` for comparison.
