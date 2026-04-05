"""Validation script for pipeline/sampling.py.

All tests run on CPU — no GPU required.

Run:
    python3 agents/engineer/workspace/validate_sampling.py
"""

from __future__ import annotations

import sys
import traceback

# ---------------------------------------------------------------------------
# Availability guards
# ---------------------------------------------------------------------------

try:
    import torch
    from torch_geometric.data import HeteroData
    from torch_geometric.loader import NeighborLoader

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

# The module under test — always importable (import guards inside)
sys.path.insert(0, "src")
from gcn_citation.pipeline.sampling import (
    build_neighbor_sampler,
    get_dataloaders,
)  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = "PASS"
_FAIL = "FAIL"
_SKIP = "SKIP"


def _result(label: str, outcome: str, detail: str = "") -> None:
    tag = f"[{outcome}]"
    msg = f"{tag} {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def _make_paper_graph(n: int = 10) -> "HeteroData":
    """Build a minimal HeteroData graph with n paper nodes and one edge type."""
    g = HeteroData()
    g["paper"].x = torch.randn(n, 8)  # 8-dim features (not 768 — small for tests)
    # Self-loop edges so every node has at least one neighbor
    src = torch.arange(n)
    dst = torch.arange(n)
    g["paper", "cites", "paper"].edge_index = torch.stack([src, dst], dim=0)
    return g


def _make_two_edge_graph(n: int = 10) -> "HeteroData":
    """Build a HeteroData with paper nodes and two edge types."""
    g = HeteroData()
    g["paper"].x = torch.randn(n, 8)
    src = torch.arange(n)
    dst = torch.arange(n)
    g["paper", "cites", "paper"].edge_index = torch.stack([src, dst], dim=0)
    g["paper", "similar_to", "paper"].edge_index = torch.stack([src, dst], dim=0)
    return g


# ---------------------------------------------------------------------------
# Test 1: ImportError guard when torch_geometric not installed
# ---------------------------------------------------------------------------


def test_import_guard() -> None:
    """If torch_geometric were absent, build_neighbor_sampler raises ImportError.

    We simulate this by temporarily monkeypatching the module flag and calling
    with a dummy graph object.
    """
    import gcn_citation.pipeline.sampling as _mod

    original = _mod._TORCH_GEOMETRIC_AVAILABLE
    try:
        _mod._TORCH_GEOMETRIC_AVAILABLE = False
        build_neighbor_sampler(object())
        _result("import_guard", _FAIL, "expected ImportError but none raised")
    except ImportError as exc:
        _result("import_guard", _PASS, f"ImportError: {exc}")
    except Exception as exc:
        _result("import_guard", _FAIL, f"unexpected exception: {exc}")
    finally:
        _mod._TORCH_GEOMETRIC_AVAILABLE = original


# ---------------------------------------------------------------------------
# Test 2: ValueError when graph has no 'paper' node type
# ---------------------------------------------------------------------------


