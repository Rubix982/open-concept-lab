# Researcher Tickets

---

### R-001 · Research Phase 0 technical dependencies

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Research three blockers before Phase 0 implementation can begin:
1. arXiv bulk metadata: access method, format, gotchas
2. Citation data: S2ORC license/availability vs alternatives
3. SPECTER2 on Apple MPS: compatibility, batch size, known issues

**Artifacts:**
- docs/research/phase0_research.md (full research brief)
- agents/shared/findings.md → [R-001] Finding: Phase 0 Technical Dependencies

**Closed:** 2026-04-05

---

### R-002 · Verify Semantic Scholar precomputed SPECTER2 coverage

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-03-29

**Description:**
The Semantic Scholar Datasets API may ship precomputed SPECTER2 embeddings for
arXiv papers. If coverage is sufficient for our target corpus (cs.AI, cs.LG,
cs.CL, cs.CV, stat.ML, math.OC + interdisciplinary), we can skip local SPECTER2
inference entirely and download the precomputed vectors.

Determine:
1. Does the Semantic Scholar Datasets API include SPECTER2 embeddings?
2. What is the API endpoint, authentication, and data format?
3. What fraction of arXiv papers have precomputed embeddings?
4. What is the download size per paper / total for 500K papers?
5. Are embeddings the same model as `allenai/specter2` (proximity adapter)?

Output findings to agents/shared/findings.md as [R-002].

**Blockers:** none

**Artifacts:**
- agents/researcher/findings/r002_specter2_coverage.md (raw notes)
- agents/shared/findings.md → [R-002] Finding: Semantic Scholar Precomputed SPECTER2 Coverage

**Key result:**
- Dataset `embeddings-specter_v2` confirmed: 120M records, 30 x 28GB shards, Apache 2.0
- Model: SPECTER2 proximity adapter (allenai/specter2) — same as R-001 local setup
- Coverage: ~60% overall S2AG; ~80-95% for arXiv cs.* with abstracts
- Access: free API key required; bulk via S3 presigned URLs (no RPS limit)
- Recommendation for E-006: hybrid downloader (bulk + per-paper API gap fill) + local fallback

**Closed:** 2026-03-29

---

### R-003 · Design L2 extraction prompt and validate schema on 5 papers

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-04-12

**Description:**
Design the Claude API prompt for L2 paper summary extraction and validate it
against 5 real papers from our 10K corpus.

**What to produce:**

1. A Claude API prompt (using tool_use / JSON mode) that takes a paper title +
   abstract and returns a structured L2 summary matching this schema:
   ```json
   {
     "contribution": "One sentence.",
     "method": "Technique/architecture used.",
     "datasets": ["list"],
     "key_findings": ["finding_1", "finding_2", "finding_3"],
     "limitations": "Known constraints.",
     "domain_tags": ["NLP", "transformers", ...],
     "related_methods": ["BERT", "GPT", ...]
   }
   ```

2. Run it against 5 diverse papers from data/pipeline/arxiv_10k.parquet
   (pick papers spanning different subfields: NLP, CV, RL, optimization, statistics)

3. Evaluate quality:
   - Is the contribution sentence accurate and self-contained?
   - Are domain_tags consistent across papers from the same field?
   - Are key_findings specific (with numbers/metrics) or vague?
   - Would a researcher unfamiliar with the paper understand what it found?

4. Note: abstract-only is sufficient for L2. Do NOT use full PDF for Phase 1.

**Output:** Write findings to agents/shared/findings.md as [R-003].
Include the final prompt text and 2-3 example extractions with quality notes.

**Blockers:** none

**Closed:** 2026-04-12

**Artifacts:**
- agents/researcher/findings/r003_l2_extractions.json (raw Ollama outputs for 5 papers)
- agents/shared/findings.md → [R-003] Finding: L2 Extraction Prompt Design and Validation

**Key result:**
- Prompt v1 produced valid JSON on all 5 papers, first attempt, no iteration needed
- Overall quality: medium-high; contribution/method/datasets fields strong; domain_tags
  has CV-as-NLP drift on cross-domain papers; findings qualitative when abstract lacks numbers
- Known failure modes documented for E-015: domain tag drift, shallow related_methods,
  limitations echo

---

### R-004 · Research NLI models for contradiction/support classification

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-04-12
**Closed:** 2026-03-29

**Description:**
Research which NLI (Natural Language Inference) model is best suited for
classifying edges between claim nodes as: supports, contradicts, neutral.

Evaluate:
1. **cross-encoder/nli-deberta-v3-small** (HuggingFace) — strong, fast
2. **facebook/bart-large-mnli** — classic, well-tested
3. **MoritzLaurer/deberta-v3-large-zeroshot-v2** — zero-shot capable

For each, check:
- Can it run on MPS (Apple Silicon)?
- What's inference time for a single pair?
- How does it handle scientific claims (not just generic NLI)?
- Does it need fine-tuning for the AI/ML domain?

