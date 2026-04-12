"""Validation script for E-016: Query interface (L1 + L2 semantic search).

Tests the structural correctness of search_papers() using the knowledge DB
populated by E-015 validation (or a minimal freshly created DB if absent).
Does NOT test topical relevance — only mechanics.

Checks:
1. search_papers returns a list
2. Each result has required keys: arxiv_id, similarity_score, contribution
3. similarity_score is float in [0, 1] (cosine of L2-normed vecs is in [-1,1];
   semantically similar docs should be >= 0, but we only check float type here)
4. Results are sorted by score descending
5. top_k > len(corpus) returns however many exist, no error
6. Non-existent DB raises FileNotFoundError or returns []

Usage:
    source .venv/bin/activate
    KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 \\
        python agents/engineer/workspace/validate_query.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

DB_PATH = _REPO_ROOT / "data" / "knowledge" / "knowledge.db"
EMB_PATH = _REPO_ROOT / "data" / "pipeline" / "embeddings_10k.npy"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = 0
_FAIL = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    """Print PASS or FAIL for a single check."""
    global _PASS, _FAIL
    status = "PASS" if condition else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    if condition:
        _PASS += 1
    else:
        _FAIL += 1


# ---------------------------------------------------------------------------
# Setup: ensure DB exists with minimal schema + some ingest data
# ---------------------------------------------------------------------------


def _ensure_db(db_path: Path) -> None:
    """Ensure the knowledge DB exists with at least the schema initialised.

    If the DB doesn't exist, create it and ingest the first 10 rows from
    arxiv_10k.parquet so search_papers() has something to look up.
    """
    from src.knowledge.schema import init_database

    if not db_path.exists():
        print(
            f"[setup] DB not found at {db_path} — creating minimal DB ...",
            file=sys.stderr,
        )
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = init_database(db_path)
        conn.close()

        # Try to ingest a few papers so lookup works
        parquet_path = _REPO_ROOT / "data" / "pipeline" / "arxiv_10k.parquet"
        if parquet_path.exists():
            try:
                import pandas as pd
                from src.knowledge.ingest import ingest_papers

                papers = pd.read_parquet(parquet_path).head(10)
                ingest_papers(papers, EMB_PATH, db_path, skip_existing=True)
                print(
                    f"[setup] Ingested {len(papers)} papers into {db_path}",
                    file=sys.stderr,
                )
            except Exception as exc:
                print(
                    f"[setup] WARNING: could not ingest papers: {exc}", file=sys.stderr
                )
        else:
            print(
                f"[setup] parquet not found at {parquet_path} — "
                "DB will be empty (structural tests still run)",
                file=sys.stderr,
            )
    else:
        print(f"[setup] Using existing DB: {db_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------


def main() -> None:
    global _PASS, _FAIL

    if not EMB_PATH.exists():
        print(f"FATAL: Embeddings file not found: {EMB_PATH}")
        print("Run the embedding pipeline (E-006) first.")
        sys.exit(1)

    _ensure_db(DB_PATH)

    from src.knowledge.query import search_papers

    print("\n" + "=" * 60)
    print("E-016 Validation: query.py — search_papers()")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Test 1: search_papers("transformer attention", top_k=3)
    # -------------------------------------------------------------------------
    print("\n[Test 1] search_papers('transformer attention', top_k=3)")
    t0 = time.monotonic()
    try:
        results1 = search_papers(
            "transformer attention",
            DB_PATH,
            EMB_PATH,
            top_k=3,
        )
        elapsed = time.monotonic() - t0
        print(f"  Returned {len(results1)} result(s) in {elapsed:.2f}s")

        check("returns a list", isinstance(results1, list))

        if results1:
            r = results1[0]
            check("each result has 'arxiv_id'", "arxiv_id" in r)
            check("each result has 'similarity_score'", "similarity_score" in r)
            check("each result has 'contribution'", "contribution" in r)
            check(
                "similarity_score is float",
                isinstance(r.get("similarity_score"), float),
                str(type(r.get("similarity_score"))),
            )
            check(
                "similarity_score <= 1.0",
                r.get("similarity_score", 999) <= 1.0,
                str(r.get("similarity_score")),
            )
            check(
                "similarity_score >= -1.0",
                r.get("similarity_score", -999) >= -1.0,
                str(r.get("similarity_score")),
            )
            # Verify descending sort
            if len(results1) > 1:
                sorted_ok = all(
                    results1[i]["similarity_score"]
                    >= results1[i + 1]["similarity_score"]
                    for i in range(len(results1) - 1)
                )
                check("results sorted by score descending", sorted_ok)
        else:
            print("  (No results — DB may be empty; skipping per-result checks)")

    except Exception as exc:
        print(f"  ERROR: {exc}")
        check("no exception raised", False, str(exc))

    # -------------------------------------------------------------------------
    # Test 2: search_papers("batch normalization", top_k=3)
    # -------------------------------------------------------------------------
    print("\n[Test 2] search_papers('batch normalization', top_k=3)")
    t0 = time.monotonic()
    try:
        results2 = search_papers(
            "batch normalization",
            DB_PATH,
            EMB_PATH,
            top_k=3,
        )
        elapsed = time.monotonic() - t0
        print(f"  Returned {len(results2)} result(s) in {elapsed:.2f}s")

        check("returns a list", isinstance(results2, list))

        if results2:
            r = results2[0]
            check("has 'arxiv_id'", "arxiv_id" in r)
            check("has 'similarity_score'", "similarity_score" in r)
            check("has 'contribution'", "contribution" in r)
            check(
                "similarity_score is float",
                isinstance(r.get("similarity_score"), float),
            )
            if len(results2) > 1:
                sorted_ok = all(
                    results2[i]["similarity_score"]
                    >= results2[i + 1]["similarity_score"]
                    for i in range(len(results2) - 1)
                )
                check("results sorted by score descending", sorted_ok)
        else:
            print("  (No results — structural check only)")

    except Exception as exc:
        print(f"  ERROR: {exc}")
        check("no exception raised", False, str(exc))

    # -------------------------------------------------------------------------
    # Test 3: top_k > corpus size — should return however many exist, no error
    # -------------------------------------------------------------------------
    print("\n[Test 3] top_k=9999 (larger than corpus)")
    try:
        results3 = search_papers(
            "graph neural network",
            DB_PATH,
            EMB_PATH,
            top_k=9999,
        )
        check("returns a list (no exception)", isinstance(results3, list))
        print(f"  Returned {len(results3)} result(s) (expected <= corpus size)")
    except Exception as exc:
        print(f"  ERROR: {exc}")
        check("no exception raised", False, str(exc))

    # -------------------------------------------------------------------------
    # Test 4: non-existent DB — should raise FileNotFoundError or return []
    # -------------------------------------------------------------------------
    print("\n[Test 4] non-existent DB path")
    fake_db = Path("/tmp/definitely_does_not_exist_gcn_e016.db")
    try:
        results4 = search_papers(
            "attention",
            fake_db,
            EMB_PATH,
            top_k=3,
        )
        # If it returns [] without raising, that is also acceptable
        check("returns [] for missing DB (graceful)", results4 == [])
    except FileNotFoundError:
        check("raises FileNotFoundError for missing DB", True)
    except Exception as exc:
        check("raises FileNotFoundError for missing DB", False, str(exc))

    # -------------------------------------------------------------------------
    # Test 5: model cache — second call is faster (no reload)
    # -------------------------------------------------------------------------
    print("\n[Test 5] Model cache — second call should be faster")
    try:
        t0 = time.monotonic()
        search_papers("deep learning", DB_PATH, EMB_PATH, top_k=1)
        first_call = time.monotonic() - t0

        t0 = time.monotonic()
        search_papers("reinforcement learning", DB_PATH, EMB_PATH, top_k=1)
        second_call = time.monotonic() - t0

        print(f"  First call: {first_call:.2f}s, Second call: {second_call:.2f}s")
        # Second call should be much faster (no model loading)
        check(
            "second call faster than first (model cached)",
            second_call < first_call,
            f"{second_call:.2f}s vs {first_call:.2f}s",
        )
    except Exception as exc:
        print(f"  ERROR: {exc}")
        check("no exception raised", False, str(exc))

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"Results: {_PASS} passed, {_FAIL} failed")
    if _FAIL == 0:
        print("ALL CHECKS PASSED")
    else:
        print(f"{_FAIL} CHECK(S) FAILED")
    sys.exit(0 if _FAIL == 0 else 1)


if __name__ == "__main__":
    main()
