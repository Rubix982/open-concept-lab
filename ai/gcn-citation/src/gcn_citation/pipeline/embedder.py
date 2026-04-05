"""SPECTER2 embedding pipeline with hybrid download and MPS batching.

Embeds arXiv papers using precomputed SPECTER2 embeddings from the Semantic
Scholar Datasets API where available, falling back to local inference with
``allenai/specter2_base`` + adapters for papers not found in bulk or per-paper
API endpoints.

**Three-path hybrid strategy (tried in order)**:

1. **Bulk S3 download** — Downloads ``embeddings-specter_v2`` shards from
   Semantic Scholar, filtered to the target corpus (~80–95% coverage for
   arXiv cs.* papers).  Requires a free API key.

2. **Per-paper API gap-fill** — For papers not found in bulk, calls the Graph
   API at ``/graph/v1/paper/ArXiv:{id}?fields=embedding.specterv2`` at ≤1 RPS.

3. **Local SPECTER2 inference** — For papers missing from both API paths (very
   new preprints), runs local inference with ``allenai/specter2_base`` + the
   proximity adapter.  Requires ``torch``, ``transformers``, and ``adapters``.

Output is a float32 array of shape ``[N, 768]`` stored as a memory-mapped
``.npy`` file, L2-normalised across all rows after all paths complete.
Checkpoint JSON maps ``arxiv_id → row_index`` for resume support.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:
    import torch
    from transformers import AutoTokenizer
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]

try:
    import adapters  # noqa: F401 — checked at call time
except ImportError:  # pragma: no cover
    adapters = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_S2_DATASETS_BASE = "https://api.semanticscholar.org/datasets/v1"
_S2_GRAPH_BASE = "https://api.semanticscholar.org/graph/v1"
_EMBEDDING_DIM = 768


def _s2_get(url: str, api_key: str) -> Any:
    """Perform a GET request to the Semantic Scholar API.

    Args:
        url: Full URL to fetch.
        api_key: Semantic Scholar API key sent as ``x-api-key`` header.

    Returns:
        Parsed JSON response body.

    Raises:
        RuntimeError: If the HTTP response status is not 200.
    """
    req = Request(url, headers={"x-api-key": api_key})
    with urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f"[embedder] HTTP {resp.status} fetching {url}")
        return json.loads(resp.read().decode("utf-8"))


def _s2_get_shard_urls(dataset: str, api_key: str) -> list[str]:
    """Fetch the list of presigned S3 shard URLs for a Semantic Scholar dataset.

    Args:
        dataset: Dataset name, e.g. ``"embeddings-specter_v2"`` or
            ``"papers"``.
        api_key: Semantic Scholar API key.

    Returns:
        List of presigned S3 URLs (one per shard).
    """
    url = f"{_S2_DATASETS_BASE}/release/latest/dataset/{dataset}"
    data = _s2_get(url, api_key)
    return data["files"]


def _download_shard(shard_url: str, dest_path: Path) -> None:
    """Download a single shard file to ``dest_path`` if not already present.

    The shard URL is a presigned S3 URL and requires no authentication headers.

    Args:
        shard_url: Presigned S3 URL to the shard.
        dest_path: Local file path to write (or skip if already exists).
    """
    if dest_path.exists():
        print(f"[embedder] Shard already cached: {dest_path.name}", file=sys.stderr)
        return

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[embedder] Downloading shard → {dest_path.name} ...", file=sys.stderr)
    req = Request(shard_url)
    with urlopen(req) as resp, open(dest_path, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)  # 1 MB chunks
            if not chunk:
                break
            fh.write(chunk)


def _iter_jsonl_gz(path: Path):
    """Iterate over records in a gzipped JSONL file.

    Args:
        path: Path to a ``.jsonl.gz`` file.

    Yields:
        Parsed JSON objects (dicts).
    """
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"[embedder] WARNING: skipping malformed JSONL line: {exc}",
                    file=sys.stderr,
                )


def _load_checkpoint(checkpoint_path: Path) -> dict[str, int]:
    """Load an existing checkpoint JSON file.

    Args:
        checkpoint_path: Path to a JSON file mapping ``arxiv_id → row_index``.

    Returns:
        Dict of ``{arxiv_id: row_index}``.  Empty dict if file does not exist
        or is unreadable.
    """
    if not checkpoint_path.exists():
        return {}
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        print(
            f"[embedder] WARNING: could not read checkpoint ({exc}); starting fresh.",
            file=sys.stderr,
        )
        return {}


def _save_checkpoint(checkpoint: dict[str, int], checkpoint_path: Path) -> None:
    """Persist the checkpoint dict to JSON.

    Args:
        checkpoint: Dict mapping ``arxiv_id → row_index``.
        checkpoint_path: Destination path.
    """
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as fh:
        json.dump(checkpoint, fh)


def _l2_normalize(embeddings: np.ndarray) -> np.ndarray:
    """L2-normalise each row of an embedding matrix in-place.

    Rows that are all zeros (unfilled) are left unchanged.

    Args:
        embeddings: Float32 array of shape ``[N, D]``.

    Returns:
        The same array with each non-zero row normalised to unit L2 norm.
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    nonzero = norms[:, 0] > 0
    embeddings[nonzero] /= norms[nonzero]
    return embeddings


