from __future__ import annotations

import json
import tarfile
import urllib.request
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path

import duckdb
import numpy as np


DATASET_URL = "https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz"


@dataclass
class GraphData:
    features: np.ndarray
    labels: np.ndarray
    label_names: list[str]
    adjacency_hat: np.ndarray
    train_mask: np.ndarray
    val_mask: np.ndarray
    test_mask: np.ndarray
    paper_ids: np.ndarray
    edges: np.ndarray


def clone_graph_data(
    graph: GraphData,
    *,
    features: np.ndarray | None = None,
    adjacency_hat: np.ndarray | None = None,
) -> GraphData:
    return replace(
        graph,
        features=graph.features if features is None else features,
        adjacency_hat=graph.adjacency_hat if adjacency_hat is None else adjacency_hat,
    )


def identity_adjacency(num_nodes: int) -> np.ndarray:
    return np.eye(num_nodes, dtype=np.float32)


def structural_identity_features(num_nodes: int) -> np.ndarray:
    return np.eye(num_nodes, dtype=np.float32)


def ensure_cora_dataset(data_dir: Path) -> tuple[Path, Path]:
    raw_dir = data_dir / "raw"
    extracted_dir = raw_dir / "cora"
    content_path = extracted_dir / "cora.content"
    cites_path = extracted_dir / "cora.cites"

    if content_path.exists() and cites_path.exists():
        return content_path, cites_path

    data_dir.mkdir(parents=True, exist_ok=True)
    archive_path = data_dir / "cora.tgz"

    if not archive_path.exists():
        urllib.request.urlretrieve(DATASET_URL, archive_path)

    raw_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(raw_dir)

    return content_path, cites_path


def _parse_cora(
    content_path: Path, cites_path: Path
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray, np.ndarray]:
    rows = [
        line.strip().split()
        for line in content_path.read_text().splitlines()
        if line.strip()
    ]
    paper_ids = np.array([row[0] for row in rows], dtype=object)
    features = np.asarray(
        [[int(value) for value in row[1:-1]] for row in rows], dtype=np.float32
    )
    label_names = sorted({row[-1] for row in rows})
    label_to_idx = {label: idx for idx, label in enumerate(label_names)}
    labels = np.array([label_to_idx[row[-1]] for row in rows], dtype=np.int64)

    paper_to_idx = {paper_id: idx for idx, paper_id in enumerate(paper_ids.tolist())}
    edges: list[tuple[int, int]] = []
    for line in cites_path.read_text().splitlines():
        src_paper, dst_paper = line.strip().split()
        if src_paper in paper_to_idx and dst_paper in paper_to_idx:
            src_idx = paper_to_idx[src_paper]
            dst_idx = paper_to_idx[dst_paper]
            edges.append((src_idx, dst_idx))
            edges.append((dst_idx, src_idx))

    edge_array = np.asarray(edges, dtype=np.int64)
    return paper_ids, features, label_names, labels, edge_array


