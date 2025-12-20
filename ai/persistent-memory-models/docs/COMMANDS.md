# 🎓 Research Paper System - Command Reference

## Overview

You now have a complete system for:
1. **Downloading** research papers from arXiv
2. **Caching** them locally (no re-downloads)
3. **Processing** with hierarchical attention
4. **Querying** with semantic search

---

## 📋 Available Commands

### 1. Repository Management (`repo_cli`)

```bash
# Show repository statistics
python -m persistent_memory.repo_cli stats

# Get a specific paper (downloads if not cached)
python -m persistent_memory.repo_cli get 1706.03762

# Get paper with text preview
python -m persistent_memory.repo_cli get 1706.03762 --show-text

# Search and cache papers
python -m persistent_memory.repo_cli search "hierarchical attention" --max-results=5

# List all cached papers
python -m persistent_memory.repo_cli list-cached

# Get extracted text
python -m persistent_memory.repo_cli get-text 1706.03762

# Clear cache for specific paper
python -m persistent_memory.repo_cli clear --arxiv-id=1706.03762

# Clear entire cache
python -m persistent_memory.repo_cli clear --all
```

### 2. Paper Search (`cli`)

```bash
# Search arXiv (without downloading)
python -m persistent_memory.cli search-papers "transformers" --max-results=10
```

### 3. Paper Ingestion (`cli`)

```bash
# Ingest specific papers by arXiv ID
python -m persistent_memory.cli ingest-papers --arxiv-ids="1706.03762,1409.0473"

# Search and ingest
python -m persistent_memory.cli ingest-papers --search="attention mechanisms" --max-papers=5

# Ingest curated collection
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms

# Available collections:
#   - attention_mechanisms
#   - rag_systems
#   - memory_networks
#   - hierarchical_models
```

### 4. Querying (`cli`)

```bash
# Query the memory system
python -m persistent_memory.cli query "What is the transformer architecture?"

# Query with more results
python -m persistent_memory.cli query "How does attention work?" --k=10
```

### 5. Interactive Demo

```bash
# Run the interactive demo
python quick_demo.py
```

---

## 🐳 Docker Commands

Once services are running (`docker-compose up -d`):

```bash
# Repository stats
docker-compose exec app python -m persistent_memory.repo_cli stats

# Get a paper
docker-compose exec app python -m persistent_memory.repo_cli get 1706.03762

# Ingest papers
docker-compose exec app python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms

# Query
docker-compose exec app python -m persistent_memory.cli query "transformers"
```

---

## 📚 Example Workflows

### Workflow 1: Quick Start
```bash
# 1. Search for papers
python -m persistent_memory.cli search-papers "hierarchical attention"

# 2. Download one
python -m persistent_memory.repo_cli get 1706.03762

# 3. Check stats
python -m persistent_memory.repo_cli stats
```

### Workflow 2: Build Knowledge Base
```bash
# 1. Ingest curated collection
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms

# 2. Query it
python -m persistent_memory.cli query "What is self-attention?"

# 3. Query with more context
python -m persistent_memory.cli query "Compare different attention mechanisms" --k=10
```

### Workflow 3: Research Specific Topic
```bash
# 1. Search for papers
python -m persistent_memory.cli search-papers "retrieval augmented generation" --max-results=10

# 2. Ingest top 5
python -m persistent_memory.cli ingest-papers --search="retrieval augmented generation" --max-papers=5

# 3. Query
python -m persistent_memory.cli query "How does RAG work?"
```

---

## 🎯 What Each Component Does

### `data_repository.py`
- **Downloads** papers from arXiv
- **Caches** PDFs and extracted text
- **Prevents** duplicate downloads
- **Organizes** data in clean directory structure

### `arxiv_downloader.py`
- **Searches** arXiv API
- **Downloads** PDFs
- **Extracts** text from PDFs
- **Rate limits** to respect arXiv

### `paper_ingestion_workflow.py`
- **Orchestrates** paper processing with Temporal
- **Chunks** text for embedding
- **Extracts** facts with LLM
- **Stores** in vector store + knowledge graph

### `hierarchical_attention.py`
- **Learns** which contexts are most relevant
- **Multi-level** attention (chunk + sentence)
- **Adaptive** context selection

### `attention_retrieval.py`
- **Integrates** attention with retrieval
- **Ranks** contexts intelligently
- **Returns** weighted results

---

## 📊 Directory Structure

After running commands, you'll have:

```
data/
├── papers/
│   ├── 1706.03762/              # Attention Is All You Need
│   │   ├── metadata.json        # Paper info
│   │   ├── paper.pdf            # Original PDF
│   │   └── extracted_text.txt   # Extracted text
│   └── 1409.0473/               # Another paper
│       └── ...
├── cache/
│   └── index.json               # Fast lookup
└── processed/
    └── embeddings/              # Future: cached embeddings
```

---

## 💡 Pro Tips

1. **First download is slow** (~30s per paper)
   - Downloads PDF
   - Extracts text
   - Saves to cache

2. **Subsequent access is instant**
   - Reads from cache
   - No network calls

3. **All pipelines share cache**
   - Ingest once, use everywhere
   - No duplicate downloads

4. **Check cache before ingesting**
   ```bash
   python -m persistent_memory.repo_cli list-cached
   ```

5. **Clear cache to free space**
   ```bash
   python -m persistent_memory.repo_cli stats  # Check size
   python -m persistent_memory.repo_cli clear --all  # Clear if needed
   ```

---

## 🚀 Next Steps

1. **Install dependencies** (if not in Docker):
   ```bash
   pip install -r requirements.txt
   ```

2. **Try the demo**:
   ```bash
   python quick_demo.py
   ```

3. **Ingest some papers**:
   ```bash
   python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
   ```

4. **Query them**:
   ```bash
   python -m persistent_memory.cli query "What is the transformer?"
   ```

5. **Check the docs**:
   - `QUICKSTART.md` - Detailed guide
   - `docs/research/HIERARCHICAL_ATTENTION.md` - Research paper
   - `docs/OLLAMA_INTEGRATION.md` - LLM setup

---

**You're all set! Start exploring research papers with AI-powered search! 🎉**
