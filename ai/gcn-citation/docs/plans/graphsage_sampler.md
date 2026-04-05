# GraphSAGE Sampler Variants Plan

This document captures the next extension step for GraphSAGE after stabilizing the `v2` mini-batch path.

## Why samplers are next

The current GraphSAGE implementation already has:

- mean aggregation
- fixed fanout
- a working mini-batch path
- batching diagnostics

The next clean comparison axis is **neighbor sampling strategy**.

This is a natural next step because it changes how neighborhood information is selected while keeping the rest of the GraphSAGE architecture stable.

## Immediate goal

Introduce configurable sampler strategies for GraphSAGE while preserving:

- the same mean aggregator
- the same mini-batch training path
- the same reporting and experiment workflow

That allows sampler comparisons to remain controlled and interpretable.

## Sampler roadmap

### 1. uniform

Definition:

- sample up to `fanout` neighbors uniformly at random

Role:

- baseline strategy
- current default behavior

### 2. with-replacement

Definition:

- sample exactly `fanout` neighbors uniformly at random with replacement

Role:

- allows repeated neighbors inside the sampled neighborhood
- useful for contrasting "fixed sample budget" behavior against without-replacement sampling

### 3. degree-weighted

Definition:

- sample neighbors with probabilities derived from node degree

Role:

- later extension once the first two sampler paths are stable

## Immediate implementation scope

Implement only:

- sampler flag plumbing
- `uniform`
- `with-replacement`
- `degree-weighted`

Do not add new aggregators during this step.

## Comparison plan

Compare on the same cached arXiv corpus:

- GraphSAGE `v2` + `uniform`
- GraphSAGE `v2` + `with-replacement`
- GraphSAGE `v2` + `degree-weighted`

Track:

- train/val/test accuracy
- embedding quality
- batching diagnostics
- runtime

## What comes after sampler variants

After sampler comparisons are stable:

1. compare sampler runtime, batch growth, and accuracy on larger arXiv corpora
2. add a pooling aggregator
3. consider LSTM aggregation after that
