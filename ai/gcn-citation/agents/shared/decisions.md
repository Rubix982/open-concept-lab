# Shared Decisions

_Owned by: Engineer. All agents read. Append-only._

---

## [O-004] Decision: Semantic Scholar API — rate limiting and backoff required

_Date: 2026-04-12_

**Decision:** All Semantic Scholar API calls must implement exponential backoff and
respect the 1 RPS rate limit. This is a hard requirement agreed to in the API
license during registration — not optional.

**Rules for any code that calls the Semantic Scholar API:**
1. **Rate limit**: never exceed 1 request per second. Use `time.sleep(1.0 / rps)`
   between calls with `rps ≤ 0.9` as the default (stay safely under the limit).
2. **Exponential backoff**: on any 429 (Too Many Requests) or 5xx response, wait
   `min(2^attempt * base_delay, max_delay)` before retrying. Defaults:
   `base_delay=1.0s`, `max_delay=60.0s`, `max_attempts=5`.
3. **Jitter**: add random jitter (`random.uniform(0, 0.5) * delay`) to backoff
   to avoid thundering herd if multiple processes run simultaneously.
4. **Respect Retry-After**: if the response includes a `Retry-After` header, use
   that value instead of computed backoff.
5. **Never hammer on error**: if 5 consecutive retries fail, log and skip — do not
   loop indefinitely.
6. **API key inactive warning**: keys inactive for 60+ days may be revoked. Ensure
   at least one API call is made every ~45 days if the key is to be kept active.

**Rationale:** We agreed to these terms in the API license agreement. Violating
rate limits risks key revocation and is inconsiderate to a free public resource.

**Applies to:** `pipeline/embedder.py` (fetch_embeddings_per_paper), any future
code that calls api.semanticscholar.org.

---

## [O-000] Decision: Python Environment — dedicated venv required

_Date: 2026-04-05_

**Decision:** All work runs inside `.venv`. Never install into system Python.
**Workflow:** `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt`. After any new install: `pip freeze > requirements.txt` immediately.
**Rationale:** `requirements.txt` is only authoritative if the venv is the source of truth.

---

## [R-001] Decision: Citation Data Source — OpenAlex over S2ORC

_Date: 2026-04-05_

**Decision:** Use OpenAlex for citation edges. Do not use S2ORC.
**Rationale:** S2ORC original bulk download links are defunct. OpenAlex is CC0
licensed, requires no API key, is freely accessible via S3, and has 271M papers.
**Alternatives rejected:** S2ORC bulk (dead links); Semantic Scholar Datasets API
(requires API key registration, ODC-By license adds attribution overhead).
**Revisit if:** OpenAlex coverage of arXiv papers proves insufficient (<70% of
target corpus has citation data).

---

## [O-002] Decision: Working Scale — 500K for comparative experiments

_Date: 2026-04-04_

**Decision:** Run all pre-training and prompting comparison experiments at 500K papers.
Scale to 1M in Phase 4.
**Rationale:** 500K is 3× larger than any published GNN prompting benchmark (OGB-arxiv
is 169K). A full pre-training run at 500K is ~5 hours on M2 — tractable per weekend.
At 2M, a single run is ~30–40 hours, making comparison studies infeasible on M2.
**Alternatives rejected:** 100K (too close to existing benchmarks, less impressive);
2M (impractical for comparative study on M2).
**Revisit if:** 500K runs consistently OOM on M2 during training.

---

## [O-002] Decision: Pre-training Implementation Order

_Date: 2026-04-04_

