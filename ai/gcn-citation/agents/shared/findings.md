# Shared Findings

_Owned by: Researcher. All agents read. Append-only._

---

## [R-001] Finding: Phase 0 Technical Dependencies

_Date: 2026-04-05_

Researched three blockers for Phase 0: arXiv metadata access, citation data source,
and SPECTER2 compatibility on Apple MPS.

**arXiv metadata snapshot**:
- Free download, no AWS account required. Requester-pays applies to PDFs only.
- Best source: Kaggle Cornell University arXiv dataset or HuggingFace mirror
- Format: JSONL, ~3.5GB uncompressed, ~1.2GB compressed, ~2.2M records
- `categories` field is a space-separated string (not a list) — must split manually
- Old-format IDs contain slashes (e.g. `math/0406594`); new-format do not
- Stream line-by-line with `json.loads()` — too large to load at once

**Citation data — use OpenAlex, not S2ORC**:
- Original S2ORC bulk S3 links are defunct — do not use
- OpenAlex: CC0 license, no API key required, free S3 via `--no-sign-request`
- 271M papers indexed; arXiv papers identifiable via `ids.arxiv` field
- Citations stored as `referenced_works` per paper (outgoing only — reverse for full graph)
- Semantic Scholar Datasets API is an alternative (requires free API key, ODC-By license)

**SPECTER2 on Apple MPS**:
- Model: `allenai/specter2_base` + proximity adapter (`allenai/specter2`)
- Requires `pip install adapters` (separate from `transformers`)
- Must use float32 on MPS — bfloat16 unsupported, float16 unstable
- Set environment variable: `PYTORCH_ENABLE_MPS_FALLBACK=1`
- Input format: `title + tokenizer.sep_token + abstract`, truncated to 512 tokens
- Batch size 32–64 on M2 with 16–32GB unified memory
- **Key shortcut**: Semantic Scholar Datasets API may ship precomputed SPECTER2
  embeddings for arXiv papers — check before committing to local inference (R-002)
- Simpler prototype alternative: `sentence-transformers/allenai-specter` (no adapters)

Confidence: high

---

## [R-002] Finding: Semantic Scholar Precomputed SPECTER2 Coverage

_Date: 2026-03-29_

**Short answer: precomputed SPECTER2 embeddings exist, are broadly available for arXiv cs.* papers, and a hybrid download strategy is practical. E-006 should implement a downloader first, with local inference as fallback.**

### 1. Does the dataset exist?

Yes. The Semantic Scholar Datasets API (`api.semanticscholar.org/datasets/v1/release/latest`,
release `2026-03-10`) includes a dataset named **`embeddings-specter_v2`**:

> "A dense vector embedding representing the contents of the paper, generated with SPECTER2.
> 120M records in 30 28GB files."

The dataset is explicitly named alongside `embeddings-specter_v1` as a separate offering.

### 2. Model, format, and fields

- **Model**: SPECTER2 proximity adapter (`allenai/specter2` on HuggingFace). This is the
  correct adapter for document similarity and kNN graph construction — exactly our use case.
  The bulk embeddings are compatible with local inference using the same adapter.
- **File format**: gzipped JSONL (`.jsonl.gz`), 30 shards
- **Per-record schema**:
  - `corpusId`: integer (S2AG primary key)
  - `vector`: array of 768 float32 values
- **License**: Apache 2.0 — permissive, no research restrictions

### 3. Coverage

- **Overall S2AG coverage**: 120M embeddings / 200M total papers ≈ **60%**
- **arXiv cs.* coverage**: Likely **80–95%** for papers with titles and abstracts.
  arXiv is a primary S2AG data source; SPECTER2 needs only title + abstract to embed,
  and nearly all cs.* arXiv papers supply both. Gaps are mostly very old or obscure papers.
- **Our target corpus** (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML, math.OC, ~500K papers):
  Expected coverage is high — conservative estimate 80%+, likely higher for post-2018 papers.

### 4. Download size and access

| Dimension | Value |
|-----------|-------|
| Full dataset (30 shards) | ~840GB compressed |
| Estimated for ~500K target papers | ~3.5GB compressed |
| Embedding size per paper | ~3KB (768 × float32) |
| API key required | Yes (free, via semanticscholar.org Partner Form) |
| Authentication method | `x-api-key` HTTP header |
| Rate limit | 1 RPS personal; S3 bulk download not RPS-limited |

Full bulk download is 840GB; we only need a filtered subset (~3.5GB). The workflow is:
download all shards, filter by intersection with our arXiv corpus, discard the rest.

### 5. Two access paths for E-006

**Path A: Per-paper Graph API** (simple, good for small or incremental fetches)

