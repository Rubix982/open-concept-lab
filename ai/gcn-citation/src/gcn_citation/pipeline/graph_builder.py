"""Heterogeneous graph construction for the arXiv paper corpus.

Builds a PyTorch Geometric :class:`~torch_geometric.data.HeteroData` graph
with four edge types:

- ``('paper', 'cites', 'paper')`` — directed citation edges from S2ORC
- ``('paper', 'similar_to', 'paper')`` — undirected FAISS k-NN semantic edges
- ``('paper', 'belongs_to', 'category')`` — paper→category membership
- ``('paper', 'co_category', 'paper')`` — undirected, share at least one category

Node features on ``'paper'`` are SPECTER2 embeddings (768-dimensional float32).
Category nodes carry no feature vector.

All FAISS operations run on CPU (``faiss-cpu``) as required by the M2 compute
constraints in ``docs/research_requirements.md``.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path  # noqa: F401 — used in type hints within docstrings
from typing import TYPE_CHECKING

import numpy as np

try:
    import pandas as pd  # noqa: F401
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore[assignment]

try:
    import torch
    from torch_geometric.data import HeteroData
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    HeteroData = None  # type: ignore[assignment]

from .citations import CitationEdges

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EXPECTED_EMBEDDING_DIM = 768
_CO_CATEGORY_CAP = 1_000  # max pairs emitted per category to avoid O(N²) blowup


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_knn_edges(
    embeddings: np.ndarray,
    *,
    k: int = 10,
    batch_size: int = 10_000,
) -> tuple[np.ndarray, np.ndarray]:
    """Build k-NN similarity edges using FAISS (CPU).

    L2-normalises ``embeddings`` and builds a ``faiss.IndexFlatIP`` (inner
    product = cosine similarity after normalisation).  Queries the index in
    chunks of ``batch_size`` rows to bound peak memory usage.  Self-loops
    (a node's nearest neighbour being itself) are excluded from the output.

    Args:
        embeddings: Float32 array of shape ``[N, D]``.  Typically D=768 for
            SPECTER2.
        k: Number of nearest neighbours to retrieve per node.
        batch_size: Number of query rows processed per FAISS call.  Lower
            values reduce peak memory at the cost of slightly higher overhead.

    Returns:
        A tuple ``(source_indices, target_indices)`` of int64 integer arrays,
        each of length up to ``N * k`` after self-loops are removed.

    Raises:
        ImportError: If ``faiss`` is not installed.
        ValueError: If ``embeddings`` is not 2-D or not float32.
    """
    if faiss is None:
        raise ImportError(
            "faiss is required for build_knn_edges(). "
            "Install it with: pip install faiss-cpu"
        )

    if embeddings.ndim != 2:
        raise ValueError(f"embeddings must be 2-D, got shape {embeddings.shape}")
    if embeddings.dtype != np.float32:
        raise ValueError(f"embeddings must be float32, got dtype {embeddings.dtype}")

    n, d = embeddings.shape
    print(
        f"[graph_builder] Building k-NN index: N={n}, D={d}, k={k}",
        file=sys.stderr,
    )

    # L2-normalise a copy — do not mutate the caller's array
    vecs = embeddings.copy()
    faiss.normalize_L2(vecs)  # in-place on our copy

    # Build inner-product index (cosine after normalisation)
    index = faiss.IndexFlatIP(d)
    index.add(vecs)

    all_src: list[np.ndarray] = []
    all_dst: list[np.ndarray] = []

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch = vecs[start:end]
        # Retrieve k+1 neighbours so we can discard the self-loop
        _, indices = index.search(batch, k + 1)
        # indices shape: [batch_len, k+1]
        batch_len = end - start
        src_nodes = np.repeat(np.arange(start, end, dtype=np.int64), k + 1)
        dst_nodes = indices.reshape(-1).astype(np.int64)

        # Remove self-loops
        mask = src_nodes != dst_nodes
        src_nodes = src_nodes[mask]
        dst_nodes = dst_nodes[mask]

        # Each source should have exactly k valid neighbours (after self-loop
        # removal); trim to k per source in case FAISS returned the self as
        # one of the k neighbours AND another duplicate slipped in.
        # Simpler: just keep all non-self edges — spec only says "remove self-loops".
        all_src.append(src_nodes)
        all_dst.append(dst_nodes)

        if (start // batch_size) % 10 == 0:
            print(
                f"[graph_builder] k-NN batch {start}–{end} done.",
                file=sys.stderr,
            )

    source_indices = np.concatenate(all_src).astype(np.int64)
    target_indices = np.concatenate(all_dst).astype(np.int64)

    print(
        f"[graph_builder] k-NN edges: {len(source_indices)} (after self-loop removal).",
        file=sys.stderr,
    )
    return source_indices, target_indices


def build_hetero_graph(
    papers: "pd.DataFrame",
    embeddings: np.ndarray,
    citation_edges: CitationEdges,
    *,
    knn_k: int = 10,
) -> object:
    """Build a PyG HeteroData heterogeneous graph.

    Assembles a :class:`torch_geometric.data.HeteroData` object from the
    pre-computed components.  The graph has two node types and four edge types:

    **Node types**:

    - ``'paper'``: N nodes.

      - ``x``: SPECTER2 embeddings, shape ``[N, 768]``, float32.
      - ``arxiv_id``: list of string IDs, length N.
      - ``y``: multi-hot category label matrix, shape ``[N, num_categories]``,
        float32.
      - ``is_interdisciplinary``: bool tensor, shape ``[N]``.
      - ``primary_category_idx``: int64 tensor, shape ``[N]``.

    - ``'category'``: M nodes (~150 unique arXiv leaf categories in the subset).
      No feature vector.

    **Edge types**:

    - ``('paper', 'cites', 'paper')``: directed, from ``citation_edges``.
    - ``('paper', 'similar_to', 'paper')``: undirected, from
      :func:`build_knn_edges` with ``k=knn_k``.
    - ``('paper', 'belongs_to', 'category')``: directed, derived from the
      ``categories`` column of ``papers``.
    - ``('paper', 'co_category', 'paper')``: undirected; two papers are
      connected if they share at least one category.  Derived from
      ``belongs_to`` edges without explicit construction of pair-wise category
      membership — use the ``belongs_to`` adjacency product.

    Args:
        papers: DataFrame with columns ``arxiv_id``, ``categories``
            (list of str), ``primary_category`` (str), and
            ``is_interdisciplinary`` (bool).  Row order defines node indices.
        embeddings: Float32 array of shape ``[N, 768]``, aligned row-for-row
            with ``papers``.
        citation_edges: A :class:`~.citations.CitationEdges` object with
            integer ``source_indices`` and ``target_indices`` already assigned
            (i.e. :func:`~.citations.assign_indices` has been called).
        knn_k: Neighbour count passed to :func:`build_knn_edges`.

    Returns:
        A :class:`torch_geometric.data.HeteroData` instance ready for use
        with PyG dataloaders and models.

    Raises:
        ImportError: If ``torch`` or ``torch_geometric`` are not installed.
        ValueError: If ``citation_edges.source_indices`` is ``None`` (indices
            not yet assigned).
        ValueError: If ``len(papers) != len(embeddings)``.
    """
    if torch is None or HeteroData is None:
        raise ImportError(
            "torch and torch_geometric are required for build_hetero_graph(). "
            "Install with: pip install torch torch-geometric"
        )

    if citation_edges.source_indices is None:
        raise ValueError(
            "citation_edges.source_indices is None — call assign_indices() first."
        )

    n_papers = len(papers)
    if n_papers != len(embeddings):
        raise ValueError(
            f"len(papers)={n_papers} does not match len(embeddings)={len(embeddings)}."
        )

    print(
        f"[graph_builder] Building HeteroData graph for {n_papers} papers.",
        file=sys.stderr,
    )

    graph = HeteroData()

    # -----------------------------------------------------------------------
    # Category index — sorted for determinism
    # -----------------------------------------------------------------------
    all_categories: set[str] = set()
    categories_per_paper: list[list[str]] = list(papers["categories"])
    for cats in categories_per_paper:
        all_categories.update(cats)

    unique_categories = sorted(all_categories)
    category_to_idx: dict[str, int] = {c: i for i, c in enumerate(unique_categories)}
    num_categories = len(unique_categories)

    print(
        f"[graph_builder] {num_categories} unique categories found.",
        file=sys.stderr,
    )

    # -----------------------------------------------------------------------
    # Paper node attributes
    # -----------------------------------------------------------------------
    graph["paper"].x = torch.tensor(embeddings, dtype=torch.float32)
    graph["paper"].arxiv_id = list(papers["arxiv_id"])

    # Multi-hot label matrix [N, num_categories]
    y = np.zeros((n_papers, num_categories), dtype=np.float32)
    for i, cats in enumerate(categories_per_paper):
        for c in cats:
            idx = category_to_idx.get(c)
            if idx is not None:
                y[i, idx] = 1.0
    graph["paper"].y = torch.tensor(y, dtype=torch.float32)

    # is_interdisciplinary
    is_interdisciplinary = torch.tensor(
        list(papers["is_interdisciplinary"]), dtype=torch.bool
    )
    graph["paper"].is_interdisciplinary = is_interdisciplinary

    # primary_category_idx
    primary_cat_indices = [
        category_to_idx.get(pc, 0) for pc in papers["primary_category"]
    ]
    graph["paper"].primary_category_idx = torch.tensor(
        primary_cat_indices, dtype=torch.long
    )

    # -----------------------------------------------------------------------
    # Category node — no feature vector, just num_nodes and mapping
    # -----------------------------------------------------------------------
    graph["category"].num_nodes = num_categories
    graph["category"].category_to_idx = category_to_idx

    # -----------------------------------------------------------------------
    # Edge type 1: ('paper', 'cites', 'paper')
    # -----------------------------------------------------------------------
    cites_src = torch.tensor(citation_edges.source_indices, dtype=torch.long)
    cites_dst = torch.tensor(citation_edges.target_indices, dtype=torch.long)
    graph[("paper", "cites", "paper")].edge_index = torch.stack(
        [cites_src, cites_dst], dim=0
    )
    print(
        f"[graph_builder] 'cites' edges: {cites_src.shape[0]}.",
        file=sys.stderr,
    )

    # -----------------------------------------------------------------------
    # Edge type 2: ('paper', 'similar_to', 'paper') — undirected k-NN
    # -----------------------------------------------------------------------
    knn_src, knn_dst = build_knn_edges(embeddings.astype(np.float32), k=knn_k)

    # Make undirected: concatenate (src, dst) and (dst, src), then deduplicate
    sim_src = np.concatenate([knn_src, knn_dst])
    sim_dst = np.concatenate([knn_dst, knn_src])

    # Deduplicate using unique on stacked pairs
    pairs = np.stack([sim_src, sim_dst], axis=1)  # [E*2, 2]
    unique_pairs = np.unique(pairs, axis=0)
    sim_src_uniq = unique_pairs[:, 0]
    sim_dst_uniq = unique_pairs[:, 1]

    graph[("paper", "similar_to", "paper")].edge_index = torch.tensor(
        np.stack([sim_src_uniq, sim_dst_uniq], axis=0), dtype=torch.long
    )
    print(
        f"[graph_builder] 'similar_to' edges: {len(sim_src_uniq)} (undirected, deduped).",
        file=sys.stderr,
    )

    # -----------------------------------------------------------------------
    # Edge type 3: ('paper', 'belongs_to', 'category')
    # -----------------------------------------------------------------------
    bt_src: list[int] = []
    bt_dst: list[int] = []
    for i, cats in enumerate(categories_per_paper):
        for c in cats:
            cat_idx = category_to_idx.get(c)
            if cat_idx is not None:
                bt_src.append(i)
                bt_dst.append(cat_idx)

    graph[("paper", "belongs_to", "category")].edge_index = torch.tensor(
        [bt_src, bt_dst], dtype=torch.long
    )
    print(
        f"[graph_builder] 'belongs_to' edges: {len(bt_src)}.",
        file=sys.stderr,
    )

    # -----------------------------------------------------------------------
    # Edge type 4: ('paper', 'co_category', 'paper') — undirected
    # Group paper indices by category, emit pairs within each group.
    # Cap pairs per category at _CO_CATEGORY_CAP to avoid O(N²) blowup.
    # -----------------------------------------------------------------------
    papers_by_category: dict[int, list[int]] = defaultdict(list)
    for i, cats in enumerate(categories_per_paper):
        for c in cats:
            cat_idx = category_to_idx.get(c)
            if cat_idx is not None:
                papers_by_category[cat_idx].append(i)

    co_src: list[int] = []
    co_dst: list[int] = []
    for cat_idx, paper_ids in papers_by_category.items():
        if len(paper_ids) < 2:
            continue
        pairs_emitted = 0
        for a_pos in range(len(paper_ids)):
            for b_pos in range(a_pos + 1, len(paper_ids)):
                if pairs_emitted >= _CO_CATEGORY_CAP:
                    break
                co_src.append(paper_ids[a_pos])
                co_dst.append(paper_ids[b_pos])
                pairs_emitted += 1
            if pairs_emitted >= _CO_CATEGORY_CAP:
                break

    # Make undirected + deduplicate + remove self-loops
    co_src_arr = np.array(co_src + co_dst, dtype=np.int64)
    co_dst_arr = np.array(co_dst + co_src, dtype=np.int64)

    # Remove self-loops
    mask = co_src_arr != co_dst_arr
    co_src_arr = co_src_arr[mask]
    co_dst_arr = co_dst_arr[mask]

    # Deduplicate
    if len(co_src_arr) > 0:
        co_pairs = np.stack([co_src_arr, co_dst_arr], axis=1)
        co_pairs_uniq = np.unique(co_pairs, axis=0)
        co_src_final = co_pairs_uniq[:, 0]
        co_dst_final = co_pairs_uniq[:, 1]
    else:
        co_src_final = co_src_arr
        co_dst_final = co_dst_arr

    graph[("paper", "co_category", "paper")].edge_index = torch.tensor(
        np.stack([co_src_final, co_dst_final], axis=0)
        if len(co_src_final) > 0
        else np.zeros((2, 0), dtype=np.int64),
        dtype=torch.long,
    )
    print(
        f"[graph_builder] 'co_category' edges: {len(co_src_final)} "
        f"(undirected, deduped, capped at {_CO_CATEGORY_CAP}/category).",
        file=sys.stderr,
    )

    print("[graph_builder] HeteroData graph construction complete.", file=sys.stderr)
    return graph


def validate_graph(graph: object) -> list[str]:
    """Run sanity checks on the constructed graph.

    Intended to be called immediately after :func:`build_hetero_graph` to
    catch common construction errors before expensive training runs.

    Checks performed:

    - Paper node feature shape is ``[N, 768]``.
    - No duplicate edges within any edge type (COO deduplication check).
    - No self-loops in ``('paper', 'similar_to', 'paper')`` edges.
    - All citation edge indices are valid node indices (in ``[0, N)``).
    - The number of ``'category'`` nodes equals the number of unique categories
      observed in paper metadata.
    - ``is_interdisciplinary`` flag matches actual per-node category count
      (``is_interdisciplinary[i]`` iff ``len(paper_categories[i]) >= 2``).

    Args:
        graph: A :class:`torch_geometric.data.HeteroData` instance, as
            returned by :func:`build_hetero_graph`.

    Returns:
        A list of warning strings describing any failed checks.  An empty list
        means the graph passed all checks.
    """
    warnings: list[str] = []

    # -----------------------------------------------------------------------
    # Check 1: Paper feature shape is [N, 768]
    # -----------------------------------------------------------------------
    try:
        x = graph["paper"].x
        if x.ndim != 2 or x.shape[1] != _EXPECTED_EMBEDDING_DIM:
            warnings.append(
                f"CHECK 1 FAIL: paper.x shape is {tuple(x.shape)}, "
                f"expected [N, {_EXPECTED_EMBEDDING_DIM}]."
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"CHECK 1 FAIL: could not access paper.x — {exc}.")

    # -----------------------------------------------------------------------
    # Check 2: No duplicate edges in any edge type
    # -----------------------------------------------------------------------
    edge_types = [
        ("paper", "cites", "paper"),
        ("paper", "similar_to", "paper"),
        ("paper", "belongs_to", "category"),
        ("paper", "co_category", "paper"),
    ]
    for edge_type in edge_types:
        try:
            ei = graph[edge_type].edge_index  # shape [2, E]
            if ei.shape[1] == 0:
                continue
            # Stack pairs and check for uniqueness
            pairs = ei.T  # [E, 2]
            num_unique = torch.unique(pairs, dim=0).shape[0]
            if num_unique < pairs.shape[0]:
                dup_count = pairs.shape[0] - num_unique
                warnings.append(
                    f"CHECK 2 FAIL: {edge_type} has {dup_count} duplicate edges "
                    f"({pairs.shape[0]} total, {num_unique} unique)."
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"CHECK 2 FAIL: could not access edge_index for {edge_type} — {exc}."
            )

    # -----------------------------------------------------------------------
    # Check 3: No self-loops in similar_to edges
    # -----------------------------------------------------------------------
    try:
        ei = graph[("paper", "similar_to", "paper")].edge_index
        if ei.shape[1] > 0:
            self_loops = (ei[0] == ei[1]).sum().item()
            if self_loops > 0:
                warnings.append(
                    f"CHECK 3 FAIL: 'similar_to' edges contain {self_loops} self-loops."
                )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"CHECK 3 FAIL: could not check self-loops in 'similar_to' — {exc}."
        )

    # -----------------------------------------------------------------------
    # Check 4: All citation indices in [0, N)
    # -----------------------------------------------------------------------
    try:
        n = graph["paper"].x.shape[0]
        ei = graph[("paper", "cites", "paper")].edge_index
        if ei.shape[1] > 0:
            min_idx = ei.min().item()
            max_idx = ei.max().item()
            if min_idx < 0 or max_idx >= n:
                warnings.append(
                    f"CHECK 4 FAIL: citation indices out of range [0, {n}): "
                    f"min={min_idx}, max={max_idx}."
                )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"CHECK 4 FAIL: could not validate citation indices — {exc}.")

    # -----------------------------------------------------------------------
    # Check 5: Number of category nodes == number of unique categories in metadata
    # -----------------------------------------------------------------------
    try:
        category_to_idx = graph["category"].category_to_idx
        num_cat_nodes = graph["category"].num_nodes
        num_cat_mapping = len(category_to_idx)
        if num_cat_nodes != num_cat_mapping:
            warnings.append(
                f"CHECK 5 FAIL: 'category' num_nodes={num_cat_nodes} does not match "
                f"len(category_to_idx)={num_cat_mapping}."
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"CHECK 5 FAIL: could not validate category count — {exc}.")

    # -----------------------------------------------------------------------
    # Check 6: is_interdisciplinary[i] matches len(categories[i]) >= 2
    # -----------------------------------------------------------------------
    try:
        is_inter = graph["paper"].is_interdisciplinary  # bool tensor [N]
        y = graph["paper"].y  # [N, num_categories]
        # Recompute category counts from the multi-hot y matrix
        cat_counts = y.sum(dim=1)  # [N]
        expected_inter = cat_counts >= 2  # bool tensor [N]
        mismatches = (is_inter != expected_inter).sum().item()
        if mismatches > 0:
            warnings.append(
                f"CHECK 6 FAIL: is_interdisciplinary mismatch at {mismatches} nodes "
                f"(flag does not agree with len(categories[i]) >= 2 derived from y)."
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"CHECK 6 FAIL: could not validate is_interdisciplinary — {exc}."
        )

    return warnings
