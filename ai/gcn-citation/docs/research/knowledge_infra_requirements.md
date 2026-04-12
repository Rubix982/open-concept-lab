# Research Knowledge Infrastructure — Requirements

**Date**: 2026-04-12
**Status**: Active — Phase 1 planning
**Domain**: AI, Machine Learning, Deep Learning, Computer Vision, Statistics
**Relation to prior work**: The arXiv pipeline and GNN models in this repo are the
technical foundation for this system. Papers are now inputs, not nodes.

---

## Problem

Existing tools (Semantic Scholar, Connected Papers, Elicit) work at the citation
level. A citation says "this paper referenced that paper" — not what specific idea
was borrowed, whether it was used to support or contradict a claim, or how an
idea evolved across years of literature.

Research in AI/ML is especially siloed: the same idea — attention, contrastive
learning, diffusion, message passing — appears independently across NLP, CV,
RL, and graph learning with different vocabulary, different citations, and no
visible lineage connecting them.

**What this system builds toward:** a queryable map of what ideas exist in the
AI/ML literature, what they are built on, where they contradict each other, and
where the same idea surfaced in a different field.

---

## The Atomic Unit

**Idea node** — the smallest discrete claim that can stand alone and be built upon.

Papers are containers. Citations are weak pointers. The dependency graph underneath
is what we are building.

These questions become answerable:
- Which papers challenge this claim?
- Has anyone applied this method to that problem?
- Where did batch normalization originate and how has the justification evolved?
- What is the strongest counterevidence to the "scaling laws" hypothesis?
- Which computer vision claims are restatements of earlier NLP results?

---

## Architecture: Four-Layer Memory Model

```
Layer 4 — Conceptual / Meta
    Inferred patterns across L3 facts. Not in any single source.
    "Methods that consistently outperform baselines on long-range tasks
    share property X." Updated as a batch job, not in real time.

Layer 3 — Semantic Facts  ← PRIMARY QUERY TARGET
    Discrete claims extracted from papers. Deduplicated and confidence-
    scored across sources. Typed edges: supports, contradicts, extends,
    replicates-in-domain.
    Schema: { claim, type, domain, method, metric, value, conditions,
              epistemic_status, source_papers[], confidence }

Layer 2 — Episodic (Paper-level)
    One record per paper: what was studied, how, what was found.
    Answers "find papers that worked on X."
    Schema: { title, abstract, contribution, method, datasets,
              key_findings, limitations, domain_tags }

Layer 1 — Raw Chunks
    Exact source text. High fidelity, no interpretation.
    Retrieved only when grounding a specific claim requires primary
    source precision.
```

**Retrieval flow:**
```
Query → Router (classify intent)
  → L3 semantic fact search         (factual questions)
  → L2 episodic lookup for context  (exploratory questions)
  → L4 meta check for patterns      (synthesis questions)
  → L1 raw fetch if grounding needed (verification)
```

---

## Domain-Specific Schema: AI/ML/DL/CV/Statistics

### L3 Claim Node

```json
{
  "id": "uuid",
  "claim_type": "empirical | theoretical | architectural | comparative | observation",
  "assertion": "The claim in plain English, self-contained.",
  "domain": "NLP | CV | RL | optimization | theory | graph_learning | statistics | ...",
  "method": "Name of technique, architecture, or algorithm being described.",
  "dataset": "Dataset name if applicable, null otherwise.",
  "metric": "Accuracy | F1 | BLEU | FID | perplexity | ... | null",
  "value": "Numeric result as string (e.g. '94.5%'), null if non-numeric.",
  "conditions": "Experimental conditions that qualify this claim.",
  "epistemic_status": "established | preliminary | contested | ungrounded",
  "source_papers": ["arxiv_id_1", "arxiv_id_2"],
  "confidence": 0.0,
  "created_at": "ISO timestamp",
  "last_updated": "ISO timestamp"
}
```

### Claim Types for AI/ML

