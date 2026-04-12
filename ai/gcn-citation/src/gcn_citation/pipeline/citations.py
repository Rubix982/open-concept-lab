"""Citation edge loading and arXiv-ID-to-index mapping.

Supports two citation data sources:

- **OpenAlex**: CC0-licensed bulk data, freely accessible via S3 with no API
  key required.  Papers are identified via the ``ids.arxiv`` field; outgoing
  citations are stored in ``referenced_works`` as OpenAlex URLs.
- **OpenAlex REST API** (:func:`load_openalex_citations_api`): for smaller
  corpora (≤50 K papers) where the S3 bulk download is impractical.  No API
  key is required; rate-limited to ≤9 RPS by default.
- **S2ORC** (Semantic Scholar Open Research Corpus): bulk download links are
  defunct.  :func:`load_s2orc_citations` raises :exc:`NotImplementedError`
  and directs callers to :func:`load_openalex_citations`.

In all cases only edges where *both* endpoints are in the working paper set
are retained.  String IDs are kept in :class:`CitationEdges` until
:func:`assign_indices` maps them to integer node indices for use in PyG.
"""

from __future__ import annotations

import gzip
import json
import random
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import requests as _requests
except ImportError:  # pragma: no cover
    _requests = None  # type: ignore[assignment]

try:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config as BotocoreConfig

    _BOTO3_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BOTO3_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class CitationEdges:
    """Container for citation edge data at various stages of processing.

    Attributes:
        source_ids: String arXiv IDs of the citing papers, shape ``[E]``.
        target_ids: String arXiv IDs of the cited papers, shape ``[E]``.
        source_indices: Integer node indices for ``source_ids`` after
            :func:`assign_indices` has been called.  ``None`` before mapping.
        target_indices: Integer node indices for ``target_ids`` after
            :func:`assign_indices` has been called.  ``None`` before mapping.
    """

    source_ids: np.ndarray
    target_ids: np.ndarray
    source_indices: np.ndarray | None
    target_indices: np.ndarray | None


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_OPENALEX_BUCKET = "openalex"
_OPENALEX_S3_PREFIX = "data/works/"
_OPENALEX_HTTPS_BASE = "https://openalex.s3.amazonaws.com/"
_PROGRESS_FILENAME = "progress.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _list_openalex_shards() -> list[str]:
    """Return all S3 object keys under the OpenAlex works prefix.

    Tries boto3 first; falls back to an HTTPS listing request using urllib.

    Returns:
        List of S3 keys (strings), e.g. ``["data/works/part_000.gz", ...]``.
    """
    if _BOTO3_AVAILABLE:
        s3 = boto3.client("s3", config=BotocoreConfig(signature_version=UNSIGNED))
        keys: list[str] = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=_OPENALEX_BUCKET, Prefix=_OPENALEX_S3_PREFIX
        ):
            for obj in page.get("Contents", []):
                key: str = obj["Key"]
                # Skip the prefix "directory" entry itself
                if not key.endswith("/"):
                    keys.append(key)
        return keys

    # Fallback: S3 XML listing via HTTPS (unsigned, public bucket)
    url = (
        f"https://{_OPENALEX_BUCKET}.s3.amazonaws.com/"
        f"?list-type=2&prefix={_OPENALEX_S3_PREFIX}"
    )
    with urllib.request.urlopen(url) as resp:
        body = resp.read().decode("utf-8")

    # Parse the XML manually to avoid an lxml/ElementTree dependency mess
    keys = []
    for token in body.split("<Key>")[1:]:
        key = token.split("</Key>")[0]
        if not key.endswith("/"):
            keys.append(key)
    return keys


