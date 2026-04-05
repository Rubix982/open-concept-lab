"""Pipeline subpackage for the ProG-scale arXiv graph learning system.

This package provides the end-to-end data pipeline for ingesting arXiv bulk
metadata, embedding papers with SPECTER2, loading citation edges from S2ORC,
constructing a PyG HeteroData graph, and serving mini-batch neighbor samples
for downstream training.

Module dependency order:
    arxiv_bulk  → embedder  → citations  → graph_builder  → sampling

Typical entry point: build a PipelineConfig via config.default_config(),
then call each module's public functions in the order above.
"""
