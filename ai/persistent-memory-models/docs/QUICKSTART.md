# Quick Start Guide

## 🚀 How to Use the Research Paper System

### 1. **Search for Papers**
```bash
# Search arXiv
python -m persistent_memory.repo_cli search "hierarchical attention"

# Or use the CLI
python -m persistent_memory.cli search-papers "transformers"
```

### 2. **Download & Cache Papers**
```bash
# Get a specific paper (downloads if not cached)
python -m persistent_memory.repo_cli get 1706.03762

# The famous "Attention Is All You Need" paper
# Downloads once, cached forever!
```

### 3. **View Repository Stats**
```bash
python -m persistent_memory.repo_cli stats
```

### 4. **Ingest Papers into Memory System**
```bash
# Ingest specific papers
python -m persistent_memory.cli ingest-papers --arxiv-ids="1706.03762,1409.0473"

# Search and ingest
python -m persistent_memory.cli ingest-papers --search="attention mechanisms" --max-papers=3

# Use curated collection
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
```

### 5. **Query the System**
```bash
# Query ingested papers
python -m persistent_memory.cli query "What is the transformer architecture?"

# With more results
python -m persistent_memory.cli query "How does attention work?" --k=10
```

### 6. **Run Interactive Demo**
```bash
python quick_demo.py
```

## 📚 Curated Collections

### `attention_mechanisms`
- 1706.03762 - Attention Is All You Need (Transformers)
- 1409.0473 - Neural Machine Translation (Bahdanau)
- 1508.04025 - Effective Approaches to Attention (Luong)

### `rag_systems`
- 2005.11401 - RAG: Retrieval-Augmented Generation
- 2002.08909 - REALM
- 2004.04906 - DPR: Dense Passage Retrieval

### `memory_networks`
- 1410.3916 - Memory Networks
- 1503.08895 - End-To-End Memory Networks
- 1606.03126 - Key-Value Memory Networks

### `hierarchical_models`
- 1606.02393 - Hierarchical Attention Networks
- 1511.06303 - Hierarchical RNNs

## 🎯 Example Workflow

```bash
# 1. Search for papers
python -m persistent_memory.repo_cli search "transformers" --max-results=5

# 2. Download and cache a paper
python -m persistent_memory.repo_cli get 1706.03762

# 3. Check what's cached
python -m persistent_memory.repo_cli list-cached

# 4. Ingest into memory system
python -m persistent_memory.cli ingest-papers --arxiv-ids="1706.03762"

# 5. Query the system
python -m persistent_memory.cli query "What is self-attention?"

# 6. View stats
python -m persistent_memory.repo_cli stats
```

## 🐳 With Docker

Once services are running:

```bash
# All commands work the same, just prefix with docker-compose exec app
docker-compose exec app python -m persistent_memory.repo_cli stats
docker-compose exec app python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
docker-compose exec app python -m persistent_memory.cli query "transformers"
```

## 💡 Tips

- **First download is slow** (downloads PDF, extracts text)
- **Subsequent access is instant** (uses cache)
- **All pipelines share the cache** (no duplicate downloads)
- **Clear cache if needed**: `python -m persistent_memory.repo_cli clear --all`

## 🎓 Advanced Usage

### Python API
```python
from persistent_memory.data_repository import get_repository

repo = get_repository()

# Get paper (auto-caches)
paper = repo.get_paper('1706.03762')
print(paper['metadata']['title'])
print(f"Text: {len(paper['text'])} chars")

# Just get text
text = repo.get_text('1706.03762')

# Check if cached
if repo.is_cached('1706.03762'):
    print("Already downloaded!")

# Search and cache
papers = repo.search_and_cache("attention", max_results=5)
```

### Hierarchical Attention
```python
from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.persistent_vector_store import PersistentVectorStore

vs = PersistentVectorStore()
retrieval = AttentionEnhancedRetrieval(vs)

# Query with attention
result = retrieval.retrieve_with_attention(
    "What is the transformer?",
    k=10,
    return_attention=True
)

# See attention weights
for ctx in result['contexts']:
    print(f"Attention: {ctx['attention_score']:.3f}")
    print(f"Text: {ctx['text'][:100]}...")
```

## 🔧 Troubleshooting

### Services not running?
```bash
docker-compose up -d
docker-compose ps
```

### Missing dependencies?
```bash
pip install -r requirements.txt
```

### Clear cache?
```bash
python -m persistent_memory.repo_cli clear --all
```

---

**You now have a complete research paper ingestion and querying system!** 🎉
