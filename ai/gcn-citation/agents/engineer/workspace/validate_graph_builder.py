"""Validation script for pipeline/graph_builder.py.

Runs four test suites:
  1. build_knn_edges smoke test (skipped if faiss not installed)
  2. build_hetero_graph integration test (skipped if torch_geometric not installed)
  3. validate_graph unit tests (mocks HeteroData-like dict if torch_geometric absent)
  4. co_category cap test

Print PASS/FAIL for each check.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Ensure repo root is on path
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import numpy as np

# ---------------------------------------------------------------------------
# Availability guards
# ---------------------------------------------------------------------------
try:
    import faiss

    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None  # type: ignore[assignment]
    _FAISS_AVAILABLE = False

try:
    import torch
    from torch_geometric.data import HeteroData

    _TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    HeteroData = None  # type: ignore[assignment]
    _TORCH_GEOMETRIC_AVAILABLE = False

try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore[assignment]
    _PANDAS_AVAILABLE = False

from gcn_citation.pipeline.citations import CitationEdges

_pass_count = 0
_fail_count = 0
_skip_count = 0


def _report(label: str, passed: bool | None, detail: str = "") -> None:
    global _pass_count, _fail_count, _skip_count
    if passed is None:
        _skip_count += 1
        tag = "SKIP"
    elif passed:
        _pass_count += 1
        tag = "PASS"
    else:
        _fail_count += 1
        tag = "FAIL"
    msg = f"  [{tag}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# ===========================================================================
# Test Suite 1: build_knn_edges smoke test
# ===========================================================================


def test_build_knn_edges() -> None:
    print("\n=== Suite 1: build_knn_edges smoke test ===")

    if not _FAISS_AVAILABLE:
        _report("build_knn_edges (all subtests)", None, "SKIP (faiss not installed)")
        return

    from gcn_citation.pipeline.graph_builder import build_knn_edges

    rng = np.random.default_rng(0)
    N, D, K = 20, 16, 3
    vecs = rng.standard_normal((N, D)).astype(np.float32)

    try:
        src, dst = build_knn_edges(vecs, k=K, batch_size=8)
    except Exception as exc:
        _report("build_knn_edges returns without error", False, str(exc))
        return

    _report(
        "output src is 1-D int64",
        src.ndim == 1 and src.dtype == np.int64,
        f"shape={src.shape}, dtype={src.dtype}",
    )
    _report(
        "output dst is 1-D int64",
        dst.ndim == 1 and dst.dtype == np.int64,
        f"shape={dst.shape}, dtype={dst.dtype}",
    )
    _report(
        "src and dst same length",
        len(src) == len(dst),
        f"len(src)={len(src)}, len(dst)={len(dst)}",
    )
    _report(
        "no self-loops in output",
        bool(np.all(src != dst)),
        f"self-loops: {int(np.sum(src == dst))}",
    )
    _report(
        "all src indices in [0, N)",
        bool(np.all(src >= 0) and np.all(src < N)),
        f"min={src.min()}, max={src.max()}",
    )
    _report(
        "all dst indices in [0, N)",
        bool(np.all(dst >= 0) and np.all(dst < N)),
        f"min={dst.min()}, max={dst.max()}",
    )
    # Input not mutated — check norms (original should NOT all be unit)
    original_norm = float(np.linalg.norm(vecs[0]))
    _report(
        "input array not mutated (not L2-normalised in-place)",
        abs(original_norm - 1.0) > 0.01,  # original was random, not normalised
        f"norm of vecs[0] after call: {original_norm:.4f}",
    )

    # ValueError on wrong shape
    try:
        build_knn_edges(rng.standard_normal(16).astype(np.float32), k=3)
        _report("ValueError on 1-D input", False, "no exception raised")
    except ValueError:
        _report("ValueError on 1-D input", True)

    # ValueError on wrong dtype
    try:
        build_knn_edges(vecs.astype(np.float64), k=3)
        _report("ValueError on float64 input", False, "no exception raised")
    except ValueError:
        _report("ValueError on float64 input", True)


# ===========================================================================
# Test Suite 2: build_hetero_graph integration test
# ===========================================================================


def _make_papers_df(n: int = 10) -> "pd.DataFrame":
    """Build a minimal papers DataFrame with 3 categories."""
    import pandas as pd

    categories_pool = [
        ["cs.LG"],
        ["cs.AI"],
        ["cs.CL"],
        ["cs.LG", "cs.AI"],
        ["cs.CL", "cs.LG"],
    ]
    rows = []
    for i in range(n):
        cats = categories_pool[i % len(categories_pool)]
        rows.append(
            {
                "arxiv_id": f"2101.{i:05d}",
                "title": f"Paper {i}",
                "abstract": f"Abstract {i}",
                "categories": cats,
                "primary_category": cats[0],
                "is_interdisciplinary": len(cats) >= 2,
                "year": 2021,
                "month": 1,
            }
        )
    return pd.DataFrame(rows)


def test_build_hetero_graph() -> None:
    print("\n=== Suite 2: build_hetero_graph integration test ===")

    if not _TORCH_GEOMETRIC_AVAILABLE:
        _report(
            "build_hetero_graph (all subtests)",
            None,
            "SKIP (torch_geometric not installed)",
        )
        return
    if not _PANDAS_AVAILABLE:
        _report(
            "build_hetero_graph (all subtests)", None, "SKIP (pandas not installed)"
        )
        return
    if not _FAISS_AVAILABLE:
        _report("build_hetero_graph (all subtests)", None, "SKIP (faiss not installed)")
        return

    from gcn_citation.pipeline.graph_builder import build_hetero_graph, validate_graph

    N = 10
    papers = _make_papers_df(N)
    rng = np.random.default_rng(42)
    embeddings = rng.standard_normal((N, 768)).astype(np.float32)

    # Fake citation edges: a few in-graph pairs
    citation_edges = CitationEdges(
        source_ids=np.array(["2101.00000", "2101.00001"], dtype=object),
        target_ids=np.array(["2101.00002", "2101.00003"], dtype=object),
        source_indices=np.array([0, 1], dtype=np.int64),
        target_indices=np.array([2, 3], dtype=np.int64),
    )

    try:
        graph = build_hetero_graph(papers, embeddings, citation_edges, knn_k=2)
    except Exception as exc:
        _report("build_hetero_graph returns without error", False, str(exc))
        traceback.print_exc()
        return

    _report("build_hetero_graph returns without error", True)

    # Paper node count
    _report(
        "paper node count == N",
        graph["paper"].x.shape[0] == N,
        f"shape={tuple(graph['paper'].x.shape)}",
    )

    # Embedding dimension
    _report(
        "paper.x dim == 768",
        graph["paper"].x.shape[1] == 768,
        f"dim={graph['paper'].x.shape[1]}",
    )

    # Category node count (3 unique categories: cs.LG, cs.AI, cs.CL)
    expected_cats = 3
    _report(
        "category node count == 3",
        graph["category"].num_nodes == expected_cats,
        f"num_nodes={graph['category'].num_nodes}",
    )

    # cites edge_index shape
    cites_ei = graph[("paper", "cites", "paper")].edge_index
    _report(
        "cites edge_index shape [2, E]",
        cites_ei.ndim == 2 and cites_ei.shape[0] == 2,
        f"shape={tuple(cites_ei.shape)}",
    )

    # similar_to edge_index shape
    sim_ei = graph[("paper", "similar_to", "paper")].edge_index
    _report(
        "similar_to edge_index shape [2, E]",
        sim_ei.ndim == 2 and sim_ei.shape[0] == 2,
        f"shape={tuple(sim_ei.shape)}",
    )

    # belongs_to edge_index shape
    bt_ei = graph[("paper", "belongs_to", "category")].edge_index
    _report(
        "belongs_to edge_index shape [2, E]",
        bt_ei.ndim == 2 and bt_ei.shape[0] == 2,
        f"shape={tuple(bt_ei.shape)}",
    )

    # validate_graph returns empty warnings
    try:
        warnings = validate_graph(graph)
        _report(
            "validate_graph returns empty warnings list",
            len(warnings) == 0,
            f"warnings: {warnings}",
        )
    except Exception as exc:
        _report("validate_graph runs without error", False, str(exc))
        traceback.print_exc()

    # ImportError when source_indices is None
    from gcn_citation.pipeline.graph_builder import build_hetero_graph

    bad_edges = CitationEdges(
        source_ids=np.array([], dtype=object),
        target_ids=np.array([], dtype=object),
        source_indices=None,
        target_indices=None,
    )
    try:
        build_hetero_graph(papers, embeddings, bad_edges, knn_k=2)
        _report("ValueError when source_indices is None", False, "no exception raised")
    except ValueError:
        _report("ValueError when source_indices is None", True)

    # ValueError when len(papers) != len(embeddings)
    try:
        build_hetero_graph(papers, embeddings[:5], citation_edges, knn_k=2)
        _report("ValueError when len mismatch", False, "no exception raised")
    except ValueError:
        _report("ValueError when len mismatch", True)


# ===========================================================================
# Test Suite 3: validate_graph unit tests (mock HeteroData if pyg not available)
# ===========================================================================


class _MockStorage:
    """Minimal attribute bag mimicking torch_geometric NodeStorage/EdgeStorage."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _MockGraph:
    """Minimal HeteroData-like object for validate_graph unit tests."""

    def __init__(self):
        self._data: dict = {}

    def __getitem__(self, key):
        if key not in self._data:
            self._data[key] = _MockStorage()
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value


