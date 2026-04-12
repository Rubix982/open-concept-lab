"""L1 paper ingest pipeline — abstract-only chunking into SQLite.

Each paper produces one chunk (its abstract).  The SPECTER2 embedding for
that chunk is reused from the pre-computed ``embeddings_10k.npy`` file,
so no re-embedding is required for the initial 10 K corpus.

The ``embedding_row`` field in each chunk record is the row index in the
embeddings array, which corresponds to the row index in the source DataFrame.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import get_connection, init_database


def ingest_papers(
    papers: pd.DataFrame,
    embeddings_path: Path,
    db_path: Path,
    *,
    batch_size: int = 100,
    skip_existing: bool = True,
) -> dict[str, int]:
    """Ingest arXiv papers as L1 chunks into the knowledge SQLite database.

    Each paper produces exactly one chunk using its abstract text.  The
    ``embedding_row`` field is set to the paper's integer position in
    ``papers`` (i.e. its DataFrame row index), which aligns with the
    corresponding row in ``embeddings_path``.

    Args:
        papers: DataFrame with at minimum columns ``arxiv_id`` and
            ``abstract``.  Title is stored if present.  Row order must
            match the embedding array.
        embeddings_path: Path to the pre-computed SPECTER2 ``.npy`` file.
            Used only to validate that ``embedding_row`` indices are in range.
        db_path: Path to the SQLite knowledge database.  Initialized
            (tables created) if it does not already exist.
        batch_size: Number of rows inserted per ``executemany`` call and
            per ``commit``.  Lower values reduce memory pressure.
        skip_existing: When ``True``, papers already present in the
            ``chunks`` table (matched by ``chunk_id``) are skipped without
            error.

    Returns:
        A dict with keys ``"ingested"``, ``"skipped"``, and ``"errors"``
        reporting the count of each outcome.
    """
    db_path = Path(db_path)
    embeddings_path = Path(embeddings_path)

    # Validate embedding array dimensions
    embeddings = np.load(str(embeddings_path), mmap_mode="r")
    n_embeddings = len(embeddings)

    conn = init_database(db_path)

    counters: dict[str, int] = {"ingested": 0, "skipped": 0, "errors": 0}

    # Pre-fetch existing chunk_ids for skip logic (one query, not N)
    existing: set[str] = set()
    if skip_existing:
        rows = conn.execute("SELECT chunk_id FROM chunks").fetchall()
        existing = {row[0] for row in rows}

    batch: list[tuple] = []
    total = len(papers)
    n_batches = max(1, (total + batch_size - 1) // batch_size)

    def _flush(batch: list[tuple]) -> None:
        conn.executemany(
            """
            INSERT OR IGNORE INTO chunks
                (chunk_id, arxiv_id, chunk_index, text,
                 char_start, char_end, embedding_row)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()

    for idx, row in enumerate(papers.itertuples(index=False)):
        arxiv_id: str = str(row.arxiv_id)
        chunk_id = f"{arxiv_id}_abstract"

        if skip_existing and chunk_id in existing:
            counters["skipped"] += 1
            continue

        try:
            abstract: str = str(row.abstract) if pd.notna(row.abstract) else ""
            embedding_row = idx  # aligns with embeddings array row

            if embedding_row >= n_embeddings:
                print(
                    f"[ingest] WARNING: embedding_row {embedding_row} out of range "
                    f"(n_embeddings={n_embeddings}), skipping {arxiv_id}",
                    file=sys.stderr,
                )
                counters["errors"] += 1
                continue

            batch.append(
                (
                    chunk_id,
                    arxiv_id,
                    0,  # chunk_index
                    abstract,
                    0,  # char_start
                    len(abstract),
                    embedding_row,
                )
            )
            counters["ingested"] += 1

            if len(batch) >= batch_size:
                batch_num = (idx // batch_size) + 1
                print(
                    f"[ingest] Ingesting batch {batch_num}/{n_batches} "
                    f"({counters['ingested']} ingested so far)...",
                    file=sys.stderr,
                )
                _flush(batch)
                batch = []

        except Exception as exc:
            print(
                f"[ingest] ERROR on {arxiv_id}: {exc}",
                file=sys.stderr,
            )
            counters["errors"] += 1

    # Flush remaining rows
    if batch:
        _flush(batch)

    conn.close()
    print(
        f"[ingest] Done. ingested={counters['ingested']}, "
        f"skipped={counters['skipped']}, errors={counters['errors']}",
        file=sys.stderr,
    )
    return counters
