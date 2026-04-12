"""SQLite schema for the four-layer knowledge infrastructure.

SQLite is used instead of DuckDB because DuckDB allows only one writer connection
at a time, which blocks parallel extraction pipelines. SQLite with WAL mode supports
concurrent readers and one writer, and is Python stdlib (no install required).

Tables created:

- ``chunks``          — L1 raw text chunks from papers
- ``paper_summaries`` — L2 paper-level structured summaries
- ``claims``          — L3 discrete claim nodes
- ``claim_sources``   — L3 mapping from claims to supporting papers
- ``claim_edges``     — L3 typed edges between claims
- ``_meta``           — internal DB versioning key/value store

All tables use ``CREATE TABLE IF NOT EXISTS`` so :func:`init_database` is safe
to call on an existing database without data loss.

JSON columns are stored as TEXT — use ``json.dumps()`` on write and
``json.loads()`` on read. SQLite's JSON1 extension is available for queries.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KNOWLEDGE_DB_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL_CHUNKS = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id       TEXT PRIMARY KEY,
    arxiv_id       TEXT NOT NULL,
    chunk_index    INTEGER NOT NULL,
    text           TEXT NOT NULL,
    char_start     INTEGER,
    char_end       INTEGER,
    embedding_row  INTEGER,
    created_at     TEXT DEFAULT (datetime('now'))
);
"""

_DDL_PAPER_SUMMARIES = """
CREATE TABLE IF NOT EXISTS paper_summaries (
    arxiv_id          TEXT PRIMARY KEY,
    title             TEXT,
    contribution      TEXT,
    method            TEXT,
    datasets          TEXT,          -- JSON array stored as text
    key_findings      TEXT,          -- JSON array stored as text
    limitations       TEXT,
    domain_tags       TEXT,          -- JSON array stored as text
    related_methods   TEXT,          -- JSON array stored as text
    extraction_model  TEXT,
    extracted_at      TEXT DEFAULT (datetime('now'))
);
"""

_DDL_CLAIMS = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id         TEXT PRIMARY KEY,
    claim_type       TEXT CHECK (claim_type IN (
                         'empirical', 'theoretical', 'architectural',
                         'comparative', 'observation'
                     )),
    assertion        TEXT NOT NULL,
    domain           TEXT,
    method           TEXT,
    dataset          TEXT,
    metric           TEXT,
    value            TEXT,
    conditions       TEXT,
    epistemic_status TEXT DEFAULT 'preliminary' CHECK (epistemic_status IN (
                         'established', 'preliminary', 'contested', 'ungrounded'
                     )),
    confidence       REAL DEFAULT 0.5,
    embedding_row    INTEGER,
    created_at       TEXT DEFAULT (datetime('now')),
    last_updated     TEXT DEFAULT (datetime('now'))
);
"""

_DDL_CLAIM_SOURCES = """
CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id    TEXT NOT NULL,
    arxiv_id    TEXT NOT NULL,
    excerpt     TEXT,
    PRIMARY KEY (claim_id, arxiv_id)
);
"""

_DDL_CLAIM_EDGES = """
CREATE TABLE IF NOT EXISTS claim_edges (
    edge_id      TEXT PRIMARY KEY,
    source_id    TEXT NOT NULL,
    target_id    TEXT NOT NULL,
    edge_type    TEXT CHECK (edge_type IN (
                     'supports', 'contradicts', 'extends',
                     'replicates_in_domain', 'requires', 'refines'
                 )),
    confidence   REAL DEFAULT 0.5,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""

_DDL_PAPER_EDGES = """
CREATE TABLE IF NOT EXISTS paper_edges (
    edge_id      TEXT PRIMARY KEY,
    source_id    TEXT NOT NULL,    -- arxiv_id of the source paper
    target_id    TEXT NOT NULL,    -- arxiv_id of the target paper
    edge_type    TEXT NOT NULL,    -- shares_method | co_domain
    shared_value TEXT,             -- the normalised method name or domain tag
    confidence   REAL DEFAULT 0.8,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""

_DDL_META = """
CREATE TABLE IF NOT EXISTS _meta (
    key    TEXT PRIMARY KEY,
    value  TEXT
);
"""

_DDL_SEARCH_INDEX = """
CREATE VIRTUAL TABLE IF NOT EXISTS search_index
USING fts5(arxiv_id UNINDEXED, text, tokenize='porter ascii');
"""

_ALL_DDL = [
    _DDL_CHUNKS,
    _DDL_PAPER_SUMMARIES,
    _DDL_CLAIMS,
    _DDL_CLAIM_SOURCES,
    _DDL_CLAIM_EDGES,
    _DDL_PAPER_EDGES,
    _DDL_META,
    _DDL_SEARCH_INDEX,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(value: Any) -> str | None:
    """Serialize a list/dict to JSON string for storage. None → NULL."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str | None) -> Any:
    """Deserialize a JSON string from storage. NULL → None."""
    if value is None:
        return None
    return json.loads(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_database(db_path: Path) -> sqlite3.Connection:
    """Create all tables and return an open connection.

    Idempotent — safe to call on an existing database (uses
    ``CREATE TABLE IF NOT EXISTS``). Creates parent directories if needed.
    Enables WAL mode for concurrent read access.

    Args:
        db_path: Path to the SQLite file. Created if it does not exist.

    Returns:
        An open :class:`sqlite3.Connection` with WAL mode enabled.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Enable WAL for concurrent reads + one writer
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    for ddl in _ALL_DDL:
        conn.execute(ddl)

    conn.execute(
        "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
        ("version", KNOWLEDGE_DB_VERSION),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
        ("created_at", _now_utc()),
    )
    conn.commit()
    return conn


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Return an open connection to an existing SQLite database.

    Args:
        db_path: Path to an existing SQLite file.

    Returns:
        An open :class:`sqlite3.Connection` with WAL mode and row_factory set.
    """
    conn = sqlite3.connect(str(Path(db_path)), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
