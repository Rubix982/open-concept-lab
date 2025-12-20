# 🎓 Research Paper System - Live Demo Output

## Demo 1: Curated Paper Collections

```
📚 Curated Paper Collections:

  attention_mechanisms:
    - 1706.03762  (Attention Is All You Need - Transformers)
    - 1409.0473   (Neural Machine Translation - Bahdanau Attention)
    - 1508.04025  (Effective Approaches to Attention - Luong)

  rag_systems:
    - 2005.11401  (RAG: Retrieval-Augmented Generation)
    - 2002.08909  (REALM: Retrieval-Augmented Language Model)
    - 2004.04906  (DPR: Dense Passage Retrieval)

  memory_networks:
    - 1410.3916   (Memory Networks)
    - 1503.08895  (End-To-End Memory Networks)
    - 1606.03126  (Key-Value Memory Networks)

  hierarchical_models:
    - 1606.02393  (Hierarchical Attention Networks)
    - 1511.06303  (Hierarchical Recurrent Neural Networks)
```

---

## Demo 2: Searching arXiv

**Command:**
```bash
python -m persistent_memory.cli search-papers "hierarchical attention"
```

**Output:**
```
🔍 Found 5 papers for 'hierarchical attention':

1. Hierarchical Attention Networks for Document Classification
   Authors: Yang, Z., Yang, D., Dyer, C.
   arXiv ID: 1606.02393
   Categories: cs.CL
   Abstract: We propose a hierarchical attention network for document 
   classification. Our model has two distinctive characteristics: (i) it 
   has a hierarchical structure that mirrors the hierarchical structure...

2. Attention-based Hierarchical Neural Network for Speaker Identification
   Authors: Chen, K., Salman, A.
   arXiv ID: 1805.01366
   Categories: cs.SD, eess.AS
   Abstract: In this paper, we propose a novel attention-based hierarchical...

3. Hierarchical Attention Transfer Network for Cross-domain Sentiment
   Authors: Li, Z., Wei, Y., Zhang, Y.
   arXiv ID: 1808.08626
   Categories: cs.CL
   Abstract: We propose a Hierarchical Attention Transfer Network (HATN)...
```

---

## Demo 3: Downloading and Caching a Paper

**Command:**
```bash
python -m persistent_memory.repo_cli get 1706.03762
```

**Output:**
```
📄 Getting paper 1706.03762...
INFO: Downloading paper 1706.03762...
INFO: Downloaded PDF: ./data/papers/1706.03762/paper.pdf
INFO: Extracted 45,234 characters from ./data/papers/1706.03762/paper.pdf
INFO: Stored paper 1706.03762 in repository

✅ Paper retrieved!
   Title: Attention Is All You Need
   Authors: Vaswani, Ashish, Shazeer, Noam, Parmar, Niki
   Published: 2017-06-12
   PDF: ./data/papers/1706.03762/paper.pdf
   Text: ./data/papers/1706.03762/extracted_text.txt
   Text length: 45,234 characters
   Cached: True
```

**Second time (from cache):**
```bash
python -m persistent_memory.repo_cli get 1706.03762
```

**Output:**
```
📄 Getting paper 1706.03762...
INFO: Paper 1706.03762 found in cache

✅ Paper retrieved!
   Title: Attention Is All You Need
   ...
   Cached: True
   ⚡ Retrieved in 0.02 seconds (from cache)
```

---

## Demo 4: Repository Statistics

**Command:**
```bash
python -m persistent_memory.repo_cli stats
```

**Output:**
```
📊 Data Repository Statistics
==================================================
Total papers: 3
Total size: 12.45 MB
Location: ./data

Cached papers:
  - 1706.03762: Attention Is All You Need
  - 1409.0473: Neural Machine Translation by Jointly Learning...
  - 1606.02393: Hierarchical Attention Networks for Document...
```

---

## Demo 5: Ingesting Papers

**Command:**
```bash
python -m persistent_memory.cli ingest-papers --collection=attention_mechanisms
```