Test with 5 real claim pairs from AI/ML literature where you know the ground truth:
- A clear support pair (two papers claiming same result)
- A clear contradiction pair (two papers with opposing findings)
- A neutral pair (unrelated claims)

Output: agents/shared/findings.md as [R-004].
Recommendation: which model to use for Phase 2 edge classification.

**Blockers:** none (can run in parallel with Phase 1)

**Artifacts:**
- agents/researcher/findings/r004_nli_results.json (raw inference outputs across all models and methods)
- agents/shared/findings.md → [R-004] Finding: NLI Models for Contradiction/Support Classification

**Key result:**
- All three models run on MPS without errors
- `cross-encoder/nli-deberta-v3-small` recommended for E-021: fastest (190ms/pair), correct on support and contradiction pairs
- Use zero-shot-classification pipeline with semantic label template + confidence threshold 0.50 for neutral fallback
- `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` (corrected ID) is a binary model — cannot distinguish contradiction from neutral, wrong fit for this task
- Neutral detection fails universally for structurally similar but topically unrelated claim pairs — confidence threshold mitigates this

**Closed:** 2026-03-29

---

### R-005 · Design L3 claim extraction schema and prompt for AI/ML domain

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-12

**Description:**
Design the L3 claim extraction schema and validate it on 5 papers from the L2
corpus. L3 is the hardest layer — it must extract discrete, self-contained claims
at the granularity of ideas, not sentences.

**The core question**: what is a "claim" in an AI/ML paper? It must be:
- Self-contained (can stand alone without reading the paper)
- Falsifiable (could in principle be contradicted by another paper)
- Atomic (not bundled with multiple distinct assertions)

**Schema to design:**
```json
{
  "claim_id": "uuid — generated",
  "claim_type": "empirical | theoretical | architectural | comparative | observation",
  "assertion": "The claim in one sentence, self-contained.",
  "method": "Technique or model being described (e.g. 'BERT', 'ResNet', 'Adam')",
  "domain": "NLP | CV | RL | optimization | theory | graph_learning | statistics",
  "dataset": "Dataset name if applicable, null otherwise",
  "metric": "Accuracy | F1 | BLEU | loss | etc., null if non-numeric",
  "value": "Numeric result as string, null if absent",
  "conditions": "What conditions qualify this claim (dataset size, architecture, etc.)"
}
```

**Prompt design task:**
1. Write a single Ollama prompt (qwen2.5-coder:7b) that takes a paper's
   title + abstract + key_findings (from L2) and returns a JSON array of
   1-5 claim objects
2. Test on 5 papers from the L2 corpus covering different subfields
3. For each paper, manually verify:
   - Are the claims atomic (not bundled)?
   - Is the assertion self-contained (no "this paper" or "we")?
   - Is claim_type correct?
   - Would two papers asserting the same thing produce mergeable claims?

**Critical: claim identity test**
Take one claim from paper A and find a paper B that makes the same claim.
Do the extracted claims look similar enough to be deduplicated via embedding?
This tests whether the extraction is consistent enough for L3 to work.

**Output:** Write to agents/shared/findings.md as [R-005]:
- Final prompt text
- 5-paper extraction results (table)
- Quality verdict: high / medium / low
- Claim identity test result
- Known failure modes for E-021

**Blockers:** E-018 (need L2 summaries to feed as input)

**Closed:** 2026-04-12

---

### R-006 · Research Semantic Scholar API for real citation edges

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-04-12

**Description:**
OpenAlex has 0 citation edges for arXiv preprints (referenced_works empty for
papers without journal publication). Semantic Scholar extracts references from
PDF text — it has real citation data for preprints.

We applied for a Semantic Scholar API key. This ticket covers the research and
initial implementation once the key arrives.

**Research questions:**
1. What endpoint gives outgoing citations for a paper? (referenced_works analog)
   - Check: `GET /graph/v1/paper/ArXiv:{id}?fields=references`
   - Does `references` include papers cited IN this paper?
2. What is the rate limit for the standard tier vs partner tier?
3. For our 500-paper corpus: what % of papers have reference data in S2?
   Test with 10 papers: `GET /graph/v1/paper/ArXiv:{id}?fields=references,citationCount`
4. What is the reference schema? Do we get arXiv IDs for cited papers,
   or just S2 paper IDs we need to resolve?
5. Estimate: how many citation edges would 500 papers produce?

