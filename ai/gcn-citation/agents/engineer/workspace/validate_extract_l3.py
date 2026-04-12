"""Validation script for E-020: extract_l3.py

Strategy:
- Uses a FRESH isolated temp DB (populated with paper_summaries from real DB)
  so we always run extraction from a clean state.
- This ensures Ollama is called and we can verify real outputs.
- The real production DB is never written to by this script.

Checks:
1. Extract claims for 10 papers into an isolated temp DB.
2. claims table has 10-30 rows (1-3 per paper).
3. All claim_type values are valid enum values.
4. All assertion fields non-empty and don't start with "This paper" / "We".
5. All claim_id values follow {arxiv_id}_NN pattern.
6. claim_sources has one row per claim.
7. Resume check: run again with skip_existing=True → 0 new claims inserted.

Prints PASS/FAIL for each check and a final summary.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Setup: locate project root and activate imports
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from knowledge.extract_l3 import extract_claims_batch  # noqa: E402
from knowledge.schema import get_connection, init_database  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REAL_DB = _REPO_ROOT / "data" / "knowledge" / "knowledge.db"
_VALID_CLAIM_TYPES = frozenset(
    {"empirical", "theoretical", "architectural", "comparative", "observation"}
)
_CLAIM_ID_PATTERN = re.compile(r"^.+_\d{2}$")
_ASSERTION_BAD_PREFIXES = re.compile(r"^(this paper|we |our )", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def count_claims(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]


def count_claim_sources(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM claim_sources").fetchone()[0]


def build_isolated_db(tmp_db: Path, n_papers: int = 10) -> list[str]:
    """Create a fresh isolated DB with n_papers from paper_summaries only.

    Reads paper_summaries from the real DB and writes them to a fresh temp DB.
    The claims and claim_sources tables are empty (fresh extraction target).

    Args:
        tmp_db: Path for the new isolated DB.
        n_papers: Number of papers to copy.

    Returns:
        List of arxiv_ids copied.
    """
    # Create fresh schema (no data)
    conn = init_database(tmp_db)

    # Read from real DB
    real_conn = sqlite3.connect(str(_REAL_DB))
    real_conn.row_factory = sqlite3.Row
    rows = real_conn.execute(
        """
        SELECT arxiv_id, title, contribution, method, datasets, key_findings,
               limitations, domain_tags, related_methods, extraction_model
        FROM paper_summaries
        ORDER BY arxiv_id
        LIMIT ?
        """,
        (n_papers,),
    ).fetchall()
    real_conn.close()

    arxiv_ids = []
    for row in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO paper_summaries
                (arxiv_id, title, contribution, method, datasets, key_findings,
                 limitations, domain_tags, related_methods, extraction_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["arxiv_id"],
                row["title"],
                row["contribution"],
                row["method"],
                row["datasets"],
                row["key_findings"],
                row["limitations"],
                row["domain_tags"],
                row["related_methods"],
                row["extraction_model"],
            ),
        )
        arxiv_ids.append(row["arxiv_id"])
    conn.commit()
    conn.close()
    return arxiv_ids


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all validation checks. Returns 0 on all-pass, 1 on any failure."""
    results: list[bool] = []

    # -----------------------------------------------------------------------
    # 0. Verify source DB exists and has paper_summaries
    # -----------------------------------------------------------------------
    print("\n=== Setup ===")
    if not _REAL_DB.exists():
        print(f"  [FAIL] knowledge.db not found at {_REAL_DB}")
        print("  Cannot proceed — run E-015 / E-018 first to populate paper_summaries.")
        return 1

    real_conn = sqlite3.connect(str(_REAL_DB))
    real_conn.row_factory = sqlite3.Row
    n_summaries = real_conn.execute("SELECT COUNT(*) FROM paper_summaries").fetchone()[
        0
    ]
    real_conn.close()

    ok = check(
        "paper_summaries populated",
        n_summaries >= 10,
        f"{n_summaries} rows in paper_summaries",
    )
    results.append(ok)
    if not ok:
        print("  Cannot proceed — need at least 10 papers in paper_summaries.")
        return 1

    # -----------------------------------------------------------------------
    # 1. Build isolated DB and run extraction for 10 papers
    # -----------------------------------------------------------------------
    print("\n=== Check 1: Extract claims for 10 papers (isolated DB) ===")

    tmp_dir = tempfile.mkdtemp(prefix="validate_l3_")
    tmp_db = Path(tmp_dir) / "knowledge_isolated.db"

    arxiv_ids = build_isolated_db(tmp_db, n_papers=10)
    print(f"  Isolated DB: {tmp_db}")
    print(f"  Papers in isolated DB: {len(arxiv_ids)}")
    print(f"  First 3 arxiv_ids: {arxiv_ids[:3]}")

    # Run extraction on isolated DB (no existing claims → all papers processed)
    counters = extract_claims_batch(
        tmp_db,
        skip_existing=True,  # safe here — isolated DB has no claims
        limit=10,
    )

    papers_processed = counters["papers_processed"]
    claims_extracted = counters["claims_extracted"]
    errors = counters["errors"]

    ok = check(
        "extraction completed with at least 1 paper processed",
        papers_processed > 0,
        f"papers_processed={papers_processed}, errors={errors}",
    )
    results.append(ok)

    if not ok:
        print(
            "  NOTE: If Ollama is not running, start it with `ollama serve` "
            "and re-run validation."
        )
        # Still run remaining checks against empty DB to confirm structure
    else:
        print(
            f"  Extracted {claims_extracted} claims from {papers_processed} papers "
            f"({errors} errors)"
        )

    # -----------------------------------------------------------------------
    # 2. claims table row count: 10-30
    # -----------------------------------------------------------------------
    print("\n=== Check 2: claims table row count (10–30 expected) ===")

    conn = get_connection(tmp_db)
    n_claims = count_claims(conn)

    ok = check(
        "claims table has 10–30 rows",
        10 <= n_claims <= 30,
        f"{n_claims} rows found",
    )
    results.append(ok)

    # -----------------------------------------------------------------------
    # 3. All claim_type values are valid
    # -----------------------------------------------------------------------
    print("\n=== Check 3: claim_type values ===")

    if n_claims > 0:
        bad_types = conn.execute(
            f"""
            SELECT claim_id, claim_type FROM claims
            WHERE claim_type NOT IN ({', '.join('?' * len(_VALID_CLAIM_TYPES))})
            """,
            list(_VALID_CLAIM_TYPES),
        ).fetchall()

        ok = check(
            "all claim_type values valid",
            len(bad_types) == 0,
            f"{len(bad_types)} invalid: {[dict(r) for r in bad_types[:5]]}",
        )
    else:
        ok = check(
            "all claim_type values valid",
            False,
            "skipped — no claims extracted",
        )
    results.append(ok)

    # -----------------------------------------------------------------------
    # 4. All assertion fields non-empty and no first-person prefixes
    # -----------------------------------------------------------------------
    print("\n=== Check 4: assertion field quality ===")

    if n_claims > 0:
        all_claims = conn.execute("SELECT claim_id, assertion FROM claims").fetchall()

        empty_assertions = [r["claim_id"] for r in all_claims if not r["assertion"]]
        ok_empty = check(
            "no empty assertion fields",
            len(empty_assertions) == 0,
            f"{len(empty_assertions)} empty: {empty_assertions[:5]}",
        )
        results.append(ok_empty)

        bad_assertions = [
            r["claim_id"]
            for r in all_claims
            if _ASSERTION_BAD_PREFIXES.match(r["assertion"] or "")
        ]
        ok_prefixes = check(
            "no first-person prefixes in assertions",
            len(bad_assertions) == 0,
            f"{len(bad_assertions)} bad: {bad_assertions[:5]}",
        )
        results.append(ok_prefixes)
    else:
        ok_empty = check(
            "no empty assertion fields",
            False,
            "skipped — no claims extracted",
        )
        ok_prefixes = check(
            "no first-person prefixes in assertions",
            False,
            "skipped — no claims extracted",
        )
        results.append(ok_empty)
        results.append(ok_prefixes)

    # -----------------------------------------------------------------------
    # 5. All claim_id values follow {arxiv_id}_NN pattern
    # -----------------------------------------------------------------------
    print("\n=== Check 5: claim_id format ===")

    if n_claims > 0:
        all_claim_ids = conn.execute("SELECT claim_id FROM claims").fetchall()
        bad_ids = [
            row["claim_id"]
            for row in all_claim_ids
            if not _CLAIM_ID_PATTERN.match(row["claim_id"])
        ]
        ok = check(
            "all claim_ids match {arxiv_id}_NN pattern",
            len(bad_ids) == 0,
            f"{len(bad_ids)} bad IDs: {bad_ids[:5]}",
        )
    else:
        ok = check(
            "all claim_ids match {arxiv_id}_NN pattern",
            False,
            "skipped — no claims extracted",
        )
    results.append(ok)

    # -----------------------------------------------------------------------
    # 6. claim_sources has one row per claim
    # -----------------------------------------------------------------------
    print("\n=== Check 6: claim_sources coverage ===")

    n_sources = count_claim_sources(conn)
    ok = check(
        "claim_sources row count equals claims row count",
        n_sources == n_claims,
        f"{n_sources} source rows vs {n_claims} claim rows",
    )
    results.append(ok)

    if n_claims > 0:
        orphaned = conn.execute(
            """
            SELECT c.claim_id FROM claims c
            LEFT JOIN claim_sources cs ON cs.claim_id = c.claim_id
            WHERE cs.claim_id IS NULL
            """
        ).fetchall()
        ok = check(
            "no orphaned claims (every claim has a source row)",
            len(orphaned) == 0,
            f"{len(orphaned)} orphaned: {[r['claim_id'] for r in orphaned[:5]]}",
        )
    else:
        ok = check(
            "no orphaned claims",
            True,
            "trivially true — no claims",
        )
    results.append(ok)

    # -----------------------------------------------------------------------
    # 7. Resume check: run again with skip_existing=True → 0 new claims
    # -----------------------------------------------------------------------
    print("\n=== Check 7: resume / skip_existing ===")

    n_before = count_claims(conn)
    conn.close()

    counters2 = extract_claims_batch(
        tmp_db,
        skip_existing=True,
        limit=10,
    )

    conn2 = get_connection(tmp_db)
    n_after = count_claims(conn2)
    conn2.close()

    ok = check(
        "second run with skip_existing=True adds 0 new claims",
        n_after == n_before,
        (
            f"before={n_before}, after={n_after}, "
            f"papers_processed={counters2['papers_processed']}"
        ),
    )
    results.append(ok)

    # -----------------------------------------------------------------------
    # Summary statistics
    # -----------------------------------------------------------------------
    print("\n=== Summary ===")
    if papers_processed > 0:
        avg = claims_extracted / papers_processed
        print(f"  Papers processed : {papers_processed}")
        print(f"  Claims extracted : {claims_extracted}")
        print(f"  Avg claims/paper : {avg:.2f}")
        print(f"  Errors           : {errors}")

    # Print sample of claims for quality inspection
    conn_final = get_connection(tmp_db)
    sample_claims = conn_final.execute(
        "SELECT claim_id, claim_type, assertion, domain, method FROM claims LIMIT 5"
    ).fetchall()
    conn_final.close()

    if sample_claims:
        print("\n  Sample claims:")
        for c in sample_claims:
            print(
                f"    {c['claim_id']} [{c['claim_type']}] "
                f"{(c['assertion'] or '')[:80]}"
            )

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Final verdict
    # -----------------------------------------------------------------------
    n_pass = sum(results)
    n_fail = len(results) - n_pass
    print(f"\n=== RESULT: {n_pass}/{len(results)} checks passed ===")
    if n_fail == 0:
        print("ALL CHECKS PASSED")
        return 0
    else:
        print(f"FAILED: {n_fail} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