# ---------------------------------------------------------------------------
# Path 1 — Bulk S3 download
# ---------------------------------------------------------------------------


def download_bulk_embeddings(
    arxiv_ids: list[str],
    output_path: Path,
    checkpoint_path: Path,
    *,
    api_key: str,
    cache_dir: Path,
) -> tuple[np.ndarray, set[str]]:
    """Download SPECTER2 embeddings from the Semantic Scholar bulk dataset.

    Implements Path 1 of the hybrid pipeline.  The function:

    1. Fetches presigned S3 URLs for ``papers`` and ``embeddings-specter_v2``
       datasets.
    2. Streams ``papers`` shards to build a mapping from ``corpusId`` to
       ``arxiv_id`` for the target corpus.
    3. Streams ``embeddings-specter_v2`` shards, writing matching vectors into
       ``embeddings`` at the row index determined by ``arxiv_id`` position.
    4. Checkpoints progress after each shard (append to ``checkpoint_path``).
    5. Resumes by skipping shards whose entire output is already in the
       checkpoint.

    Note: This function requires a valid Semantic Scholar API key and active
    internet access.  It does NOT download all 840 GB — each shard is streamed,
    filtered, then discarded.

    Args:
        arxiv_ids: Ordered list of arXiv IDs matching the row order of
            ``output_path``.  Determines which papers to look up.
        output_path: Path to the pre-allocated ``.npy`` embedding file
            (shape ``[N, 768]``, float32).
        checkpoint_path: JSON checkpoint file mapping
            ``{arxiv_id: row_index}``.  Updated after each shard.
        api_key: Free Semantic Scholar API key (``x-api-key`` header).
        cache_dir: Directory where downloaded shard files are cached.
            Shards are not re-downloaded if already present.

    Returns:
        Tuple of:
        - ``embeddings``: Float32 array of shape ``[N, 768]`` with matched
          rows filled in.
        - ``gap_ids``: Set of arXiv IDs for which no ``corpusId`` was found in
          the ``papers`` dataset (these are passed to Path 2).
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # --- Index: arxiv_id → row index ---
    arxiv_id_to_row: dict[str, int] = {aid: i for i, aid in enumerate(arxiv_ids)}
    target_arxiv_set: set[str] = set(arxiv_ids)

    # --- Load existing checkpoint ---
    checkpoint = _load_checkpoint(checkpoint_path)
    already_done: set[str] = set(checkpoint.keys())
    print(
        f"[embedder] Bulk: {len(already_done)} papers already checkpointed.",
        file=sys.stderr,
    )

    # --- Load or build memory-mapped embeddings array ---
    n = len(arxiv_ids)
    if output_path.exists():
        embeddings = np.load(str(output_path), mmap_mode="r+")
        assert embeddings.shape == (
            n,
            _EMBEDDING_DIM,
        ), f"Existing output shape {embeddings.shape} != expected ({n}, {_EMBEDDING_DIM})"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        embeddings = np.lib.format.open_memmap(
            str(output_path), mode="w+", dtype=np.float32, shape=(n, _EMBEDDING_DIM)
        )

    # --- Step 1: Build corpusId → arxiv_id map from 'papers' dataset shards ---
    print("[embedder] Bulk: fetching 'papers' dataset shard URLs ...", file=sys.stderr)
    papers_shard_urls = _s2_get_shard_urls("papers", api_key)
    corpus_to_arxiv: dict[int, str] = {}

    for shard_idx, shard_url in enumerate(papers_shard_urls):
        shard_name = f"papers_{shard_idx:03d}.jsonl.gz"
        shard_path = cache_dir / shard_name
        _download_shard(shard_url, shard_path)

        for record in _iter_jsonl_gz(shard_path):
            external_ids = record.get("externalIds") or {}
            arxiv_id = external_ids.get("ArXiv")
            if arxiv_id and arxiv_id in target_arxiv_set:
                corpus_id = record.get("corpusId")
                if corpus_id is not None:
                    corpus_to_arxiv[int(corpus_id)] = arxiv_id

        print(
            f"[embedder] Bulk: papers shard {shard_idx + 1}/{len(papers_shard_urls)} "
            f"processed — {len(corpus_to_arxiv)} corpusId matches so far.",
            file=sys.stderr,
        )

    # Compute gap set: arxiv IDs with no corpusId found
    matched_arxiv_set: set[str] = set(corpus_to_arxiv.values())
    gap_ids: set[str] = target_arxiv_set - matched_arxiv_set - already_done

    print(
        f"[embedder] Bulk: corpusId map built — "
        f"{len(corpus_to_arxiv)} matched, {len(gap_ids)} in gap set.",
        file=sys.stderr,
    )

    # --- Step 2: Stream embeddings shards, filter, write ---
    print(
        "[embedder] Bulk: fetching 'embeddings-specter_v2' dataset shard URLs ...",
        file=sys.stderr,
    )
    emb_shard_urls = _s2_get_shard_urls("embeddings-specter_v2", api_key)
    matched_corpus_ids: set[int] = set(corpus_to_arxiv.keys())

    for shard_idx, shard_url in enumerate(emb_shard_urls):
        shard_name = f"embeddings_{shard_idx:03d}.jsonl.gz"
        shard_path = cache_dir / shard_name
        _download_shard(shard_url, shard_path)

        shard_hits = 0
        for record in _iter_jsonl_gz(shard_path):
            corpus_id = record.get("corpusId")
            if corpus_id is None or int(corpus_id) not in matched_corpus_ids:
                continue
            arxiv_id = corpus_to_arxiv[int(corpus_id)]
            if arxiv_id in already_done:
                shard_hits += 1
                continue  # already in checkpoint
            row_idx = arxiv_id_to_row[arxiv_id]
            vector = record.get("vector")
            if vector and len(vector) == _EMBEDDING_DIM:
                embeddings[row_idx] = np.array(vector, dtype=np.float32)
                checkpoint[arxiv_id] = row_idx
                already_done.add(arxiv_id)
                shard_hits += 1

        # Checkpoint after each embedding shard
        _save_checkpoint(checkpoint, checkpoint_path)
        print(
            f"[embedder] Bulk: embeddings shard {shard_idx + 1}/{len(emb_shard_urls)} "
            f"— {shard_hits} hits this shard, {len(checkpoint)} total checkpointed.",
            file=sys.stderr,
        )

    return embeddings, gap_ids


# ---------------------------------------------------------------------------
# Path 2 — Per-paper API gap fill
# ---------------------------------------------------------------------------


def fetch_embeddings_per_paper(
    arxiv_ids: list[str],
    embeddings: np.ndarray,
    checkpoint_path: Path,
    *,
    api_key: str,
    requests_per_second: float = 0.9,
) -> tuple[np.ndarray, set[str]]:
    """Fill embedding gaps using the Semantic Scholar per-paper Graph API.

    Implements Path 2 of the hybrid pipeline.  Called with the gap set from
    :func:`download_bulk_embeddings` (papers whose ``corpusId`` was not found
    in the bulk ``papers`` dataset).

    Uses ``GET /graph/v1/paper/ArXiv:{id}?fields=embedding.specterv2``.
    Rate-limited to ``requests_per_second`` (default 0.9, safely under the
    1 RPS limit for personal API keys).

    Note: This function requires a valid Semantic Scholar API key and active
    internet access.  Paths 1+2 together are expected to cover ~80–95% of
    arXiv cs.* papers.

    Args:
        arxiv_ids: Ordered list of arXiv IDs (all N papers), used to look up
            each ID's row index in ``embeddings``.
        embeddings: Partially-filled float32 array of shape ``[N, 768]``.
            Modified in-place.
        checkpoint_path: JSON checkpoint file (same file used by Path 1).
            Already-checkpointed IDs are skipped.
        api_key: Free Semantic Scholar API key.
        requests_per_second: Maximum API request rate.  Default 0.9 stays
            safely under the 1 RPS personal key limit.

    Returns:
        Tuple of:
        - ``embeddings``: Updated array with additional rows filled.
        - ``still_missing``: Set of arXiv IDs for which the API returned no
          embedding (passed to Path 3 for local inference).
    """
    arxiv_id_to_row: dict[str, int] = {aid: i for i, aid in enumerate(arxiv_ids)}
    checkpoint = _load_checkpoint(checkpoint_path)
    already_done: set[str] = set(checkpoint.keys())

    still_missing: set[str] = set()
    delay = 1.0 / requests_per_second

    pending = [aid for aid in arxiv_ids if aid not in already_done]
    print(
        f"[embedder] PerPaper: {len(pending)} papers to fetch via Graph API.",
        file=sys.stderr,
    )

    for i, arxiv_id in enumerate(pending):
        url = f"{_S2_GRAPH_BASE}/paper/ArXiv:{arxiv_id}" f"?fields=embedding.specterv2"
        try:
            req = Request(url, headers={"x-api-key": api_key})
            with urlopen(req) as resp:
                if resp.status != 200:
                    still_missing.add(arxiv_id)
                    continue
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(
                f"[embedder] PerPaper: ERROR fetching {arxiv_id}: {exc}",
                file=sys.stderr,
            )
            still_missing.add(arxiv_id)
            time.sleep(delay)
            continue

        embedding_obj = data.get("embedding") or {}
        vector = embedding_obj.get("vector")
        if vector and len(vector) == _EMBEDDING_DIM:
            row_idx = arxiv_id_to_row[arxiv_id]
            embeddings[row_idx] = np.array(vector, dtype=np.float32)
            checkpoint[arxiv_id] = row_idx
        else:
            still_missing.add(arxiv_id)

        # Checkpoint every 100 papers
        if (i + 1) % 100 == 0:
            _save_checkpoint(checkpoint, checkpoint_path)
            print(
                f"[embedder] PerPaper: {i + 1}/{len(pending)} fetched, "
                f"{len(still_missing)} still missing.",
                file=sys.stderr,
            )

        time.sleep(delay)

    # Final checkpoint save
    _save_checkpoint(checkpoint, checkpoint_path)
    print(
        f"[embedder] PerPaper: done — {len(still_missing)} papers still missing.",
        file=sys.stderr,
    )
    return embeddings, still_missing


# ---------------------------------------------------------------------------
# Path 3 — Local SPECTER2 inference
# ---------------------------------------------------------------------------


def embed_locally(
    arxiv_ids: list[str],
    papers_df: "pd.DataFrame",
    embeddings: np.ndarray,
    checkpoint_path: Path,
    *,
    batch_size: int = 32,
    device: str = "mps",
    model_name: str = "allenai/specter2_base",
) -> np.ndarray:
    """Embed papers locally using SPECTER2 + the proximity adapter.

    Implements Path 3 (last-resort fallback) of the hybrid pipeline.  Used for
    papers that are absent from both the Semantic Scholar bulk dataset and the
    per-paper API — typically very recent preprints not yet indexed by S2AG.

    Requires ``torch``, ``transformers``, and ``adapters`` to be installed.
    Set ``device="cpu"`` when MPS or CUDA are unavailable.

    Input format per paper::

        title + tokenizer.sep_token + abstract

    truncated to 512 tokens.  Uses float32 (bfloat16 is unsupported on MPS;
    float16 is numerically unstable with SPECTER2).

    Args:
        arxiv_ids: Ordered list of arXiv IDs *to embed* (the still-missing set
            from Path 2).  Their row positions are looked up from
            ``papers_df.arxiv_id``.
        papers_df: DataFrame with columns ``arxiv_id``, ``title``, ``abstract``.
        embeddings: Partially-filled float32 array of shape ``[N, 768]``.
            Modified in-place.
        checkpoint_path: JSON checkpoint file (same file used by Paths 1+2).
            Already-checkpointed IDs are skipped.
        batch_size: Number of papers per inference batch.  32–64 works well
            on M2 with 16–32 GB unified memory.
        device: PyTorch device string — ``"mps"``, ``"cuda"``, or ``"cpu"``.
        model_name: HuggingFace model identifier for SPECTER2 base model.
            Default ``"allenai/specter2_base"``.

    Returns:
        The embedding array with locally-inferred rows filled in.

    Raises:
        ImportError: If ``torch``, ``transformers``, or ``adapters`` are not
            installed.
    """
    if torch is None or AutoTokenizer is None:
        raise ImportError(
            "embed_locally() requires torch and transformers. "
            "Install with: pip install torch transformers adapters"
        )
    if adapters is None:
        raise ImportError(
            "embed_locally() requires the 'adapters' library. "
            "Install with: pip install adapters"
        )

    # Enable MPS fallback for ops not natively supported on Apple Silicon
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    # Lazy imports to avoid hard dependency at module level
    from adapters import AutoAdapterModel  # type: ignore[import]

    # --- Index for the full paper set ---
    row_of: dict[str, int] = {
        aid: i for i, aid in enumerate(papers_df["arxiv_id"].tolist())
    }

    checkpoint = _load_checkpoint(checkpoint_path)
    already_done: set[str] = set(checkpoint.keys())

    pending = [aid for aid in arxiv_ids if aid not in already_done]
    if not pending:
        print(
            "[embedder] Local: no papers to embed (all already checkpointed).",
            file=sys.stderr,
        )
        return embeddings

    print(
        f"[embedder] Local: embedding {len(pending)} papers on {device} ...",
        file=sys.stderr,
    )

    # --- Load model and tokenizer ---
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoAdapterModel.from_pretrained(model_name)
    model.load_adapter(
        "allenai/specter2", source="hf", load_as="specter2", set_active=True
    )
    model = model.to(device)
    model.eval()

    # --- Lookup paper text by arxiv_id ---
    text_lookup: dict[str, tuple[str, str]] = {}
    for _, row in papers_df[papers_df["arxiv_id"].isin(set(pending))].iterrows():
        text_lookup[row["arxiv_id"]] = (row["title"], row["abstract"])

    # --- Batch inference ---
    with torch.no_grad():
        for batch_start in range(0, len(pending), batch_size):
            batch_ids = pending[batch_start : batch_start + batch_size]
            texts = []
            valid_ids = []
            for aid in batch_ids:
                if aid not in text_lookup:
                    continue
                title, abstract = text_lookup[aid]
                texts.append(f"{title}{tokenizer.sep_token}{abstract}")
                valid_ids.append(aid)

            if not texts:
                continue

            encoded = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded = {k: v.to(device) for k, v in encoded.items()}

            outputs = model(**encoded)
            # CLS token representation (first token of last hidden state)
            batch_embeddings = outputs.last_hidden_state[:, 0, :].to(
                dtype=torch.float32
            )
            batch_np = batch_embeddings.cpu().numpy()

            for j, aid in enumerate(valid_ids):
                row_idx = row_of[aid]
                embeddings[row_idx] = batch_np[j]
                checkpoint[aid] = row_idx

            # Checkpoint after each batch
            _save_checkpoint(checkpoint, checkpoint_path)

            done = min(batch_start + batch_size, len(pending))
            print(
                f"[embedder] Local: {done}/{len(pending)} embedded.",
                file=sys.stderr,
            )

    return embeddings


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------


def embed_papers(
    papers: "pd.DataFrame",
    output_path: Path,
    checkpoint_path: Path,
    *,
    api_key: str | None = None,
    cache_dir: Path | None = None,
    batch_size: int = 32,
    device: str = "mps",
    model_name: str = "allenai/specter2_base",
) -> np.ndarray:
    """Embed arXiv papers with SPECTER2 using a hybrid three-path strategy.

    Tries three paths in order, using results from earlier paths to avoid
    redundant work:

    1. **Bulk S3 download** (Path 1) — fetches precomputed SPECTER2 embeddings
       from Semantic Scholar bulk dataset.  Skipped if ``api_key`` is ``None``.
    2. **Per-paper API** (Path 2) — fills gaps from Path 1 via Graph API at
       ≤1 RPS.  Skipped if ``api_key`` is ``None``.
    3. **Local inference** (Path 3) — runs SPECTER2 locally for any remaining
       papers.  Always attempted if papers are still missing after Paths 1+2.

    The output array is L2-normalised after all paths complete.

    Checkpoint JSON at ``checkpoint_path`` maps ``arxiv_id → row_index`` and
    is updated incrementally.  On re-entry, already-embedded papers are skipped.

    Args:
        papers: DataFrame with columns ``arxiv_id``, ``title``, ``abstract``.
            Row order determines the row order of the output embedding matrix.
        output_path: Destination ``.npy`` file for the float32 embedding matrix
            of shape ``[N, 768]``.  Created (or resumed) by this function.
        checkpoint_path: JSON checkpoint file.  Created if absent; updated
            after each shard/batch.
        api_key: Semantic Scholar API key.  If ``None``, Paths 1 and 2 are
            skipped and the function falls straight through to local inference.
        cache_dir: Directory for temporarily cached shard files during Path 1.
            Defaults to ``output_path.parent / "s2_shard_cache"``.
        batch_size: Batch size for local SPECTER2 inference (Path 3).
        device: PyTorch device string for local inference — ``"mps"``,
            ``"cuda"``, or ``"cpu"``.
        model_name: HuggingFace model identifier for the SPECTER2 base model.
            Default ``"allenai/specter2_base"``.

    Returns:
        Float32 numpy array of shape ``[N, 768]``, L2-normalised.  The array
        is memory-mapped from ``output_path``.
    """
    if pd is None:
        raise ImportError("pandas is required for embed_papers()")

    required_cols = {"arxiv_id", "title", "abstract"}
    missing_cols = required_cols - set(papers.columns)
    if missing_cols:
        raise ValueError(
            f"papers DataFrame is missing required columns: {missing_cols}"
        )

    arxiv_ids: list[str] = papers["arxiv_id"].tolist()
    n = len(arxiv_ids)

    output_path = Path(output_path)
    checkpoint_path = Path(checkpoint_path)
    if cache_dir is None:
        cache_dir = output_path.parent / "s2_shard_cache"

    # --- Pre-allocate output array if it doesn't exist ---
    if not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        embeddings: np.ndarray = np.lib.format.open_memmap(
            str(output_path), mode="w+", dtype=np.float32, shape=(n, _EMBEDDING_DIM)
        )
        print(
            f"[embedder] Pre-allocated embeddings array: shape=({n}, {_EMBEDDING_DIM}), "
            f"dtype=float32 → {output_path}",
            file=sys.stderr,
        )
    else:
        embeddings = np.load(str(output_path), mmap_mode="r+")
        print(
            f"[embedder] Loaded existing embeddings array: shape={embeddings.shape} "
            f"→ {output_path}",
            file=sys.stderr,
        )

    # --- Load existing checkpoint to find still-missing IDs ---
    checkpoint = _load_checkpoint(checkpoint_path)
    already_done: set[str] = set(checkpoint.keys())
    missing_ids: set[str] = set(arxiv_ids) - already_done
    print(
        f"[embedder] Starting: {len(already_done)} already embedded, "
        f"{len(missing_ids)} remaining.",
        file=sys.stderr,
    )

    if not missing_ids:
        print(
            "[embedder] All papers already embedded; normalising and returning.",
            file=sys.stderr,
        )
        embeddings = _l2_normalize(embeddings)
        if hasattr(embeddings, "flush"):
            embeddings.flush()  # type: ignore[attr-defined]
        return embeddings

    # --- Path 1: Bulk S3 download ---
    gap_ids: set[str] = missing_ids
    if api_key is not None:
        print("[embedder] >>> Path 1: Bulk S3 download ...", file=sys.stderr)
        embeddings, gap_ids = download_bulk_embeddings(
            arxiv_ids,
            output_path,
            checkpoint_path,
            api_key=api_key,
            cache_dir=cache_dir,
        )
        print(
            f"[embedder] Path 1 complete: {len(gap_ids)} papers still missing.",
            file=sys.stderr,
        )
    else:
        print(
            "[embedder] No api_key provided — skipping Path 1 (bulk) and Path 2 (per-paper).",
            file=sys.stderr,
        )

    # --- Path 2: Per-paper API gap fill ---
    still_missing: set[str] = gap_ids
    if api_key is not None and gap_ids:
        print(
            f"[embedder] >>> Path 2: Per-paper API gap fill ({len(gap_ids)} papers) ...",
            file=sys.stderr,
        )
        gap_id_list = [aid for aid in arxiv_ids if aid in gap_ids]
        embeddings, still_missing = fetch_embeddings_per_paper(
            arxiv_ids,
            embeddings,
            checkpoint_path,
            api_key=api_key,
        )
        # still_missing is computed relative to arxiv_ids; filter to gap_ids
        still_missing = still_missing & gap_ids
        print(
            f"[embedder] Path 2 complete: {len(still_missing)} papers still missing.",
            file=sys.stderr,
        )

    # --- Path 3: Local SPECTER2 inference ---
    if still_missing:
        print(
            f"[embedder] >>> Path 3: Local SPECTER2 inference ({len(still_missing)} papers) ...",
            file=sys.stderr,
        )
        still_missing_list = [aid for aid in arxiv_ids if aid in still_missing]
        embeddings = embed_locally(
            still_missing_list,
            papers,
            embeddings,
            checkpoint_path,
            batch_size=batch_size,
            device=device,
            model_name=model_name,
        )

    # --- L2 normalise all rows ---
    # embeddings may be a memory-mapped array (writable); normalise in-place.
    # Do NOT call np.save() on a memmap — it would try to write a second copy
    # of the file while the mmap file handle is still open, which can deadlock
    # on some platforms.  The in-place modification is already reflected in the
    # .npy file on disk (mmap writes through).
    print("[embedder] L2-normalising embeddings ...", file=sys.stderr)
    embeddings = _l2_normalize(embeddings)
    if hasattr(embeddings, "flush"):
        embeddings.flush()  # type: ignore[attr-defined]
    print(f"[embedder] Done. Embeddings saved → {output_path}", file=sys.stderr)

    return embeddings


# ---------------------------------------------------------------------------
# Load helper (finalise stub from E-003)
# ---------------------------------------------------------------------------


def load_embeddings(output_path: Path) -> np.ndarray:
    """Load embeddings as a memory-mapped numpy array (read-only).

    Opens ``output_path`` with ``np.load(..., mmap_mode="r")`` so that only
    the rows accessed during training are paged into memory.

    Args:
        output_path: Path to a ``.npy`` file previously written by
            :func:`embed_papers`.

    Returns:
        A read-only memory-mapped numpy array of shape ``[N, 768]``,
        dtype float32.

    Raises:
        FileNotFoundError: If ``output_path`` does not exist.
    """
    output_path = Path(output_path)
    if not output_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {output_path}")
    return np.load(str(output_path), mmap_mode="r")
