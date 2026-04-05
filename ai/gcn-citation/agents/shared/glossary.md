# Shared Glossary

_Owned by: all agents. Append-only. Never edit prior entries._

---

- **ProG**: "Graph Prompting" paradigm (Sun et al., 2023) — pre-train once, adapt via prompts
- **SPECTER2**: Academic paper embedding model by Allen AI (allenai/specter2_base); 768d float32 vectors trained on citation-contrastive loss
- **HeteroGraph**: Heterogeneous graph with multiple node types (Paper, Category) and edge types (cites, similar_to, belongs_to, co_category)
- **GraphMAE**: Graph Masked Autoencoder — pre-trains by masking and reconstructing node features (Hou et al., 2022)
- **DGI**: Deep Graph Infomax — pre-trains by maximizing MI between node and global graph embeddings (Veličković et al., 2019)
- **SimGRACE**: Simple Graph Contrastive — perturbs encoder weights instead of graph data to create views (Xia et al., 2022)
- **GraphCL**: Graph Contrastive Learning — augments the graph (edge drop, feature mask) and applies contrastive loss (You et al., 2020)
- **EdgePre**: Edge Prediction pre-training — pre-trains on edge existence prediction; aligns with link prediction downstream tasks
- **GPF / GPF-plus**: Graph Prompt Feature — adds a learnable feature vector to all input nodes; plus variant supports task-specific vectors (Sun et al., 2023)
- **GPPT**: Graph Pre-trained Prompt Tuning — reformulates node classification as link prediction between node and class prototype (Sun et al., 2022)
- **Gprompt**: Learnable prompt token combined with node features via inner product readout (Liu et al., 2023)
- **All-in-one**: Prompt is a small subgraph prepended to input; handles node classification, link prediction, and graph classification (Sun et al., 2023)
- **OGB-arxiv**: Open Graph Benchmark arXiv dataset — 169,343 nodes, used as the "large" GNN benchmark; our 500K target exceeds this
- **OpenAlex**: Open academic knowledge graph (CC0 license); replacement for defunct S2ORC for citation data
- **S2ORC**: Semantic Scholar Open Research Corpus — original bulk citation dataset; bulk download links are defunct as of 2026
- **MPS**: Apple Metal Performance Shaders — GPU compute backend for PyTorch on Apple Silicon
- **FAISS**: Facebook AI Similarity Search — library for fast approximate nearest-neighbor search; used for k-NN semantic graph construction
- **HeteroData**: PyTorch Geometric heterogeneous graph container (`torch_geometric.data.HeteroData`)
- **NeighborLoader**: PyG mini-batch sampler that samples fixed-size neighborhoods per hop (GraphSAGE-style)
- **Interdisciplinary paper**: A paper tagged with 2+ primary arXiv categories; explicitly flagged in graph construction for Goal 2 experiments
- **Cross-disciplinary pair**: Two papers from different fields sharing a deep conceptual idea without citation links; used for Goal 1 evaluation
- **Residual stream**: The accumulated hidden state in a transformer that each block reads from and writes to via residual connections
- **Routing shift**: Change in attention weight distribution (who attends to whom) caused by an intervention on a prior block's output
- **docs/sessions/**: Session notes indexed by date (YYYY-MM-DD.md format); one file per working session
- **docs/plans/**: Implementation plans for features, models, and pipeline stages; one file per plan
- **docs/research/**: Research findings, project requirements, and structured open questions
