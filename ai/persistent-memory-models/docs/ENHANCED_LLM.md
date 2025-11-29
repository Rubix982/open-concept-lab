# Enhanced LLM - Production Chatbot with Persistent Memory

## 🎯 What Is This?

This is a **complete, working chatbot** that takes an open-source LLM (like Mistral via Ollama) and **fundamentally enhances it** with advanced AI techniques.

## 🚀 Quick Start

### 1. Start Ollama
```bash
brew services start ollama
ollama pull mistral
```

### 2. Start Services (Optional - for full features)
```bash
make up  # Starts Docker services (ChromaDB, Redis, etc.)
```

### 3. Run the Chatbot
```bash
python chatbot.py
```

---

## 💡 How It Enhances the Base Model

The `EnhancedLLM` class wraps a base LLM (Mistral, Llama2, etc.) and adds:

### 1. **Persistent Memory** 🧠
- **Base Model**: Forgets everything after the conversation
- **Enhanced**: Remembers ALL past conversations forever
- **Implementation**: Vector store (ChromaDB) + Knowledge graph (NetworkX)

### 2. **Hierarchical Attention** 🔬
- **Base Model**: Uses simple similarity search for context
- **Enhanced**: Uses multi-level attention to find the BEST context
- **Implementation**: `HierarchicalAttentionNetwork` with chunk + sentence attention

### 3. **Dynamic Context Allocation** 🎯
- **Base Model**: Fixed context window
- **Enhanced**: Adapts context budget based on query complexity
- **Implementation**: `DynamicContextAllocator` with complexity analysis

### 4. **Quality Monitoring** 📊
- **Base Model**: No quality checks
- **Enhanced**: Monitors relevance, diversity, coverage, hallucination risk
- **Implementation**: `ContextQualityMonitor` with real-time metrics

### 5. **Query Caching** ⚡
- **Base Model**: Recomputes every query
- **Enhanced**: Caches frequent queries for instant responses
- **Implementation**: Redis-based `QueryCache` with TTL

### 6. **Fact Extraction & Learning** 🔍
- **Base Model**: Doesn't learn from conversations
- **Enhanced**: Extracts facts and builds knowledge graph over time
- **Implementation**: `FactExtractor` with automatic knowledge graph updates

---

## 🏗️ Architecture

```
User Query
    ↓
┌─────────────────────────────────────────┐
│         Enhanced LLM Pipeline           │
├─────────────────────────────────────────┤
│ 1. Check Cache (Redis)                  │ ← Instant if cached
│ 2. Retrieve Context (Hierarchical Attn) │ ← Smart retrieval
│ 3. Allocate Budget (Dynamic)            │ ← Adaptive
│ 4. Generate Response (Base LLM)         │ ← Mistral/Llama
│ 5. Monitor Quality                      │ ← Validation
│ 6. Extract Facts                        │ ← Learning
│ 7. Store in Memory                      │ ← Persistence
│ 8. Cache Result                         │ ← Future speedup
└─────────────────────────────────────────┘
    ↓
Enhanced Response
```

---

## 📊 Performance Comparison

| Feature | Base Mistral | Enhanced LLM |
|---------|--------------|--------------|
| **Memory** | None (forgets) | Persistent (remembers forever) |
| **Context Selection** | Simple similarity | Hierarchical attention |
| **Context Budget** | Fixed 4K tokens | Dynamic (adapts to complexity) |
| **Quality Checks** | None | Real-time monitoring |
| **Caching** | None | Redis-based |
| **Learning** | Static | Learns from conversations |
| **Latency (cached)** | ~2-3s | **~0.1s** ⚡ |
| **Latency (uncached)** | ~2-3s | ~3-4s (worth it for quality) |

---

## 🎮 Usage Examples

### Basic Chat
```python
from persistent_memory.enhanced_llm import EnhancedLLM

bot = EnhancedLLM(model="mistral")
response = await bot.chat("What is a transformer?")
print(response)
```

### With Metadata
```python
result = await bot.chat(
    "Explain attention mechanisms",
    return_metadata=True
)

print(f"Response: {result['response']}")
print(f"Latency: {result['latency']:.2f}s")
print(f"Quality: {result['quality_metrics']['relevance_score']:.3f}")
```

### Teaching the Bot
```python
await bot.teach(
    "Transformers use self-attention to process sequences in parallel.",
    source="research_paper"
)
```

### Get Statistics
```python
stats = bot.get_stats()
print(f"Conversations: {stats['conversation_turns']}")
print(f"Cache hit rate: {stats['cache']['hit_rate']:.1%}")
```

---

## 🔧 Configuration

### Enable/Disable Features
```python
bot = EnhancedLLM(
    model="mistral",
    enable_cache=True,              # Query caching
    enable_attention=True,          # Hierarchical attention
    enable_quality_monitoring=True, # Quality checks
    max_context_tokens=4096,        # Context budget
)
```

