# GAT Implementation Plan

This note captures the next end-to-end graph model step after GCN and GraphSAGE.

## Why GAT next

Graph Attention Networks are the natural next model because they introduce
learned neighbor weighting without jumping all the way to Graph Transformers.

## First implementation scope

The first GAT version in this repo is deliberately small:

- JAX backend
- full-batch training
- dense adjacency masking
- single-head attention
- same dataset pipeline
- same experiment/reporting surface

## What comes next

After the first GAT baseline is stable:

1. add multi-head attention
2. compare depth `1` vs `2`
3. evaluate on cached arXiv
4. then decide whether to move onward to Graph Transformer