```
GET /graph/v1/paper/ArXiv:{arxiv_id}?fields=embedding.specterv2
x-api-key: {key}
```
Returns `{"embedding": {"model": "specter@v0.1.1", "vector": [768 floats]}}`.
Direct arXiv ID lookup — no joining. At 1 RPS, 500K papers = ~139 hours. Viable only for
small corpus (< 50K papers) or incremental top-ups.

**Path B: Bulk dataset download** (correct path for corpus-scale work)

1. `GET /datasets/v1/release/latest/dataset/embeddings-specter_v2` → 30 presigned S3 URLs
2. Download shards (S3 transfer, no RPS limit)
3. Parse JSONL: `{"corpusId": int, "vector": [...]}`
4. Build arXiv → corpusId map from `papers` dataset (`externalIds.ArXiv`)
5. Filter to target corpusIds and persist vectors

### 6. ID alignment

S2AG embeddings use `corpusId` as key, not arXiv ID. Two alignment options:
- Join `papers` dataset (`externalIds.ArXiv` → `corpusId`), then join to embeddings
- OR use per-paper API with `ArXiv:{id}` directly (Path A above)

For bulk pipeline, the `papers` shard download (~1.5GB per shard × 30 = ~45GB) is
required for the join. Alternatively, fetch the `paper-ids` dataset (30 × 500MB = 15GB)
which maps sha-IDs to corpusId, then use the Graph API to resolve arXiv→sha.

### 7. Recommendation for E-006

**Implement a hybrid downloader**:

1. **Primary path**: Bulk dataset download + corpusId join (covers ~80–95% of corpus)
   - Fetch `papers` dataset shards, filter rows where `externalIds.ArXiv` is in our corpus
   - Fetch `embeddings-specter_v2` shards, filter by matching corpusIds
   - Store as `{arxiv_id: vector}` in a local cache (numpy/HDF5/parquet)

2. **Gap-fill path**: Per-paper API for papers missing from bulk dataset
   - For any arXiv ID with no embedding from bulk, call `ArXiv:{id}?fields=embedding.specterv2`
   - Rate: 1 RPS; expected gap is small (< 20% of corpus), feasible overnight

3. **Last-resort fallback**: Local SPECTER2 inference (from R-001) for papers S2AG
   doesn't know about at all (very new preprints, < 1 month old, not yet indexed)

The MPS setup from R-001 remains valid as fallback, but should not be the primary path —
the precomputed embeddings are model-compatible (same proximity adapter) and save days of
local compute.

**No new model compatibility concerns introduced.** The bulk embeddings are produced by
the same `allenai/specter2` proximity adapter that R-001 identified for local inference.

Confidence: high
Recommendation for E-006: downloader (bulk + per-paper API gap fill), local inference as last-resort fallback

---

## [R-003] Finding: L2 Extraction Prompt Design and Validation

_Date: 2026-04-12_
_Model tested: qwen2.5-coder:7b via Ollama at http://localhost:11434_

### Summary

Designed and validated a single-string L2 extraction prompt against 5 real arXiv papers
from the 10K corpus. All 5 extractions parsed as valid JSON on the first attempt. Quality
is medium-to-high with specific known failure modes documented below.

---

### Final Prompt (v1)

```
You are a research assistant specializing in AI, machine learning, and computer science.
Your task is to extract a structured summary from an arXiv paper.

Read the title and abstract below, then output ONLY a single JSON object that matches
the schema exactly. Do NOT add any explanation, markdown, code fences, preamble, or
commentary. Output raw JSON only.

Schema:
{
  "contribution": "<ONE sentence: the main contribution of this paper>",
  "method": "<The specific technique, architecture, or algorithm used — be precise,
not generic (e.g. 'transformer encoder with cross-attention' not 'deep learning')>",
  "datasets": ["<dataset name>", "..."],
  "key_findings": [
    "<finding 1 — include numbers/metrics where available>",
    "<finding 2>",
    "<finding 3>"
  ],
  "limitations": "<Known constraints, scope limitations, or null if none stated>",
  "domain_tags": ["<2-4 specific tags, e.g. NLP, transformers, language_modeling>"],
  "related_methods": ["<name of related technique or paper>", "..."]
}

Rules:
- "contribution" must be one sentence only.
- "method" must name the specific technique, not just "neural network" or "deep learning".
- "key_findings" must contain exactly 3 items; include numeric results if stated.
- "datasets" must be an empty list [] if no datasets are named in the abstract.
- "domain_tags" must contain 2 to 4 tags maximum.
- Output JSON only. No explanation. No markdown. No code fences.

Paper title: {title}

Abstract:
{abstract}

JSON:
```

