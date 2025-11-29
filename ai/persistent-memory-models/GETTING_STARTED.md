# 🚀 Quick Start Guide

## Getting Started with the Persistent Memory System

This guide will get you from zero to running demos in **5 minutes**.

---

## 📋 Prerequisites

- **Python 3.11+** (3.14-dev works too)
- **Docker Desktop** (for services)
- **macOS** (for Ollama with Metal GPU support)
- **Git** (for version control)

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd /Users/saifulislam/code/open-concept-lab/ai/persistent-memory-models

# Install Python dependencies
pip install -r requirements.txt

# Or for development (includes testing tools)
pip install -r requirements-dev.txt
```

### Step 2: Start Services

```bash
# Start all Docker services (Postgres, Temporal, ChromaDB, Redis, etc.)
make up

# Wait ~30 seconds for services to initialize
# Check status
docker-compose ps
```

### Step 3: Set Up Ollama (Local LLM)

```bash
# Install and configure Ollama with Mistral model
make setup-host-llm

# This will:
# - Install Ollama via Homebrew
# - Start the Ollama service
# - Pull the Mistral model (~4GB download)
```

### Step 4: Run Your First Demo

```bash
# Demo 1: Research Paper System
python quick_demo.py

# Demo 2: Conference Integration
python demo_conferences.py

# Demo 3: Paper Ingestion (requires Temporal)
python demo_papers.py
```

---

## 🎯 What Can You Do?

### 1. **Search & Download Research Papers**

```bash
# Search arXiv
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python -m persistent_memory.cli search-papers "transformers"

# Download and cache a paper
python -m persistent_memory.repo_cli get 1706.03762

# Check what's cached
python -m persistent_memory.repo_cli stats
```

### 2. **Ingest Papers into Memory System**

```bash
# Ingest specific papers
python -m persistent_memory.cli ingest-papers --arxiv-ids="1706.03762,1409.0473"

# Ingest by search
python -m persistent_memory.cli ingest-papers --search="attention mechanisms" --max-papers=5

# Ingest curated collection
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
```

### 3. **Query the System**

```bash
# Query ingested papers
python -m persistent_memory.cli query "What is the transformer architecture?"

# Query with more results
python -m persistent_memory.cli query "How does attention work?" --k=10
```

### 4. **Conference Papers**

```bash
# List supported conferences
python -m persistent_memory.cli list-conferences

# Ingest NeurIPS 2023 papers
python -m persistent_memory.cli ingest-conference --name=neurips --year=2023
```

---

## 🧠 Using Persistent Memory Techniques with Your Model

This system provides **advanced persistent memory capabilities** that you can integrate with your LLM applications. Here's how to use each technique:

### 1. **Multi-Layer Memory Architecture**

The system uses a **4-layer memory hierarchy** for optimal context management:

```python
from persistent_memory import (
    PersistentVectorStore,      # Episodic memory
    PersistentKnowledgeGraph,   # Semantic memory
    PersistentContext,          # Working memory
)

# Initialize memory layers
vector_store = PersistentVectorStore()  # ChromaDB for semantic search
knowledge_graph = PersistentKnowledgeGraph()  # NetworkX for facts
context = PersistentContext(llm_model)  # Active context

# Store information across layers
vector_store.add_text("Transformers use self-attention", metadata={"source": "paper"})
knowledge_graph.add_fact("Transformer", "uses", "self-attention")
```

**When to use:**
- **Vector Store**: Semantic search, finding similar content
- **Knowledge Graph**: Structured facts, relationships, reasoning
- **Context**: Active conversation, working memory

---

### 2. **Hierarchical Attention Mechanism** 🔬

Our **research-grade attention system** learns which contexts are most relevant:

```python
from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.persistent_vector_store import PersistentVectorStore

# Initialize
vs = PersistentVectorStore()
retrieval = AttentionEnhancedRetrieval(vs)

# Retrieve with learned attention weights
result = retrieval.retrieve_with_attention(
    query="What is the transformer architecture?",
    k=10,
    return_attention=True
)

