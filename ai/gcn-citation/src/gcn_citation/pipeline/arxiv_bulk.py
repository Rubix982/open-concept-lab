"""Streaming parser for the arXiv bulk metadata OAI snapshot.

The snapshot file (``arxiv-metadata-oai-snapshot.json``) is a ~3.5 GB
newline-delimited JSON file distributed via the arXiv S3 bucket.  Each line
is a JSON object describing one paper.  This module streams it line-by-line
so it never needs to be loaded fully into memory, and provides a
checkpoint-based loader that can resume from a previously saved ``.parquet``
file.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]


@dataclass
class ArxivPaper:
    """Parsed representation of a single arXiv paper from the bulk snapshot.

    Attributes:
        arxiv_id: Canonical arXiv identifier, e.g. ``"2310.12345"``.
        title: Paper title with internal whitespace normalised.
        abstract: Paper abstract with internal whitespace normalised.
        categories: All arXiv category tags listed for the paper,
            e.g. ``["cs.LG", "stat.ML"]``.
        primary_category: First entry in ``categories`` (as stored in the
            snapshot), which is the submitter's primary designation.
        is_interdisciplinary: ``True`` when ``len(categories) >= 2``.
        year: Four-digit submission year parsed from the ``versions`` field.
        month: One- or two-digit submission month (1–12).
    """

    arxiv_id: str
    title: str
    abstract: str
    categories: list[str]
    primary_category: str
    is_interdisciplinary: bool
    year: int
    month: int


def _extract_year_month(record: dict) -> tuple[int, int]:
    """Extract year and month from a raw snapshot record.

    Tries ``update_date`` first (format ``YYYY-MM-DD``), then falls back to
    parsing the arXiv ID itself for new-format IDs (``YYMM.NNNNN``).

    Args:
        record: Raw JSON object from the snapshot.

    Returns:
        ``(year, month)`` as integers.  Returns ``(0, 0)`` when neither
        source is parseable.
    """
    # Prefer update_date field (most reliable, present in virtually all records)
    update_date: str = record.get("update_date", "")
    if update_date and len(update_date) >= 7:
        try:
            parts = update_date.split("-")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass

    # Fall back to new-format ID: YYMM.NNNNN
    arxiv_id: str = record.get("id", "")
    if arxiv_id and "/" not in arxiv_id:
        # new-format IDs start with YYMM
        id_part = arxiv_id.split("v")[0]  # strip version suffix if present
        if len(id_part) >= 4:
            try:
                yy = int(id_part[:2])
                mm = int(id_part[2:4])
                # arXiv started new-format IDs in 2007; 00–06 → 2000–2006
                # is ambiguous, but new IDs didn't exist then, so 07–99 → 2007–2099
                year = 2000 + yy if yy >= 7 else 2100 + yy  # conservative
                return year, mm
            except ValueError:
                pass

    return 0, 0


def stream_arxiv_metadata(
    snapshot_path: Path,
    *,
    categories: list[str] | None = None,
    max_papers: int | None = None,
    start_year: int | None = None,
) -> Iterator[ArxivPaper]:
    """Stream papers from the arXiv bulk metadata JSON snapshot.

    Reads ``snapshot_path`` line-by-line to avoid loading the ~3.5 GB file
    into memory.  Each line is a JSON object; malformed lines are skipped with
    a warning printed to stderr.

    The ``categories`` field in the snapshot is a space-separated string
    (e.g. ``"cs.LG stat.ML"``).  A paper qualifies when at least one of those
    tokens appears in the ``categories`` filter list.

    Both old-format arXiv IDs (e.g. ``math/0406594``, containing a ``/``) and
    new-format IDs (e.g. ``1706.03762``) are supported.

    Args:
        snapshot_path: Path to ``arxiv-metadata-oai-snapshot.json``.
        categories: If given, only yield papers where at least one of the
            paper's categories appears in this list.  ``None`` means no filter.
        max_papers: Stop after yielding this many papers.  ``None`` means no
            limit.
        start_year: If given, skip papers submitted before this calendar year.

    Yields:
        :class:`ArxivPaper` objects, one per qualifying paper.

    Raises:
        FileNotFoundError: If ``snapshot_path`` does not exist.
    """
    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    category_set: set[str] | None = set(categories) if categories is not None else None
    yielded = 0

    with open(snapshot_path, "r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"[arxiv_bulk] WARNING: skipping malformed line {line_num}: {exc}",
                    file=sys.stderr,
                )
                continue

            # --- Parse categories (space-separated string in snapshot) ---
            raw_cats: str = record.get("categories", "") or ""
            cat_list: list[str] = raw_cats.split() if raw_cats else []

            # --- Category filter ---
            if category_set is not None:
                if not any(c in category_set for c in cat_list):
                    continue

            # --- Extract year/month ---
            year, month = _extract_year_month(record)

            # --- Year filter ---
            if start_year is not None and year > 0 and year < start_year:
                continue

            # --- Build paper object ---
            arxiv_id: str = record.get("id", "").strip()
            title: str = " ".join((record.get("title", "") or "").split())
            abstract: str = " ".join((record.get("abstract", "") or "").split())
            primary_category: str = cat_list[0] if cat_list else ""
            is_interdisciplinary: bool = len(cat_list) >= 2

            paper = ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                abstract=abstract,
                categories=cat_list,
                primary_category=primary_category,
                is_interdisciplinary=is_interdisciplinary,
                year=year,
                month=month,
            )

            yield paper
            yielded += 1

            if max_papers is not None and yielded >= max_papers:
                break


def load_papers_to_dataframe(
    snapshot_path: Path,
    *,
    categories: list[str] | None = None,
    max_papers: int | None = None,
) -> "pd.DataFrame":
    """Load filtered papers into a pandas DataFrame with resume support.

    Streams the snapshot through :func:`stream_arxiv_metadata`, collecting
    results into a DataFrame.  Checkpoints progress by writing a ``.parquet``
    file alongside ``snapshot_path`` every 10,000 papers.  The checkpoint path
    is ``snapshot_path.with_suffix('.checkpoint.parquet')``.

    If the checkpoint already exists on startup, it is loaded and the count of
    already-saved rows is used to skip that many qualifying papers before
    continuing to stream.

    The returned DataFrame has these columns:

    - ``arxiv_id`` (str)
    - ``title`` (str)
    - ``abstract`` (str)
    - ``categories`` (object — list of str)
    - ``primary_category`` (str)
    - ``is_interdisciplinary`` (bool)
    - ``year`` (int)
    - ``month`` (int)

    Args:
        snapshot_path: Path to ``arxiv-metadata-oai-snapshot.json``.
        categories: Category filter forwarded to :func:`stream_arxiv_metadata`.
        max_papers: Paper cap forwarded to :func:`stream_arxiv_metadata`.

    Returns:
        A :class:`pandas.DataFrame` with one row per paper.

    Raises:
        ImportError: If ``pandas`` is not installed.
    """
    if pd is None:
        raise ImportError("pandas is required for load_papers_to_dataframe()")

    snapshot_path = Path(snapshot_path)
    checkpoint_path = snapshot_path.with_suffix(".checkpoint.parquet")

    CHECKPOINT_INTERVAL = 10_000
    COLUMNS = [
        "arxiv_id",
        "title",
        "abstract",
        "categories",
        "primary_category",
        "is_interdisciplinary",
        "year",
        "month",
    ]

    # --- Resume: load existing checkpoint if present ---
    existing_df: pd.DataFrame | None = None
    already_saved = 0
    if checkpoint_path.exists():
        try:
            existing_df = pd.read_parquet(checkpoint_path)
            already_saved = len(existing_df)
            print(
                f"[arxiv_bulk] Resuming from checkpoint: {already_saved} papers already saved.",
                file=sys.stderr,
            )
        except Exception as exc:  # noqa: BLE001
            print(
                f"[arxiv_bulk] WARNING: could not read checkpoint ({exc}); starting fresh.",
                file=sys.stderr,
            )
            existing_df = None
            already_saved = 0

    # --- Determine how many more papers are needed ---
    remaining: int | None = None
    if max_papers is not None:
        remaining = max(0, max_papers - already_saved)
        if remaining == 0:
            # Checkpoint already covers the full request
            assert existing_df is not None
            return existing_df[COLUMNS].reset_index(drop=True)

    # --- Stream new papers (skip the ones already checkpointed) ---
    stream = stream_arxiv_metadata(
        snapshot_path,
        categories=categories,
        max_papers=None,  # We control the limit ourselves below
        start_year=None,
    )

    rows: list[dict] = []
    skipped = 0
    total_new = 0

    # rows already in checkpoint count toward the saved set; skip them in stream
    # (we cannot seek the file, so we count the qualifying papers we skip)
    for paper in stream:
        if skipped < already_saved:
            skipped += 1
            continue

        rows.append(
            {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "primary_category": paper.primary_category,
                "is_interdisciplinary": paper.is_interdisciplinary,
                "year": paper.year,
                "month": paper.month,
            }
        )
        total_new += 1

        # Checkpoint every CHECKPOINT_INTERVAL new papers
        if total_new % CHECKPOINT_INTERVAL == 0:
            partial_df = pd.DataFrame(rows, columns=COLUMNS)
            combined = (
                pd.concat([existing_df, partial_df], ignore_index=True)
                if existing_df is not None
                else partial_df
            )
            combined.to_parquet(checkpoint_path, index=False)
            print(
                f"[arxiv_bulk] Checkpoint: {len(combined)} papers saved to {checkpoint_path}",
                file=sys.stderr,
            )

        if remaining is not None and total_new >= remaining:
            break

    # --- Combine existing + new rows ---
    new_df = pd.DataFrame(rows, columns=COLUMNS)
    if existing_df is not None and len(existing_df) > 0:
        result_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        result_df = new_df.reset_index(drop=True)

    # Final checkpoint save
    if len(rows) > 0:
        result_df.to_parquet(checkpoint_path, index=False)
        print(
            f"[arxiv_bulk] Final checkpoint: {len(result_df)} papers saved to {checkpoint_path}",
            file=sys.stderr,
        )

    return result_df[COLUMNS].reset_index(drop=True)
