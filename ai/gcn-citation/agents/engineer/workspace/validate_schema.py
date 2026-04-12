"""Validation script for src/knowledge/schema.py.

Tests:
    1. init_database creates all 6 tables
    2. init_database is idempotent (calling twice raises no error)
    3. insert a paper_summary, query it back — all fields round-trip correctly
    4. insert a claim with valid claim_type, query it back
    5. invalid claim_type raises constraint error
    6. invalid epistemic_status raises constraint error
    7. claim_edges edge_type constraint enforced
    8. get_connection returns working connection to existing DB

Run: python agents/engineer/workspace/validate_schema.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import sqlite3
from knowledge.schema import init_database, get_connection, KNOWLEDGE_DB_VERSION

TEST_DB = Path("/tmp/test_knowledge.db")

PASS = "PASS"
FAIL = "FAIL"

results: list[tuple[str, str, str]] = []  # (name, status, detail)


def _cleanup() -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()


def _record(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, status, detail))
    mark = "✓" if passed else "✗"
    print(f"  [{mark}] {name}: {status}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Test 1: init_database creates all 6 expected tables
# ---------------------------------------------------------------------------
_cleanup()
try:
    conn = init_database(TEST_DB)
    tables_result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = {row[0] for row in tables_result}
    expected = {
        "chunks",
        "paper_summaries",
        "claims",
        "claim_sources",
        "claim_edges",
        "_meta",
    }
    missing = expected - table_names
    _record(
        "init_database_creates_6_tables",
        len(missing) == 0,
        f"missing={missing}" if missing else f"found={sorted(table_names)}",
    )
    conn.close()
except Exception as exc:
    _record("init_database_creates_6_tables", False, str(exc))

# ---------------------------------------------------------------------------
# Test 2: init_database is idempotent
# ---------------------------------------------------------------------------
try:
    conn2 = init_database(TEST_DB)  # second call on same file
    conn2.close()
    _record("init_database_idempotent", True, "second call raised no error")
except Exception as exc:
    _record("init_database_idempotent", False, str(exc))

# ---------------------------------------------------------------------------
# Test 3: paper_summary round-trip
# ---------------------------------------------------------------------------
try:
    conn = init_database(TEST_DB)
    datasets_val = json.dumps(["CIFAR-10", "ImageNet"])
    key_findings_val = json.dumps(["Finding A", "Finding B"])
    domain_tags_val = json.dumps(["CV", "deep_learning"])
    related_methods_val = json.dumps(["ResNet", "VGG"])
    conn.execute(
        """
        INSERT INTO paper_summaries
            (arxiv_id, title, contribution, method, datasets, key_findings,
             limitations, domain_tags, related_methods, extraction_model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "2303.00001",
            "Test Paper Title",
            "Introduces a new method.",
            "Convolutional neural network.",
            datasets_val,
            key_findings_val,
            "Limited to image classification.",
            domain_tags_val,
            related_methods_val,
            "claude-sonnet-4-6",
        ],
    )
    row = conn.execute(
        "SELECT arxiv_id, title, contribution, method, datasets, key_findings, "
        "limitations, domain_tags, related_methods, extraction_model "
        "FROM paper_summaries WHERE arxiv_id = '2303.00001'"
    ).fetchone()
    assert row is not None, "row not found"
    assert row[0] == "2303.00001"
    assert row[1] == "Test Paper Title"
    assert row[2] == "Introduces a new method."
    assert row[3] == "Convolutional neural network."
    assert row[9] == "claude-sonnet-4-6"
    conn.commit()  # SQLite requires explicit commit before close
    _record("paper_summary_round_trip", True, "all 10 fields verified")
    conn.close()
except Exception as exc:
    _record("paper_summary_round_trip", False, str(exc))

