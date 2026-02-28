# Research Knowledge Infrastructure - Vision, Architecture, and Design Rationale

- [Research Knowledge Infrastructure - Vision, Architecture, and Design Rationale](#research-knowledge-infrastructure---vision-architecture-and-design-rationale)
  - [Problem Statement](#problem-statement)
    - [Why This Matters](#why-this-matters)
  - [Goal](#goal)
  - [Architecture](#architecture)
    - [Four-Layer Memory Model](#four-layer-memory-model)
    - [Human Analogy for Each Layer](#human-analogy-for-each-layer)
    - [Technical Requirements Per Layer](#technical-requirements-per-layer)
      - [Layer 1](#layer-1)
      - [Layer 2](#layer-2)
      - [Layer 3](#layer-3)
      - [Layer 4](#layer-4)
      - [Claim Identity and Edge Classification](#claim-identity-and-edge-classification)
    - [The Full AI Stack](#the-full-ai-stack)
    - [Fine-Tuning and the Data Flywheel](#fine-tuning-and-the-data-flywheel)
    - [Build Sequence](#build-sequence)
    - [Epistemic Classification](#epistemic-classification)
  - [Build Order](#build-order)
  - [Honest Constraints](#honest-constraints)

---

## Problem Statement

Researchers spend enormous time doing what is essentially manual graph traversal — reading a paper, following citations, finding related work, holding connections in working memory, synthesizing across sources. This process is slow, lossy, and does not scale beyond what one person can hold in their head at once.

It is not that there is not an abundant research related to a target problem or area, the problem is that it is hard to connect evidence across them efficiently.

Existing tools — Connected Papers, Semantic Scholar, Elicit, ResearchRabbit — operate at the citation level. A citation only means "this paper referenced that paper." It says nothing about why, what specifically was borrowed, whether it was used to support or contradict a claim, or how an idea evolved across years of literature.

### Why This Matters

Research is siloed in ways that are not just linguistic or geographic — they are structural. A team working on a problem may be unaware that a foundational piece of it was solved elsewhere years prior, because citation graphs do not surface that connection at the right granularity.

What this system builds toward is **intellectual infrastructure**: a queryable map of what ideas exist, what they are built on, and where they are being taken. Starting with research literature, scoped carefully, built with rigor.

---

## Goal

Build infrastructure that captures research knowledge at its lowest granularity — discrete ideas and the dependency relationships between them — and makes those relationships queryable.

The atomic unit is an **idea node**: the smallest discrete concept that can stand alone and be built upon. Papers are containers. Citations are weak pointers. The goal is the dependency graph underneath both.

This makes the intellectual lineage of an idea visible and traversable:

- Which papers challenge this claim?
- Has anyone applied this method to that problem?
- Where did this idea originate and how has it evolved?
- What is the strongest counterevidence to this hypothesis?
- What foundational work does this result depend on?

These are graph traversal questions. No current tool answers them at the claim level.

---

## Architecture

### Four-Layer Memory Model

Rather than flat vector retrieval (top-k chunks), the system is organized into four distinct memory layers, each operating at a different level of abstraction. Retrieval cascades through layers depending on query type.

```
Layer 4 — Conceptual / Meta
    Derived patterns across many papers. Not extracted from any single source
    but inferred across the corpus. "Methods that consistently outperform
    baselines on X share property Y." Updated incrementally.

Layer 3 — Semantic Facts
    Structured claims extracted from papers. Deduplicated and confidence-scored
    across sources. The primary query target for factual questions.
    Schema: { claim, evidence, metric, value, source_papers[], confidence }

Layer 2 — Episodic (Paper-level)
    One record per paper capturing its narrative context: what was studied,
    how, and what was found. Answers "find papers that worked on X."

Layer 1 — Raw Chunks
    Exact source text. High fidelity, no interpretation. Retrieved only when
    grounding a specific claim requires primary source precision.
```

**Retrieval flow:**

```
Query → Router (classify query type)
  → L3 semantic fact search
  → L2 episodic lookup for context
  → L4 meta check for known patterns
  → L1 raw fetch only if grounding required
```

The query router classifies intent — factual, exploratory, grounding, synthesis — and determines which layers to engage and in what order.

---

### Human Analogy for Each Layer

A precise way to understand what each layer represents, using a concrete example of learning a programming language from a book:

**Layer 1 — Memorization.** Reading a book and memorizing it word for word. Given a phrase, you can confirm whether it existed in the text and point to exactly where. But memorization is not understanding. The only guarantee is that the exact words and their order are preserved. No interpretation, no growth, no reasoning.

**Layer 2 — Understanding (Episodic).** Reading two different C language books. Both teach the same syntax, but you now have two distinct episodes — two reading experiences that produced the same underlying understanding. The layer captures context and narrative: what was studied, how it was approached, what was learned. Two papers on the same topic produce two L2 records but may converge on the same L3 facts.

**Layer 3 — Knowledge (Semantic).** The actual representation of what C syntax is — decoupled from which book taught it. This is the distilled fact, independent of its source. If ten papers assert the same claim, it lives as one L3 node with ten sources. This layer is what the system primarily reasons over.

**Layer 4 — Meta-Knowledge (Conceptual).** Abstract patterns inferred across many L3 facts. For example: constructs from one programming language map onto another in predictable ways. Not stated in any single source — emergent from the corpus as a whole. This is the layer that enables genuine synthesis rather than retrieval.

---

### Technical Requirements Per Layer

Each layer requires distinct AI techniques. They are not interchangeable.

#### Layer 1

**Layer 1** uses standard dense retrieval — chunk, embed, store in a vector index. No LLM needed at query time. Model required: any capable embedding model (`bge-m3`, `nomic-embed-text`).

#### Layer 2

**Layer 2** uses structured extraction via a prompted LLM, once per paper at ingest time. The paper is passed to the model with a fixed schema to fill. Model required: any capable instruction-following model, 7B–8B class. Key technique: structured output generation (JSON mode).

#### Layer 3

**Layer 3** is the hardest layer. Three sub-problems must be solved:

- _Extraction_ — prompt the LLM per paper section to pull discrete claims in structured form
- _Deduplication_ — embedding similarity pre-filter followed by LLM confirmation: "are these the same claim?" This is entity resolution applied to ideas
- _Epistemic classification_ — assign status based on cross-paper agreement and contradiction detection

Model required: a small model (3B–8B) fine-tuned specifically on your extraction schema. General models are too inconsistent for structured extraction at scale. A dedicated NLI (Natural Language Inference) classifier handles contradiction detection between claims.

#### Layer 4

**Layer 4** runs as a batch job, not real-time. Two steps: cluster L3 fact embeddings by similarity (HDBSCAN or k-means), then pass each cluster to a reasoning-capable LLM asking what general principle the cluster suggests. Model required: a larger reasoning model, called infrequently.

#### Claim Identity and Edge Classification

The deduplication problem at L3 is not a pure semantic similarity problem. Two claims can be semantically close but epistemically divergent — collapsing them destroys exactly the information the system is built to preserve.

Claim identity is a function of three components: content (what is being asserted), context (domain and experimental conditions), and epistemic status (what was found, and with what confidence). Two claims are candidates for merging only when all three components are in sufficient agreement.

The merge/cluster algorithm operates on four signals:

```groovy
merge_score = f(
  semantic_similarity(assertion_embeddings),
  domain_overlap(domain_tags),
  condition_compatibility(experimental_setup),
  epistemic_agreement(outcome, status)
)
```

High semantic similarity alone is not sufficient for a merge. The outcome of the algorithm is not binary — it produces typed edges:

|                    Signal Pattern                    |                   Action                   |
| :--------------------------------------------------: | :----------------------------------------: |
|       High similarity across all four signals        |   Merge → single node, multiple sources    |
|    High semantic + same domain + opposing outcome    |             Contradiction edge             |
|   High semantic + different domain + same outcome    | Replication edge (cross-domain validation) |
| High semantic + different domain + different outcome |         Separate nodes, weak link          |

A contradiction edge is not a failure state. It is a first-class data structure — the signal that a claim is contested at L3 epistemic classification.

Domain tags are not assigned from a predefined taxonomy. They are extracted from the paper at ingest time as flat strings, then clustered and merged as the corpus grows. The domain hierarchy is a derived layer, not an ingest-time constraint.

---

### The Full AI Stack

```
Embedding model      → sentence transformer, runs locally
                       used at L1, L2, L3, L4 for vector indexing

Extraction model     → small fine-tuned LLM (3B–8B), runs locally
                       used at L2 and L3, called thousands of times
                       must be local — cost and privacy

NLI classifier       → BERT-class model, fast and well-studied
                       used at L3 for contradiction/support edge classification

Reasoning model      → larger LLM (fine-tuned 70B or API)
                       used at L4 synthesis and query-time response generation
                       called infrequently
```

---

### Fine-Tuning and the Data Flywheel

The extraction model at L2 and L3 is the critical piece. A general model called thousands of times is expensive, slow, and inconsistent. A small model fine-tuned on your specific schema solves all three problems.

The bootstrap process:

1. Use an API model (Claude, GPT-4) to extract facts from the first 500 papers — this is the **teacher**
2. That output becomes labeled training data
3. Fine-tune a small local model on that data — this is the **student**
4. The student runs locally at scale, cheaply

This is knowledge distillation. The corpus generates its own training data. The system bootstraps itself.

As the corpus grows, so does the labeled dataset — structured claims with provenance, typed relationships, epistemic status, contradiction pairs. This is exactly the kind of structured reasoning data that is difficult to collect at scale. The infrastructure eventually produces a dataset valuable enough to train a model that reasons over the graph natively, not just extracts from it.

---

### Build Sequence

```
Phase 1   L1 + L2 using API model
          Clean ingest pipeline
          Prove paper-level retrieval is useful

Phase 2   L3 extraction using API model
          Design fact schema carefully for your domain
          Build to 1000+ fact nodes in DuckDB

Phase 3   Fine-tune small local model on L2 + L3 extraction
          Replace API calls with local inference
          Add NLI classifier for edge classification

Phase 4   L4 batch synthesis
          Clustering + pattern derivation
          Only meaningful once L3 corpus is large enough
```

---

### Epistemic Classification

Every claim node carries an epistemic status, assigned at ingest time and updated as the corpus grows:

| Status        | Definition                                                                                         |
| ------------- | -------------------------------------------------------------------------------------------------- |
| `established` | Asserted by multiple independent sources, no significant contradiction, reproduced across datasets |
| `preliminary` | One or few sources, not yet replicated, or narrow experimental conditions                          |
| `contested`   | Conflicting evidence exists across literature, active disagreement between research groups         |
| `ungrounded`  | Asserted by the LLM with no traceable fact node in the corpus                                      |

The fourth class — ungrounded — is what most RAG systems silently ignore. When a response is generated, each claim is traced back to its fact node. Claims that cannot be traced are flagged, not silently included.

This is not general misinformation detection. The system operates on a closed epistemic corpus — peer-reviewed literature only. Within that boundary, every claim has traceable provenance. That constraint is the source of the system's reliability.

**Limitation to state clearly:** the system can only flag what contradicts the ingested corpus. A flawed paper that was ingested will be treated as a source. Epistemic value is proportional to corpus quality.

---

## Build Order

1. Ingest 50–100 papers in one focused domain
2. Design extraction schema for that domain — what does a "fact" look like here specifically
3. Write extraction prompt returning structured JSON fact nodes per paper
4. Store facts and typed edges in DuckDB
5. Build Go API: `/query` → semantic search → fact lookup → graph expansion → LLM synthesis with citations and epistemic markers
6. Minimal UI rendering answers with provenance and confidence visible

Prove the structure works on a small corpus before expanding scope.

---

## Honest Constraints

**Extraction is noisy.** LLMs will misclassify claims and miss nuance. The extraction schema needs careful domain-specific design. Treat extracted facts as high-quality drafts, not ground truth.

**Granularity is subjective.** What counts as a primitive idea varies by field. Scope to one domain early or invest in a flexible ontology before expanding.

**Maintenance is ongoing.** Research evolves. Foundational claims get overturned. The graph must reflect this without corrupting structures built on top of affected nodes.

**Corpus quality is the ceiling.** The system's epistemic reliability is bounded by what is ingested. Garbage in, garbage out — but at a more dangerous level of apparent authority.

None of these are blockers. They are engineering problems with tractable solutions. Stating them clearly now prevents over-promising later.