def _download_shard(key: str, dest: Path) -> None:
    """Download a single OpenAlex shard from S3 to ``dest``.

    Uses boto3 if available, otherwise falls back to urllib over HTTPS.

    Args:
        key: S3 object key, e.g. ``"data/works/part_000.gz"``.
        dest: Local destination path (including filename).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if _BOTO3_AVAILABLE:
        s3 = boto3.client("s3", config=BotocoreConfig(signature_version=UNSIGNED))
        s3.download_file(_OPENALEX_BUCKET, key, str(dest))
        return

    url = _OPENALEX_HTTPS_BASE + key
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)  # 1 MiB chunks
            if not chunk:
                break
            fh.write(chunk)


def _open_shard(path: Path):
    """Open a shard for reading; handles gzip and plain files.

    Args:
        path: Path to a local shard file.

    Returns:
        A file-like object yielding bytes (gzip-transparent).
    """
    if path.suffix in (".gz", ".gzip"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def _load_progress(cache_dir: Path) -> set[str]:
    """Load the set of fully processed shard keys from ``progress.json``.

    Args:
        cache_dir: Directory containing ``progress.json``.

    Returns:
        Set of S3 key strings that have been fully processed.
    """
    progress_path = cache_dir / _PROGRESS_FILENAME
    if not progress_path.exists():
        return set()
    try:
        with open(progress_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return set(data.get("completed_shards", []))
    except Exception as exc:  # noqa: BLE001
        print(
            f"[citations] WARNING: could not read progress.json ({exc}); starting fresh.",
            file=sys.stderr,
        )
        return set()


def _save_progress(cache_dir: Path, completed: set[str]) -> None:
    """Persist the set of completed shard keys to ``progress.json``.

    Args:
        cache_dir: Directory where ``progress.json`` will be written.
        completed: Set of S3 key strings that have been fully processed.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    progress_path = cache_dir / _PROGRESS_FILENAME
    with open(progress_path, "w", encoding="utf-8") as fh:
        json.dump({"completed_shards": sorted(completed)}, fh, indent=2)


def _shard_local_path(key: str, cache_dir: Path) -> Path:
    """Compute a stable local path for a given S3 key.

    The key's path separators are replaced with underscores to produce a flat
    filename inside ``cache_dir``.

    Args:
        key: S3 object key, e.g. ``"data/works/part_000.gz"``.
        cache_dir: Local cache directory.

    Returns:
        Absolute path for the cached shard file.
    """
    filename = key.replace("/", "_")
    return cache_dir / filename


# ---------------------------------------------------------------------------
# Two-pass processing helpers
# ---------------------------------------------------------------------------


def _process_shard_pass1(
    path: Path,
    known_arxiv_ids: set[str],
    openalex_url_to_arxiv: dict[str, str],
    raw_edges: list[tuple[str, str]],
) -> None:
    """First pass over one shard: build URL→arXiv map and collect raw edges.

    For each work record:
    - Extract ``ids.arxiv`` and map the work's OpenAlex URL to that arXiv ID.
    - If the arXiv ID is in ``known_arxiv_ids``, record
      ``(arxiv_id, referenced_openalex_url)`` pairs for later resolution.

    Args:
        path: Local path to the shard file.
        known_arxiv_ids: The working paper set.
        openalex_url_to_arxiv: Mutable map to populate (OpenAlex URL → arXiv ID).
        raw_edges: Mutable list to append ``(source_arxiv_id, target_openalex_url)``
            tuples to.
    """
    line_num = 0
    with _open_shard(path) as fh:
        for line in fh:
            line_num += 1
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"[citations] WARNING: skipping malformed line {line_num} in {path.name}: {exc}",
                    file=sys.stderr,
                )
                continue

            openalex_url: str = record.get("id", "") or ""
            ids: dict = record.get("ids") or {}
            arxiv_raw: str | None = ids.get("arxiv")

            if openalex_url and arxiv_raw:
                # OpenAlex arxiv field sometimes has a URL prefix; strip it
                arxiv_id = _normalise_arxiv_id(arxiv_raw)
                openalex_url_to_arxiv[openalex_url] = arxiv_id

                if arxiv_id in known_arxiv_ids:
                    refs: list[str] = record.get("referenced_works") or []
                    for ref_url in refs:
                        raw_edges.append((arxiv_id, ref_url))