| Type | Example |
|---|---|
| `empirical` | "GPT-4 achieves 86.4% on MMLU under 5-shot evaluation." |
| `theoretical` | "SGD with momentum converges to a stationary point under L-smoothness." |
| `architectural` | "The transformer encoder uses multi-head self-attention with residual connections." |
| `comparative` | "Attention-based models outperform RNNs on tasks requiring long-range dependencies." |
| `observation` | "Larger language models exhibit emergent capabilities not present at smaller scale." |

### L3 Edge Types

| Edge | Definition | Example |
|---|---|---|
| `supports` | Second claim provides evidence for first | Scaling law → emergent capabilities |
| `contradicts` | Claims assert incompatible outcomes under similar conditions | "Dropout prevents overfit" ↔ "Dropout hurts small datasets" |
| `extends` | Second generalizes or builds on first | BERT → RoBERTa (same arch, different training) |
| `replicates_in_domain` | Same idea, different field — cross-disciplinary connection | Attention (NLP) → Attention (CV, ViT) |
| `requires` | First claim depends on second being true | Transformer performance → Attention mechanism |
| `refines` | Second adds precision or conditions to first | "Batch norm helps" → "Batch norm helps when batch size > 32" |

### Epistemic Status Rules

| Status | Definition |
|---|---|
| `established` | Multiple independent sources, reproduced across datasets, no significant contradiction |
| `preliminary` | 1-2 sources, narrow conditions, or very recent |
| `contested` | Conflicting evidence in corpus, active disagreement |
| `ungrounded` | LLM assertion with no traceable source in corpus — flagged, not silently included |

**Key invariant:** contradiction is a first-class data structure, not a failure state.

### L2 Paper Summary Schema

```json
{
  "arxiv_id": "string",
  "title": "string",
  "contribution": "One sentence: what this paper contributes.",
  "method": "What approach/architecture/technique was used.",
  "datasets": ["dataset_name_1", "dataset_name_2"],
  "key_findings": ["finding_1", "finding_2", "finding_3"],
  "limitations": "Known limitations or scope constraints.",
  "domain_tags": ["NLP", "transformers", "language_modeling"],
  "related_methods": ["BERT", "GPT", "T5"],
  "extracted_at": "ISO timestamp",
  "extraction_model": "claude-sonnet-4-6"
}
```

---

## Technical Stack

```
Data source        arXiv pipeline (already built)
                   SPECTER2 embeddings (already built)

Embedding model    allenai/specter2 — already integrated
                   Used at L1, L2, L3 for vector indexing

Extraction model   Claude API (claude-sonnet-4-6) as teacher
(Phase 1-2)        Called per paper at ingest time
                   Structured JSON output (tool use)

Extraction model   Small local LLM fine-tuned on teacher output
(Phase 3)          3B–8B class, runs locally on MPS
                   Student replacing API calls at scale

NLI classifier     BERT-class model for contradiction/support
                   edge classification between claim pairs

Storage            DuckDB — all structured data (L2, L3 nodes + edges)
                   Numpy mmap — L1 and L3 embedding arrays
                   FAISS (standalone process) — vector index for search

Query API          Python FastAPI or simple CLI
                   Returns claims with provenance + epistemic markers
```

---

## AI Stack Decision: Teacher → Student Distillation

1. Use **Claude API** (claude-sonnet-4-6) to extract L2 summaries and L3 claims
   from the first **500 papers** — this is the teacher
2. Teacher output becomes **labeled training data**
3. Fine-tune a small local model (e.g. Qwen2.5-3B or Llama-3.2-3B) on that data
4. Student runs locally at scale, cheaply and privately

This bootstraps the system without requiring a pre-labeled dataset.

---

## Data Source Strategy

**Starting corpus**: 500 papers from our existing 10K arXiv dataset
(cs.AI, cs.LG, cs.CV, cs.CL, stat.ML — already embedded with SPECTER2)

**Filter for quality**: prefer papers from 2018–2024 with >50 citations
(proxy for significance; use Semantic Scholar citation count via API)

**Ingest order**: 50 papers first to validate schema design → 500 for teacher
dataset → scale as needed

---

## Phase Plan

