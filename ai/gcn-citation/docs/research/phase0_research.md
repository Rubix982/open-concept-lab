# Phase 0 Research Brief

**Date**: 2026-03-29
**Purpose**: Pre-implementation research for the arXiv-scale graph learning pipeline
**Scope**: Three blocking questions for Phase 0 infrastructure

---

## Question 1: arXiv Bulk S3 Access

### How access works

The arXiv S3 bucket (`s3://arxiv`) is **requester-pays**. You pay AWS data transfer costs
(~$0.09–$0.12/GB) at the time of download. An AWS account with a registered credit card is
**required**. Anonymous access is not possible — the AWS SDK will reject requests that do
not include requester-pays headers.

However, there is an important distinction between **metadata** and **full content**:

- **PDFs and source files (TeX)**: these live in the requester-pays S3 buckets. The full
  set as of early 2025 is ~9.2 TB total, growing ~100 GB/month. Source files alone are
  ~2.9 TB. These cost money to download.

- **Metadata snapshot** (`arxiv-metadata-oai-snapshot.json`): this is **not** distributed
  via the requester-pays S3 bucket. The canonical free source is the
  [Cornell University Kaggle dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv),
  which is updated regularly. It is also mirrored as HuggingFace datasets
  (`jackkuo/arXiv-metadata-oai-snapshot`, `librarian-bots/arxiv-metadata-snapshot`).

  **The metadata file is free and does not require AWS at all.** The requester-pays model
  applies to PDFs and source, not metadata.

For this project (title + abstract only, no PDFs), **no AWS account is needed and no cost
is incurred**. Download the metadata file from Kaggle or HuggingFace.

### Exact fields in `arxiv-metadata-oai-snapshot.json`

The file is **JSONL** (one JSON object per line, newlines within fields are escaped).
Each record contains:

| Field | Type | Notes |
|---|---|---|
| `id` | string | arXiv ID, e.g. `"2301.07088"` |
| `submitter` | string | Name of submitter |
| `authors` | string | Raw author string |
| `authors_parsed` | list | Parsed `[[last, first, ""], ...]` |
| `title` | string | Paper title |
| `abstract` | string | Full abstract text |
| `categories` | string | Space-separated arXiv categories, e.g. `"cs.LG stat.ML"` |
| `license` | string | License URL or null |
| `doi` | string | DOI or null |
| `journal-ref` | string | Journal reference or null |
| `report-no` | string | Report number or null |
| `comments` | string | Author comments or null |
| `update_date` | string | Most recent update date, `"YYYY-MM-DD"` |
| `versions` | list | `[{"version": "v1", "created": "<RFC date>"}, ...]` |

The `categories` field is the primary one for this project. The **first category listed is
the primary category**. Multi-category papers have space-separated values.

The `id` field is the canonical arXiv ID and is stable across versions.

### File size and download time

- Compressed (.zip or .gz): ~1.1–1.2 GB
- Uncompressed: ~3.5 GB
- Records: ~2.2 million papers (as of late 2024)
- Download time from Kaggle: 5–10 minutes on a fast connection
- Download time from HuggingFace: similar

### Terms of service