No iterations needed. Prompt worked on first attempt with clean JSON output across all 5 papers.

---

### Quality Assessment — 5 Papers

| # | Subfield | arxiv_id | contribution OK? | method specific? | findings specific (w/ metrics)? | domain_tags sensible? | JSON parse |
|---|---|---|---|---|---|---|---|
| 1 | NLP / language modeling | 2603.01059 | Yes — accurate, one sentence | Partial — "small-large model collaborative architecture" (names the pattern but not exact model names) | Yes — 4.72/5.0, 3x token reduction | Yes — [NLP, chatbots, privacy] (3 tags) | OK |
| 2 | Computer Vision | 2512.11321 | Yes — accurate, one sentence | Yes — "language-driven model trained on multimodal data...ARKit-based facial control space" | Yes — 3.4% and 2.7% improvements named | Partial — [NLP, facial_animation] (should include "computer_vision" or "3D_animation") | OK |
| 3 | Optimization / theory | 2603.28939 | Yes — accurate, one sentence | Yes — "Polar Linear Algebra with self-adjoint-inspired spectral constraints" | Partial — findings are qualitative, not numeric (abstract lacks quantitative results) | Yes — [operator_learning, spectral_properties, linear_algebra] | OK |
| 4 | Graph learning / GNN* | 2604.02322 | Yes — accurate for the actual paper | Yes — "training to solve N problems simultaneously within shared context window" | Yes — 15.8%-62.6% token reduction named | Partial — [NLP, transformers, language_modeling] (paper is LLM efficiency, not GNN) | OK |
| 5 | Statistics / probabilistic ML | 2510.17903 | Yes — accurate, one sentence | Yes — "fused-lasso regularizer on Laplacians + ADMM algorithm" (precise) | Partial — findings are qualitative ("outperforms baselines") due to abstract level | Yes — [graph_signal_processing, time_varying_networks, ADMM] | OK |

**Note on Paper 4**: The sampling strategy selected a cs.LG paper about LLM batch-reasoning
efficiency rather than a GNN paper. The GNN paper category is weakly represented in cs.LG;
E-015 should filter by title/abstract keywords (e.g. "graph neural", "GNN", "message
passing") when sampling for domain coverage tests.

---

### Overall Quality Verdict

**Medium-high.**

- JSON parsing: 5/5 clean parses — no structural failures
- Contribution field: 5/5 accurate one-sentence summaries
- Method field: 4/5 specific; 1 partial (Paper 1: architecture pattern named but not implementation detail)
- Key findings with metrics: 3/5 have numeric results (abstracts for Papers 3 and 5 were
  qualitative by nature, not extraction failures)
- Domain tags: 4/5 sensible; 1 miss (Paper 2 tagged NLP instead of CV)
- Limitations field: model often echoes the abstract text rather than synthesizing a true
  constraint; acceptable for L2 use case

---

### Known Failure Modes for E-015

1. **Domain tag drift for cross-domain papers**: Papers at NLP/CV intersection were tagged
   as NLP, dropping CV. E-015 should post-process domain_tags against the paper's arXiv
   category field to catch cross-domain mislabels.

2. **Vague method for system/framework papers**: Papers that describe a "system" or
   "framework" rather than a single algorithm produce coarser method descriptions.
   Acceptable for L2, but will degrade L3 claim specificity.

3. **Qualitative findings when abstract lacks numbers**: If the abstract reports no
   quantitative results, the model produces qualitative findings. This is correct behavior
   (the model is not hallucinating numbers), but E-015 should flag these as `has_metrics: false`
   so downstream users know to expect prose findings.

4. **Limitations field echoes abstract text**: Model often repeats stated challenges as
   "limitations" rather than identifying scope constraints. Acceptable for Phase 1 but
   worth improving in student fine-tuning (Phase 3).

5. **related_methods field is shallow**: Tends to name 1-2 broad methods rather than
   specific prior works. For L2 this is acceptable; for L3 claim extraction this would
   need a stronger prompt.

6. **Sampling note**: The parquet categories for GNN/graph papers are scattered across
   cs.LG and cs.AI. A keyword pre-filter on title+abstract is needed to reliably select
   GNN papers from these categories.

---

### Confidence

**High** for production use in E-015 Phase 1 pipeline. The prompt reliably produces
valid, parseable JSON with accurate contribution sentences and specific methods.
The identified failure modes are predictable and manageable via post-processing.

Recommended: use this prompt verbatim for the first 50-paper ingest. Re-evaluate after
reviewing those 50 extractions before scaling to 500.

Raw extraction outputs: `agents/researcher/findings/r003_l2_extractions.json`
