"""L2-derived relational edges — shares_method and co_domain.

Mines ``related_methods`` and ``domain_tags`` fields from the ``paper_summaries``
table (populated by the L2 extraction pipeline) to build two new typed edge sets:

- **shares_method**: Two papers that both list the same method in their
  ``related_methods`` field.  Method names are lowercased and punctuation-stripped
  before matching.

- **co_domain**: Two papers that share at least one specific domain tag in their
  ``domain_tags`` field.  Generic tags (e.g. ``"deep_learning"``) are excluded to
  avoid generating near-complete cliques over the corpus.

Edges are stored in the ``paper_edges`` table (created by :func:`init_database`
in :mod:`schema`).  This table uses paper-level ``arxiv_id`` values as endpoints,
not claim IDs, so it is useful before L3 is fully built.
"""

from __future__ import annotations

import re
import sys
from itertools import combinations
from pathlib import Path

from .schema import get_connection, init_database, json_loads

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_GENERIC_TAGS: frozenset[str] = frozenset(
    {
        "deep_learning",
        "machine_learning",
        "neural_network",
        "AI",
        "artificial_intelligence",
        "NLP",
        "CV",
        "computer_vision",
    }
)

_PUNCT_RE = re.compile(r"[^\w\s]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_method(name: str) -> str:
    """Return a canonical form of a method name for grouping.

    Lowercases and strips punctuation (keeping alphanumeric and whitespace),
    then collapses runs of whitespace.

    Args:
        name: Raw method name string from L2 extraction.

    Returns:
        Normalized string suitable for use as a grouping key.
    """
    lowered = name.lower()
    no_punct = _PUNCT_RE.sub(" ", lowered)
    return " ".join(no_punct.split())


def _ordered_pair(a: str, b: str) -> tuple[str, str]:
    """Return (a, b) sorted lexicographically so a <= b.

    Args:
        a: First arXiv ID.
        b: Second arXiv ID.

    Returns:
        Tuple with the lexicographically smaller ID first.
    """
    return (a, b) if a <= b else (b, a)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_method_edges(
    db_path: Path,
    *,
    min_papers_per_method: int = 2,
    max_pairs_per_method: int = 50,
) -> int:
    """Build shares_method edges between papers with common related_methods.

    Loads all ``paper_summaries`` rows with a non-NULL ``related_methods``
    field, normalises each method name (lowercase + strip punctuation), builds
    an inverted index from method → list[arxiv_id], then generates all
    pairwise paper combinations for each method that appears in at least
    ``min_papers_per_method`` papers.  Pairs are capped at
    ``max_pairs_per_method`` per method (taken after lexicographic sort) to
    avoid combinatorial blowup from high-frequency methods.

    Inserts into the ``paper_edges`` table (created if absent).  Duplicate
    edge IDs are silently ignored (``INSERT OR IGNORE``).

    Args:
        db_path: Path to the SQLite knowledge database.
        min_papers_per_method: Minimum number of papers that must share a
            method before any edges are generated for that method.
        max_pairs_per_method: Maximum number of pairs to insert per method.

    Returns:
        Number of edges inserted in this run (ignores pre-existing rows).
    """
    db_path = Path(db_path)
    conn = init_database(db_path)

    print("[derive_edges] Loading paper_summaries for method edges...", file=sys.stderr)

    rows = conn.execute(
        "SELECT arxiv_id, related_methods FROM paper_summaries "
        "WHERE related_methods IS NOT NULL AND related_methods != '[]'"
    ).fetchall()

    print(f"[derive_edges] {len(rows)} papers with related_methods", file=sys.stderr)

    # Build inverted index: normalised_method -> [arxiv_id, ...]
    index: dict[str, list[str]] = {}
    for row in rows:
        arxiv_id = row[0]
        methods: list[str] = json_loads(row[1]) or []
        for raw_method in methods:
            if not raw_method or not isinstance(raw_method, str):
                continue
            norm = _normalize_method(raw_method)
            if not norm:
                continue
            index.setdefault(norm, []).append(arxiv_id)

    print(f"[derive_edges] {len(index)} distinct normalised methods", file=sys.stderr)

    inserted = 0
    methods_with_edges = 0

    for method_norm, paper_ids in sorted(index.items()):
        # Deduplicate within this method's paper list
        unique_ids = sorted(set(paper_ids))
        if len(unique_ids) < min_papers_per_method:
            continue

        pairs = list(combinations(unique_ids, 2))
        if len(pairs) > max_pairs_per_method:
            pairs = pairs[:max_pairs_per_method]

        methods_with_edges += 1

        for arxiv_a, arxiv_b in pairs:
            id_a, id_b = _ordered_pair(arxiv_a, arxiv_b)
            edge_id = f"method_{method_norm.replace(' ', '_')}_{id_a}_{id_b}"
            conn.execute(
                """
                INSERT OR IGNORE INTO paper_edges
                    (edge_id, source_id, target_id, edge_type, shared_value, confidence)
                VALUES (?, ?, ?, 'shares_method', ?, 0.8)
                """,
                (edge_id, id_a, id_b, method_norm),
            )
            inserted += 1

    conn.commit()
    conn.close()

    print(
        f"[derive_edges] shares_method: {inserted} edges from "
        f"{methods_with_edges} methods",
        file=sys.stderr,
    )
    return inserted


def build_domain_edges(
    db_path: Path,
    *,
    exclude_generic: set[str] | None = None,
    max_pairs_per_domain: int = 50,
) -> int:
    """Build co_domain edges between papers sharing specific domain_tags.

    Loads all ``paper_summaries`` rows with a non-NULL ``domain_tags`` field,
    filters out tags in ``exclude_generic``, builds an inverted index from
    tag → list[arxiv_id], then generates all pairwise paper combinations for
    each retained tag.  Pairs are capped at ``max_pairs_per_domain`` per tag
    (taken after lexicographic sort).

    Inserts into the ``paper_edges`` table (created if absent).  Duplicate
    edge IDs are silently ignored (``INSERT OR IGNORE``).

    Args:
        db_path: Path to the SQLite knowledge database.
        exclude_generic: Set of tag strings to skip entirely.  Defaults to
            :data:`_DEFAULT_GENERIC_TAGS` (``deep_learning``, ``machine_learning``,
            etc.).  Comparison is case-sensitive — tags are matched as-is.
        max_pairs_per_domain: Maximum number of pairs to insert per domain tag.

    Returns:
        Number of edges inserted in this run (ignores pre-existing rows).
    """
    db_path = Path(db_path)

    if exclude_generic is None:
        exclude_generic = set(_DEFAULT_GENERIC_TAGS)

    conn = init_database(db_path)

    print("[derive_edges] Loading paper_summaries for domain edges...", file=sys.stderr)

    rows = conn.execute(
        "SELECT arxiv_id, domain_tags FROM paper_summaries "
        "WHERE domain_tags IS NOT NULL AND domain_tags != '[]'"
    ).fetchall()

    print(f"[derive_edges] {len(rows)} papers with domain_tags", file=sys.stderr)

    # Build inverted index: tag -> [arxiv_id, ...]
    index: dict[str, list[str]] = {}
    for row in rows:
        arxiv_id = row[0]
        tags: list[str] = json_loads(row[1]) or []
        for tag in tags:
            if not tag or not isinstance(tag, str):
                continue
            if tag in exclude_generic:
                continue
            index.setdefault(tag, []).append(arxiv_id)

    print(
        f"[derive_edges] {len(index)} distinct non-generic domain tags",
        file=sys.stderr,
    )

    inserted = 0
    tags_with_edges = 0

    for tag, paper_ids in sorted(index.items()):
        unique_ids = sorted(set(paper_ids))
        if len(unique_ids) < 2:
            continue

        pairs = list(combinations(unique_ids, 2))
        if len(pairs) > max_pairs_per_domain:
            pairs = pairs[:max_pairs_per_domain]

        tags_with_edges += 1

        for arxiv_a, arxiv_b in pairs:
            id_a, id_b = _ordered_pair(arxiv_a, arxiv_b)
            edge_id = f"domain_{tag.replace(' ', '_')}_{id_a}_{id_b}"
            conn.execute(
                """
                INSERT OR IGNORE INTO paper_edges
                    (edge_id, source_id, target_id, edge_type, shared_value, confidence)
                VALUES (?, ?, ?, 'co_domain', ?, 0.8)
                """,
                (edge_id, id_a, id_b, tag),
            )
            inserted += 1

    conn.commit()
    conn.close()

    print(
        f"[derive_edges] co_domain: {inserted} edges from {tags_with_edges} tags",
        file=sys.stderr,
    )
    return inserted


def build_all_edges(
    db_path: Path,
    *,
    min_papers_per_method: int = 2,
    max_pairs_per_method: int = 50,
    max_pairs_per_domain: int = 50,
) -> dict[str, int]:
    """Run both edge builders and return counts.

    Convenience wrapper that calls :func:`build_method_edges` and
    :func:`build_domain_edges` in sequence.

    Args:
        db_path: Path to the SQLite knowledge database.
        min_papers_per_method: Passed to :func:`build_method_edges`.
        max_pairs_per_method: Passed to :func:`build_method_edges`.
        max_pairs_per_domain: Passed to :func:`build_domain_edges`.

    Returns:
        Dict with keys ``"method_edges"`` and ``"domain_edges"`` giving the
        count of edges inserted by each builder.
    """
    method_edges = build_method_edges(
        db_path,
        min_papers_per_method=min_papers_per_method,
        max_pairs_per_method=max_pairs_per_method,
    )
    domain_edges = build_domain_edges(
        db_path,
        max_pairs_per_domain=max_pairs_per_domain,
    )
    return {"method_edges": method_edges, "domain_edges": domain_edges}
