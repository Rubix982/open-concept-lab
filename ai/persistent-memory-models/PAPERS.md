# Research Papers Tracking

This file tracks the research papers and influential projects mentioned during the development and research of the Persistent Memory LLM system.

## Foundational Attention & Scaling

- **[Attention Is All You Need](https://arxiv.org/abs/1706.03762)** (Vaswani et al., 2017)
  - _Key Contribution:_ The Transformer architecture.
- **[Hierarchical Attention Networks for Document Classification](https://www.cs.cmu.edu/~./hovy/papers/16HLT-hierarchical-attention-networks.pdf)** (Yang et al., 2016)
  - _Key Contribution:_ Multi-level attention (Word -> Sentence) used as inspiration for our Chunk -> Sentence retrieval.
- **[Leave No Tokens Behind: Scaling Transformers to 1M+ Tokens](https://arxiv.org/abs/2404.07143)** (Ding et al., 2024)
  - _Key Contribution:_ Infini-attention and techniques for extremely long context.

## Memory Architecture & Systems

- **[MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)** (Packer et al., 2023)
  - _Key Contribution:_ Treating context as a multi-tiered memory hierarchy (RAM vs. Disk).
- **[vLLM: Efficient Memory Management with PagedAttention](https://arxiv.org/abs/2309.06180)** (Kwon et al., 2023)
  - _Key Contribution:_ PagedAttention for efficient KV cache sharing and management.

## Optimization & Retrieval

- **[H2O: Heavy-Hitter Oracle for KV Cache Eviction](https://arxiv.org/abs/2306.14048)** (Zhang et al., 2023)
  - _Key Contribution:_ Identifying and retaining high-attention "heavy hitter" tokens while pruning others.
- **[Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511)** (Asai et al., 2023)
  - _Key Contribution:_ A framework for models to autonomously decide when and what to retrieve.
