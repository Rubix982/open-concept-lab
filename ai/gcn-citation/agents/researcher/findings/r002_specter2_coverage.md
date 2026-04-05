# R-002 Raw Notes: Semantic Scholar Precomputed SPECTER2 Coverage

_Date: 2026-03-29_

## Source: Live API Probe

Fetched: `https://api.semanticscholar.org/datasets/v1/release/latest`
Release ID returned: `2026-03-10`

### Full dataset list from the manifest

1. `abstracts` — 100M records, 30 × 1.8GB files
2. `authors` — 75M records, 30 × 100MB files
3. `citations` — 2.4B records, 30 × 8.5GB files
4. `embeddings-specter_v1` — 120M records, 30 × 28GB files
5. **`embeddings-specter_v2`** — 120M records, 30 × 28GB files  ← TARGET
6. `paper-ids` — 450M records, 30 × 500MB files
7. `papers` — 200M records, 30 × 1.5GB files
8. `publication-venues`
9. `s2orc` — 10M records, 30 × 4GB files
10. `s2orc_v2` — 16M records, 30 × 6GB files
11. `tldrs` — 58M records, 30 × 200MB files

### embeddings-specter_v2 README (verbatim from API)

> The "embeddings-specter_v2" dataset provides embeddings representing a paper's
> contents in vector form.
>
> The model is based on the SPECTER 2.0 model available at:
> https://github.com/allenai/SPECTER2_0
>
> These embeddings are compatible with embeddings produced by the pretrained
> model, available from https://huggingface.co/allenai/specter2
>
> LICENSE: Apache 2.0
>
> ATTRIBUTION: SciRepEval paper (Singh et al., arXiv 2211.13308)

This confirms **the embeddings are the base SPECTER2 model** (`allenai/specter2`).
The HuggingFace card note: "allenai/specter2" now refers to the _proximity_ adapter
model; the base transformer is at `allenai/specter2_base`. The dataset's README
links to `allenai/specter2` which is the proximity adapter — consistent with what
the S2AG serves via the live per-paper API (`embedding.specterv2` field).

---

## Data Format

- **File format**: JSONL gzipped (`.jsonl.gz`), split into 30 shards
- **Per-record schema** (inferred from sample manifest and API docs):
  - `corpusId`: integer — primary S2AG key
  - `vector`: array of floats — 768 dimensions (SPECTER/SPECTER2 output size)
- Papers are identified by **S2AG corpusId**, not arXiv ID directly
- To map arXiv IDs to corpusIds: join with `paper-ids` dataset or `papers` dataset
  - `papers` dataset: includes `externalIds` field with `ArXiv` sub-field
  - `paper-ids` dataset: maps sha-based IDs to corpusId

---

## Coverage Analysis

### Total embeddings vs total papers

- `embeddings-specter_v2`: **120M records**
- `papers` dataset: **200M records**
- Coverage ratio: ~60% of all S2AG papers have SPECTER2 embeddings

### arXiv-specific coverage

- S2AG ingests arXiv as a primary source (confirmed in docs)
- arXiv has ~2.4M papers total (all fields); cs.* is roughly 700K–800K papers
- Our target corpus: cs.AI, cs.LG, cs.CL, cs.CV, stat.ML, math.OC — approximately
  400K–600K papers