# Access results with attention scores
for ctx in result['contexts']:
    print(f"Attention: {ctx['attention_score']:.3f}")
    print(f"Text: {ctx['text'][:100]}...")
    print(f"Key sentence: {ctx['key_sentence']}")
```

**Benefits:**
- ✅ **Learns** which contexts are most relevant
- ✅ **Multi-level**: Chunk-level + sentence-level attention
- ✅ **Adaptive**: Improves over time with training

**Train the attention model:**
```bash
python src/persistent_memory/train_attention.py
```

---

### 3. **Dynamic Context Allocation**

Automatically allocate context budget based on query complexity:

```python
from persistent_memory.dynamic_context_allocator import DynamicContextAllocator

allocator = DynamicContextAllocator(max_tokens=4096)

# Allocate context based on query
allocation = allocator.allocate_context(
    query="Explain transformers in detail",
    available_contexts=retrieved_contexts
)

print(f"Allocated {allocation['total_tokens']} tokens")
print(f"Contexts selected: {len(allocation['contexts'])}")
```

**Features:**
- 📊 Complexity-aware allocation
- 🎯 Priority-based selection
- 📈 Adaptive budget management

---

### 4. **Context Quality Monitoring**

Monitor and ensure high-quality context retrieval:

```python
from persistent_memory.context_quality_monitor import ContextQualityMonitor

monitor = ContextQualityMonitor()

# Evaluate context quality
metrics = monitor.evaluate_context(
    query="What is attention?",
    retrieved_contexts=contexts,
    generated_response=response
)

print(f"Relevance: {metrics.relevance_score:.2f}")
print(f"Diversity: {metrics.diversity_score:.2f}")
print(f"Coverage: {metrics.coverage_score:.2f}")
```

**Metrics tracked:**
- 🎯 Relevance score
- 🌈 Diversity score
- 📊 Coverage score
- ⚠️ Hallucination detection

---

### 5. **Streaming Query Engine**

Stream results in real-time for better UX:

```python
from persistent_memory.streaming_query import StreamingQueryEngine

engine = StreamingQueryEngine(vector_store, knowledge_graph, llm)

# Stream results
async for phase in engine.stream_query("What is RAG?"):
    if phase['type'] == 'vector_search':
        print(f"Found {len(phase['results'])} relevant chunks")
    elif phase['type'] == 'knowledge_graph':
        print(f"Retrieved {len(phase['results'])} facts")
    elif phase['type'] == 'llm_response':
        print(f"Answer: {phase['text']}")
```

**Phases:**
1. Vector search results
2. Knowledge graph facts
3. LLM-generated answer

---

### 6. **Query Caching with Redis**

Cache frequent queries for instant responses:

```python
from persistent_memory.query_cache import QueryCache

cache = QueryCache(redis_url="redis://localhost:6379")

# Check cache first
cached = await cache.get("What is attention?")
if cached:
    return cached

# Generate and cache
response = generate_response(query)
await cache.set(query, response, ttl=3600)  # 1 hour TTL
```

**Benefits:**
- ⚡ Instant responses for repeated queries
- 💰 Reduced LLM API costs
- 📊 Hit/miss metrics tracking

---

### 7. **Batch Processing**

Process multiple documents efficiently:

```python
from persistent_memory.batch_processor import BatchProcessor

processor = BatchProcessor(
    vector_store=vs,
    knowledge_graph=kg,
    max_concurrent=5
)

# Process directory
results = await processor.process_directory(
    "./papers",
    file_pattern="*.txt"
)

print(f"Processed {results['successful']}/{results['total']} files")
```

**Features:**
- 🔄 Concurrent processing
- 🔁 Automatic retries
- 📊 Progress tracking

---

### 8. **Context Compression**

Compress old contexts to save space:

```python
from persistent_memory.context_autoencoder import ContextAutoencoder

autoencoder = ContextAutoencoder(compression_ratio=0.5)