**If API key is available:**
Write a small test script that fetches citations for 5 papers and reports
how many references each had, and how many of those references are also
in our 500-paper corpus (i.e. how many intra-corpus citation edges we'd get).

**Output:** agents/shared/findings.md as [R-006]:
- Endpoint that works for citation data
- Coverage: % of our papers with reference data
- Estimated intra-corpus citation edges
- Rate limits and download strategy for 500 papers

**Blockers:** Semantic Scholar API key (external — still pending approval)

**Closed:** 2026-04-12

---

### R-007 · Research embedding models for concept/idea-level search

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-12
**Closed:** 2026-03-29

**Description:**
SPECTER2 (proximity adapter) fails for concept-level keyword search because it
was trained for paper-paper citation similarity, not query-document retrieval.
All ML papers score 0.89-0.94 against any query — not discriminative.

Research which model best represents **ideas** as searchable vectors, evaluating
both paper-level and claim-level encoding.

**Key insight to test first:** SPECTER2 has an `adhoc_query` adapter designed
specifically for query-document retrieval. Test this before switching models:
```python
model.load_adapter("allenai/specter2", source="hf", set_active=True)  # current (proximity)
model.load_adapter("allenai/specter2_adhoc_query", source="hf", set_active=True)  # test this
```

**Candidate models to evaluate (all run on MPS):**

1. **SPECTER2 adhoc_query adapter** — same model, different head. Zero extra cost.
2. **`nomic-ai/nomic-embed-text-v1.5`** — top MTEB open model, 768d, runs locally
3. **`BAAI/bge-small-en-v1.5`** — compact (33M params), fast, strong concept search
4. **`sentence-transformers/all-MiniLM-L6-v2`** — 22M params, very fast, proven quality

**Evaluation protocol:**

Use the 10 Phase 1 queries from E-019. For each model:
1. Embed the query text
2. Embed all 500 paper contributions from `paper_summaries` (short text, not full abstract)
3. Cosine search → top 5
4. Count: how many of the top 5 are topically relevant to the query?

Record for each model:
- Relevance score (topical hits in top 5, out of 10 queries)
- Inference time per paper on MPS
- Model size (params, disk)
- Does it handle short concept phrases well?

**Critical question for L3 claims:** will the same model work for short
one-sentence claim assertions (e.g. "Batch normalization reduces internal
covariate shift in deep networks")? Test on 5 sample claims from the DB.

**Output:** Write to agents/shared/findings.md as [R-007]:
- Results table: model × relevance × speed × size
- Recommendation: which model to use for E-025 re-embedding
- Whether SPECTER2 adhoc_query fixes it (saves switching models)

**Blockers:** none

**Artifacts:**
- agents/researcher/findings/r007_embedding_eval.json (SPECTER2 adhoc_query results, relevance annotations)
- agents/shared/findings.md → [R-007] Finding: Embedding Models for Concept/Idea-Level Search

**Key result:**
- SPECTER2 adhoc_query adapter fixes score compression: range 0.52-0.79 (std=0.036) vs proximity adapter 0.89-0.94 (std~0.01)
- 4/10 fully relevant at rank 1, 4/10 partial — significantly better than proximity adapter (0/10)
- 11ms/paper on MPS — identical speed to proximity adapter
- Recommendation for E-025: swap to adhoc_query adapter (zero-cost fix, same base model)
- BGE-small-en-v1.5 installed as fallback; run r007_eval.py to get BGE comparison numbers
- Claim-level embeddings are usable: off-diagonal cosine 0.61-0.68 (not collapsed)

**Closed:** 2026-03-29

---

### R-008 · Design hybrid retrieval strategy for idea-level queries

**Status:** open
**Type:** research
**Priority:** high
**Created:** 2026-04-12

**Description:**
Even with a better embedding model, hybrid retrieval (text search + semantic
search) is standard practice for production knowledge systems. Research the
best hybrid strategy for our SQLite-based system.

**SQLite FTS5 is built-in** — no extra library needed. Research:

1. **FTS5 text search** over L2 `contribution + key_findings`:
   - Syntax: `CREATE VIRTUAL TABLE search_index USING fts5(arxiv_id, text)`
   - Query: `SELECT * FROM search_index WHERE search_index MATCH 'batch normalization'`
   - Does BM25 scoring from FTS5 already give good topical results?
   - Test on same 10 Phase 1 queries

2. **Hybrid scoring formula** — combine text + embedding scores:
   - `final_score = alpha * bm25_score + (1-alpha) * embedding_score`
   - What alpha gives best results? Test alpha = 0.3, 0.5, 0.7

3. **Query expansion**: for short queries, expand with related terms before
   searching. E.g., "GNN" → "graph neural network message passing aggregation"
   Use qwen2.5-coder:7b for expansion (already installed, no extra cost):
   ```python
   expanded = ollama_expand("GNN")  # returns richer query
   ```

4. **L3 claim search**: when claim nodes exist, should we search claim
   assertions directly instead of paper contributions? How does this interact
   with hybrid retrieval?

**Output:** Write to agents/shared/findings.md as [R-008]:
- FTS5 alone: relevance on 10 queries
- Hybrid alpha sweep: which alpha is best
- Query expansion: does it help?
- Recommendation for E-024 implementation

**Blockers:** none (can use existing DB)

**Closed:** —
