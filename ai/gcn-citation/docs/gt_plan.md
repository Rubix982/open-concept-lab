# GT Implementation Plan

This note captures the first Graph Transformer direction for the repo.

## Why GT now

Graph Transformer is the natural next step after GAT because it keeps the
attention idea, but moves into a more general Transformer-style block with:

- multi-head self-attention
- residual connections
- feedforward sublayers
- normalization

## First implementation scope

The first `GT` path in this repo is intentionally practical:

- PyTorch backend
- full-batch training
- graph-aware pairwise attention mask
- residual Transformer blocks
- degree signal injected as a small structural feature
- same experiment/reporting pipeline as the other models
- optional NNsight tracing for internal module outputs

## What comes next

After the first baseline is stable:

1. compare depth `1` vs `2`
2. evaluate on cached arXiv
3. consider richer structural encodings
4. add more attention diagnostics or intervention tooling
5. then think about NNsight-compatible introspection