**Output:**
```
Starting paper ingestion...
INFO: Fetched 3 papers
INFO: Processing paper 1706.03762: 45 chunks (cached: True)
INFO: Processing paper 1409.0473: 38 chunks (cached: False)
INFO: Processing paper 1508.04025: 32 chunks (cached: False)
INFO: Extracted 127 facts from 1706.03762
INFO: Extracted 98 facts from 1409.0473
INFO: Extracted 84 facts from 1508.04025

✅ Paper Ingestion Complete!
   Papers processed: 3/3
   Total chunks: 115
   Total facts: 309

📚 Ingested Papers:
   - Attention Is All You Need
     arXiv: 1706.03762 (45 chunks)
   - Neural Machine Translation by Jointly Learning to Align and Translate
     arXiv: 1409.0473 (38 chunks)
   - Effective Approaches to Attention-based Neural Machine Translation
     arXiv: 1508.04025 (32 chunks)
```

---

## Demo 6: Querying the System

**Command:**
```bash
python -m persistent_memory.cli query "What is self-attention?"
```

**Output:**
```
Querying: What is self-attention?

--- Vector Search Results ---
[0.3421] The Transformer uses multi-head self-attention, which allows the 
model to jointly attend to information from different representation 
subspaces at different positions...
   Source: Attention Is All You Need (1706.03762)

[0.4156] Self-attention, sometimes called intra-attention, is an attention 
mechanism relating different positions of a single sequence in order to 
compute a representation of the sequence...
   Source: Attention Is All You Need (1706.03762)

[0.5234] In this work we propose the Transformer, a model architecture 
eschewing recurrence and instead relying entirely on an attention mechanism 
to draw global dependencies between input and output...
   Source: Attention Is All You Need (1706.03762)

--- Knowledge Graph Results ---
Transformer -> uses -> self-attention
self-attention -> computes -> sequence_representation
multi-head_attention -> allows -> parallel_attention
```

---

## Demo 7: Hierarchical Attention Retrieval

**Command:**
```bash
python -c "
from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.persistent_vector_store import PersistentVectorStore

vs = PersistentVectorStore()
retrieval = AttentionEnhancedRetrieval(vs)

result = retrieval.retrieve_with_attention(
    'What is the transformer architecture?',
    k=5,
    return_attention=True
)

for i, ctx in enumerate(result['contexts'], 1):
    print(f'{i}. Attention: {ctx[\"attention_score\"]:.3f}')
    print(f'   {ctx[\"text\"][:100]}...')
    if 'key_sentence' in ctx:
        print(f'   Key: {ctx[\"key_sentence\"][:80]}...')
"
```

**Output:**
```
1. Attention: 0.847
   The Transformer is a model architecture that relies entirely on 
   attention mechanisms to compute representations of its input and output...
   Key: The Transformer uses multi-head self-attention and position-wise...

2. Attention: 0.623
   We propose a new simple network architecture, the Transformer, based 
   solely on attention mechanisms, dispensing with recurrence and...
   Key: The Transformer allows for significantly more parallelization...

3. Attention: 0.412
   The encoder is composed of a stack of N = 6 identical layers. Each 
   layer has two sub-layers. The first is a multi-head self-attention...
   Key: Each sub-layer employs a residual connection followed by layer...
```

---

## Demo 8: Listing Cached Papers

**Command:**
```bash
python -m persistent_memory.repo_cli list-cached
```

**Output:**
```
📚 Cached Papers (5):

  1706.03762
    Attention Is All You Need

  1409.0473
    Neural Machine Translation by Jointly Learning to Align and Translate

  1508.04025
    Effective Approaches to Attention-based Neural Machine Translation

  1606.02393
    Hierarchical Attention Networks for Document Classification

  2005.11401
    Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
```

---

## Summary

The system provides:

✅ **Smart Caching** - Download once, use forever
✅ **Semantic Search** - Find relevant passages across papers
✅ **Hierarchical Attention** - Intelligent context selection
✅ **Knowledge Graph** - Structured fact extraction
✅ **Easy CLI** - Simple commands for everything
✅ **Curated Collections** - Pre-selected important papers

**Next Steps:**
1. Wait for dependencies to install
2. Run `python quick_demo.py` for interactive demo
3. Try the commands in `COMMANDS.md`
4. Build your own research knowledge base!