def persist_to_duckdb(
    db_path: Path,
    paper_ids: np.ndarray,
    features: np.ndarray,
    label_names: list[str],
    labels: np.ndarray,
    edges: np.ndarray,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(db_path))

    try:
        connection.execute("DROP TABLE IF EXISTS nodes")
        connection.execute("DROP TABLE IF EXISTS node_features")
        connection.execute("DROP TABLE IF EXISTS edges")
        connection.execute("DROP TABLE IF EXISTS metadata")

        connection.execute(
            """
            CREATE TABLE nodes (
                node_idx INTEGER,
                paper_id VARCHAR,
                label_id INTEGER,
                label_name VARCHAR
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE node_features (
                node_idx INTEGER,
                feature_idx INTEGER,
                value FLOAT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE edges (
                src_idx INTEGER,
                dst_idx INTEGER
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE metadata (
                key VARCHAR,
                value VARCHAR
            )
            """
        )

        node_rows = [
            (
                int(idx),
                str(paper_ids[idx]),
                int(labels[idx]),
                str(label_names[labels[idx]]),
            )
            for idx in range(len(paper_ids))
        ]
        connection.executemany("INSERT INTO nodes VALUES (?, ?, ?, ?)", node_rows)

        nonzero_rows = np.argwhere(features > 0)
        feature_rows = [
            (int(node_idx), int(feature_idx), float(features[node_idx, feature_idx]))
            for node_idx, feature_idx in nonzero_rows
        ]
        connection.executemany(
            "INSERT INTO node_features VALUES (?, ?, ?)", feature_rows
        )

        edge_rows = [(int(src_idx), int(dst_idx)) for src_idx, dst_idx in edges]
        connection.executemany("INSERT INTO edges VALUES (?, ?)", edge_rows)

        metadata = {
            "num_nodes": str(features.shape[0]),
            "num_features": str(features.shape[1]),
            "num_edges": str(edges.shape[0]),
            "num_classes": str(len(label_names)),
            "label_names": json.dumps(label_names),
        }
        connection.executemany(
            "INSERT INTO metadata VALUES (?, ?)", list(metadata.items())
        )
    finally:
        connection.close()


def make_splits(
    labels: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    num_nodes = labels.shape[0]
    train_mask = np.zeros(num_nodes, dtype=bool)
    val_mask = np.zeros(num_nodes, dtype=bool)
    test_mask = np.zeros(num_nodes, dtype=bool)

    for label in np.unique(labels):
        label_indices = np.where(labels == label)[0]
        shuffled = rng.permutation(label_indices)
        if shuffled.shape[0] >= 30:
            train_count = 20
        else:
            # For smaller custom datasets, keep some examples aside for validation/test.
            train_count = max(1, int(np.floor(shuffled.shape[0] * 0.6)))
        train_mask[shuffled[:train_count]] = True

    remaining = np.where(~train_mask)[0]
    remaining = rng.permutation(remaining)

    if remaining.shape[0] >= 1500:
        val_count = 500
        test_count = min(1000, remaining.shape[0] - val_count)
    elif remaining.shape[0] <= 1:
        val_count = remaining.shape[0]
        test_count = 0
    else:
        val_count = max(1, remaining.shape[0] // 3)
        test_count = remaining.shape[0] - val_count

    val_mask[remaining[:val_count]] = True
    test_mask[remaining[val_count : val_count + test_count]] = True

    if (~(train_mask | val_mask | test_mask)).any():
        leftover = np.where(~(train_mask | val_mask | test_mask))[0]
        test_mask[leftover] = True

    return train_mask, val_mask, test_mask


def build_normalized_adjacency(num_nodes: int, edges: np.ndarray) -> np.ndarray:
    adjacency = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    adjacency[edges[:, 0], edges[:, 1]] = 1.0
    adjacency = np.maximum(adjacency, adjacency.T)
    adjacency += np.eye(num_nodes, dtype=np.float32)

    degree = adjacency.sum(axis=1)
    inv_sqrt_degree = np.power(degree, -0.5, dtype=np.float32)
    inv_sqrt_degree[np.isinf(inv_sqrt_degree)] = 0.0
    normalized = adjacency * inv_sqrt_degree[:, None] * inv_sqrt_degree[None, :]
    return normalized.astype(np.float32)


def load_graph_data(data_dir: Path, db_path: Path, seed: int) -> GraphData:
    content_path, cites_path = ensure_cora_dataset(data_dir)
    paper_ids, features, label_names, labels, edges = _parse_cora(
        content_path, cites_path
    )
    persist_to_duckdb(db_path, paper_ids, features, label_names, labels, edges)

    rng = np.random.default_rng(seed)
    train_mask, val_mask, test_mask = make_splits(labels, rng)
    adjacency_hat = build_normalized_adjacency(features.shape[0], edges)

    return GraphData(
        features=features,
        labels=labels,
        label_names=label_names,
        adjacency_hat=adjacency_hat,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        paper_ids=paper_ids,
        edges=edges,
    )