# Compress old context
compressed = autoencoder.compress(old_context)
print(f"Reduced from {len(old_context)} to {len(compressed)} tokens")

# Decompress when needed
decompressed = autoencoder.decompress(compressed)
```

**Use cases:**
- 📦 Archive old conversations
- 💾 Reduce storage costs
- ⚡ Faster retrieval

---

### 9. **Fact Extraction**

Automatically extract structured facts from text:

```python
from persistent_memory.fact_extractor import FactExtractor

extractor = FactExtractor(llm_model, knowledge_graph)

# Extract facts from text
facts = extractor.extract_from_text(
    "Transformers use self-attention to process sequences in parallel."
)

for fact in facts['facts']:
    print(f"{fact['subject']} -> {fact['predicate']} -> {fact['object']}")
    # Output: Transformers -> use -> self-attention
```

**Extracted:**
- 📌 Entities
- 🔗 Relationships
- 🏷️ Topics

---

### 10. **Multi-User Context System**

Isolate context per user/session:

```python
from persistent_memory.multi_user_context_system import MultiUserContextSystem

system = MultiUserContextSystem()

# User-specific context
user_context = system.get_user_context(user_id="user123")
user_context.add_turn(user_input, assistant_response)

# Query with user context
response = system.query_with_context(
    user_id="user123",
    query="What did we discuss earlier?"
)
```

**Features:**
- 👥 Per-user isolation
- 🔒 Privacy-preserving
- 📊 User-specific analytics

---

## 🎯 Complete Example: Building a Research Assistant

Here's how to combine these techniques:

```python
import asyncio
from persistent_memory import (
    PersistentVectorStore,
    PersistentKnowledgeGraph,
    DataRepository,
    ArxivDownloader,
)
from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.streaming_query import StreamingQueryEngine
from persistent_memory.query_cache import QueryCache

async def research_assistant(query: str):
    """Complete research assistant with all techniques."""
    
    # 1. Initialize components
    vs = PersistentVectorStore()
    kg = PersistentKnowledgeGraph()
    repo = DataRepository()
    cache = QueryCache()
    
    # 2. Check cache first
    cached = await cache.get(query)
    if cached:
        return cached
    
    # 3. Use hierarchical attention for retrieval
    retrieval = AttentionEnhancedRetrieval(vs)
    contexts = retrieval.retrieve_with_attention(query, k=10)
    
    # 4. Stream response
    engine = StreamingQueryEngine(vs, kg, llm)
    response = ""
    
    async for phase in engine.stream_query(query):
        if phase['type'] == 'llm_response':
            response += phase['text']
            print(phase['text'], end='', flush=True)
    
    # 5. Cache result
    await cache.set(query, response, ttl=3600)
    
    return response

# Run
asyncio.run(research_assistant("What are the latest advances in transformers?"))
```

---

## 📊 Performance Optimization Tips

### 1. **Use Attention for Quality**
```python
# Better results with learned attention
retrieval = AttentionEnhancedRetrieval(vs)
contexts = retrieval.retrieve_with_attention(query, k=10)
```

### 2. **Cache Frequent Queries**
```python
# Save LLM costs
cache = QueryCache()
cached = await cache.get(query)
```

### 3. **Batch Process Documents**
```python
# Faster ingestion
processor = BatchProcessor(max_concurrent=10)
await processor.process_directory("./papers")
```

### 4. **Monitor Quality**
```python
# Ensure high-quality retrieval
monitor = ContextQualityMonitor()
metrics = monitor.evaluate_context(query, contexts, response)
```

### 5. **Compress Old Data**
```python
# Save storage
autoencoder = ContextAutoencoder()
compressed = autoencoder.compress(old_context)
```


---

## 🏗️ Project Structure

```
persistent-memory-models/
├── src/persistent_memory/     # Core library
│   ├── arxiv_downloader.py    # arXiv integration
│   ├── data_repository.py     # Paper caching
│   ├── conference_connector.py # Conference support
│   ├── hierarchical_attention.py # AI research
│   └── ...
├── demo_papers.py             # Paper demo
├── demo_conferences.py        # Conference demo
├── quick_demo.py              # Quick demo
├── requirements.txt           # Dependencies
├── docker-compose.yml         # Services
└── Makefile                   # Automation
```

---

## 🔧 Common Commands

### Development Workflow

```bash
# Format and lint code
make format-lint