**Decision:** Implement GraphMAE first, then SimGRACE, DGI, GraphCL, EdgePre.
**Rationale:** GraphMAE is the best theoretical fit for rich SPECTER2 features (masked
reconstruction rewards feature richness). It is also the most memory-efficient method,
making it the safest first implementation on M2.
**Alternatives rejected:** DGI first (classic but less suited to rich features);
EdgePre first (good for link prediction but doesn't help classify).
**Revisit if:** GraphMAE implementation reveals fundamental incompatibility with
heterogeneous graph structure.

---

## [O-002] Decision: Prompting Implementation Order

_Date: 2026-04-04_

**Decision:** Implement GPF-plus first, then Gprompt, GPPT, All-in-one.
**Rationale:** GPF-plus is the simplest prompting method (adds a learnable vector
to node features) and establishes the baseline. All-in-one is the target for
multi-task prompting but is the most complex — work up to it.
**Alternatives rejected:** All-in-one first (too complex to debug without simpler
baseline).
**Revisit if:** GPF-plus fails completely at 500K scale (would suggest scale issues
with prompting in general, worth escalating before building more complex methods).

---

## [E-005] Decision: arxiv_bulk.py — Implementation Choices

_Date: 2026-03-29_

**Decision: Year/month extraction priority** — Use `update_date` (format `YYYY-MM-DD`)
as the primary source for year/month. Fall back to parsing the arXiv ID itself only for
new-format IDs (no `/`) when `update_date` is absent or malformed. Old-format IDs
(containing `/`, e.g. `math/0406594`) cannot encode a reliable date in the ID, so they
only get year/month from `update_date`.
**Rationale:** `update_date` is present in virtually all records and is authoritative.
New-format IDs embed YYMM as the first four digits, which is a reliable fallback.
Old-format IDs predate the YYMM convention and must rely on `update_date`.

**Decision: Missing abstract** — Use `" ".join(... .split())` on `(record.get("abstract", "") or "")`.
The `or ""` handles the case where the field exists but has a `null` JSON value, producing
an empty string rather than `None` or raising an AttributeError.
**Rationale:** Downstream embedding models (SPECTER2) handle empty abstracts gracefully;
the spec says "use empty string" for missing abstracts.

**Decision: Checkpoint scoping** — The checkpoint file is keyed to `snapshot_path` only
(`snapshot_path.with_suffix('.checkpoint.parquet')`), not to the filter arguments.
A single snapshot file is expected to map to a single resume-able run with fixed filter
parameters. Callers using different filters on the same snapshot should use separate
output paths (or snapshot copies) to avoid checkpoint contamination.
**Rationale:** Matches the spec's wording ("save progress to a `.parquet` file at
`snapshot_path.with_suffix('.checkpoint.parquet')`"). Keeping the checkpoint path
deterministic and simple avoids complex cache-key logic.

**Decision: Resume skip logic** — On resume, the number of already-saved rows from the
checkpoint is used to skip that many qualifying papers in the stream (not by comparing
IDs). This is safe because the stream is deterministic for a given snapshot file and
filter configuration — the same papers always appear in the same order.
**Rationale:** ID-based skipping would require loading a set of all checkpoint IDs into
memory, adding ~8 bytes × N overhead. Row-count skipping is O(1) in memory and correct
for deterministic streams.

---

## [E-006] Decision: embedder.py — Implementation Choices

_Date: 2026-03-29_

**Decision: No np.save() on open memmap** — L2 normalisation is done in-place on the
memory-mapped array, followed by `flush()` rather than `np.save()`.  Calling `np.save()`
on a file that is simultaneously open as a writable memmap can deadlock on macOS (the OS
tries to write to a file whose mmap handle is still held).  The in-place write + flush is
sufficient: the `.npy` header is already written by `np.lib.format.open_memmap` at
creation time, and the data region is updated in-place.
**Rationale:** Observed hang in validation testing when `np.save()` was called on an
`open_memmap`-created array. The fix (in-place modify + flush) is safe and idiomatic.

**Decision: Checkpoint shared across all three paths** — All three paths (bulk, per-paper,
local) read and append to the same `checkpoint_path` JSON file.  Any path can resume from
where any other path left off (e.g. if bulk succeeds for 80% and crashes, per-paper
resumes for the remaining gap without re-embedding anything).
**Rationale:** Simpler than per-path checkpoints; correct because `arxiv_id → row_index`
is globally unique regardless of which path wrote the entry.

**Decision: api_key=None fast-path** — When `api_key=None`, Paths 1 and 2 are
unconditionally skipped and the function delegates entirely to `embed_locally()`.  Makes
the pipeline usable offline (CI, dev machines without S2 keys) without network access.
**Rationale:** Matches the spec; also makes unit-testing trivial (mock embed_locally only).

**Decision: corpusId join via papers dataset** — Path 1 downloads all `papers` dataset
shards to build the `corpusId → arxiv_id` map.  Each shard is cached locally so only new
shards need to be re-downloaded on resume.
**Rationale:** The `embeddings-specter_v2` dataset uses `corpusId` as its only key (not
arXiv ID), so the join is mandatory for bulk access.  Path 2 uses `ArXiv:{id}` directly
and does not require this join.

---

## [E-007] Decision: citations.py — Implementation Choices

_Date: 2026-03-29_

**Decision: HTTP transport** — Use boto3 with `UNSIGNED` config when available; fall back
to `urllib.request` over `https://openalex.s3.amazonaws.com/` when boto3 is absent.
**Rationale:** boto3 is not in requirements.txt and the OpenAlex S3 bucket is a public
no-credentials bucket, so urllib is sufficient as a stdlib-only fallback. The guard
follows the same try/except import pattern as the pandas guard in arxiv_bulk.py.

**Decision: Two logical passes, one physical pass per shard** — Each shard is opened once.
The first pass simultaneously builds `openalex_url → arxiv_id` (for all works with an
arXiv ID) and collects raw `(source_arxiv_id, target_openalex_url)` edge pairs (for works
whose arXiv ID is in `known_arxiv_ids`). Resolution (URL → arXiv ID → filter) runs after
all shards are processed.
**Rationale:** A strict two-file-pass design would require reading each shard twice
(4× I/O for a typical run). The single-pass approach is equivalent because the URL→arXiv
map and the raw edges are accumulated in memory together. Cross-shard forward references
are resolved after the final shard completes, which is correct.

**Decision: `ids.arxiv` normalisation** — Strip known URL prefixes
(`https://arxiv.org/abs/`, `http://arxiv.org/abs/`, `arxiv:`) case-insensitively.
Return the bare ID unchanged if no prefix is found.
**Rationale:** OpenAlex sometimes stores the arxiv field as a full URL; the working set
uses bare IDs (e.g. `2106.01234`). Normalisation ensures lookup correctness.

**Decision: `build_id_to_index()` sorts lexicographically** — Index is assigned by
`sorted(set(arxiv_ids))`. Reproducible across runs with the same corpus.
**Rationale:** arXiv IDs have a date-prefixed structure (YYMM.NNNNN) so lexicographic
order is also roughly chronological, which is a sensible default ordering.

**Decision: `assign_indices()` drops silently** — Edges where either endpoint is absent
from `id_to_index` are dropped without warning.
**Rationale:** This is the standard behaviour for graph sub-sampling; callers that need
coverage diagnostics should compare `len(edges.source_ids)` before and after.

**Decision: progress.json keyed on shard S3 key** — Completed shards are stored as a
sorted list of S3 key strings in `cache_dir/progress.json`.
**Rationale:** S3 keys are stable identifiers for shard files. JSON is human-readable
and easy to inspect/edit manually if a shard needs re-processing.

---

## [E-008] Decision: graph_builder.py — Implementation Choices

_Date: 2026-03-29_

**Decision: co_category pairs capped at 1,000 per category** — When grouping papers
by category to emit co_category edges, at most 1,000 (source, target) directed pairs
are emitted per category before the inner loop breaks.  After symmetrisation and
`np.unique` deduplication, the maximum undirected edges contributed by any single
category is 2,000.
**Rationale:** cs.LG alone has ~300K papers in the full arXiv corpus.  All-pairs
within cs.LG = ~45 billion edges — obviously infeasible.  At 10K scale (~3K cs.LG
papers) it is still ~4.5M edges from one category, which bloats the graph without
adding useful signal (every cs.LG paper would be adjacent to every other via this
edge type, collapsing the category's subgraph to a clique).  A cap of 1,000 pairs
keeps co_category informative as a structural signal while remaining O(N) in space.
The cap is a module-level constant `_CO_CATEGORY_CAP = 1_000` that callers can
inspect; the cap decision and value are also recorded here.
**Alternatives rejected:** No cap (O(N²) blowup); cap by sampling (randomises which
pairs survive, non-deterministic across runs); cap by degree-truncation (complex).
**Revisit if:** 1,000 turns out too sparse at 10K scale — re-run with cap=10_000
and check whether boundary paper classification improves.

**Decision: category index is `sorted(set(all categories))`** — Sorted for
determinism across Python runs.  The category index is stored on the graph as
`graph["category"].category_to_idx` (a Python dict) so downstream code and
`validate_graph()` can cross-check without a separate side-channel.
**Rationale:** Deterministic index is critical for reproducibility — the same paper
must get the same `primary_category_idx` across all runs.

**Decision: embeddings copied before L2-normalise in `build_knn_edges()`** — The
function copies `embeddings` before calling `faiss.normalize_L2()` (which is in-place).
**Rationale:** Callers may need the original un-normalised embeddings for other
purposes (e.g. computing cosine similarity outside FAISS, or the embedder's own
L2-normalised copy is used here but the original memmap should remain intact).
Matches the E-006 decision to never mutate the memmap after it is written.

**Decision: `validate_graph()` infers `is_interdisciplinary` from `paper.y`** — Check
6 recomputes expected flags as `(y.sum(dim=1) >= 2)` and compares to the stored bool
tensor.  This avoids storing the raw `categories` list on the graph node storage.
**Rationale:** The multi-hot `y` matrix is already stored on the graph; it encodes
exactly the same information as `categories` for the purpose of the
interdisciplinary flag.  No additional attribute needed.

---

## [E-003] Decision: Pipeline Stub Interface Design

_Date: 2026-04-05_

**Decision:** All pipeline modules use `PipelineConfig` dataclass for configuration.
No global state. Each module is independently importable and testable.
**Rationale:** Consistent with existing codebase patterns in `data.py` and
`arxiv_data.py`. Enables unit testing each stage without running the full pipeline.
**Interface contracts:**
- `arxiv_bulk.py` → outputs `pd.DataFrame` + `.jsonl` checkpoint
- `embedder.py` → outputs memory-mapped `.npy` + per-ID checkpoint
- `citations.py` → outputs `CitationEdges` dataclass
- `graph_builder.py` → outputs PyG `HeteroData`
- `sampling.py` → outputs PyG `NeighborLoader`

---

## [E-010] Decision: load_openalex_citations_api() — Implementation Choices

_Date: 2026-03-29_

**Decision: `_api_get()` helper owns all retry/backoff/sleep logic** — All rate
limiting, retry, exponential backoff, jitter, and `Retry-After` handling is
centralised in a single `_api_get()` helper.  The main function never calls
`time.sleep` or inspects HTTP status codes directly.
**Rationale:** Keeps `load_openalex_citations_api()` readable and makes the
retry behaviour independently testable (Test 2, 3, 4 in the validation script
call `_api_get()` directly).

**Decision: Jitter formula is `delay += random.uniform(0, 0.5) * delay`** —
Up to 50% of the computed backoff is added as random jitter.  So a 2-second
backoff becomes 2.0–3.0 seconds randomly.
**Rationale:** Matches the O-004 spec (`random.uniform(0, 0.5) * delay`).
Using multiplicative jitter (not additive) keeps jitter proportional to the
backoff magnitude, which is better at separating concurrent processes at
longer backoffs.

**Decision: Pass 1 cache written after EACH batch** — The JSON cache is
flushed to disk immediately after each Pass 1 batch completes.
**Rationale:** Crash-safe resume — if the process is killed mid-run, the next
invocation will skip all batches processed so far.  The cost (one JSON write
per batch) is negligible compared to the HTTP round-trip.

**Decision: `requests_per_second` hard-clamped to 9.0** — Even if the caller
passes a higher value, `rps = min(requests_per_second, 9.0)` is enforced
inside the function before any requests are made.
**Rationale:** OpenAlex's documented limit is 10 RPS.  Staying at 9.0 leaves
a 10% safety margin.  The clamp makes the O-004 constraint automatic rather
than relying on callers to pass a safe value.

**Decision: Pass 2 strips full OpenAlex URL to bare work-ID** — Referenced
work URLs like `https://openalex.org/W123456` are stripped to `W123456` for
the `openalex_id:` filter query.  The original full URL is retained as the
lookup key for the `openalex_url → arxiv_id` resolution map.
**Rationale:** The OpenAlex API filter `openalex_id:W123` expects the bare ID
format.  Keeping the full URL as the internal map key avoids a second
URL-reconstruction step when writing to `openalex_to_arxiv`.

---

## [E-009] Decision: sampling.py — num_workers=0 MPS Constraint

_Date: 2026-03-29_

**Decision:** `build_neighbor_sampler` and `get_dataloaders` both hard-default
`num_workers=0`.  `get_dataloaders` does not expose `num_workers` as a parameter
at all (always 0).  `build_neighbor_sampler` accepts it as a keyword argument but
documents it prominently as a footgun.
**Rationale:** PyTorch Geometric's `NeighborLoader` with `num_workers > 0` spawns
Python sub-processes via the standard DataLoader worker mechanism.  On macOS with
Apple Silicon (M1/M2/M3), those worker processes cannot inherit the parent's MPS
device context.  The result is a silent hang at the first `.next()` call or an
immediate crash with a cryptic MPS error.  Setting `num_workers=0` forces
single-process iteration, which is safe and sufficient for the batch sizes used in
this project (512 seed nodes, 10K–500K graph).

**Decision:** `edge_types` filter matches the **relation string** (middle element
of the `(src_type, rel, dst_type)` triplet), not the full triplet.
**Rationale:** Callers working with the graph conceptually think in terms of
relation names ("cites", "similar_to") rather than full triplets.  The triplet
structure is an internal PyG detail.  Filtering by relation string is more ergonomic
and avoids requiring callers to know (or spell out) the src/dst node types.

**Decision:** `get_dataloaders` constructs three independent `NeighborLoader`
instances (one per split) with the same `num_neighbors` dict.  The dict is built
once and reused.
**Rationale:** `NeighborLoader` takes `input_nodes=('paper', mask)` to restrict
seed nodes to a given split.  There is no way to share a single loader across
splits with different masks — each split needs its own loader.  Building the
`num_neighbors` dict once avoids repeating the edge-type filtering logic.

---

## [E-012] Decision: FAISS + PyTorch OpenMP conflict on macOS Apple Silicon

_Date: 2026-04-12_

**Decision:** Never import `faiss` and `torch` in the same process on macOS. `graph_builder.py` now auto-detects whether torch is in `sys.modules` and automatically uses `sklearn.NearestNeighbors` instead of FAISS when both would be present.

**What happens:** FAISS bundles its own OpenMP runtime. PyTorch bundles a different one. When both are loaded in the same process on macOS, the result is either a segfault (exit 139) or a silent hang (process never returns). `KMP_DUPLICATE_LIB_OK=TRUE` suppresses the error message but does NOT fix the underlying conflict.

**Rule:** Any code that uses FAISS must either (a) not import torch, or (b) use `use_sklearn_fallback=True` in `build_knn_edges()`. For the graph building pipeline (which always has torch imported), sklearn is the correct path.

**Performance:** sklearn brute-force k-NN on 10K × 768 takes ~22 seconds — acceptable. At 100K it will be much slower; revisit with a subprocess-based FAISS isolator for Phase 1.

**Applies to:** `pipeline/graph_builder.py`, any future code mixing FAISS and PyTorch.

---

## [E-012] Decision: OpenAlex does not index referenced_works for arXiv preprints

_Date: 2026-04-12_

**Decision:** The `referenced_works` field in OpenAlex is empty for arXiv preprints that were never published in a journal. Only papers with publisher metadata (journal articles with DOIs registered in CrossRef) have outgoing citation data in OpenAlex.

**Impact:** For a corpus of recent arXiv preprints, citation edges will be near-zero via OpenAlex. The integration test confirmed 0 citation edges for 10K cs.* papers from 2022-2023.

**Fix for Phase 1:** Consider Semantic Scholar API which extracts references directly from PDF text — it has much better preprint coverage. Alternatively, accept that `cites` edges are sparse and rely on `similar_to` (k-NN) edges as the primary graph structure for arXiv preprints.

---

## [E-012] Decision: arxiv_id must not be stored as HeteroData node attribute

_Date: 2026-04-12_

**Decision:** `graph["paper"].arxiv_id` was removed. PyG's `NeighborLoader` tries to batch ALL node attributes into tensors during mini-batch construction. A Python list of strings cannot be batched and raises "invalid feature tensor type".

**Rule:** Only store tensors (float32, int64, bool) as HetggeroData node attributes. Non-tensor metadata (string IDs, category names) must be kept in separate Python dicts external to the graph.

**Correct pattern:** maintain `id_to_index = build_id_to_index(arxiv_ids)` separately; look up node IDs by integer index when needed.

---

## [E-013] Decision: knowledge/schema.py — DuckDB schema design choices

_Date: 2026-03-29_

**Decision: L3 tables created upfront with full CHECK constraints** — All five domain
tables (chunks, paper_summaries, claims, claim_sources, claim_edges) plus `_meta` are
created at `init_database()` time, even though Phase 1 only writes L1/L2 data.  The
`claims`, `claim_sources`, and `claim_edges` tables carry their full CHECK constraints
(`claim_type`, `epistemic_status`, `edge_type`) from day one.
**Rationale:** Schema migrations on DuckDB are painful — there is no `ALTER TABLE ADD
CONSTRAINT`.  Defining constraints now avoids a destructive drop-and-recreate when
Phase 2 begins populating L3.  Empty tables with correct constraints are zero cost.

**Decision: No foreign keys on `claim_sources` or `claim_edges`** — The ticket DDL
spec uses `VARCHAR NOT NULL` (not `REFERENCES claims(claim_id)`) for `claim_id`
columns in `claim_sources` and `claim_edges`.  DuckDB parses `REFERENCES` syntax but
does NOT enforce FK constraints at DML time (it is a no-op).  Keeping the columns as
plain `NOT NULL` avoids the false impression of enforced referential integrity while
matching the spec.
**Rationale:** Referential integrity is enforced at the application layer
(`ingest.py`, `extract_l3.py`) where the claim must exist before sources/edges are
written.  Relying on silent DuckDB FKs would be misleading.

**Decision: `get_connection` is a thin wrapper — does not call `init_database`** —
`get_connection(db_path)` opens and returns a connection; it does not create tables.
Callers are expected to have called `init_database()` previously.
**Rationale:** Separates the "ensure schema exists" concern from the "open a
connection" concern.  Callers that only want to read from an already-initialised DB
should not pay the cost of re-running all DDL.  The two functions have distinct
semantics and are both named in the public API.

**Decision: `INSERT OR REPLACE` for `_meta` versioning** — After creating tables,
`init_database` runs `INSERT OR REPLACE INTO _meta VALUES ('version', ?)` to stamp the
DB version.  This is idempotent on re-initialisation.
**Rationale:** `INSERT OR REPLACE` is DuckDB's idiomatic upsert syntax (equivalent to
`INSERT INTO ... ON CONFLICT (key) DO UPDATE SET value = excluded.value`).  It keeps
the version row current on any future schema upgrade that bumps
`KNOWLEDGE_DB_VERSION`.

---

## [O-005] Decision: SQLite over DuckDB for knowledge infrastructure

_Date: 2026-04-12_

**Decision:** Use SQLite (stdlib `sqlite3`) instead of DuckDB for `data/knowledge/knowledge.db`.
**Rationale:** DuckDB allows only one writer connection at a time. Parallel extraction
pipelines (L2 extraction for multiple papers simultaneously) would block on each other.
SQLite with WAL mode (`PRAGMA journal_mode=WAL`) supports concurrent readers and one
writer, and requires no additional install.
**How to apply:** All `src/knowledge/` modules use `sqlite3` from stdlib.
JSON fields stored as TEXT — use `json.dumps()` on write, `json.loads()` on read.
Always call `conn.commit()` after DML operations.
**Revisit if:** Query complexity grows to require DuckDB's analytical SQL features
(window functions, ASOF joins, etc.).

---

## [E-015] Decision: extract_l2.py — Implementation Choices

_Date: 2026-03-29_

**Decision: timeout=90s instead of ticket stub's 60s** — The first Ollama call
in a session incurs a model-load overhead (~10-12s on M2 for qwen2.5-coder:7b).
Combined with a heavy abstract and JSON generation, 60s is tight. 90s provides
safe headroom without meaningfully delaying the batch pipeline.
**Rationale:** Observed first-paper latency of 11.2s during validation. With a
60s timeout the cold-start case could timeout spuriously on a loaded M2.

**Decision: `_validate_summary()` coerces list fields from strings** — The model
occasionally returns a JSON string (e.g. `"key_findings": "finding one"`) rather
than a list for list-typed fields. `_validate_summary()` wraps non-list values as
`[str(val)]` rather than failing.
**Rationale:** Prevents DB insert from failing on a type mismatch. Downstream
consumers (L3 extraction, query interface) always receive a list, regardless of
model output variance.

**Decision: retry prepends `_RETRY_PREFIX` to the full original prompt** — On
`json.JSONDecodeError` in attempt 1, attempt 2 prepends "Return ONLY a JSON
object, no other text:" before the full prompt (including schema and rules).
**Rationale:** The prefix reinforces the JSON-only constraint without discarding
the schema instructions. A replacement prompt without the schema would lose the
field definitions that guide extraction quality.

**Decision: `INSERT OR REPLACE` for paper_summaries** — Re-running with
`skip_existing=False` or after a partial failure will overwrite the row rather
than raise a `UNIQUE constraint` error.
**Rationale:** Idempotent inserts make reruns safe. The alternative (`INSERT OR
IGNORE`) would silently skip re-extraction if a row exists but is incomplete (e.g.
from a partial failure where only defaults were written). `OR REPLACE` ensures the
latest successful extraction always wins.

**Decision: skip_existing uses a pre-fetched in-memory set** — All existing
`arxiv_id` values are loaded in one `SELECT arxiv_id FROM paper_summaries` query
at the start of `extract_batch()`. Per-paper lookup is O(1) set membership.
**Rationale:** N round-trips to SQLite at 6s/paper (Ollama latency) would add
negligible absolute time, but the single-query pattern is consistent with
`ingest.py` and is correct regardless of batch size.

---

## [E-014] Decision: ingest.py — L1 paper ingest implementation choices

_Date: 2026-03-29_

**Decision: `embedding_row` = DataFrame `iloc` index** — The `embedding_row` field
in each chunk record is set to the paper's positional index in the input DataFrame
(i.e. `idx` from `itertuples`), not the original DataFrame index.  This aligns with
how `embeddings_10k.npy` was produced — the embedder outputs one row per paper in
DataFrame order, so row 0 in the `.npy` corresponds to `papers.iloc[0]`.
**Rationale:** The embeddings file was written sequentially during `embed_papers()`,
which iterates the DataFrame in positional order.  Using `iloc` index (not `.index`)
ensures alignment even when the caller passes a reset-indexed subset.

**Decision: `INSERT OR IGNORE` instead of `INSERT`** — The SQL is `INSERT OR IGNORE
INTO chunks ...`.  The `skip_existing` pre-fetch set is the primary deduplication
mechanism (avoids wasted work); `INSERT OR IGNORE` is a safety net for concurrent
writers or edge cases where the pre-fetch set is stale.
**Rationale:** Matching behaviour of existing pipeline modules.  `INSERT OR IGNORE`
never raises and never overwrites existing data, which is correct for an idempotent
ingest.

**Decision: Pre-fetch all existing `chunk_id` values once** — When `skip_existing=True`,
one `SELECT chunk_id FROM chunks` query loads all existing IDs into a Python `set`.
Per-row existence checks are then O(1) in-process lookups rather than N round-trips.
**Rationale:** For a 10K ingest over an existing 9K-row table, N individual `SELECT`
calls would add measurable overhead.  The set fits easily in RAM (each chunk_id is
~20 chars = ~20 bytes × 10K ≈ 200 KB).

**Decision: `mmap_mode="r"` for embeddings** — The `.npy` file is opened with
`np.load(..., mmap_mode="r")` to read only the array length (used for bounds
checking), then the reference is discarded.  The full 10K × 768 float32 array
(~30 MB) is never loaded into memory by this function.
**Rationale:** `ingest.py` does not need the embedding values — it only stores the
row index.  Memory-mapping for a shape check avoids reading 30 MB unnecessarily.

---

## [E-016] Decision: query.py — numpy cosine search and model caching

_Date: 2026-03-29_

**Decision: numpy dot-product instead of FAISS** — `query.py` uses
`embeddings @ query_vec` (numpy matrix-vector dot product) for k-NN search
rather than FAISS.  FAISS is never imported in this module.
**Rationale:** E-012 established that FAISS and PyTorch cannot coexist in the
same process on macOS Apple Silicon due to conflicting OpenMP runtimes (either
segfault or silent hang, even with `KMP_DUPLICATE_LIB_OK=TRUE`).  Since
`query.py` must import PyTorch to run SPECTER2 inference, FAISS is categorically
excluded.  Numpy dot-product on L2-normalised vectors is equivalent to cosine
similarity.  Performance on 10K × 768 is sub-second; revisit for 100K+ scale.

**Decision: module-level `_MODEL_CACHE` dict** — SPECTER2 tokenizer and model
are cached in a module-level `_MODEL_CACHE: dict` keyed by `(model_name, device)`
tuple.  Subsequent calls to `search_papers()` in the same process skip model
loading entirely.
**Rationale:** SPECTER2 loading takes ~10–20s on cold start (model download +
adapter loading + device transfer).  For any workload with multiple sequential
queries (CLI loop, batch evaluation), caching is essential.  The dict approach
supports multiple (model, device) combinations without global singletons.

**Decision: query embedded as raw text (no sep_token)** — For free-text queries,
the query string is passed directly to the tokenizer without the
`title + sep_token + abstract` format used for paper ingestion.
**Rationale:** The `sep_token` format is for SPECTER2's proximity adapter, which
was trained on (title, abstract) pairs.  A free-text query does not have a title
and abstract — wrapping it in that format would add noise.  The query is treated
as a short document and the model handles it correctly as-is.

**Decision: `mmap_mode="r"` for embeddings in query** — The embeddings matrix is
opened read-only with `np.load(..., mmap_mode="r")` so only accessed pages are
paged into RAM.  The full 10K × 768 float32 array (~30 MB) must be loaded for the
matrix multiply; mmap allows the OS to manage this efficiently.
**Rationale:** Consistent with E-014 mmap pattern.  Also prevents any accidental
mutation of the embeddings file during query execution.

---

## [E-022] Decision: derive_edges.py — paper_edges table and edge-building choices

_Date: 2026-03-29_

**Decision: New `paper_edges` table instead of `claim_edges`** — L2-derived relational
edges (`shares_method`, `co_domain`) are stored in a new `paper_edges` table, not in the
existing `claim_edges` table.
**Rationale:** `claim_edges` has a `CHECK (edge_type IN (...))` constraint that does not
include the new types. SQLite does not support `ALTER TABLE ADD CONSTRAINT`, so adding
types to the CHECK requires a drop-and-recreate of the table. Storing in a dedicated
`paper_edges` table avoids touching the L3 claim graph schema, keeps the two concerns
cleanly separated, and is zero cost (the table is added to `_ALL_DDL` in `schema.py`).

**Decision: Method name normalisation is lowercase + strip punctuation** — Raw method
strings from L2 extraction are lowercased and all punctuation is replaced with spaces,
then whitespace is collapsed. E.g. `"PINN (Physics-Informed)"` becomes
`"pinn physics informed"`.
**Rationale:** The LLM extraction produces inconsistent capitalisation and punctuation for
the same concept (e.g. `"PINNs"` vs `"physics-informed neural networks"`). Normalisation
dramatically increases the match rate without requiring fuzzy string matching.

**Decision: Edge IDs are deterministic and prefixed** — `edge_id` for method edges is
`method_{method_norm}_{id_a}_{id_b}`; for domain edges it is `domain_{tag}_{id_a}_{id_b}`.
`INSERT OR IGNORE` is used so repeated calls are idempotent.
**Rationale:** Deterministic IDs make re-runs safe and make the edge provenance
(which method or tag caused this edge) human-readable from the ID alone.

**Decision: source_id < target_id (lexicographic order)** — All edges store the
lexicographically smaller `arxiv_id` in `source_id`. The pair `(id_a, id_b)` with
`id_a <= id_b` is enforced at insert time by `_ordered_pair()`.
**Rationale:** Undirected pairs have no natural direction. Enforcing a canonical order
eliminates duplicate edges (e.g. `A→B` and `B→A`) and makes deduplication trivial.

**Decision: Generic domain tags excluded by default** — The default exclusion set is
`{deep_learning, machine_learning, neural_network, AI, artificial_intelligence, NLP,
CV, computer_vision}`. These tags appear in nearly every paper and would create a
near-complete clique.
**Rationale:** Consistent with the co_category cap decision in E-008. Specific tags
like `transformers`, `diffusion_models`, `graph_neural_network` are retained because
they identify a meaningful methodological cluster.

**Results on current corpus (296/353 papers with method/domain fields):**
- 15 shares_method edges (13 distinct methods; corpus is still small)
- 306 co_domain edges (55 distinct tags; capped at 50 per tag)
- Spot-check quality: CLIP, curriculum learning, diffusion model pairs confirmed related

---

## [E-020] Decision: extract_l3.py — L3 claim extraction implementation choices

_Date: 2026-03-29_

**Decision: Both bare array and dict-wrapped response forms handled** — `_parse_claims_response()`
accepts both `[{...}]` (expected) and `{"claims": [{...}]}` (known R-005 failure mode) without
requiring a retry. A single retry with explicit JSON-array instruction prefix is attempted only
when `json.JSONDecodeError` is raised or the parsed object is neither a list nor a recognisable dict wrapper.
**Rationale:** R-005 documented the dict-wrapped form as a known failure mode. Handling it
in the parser avoids a wasted retry round-trip for a predictable model behavior.

**Decision: `claim_type` clamped to valid enum, defaulting to "empirical"** — If the model
returns an unknown `claim_type` string, it is replaced with `"empirical"` (the most common
type). This ensures the SQLite CHECK constraint is never violated.
**Rationale:** `empirical` is the safest default — it makes the fewest ontological commitments.
The alternative (rejecting the claim) would discard valid assertions when the model uses slight
variations (e.g. `"observation_empirical"`).

**Decision: First-person prefix stripping via regex at normalisation time** — Assertions matching
`^(this paper[,\s]+|we\s+|our\s+)` (case-insensitive) have the prefix stripped. This is applied
by `_validate_claim()` after model output is received, not in the prompt.
**Rationale:** The R-005 prompt's "no this paper / we / our" instruction already suppresses
first-person prefixes for 5/5 papers in testing. The regex strip is a safety net for edge cases,
consistent with R-005's documented approach.

**Decision: `skip_existing` uses suffix-based arxiv_id extraction from claim_id** — The
`existing_arxiv_ids` set is built by stripping the `_NN` suffix from all claim_ids in the DB
(format `{arxiv_id}_{NN}` where NN is exactly 2 digits). This avoids a separate index column
or JOIN.
**Rationale:** Deterministic claim_id format makes this safe and efficient. The strip is O(1)
per claim_id and the set membership check is O(1). A separate index column would require a
schema change.

**Decision: `max_claims=3` parameter controls prompt count request** — The prompt includes
"Extract exactly {max_claims} claims if possible, fewer only if the paper has fewer distinct
assertions." per R-005 recommendation. The model currently returns 1 claim despite this
instruction (known R-005 behavior). The parameter is preserved for future prompt tuning.
**Rationale:** R-005 explicitly noted "1 claim even when abstract contains 3+ assertions —
prompt needs 'extract AT LEAST 3'". The instruction is correct per spec; model compliance
varies. No further prompt engineering is in scope for E-020.

**Validation results:** 10/10 checks passed on first run.
- Avg claims/paper: 1.00 (model compliance with max_claims=3 instruction TBD)
- All claim_types valid, assertions non-empty, no first-person prefixes
- claim_id format correct, claim_sources coverage 100%, resume idempotent