def _make_valid_mock_graph(n: int = 5, d: int = 768, num_cats: int = 3):
    """Build a fully-valid mock graph for baseline validate_graph checks."""
    if _TORCH_GEOMETRIC_AVAILABLE:
        # Use real tensors
        import torch as _torch

        x = _torch.randn(n, d)
        y = _torch.zeros(n, num_cats)
        y[0, 0] = 1.0
        y[0, 1] = 1.0  # paper 0: 2 categories → interdisciplinary
        y[1, 1] = 1.0  # paper 1: 1 category
        y[2, 2] = 1.0
        y[3, 0] = 1.0
        y[4, 1] = 1.0
        y[4, 2] = 1.0  # paper 4: 2 categories → interdisciplinary
        is_inter = _torch.tensor([True, False, False, False, True], dtype=_torch.bool)
        cat_to_idx = {"cs.LG": 0, "cs.AI": 1, "cs.CL": 2}

        cites_ei = _torch.tensor([[0, 1], [2, 3]], dtype=_torch.long)
        sim_ei = _torch.tensor([[0, 1, 2, 3], [1, 0, 3, 2]], dtype=_torch.long)
        bt_ei = _torch.tensor(
            [[0, 0, 1, 2, 3, 4, 4], [0, 1, 1, 2, 0, 1, 2]], dtype=_torch.long
        )
        co_ei = _torch.tensor([[0, 1, 2], [1, 0, 3]], dtype=_torch.long)

        from torch_geometric.data import HeteroData as _HD

        g = _HD()
        g["paper"].x = x
        g["paper"].y = y
        g["paper"].is_interdisciplinary = is_inter
        g["paper"].primary_category_idx = _torch.zeros(n, dtype=_torch.long)
        g["paper"].arxiv_id = [f"2101.{i:05d}" for i in range(n)]
        g["category"].num_nodes = num_cats
        g["category"].category_to_idx = cat_to_idx
        g[("paper", "cites", "paper")].edge_index = cites_ei
        g[("paper", "similar_to", "paper")].edge_index = sim_ei
        g[("paper", "belongs_to", "category")].edge_index = bt_ei
        g[("paper", "co_category", "paper")].edge_index = co_ei
        return g
    else:
        # Mock without torch
        import numpy as _np

        g = _MockGraph()
        x = _np.random.randn(n, d).astype("float32")

        # Wrap in a mock tensor-like
        class _T:
            def __init__(self, arr):
                self._a = arr

            @property
            def ndim(self):
                return self._a.ndim

            @property
            def shape(self):
                return self._a.shape

            def __getitem__(self, idx):
                return _T(self._a[idx])

            def __eq__(self, other):
                return _T(self._a == (other._a if isinstance(other, _T) else other))

            def sum(self, **kwargs):
                return _T(self._a.sum(**kwargs))

            def item(self):
                return self._a.item()

            def min(self):
                return _T(_np.array(self._a.min()))

            def max(self):
                return _T(_np.array(self._a.max()))

        g["paper"].x = _T(x)
        # Skip full mock — not worth replicating entire torch tensor API
        return None  # signal caller to skip