ArXiv metadata is freely available for research use. ArXiv's terms grant a perpetual
non-exclusive license to distribute articles. The Kaggle dataset is hosted by Cornell
University (arXiv's operator) and is explicitly made available for research. No restrictions
on personal, non-commercial academic use.

### Best Python approach for stream-parsing

The JSONL format means each line is a complete JSON object. **Do not load the whole file
into memory.** The correct pattern is:

```python
import json

def stream_arxiv_metadata(path):
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

# Usage
for record in stream_arxiv_metadata("arxiv-metadata-oai-snapshot.json"):
    arxiv_id = record["id"]
    title = record["title"]
    abstract = record["abstract"]
    categories = record["categories"].split()
    update_date = record["update_date"]
```

For more complex streaming use cases (e.g. nested field extraction), `ijson` works but
is overkill for JSONL — standard line-by-line iteration is sufficient and faster.

For a 100K working subset filtered on categories (`cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`,
`stat.ML`), stream the full 3.5 GB file once, filter, and write out the subset. This
takes about 30–60 seconds on an M2.

### Recommendation

Use the **Kaggle or HuggingFace mirror** of the metadata snapshot. Do not set up AWS
access unless you later need PDFs (you do not for SPECTER2). Download once, keep locally.
Filter to target categories on the fly during streaming. Store filtered results in a local
SQLite or DuckDB file for reuse.

### Gotchas

- The `categories` field is a single space-separated string, not a list. Split it yourself.
- The `id` field does not include the `https://arxiv.org/abs/` prefix. It is just the
  bare ID like `"2301.07088"` or (for older papers) `"hep-th/9901001"`.
- Old-format arXiv IDs (pre-2007) follow the pattern `<category>/<YYMMNNN>` and contain
  a slash. This will break naive path construction or database keys. Normalize to use
  underscores or just keep as-is and handle the edge case.
- `update_date` reflects the last version update, not first submission. To get submission
  date, parse `versions[0]["created"]`.
- Some `abstract` fields have embedded newlines and extra whitespace. Strip and normalize
  before feeding to SPECTER2.
- The file grows monthly. For reproducibility, note which snapshot date you used.
- Kaggle requires a Kaggle account and `kaggle` CLI for programmatic download, but the
  file can also be downloaded manually from the browser.

---

## Question 2: S2ORC / Semantic Scholar / OpenAlex for Citation Data

### What S2ORC is

**S2ORC (Semantic Scholar Open Research Corpus)** is a large corpus of academic papers
built by Allen Institute for AI (Ai2). Original paper: Lo et al., ACL 2020.

The original S2ORC (the standalone bulk download from 2020–2022) is **no longer available
for direct download** as a flat file. As of January 2023, it has been folded into the
Semantic Scholar Academic Graph API as a "Bulk Dataset" offering.

### Current access method

Access is through the **Semantic Scholar Datasets API**:
- URL: `https://api.semanticscholar.org/api-docs/datasets`
- Requires a **free API key** (register at semanticscholar.org, no cost)
- Provides monthly snapshots as gzipped JSONL files
- Download links are signed S3 URLs — no AWS account needed, just the API key

Available datasets include:
- `papers` — metadata + abstracts
- `citations` — citation links between papers (this is the one you need)
- `paper-ids` — mapping between Semantic Scholar IDs and external IDs (arXiv, DOI, PubMed)
- `embeddings` — SPECTER2 embeddings pre-computed by Semantic Scholar

The `citations` dataset format (gzipped JSONL):
```json
{"citingpaperid": "abc123", "citedpaperid": "xyz789", "isinfluential": true, "intents": ["methodology"]}
```

The `papers` dataset includes `externalids` with the arXiv ID mapping:
```json
{"corpusid": 12345, "externalids": {"ArXiv": "2301.07088", "DOI": "...", "MAG": "..."}, ...}
```

This is how you join Semantic Scholar citations back to arXiv IDs.

### License

The current Semantic Scholar corpus is released under **ODC-By 1.0** (Open Data Commons
Attribution License). This is permissive: attribution required, but commercial and
non-commercial use are both allowed. Personal research use is unambiguously permitted.

Note: the original S2ORC from 2020 had a more restrictive non-commercial license. The
current API-based corpus uses ODC-By 1.0, which is cleaner. **No license barrier for
this project.**

### Scale

- 225M+ papers indexed
- 2.8B+ citation edges
- Indexes arXiv, PubMed, Springer Nature, and others
- Monthly update cadence

### OpenAlex as an alternative

**OpenAlex** (`https://openalex.org`) is a strong alternative and in several ways
**preferable** for this use case:

| Attribute | Semantic Scholar (S2ORC) | OpenAlex |
|---|---|---|
| Papers indexed | ~225M | ~271M (as of late 2025) |
| License | ODC-By 1.0 | **CC0** (no attribution required) |
| Citation edges | 2.8B+ | Comparable |
| arXiv ID mapping | Yes (`externalids.ArXiv`) | Yes (`ids.arxiv`) |
| API key required | Yes (free) | No (recommended but optional) |
| Bulk download | Signed S3 URLs via API | Direct S3 (`s3://openalex`) |
| Cost | Free | **Free, no requester-pays** |
| Format | Gzipped JSONL | Gzipped JSONL |

OpenAlex bulk snapshot is hosted on AWS as a **public dataset** (not requester-pays).
The snapshot is updated monthly. Access via:
```bash
aws s3 ls s3://openalex/ --no-sign-request
aws s3 sync s3://openalex/data/works/ ./openalex-works/ --no-sign-request
```

OpenAlex `Work` object format (relevant fields):
```json
{
  "id": "https://openalex.org/W2741809807",
  "ids": {"doi": "...", "arxiv": "2301.07088"},
  "referenced_works": ["https://openalex.org/W2741809807", ...],
  "title": "...",
  "publication_year": 2023
}
```

`referenced_works` is a list of OpenAlex work IDs for papers this paper cites. To get
arXiv-to-arXiv citation edges, you need to:
1. Build an `openalex_id → arxiv_id` mapping from the snapshot
2. Filter `referenced_works` to only those with known arXiv IDs
3. Emit `(citing_arxiv_id, cited_arxiv_id)` pairs

Total size of the OpenAlex works snapshot is large (~hundreds of GB compressed). For the
arXiv subset only, filter during streaming — no need to download everything.

### Recommendation

Use **OpenAlex** for citation data. Reasons:
1. CC0 license — no attribution requirement, zero ambiguity
2. No API key required (unlike Semantic Scholar)
3. No-cost S3 access (`--no-sign-request`) — no AWS account needed
4. Comparable coverage to Semantic Scholar for arXiv papers
5. Well-maintained, active development, growing corpus

For Phase 0 (10K papers), the Semantic Scholar Graph API (not bulk) is also viable — it
allows per-paper citation lookup with a free API key at 1 req/sec (authenticated). This
may be simpler for small-scale bootstrapping before you build the full pipeline.

### Gotchas

- **OpenAlex bulk is large**: the full `works` snapshot is hundreds of GB. For Phase 0,
  either use the API or filter aggressively during streaming. Do not try to download the
  full snapshot on an M2 unless you have the storage.
- **OpenAlex arXiv ID format**: the `ids.arxiv` field is typically just the bare arXiv ID
  without the `https://arxiv.org/abs/` prefix. Confirm this during implementation.
- **Citation completeness**: neither OpenAlex nor Semantic Scholar has 100% citation
  coverage. Coverage is better for papers with available PDFs. Older arXiv papers
  (pre-2010) have lower coverage. Expect gaps.
- **S2ORC Semantic Scholar API rate limits**: authenticated users get 1 req/sec. For bulk
  downloads via the Datasets API, rate limits apply to obtaining the signed download URLs
  but not to the actual S3 file downloads.
- **OpenAlex `referenced_works` vs `citing_works`**: `referenced_works` = outgoing
  citations (papers this work cites). `citing_works` is NOT stored in the bulk snapshot
  (only available via API). Build your citation graph from `referenced_works` and
  reverse it — for each paper A with `referenced_works` [B, C], emit edges A→B and A→C.
- **The original S2ORC bulk download links are dead**. The old `s3://ai2-s2-research-public`
  paths referenced in old blog posts and GitHub READMEs are defunct. Use the Datasets API
  or OpenAlex instead.

---

## Question 3: SPECTER2 on Apple MPS (Metal)

### Model ID and loading

SPECTER2 is a family of models, not a single checkpoint. The correct architecture is:

- **Base transformer**: `allenai/specter2_base` (a fine-tuned SciBERT)
- **Task-specific adapters** loaded on top of the base

For this project (embedding papers for k-NN similarity), use the **proximity adapter**:

```python
from transformers import AutoTokenizer
from adapters import AutoAdapterModel

tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
model = AutoAdapterModel.from_pretrained("allenai/specter2_base")

# Load proximity adapter (for nearest-neighbor / similarity tasks)
model.load_adapter("allenai/specter2", source="hf", load_as="proximity", set_active=True)
model.eval()
```

The `adapters` library is a separate package (not `transformers`). Install:
```bash
pip install adapters
```

Available adapters and their use cases:

| HuggingFace ID | Use case |
|---|---|
| `allenai/specter2` | **Proximity / nearest-neighbor search** — use this |
| `allenai/specter2_classification` | Linear classification probes |
| `allenai/specter2_regression` | Regression tasks |
| `allenai/specter2_adhoc_query` | Short query strings (search) |

### Input formatting

```python
text_batch = [
    paper["title"] + tokenizer.sep_token + (paper.get("abstract") or "")
    for paper in papers
]

inputs = tokenizer(
    text_batch,
    padding=True,
    truncation=True,
    return_tensors="pt",
    return_token_type_ids=False,
    max_length=512,
)

with torch.no_grad():
    output = model(**inputs)

# CLS token embedding
embeddings = output.last_hidden_state[:, 0, :]  # shape: (batch_size, 768)
```

The separator is `tokenizer.sep_token` (which is `[SEP]` for SciBERT-based tokenizers),
not the string `" [SEP] "` — use the tokenizer attribute, not a hardcoded string.

Output is 768-dimensional float32 vectors.

### MPS (Apple Metal) support

**MPS is usable but has documented limitations:**

**What works:**
- Float32 inference: fully supported, stable, no known issues
- Moving model and inputs to `device="mps"`: works

**Known issues:**

1. **BFloat16 is not supported on MPS** (as of PyTorch 2.x). HuggingFace models that
   default to `torch_dtype=torch.bfloat16` will error with
   `TypeError: BFloat16 is not supported on MPS`. SPECTER2/SciBERT defaults to float32,
   so this is not an immediate issue — but be careful if you add mixed precision training.

2. **Float16 AMP on MPS is unstable**. Do not use `torch.autocast("mps")` or
   `torch.cuda.amp` equivalents. Stick to float32 for inference.

3. **Some operators fall back to CPU** silently. Set
   `PYTORCH_ENABLE_MPS_FALLBACK=1` in your environment to allow this without errors.
   Without it, unsupported ops raise instead of fallback.

4. **NaN issues with float16**: if you ever force float16, NaN values can appear in
   attention layers. Not a concern for float32 inference.

**Recommended device setup:**
```python
import torch

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
model = model.to(device)
inputs = {k: v.to(device) for k, v in inputs.items()}
```

**Environment variable** (add to shell or set in script):
```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

### Recommended batch size

The requirements document estimates ~11 minutes for 100K papers on M2. Working backward
from known BERT-scale inference speeds on M2 MPS (approximately 300–500 sequences/second
at batch=32 for sequence length ~200, slower for full 512):

- **Batch size 32** is the safe starting point for M2 with 16GB unified memory
- **Batch size 64** is likely feasible with the base model + one adapter (no gradient storage)
- SPECTER2 official documentation mentions batch size 256 for adapter training, but that
  is on GPU with gradient checkpointing — do not use that number for inference memory
  estimation on M2
- For 512-token inputs (worst case, long abstracts), stay at batch=32 to avoid OOM
- For typical title+abstract (average ~150–200 tokens), batch=64 is safe

**Recommended**: start at batch=32, verify memory usage, scale up if headroom allows.

### Throughput estimate for this project

Based on M2 MPS performance characteristics for BERT-scale models (110M parameters):

| Papers | Estimated time (batch=32) |
|---|---|
| 10K | ~1–2 min |
| 100K | ~10–20 min |
| 500K | ~1–2 hr |
| 1M | ~2–4 hr |

The requirements document estimates 11 minutes for 100K and 55 minutes for 500K, which is
on the optimistic end. Plan for up to 2x that if abstracts are long. Checkpoint embeddings
by arXiv ID as you go — do not re-run from scratch if the process is interrupted.

### Lighter/faster alternatives

| Model | Notes |
|---|---|
| `sentence-transformers/allenai-specter` | Original SPECTER via sentence-transformers. Faster to load (no adapters library), slightly lower quality than SPECTER2. Good for Phase 0 prototyping. |
| `allenai/scibert_scivocab_uncased` | Base SciBERT. Lower quality for similarity (not citation-tuned). Not recommended for production embeddings. |
| `allenai/specter` | Original SPECTER on HuggingFace directly. Same as sentence-transformers version but without the ST wrapper. |
| `BAAI/bge-small-en-v1.5` | General-purpose, very fast (33M params), not citation-tuned. Loses cross-disciplinary signal. |

**Verdict**: For Phase 0 (10K papers), use `sentence-transformers/allenai-specter` if you
want to move fast without dealing with the `adapters` library. For Phase 1+ (100K+), switch
to `allenai/specter2` + proximity adapter — it is meaningfully better for scientific
similarity tasks, which is directly relevant to Exploratory Goal 1. The quality difference
matters here because you are measuring cross-disciplinary idea similarity.

### Recommendation

1. Use `allenai/specter2_base` + `allenai/specter2` (proximity adapter) for all Phase 1+
   work.
2. Run inference in float32 on MPS, batch size 32–64.
3. Set `PYTORCH_ENABLE_MPS_FALLBACK=1`.
4. Checkpoint embeddings to a memory-mapped `.npy` file indexed by arXiv ID. Use a
   sidecar `.json` file mapping `arxiv_id → row_index` in the mmap array.
5. For Phase 0 prototyping (10K), `sentence-transformers/allenai-specter` is fine and
   requires zero extra dependencies.

### Gotchas

- **The `adapters` library is required** — it is not part of `transformers`. It must be
  installed separately (`pip install adapters`). The HuggingFace model card shows imports
  from `adapters`, not `transformers`. Missing this causes confusing import errors.
- **Do not use `AutoModel.from_pretrained("allenai/specter2")`** directly — this loads
  the proximity adapter as if it were a base model, which does not work correctly. Always
  load `specter2_base` first, then load the adapter on top.
- **Float16 and BFloat16 are both problematic on MPS**. Use float32. This doubles memory
  vs GPU float16 setups, so factor that into batch size.
- **The `return_token_type_ids=False` argument is important**: SciBERT expects token type
  IDs but SPECTER2's adapter setup does not use them. Passing them causes incorrect
  behavior in some adapter configurations. Follow the official code example exactly.
- **Abstract truncation**: at 512 tokens, a long abstract will be cut off. This is
  expected and acceptable — SPECTER2 was trained with this constraint. Do not set
  `max_length` higher than 512.
- **Empty abstracts**: some arXiv records have `None` or empty string for abstract. Guard
  with `paper.get("abstract") or ""` to avoid tokenizer errors.
- **MPS memory is unified with system RAM** on M2. Running SPECTER2 inference reduces
  available RAM for other processes. Close browsers and other apps during long embedding
  runs (100K+).

---

## Open Questions

These could not be resolved from available documentation and will need to be verified
experimentally or by checking primary sources during Phase 0 implementation.

| Question | Impact | How to resolve |
|---|---|---|
| **OpenAlex arXiv citation coverage rate**: what fraction of arXiv-to-arXiv citations are captured in the OpenAlex snapshot? 80%? 95%? | Affects density of `cites` edges in the graph | Sample 100 papers, manually check citations vs OpenAlex coverage |
| **OpenAlex works snapshot size for cs.* only**: the full snapshot is very large. Is there a pre-filtered arXiv-only subset, or does filtering require a full scan? | Phase 0 data download time and storage requirements | Check `aws s3 ls s3://openalex/` structure; look for category-filtered subsets |
| **SPECTER2 actual inference speed on M2 MPS**: the throughput estimates in the requirements doc are theoretical. What is the measured tokens/sec with batch=32, float32, 512-token max? | Timeline accuracy for Phase 0–1 | Run a 1000-paper benchmark locally; measure wall-clock time |
| **`adapters` library compatibility with latest PyTorch/transformers versions**: the `adapters` library has had breaking changes. Is the current version compatible with PyTorch 2.3+ and transformers 4.40+?** | Whether SPECTER2 loads without errors | `pip install adapters` and run the official loading example; check for import errors |
| **Semantic Scholar Datasets API**: does the bulk `citations` dataset include arXiv-to-arXiv citation completeness comparable to OpenAlex, or does OpenAlex have better coverage for preprints? | Choice between S2ORC and OpenAlex for citation edges | Compare citation counts for 50 known arXiv papers between both sources |
| **Pre-computed SPECTER2 embeddings from Semantic Scholar**: the Semantic Scholar Datasets API offers a pre-computed `embeddings` dataset using SPECTER2. Is this the same model (proximity adapter) used for similarity? Could we skip local inference entirely and use these bulk embeddings? | Would eliminate the most time-consuming Phase 0 step | Check the Semantic Scholar `embeddings` dataset documentation; verify adapter variant and coverage |
