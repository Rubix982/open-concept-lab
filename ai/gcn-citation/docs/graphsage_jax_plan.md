# GraphSAGE JAX Backend Plan

This document captures the direction for introducing JAX into the project as a dedicated backend for the harder GraphSAGE variants, especially the future `lstm` aggregator.

## Why JAX here

The current NumPy implementations are excellent for learning:

- manual GCN
- GraphSAGE with `mean`
- GraphSAGE with `pool`

But `lstm` aggregation is a clear complexity jump because it requires recurrent sequence-style state updates and reliable backpropagation through those updates.

JAX is a good fit because it gives us:

- automatic differentiation
- a NumPy-like array programming model
- a natural path toward more research-style model implementations

## Intended split

The repo should keep two complementary paths:

### 1. NumPy path

Best for:

- manual understanding
- simpler graph models
- direct math-to-code learning

This path should continue to own:

- GCN
- GraphSAGE `mean`
- GraphSAGE `pool`

### 2. JAX path

Best for:

- harder differentiable models
- recurrent or more expressive aggregators
- future research-style expansion

This path should begin with:

- GraphSAGE `lstm`

## Design goal

Do not rewrite the repo around JAX.

Instead:

- keep the same dataset pipeline
- keep the same experiment and reporting surface
- isolate the new backend inside a dedicated file/module

Suggested file:

- `src/gcn_citation/models/graphsage_jax.py`

## Immediate milestones

1. Add JAX as an optional dependency
2. Add a dedicated JAX GraphSAGE module
3. Reuse the existing sampled-neighborhood and experiment infrastructure where practical
4. Implement a first working JAX GraphSAGE path for `lstm`
5. Compare against the NumPy `mean` and `pool` variants

## Comparison plan

Once the JAX LSTM path is ready, compare:

- NumPy GraphSAGE `mean`
- NumPy GraphSAGE `pool`
- JAX GraphSAGE `lstm`

holding fixed:

- dataset
- depth
- fanouts
- sampler

## Important constraint

The first JAX step should be additive, not disruptive.

That means:

- do not break the current NumPy training code
- do not force a backend rewrite before the JAX path is stable
- keep reporting compatible with the existing `TrainingResult` structure

## What comes after the first JAX path

After JAX GraphSAGE `lstm` is stable:

1. decide whether more GraphSAGE variants should also move to JAX
2. consider using JAX for future pretraining methods
3. then add sweep modes once the expanded model surface is stable
