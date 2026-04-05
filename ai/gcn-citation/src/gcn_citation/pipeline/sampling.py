"""Mini-batch neighbor sampling for heterogeneous graph training.

Wraps PyTorch Geometric's :class:`~torch_geometric.loader.NeighborLoader`
to provide GraphSAGE-style 2-hop neighborhood sampling over the HeteroData
graph built by :mod:`.graph_builder`.

Training on M2 uses ``device("mps")`` with mini-batch sampling — full-batch
message passing is only feasible for Cora-scale sanity checks.

.. important:: **MPS constraint — num_workers must be 0**

   PyG's :class:`~torch_geometric.loader.NeighborLoader` spawns worker
   sub-processes when ``num_workers > 0``.  On macOS, those sub-processes
   cannot share the parent's MPS device context, causing a silent hang or
   immediate crash.  Both :func:`build_neighbor_sampler` and
   :func:`get_dataloaders` hard-default ``num_workers=0``.  Do not change
   this default when targeting an M2 (or any MPS) device.
"""

from __future__ import annotations

try:
    import torch  # noqa: F401
    from torch_geometric.data import HeteroData  # noqa: F401
    from torch_geometric.loader import NeighborLoader  # noqa: F401

    _TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    HeteroData = None  # type: ignore[assignment]
    NeighborLoader = None  # type: ignore[assignment]
    _TORCH_GEOMETRIC_AVAILABLE = False


def build_neighbor_sampler(
    graph: object,
    *,
    num_neighbors: list[int] = [10, 5],
    batch_size: int = 512,
    edge_types: list[str] | None = None,
    shuffle: bool = True,
    num_workers: int = 0,
) -> object:
    """Build a GraphSAGE-style mini-batch neighbor sampler.

    Wraps :class:`torch_geometric.loader.NeighborLoader` configured for
    2-hop neighborhood sampling over ``'paper'`` nodes.  The ``num_neighbors``
    fanout list controls how many neighbors are sampled per hop: index 0 is
    the immediate (1-hop) neighborhood, index 1 is the 2-hop neighborhood.

    .. warning:: **num_workers must be 0 on MPS (macOS M-series)**

        ``num_workers`` defaults to 0 and should not be increased when
        running on an M2 (or any Apple Silicon) device.  Worker sub-processes
        spawned by the DataLoader cannot share the parent's MPS context,
        which causes a silent hang or crash.

    Args:
        graph: A :class:`torch_geometric.data.HeteroData` instance as returned
            by :func:`.graph_builder.build_hetero_graph`.
        num_neighbors: Fanout per message-passing hop.  A list of length L
            produces an L-hop sampler.  Defaults to ``[10, 5]`` (2-hop,
            10 neighbors at hop 1, 5 at hop 2) as recommended by
            ``docs/research_requirements.md``.
        batch_size: Number of seed nodes per mini-batch.
        edge_types: Which edge types to sample over.  When ``None``, all edge
            types present in ``graph`` are used.  Pass a list such as
            ``["cites", "similar_to"]`` to restrict sampling to specific
            relation types.  Note: strings here should match the ``rel`` part
            of the ``(src_type, rel, dst_type)`` triplet stored in
            ``graph.edge_types``.
        shuffle: Whether to shuffle the seed nodes each epoch.  Defaults to
            ``True``; set to ``False`` for validation and test loaders.
        num_workers: Number of DataLoader worker processes.  **Must be 0 on
            MPS** — see the module-level warning.  Defaults to 0.

    Returns:
        A configured :class:`torch_geometric.loader.NeighborLoader` instance.
        Call it like a standard PyTorch DataLoader (``for batch in sampler``).

    Raises:
        ImportError: If ``torch`` or ``torch_geometric`` are not installed.
        ValueError: If ``graph`` has no ``'paper'`` node type.
    """
    if not _TORCH_GEOMETRIC_AVAILABLE:
        raise ImportError(
            "torch and torch_geometric are required for build_neighbor_sampler. "
            "Install them with: pip install torch torch_geometric"
        )

    if "paper" not in graph.node_types:
        raise ValueError(
            f"graph must contain a 'paper' node type, but found: {graph.node_types}"
        )

    # Build the num_neighbors dict mapping edge type triplets to the fanout list.
    if edge_types is not None:
        # Filter to edge types whose relation string (middle of triplet) is in edge_types.
        selected = [et for et in graph.edge_types if et[1] in edge_types]
        num_neighbors_dict = {et: num_neighbors for et in selected}
    else:
        num_neighbors_dict = {et: num_neighbors for et in graph.edge_types}

    return NeighborLoader(
        graph,
        num_neighbors=num_neighbors_dict,
        batch_size=batch_size,
        input_nodes=("paper", None),
        shuffle=shuffle,
        num_workers=num_workers,
    )


