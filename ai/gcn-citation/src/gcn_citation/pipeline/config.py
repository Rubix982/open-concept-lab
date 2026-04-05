"""Dataclass-based configuration for the arXiv graph learning pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    """Top-level configuration for the end-to-end graph learning pipeline.

    Attributes:
        data_dir: Root data directory. All relative artifact paths are resolved
            beneath this directory.
        arxiv_snapshot_path: Path to the arXiv bulk metadata OAI snapshot
            (``arxiv-metadata-oai-snapshot.json``), downloaded from arXiv S3.
            The file is streamed line-by-line and is never loaded fully into memory.
        embeddings_path: Path where the SPECTER2 float32 embedding matrix is
            stored as a memory-mapped ``.npy`` file of shape ``[N, 768]``.
        citations_path: Path to the processed citation edge list, stored as a
            two-column ``.npy`` or ``.parquet`` file of (source_arxiv_id,
            target_arxiv_id) string pairs.
        graph_path: Path to the serialised ``torch_geometric.data.HeteroData``
            graph object (saved via ``torch.save``).
        categories: arXiv category identifiers to include in the working subset,
            e.g. ``["cs.LG", "cs.AI", "stat.ML"]``.  Papers with at least one
            matching category are retained.
        max_papers: Hard cap on the number of papers kept after filtering.
            Useful for staged scaling (10K dev, 100K baseline, 500K experiments).
        embedding_batch_size: Number of papers forwarded through SPECTER2 per
            MPS/CUDA batch.  32-64 is recommended for M2 unified memory.
        knn_k: Number of nearest neighbours per paper for the semantic
            ``similar_to`` k-NN graph constructed with FAISS.
        seed: Global random seed used for reproducible dataset splits and any
            stochastic operations in the pipeline.
    """

    data_dir: Path
    arxiv_snapshot_path: Path
    embeddings_path: Path
    citations_path: Path
    graph_path: Path
    categories: list[str]
    max_papers: int
    embedding_batch_size: int
    knn_k: int
    seed: int


def default_config(data_dir: Path | None = None) -> PipelineConfig:
    """Return a PipelineConfig with sensible defaults for 10K development scale.

    All path defaults are relative to ``data_dir`` (defaults to ``data/pipeline``
    inside the repository root, inferred from this file's location).

    Args:
        data_dir: Override the root data directory.  When ``None``, defaults to
            ``<repo_root>/data/pipeline``.

    Returns:
        A PipelineConfig ready for a 10K-paper development run.
    """
    if data_dir is None:
        # Resolve repo root as three levels up from this file:
        # src/gcn_citation/pipeline/config.py -> repo root
        _repo_root = Path(__file__).resolve().parents[3]
        data_dir = _repo_root / "data" / "pipeline"

    return PipelineConfig(
        data_dir=data_dir,
        arxiv_snapshot_path=data_dir / "raw" / "arxiv-metadata-oai-snapshot.json",
        embeddings_path=data_dir / "embeddings" / "specter2_embeddings.npy",
        citations_path=data_dir / "citations" / "citation_edges.parquet",
        graph_path=data_dir / "graph" / "hetero_graph.pt",
        categories=["cs.LG", "cs.AI", "cs.CL", "cs.CV", "stat.ML"],
        max_papers=10_000,
        embedding_batch_size=32,
        knn_k=10,
        seed=42,
    )