def _arxiv_id_from_doi(doi: str) -> str | None:
    """Extract arXiv ID from an OpenAlex DOI field.

    OpenAlex stores arXiv papers by DOI rather than a dedicated arxiv field.
    All arXiv preprints have a DOI of the form ``10.48550/arXiv.XXXX.XXXXX``
    (or lowercase ``arxiv``).  This helper extracts the bare arXiv ID.

    Args:
        doi: Raw DOI string, e.g. ``https://doi.org/10.48550/arxiv.1706.03762``
             or just ``10.48550/arXiv.1706.03762``.

    Returns:
        Bare arXiv ID (e.g. ``1706.03762``), or ``None`` if the DOI is not an
        arXiv DOI.
    """
    if not doi:
        return None
    lower = doi.lower()
    prefix = "10.48550/arxiv."
    idx = lower.find(prefix)
    if idx == -1:
        return None
    return doi[idx + len(prefix) :]


def _normalise_arxiv_id(raw: str) -> str:
    """Strip URL prefixes from an OpenAlex arXiv ID field.

    OpenAlex sometimes stores ``ids.arxiv`` as a full URL
    (e.g. ``https://arxiv.org/abs/2106.01234``).  This function extracts
    just the bare ID (e.g. ``2106.01234``).

    Args:
        raw: Raw value from ``ids.arxiv`` in an OpenAlex record.

    Returns:
        Bare arXiv ID string.
    """
    raw = raw.strip()
    for prefix in (
        "https://arxiv.org/abs/",
        "http://arxiv.org/abs/",
        "arxiv:",
    ):
        if raw.lower().startswith(prefix):
            return raw[len(prefix) :]
    return raw


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_openalex_citations(
    known_arxiv_ids: set[str],
    *,
    cache_dir: Path,
    max_works: int | None = None,
) -> CitationEdges:
    """Load citation edges from OpenAlex bulk data via S3.

    OpenAlex distributes its works as gzipped JSONL shards at
    ``s3://openalex/data/works/`` (public, no credentials required).  Each
    work record includes a ``referenced_works`` list of OpenAlex URLs and an
    ``ids.arxiv`` field when the paper is an arXiv preprint.

    Processing runs in **two logical passes** over each shard (sequentially,
    one shard at a time, so only one shard is in memory at once):

    1. Build a mapping from OpenAlex URL → arXiv ID for every work that has an
       arXiv identifier.
    2. Resolve each raw edge ``(source_arxiv_id, target_openalex_url)`` through
       that map, keeping only edges where both endpoints are in
       ``known_arxiv_ids``.

    Resume support: a ``progress.json`` file in ``cache_dir`` tracks which
    shards have been fully processed.  On restart, already-completed shards
    are skipped (both the download and the processing steps).

    Args:
        known_arxiv_ids: Set of arXiv IDs in the working paper subset.  Only
            edges whose both endpoints appear here are retained.
        cache_dir: Directory where downloaded OpenAlex shards are cached.
            Created if it does not exist.
        max_works: If set, stop after processing this many work records total
            (across all shards).  Useful for development/testing.  ``None``
            means no cap.

    Returns:
        A :class:`CitationEdges` with string-typed ``source_ids`` and
        ``target_ids``, indices set to ``None``.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: List all available shards ---
    print("[citations] Listing OpenAlex shards …", file=sys.stderr)
    all_keys = _list_openalex_shards()
    print(f"[citations] Found {len(all_keys)} shards.", file=sys.stderr)

    # --- Step 2: Load resume state ---
    completed = _load_progress(cache_dir)
    pending_keys = [k for k in all_keys if k not in completed]
    print(
        f"[citations] {len(completed)} shards already processed; "
        f"{len(pending_keys)} remaining.",
        file=sys.stderr,
    )

    # --- Step 3: Process shards (single-pass per shard, two logical passes total) ---
    # We build the URL→arXiv map and raw edges together in one physical pass per shard,
    # but we delay resolution until all shards are done so cross-shard references resolve.
    openalex_url_to_arxiv: dict[str, str] = {}
    raw_edges: list[tuple[str, str]] = []
    total_works = 0

    for i, key in enumerate(pending_keys, start=1):
        local_path = _shard_local_path(key, cache_dir)

        # --- Download if not already on disk ---
        if not local_path.exists():
            print(
                f"[citations] Downloading shard {i}/{len(pending_keys)}: {key} …",
                file=sys.stderr,
            )
            _download_shard(key, local_path)
        else:
            print(
                f"[citations] Shard already on disk, processing: {key}",
                file=sys.stderr,
            )

        # --- Process the shard ---
        before = len(raw_edges)
        _process_shard_pass1(
            local_path,
            known_arxiv_ids,
            openalex_url_to_arxiv,
            raw_edges,
        )
        new_edges = len(raw_edges) - before
        print(
            f"[citations] Shard {i}/{len(pending_keys)} done: "
            f"+{new_edges} raw edges, {len(openalex_url_to_arxiv)} URL mappings so far.",
            file=sys.stderr,
        )

        completed.add(key)
        _save_progress(cache_dir, completed)

        # --- max_works cap (approximate: counts raw edges as proxy) ---
        if max_works is not None:
            total_works += new_edges
            if total_works >= max_works:
                print(
                    f"[citations] Reached max_works cap ({max_works}); stopping early.",
                    file=sys.stderr,
                )
                break

    # --- Step 4: Resolve raw edges ---
    print(
        f"[citations] Resolving {len(raw_edges)} raw edges …",
        file=sys.stderr,
    )
    source_ids: list[str] = []
    target_ids: list[str] = []

    for src_arxiv, tgt_openalex_url in raw_edges:
        tgt_arxiv = openalex_url_to_arxiv.get(tgt_openalex_url)
        if tgt_arxiv is None:
            continue  # target not in our URL→arXiv map
        if tgt_arxiv not in known_arxiv_ids:
            continue  # target not in the working set
        source_ids.append(src_arxiv)
        target_ids.append(tgt_arxiv)

    print(
        f"[citations] {len(source_ids)} edges retained after filtering.",
        file=sys.stderr,
    )

    return CitationEdges(
        source_ids=np.array(source_ids, dtype=object),
        target_ids=np.array(target_ids, dtype=object),
        source_indices=None,
        target_indices=None,
    )


# ---------------------------------------------------------------------------
# OpenAlex REST API helpers
# ---------------------------------------------------------------------------

_OPENALEX_API_BASE = "https://api.openalex.org/works"


def _api_get(
    url: str,
    *,
    session: "_requests.Session",
    requests_per_second: float,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> "dict | None":
    """Perform a rate-limited GET request with exponential backoff.

    Sleeps ``1.0 / requests_per_second`` before every request.  On 429 or
    5xx responses, backs off exponentially with jitter, honouring any
    ``Retry-After`` header.  After ``max_retries`` consecutive failures logs
    to stderr and returns ``None`` so the caller can skip the batch.

    Args:
        url: Full request URL including query string.
        session: A ``requests.Session`` for connection reuse.
        requests_per_second: Maximum sustained request rate.
        max_retries: Number of retry attempts before giving up on a batch.
        base_delay: Base back-off delay in seconds (default: 1.0).
        max_delay: Maximum back-off delay in seconds (default: 60.0).

    Returns:
        Parsed JSON dict on success, or ``None`` if all retries fail.
    """
    time.sleep(1.0 / requests_per_second)

    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=30)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[citations_api] WARNING: request error (attempt {attempt + 1}/{max_retries}): {exc}",
                file=sys.stderr,
            )
            delay = min(2**attempt * base_delay, max_delay)
            delay += random.uniform(0, 0.5) * delay
            time.sleep(delay)
            continue

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code in (429,) or resp.status_code >= 500:
            # Respect Retry-After header if present
            retry_after = resp.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = min(2**attempt * base_delay, max_delay)
            else:
                delay = min(2**attempt * base_delay, max_delay)
                delay += random.uniform(0, 0.5) * delay

            print(
                f"[citations_api] WARNING: HTTP {resp.status_code} (attempt {attempt + 1}/{max_retries}), "
                f"backing off {delay:.1f}s …",
                file=sys.stderr,
            )
            time.sleep(delay)
            continue

        # Unexpected non-retryable status — log and return None
        print(
            f"[citations_api] WARNING: unexpected HTTP {resp.status_code} for {url}; skipping.",
            file=sys.stderr,
        )
        return None

    print(
        f"[citations_api] WARNING: exceeded {max_retries} retries for {url}; skipping batch.",
        file=sys.stderr,
    )
    return None


def _load_api_cache(cache_path: Path) -> dict[str, dict]:
    """Load the API response cache from a JSON file.

    Args:
        cache_path: Path to the cache JSON file.

    Returns:
        Dict mapping arXiv ID to ``{"openalex_id": str, "referenced_openalex_ids": [str]}``,
        or an empty dict if the file does not exist or is unreadable.
    """
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        print(
            f"[citations_api] WARNING: could not read cache {cache_path} ({exc}); starting fresh.",
            file=sys.stderr,
        )
        return {}


def _save_api_cache(cache_path: Path, cache: dict[str, dict]) -> None:
    """Persist the API cache to a JSON file.

    Args:
        cache_path: Destination path for the cache JSON file.
        cache: Cache dict to serialise.
    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2)


