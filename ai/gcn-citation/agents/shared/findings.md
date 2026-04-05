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