### Phase 1: L1 + L2 Pipeline (2–3 weekends)

*Goal: prove paper-level retrieval works.*

- [ ] DuckDB schema for L1 chunks and L2 summaries
- [ ] Paper text extraction (arXiv abstract + sections via PDF or abstract-only first)
- [ ] L1 chunking + SPECTER2 embedding → DuckDB + mmap index
- [ ] L2 extraction prompt (Claude API → structured JSON per paper)
- [ ] Store L2 summaries in DuckDB
- [ ] Basic query: "find papers about X" → L2 semantic search → formatted output

**Done when**: can answer "what papers studied batch normalization in transformers?"
with proper citations and brief summaries.

---

### Phase 2: L3 Claim Extraction (3–4 weekends)

*Goal: extract discrete claims and type the edges between them.*

- [ ] Finalize L3 claim schema for AI/ML domain
- [ ] L3 extraction prompt (Claude API, per paper section)
- [ ] Claim deduplication: SPECTER2 similarity pre-filter → LLM confirmation
- [ ] Epistemic classification: assign status at ingest, update on contradiction
- [ ] Edge classification: NLI model for supports/contradicts/extends/replicates
- [ ] Store claim nodes + edges in DuckDB
- [ ] Query: "which claims contradict the scaling laws hypothesis?"

**Done when**: can answer a claim-level question with provenance and epistemic status
across 50 papers.

---

### Phase 3: Local Fine-Tuning (3–4 weekends)

*Goal: replace API calls with local inference.*

- [ ] Build labeled dataset from Phase 2 teacher output (L2 + L3 extractions)
- [ ] Fine-tune small local model (3B–8B) on extraction schema
- [ ] Evaluate: student vs teacher accuracy on held-out papers
- [ ] Replace API calls with local model for bulk ingest
- [ ] Add NLI classifier for contradiction detection

---

### Phase 4: GNN Pre-training Over Claim Graph (future)

*This is where gcn-citation work applies directly.*

- [ ] Once L3 graph has 5K+ claim nodes with typed edges
- [ ] Pre-train GraphMAE over claim nodes (embeddings = SPECTER2 + fine-tuned extraction)
- [ ] Frozen encoder + GPF-plus prompting for multi-task queries
- [ ] Tasks: claim classification by type, link prediction for missing edges,
        cross-domain replication detection (Goal 1 from original research)

---

## Open Questions

| Question | Impact | Phase |
|---|---|---|
| Abstract-only vs full PDF extraction for L1/L2? | Coverage vs cost | Phase 1 |
| Which 3B-8B model for fine-tuning? (Qwen2.5-3B vs Llama-3.2-3B vs Phi-3.5) | Phase 3 quality | Phase 2 |
| NLI model selection for contradiction detection | Edge quality | Phase 2 |
| Citation count API for quality filtering? | Starting corpus quality | Phase 1 |
| Query interface: CLI first or FastAPI from the start? | Scope | Phase 1 |

---

## What This Is NOT

- Not a paper recommendation engine
- Not a RAG system over raw PDFs
- Not trying to replace researchers — the goal is to surface connections they miss
- Not real-time — extraction runs at ingest time, not at query time

---

## Connection to gcn-citation Codebase

```
src/gcn_citation/pipeline/     ← data source (keep as-is)
  arxiv_bulk.py                   papers → DataFrame
  embedder.py                     SPECTER2 embeddings
  citations.py                    OpenAlex citation edges

src/knowledge/                 ← NEW: knowledge infrastructure
  schema.py                       DuckDB table definitions
  ingest.py                       L1 chunking + indexing
  extract_l2.py                   Paper → L2 summary (Claude API)
  extract_l3.py                   Sections → L3 claim nodes (Claude API)
  deduplicate.py                  Claim identity + merge logic
  classify.py                     Epistemic status + edge typing
  query.py                        Query router + retrieval
```

DuckDB database: `data/knowledge/knowledge.duckdb`
Embeddings: `data/knowledge/embeddings_l1.npy`, `data/knowledge/embeddings_l3.npy`