def load_openalex_citations_api(
    arxiv_ids: list[str],
    *,
    requests_per_second: float = 9.0,
    cache_path: Path | None = None,
) -> CitationEdges:
    """Load citation edges via the OpenAlex REST API.

    Suitable for corpora of ≤50 K papers where the S3 bulk download is
    impractical.  No API key is required.  Rate-limited to at most
    ``requests_per_second`` (default 9.0, i.e. safely under the 10 RPS cap).

    Algorithm (three passes):

    **Pass 1 — fetch source papers:**
    Batches ``arxiv_ids`` into groups of 50 and calls::

        GET https://api.openalex.org/works
            ?filter=ids.arxiv:{id1}|{id2}|...
            &select=id,ids,referenced_works
            &per-page=50

    Extracts ``ids.arxiv`` (source arXiv ID) and ``referenced_works`` (list of
    OpenAlex work URLs).  Builds a ``source_arxiv_id → [openalex_url]`` map and
    collects all unique referenced OpenAlex URLs.

    **Pass 2 — resolve referenced works:**
    Batches unique OpenAlex URLs into groups of 50 and calls::

        GET https://api.openalex.org/works
            ?filter=openalex_id:{W123}|{W456}|...
            &select=id,ids
            &per-page=50

    Builds an ``openalex_url → target_arxiv_id`` map.

    **Pass 3 — build edges:**
    Filters to ``(source, target)`` pairs where both arXiv IDs are in the
    input ``arxiv_ids`` set.

    Caching:
        If ``cache_path`` is provided, Pass 1 results are persisted as JSON
        after each batch.  On resume, already-cached arXiv IDs are skipped so
        the run can be interrupted and restarted cheaply.

    Args:
        arxiv_ids: List of arXiv IDs defining the working corpus.
        requests_per_second: Maximum sustained request rate (must be ≤ 9.0
            to stay safely under OpenAlex's 10 RPS cap).
        cache_path: Optional path to a ``.json`` cache file for Pass 1
            results.  Enables resume across interrupted runs.

    Returns:
        A :class:`CitationEdges` with string-typed ``source_ids`` and
        ``target_ids``, indices set to ``None``.

    Raises:
        ImportError: If the ``requests`` package is not installed.
    """
    if _requests is None:
        raise ImportError(
            "The 'requests' package is required for load_openalex_citations_api(). "
            "Install it with: pip install requests"
        )

    # Clamp rate to safe maximum
    rps = min(requests_per_second, 9.0)

    corpus_set: set[str] = set(arxiv_ids)
    total = len(arxiv_ids)
    batch_size = 50
    batches = [arxiv_ids[i : i + batch_size] for i in range(0, total, batch_size)]
    n_batches = len(batches)

    print(
        f"[citations_api] Fetching {total} papers in {n_batches} batches…",
        file=sys.stderr,
    )

    # --- Load existing cache ---
    cache: dict[str, dict] = {}
    if cache_path is not None:
        cache_path = Path(cache_path)
        cache = _load_api_cache(cache_path)

    # already-cached arXiv IDs (keyed exactly as they appear in cache)
    cached_ids: set[str] = set(cache.keys())

    # source_arxiv_id → list of referenced openalex URLs
    source_to_refs: dict[str, list[str]] = {}
    # Populate from cache
    for aid, entry in cache.items():
        source_to_refs[aid] = entry.get("referenced_openalex_ids", [])

    session = _requests.Session()

    # -----------------------------------------------------------------------
    # Pass 1: fetch source papers
    # -----------------------------------------------------------------------
    for batch_num, batch in enumerate(batches, start=1):
        # Skip IDs already in cache
        uncached = [aid for aid in batch if aid not in cached_ids]
        if not uncached:
            continue

        # OpenAlex stores arXiv papers by DOI (10.48550/arXiv.XXXX.XXXXX),
        # not via an ids.arxiv field. Use doi filter with the arXiv DOI prefix.
        doi_filter = "|".join(f"10.48550/arXiv.{aid}" for aid in uncached)
        url = (
            f"{_OPENALEX_API_BASE}"
            f"?filter=doi:{doi_filter}"
            f"&select=id,ids,referenced_works"
            f"&per-page={len(uncached)}"
        )

        data = _api_get(url, session=session, requests_per_second=rps)
        if data is None:
            # Batch failed — skip silently (already logged in _api_get)
            continue

        results = data.get("results") or []
        for work in results:
            openalex_url: str = work.get("id") or ""
            ids_field: dict = work.get("ids") or {}
            # Extract arXiv ID from DOI: "https://doi.org/10.48550/arxiv.1706.03762"
            doi_raw: str = ids_field.get("doi") or ""
            aid = _arxiv_id_from_doi(doi_raw)
            if not aid:
                continue
            refs: list[str] = work.get("referenced_works") or []
            source_to_refs[aid] = refs
            cache[aid] = {
                "openalex_id": openalex_url,
                "referenced_openalex_ids": refs,
            }
            cached_ids.add(aid)

        # Persist cache after each batch
        if cache_path is not None:
            _save_api_cache(cache_path, cache)

        pct = int(batch_num / n_batches * 100)
        print(
            f"[citations_api] Pass 1: batch {batch_num}/{n_batches} done ({pct}%)",
            file=sys.stderr,
        )

    # -----------------------------------------------------------------------
    # Pass 2: resolve referenced works → arXiv IDs
    # -----------------------------------------------------------------------
    # Collect all unique referenced OpenAlex URLs from corpus papers only
    all_ref_urls: set[str] = set()
    for aid in corpus_set:
        for ref_url in source_to_refs.get(aid, []):
            all_ref_urls.add(ref_url)

    ref_url_list = list(all_ref_urls)
    print(
        f"[citations_api] Pass 2: resolving {len(ref_url_list)} referenced works…",
        file=sys.stderr,
    )

    # openalex_url → target arXiv ID
    openalex_to_arxiv: dict[str, str] = {}

    ref_batches = [
        ref_url_list[i : i + batch_size]
        for i in range(0, len(ref_url_list), batch_size)
    ]
    for batch_num, ref_batch in enumerate(ref_batches, start=1):
        # Extract just the work ID part (e.g. "W123456") from full URLs
        id_parts: list[str] = []
        url_by_id: dict[str, str] = {}  # id_part → original URL
        for ref_url in ref_batch:
            # Full URL: "https://openalex.org/W123456" → id_part = "W123456"
            id_part = ref_url.rstrip("/").rsplit("/", 1)[-1]
            id_parts.append(id_part)
            url_by_id[id_part] = ref_url

        filter_str = "|".join(id_parts)
        url = (
            f"{_OPENALEX_API_BASE}"
            f"?filter=openalex_id:{filter_str}"
            f"&select=id,ids"
            f"&per-page={len(id_parts)}"
        )

        data = _api_get(url, session=session, requests_per_second=rps)
        if data is None:
            continue

        results = data.get("results") or []
        for work in results:
            openalex_url: str = work.get("id") or ""
            ids_field: dict = work.get("ids") or {}
            doi_raw: str = ids_field.get("doi") or ""
            target_aid = _arxiv_id_from_doi(doi_raw)
            if not target_aid or not openalex_url:
                continue
            openalex_to_arxiv[openalex_url] = target_aid

    # -----------------------------------------------------------------------
    # Pass 3: build filtered edges
    # -----------------------------------------------------------------------
    source_ids: list[str] = []
    target_ids: list[str] = []

    for src_aid in corpus_set:
        for ref_url in source_to_refs.get(src_aid, []):
            tgt_aid = openalex_to_arxiv.get(ref_url)
            if tgt_aid is None:
                continue
            if tgt_aid not in corpus_set:
                continue
            source_ids.append(src_aid)
            target_ids.append(tgt_aid)

    print(
        f"[citations_api] Found {len(source_ids)} citation edges within corpus.",
        file=sys.stderr,
    )

    return CitationEdges(
        source_ids=np.array(source_ids, dtype=object),
        target_ids=np.array(target_ids, dtype=object),
        source_indices=None,
        target_indices=None,
    )


