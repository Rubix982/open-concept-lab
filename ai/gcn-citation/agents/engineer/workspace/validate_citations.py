"""Validation script for pipeline/citations.py.

Mocks S3 by loading from a local test fixture (test_citations_sample.jsonl).
Runs all checks and prints PASS/FAIL per check.

Usage:
    python3 agents/engineer/workspace/validate_citations.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Ensure the src tree is on the path
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import numpy as np

from gcn_citation.pipeline.citations import (
    CitationEdges,
    _normalise_arxiv_id,
    _process_shard_pass1,
    assign_indices,
    build_id_to_index,
    load_s2orc_citations,
)

# ---------------------------------------------------------------------------
# Test setup
# ---------------------------------------------------------------------------

FIXTURE_PATH = Path(__file__).parent / "test_citations_sample.jsonl"

# The working set: papers 01001, 01002, 01003 have in-set refs;
# 01004 and 01005 are in set but reference out-of-set papers.
KNOWN_ARXIV_IDS = {
    "2106.01001",
    "2106.01002",
    "2106.01003",
    "2106.01004",
    "2106.01005",
}

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    """Record a check result and print immediately."""
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}" + (f": {detail}" if detail else ""))
    RESULTS.append((name, passed, detail))


# ---------------------------------------------------------------------------
# Helper: run the two-pass logic against the local fixture (no S3)
# ---------------------------------------------------------------------------


def _run_local_fixture() -> CitationEdges:
    """Process the fixture file directly (bypasses S3 download)."""
    openalex_url_to_arxiv: dict[str, str] = {}
    raw_edges: list[tuple[str, str]] = []

    _process_shard_pass1(
        FIXTURE_PATH,
        KNOWN_ARXIV_IDS,
        openalex_url_to_arxiv,
        raw_edges,
    )

    # Resolve edges
    source_ids: list[str] = []
    target_ids: list[str] = []

    for src_arxiv, tgt_openalex_url in raw_edges:
        tgt_arxiv = openalex_url_to_arxiv.get(tgt_openalex_url)
        if tgt_arxiv is None:
            continue
        if tgt_arxiv not in KNOWN_ARXIV_IDS:
            continue
        source_ids.append(src_arxiv)
        target_ids.append(tgt_arxiv)

    return CitationEdges(
        source_ids=np.array(source_ids, dtype=object),
        target_ids=np.array(target_ids, dtype=object),
        source_indices=None,
        target_indices=None,
    )


# ---------------------------------------------------------------------------
# Check 1: load_s2orc_citations raises NotImplementedError
# ---------------------------------------------------------------------------

print("\n=== Check group 1: load_s2orc_citations stub ===")
try:
    load_s2orc_citations(Path("/nonexistent"), set())
    check("s2orc raises NotImplementedError", False, "did not raise")
except NotImplementedError as exc:
    msg = str(exc)
    check("s2orc raises NotImplementedError", True)
    check(
        "s2orc error message mentions load_openalex_citations",
        "load_openalex_citations" in msg,
        f"message: {msg[:80]}",
    )

# ---------------------------------------------------------------------------
# Check 2: _normalise_arxiv_id handles URL prefixes
# ---------------------------------------------------------------------------

print("\n=== Check group 2: _normalise_arxiv_id ===")
cases = [
    ("2106.01234", "2106.01234"),
    ("https://arxiv.org/abs/2106.01234", "2106.01234"),
    ("http://arxiv.org/abs/1706.03762", "1706.03762"),
    ("arxiv:2101.00001", "2101.00001"),
    ("HTTPS://ARXIV.ORG/ABS/2106.01234", "2106.01234"),
]
for raw, expected in cases:
    result = _normalise_arxiv_id(raw)
    check(f"normalise_arxiv_id({raw!r})", result == expected, f"got {result!r}")

# ---------------------------------------------------------------------------
# Check 3: process fixture — correct edge count
# ---------------------------------------------------------------------------

print("\n=== Check group 3: edge filtering from fixture ===")
edges = _run_local_fixture()

check(
    "CitationEdges has 3 edges",
    len(edges.source_ids) == 3,
    f"got {len(edges.source_ids)}",
)
check(
    "source_ids is np.ndarray",
    isinstance(edges.source_ids, np.ndarray),
    str(type(edges.source_ids)),
)
check(
    "target_ids is np.ndarray",
    isinstance(edges.target_ids, np.ndarray),
    str(type(edges.target_ids)),
)
check("source_indices is None before assign", edges.source_indices is None)
check("target_indices is None before assign", edges.target_indices is None)

# Check specific edges (order may vary; use set of pairs)
edge_pairs = set(zip(edges.source_ids.tolist(), edges.target_ids.tolist()))
expected_pairs = {
    ("2106.01001", "2106.01002"),
    ("2106.01002", "2106.01003"),
    ("2106.01003", "2106.01001"),
}
check(
    "correct edge pairs (both-in-set edges only)",
    edge_pairs == expected_pairs,
    f"got {edge_pairs}",
)

# Verify out-of-set sources not present
out_of_set_sources = {
    "9999.99991",
    "9999.99992",
}
source_set = set(edges.source_ids.tolist())
check(
    "out-of-set sources filtered",
    out_of_set_sources.isdisjoint(source_set),
    f"sources present: {source_set & out_of_set_sources}",
)

# Verify in-set-but-out-of-set-target papers (01004, 01005) appear nowhere
check(
    "papers with out-of-set targets absent from source_ids",
    "2106.01004" not in source_set and "2106.01005" not in source_set,
    f"found: {source_set & {'2106.01004', '2106.01005'}}",
)

# ---------------------------------------------------------------------------
# Check 4: build_id_to_index
# ---------------------------------------------------------------------------

print("\n=== Check group 4: build_id_to_index ===")
sample_ids = ["2106.01234", "1706.03762", "2101.00001", "1706.03762"]  # dup
id_map = build_id_to_index(sample_ids)

check("returns dict", isinstance(id_map, dict))
check("deduplicates IDs", len(id_map) == 3, f"got {len(id_map)}")
check(
    "indices by sorted order",
    id_map == {"1706.03762": 0, "2101.00001": 1, "2106.01234": 2},
    str(id_map),
)
check("lowest lexicographic ID gets index 0", id_map["1706.03762"] == 0)
check("highest lexicographic ID gets index 2", id_map["2106.01234"] == 2)

# ---------------------------------------------------------------------------
# Check 5: assign_indices
# ---------------------------------------------------------------------------

print("\n=== Check group 5: assign_indices ===")
# Build a small id_to_index for the in-set IDs
id_to_index = build_id_to_index(sorted(KNOWN_ARXIV_IDS))

mapped = assign_indices(edges, id_to_index)

check("mapped source_indices is ndarray", isinstance(mapped.source_indices, np.ndarray))
check("mapped target_indices is ndarray", isinstance(mapped.target_indices, np.ndarray))
check("mapped source_indices dtype int64", mapped.source_indices.dtype == np.int64)
check("mapped target_indices dtype int64", mapped.target_indices.dtype == np.int64)
check(
    "same number of edges after assign",
    len(mapped.source_ids) == 3,
    f"got {len(mapped.source_ids)}",
)

# Verify each source_id maps to the expected index
for sid, sidx in zip(mapped.source_ids.tolist(), mapped.source_indices.tolist()):
    expected_idx = id_to_index[sid]
    check(
        f"source_id {sid!r} maps to index {expected_idx}",
        sidx == expected_idx,
        f"got {sidx}",
    )

for tid, tidx in zip(mapped.target_ids.tolist(), mapped.target_indices.tolist()):
    expected_idx = id_to_index[tid]
    check(
        f"target_id {tid!r} maps to index {expected_idx}",
        tidx == expected_idx,
        f"got {tidx}",
    )

# Check that an unknown ID causes the edge to be dropped
extra_edge = CitationEdges(
    source_ids=np.array(["2106.01001", "UNKNOWN_ID"], dtype=object),
    target_ids=np.array(["2106.01002", "2106.01002"], dtype=object),
    source_indices=None,
    target_indices=None,
)
mapped_extra = assign_indices(extra_edge, id_to_index)
check(
    "edge with unknown source dropped by assign_indices",
    len(mapped_extra.source_ids) == 1,
    f"got {len(mapped_extra.source_ids)} edges",
)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Summary ===")
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = sum(1 for _, ok, _ in RESULTS if not ok)
total = len(RESULTS)
print(f"  {passed}/{total} checks passed, {failed} failed.")

if failed > 0:
    print("\nFailed checks:")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  FAIL  {name}: {detail}")
    sys.exit(1)
else:
    print("  All checks PASS.")
    sys.exit(0)
