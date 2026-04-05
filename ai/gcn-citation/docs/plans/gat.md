# GAT Implementation Plan

This note captures the next end-to-end graph model step after GCN and GraphSAGE.

## Why GAT next

Graph Attention Networks are the natural next model because they introduce
learned neighbor weighting without jumping all the way to Graph Transformers.

## Current implementation scope

The current GAT path is still intentionally compact, but it is now more
reusable than the first single-head baseline:

- JAX backend
- full-batch training
- dense adjacency masking
- configurable multi-head hidden attention
- separate feature dropout and attention dropout
- attention diagnostics saved into experiment details
- same dataset pipeline
- same experiment/reporting surface

## What comes next

After this reusable baseline is stable:

1. compare depth `1` vs `2`
2. evaluate on cached arXiv
3. consider output-head averaging variants
4. possibly add edge-level attention export for selected nodes
5. then decide whether to move onward to Graph Transformer