def load_s2orc_citations(
    s2orc_path: Path,
    known_arxiv_ids: set[str],
) -> CitationEdges:
    """Load citation edges from S2ORC bulk data.

    .. deprecated::
        The S2ORC bulk download links are defunct.  Use
        :func:`load_openalex_citations` instead.

    Args:
        s2orc_path: Path to the S2ORC bulk data root directory or a single
            shard file.
        known_arxiv_ids: Set of arXiv IDs in the working paper subset.

    Returns:
        Never returns — always raises.

    Raises:
        NotImplementedError: Always.  S2ORC bulk links are defunct; use
            :func:`load_openalex_citations` instead.
    """
    raise NotImplementedError(
        "S2ORC bulk download links are defunct and this function is not "
        "implemented.  Use load_openalex_citations() instead, which "
        "downloads from the publicly accessible OpenAlex S3 bucket "
        "(s3://openalex/data/works/, no credentials required)."
    )


def build_id_to_index(arxiv_ids: list[str]) -> dict[str, int]:
    """Build a deterministic arXiv ID → integer index mapping.

    Indices are assigned by sorted order of arXiv ID for reproducibility
    across runs with the same corpus.

    Args:
        arxiv_ids: List of arXiv ID strings (may contain duplicates; only
            unique IDs are indexed).

    Returns:
        Dict mapping each unique arXiv ID to a zero-based integer index,
        ordered by lexicographic sort of the ID.

    Example:
        >>> build_id_to_index(["2106.01234", "1706.03762", "2101.00001"])
        {'1706.03762': 0, '2101.00001': 1, '2106.01234': 2}
    """
    unique_sorted = sorted(set(arxiv_ids))
    return {arxiv_id: i for i, arxiv_id in enumerate(unique_sorted)}