def get_dataloaders(
    graph: object,
    *,
    train_mask: "torch.Tensor",
    val_mask: "torch.Tensor",
    test_mask: "torch.Tensor",
    num_neighbors: list[int] = [10, 5],
    batch_size: int = 512,
    edge_types: list[str] | None = None,
) -> tuple[object, object, object]:
    """Build train, val, and test NeighborLoader instances from boolean masks.

    A convenience wrapper around :func:`build_neighbor_sampler` that constructs
    three loaders — one per split — each restricted to seed nodes identified by
    the corresponding boolean mask.  The train loader uses ``shuffle=True``; val
    and test loaders use ``shuffle=False``.  All three loaders use
    ``num_workers=0`` to satisfy the MPS constraint (see module warning).

    Args:
        graph: A :class:`torch_geometric.data.HeteroData` instance as returned
            by :func:`.graph_builder.build_hetero_graph`.
        train_mask: Boolean tensor of shape ``[N]`` marking training seed nodes.
        val_mask: Boolean tensor of shape ``[N]`` marking validation seed nodes.
        test_mask: Boolean tensor of shape ``[N]`` marking test seed nodes.
        num_neighbors: Fanout per message-passing hop, passed to
            :func:`build_neighbor_sampler`.  Defaults to ``[10, 5]``.
        batch_size: Number of seed nodes per mini-batch.
        edge_types: Relation strings to restrict sampling over.  ``None`` means
            use all edge types in ``graph``.

    Returns:
        A 3-tuple ``(train_loader, val_loader, test_loader)`` of
        :class:`torch_geometric.loader.NeighborLoader` instances.

    Raises:
        ImportError: If ``torch`` or ``torch_geometric`` are not installed.
        ValueError: If ``graph`` has no ``'paper'`` node type.
    """
    if not _TORCH_GEOMETRIC_AVAILABLE:
        raise ImportError(
            "torch and torch_geometric are required for get_dataloaders. "
            "Install them with: pip install torch torch_geometric"
        )

    if "paper" not in graph.node_types:
        raise ValueError(
            f"graph must contain a 'paper' node type, but found: {graph.node_types}"
        )

    # Build the num_neighbors dict (shared across all three loaders).
    if edge_types is not None:
        selected = [et for et in graph.edge_types if et[1] in edge_types]
        num_neighbors_dict = {et: num_neighbors for et in selected}
    else:
        num_neighbors_dict = {et: num_neighbors for et in graph.edge_types}

    train_loader = NeighborLoader(
        graph,
        num_neighbors=num_neighbors_dict,
        batch_size=batch_size,
        input_nodes=("paper", train_mask),
        shuffle=True,
        num_workers=0,
    )
    val_loader = NeighborLoader(
        graph,
        num_neighbors=num_neighbors_dict,
        batch_size=batch_size,
        input_nodes=("paper", val_mask),
        shuffle=False,
        num_workers=0,
    )
    test_loader = NeighborLoader(
        graph,
        num_neighbors=num_neighbors_dict,
        batch_size=batch_size,
        input_nodes=("paper", test_mask),
        shuffle=False,
        num_workers=0,
    )

    return train_loader, val_loader, test_loader
