"""Citation edge loading and arXiv-ID-to-index mapping.

Supports two citation data sources:

- **OpenAlex**: CC0-licensed bulk data, freely accessible via S3 with no API
  key required.  Papers are identified via the ``ids.arxiv`` field; outgoing
  citations are stored in ``referenced_works`` as OpenAlex URLs.
- **S2ORC** (Semantic Scholar Open Research Corpus): bulk download links are
  defunct.  :func:`load_s2orc_citations` raises :exc:`NotImplementedError`
  and directs callers to :func:`load_openalex_citations`.

In both cases only edges where *both* endpoints are in the working paper set
(``known_arxiv_ids``) are retained.  String IDs are kept in
:class:`CitationEdges` until :func:`assign_indices` maps them to integer node
indices for use in PyG.
"""

from __future__ import annotations

import gzip
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

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
