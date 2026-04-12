"""Validation script for E-015: L2 extraction pipeline.

Steps:
1. Extract L2 summaries for 10 papers from data/pipeline/arxiv_10k.parquet
   into /tmp/test_extract_l2.db
2. Verify table has exactly 10 rows
3. Verify all contribution fields are non-empty
4. Verify all domain_tags fields are parseable as JSON lists
5. Verify all key_findings fields have >= 1 item
6. Verify extraction_model == "qwen2.5-coder:7b" for all rows
7. Re-run with skip_existing=True — verify result["skipped"] == 10

Usage:
    source .venv/bin/activate
    python agents/engineer/workspace/validate_extract_l2.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
PARQUET_PATH = REPO_ROOT / "data" / "pipeline" / "arxiv_10k.parquet"
DB_PATH = Path("/tmp/test_extract_l2.db")

sys.path.insert(0, str(REPO_ROOT))

from src.knowledge.extract_l2 import extract_batch  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    """Record a single check result."""
    status = PASS if condition else FAIL
    _results.append((name, condition, detail))
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------


def main() -> int:
    print("=" * 60)
    print("E-015 Validation: L2 Extraction Pipeline")
    print("=" * 60)

    # --- Setup ---
    if not PARQUET_PATH.exists():
        print(f"[ERROR] Parquet file not found: {PARQUET_PATH}")
        return 1

    # Remove stale test DB if present
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed stale test DB: {DB_PATH}")

    df = pd.read_parquet(PARQUET_PATH)
    print(f"Loaded {len(df):,} papers from parquet.")

    # Use first 10 papers
    papers_10 = df.head(10).copy()
    arxiv_ids_10 = set(papers_10["arxiv_id"].tolist())
    print(f"Extracting L2 summaries for {len(papers_10)} papers...")
    print()

    # --- Step 1: Run extraction for 10 papers ---
    t0 = time.monotonic()
    result = extract_batch(
        papers=papers_10,
        db_path=DB_PATH,
        model="qwen2.5-coder:7b",
        skip_existing=False,
    )
    elapsed = time.monotonic() - t0
    avg_time = elapsed / max(result["extracted"], 1)

    print()
    print(f"Extraction complete in {elapsed:.1f}s (avg {avg_time:.1f}s/paper).")
    print(f"Result: {result}")
    print()
    print("--- Checks ---")

    # --- Step 2: Open DB and verify ---
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM paper_summaries").fetchall()

    # Check 1: exactly 10 rows
    check(
        "paper_summaries has exactly 10 rows",
        len(rows) == 10,
        f"got {len(rows)}",
    )

    # Check 2: all contribution fields non-empty
    empty_contributions = [
        r["arxiv_id"] for r in rows if not (r["contribution"] or "").strip()
    ]
    check(
        "all contribution fields non-empty",
        len(empty_contributions) == 0,
        f"empty: {empty_contributions}" if empty_contributions else "all present",
    )

    # Check 3: all domain_tags parseable as JSON lists
    bad_domain_tags = []
    for r in rows:
        try:
            val = json.loads(r["domain_tags"] or "[]")
            if not isinstance(val, list):
                bad_domain_tags.append(r["arxiv_id"])
        except json.JSONDecodeError:
            bad_domain_tags.append(r["arxiv_id"])
    check(
        "all domain_tags parseable as JSON lists",
        len(bad_domain_tags) == 0,
        f"bad: {bad_domain_tags}" if bad_domain_tags else "all valid",
    )

    # Check 4: all key_findings have >= 1 item
    short_findings = []
    for r in rows:
        try:
            findings = json.loads(r["key_findings"] or "[]")
            if len(findings) < 1:
                short_findings.append(r["arxiv_id"])
        except json.JSONDecodeError:
            short_findings.append(r["arxiv_id"])
    check(
        "all key_findings have >= 1 item",
        len(short_findings) == 0,
        f"short: {short_findings}" if short_findings else "all have findings",
    )

    # Check 5: extraction_model correct
    wrong_model = [
        r["arxiv_id"] for r in rows if r["extraction_model"] != "qwen2.5-coder:7b"
    ]
    check(
        'extraction_model == "qwen2.5-coder:7b" for all rows',
        len(wrong_model) == 0,
        f"wrong: {wrong_model}" if wrong_model else "all correct",
    )

    conn.close()

    # --- Step 3: Re-run with skip_existing=True ---
    print()
    print("Re-running with skip_existing=True...")
    result2 = extract_batch(
        papers=papers_10,
        db_path=DB_PATH,
        model="qwen2.5-coder:7b",
        skip_existing=True,
    )
    print(f"Result2: {result2}")
    print()
    print("--- Checks (skip_existing) ---")

    check(
        'skip_existing=True: result["skipped"] == 10',
        result2["skipped"] == 10,
        f"got skipped={result2['skipped']}",
    )
    check(
        'skip_existing=True: result["extracted"] == 0',
        result2["extracted"] == 0,
        f"got extracted={result2['extracted']}",
    )

    # --- Summary ---
    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"Results: {passed}/{total} checks PASSED")
    print(f"Average extraction time: {avg_time:.1f}s/paper")

    # Print sample output for quality inspection
    conn2 = sqlite3.connect(str(DB_PATH))
    conn2.row_factory = sqlite3.Row
    sample = conn2.execute(
        "SELECT arxiv_id, contribution, domain_tags, key_findings "
        "FROM paper_summaries LIMIT 3"
    ).fetchall()
    conn2.close()

    print()
    print("--- Sample Extractions (first 3 papers) ---")
    for r in sample:
        print(f"\narxiv_id: {r['arxiv_id']}")
        print(f"  contribution: {r['contribution'][:100]}...")
        print(f"  domain_tags: {r['domain_tags']}")
        findings = json.loads(r["key_findings"] or "[]")
        print(
            f"  key_findings ({len(findings)} items): {findings[0][:80] if findings else 'N/A'}..."
        )

    failed = total - passed
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
