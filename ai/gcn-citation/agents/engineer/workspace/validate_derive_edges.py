"""Validation script for derive_edges.py (E-022).

Runs build_all_edges() on data/knowledge/knowledge.db and verifies:
  1. paper_edges table exists and has rows
  2. shares_method edges > 0
  3. co_domain edges > 0
  4. No self-loops (source_id != target_id)
  5. source_id < target_id for all edges (consistent ordering)
  6. Prints top 5 methods by edge count
  7. Prints top 5 domain tags by edge count
  8. Spot-checks 3 method edges with paper titles
  9. Prints PASS/FAIL
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project root and activate src/ on the path
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent.parent  # agents/engineer/workspace -> root
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from knowledge.derive_edges import build_all_edges
from knowledge.schema import get_connection, init_database

DB_PATH = _PROJECT_ROOT / "data" / "knowledge" / "knowledge.db"


def main() -> int:
    """Run all validation checks. Returns 0 on PASS, 1 on FAIL."""
    if not DB_PATH.exists():
        print(f"ERROR: knowledge.db not found at {DB_PATH}", file=sys.stderr)
        return 1

    # -----------------------------------------------------------------------
    # Step 1 — Run edge builders
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Running build_all_edges()...")
    print("=" * 60)
    counts = build_all_edges(DB_PATH)
    print(f"\nEdge counts returned: {counts}\n")

    # -----------------------------------------------------------------------
    # Step 2 — Query the paper_edges table
    # -----------------------------------------------------------------------
    conn = get_connection(DB_PATH)

    # Ensure paper_edges was created by checking sqlite_master
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    failures: list[str] = []

    # Check 1: table exists
    if "paper_edges" not in tables:
        print("FAIL: paper_edges table does not exist")
        return 1
    print("CHECK 1 PASS: paper_edges table exists")

    # Check 2: has rows
    total = conn.execute("SELECT COUNT(*) FROM paper_edges").fetchone()[0]
    if total == 0:
        failures.append("paper_edges has 0 rows")
    else:
        print(f"CHECK 2 PASS: paper_edges has {total} rows total")

    # Check 3: shares_method edges > 0
    method_count = conn.execute(
        "SELECT COUNT(*) FROM paper_edges WHERE edge_type = 'shares_method'"
    ).fetchone()[0]
    if method_count == 0:
        failures.append("shares_method edges = 0")
    else:
        print(f"CHECK 3 PASS: {method_count} shares_method edges")

    # Check 4: co_domain edges > 0
    domain_count = conn.execute(
        "SELECT COUNT(*) FROM paper_edges WHERE edge_type = 'co_domain'"
    ).fetchone()[0]
    if domain_count == 0:
        failures.append("co_domain edges = 0")
    else:
        print(f"CHECK 4 PASS: {domain_count} co_domain edges")

    # Check 5: no self-loops
    self_loops = conn.execute(
        "SELECT COUNT(*) FROM paper_edges WHERE source_id = target_id"
    ).fetchone()[0]
    if self_loops > 0:
        failures.append(f"{self_loops} self-loop edges found")
    else:
        print("CHECK 5 PASS: no self-loops")

    # Check 6: source_id < target_id for all edges
    bad_order = conn.execute(
        "SELECT COUNT(*) FROM paper_edges WHERE source_id >= target_id"
    ).fetchone()[0]
    if bad_order > 0:
        failures.append(
            f"{bad_order} edges with source_id >= target_id (wrong ordering)"
        )
    else:
        print("CHECK 6 PASS: all edges have source_id < target_id")

    # -----------------------------------------------------------------------
    # Step 3 — Top 5 methods by edge count
    # -----------------------------------------------------------------------
    print("\n--- Top 5 methods by edge count ---")
    top_methods = conn.execute(
        """
        SELECT shared_value, COUNT(*) as cnt
        FROM paper_edges
        WHERE edge_type = 'shares_method'
        GROUP BY shared_value
        ORDER BY cnt DESC
        LIMIT 5
        """
    ).fetchall()
    for method, cnt in top_methods:
        print(f"  {cnt:4d} edges  |  {method}")

    # -----------------------------------------------------------------------
    # Step 4 — Top 5 domain tags by edge count
    # -----------------------------------------------------------------------
    print("\n--- Top 5 domain tags by edge count ---")
    top_domains = conn.execute(
        """
        SELECT shared_value, COUNT(*) as cnt
        FROM paper_edges
        WHERE edge_type = 'co_domain'
        GROUP BY shared_value
        ORDER BY cnt DESC
        LIMIT 5
        """
    ).fetchall()
    for tag, cnt in top_domains:
        print(f"  {cnt:4d} edges  |  {tag}")

    # -----------------------------------------------------------------------
    # Step 5 — Spot-check 3 method edges: print the two papers' titles
    # -----------------------------------------------------------------------
    print("\n--- Spot-check: 3 method edges with paper titles ---")
    sample_edges = conn.execute(
        """
        SELECT e.shared_value, e.source_id, e.target_id,
               s.title AS title_a, t.title AS title_b
        FROM paper_edges e
        JOIN paper_summaries s ON s.arxiv_id = e.source_id
        JOIN paper_summaries t ON t.arxiv_id = e.target_id
        WHERE e.edge_type = 'shares_method'
        ORDER BY e.edge_id
        LIMIT 3
        """
    ).fetchall()
    for idx, (method, id_a, id_b, title_a, title_b) in enumerate(sample_edges, 1):
        print(f"\nEdge {idx}: shared_method = '{method}'")
        print(f"  Paper A [{id_a}]: {title_a}")
        print(f"  Paper B [{id_b}]: {title_b}")

    conn.close()

    # -----------------------------------------------------------------------
    # Final verdict
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    if failures:
        print("FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
