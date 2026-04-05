# Pipeline Subpackage

End-to-end data pipeline for the ProG-scale arXiv graph learning system.

## What It Does

Converts the raw arXiv bulk S3 snapshot and S2ORC citation data into a
PyTorch Geometric `HeteroData` graph with SPECTER2 node features, ready
for mini-batch GNN training on M2 (MPS device).

## Module Dependency Order

```
arxiv_bulk  →  embedder  →  citations  →  graph_builder  →  sampling
```

| Module          | Responsibility                                              |
|-----------------|-------------------------------------------------------------|
| `config.py`     | `PipelineConfig` dataclass + `default_config()` factory     |
| `arxiv_bulk.py` | Stream/filter arXiv OAI snapshot; checkpoint to `.parquet`  |
| `embedder.py`   | Batch SPECTER2 inference (MPS); write memory-mapped `.npy`  |
| `citations.py`  | Load S2ORC / OpenAlex edges; map string IDs → node indices  |
| `graph_builder.py` | FAISS k-NN + PyG HeteroData assembly + sanity checks     |
| `sampling.py`   | PyG `NeighborLoader` for 2-hop mini-batch training          |

## Running the End-to-End Pipeline (once implemented)

```python
from pathlib import Path
from gcn_citation.pipeline.config import default_config
from gcn_citation.pipeline import arxiv_bulk, embedder, citations, graph_builder, sampling

cfg = default_config()

# 1. Parse and filter the arXiv snapshot
papers = arxiv_bulk.load_papers_to_dataframe(
    cfg.arxiv_snapshot_path, categories=cfg.categories, max_papers=cfg.max_papers
)

# 2. Embed with SPECTER2 (resumes from checkpoint if interrupted)
embeddings = embedder.embed_papers(
    papers, cfg.embeddings_path, cfg.embeddings_path.with_suffix(".ckpt"),
    batch_size=cfg.embedding_batch_size,
)

# 3. Load citation edges
known_ids = set(papers["arxiv_id"])
edges = citations.load_s2orc_citations(cfg.citations_path, known_ids)
id_to_index = {aid: i for i, aid in enumerate(papers["arxiv_id"])}
edges = citations.assign_indices(edges, id_to_index)

# 4. Build the heterogeneous graph
graph = graph_builder.build_hetero_graph(papers, embeddings, edges, knn_k=cfg.knn_k)
warnings = graph_builder.validate_graph(graph)

# 5. Create a mini-batch sampler for training
loader = sampling.build_neighbor_sampler(graph, batch_size=512)
```

See `docs/research/requirements.md` §3 for the full data pipeline design.
