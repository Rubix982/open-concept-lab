# 🚀 Future Data Structures and Research Directions

## 1. Introduction

While classic data structures (B-Trees, RBTs, Hash Maps) dominate production systems, **new research is actively reshaping the landscape**.  
The key drivers are:  

- **Hardware shifts** (SSDs, NVMe, GPUs, large caches).  
- **Workload evolution** (streaming, time-series, AI/ML preprocessing).  
- **Theoretical advances** (succinct structures, learned models).  

This document provides an overview of **emerging structures** with direct references to **papers, repos, and prototypes**.

---

## 2. Learned Indexes

### 2.1 Recursive Model Indexes (RMI)

- **Concept:** Replace tree traversal with ML model predictions for key positions.  
- **Paper:** [The Case for Learned Index Structures (Kraska et al., 2018)](https://arxiv.org/abs/1712.01208)  
- **Implementation:** [learned-indexes repo](https://github.com/learnedsystems/Learnedsystems)  

### 2.2 ALEX (Adaptive Learned Index)

- **Concept:** Adaptive models for dynamic datasets.  
- **Paper:** [ALEX: An Updatable Adaptive Learned Index](https://dl.acm.org/doi/10.1145/3318464.3389711)  
- **Repo:** [microsoft/ALEX](https://github.com/microsoft/ALEX)  

---

## 3. Succinct & Compressed Data Structures

### 3.1 Wavelet Trees

- **Concept:** Support rank/select queries in compressed space.  
- **Paper:** [Succinct Data Structures (Navarro & Mäkinen, 2007)](https://users.dcc.uchile.cl/~gnavarro/ps/sdsl.pdf)  
- **Library:** [SDSL-lite](https://github.com/simongog/sdsl-lite)  

### 3.2 Elias-Fano Indexes

- **Concept:** Compact integer sequence representation with fast select.  
- **Paper:** [Space-efficient Static Functions (Elias-Fano, 1974; rediscovered for search engines)](https://vigna.di.unimi.it/ftp/papers/EliasFano.pdf)  
- **Implementation:** [Google Elias-Fano in LevelDB fork](https://github.com/google/leveldb)  

---

## 4. GPU-Accelerated Structures

### 4.1 GPU B-Trees

- **Concept:** Warp-optimized traversals for SIMD parallelism.  
- **Paper:** [GPU B-Trees (Awad et al., 2019)](https://dl.acm.org/doi/10.1145/3302424.3303977)  
- **Repo:** [cuda-btree](https://github.com/owensgroup/cuda-btree)  

### 4.2 GPU Hash Tables

- **Concept:** Concurrent hash maps built for GPUs.  
- **Repo:** [moderngpu/hash](https://github.com/moderngpu/moderngpu)  

---

## 5. Hybrid Log-Tree Structures

### 5.1 PebblesDB

- **Concept:** Fractal tree index, improves on LSM by reducing write amplification.  
- **Paper:** [PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees](https://www.usenix.org/system/files/conference/sosp17/sosp17-agarwal.pdf)  
- **Repo:** [utsaslab/pebblesdb](https://github.com/utsaslab/pebblesdb)  

### 5.2 Dostoevsky LSM

- **Concept:** Unifying tiered and leveled compaction in LSM trees.  
- **Paper:** [Dostoevsky: Better Space-Time Trade-offs for LSM-Tree-Based Key-Value Stores](https://www.cs.cmu.edu/~huanche1/publications/dostoevsky-sigmod18.pdf)  

---

## 6. Learned & Probabilistic Hybrids

### 6.1 Learned Bloom Filters

- **Concept:** Neural nets replace hash functions for set membership, reducing false positives.  
- **Paper:** [The Case for Learned Index Structures (extended Bloom filter discussion)](https://arxiv.org/abs/1712.01208)  

### 6.2 Neural Cuckoo Hashing

- **Concept:** Machine-learned displacement strategies in cuckoo hashing.  
- **Research Direction:** No stable repo yet; experimental prototypes in ML systems.  

---

## 7. Temporal & Streaming Structures

### 7.1 Fractal Trees

- **Concept:** Buffered updates reduce write cost, designed for streaming.  
- **Paper:** [Cache-Oblivious Streaming B-Trees (Bender et al.)](https://dl.acm.org/doi/10.1145/1073814.1073826)  

### 7.2 Streaming Segment Trees

- **Concept:** Adapt segment trees to efficiently support sliding-window queries.  
- **Research Direction:** Used in observability + telemetry systems (no canonical repo).  

---

## 8. Quick Links Table

| Structure                 | Paper / Reference                                          | Repo / Implementation |
|----------------------------|-----------------------------------------------------------|------------------------|
| Recursive Model Index (RMI)| [Kraska et al., 2018](https://arxiv.org/abs/1712.01208)   | [learnedsystems](https://github.com/learnedsystems/Learnedsystems) |
| ALEX                       | [SIGMOD 2020](https://dl.acm.org/doi/10.1145/3318464.3389711) | [microsoft/ALEX](https://github.com/microsoft/ALEX) |
| Wavelet Trees              | [Navarro & Mäkinen](https://users.dcc.uchile.cl/~gnavarro/ps/sdsl.pdf) | [sdsl-lite](https://github.com/simongog/sdsl-lite) |
| Elias-Fano Indexes         | [Vigna et al.](https://vigna.di.unimi.it/ftp/papers/EliasFano.pdf) | [Google LevelDB fork](https://github.com/google/leveldb) |
| GPU B-Trees                | [GPU B-Trees (Awad, 2019)](https://dl.acm.org/doi/10.1145/3302424.3303977) | [cuda-btree](https://github.com/owensgroup/cuda-btree) |
| GPU Hash Tables            | Moderngpu repo                                           | [moderngpu](https://github.com/moderngpu/moderngpu) |
| PebblesDB                  | [SOSP '17](https://www.usenix.org/system/files/conference/sosp17/sosp17-agarwal.pdf) | [utsaslab/pebblesdb](https://github.com/utsaslab/pebblesdb) |
| Dostoevsky LSM             | [SIGMOD '18](https://www.cs.cmu.edu/~huanche1/publications/dostoevsky-sigmod18.pdf) | N/A |
| Fractal Trees              | [Bender et al.](https://dl.acm.org/doi/10.1145/1073814.1073826) | N/A |

---

## 9. Takeaways

- **The classics (B-Trees, LSM-Trees) are not going away soon.**  
- **Learned indexes + GPU structures** are the next major frontier.  
- **Succinct/compressed structures** matter where memory or bandwidth dominates cost.  
- **Future engineers** should be able to casually move between **classic trade-offs and emerging prototypes**.  
