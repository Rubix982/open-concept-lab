"""End-to-end 10K integration test for the Phase 0 pipeline.

Ticket: E-012
Tests: data loading → citation fetching → graph building → validation →
       dataloaders → one batch → GT forward pass
"""

from __future__ import annotations

import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import traceback
from pathlib import Path

# NOTE: do NOT import faiss here — importing faiss before torch on macOS
# causes an OpenMP double-init hang. graph_builder.py auto-detects torch
# in sys.modules and uses sklearn NearestNeighbors instead.

import numpy as np
import pandas as pd
import torch

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, bool, str]] = []  # (label, passed, detail)


def record(label: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((label, passed, detail))
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# ---------------------------------------------------------------------------
# Step 1 — Load inputs
# ---------------------------------------------------------------------------

print("\n=== Step 1: Load inputs ===")

try:
    df = pd.read_parquet("data/pipeline/arxiv_10k.parquet")
    embeddings = np.load("data/pipeline/embeddings_10k.npy", mmap_mode="r")
    arxiv_ids = df["arxiv_id"].tolist()

    papers_ok = len(df) == 10_000
    emb_ok = embeddings.shape == (10_000, 768) and embeddings.dtype == np.float32
    record("Papers loaded", papers_ok, f"{len(df):,} rows")
    record("Embeddings shape", emb_ok, f"{embeddings.shape} {embeddings.dtype}")
except Exception as exc:
    record("Load inputs", False, str(exc))
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------------------------------------
# Step 2 — Fetch citation edges via OpenAlex API
# ---------------------------------------------------------------------------

print("\n=== Step 2: Citation edges (OpenAlex API) ===")

citation_edges = None
citation_edge_count = 0

try:
    from src.gcn_citation.pipeline.citations import (
        assign_indices,
        build_id_to_index,
        load_openalex_citations_api,
    )

    id_to_index = build_id_to_index(arxiv_ids)

    citation_edges = load_openalex_citations_api(
        arxiv_ids,
        requests_per_second=9.0,
        cache_path=Path("data/pipeline/citations_10k_cache.json"),
    )
    citation_edges = assign_indices(citation_edges, id_to_index)
    citation_edge_count = len(citation_edges.source_ids)
    record("Citation edges fetched", True, f"{citation_edge_count:,} edges")
except Exception as exc:
    record("Citation edges fetched", False, str(exc))
    traceback.print_exc()
    # Create empty citation edges so graph build can still proceed
    from src.gcn_citation.pipeline.citations import CitationEdges

    citation_edges = CitationEdges(
        source_ids=[],
        target_ids=[],
        source_indices=np.array([], dtype=np.int64),
        target_indices=np.array([], dtype=np.int64),
    )

# ---------------------------------------------------------------------------
# Step 3 — Build HeteroData graph
# ---------------------------------------------------------------------------

print("\n=== Step 3: Build HeteroData graph ===")

graph = None
knn_edge_count = 0
belongs_to_count = 0
co_category_count = 0

try:
    from src.gcn_citation.pipeline.graph_builder import (
        build_hetero_graph,
        validate_graph,
    )

    # embeddings must be a writable float32 array (copy the mmap)
    emb_array = np.array(embeddings, dtype=np.float32)

    # Pass smaller knn_k to reduce FAISS memory pressure on M2
    graph = build_hetero_graph(
        papers=df,
        embeddings=emb_array,
        citation_edges=citation_edges,
        knn_k=5,  # reduced from 10 to lower FAISS memory pressure
    )

    # Count edge types
    try:
        knn_edge_count = graph[("paper", "similar_to", "paper")].edge_index.shape[1]
    except Exception:
        knn_edge_count = 0
    try:
        belongs_to_count = graph[("paper", "belongs_to", "category")].edge_index.shape[
            1
        ]
    except Exception:
        belongs_to_count = 0
    try:
        co_category_count = graph[("paper", "co_category", "paper")].edge_index.shape[1]
    except Exception:
        co_category_count = 0

    record(
        "Graph built",
        True,
        f"citation={citation_edge_count:,}, knn={knn_edge_count:,}, belongs_to={belongs_to_count:,}, co_category={co_category_count:,}",
    )
except Exception as exc:
    record("Graph built", False, str(exc))
    traceback.print_exc()

# ---------------------------------------------------------------------------
# Step 4 — Validate graph
# ---------------------------------------------------------------------------

print("\n=== Step 4: Validate graph ===")

validation_warnings: list[str] = []
validation_passed = False

if graph is not None:
    try:
        from src.gcn_citation.pipeline.graph_builder import validate_graph

        validation_warnings = validate_graph(graph)
        validation_passed = len(validation_warnings) == 0
        if validation_warnings:
            print(f"  Graph validation warnings ({len(validation_warnings)}):")
            for w in validation_warnings:
                print(f"    - {w}")
        record(
            "Graph validation",
            validation_passed,
            f"PASS"
            if validation_passed
            else f"FAIL ({len(validation_warnings)} warnings)",
        )
    except Exception as exc:
        record("Graph validation", False, str(exc))
        traceback.print_exc()
else:
    record("Graph validation", False, "Graph not built — skipped")

# ---------------------------------------------------------------------------
# Step 5 — Build dataloaders
# ---------------------------------------------------------------------------

print("\n=== Step 5: Build dataloaders ===")

train_loader = val_loader = test_loader = None
n = 0
train_count = val_count = test_count = 0

if graph is not None:
    try:
        from src.gcn_citation.pipeline.sampling import get_dataloaders

        n = graph["paper"].x.shape[0]
        perm = torch.randperm(n)
        train_mask = torch.zeros(n, dtype=torch.bool)
        val_mask = torch.zeros(n, dtype=torch.bool)
        test_mask = torch.zeros(n, dtype=torch.bool)
        train_mask[perm[: int(0.7 * n)]] = True
        val_mask[perm[int(0.7 * n) : int(0.85 * n)]] = True
        test_mask[perm[int(0.85 * n) :]] = True

        train_count = train_mask.sum().item()
        val_count = val_mask.sum().item()
        test_count = test_mask.sum().item()

        train_loader, val_loader, test_loader = get_dataloaders(
            graph,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask,
            num_neighbors=[10, 5],
            batch_size=256,
        )
        record(
            "Dataloaders built",
            True,
            f"train={train_count:,} val={val_count:,} test={test_count:,}",
        )
    except Exception as exc:
        record("Dataloaders built", False, str(exc))
        traceback.print_exc()
else:
    record("Dataloaders built", False, "Graph not built — skipped")

# ---------------------------------------------------------------------------
# Step 6 — Verify one batch
# ---------------------------------------------------------------------------

print("\n=== Step 6: One batch ===")

batch_shape = None

if train_loader is not None:
    try:
        batch = next(iter(train_loader))
        has_x = hasattr(batch["paper"], "x")
        batch_shape = batch["paper"].x.shape if has_x else None
        record(
            "One batch",
            has_x,
            f"paper.x shape: {batch_shape}"
            if batch_shape
            else "missing paper features",
        )
    except Exception as exc:
        record("One batch", False, str(exc))
        traceback.print_exc()
else:
    record("One batch", False, "No train loader — skipped")

# ---------------------------------------------------------------------------
# Step 7 — GT forward pass
# ---------------------------------------------------------------------------

print("\n=== Step 7: GT forward pass ===")

gt_status = "SKIP"
gt_detail = ""
gt_passed = None  # None = skip, True = pass, False = fail

if graph is not None:
    try:
        from src.gcn_citation.models.gt_torch import (
            GraphTransformer,
            _build_attention_mask,
            _degree_features,
        )

        num_nodes = n if n > 0 else graph["paper"].x.shape[0]
        n = num_nodes

        # Build edges numpy array from cites edge type
        try:
            ei = graph[("paper", "cites", "paper")].edge_index  # [2, E]
            edges_np = torch.stack([ei[0], ei[1]], dim=1).numpy()
        except Exception:
            # Fall back to empty edges
            edges_np = np.zeros((0, 2), dtype=np.int64)

        # Warn if 10K nodes might OOM on attn_mask
        print(
            f"  [gt] Building attention mask for {num_nodes:,} nodes "
            f"({num_nodes**2 / 1e6:.1f}M booleans = {num_nodes**2 / 1e9:.2f} GB)",
            file=sys.stderr,
        )

        if num_nodes > 8_000:
            print(
                "  [gt] WARNING: N>8K — full-batch O(N²) attention mask may OOM. "
                "Attempting anyway; will catch MemoryError.",
                file=sys.stderr,
            )

        degree_feats = torch.tensor(
            _degree_features(num_nodes, edges_np), dtype=torch.float32
        )
        attn_mask = torch.tensor(
            _build_attention_mask(num_nodes, edges_np), dtype=torch.bool
        )

        num_classes = int(graph["paper"].y.shape[1])
        features = graph["paper"].x  # [N, 768]

        model = GraphTransformer(
            input_dim=features.shape[1],
            hidden_dim=64,
            output_dim=num_classes,
            heads=4,
            layers=2,
            dropout=0.1,
        )

        model.eval()
        with torch.no_grad():
            logits, _, _ = model(
                features, degree_feats, attn_mask=attn_mask, collect_attention=False
            )

        shape_ok = logits.shape == (num_nodes, num_classes)
        gt_status = "PASS" if shape_ok else "FAIL"
        gt_detail = f"[{num_nodes}, {num_classes}]"
        gt_passed = shape_ok
        record("GT forward pass", shape_ok, f"logits {logits.shape}")

    except MemoryError as exc:
        gt_status = "SKIP"
        gt_detail = f"OOM: {exc}"
        gt_passed = None
        record("GT forward pass", False, f"SKIP (OOM): {exc}")
    except Exception as exc:
        gt_status = "FAIL"
        gt_detail = str(exc)
        gt_passed = False
        record("GT forward pass", False, str(exc))
        traceback.print_exc()
else:
    gt_status = "SKIP"
    gt_detail = "Graph not built"
    record("GT forward pass", False, "SKIP — Graph not built")

# ---------------------------------------------------------------------------
# Step 8 — Print report
# ---------------------------------------------------------------------------

print()
print("=" * 50)
print("=== Phase 0 Integration Test: 10K arXiv ===")
print(f"Papers loaded:          {len(df):>10,}")
print(f"Embeddings:             {str(list(embeddings.shape)):>10} float32")
print(f"Citation edges:         {citation_edge_count:>10,} (cites)")
print(f"k-NN edges:             {knn_edge_count:>10,} (similar_to)")
print(f"belongs_to edges:       {belongs_to_count:>10,}")
print(f"co_category edges:      {co_category_count:>10,}")

if graph is not None:
    val_label = (
        "PASS" if validation_passed else f"FAIL ({len(validation_warnings)} warnings)"
    )
else:
    val_label = "SKIP"
print(f"Graph validation:       {val_label:>10}")

print(f"Train nodes:            {train_count:>10,}")
print(f"Val nodes:              {val_count:>10,}")
print(f"Test nodes:             {test_count:>10,}")

batch_str = str(list(batch_shape)) if batch_shape is not None else "N/A"
print(f"One batch shape:        {batch_str:>10}")

if gt_passed is True:
    gt_label = f"PASS {gt_detail}"
elif gt_passed is None:
    gt_label = f"SKIP ({gt_detail})"
else:
    gt_label = f"FAIL ({gt_detail})"
print(f"GT forward pass:        {gt_label}")

print("=" * 50)

# Tally
n_total = len(CHECKS)
n_passed = sum(1 for _, ok, _ in CHECKS if ok)
n_failed = n_total - n_passed

if n_failed == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{n_failed} / {n_total} FAILED")
    for label, ok, detail in CHECKS:
        if not ok:
            print(f"  FAIL: {label} — {detail}")

print()