def assign_indices(
    edges: CitationEdges,
    id_to_index: dict[str, int],
) -> CitationEdges:
    """Map arXiv string IDs to integer node indices.

    Creates a new :class:`CitationEdges` with ``source_indices`` and
    ``target_indices`` populated by looking up each string ID in
    ``id_to_index``.  Edges where either endpoint is missing from the mapping
    are silently dropped.

    Args:
        edges: A :class:`CitationEdges` with ``source_ids`` and ``target_ids``
            populated (as returned by :func:`load_openalex_citations`).
        id_to_index: Mapping from arXiv ID string to integer node index, as
            produced by :func:`build_id_to_index` or by enumerating the
            ordered paper list.

    Returns:
        A new :class:`CitationEdges` with ``source_indices`` and
        ``target_indices`` set to integer numpy arrays and the ``*_ids``
        fields filtered to the surviving edges.
    """
    keep_src: list[str] = []
    keep_tgt: list[str] = []
    keep_src_idx: list[int] = []
    keep_tgt_idx: list[int] = []

    for src_id, tgt_id in zip(edges.source_ids, edges.target_ids):
        src_str = str(src_id)
        tgt_str = str(tgt_id)
        src_idx = id_to_index.get(src_str)
        tgt_idx = id_to_index.get(tgt_str)
        if src_idx is None or tgt_idx is None:
            continue
        keep_src.append(src_str)
        keep_tgt.append(tgt_str)
        keep_src_idx.append(src_idx)
        keep_tgt_idx.append(tgt_idx)

    return CitationEdges(
        source_ids=np.array(keep_src, dtype=object),
        target_ids=np.array(keep_tgt, dtype=object),
        source_indices=np.array(keep_src_idx, dtype=np.int64),
        target_indices=np.array(keep_tgt_idx, dtype=np.int64),
    )