### Use Different Models
```python
# Mistral (default)
bot = EnhancedLLM(model="mistral")

# Llama 2
bot = EnhancedLLM(model="llama2")

# Llama 3
bot = EnhancedLLM(model="llama3")

# Any Ollama model
bot = EnhancedLLM(model="codellama")
```

---

## 🎯 Real-World Use Cases

### 1. Customer Support Bot
```python
# Learns from past support tickets
await bot.teach(support_ticket_text, source="ticket_12345")

# Provides consistent, informed responses
response = await bot.chat("How do I reset my password?")
```

### 2. Research Assistant
```python
# Ingest research papers
await bot.teach(paper_text, source="arxiv:1706.03762")

# Answer questions with citations
result = await bot.chat(
    "What are the key innovations in transformers?",
    return_metadata=True
)
```

### 3. Personal Knowledge Base
```python
# Store personal notes
await bot.teach("Meeting notes: Project deadline is Dec 15", source="notes")

# Recall later
response = await bot.chat("When is the project deadline?")
```

---

## 📈 Metrics & Monitoring

The Enhanced LLM tracks:

- **Conversation Metrics**: Total turns, session IDs
- **Cache Metrics**: Hit rate, miss rate, latency savings
- **Quality Metrics**: Relevance, diversity, coverage, hallucination risk
- **Memory Metrics**: Total facts stored, knowledge graph size

Access via:
```python
stats = bot.get_stats()
```

---

## 🚀 Production Deployment

### Docker Compose
```yaml
services:
  chatbot:
    build: .
    environment:
      - OLLAMA_HOST=http://ollama:11434/v1
      - REDIS_URL=redis://redis:6379
      - CHROMA_HOST=vector-db
    depends_on:
      - ollama
      - redis
      - vector-db
```

### Environment Variables
```bash
export OLLAMA_HOST=http://localhost:11434/v1
export REDIS_URL=redis://localhost:6379
export CHROMA_HOST=localhost
export CHROMA_PORT=8000
```

---

## 🔬 Technical Details

### Memory Layers
1. **Working Memory**: Current conversation (in-memory list)
2. **Episodic Memory**: Past conversations (ChromaDB vector store)
3. **Semantic Memory**: Extracted facts (NetworkX knowledge graph)
4. **Cache**: Frequent queries (Redis)

### Retrieval Pipeline
1. **Vector Search**: Find similar past conversations
2. **Attention Scoring**: Rank by multi-level attention
3. **Budget Allocation**: Select top contexts within token limit
4. **Context Injection**: Add to prompt

### Quality Assurance
1. **Relevance**: Cosine similarity between query and contexts
2. **Diversity**: Uniqueness of selected contexts
3. **Coverage**: How well contexts cover the query
4. **Hallucination**: Overlap between response and contexts

---

## 🎓 Research Papers Implemented

This system implements techniques from:

1. **"Attention Is All You Need"** (Vaswani et al., 2017)
   - Multi-head attention mechanism

2. **"Hierarchical Attention Networks"** (Yang et al., 2016)
   - Multi-level attention for document classification

3. **"Retrieval-Augmented Generation"** (Lewis et al., 2020)
   - Combining retrieval with generation

4. **"Memory Networks"** (Weston et al., 2014)
   - Persistent memory for question answering

---

## 💡 Why This Matters

**Base LLMs are stateless and forgetful.** They're like having a conversation with someone who has amnesia - every message is brand new to them.

**The Enhanced LLM gives the model a brain.** It can:
- Remember past conversations
- Learn from new information
- Improve over time
- Provide consistent, informed responses
- Cite sources and facts

This is the difference between a **chatbot** and an **AI assistant**.

---

## 🚧 Future Enhancements

- [ ] Multi-user support with isolated contexts
- [ ] Automatic knowledge consolidation
- [ ] Context archiving for old memories
- [ ] Fine-tuning on conversation history
- [ ] Multi-modal support (images, audio)
- [ ] Federated learning across instances

---

## 📚 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup guide
- **[COMMANDS.md](COMMANDS.md)** - CLI reference
- **[docs/HIERARCHICAL_ATTENTION.md](docs/research/HIERARCHICAL_ATTENTION.md)** - Research paper

---

## 🤝 Contributing

Want to improve the Enhanced LLM? Areas to explore:

1. **Better Fact Extraction**: Improve accuracy of knowledge graph
2. **Smarter Caching**: Semantic caching instead of exact match
3. **Context Compression**: Compress old memories to save space
4. **Multi-hop Reasoning**: Chain facts from knowledge graph
5. **Personalization**: Adapt to individual user preferences

---

**Built with ❤️ using production-grade AI techniques**