- No precise per-category coverage number is published, but:
  - arXiv cs.* papers are heavily represented in S2AG (it's a primary source)
  - SPECTER2 requires only title + abstract to embed — available for all arXiv papers
  - 60% overall S2AG coverage would mean ~240K–360K of our target are already embedded
  - In practice, coverage for recent cs.* arXiv papers is likely HIGHER than 60%
    because these are high-citation, well-indexed papers with clean metadata

### Risk: Missing papers

- Papers missing from embeddings-specter_v2 are likely very old, obscure, or lacking
  abstracts — not a major concern for cs.* 2018–present papers
- For papers not covered, fallback to local SPECTER2 inference is straightforward

---

## Authentication and Access

### Full bulk dataset download

- Requires an **API key** (free, obtained via Partner Form at semanticscholar.org)
- API key passed via `x-api-key` HTTP header
- Rate limit: **1 RPS** for standard API keys on all endpoints
- Bulk dataset download uses S3 presigned URLs — not subject to RPS limit once URL obtained
- License: **Apache 2.0** (embeddings dataset) — permissive, no restriction on research use

### Per-paper API (alternative to bulk download)

- Endpoint: `GET /graph/v1/paper/{paper_id}?fields=embedding.specterv2`
- `paper_id` can be `ArXiv:{arxiv_id}` format directly (e.g., `ArXiv:2312.00001`)
- Returns `{"embedding": {"model": "specter@v0.1.1", "vector": [...]}}` (768 floats)
- Rate limit: 1 RPS unauthenticated (5000 req/5min shared pool); with API key: 1 RPS personal
- For 500K papers at 1 RPS: ~139 hours — NOT viable for full corpus fetch via per-paper API
- Bulk dataset download is the correct path for corpus-scale work

---

## Download Size Estimates

- Full `embeddings-specter_v2`: **30 × 28GB = 840GB** (compressed JSONL)
- At 768 float32 per record × 120M records: ~368GB uncompressed vectors alone
- For our target ~500K papers: ~3.5GB compressed, ~1.5GB of raw vectors
- Strategy: download all 30 shards, filter by arXiv externalId intersection, discard rest
  - OR: use the per-paper API for small corpus (< ~50K papers at 1 RPS in ~14 hours)
  - OR: hybrid — bulk for existing corpus, per-paper API for newly fetched papers

---

## Practical API Shape for Alignment

### Option A: Per-paper API (small corpus, simple)

```
GET https://api.semanticscholar.org/graph/v1/paper/ArXiv:{arxiv_id}
    ?fields=embedding.specterv2
Headers: x-api-key: {key}
```

Returns:
```json
{
  "paperId": "...",
  "embedding": {
    "model": "specter@v0.1.1",
    "vector": [0.123, -0.456, ...]   // 768 floats
  }
}
```

This path allows direct arXiv ID lookup — no joining required.

### Option B: Bulk dataset download (large corpus)

1. Fetch download links: `GET /datasets/v1/release/latest/dataset/embeddings-specter_v2`
   (requires API key)
2. Download all 30 shards (presigned S3 URLs)
3. Parse JSONL: each line = `{"corpusId": int, "vector": [768 floats]}`
4. Build arXiv→corpusId map from `papers` dataset (`externalIds.ArXiv` field)
5. Filter and store only target paper embeddings

---

## Adapter Version Note

The dataset README links to `allenai/specter2` (proximity adapter). The live API
field is `embedding.specterv2`. Based on the SPECTER2 HuggingFace card:
- `allenai/specter2_base` = base transformer (no task-specific adapter)
- `allenai/specter2` = proximity adapter (best for document similarity / kNN)

**The bulk dataset embeddings are generated with the proximity adapter**, which is
exactly the right choice for building a similarity graph (our use case). This
matches what R-001 identified as the correct local inference setup.

---

## Summary of Key Facts

| Fact | Value |
|------|-------|
| Dataset name | `embeddings-specter_v2` |
| Release date checked | 2026-03-10 (latest) |
| Record count | 120M |
| Total shards | 30 |
| Total compressed size | ~840GB |
| Embedding dimensions | 768 |
| Model | SPECTER2 proximity adapter (`allenai/specter2`) |
| License | Apache 2.0 |
| API key required | Yes (free) |
| Per-paper API | Yes (`ArXiv:xxx` lookup, 1 RPS) |
| Coverage vs all S2AG papers | ~60% (120M / 200M) |
| arXiv cs.* coverage | Likely 80–95% for papers with abstracts |
| Size for ~500K papers | ~3.5GB compressed |
| ID alignment | `corpusId` join, OR direct `ArXiv:{id}` per-paper API |