def test_missing_paper_node() -> None:
    if not HAS_TORCH_GEOMETRIC:
        _result("missing_paper_node", _SKIP, "torch_geometric not available")
        return

    g = HeteroData()
    g["category"].x = torch.randn(5, 4)

    try:
        build_neighbor_sampler(g)
        _result("missing_paper_node", _FAIL, "expected ValueError but none raised")
    except ValueError as exc:
        _result("missing_paper_node", _PASS, f"ValueError: {exc}")
    except Exception as exc:
        _result("missing_paper_node", _FAIL, f"unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 3: Edge type filtering — only 'cites' type in num_neighbors dict
# ---------------------------------------------------------------------------


def test_edge_type_filtering() -> None:
    if not HAS_TORCH_GEOMETRIC:
        _result("edge_type_filtering", _SKIP, "torch_geometric not available")
        return

    g = _make_two_edge_graph(n=10)

    try:
        loader = build_neighbor_sampler(
            g, num_neighbors=[2, 1], batch_size=4, edge_types=["cites"], shuffle=False
        )
    except Exception as exc:
        _result("edge_type_filtering", _FAIL, f"unexpected error: {exc}")
        traceback.print_exc()
        return

    # PyG 2.7+: num_neighbors.values is a dict mapping "src__rel__dst" strings to fanouts.
    # Only edge types explicitly passed to NeighborLoader appear here.
    nn_values = loader.node_sampler.num_neighbors.values  # dict[str, list[int]]
    rel_names = [k.split("__")[1] for k in nn_values.keys()]

    if "similar_to" in rel_names:
        _result(
            "edge_type_filtering",
            _FAIL,
            f"'similar_to' should have been filtered out; got rel_names={rel_names}",
        )
    elif "cites" not in rel_names:
        _result(
            "edge_type_filtering",
            _FAIL,
            f"'cites' missing from num_neighbors dict; got rel_names={rel_names}",
        )
    else:
        _result(
            "edge_type_filtering",
            _PASS,
            f"num_neighbors dict contains only: {rel_names}",
        )


# ---------------------------------------------------------------------------
# Test 4: get_dataloaders split sizes and shuffle flags
# ---------------------------------------------------------------------------


def test_get_dataloaders_splits() -> None:
    if not HAS_TORCH_GEOMETRIC:
        _result("get_dataloaders_splits", _SKIP, "torch_geometric not available")
        return

    n = 20
    g = _make_paper_graph(n=n)

    # 12/4/4 split masks
    train_mask = torch.zeros(n, dtype=torch.bool)
    train_mask[:12] = True
    val_mask = torch.zeros(n, dtype=torch.bool)
    val_mask[12:16] = True
    test_mask = torch.zeros(n, dtype=torch.bool)
    test_mask[16:] = True

    try:
        train_loader, val_loader, test_loader = get_dataloaders(
            g,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask,
            num_neighbors=[2, 1],
            batch_size=4,
        )
    except Exception as exc:
        _result("get_dataloaders_splits", _FAIL, f"unexpected error: {exc}")
        traceback.print_exc()
        return

    errors = []

    # Verify shuffle flags — PyG 2.7+ stores this on loader.dataset (a ShuffledDataset)
    # or via the internal _DataLoaderIter. Safest check: use the sampler type.
    # A RandomSampler means shuffle=True; SequentialSampler means shuffle=False.
    from torch.utils.data import RandomSampler, SequentialSampler

    if not isinstance(train_loader.sampler, RandomSampler):
        errors.append("train_loader should use RandomSampler (shuffle=True)")
    if not isinstance(val_loader.sampler, SequentialSampler):
        errors.append("val_loader should use SequentialSampler (shuffle=False)")
    if not isinstance(test_loader.sampler, SequentialSampler):
        errors.append("test_loader should use SequentialSampler (shuffle=False)")

    # Verify seed node counts match mask sizes
    def _seed_count(loader: NeighborLoader) -> int:
        """Return the number of seed nodes in the loader."""
        # input_nodes is stored as ('paper', mask_or_indices)
        inp = loader.input_nodes
        if isinstance(inp, tuple):
            node_id = inp[1]
        else:
            node_id = inp
        if node_id is None:
            return -1  # all nodes
        if isinstance(node_id, torch.Tensor) and node_id.dtype == torch.bool:
            return int(node_id.sum().item())
        return len(node_id)

    train_count = _seed_count(train_loader)
    val_count = _seed_count(val_loader)
    test_count = _seed_count(test_loader)

    if train_count != 12:
        errors.append(f"train seed count expected 12, got {train_count}")
    if val_count != 4:
        errors.append(f"val seed count expected 4, got {val_count}")
    if test_count != 4:
        errors.append(f"test seed count expected 4, got {test_count}")

    if errors:
        _result("get_dataloaders_splits", _FAIL, "; ".join(errors))
    else:
        _result(
            "get_dataloaders_splits",
            _PASS,
            f"train={train_count} val={val_count} test={test_count}, shuffle flags correct",
        )


# ---------------------------------------------------------------------------
# Test 5: num_workers=0 default
# ---------------------------------------------------------------------------


def test_num_workers_default() -> None:
    if not HAS_TORCH_GEOMETRIC:
        _result("num_workers_default", _SKIP, "torch_geometric not available")
        return

    g = _make_paper_graph(n=10)
    try:
        loader = build_neighbor_sampler(
            g, num_neighbors=[2], batch_size=4, shuffle=False
        )
    except Exception as exc:
        _result("num_workers_default", _FAIL, f"unexpected error: {exc}")
        traceback.print_exc()
        return

    nw = loader.num_workers
    if nw == 0:
        _result("num_workers_default", _PASS, "num_workers=0 confirmed")
    else:
        _result("num_workers_default", _FAIL, f"expected num_workers=0, got {nw}")


# ---------------------------------------------------------------------------
# Test 6: Minimal iteration — one batch from train loader is HeteroData
# ---------------------------------------------------------------------------


def test_minimal_iteration() -> None:
    if not HAS_TORCH_GEOMETRIC:
        _result("minimal_iteration", _SKIP, "torch_geometric not available")
        return

    g = _make_paper_graph(n=10)
    try:
        loader = build_neighbor_sampler(
            g, num_neighbors=[2], batch_size=4, shuffle=False
        )
        batch = next(iter(loader))
    except ImportError as exc:
        # pyg-lib or torch-sparse required for actual sampling — optional C++ ext
        _result("minimal_iteration", _SKIP, f"optional C++ extension missing: {exc}")
        return
    except Exception as exc:
        _result("minimal_iteration", _FAIL, f"iteration failed: {exc}")
        traceback.print_exc()
        return

    if not isinstance(batch, HeteroData):
        _result(
            "minimal_iteration", _FAIL, f"expected HeteroData batch, got {type(batch)}"
        )
        return

    if "paper" not in batch.node_types:
        _result(
            "minimal_iteration",
            _FAIL,
            f"batch missing 'paper' node type; node_types={batch.node_types}",
        )
        return

    _result(
        "minimal_iteration",
        _PASS,
        f"batch is HeteroData with {batch['paper'].num_nodes} paper nodes",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"torch_geometric available: {HAS_TORCH_GEOMETRIC}")
    print()

    test_import_guard()
    test_missing_paper_node()
    test_edge_type_filtering()
    test_get_dataloaders_splits()
    test_num_workers_default()
    test_minimal_iteration()

    print()
    print("Done.")


if __name__ == "__main__":
    main()