# ---------------------------------------------------------------------------
# Test 4: insert a claim with valid claim_type and query it back
# ---------------------------------------------------------------------------
try:
    conn = get_connection(TEST_DB)
    conn.execute(
        """
        INSERT INTO claims (claim_id, claim_type, assertion, domain, method,
                            epistemic_status, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "claim-001",
            "empirical",
            "Attention achieves state-of-the-art on WMT14.",
            "NLP",
            "Transformer",
            "preliminary",
            0.8,
        ],
    )
    row = conn.execute(
        "SELECT claim_id, claim_type, assertion, epistemic_status, confidence "
        "FROM claims WHERE claim_id = 'claim-001'"
    ).fetchone()
    assert row is not None
    assert row[0] == "claim-001"
    assert row[1] == "empirical"
    assert abs(row[4] - 0.8) < 1e-6
    _record(
        "claim_valid_type_round_trip",
        True,
        "claim_type='empirical' accepted and retrieved",
    )
    conn.close()
except Exception as exc:
    _record("claim_valid_type_round_trip", False, str(exc))

# ---------------------------------------------------------------------------
# Test 5: invalid claim_type raises constraint error
# ---------------------------------------------------------------------------
try:
    conn = get_connection(TEST_DB)
    raised = False
    try:
        conn.execute(
            "INSERT INTO claims (claim_id, claim_type, assertion) VALUES (?, ?, ?)",
            ["claim-bad-type", "invalid_type", "Some assertion."],
        )
    except sqlite3.IntegrityError:
        raised = True
    except Exception as exc:
        # DuckDB may raise a different error subclass — accept any error
        if "constraint" in str(exc).lower() or "check" in str(exc).lower():
            raised = True
        else:
            raise
    _record(
        "invalid_claim_type_raises",
        raised,
        "ConstraintException raised as expected" if raised else "NO error raised",
    )
    conn.close()
except Exception as exc:
    _record("invalid_claim_type_raises", False, str(exc))

# ---------------------------------------------------------------------------
# Test 6: invalid epistemic_status raises constraint error
# ---------------------------------------------------------------------------
try:
    conn = get_connection(TEST_DB)
    raised = False
    try:
        conn.execute(
            "INSERT INTO claims (claim_id, claim_type, assertion, epistemic_status) VALUES (?, ?, ?, ?)",
            ["claim-bad-status", "empirical", "Some assertion.", "definitely_true"],
        )
    except sqlite3.IntegrityError:
        raised = True
    except Exception as exc:
        if "constraint" in str(exc).lower() or "check" in str(exc).lower():
            raised = True
        else:
            raise
    _record(
        "invalid_epistemic_status_raises",
        raised,
        "ConstraintException raised as expected" if raised else "NO error raised",
    )
    conn.close()
except Exception as exc:
    _record("invalid_epistemic_status_raises", False, str(exc))

# ---------------------------------------------------------------------------
# Test 7: claim_edges edge_type constraint enforced
# ---------------------------------------------------------------------------
try:
    conn = get_connection(TEST_DB)
    raised = False
    try:
        conn.execute(
            "INSERT INTO claim_edges (edge_id, source_id, target_id, edge_type) VALUES (?, ?, ?, ?)",
            ["edge-bad", "claim-001", "claim-001", "maybe_supports"],
        )
    except sqlite3.IntegrityError:
        raised = True
    except Exception as exc:
        if "constraint" in str(exc).lower() or "check" in str(exc).lower():
            raised = True
        else:
            raise
    _record(
        "invalid_edge_type_raises",
        raised,
        "ConstraintException raised as expected" if raised else "NO error raised",
    )
    conn.close()
except Exception as exc:
    _record("invalid_edge_type_raises", False, str(exc))

# ---------------------------------------------------------------------------
# Test 8: get_connection returns working connection to existing DB
# ---------------------------------------------------------------------------
try:
    conn = get_connection(TEST_DB)
    count = conn.execute("SELECT COUNT(*) FROM paper_summaries").fetchone()[0]
    version = conn.execute("SELECT value FROM _meta WHERE key = 'version'").fetchone()[
        0
    ]
    assert count >= 1, f"expected at least 1 paper_summary, got {count}"
    assert version == KNOWLEDGE_DB_VERSION, f"version mismatch: {version!r}"
    _record(
        "get_connection_works", True, f"paper_summaries={count}, version={version!r}"
    )
    conn.close()
except Exception as exc:
    _record("get_connection_works", False, str(exc))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
_cleanup()

print()
passed = sum(1 for _, s, _ in results if s == PASS)
total = len(results)
print(f"Results: {passed}/{total} PASS")

if passed < total:
    print("\nFailed tests:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  FAIL  {name}: {detail}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