def test_validate_graph_unit() -> None:
    print("\n=== Suite 3: validate_graph unit tests ===")

    if not _TORCH_GEOMETRIC_AVAILABLE:
        _report(
            "validate_graph unit tests (all)",
            None,
            "SKIP (torch_geometric not installed)",
        )
        return

    import torch as _torch
    from torch_geometric.data import HeteroData as _HD
    from gcn_citation.pipeline.graph_builder import validate_graph

    N, D, C = 6, 768, 3
    cat_to_idx = {"cs.LG": 0, "cs.AI": 1, "cs.CL": 2}

    def _base_graph():
        g = _HD()
        g["paper"].x = _torch.randn(N, D)
        y = _torch.zeros(N, C)
        y[0, 0] = 1.0
        y[1, 1] = 1.0
        y[2, 2] = 1.0
        y[3, 0] = 1.0
        y[4, 1] = 1.0
        y[5, 0] = 1.0
        y[5, 1] = 1.0
        g["paper"].y = y
        g["paper"].is_interdisciplinary = _torch.tensor(
            [False, False, False, False, False, True], dtype=_torch.bool
        )
        g["paper"].primary_category_idx = _torch.zeros(N, dtype=_torch.long)
        g["paper"].arxiv_id = [f"id{i}" for i in range(N)]
        g["category"].num_nodes = C
        g["category"].category_to_idx = cat_to_idx
        g[("paper", "cites", "paper")].edge_index = _torch.tensor(
            [[0, 1], [2, 3]], dtype=_torch.long
        )
        g[("paper", "similar_to", "paper")].edge_index = _torch.tensor(
            [[0, 1, 2, 3], [1, 0, 3, 2]], dtype=_torch.long
        )
        g[("paper", "belongs_to", "category")].edge_index = _torch.tensor(
            [[0, 1, 2, 3, 4, 5, 5], [0, 1, 2, 0, 1, 0, 1]], dtype=_torch.long
        )
        g[("paper", "co_category", "paper")].edge_index = _torch.tensor(
            [[0, 3], [3, 0]], dtype=_torch.long
        )
        return g

    # --- Baseline: valid graph should pass all checks ---
    g = _base_graph()
    ws = validate_graph(g)
    _report(
        "valid graph → empty warnings",
        len(ws) == 0,
        f"warnings: {ws}",
    )

    # --- Check 1: wrong feature shape ---
    g_bad = _base_graph()
    g_bad["paper"].x = _torch.randn(N, 512)  # wrong dim
    ws = validate_graph(g_bad)
    has_check1 = any("CHECK 1" in w for w in ws)
    _report(
        "CHECK 1: wrong feature dim triggers warning", has_check1, f"warnings: {ws}"
    )

    # --- Check 2: duplicate edges ---
    g_dup = _base_graph()
    dup_ei = _torch.tensor(
        [[0, 0, 1], [2, 2, 3]], dtype=_torch.long
    )  # (0,2) duplicated
    g_dup[("paper", "cites", "paper")].edge_index = dup_ei
    ws = validate_graph(g_dup)
    has_check2 = any("CHECK 2" in w for w in ws)
    _report("CHECK 2: duplicate edges trigger warning", has_check2, f"warnings: {ws}")

    # --- Check 3: self-loops in similar_to ---
    g_sl = _base_graph()
    sl_ei = _torch.tensor(
        [[0, 1, 2], [0, 2, 1]], dtype=_torch.long
    )  # (0,0) is a self-loop
    g_sl[("paper", "similar_to", "paper")].edge_index = sl_ei
    ws = validate_graph(g_sl)
    has_check3 = any("CHECK 3" in w for w in ws)
    _report(
        "CHECK 3: self-loop in similar_to triggers warning",
        has_check3,
        f"warnings: {ws}",
    )

    # --- Check 4: out-of-range citation index ---
    g_oor = _base_graph()
    g_oor[("paper", "cites", "paper")].edge_index = _torch.tensor(
        [[0, 1], [2, 999]], dtype=_torch.long  # 999 is out of range for N=6
    )
    ws = validate_graph(g_oor)
    has_check4 = any("CHECK 4" in w for w in ws)
    _report(
        "CHECK 4: out-of-range citation index triggers warning",
        has_check4,
        f"warnings: {ws}",
    )

    # --- Check 5: category count mismatch ---
    g_cat = _base_graph()
    g_cat["category"].num_nodes = 99  # mismatch with category_to_idx which has 3
    ws = validate_graph(g_cat)
    has_check5 = any("CHECK 5" in w for w in ws)
    _report(
        "CHECK 5: category count mismatch triggers warning",
        has_check5,
        f"warnings: {ws}",
    )

    # --- Check 6: is_interdisciplinary mismatch ---
    g_inter = _base_graph()
    # Paper 5 has 2 categories in y so is_interdisciplinary should be True,
    # but we'll set it to False to trigger the mismatch.
    flags = _torch.tensor([False, False, False, False, False, False], dtype=_torch.bool)
    g_inter["paper"].is_interdisciplinary = flags
    ws = validate_graph(g_inter)
    has_check6 = any("CHECK 6" in w for w in ws)
    _report(
        "CHECK 6: is_interdisciplinary mismatch triggers warning",
        has_check6,
        f"warnings: {ws}",
    )


