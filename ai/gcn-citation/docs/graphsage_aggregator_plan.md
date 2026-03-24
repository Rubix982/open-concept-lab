# GraphSAGE Aggregator Expansion Plan

This note captures the next expansion stage for GraphSAGE after sampler support and mini-batch diagnostics.

## Current direction

We now want to broaden the GraphSAGE feature surface before introducing large sweep modes.

The intended order is:

1. keep current samplers
2. add a pooling-style aggregator
3. add an LSTM aggregator
4. stabilize comparisons
5. only then add sampler and aggregator sweep modes

## Aggregator roadmap

### 1. mean

- current baseline
- sampled neighbors are aggregated directly and concatenated with self features

### 2. pool

- learned neighbor projection before aggregation
- broadens GraphSAGE beyond plain averaging
- keeps the rest of the training and batching path stable

### 3. lstm

- sequence-style neighbor aggregation
- will require dedicated recurrent forward/backward logic
- should be added only after `pool` is stable

## Immediate goal

Implement `pool` cleanly across:

- GraphSAGE `v1`
- GraphSAGE `v2`
- CLI/configuration
- reporting and diagnostics
- artifact namespacing

## Comparison plan

On the same dataset, compare:

- `mean`
- `pool`

while holding fixed:

- variant
- sampler
- fanouts
- depth mode

## What comes next

After `pool` is stable and tested:

1. add the LSTM aggregator
2. verify comparisons across `mean`, `pool`, and `lstm`
3. then introduce sampler and aggregator sweep modes
