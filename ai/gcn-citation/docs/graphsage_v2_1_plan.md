# GraphSAGE v2.1 Plan

This document captures the next refinement phase for GraphSAGE after the first `v2` mini-batch path started outperforming `v1`.

## Why v2.1 exists

`GraphSAGE v2` introduced the right high-level idea:

- mini-batch training
- mean aggregation
- fixed-fanout neighborhood sampling

That is a meaningful step forward, but before pushing hard toward larger arXiv corpora such as `5K` and `10K`, the mini-batch pipeline should become cleaner, more inspectable, and easier to reason about.

`v2.1` is the “make the batching path solid” phase.

## Goals

The goals of `v2.1` are:

- make neighborhood expansion logic easier to understand
- expose useful diagnostics for batch construction and runtime behavior
- make it easier to reason about scaling before increasing corpus size

This phase does **not** add new aggregators or new samplers yet.

## Scope

### In scope

- cleaner mini-batch subgraph construction
- clearer global-to-local index mapping
- diagnostics for sampled batch structure
- diagnostics for runtime and batch counts
- better comments and code organization inside the GraphSAGE implementation

### Out of scope

- new aggregator variants
- new sampler variants
- major architectural changes unrelated to batching

## Main improvement areas

### 1. Cleaner neighborhood expansion

Current batching works, but the local sampled neighborhood logic should be easier to inspect and explain.

Refinement targets:

- separate neighborhood expansion from forward-pass code
- make per-layer active nodes explicit
- make global node ids and local node ids easier to track
- reduce “hidden” assumptions in the batching path

### 2. Better batch diagnostics

For each run, the GraphSAGE trainer should expose diagnostics such as:

- batch size
- number of batches per epoch
- average local nodes per batch
- average sampled edges or neighbor links per batch
- effective fanouts used

These should be saved in the run details so results are interpretable.

### 3. Runtime diagnostics

To prepare for larger corpora, each run should surface:

- total training time
- average epoch time

This makes scaling studies easier later.

### 4. Better educational readability

This repository is a learning and research-building environment, so the mini-batch GraphSAGE path should remain understandable.

That means:

- explicit comments at key batching steps
- simple helper functions
- stable naming for:
  - target nodes
  - expanded nodes
  - local subgraph ids
  - active nodes per layer

## Implementation order

### Phase 1

Extract and clean the batch-subgraph construction helpers.

### Phase 2

Collect diagnostic statistics during training, including:

- average local node count per batch
- average target node count per batch
- batch count per epoch

### Phase 3

Collect runtime statistics.

### Phase 4

Surface those diagnostics in experiment details and reports.

## What comes after v2.1

Once `v2.1` is stable:

1. try larger cached arXiv corpora such as `5K`
2. evaluate whether `10K` is realistic with the improved batching path
3. only then introduce sampler variants

Suggested next order after v2.1:

1. scale to `5K`
2. scale to `10K` if practical
3. add sampler variants
4. add aggregator variants

## Success criteria

`v2.1` is successful if:

- GraphSAGE `v2` still runs correctly
- reports now include useful batching diagnostics
- the batching code is easier to explain and maintain
- we can make a more informed decision about scaling to `5K` and `10K`