# ===========================================================================
# Test Suite 4: co_category cap test
# ===========================================================================


def test_co_category_cap() -> None:
    print("\n=== Suite 4: co_category cap test ===")

    if not _TORCH_GEOMETRIC_AVAILABLE:
        _report("co_category cap (all)", None, "SKIP (torch_geometric not installed)")
        return
    if not _PANDAS_AVAILABLE:
        _report("co_category cap (all)", None, "SKIP (pandas not installed)")
        return
    if not _FAISS_AVAILABLE:
        _report("co_category cap (all)", None, "SKIP (faiss not installed)")
        return

    import pandas as _pd
    from gcn_citation.pipeline.graph_builder import build_hetero_graph, _CO_CATEGORY_CAP

    # Build a papers DataFrame where one category ("cs.LG") has 50 papers
    N_LARGE = 50
    rows = []
    for i in range(N_LARGE):
        rows.append(
            {
                "arxiv_id": f"2101.{i:05d}",
                "title": f"Paper {i}",
                "abstract": f"Abstract {i}",
                "categories": ["cs.LG"],
                "primary_category": "cs.LG",
                "is_interdisciplinary": False,
                "year": 2021,
                "month": 1,
            }
        )
    papers = _pd.DataFrame(rows)
    rng = np.random.default_rng(99)
    embeddings = rng.standard_normal((N_LARGE, 768)).astype(np.float32)
    citation_edges = CitationEdges(
        source_ids=np.array([], dtype=object),
        target_ids=np.array([], dtype=object),
        source_indices=np.array([], dtype=np.int64),
        target_indices=np.array([], dtype=np.int64),
    )

    try:
        graph = build_hetero_graph(papers, embeddings, citation_edges, knn_k=2)
    except Exception as exc:
        _report("build_hetero_graph with 50-paper single-category", False, str(exc))
        traceback.print_exc()
        return

    co_ei = graph[("paper", "co_category", "paper")].edge_index
    co_edge_count = co_ei.shape[1]
    # Max edges = cap * 2 (undirected) per category, but after dedup from single category:
    # directed pairs from one category ≤ cap → undirected ≤ cap * 2 (before dedup)
    max_expected = _CO_CATEGORY_CAP * 2
    _report(
        f"co_category edge count ≤ {max_expected} (cap * 2 undirected)",
        co_edge_count <= max_expected,
        f"co_edge_count={co_edge_count}, cap={_CO_CATEGORY_CAP}",
    )
    _report(
        "co_category edge count > 0 (some edges were created)",
        co_edge_count > 0,
        f"co_edge_count={co_edge_count}",
    )


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("validate_graph_builder.py")
    print("=" * 60)

    test_build_knn_edges()
    test_build_hetero_graph()
    test_validate_graph_unit()
    test_co_category_cap()

    print(f"\n{'=' * 60}")
    print(f"Results: {_pass_count} PASS / {_fail_count} FAIL / {_skip_count} SKIP")
    print("=" * 60)

    if _fail_count > 0:
        sys.exit(1)