# Run tests
make test

# Full quality check
make check

# Clean cache
make clean
```

### Docker Services

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Open shell in container
make shell
```

### Monitoring

```bash
# Show monitoring URLs
make metrics

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# Temporal UI: http://localhost:8088
```

---

## 📚 Available Demos

### 1. **Quick Demo** (`quick_demo.py`)
- Search arXiv
- Download & cache papers
- Show repository stats
- Access extracted text

**Run:**
```bash
python quick_demo.py
```

### 2. **Conference Demo** (`demo_conferences.py`)
- List supported conferences
- Fetch NeurIPS papers
- Fetch CVPR papers

**Run:**
```bash
python demo_conferences.py
```

### 3. **Paper Ingestion Demo** (`demo_papers.py`)
- Full ingestion workflow
- Hierarchical attention retrieval
- Baseline vs attention comparison

**Run:**
```bash
python demo_papers.py
```

---

## 🎓 Curated Paper Collections

Pre-selected important papers ready to ingest:

- **`attention_mechanisms`**: Transformer, Bahdanau, Luong
- **`rag_systems`**: RAG, REALM, DPR
- **`memory_networks`**: Memory Networks papers
- **`hierarchical_models`**: Hierarchical attention papers

**Ingest a collection:**
```bash
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
```

---

## 🏛️ Supported Conferences

- **NeurIPS** (Neural Information Processing Systems)
- **ICML** (International Conference on Machine Learning)
- **ICLR** (Learning Representations)
- **CVPR** (Computer Vision)
- **ACL** (Computational Linguistics)
- **SIGGRAPH** (Computer Graphics)

---

## 🐛 Troubleshooting

### Services not starting?
```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

### Dependencies missing?
```bash
pip install -r requirements.txt
```

### Ollama not working?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
brew services restart ollama
```

### ChromaDB errors?
```bash
# Install pydantic-settings
pip install pydantic-settings
```

### Module not found?
```bash
# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

---

## 📖 Documentation

- **[COMMANDS.md](COMMANDS.md)** - CLI commands reference
- **[QUICKSTART.md](QUICKSTART.md)** - Detailed quickstart
- **[MAKEFILE_COMMANDS.md](MAKEFILE_COMMANDS.md)** - Makefile reference
- **[DEPENDENCIES.md](docs/DEPENDENCIES.md)** - Dependency management
- **[OLLAMA_INTEGRATION.md](docs/OLLAMA_INTEGRATION.md)** - LLM setup
- **[HIERARCHICAL_ATTENTION.md](docs/research/HIERARCHICAL_ATTENTION.md)** - Research paper

---

## 🎯 Recommended First Steps

1. **Start services**: `make up`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run quick demo**: `python quick_demo.py`
4. **Search papers**: `python -m persistent_memory.cli search-papers "transformers"`
5. **Download a paper**: `python -m persistent_memory.repo_cli get 1706.03762`
6. **Check stats**: `python -m persistent_memory.repo_cli stats`

---

## 💡 Pro Tips

1. **Use `make format-lint`** before every commit
2. **Check `make metrics`** for monitoring URLs
3. **Run `make check`** before pushing
4. **Use curated collections** for quick demos
5. **Set `PYTHONPATH`** if you get import errors:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)/src
   ```

---

## 🆘 Need Help?

- Check the **[DEMO_OUTPUT.md](DEMO_OUTPUT.md)** to see what commands do
- Review **[MAKEFILE_COMMANDS.md](MAKEFILE_COMMANDS.md)** for all available commands
- Look at **[docs/](docs/)** for detailed documentation

---

**You're ready to go! Start with `python quick_demo.py` 🚀**
