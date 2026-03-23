from __future__ import annotations

import json
import socket
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from urllib.error import URLError
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .data import GraphData
from .data import build_normalized_adjacency
from .data import make_splits


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def _progress(message: str) -> None:
    print(f"[arxiv] {message}", file=sys.stderr, flush=True)


@dataclass
class ArxivCacheSummary:
    corpus_key: str
    categories: list[str]
    requested_results: int
    cached_entries: int
    batch_size: int
    fetch_timestamp: float
    raw_dir: Path
    processed_dir: Path
    manifest_path: Path
    entries_path: Path


def _corpus_key(categories: list[str], max_results: int) -> str:
    category_part = "_".join(category.replace(".", "_") for category in categories)
    return f"{category_part}_{max_results}"


def _processed_key(categories: list[str], max_results: int, top_k: int, max_features: int) -> str:
    return f"{_corpus_key(categories, max_results)}_k{top_k}_f{max_features}"


def _cache_layout(data_dir: Path, categories: list[str], max_results: int) -> tuple[Path, Path]:
    corpus_key = _corpus_key(categories, max_results)
    raw_dir = data_dir / "raw" / corpus_key
    processed_dir = data_dir / "processed" / corpus_key
    return raw_dir, processed_dir


def _fetch_arxiv_feed(
    *,
    categories: list[str],
    max_results: int,
    page_size: int,
    delay_seconds: float,
    raw_dir: Path,
) -> list[str]:
    xml_chunks: list[str] = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    per_category_results = max(1, int(np.ceil(max_results / max(1, len(categories)))))
    _progress(
        f"fetching up to {max_results} papers across {len(categories)} categories "
        f"(~{per_category_results} per category)"
    )

    for category in categories:
        category_dir = raw_dir / category.replace(".", "_")
        category_dir.mkdir(parents=True, exist_ok=True)
        _progress(f"category {category}: starting fetch into {category_dir}")
        xml_chunks.extend(
            _fetch_category_feed(
                category=category,
                max_results=per_category_results,
                page_size=page_size,
                delay_seconds=delay_seconds,
                category_dir=category_dir,
            )
        )

    return xml_chunks


def _fetch_category_feed(
    *,
    category: str,
    max_results: int,
    page_size: int,
    delay_seconds: float,
    category_dir: Path,
) -> list[str]:
    search_query = f"cat:{category}"
    xml_chunks: list[str] = []
    total_batches = int(np.ceil(max_results / page_size))

    for batch_index, start in enumerate(range(0, max_results, page_size)):
        batch_size = min(page_size, max_results - start)
        batch_path = category_dir / f"batch_{batch_index:04d}.xml"
        if batch_path.exists():
            _progress(
                f"category {category}: reusing batch {batch_index + 1}/{total_batches} "
                f"({batch_size} requested)"
            )
            xml_chunks.append(batch_path.read_text())
            continue

        _progress(
            f"category {category}: fetching batch {batch_index + 1}/{total_batches} "
            f"(start={start}, size={batch_size})"
        )
        query_params = {
            "search_query": search_query,
            "start": start,
            "max_results": batch_size,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(query_params)}"
        request = urllib.request.Request(url, headers={"User-Agent": "gcn-citation/0.1 (research pipeline)"})
        xml_chunk = _fetch_batch_with_retries(request)
        xml_chunks.append(xml_chunk)
        batch_path.write_text(xml_chunk)
        if start + batch_size < max_results:
            _progress(f"category {category}: sleeping {delay_seconds:.1f}s before next batch")
            time.sleep(delay_seconds)

    return xml_chunks


def _fetch_batch_with_retries(
    request: urllib.request.Request,
    max_attempts: int = 7,
    timeout_seconds: int = 120,
) -> str:
    delay = 8.0
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return response.read().decode("utf-8")
        except HTTPError as error:
            last_error = error
            if error.code != 429 and error.code < 500:
                raise
            retry_after = error.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
            _progress(f"request throttled with HTTP {error.code}; retrying in {delay:.1f}s (attempt {attempt}/{max_attempts})")
        except (URLError, TimeoutError, socket.timeout) as error:
            last_error = error
            _progress(f"request failed with {type(error).__name__}; retrying in {delay:.1f}s (attempt {attempt}/{max_attempts})")

        if attempt == max_attempts:
            break
        time.sleep(delay)
        delay = min(delay * 2.0, 120.0)

    raise RuntimeError(
        f"Failed to fetch arXiv batch after {max_attempts} attempts. "
        f"Last error: {last_error!r}"
    )


def _parse_arxiv_entries(feed_xml: str, allowed_categories: set[str]) -> list[dict[str, str | list[str]]]:
    root = ET.fromstring(feed_xml)
    entries: list[dict[str, str | list[str]]] = []
    seen_ids: set[str] = set()

    for entry in root.findall("atom:entry", ATOM_NAMESPACE):
        paper_id = entry.findtext("atom:id", default="", namespaces=ATOM_NAMESPACE).strip()
        if not paper_id or paper_id in seen_ids:
            continue

        category_terms = [
            category.attrib["term"]
            for category in entry.findall("atom:category", ATOM_NAMESPACE)
            if "term" in category.attrib
        ]
        primary_category = next((term for term in category_terms if term in allowed_categories), None)
        if primary_category is None:
            continue

        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NAMESPACE).split())
        abstract = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NAMESPACE).split())
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NAMESPACE).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NAMESPACE).strip()

        entries.append(
            {
                "paper_id": paper_id,
                "title": title,
                "abstract": abstract,
                "published": published,
                "updated": updated,
                "primary_category": primary_category,
                "all_categories": category_terms,
            }
        )
        seen_ids.add(paper_id)

    return entries


def _parse_arxiv_entries_from_chunks(
    xml_chunks: list[str],
    allowed_categories: set[str],
) -> list[dict[str, str | list[str]]]:
    merged: list[dict[str, str | list[str]]] = []
    seen_ids: set[str] = set()

    for xml_chunk in xml_chunks:
        for entry in _parse_arxiv_entries(xml_chunk, allowed_categories):
            paper_id = str(entry["paper_id"])
            if paper_id in seen_ids:
                continue
            merged.append(entry)
            seen_ids.add(paper_id)

    return merged


def _write_manifest(
    *,
    manifest_path: Path,
    corpus_key: str,
    categories: list[str],
    max_results: int,
    batch_size: int,
    entries: list[dict[str, str | list[str]]],
    fetch_timestamp: float,
) -> dict[str, object]:
    category_counts: dict[str, int] = {}
    published_dates = [str(entry["published"]) for entry in entries if str(entry["published"])]
    for entry in entries:
        category = str(entry["primary_category"])
        category_counts[category] = category_counts.get(category, 0) + 1

    manifest = {
        "corpus_key": corpus_key,
        "categories": categories,
        "requested_results": max_results,
        "requested_results_per_category": int(np.ceil(max_results / max(1, len(categories)))),
        "cached_entries": len(entries),
        "batch_size": batch_size,
        "fetch_timestamp": fetch_timestamp,
        "category_counts": category_counts,
        "published_min": min(published_dates) if published_dates else "",
        "published_max": max(published_dates) if published_dates else "",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def fetch_and_cache_arxiv_corpus(
    *,
    data_dir: Path,
    categories: list[str],
    max_results: int,
    page_size: int,
    delay_seconds: float,
    refresh_cache: bool,
) -> ArxivCacheSummary:
    raw_dir, processed_dir = _cache_layout(data_dir, categories, max_results)
    manifest_path = raw_dir / "manifest.json"
    entries_path = raw_dir / "entries.json"
    corpus_key = _corpus_key(categories, max_results)

    if not refresh_cache and manifest_path.exists() and entries_path.exists():
        manifest = json.loads(manifest_path.read_text())
        _progress(
            f"reusing cached corpus {corpus_key} with {manifest['cached_entries']} entries "
            f"from {entries_path}"
        )
        return ArxivCacheSummary(
            corpus_key=corpus_key,
            categories=list(manifest["categories"]),
            requested_results=int(manifest["requested_results"]),
            cached_entries=int(manifest["cached_entries"]),
            batch_size=int(manifest["batch_size"]),
            fetch_timestamp=float(manifest["fetch_timestamp"]),
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            manifest_path=manifest_path,
            entries_path=entries_path,
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    if refresh_cache:
        _progress(f"refreshing cache for corpus {corpus_key}")
        for batch_file in raw_dir.rglob("batch_*.xml"):
            batch_file.unlink()

    xml_chunks = _fetch_arxiv_feed(
        categories=categories,
        max_results=max_results,
        page_size=page_size,
        delay_seconds=delay_seconds,
        raw_dir=raw_dir,
    )
    entries = _parse_arxiv_entries_from_chunks(xml_chunks, set(categories))
    entries_path.write_text(json.dumps(entries, indent=2))
    fetch_timestamp = time.time()
    _progress(f"fetched and cached {len(entries)} entries for corpus {corpus_key}")
    manifest = _write_manifest(
        manifest_path=manifest_path,
        corpus_key=corpus_key,
        categories=categories,
        max_results=max_results,
        batch_size=page_size,
        entries=entries,
        fetch_timestamp=fetch_timestamp,
    )

    return ArxivCacheSummary(
        corpus_key=corpus_key,
        categories=list(manifest["categories"]),
        requested_results=int(manifest["requested_results"]),
        cached_entries=int(manifest["cached_entries"]),
        batch_size=int(manifest["batch_size"]),
        fetch_timestamp=float(manifest["fetch_timestamp"]),
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        manifest_path=manifest_path,
        entries_path=entries_path,
    )


def _build_similarity_edges(features: np.ndarray, top_k: int) -> np.ndarray:
    normalized = features / np.clip(np.linalg.norm(features, axis=1, keepdims=True), 1e-12, None)
    similarity = normalized @ normalized.T
    np.fill_diagonal(similarity, -np.inf)
    effective_top_k = min(top_k, max(1, similarity.shape[0] - 1))

    edges: set[tuple[int, int]] = set()
    for node_index in range(similarity.shape[0]):
        neighbor_indices = np.argpartition(similarity[node_index], -effective_top_k)[-effective_top_k:]
        for neighbor_index in neighbor_indices:
            if neighbor_index == node_index:
                continue
            src, dst = sorted((int(node_index), int(neighbor_index)))
            edges.add((src, dst))
            edges.add((dst, src))

    return np.asarray(sorted(edges), dtype=np.int64)


def _graph_stats(num_nodes: int, edges: np.ndarray) -> dict[str, float | int]:
    undirected_edges = edges.shape[0] // 2
    average_degree = float(edges.shape[0] / max(1, num_nodes))
    possible_undirected_edges = max(1, num_nodes * (num_nodes - 1) / 2)
    density = float(undirected_edges / possible_undirected_edges)
    return {
        "num_nodes": int(num_nodes),
        "num_directed_edges": int(edges.shape[0]),
        "num_undirected_edges": int(undirected_edges),
        "average_degree": average_degree,
        "density": density,
    }


def persist_arxiv_to_duckdb(
    db_path: Path,
    entries: list[dict[str, str | list[str]]],
    features: np.ndarray,
    label_names: list[str],
    labels: np.ndarray,
    edges: np.ndarray,
    vectorizer: TfidfVectorizer,
    categories: list[str],
    graph_stats: dict[str, float | int],
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
                title VARCHAR,
                abstract VARCHAR,
                published VARCHAR,
                updated VARCHAR,
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
                token VARCHAR,
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
                index,
                str(entry["paper_id"]),
                str(entry["title"]),
                str(entry["abstract"]),
                str(entry["published"]),
                str(entry["updated"]),
                int(labels[index]),
                label_names[int(labels[index])],
            )
            for index, entry in enumerate(entries)
        ]
        connection.executemany("INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", node_rows)

        vocabulary = {feature_index: token for token, feature_index in vectorizer.vocabulary_.items()}
        nonzero_rows = np.argwhere(features > 0)
        feature_rows = [
            (
                int(node_idx),
                int(feature_idx),
                vocabulary.get(int(feature_idx), ""),
                float(features[node_idx, feature_idx]),
            )
            for node_idx, feature_idx in nonzero_rows
        ]
        connection.executemany("INSERT INTO node_features VALUES (?, ?, ?, ?)", feature_rows)

        edge_rows = [(int(src_idx), int(dst_idx)) for src_idx, dst_idx in edges]
        connection.executemany("INSERT INTO edges VALUES (?, ?)", edge_rows)

        metadata = {
            "source": "arxiv",
            "num_nodes": str(features.shape[0]),
            "num_features": str(features.shape[1]),
            "num_edges": str(edges.shape[0]),
            "num_classes": str(len(label_names)),
            "label_names": json.dumps(label_names),
            "categories": json.dumps(categories),
            "vocabulary_size": str(len(vectorizer.vocabulary_)),
            "graph_stats": json.dumps(graph_stats),
        }
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", list(metadata.items()))
    finally:
        connection.close()


def _load_processed_snapshot(snapshot_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    snapshot = np.load(snapshot_path, allow_pickle=False)
    return (
        snapshot["features"].astype(np.float32),
        snapshot["labels"].astype(np.int64),
        snapshot["edges"].astype(np.int64),
        snapshot["paper_ids"].astype(str),
        snapshot["label_names"].astype(str),
    )


def _save_processed_snapshot(
    snapshot_path: Path,
    *,
    features: np.ndarray,
    labels: np.ndarray,
    edges: np.ndarray,
    paper_ids: np.ndarray,
    label_names: np.ndarray,
) -> None:
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        snapshot_path,
        features=features.astype(np.float32),
        labels=labels.astype(np.int64),
        edges=edges.astype(np.int64),
        paper_ids=paper_ids.astype(str),
        label_names=label_names.astype(str),
    )


def build_cached_arxiv_dataset(
    *,
    data_dir: Path,
    db_path: Path,
    seed: int,
    categories: list[str],
    max_results: int,
    top_k: int,
    max_features: int,
    page_size: int = 100,
    delay_seconds: float = 3.0,
    refresh_cache: bool = False,
    cache_only: bool = False,
) -> tuple[GraphData | None, dict[str, object]]:
    cache_summary = fetch_and_cache_arxiv_corpus(
        data_dir=data_dir,
        categories=categories,
        max_results=max_results,
        page_size=page_size,
        delay_seconds=delay_seconds,
        refresh_cache=refresh_cache,
    )

    entries = json.loads(cache_summary.entries_path.read_text())
    if len(entries) < len(categories) * 5:
        raise ValueError(
            f"Fetched only {len(entries)} arXiv entries across categories {categories}. "
            "Try increasing --arxiv-max-results or broadening the category list."
        )

    dataset_key = _processed_key(categories, max_results, top_k, max_features)
    processed_dir = cache_summary.processed_dir / dataset_key
    processed_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = processed_dir / "dataset_snapshot.npz"
    summary_path = processed_dir / "summary.json"

    if snapshot_path.exists() and not refresh_cache:
        _progress(f"reusing processed snapshot {snapshot_path}")
        features, labels, edges, paper_ids, label_names_np = _load_processed_snapshot(snapshot_path)
        label_names = label_names_np.tolist()
    else:
        _progress(
            f"building processed snapshot {dataset_key} "
            f"(top_k={top_k}, max_features={max_features})"
        )
        corpus = [f"{entry['title']} {entry['abstract']}" for entry in entries]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
        features = vectorizer.fit_transform(corpus).astype(np.float32).toarray()

        label_names = sorted(categories)
        label_to_index = {label_name: index for index, label_name in enumerate(label_names)}
        labels = np.asarray([label_to_index[str(entry["primary_category"])] for entry in entries], dtype=np.int64)
        edges = _build_similarity_edges(features, top_k=top_k)
        paper_ids = np.asarray([str(entry["paper_id"]) for entry in entries], dtype=str)
        label_names_np = np.asarray(label_names, dtype=str)
        _save_processed_snapshot(
            snapshot_path,
            features=features,
            labels=labels,
            edges=edges,
            paper_ids=paper_ids,
            label_names=label_names_np,
        )
        _progress(f"saved processed snapshot to {snapshot_path}")

        graph_stats = _graph_stats(features.shape[0], edges)
        summary_path.write_text(
            json.dumps(
                {
                    "dataset_key": dataset_key,
                    "categories": categories,
                    "max_results": max_results,
                    "top_k": top_k,
                    "max_features": max_features,
                    "snapshot_path": str(snapshot_path),
                    "graph_stats": graph_stats,
                    "label_counts": {
                        label_name: int(np.sum(labels == index))
                        for index, label_name in enumerate(label_names)
                    },
                },
                indent=2,
            )
        )

        persist_arxiv_to_duckdb(
            db_path=db_path,
            entries=entries,
            features=features,
            label_names=label_names,
            labels=labels,
            edges=edges,
            vectorizer=vectorizer,
            categories=categories,
            graph_stats=graph_stats,
        )

    if not summary_path.exists():
        graph_stats = _graph_stats(features.shape[0], edges)
        summary_path.write_text(
            json.dumps(
                {
                    "dataset_key": dataset_key,
                    "categories": categories,
                    "max_results": max_results,
                    "top_k": top_k,
                    "max_features": max_features,
                    "snapshot_path": str(snapshot_path),
                    "graph_stats": graph_stats,
                    "label_counts": {
                        label_name: int(np.sum(labels == index))
                        for index, label_name in enumerate(label_names)
                    },
                },
                indent=2,
            )
        )

    summary = {
        "corpus_key": cache_summary.corpus_key,
        "dataset_key": dataset_key,
        "raw_dir": str(cache_summary.raw_dir),
        "processed_dir": str(processed_dir),
        "manifest_path": str(cache_summary.manifest_path),
        "entries_path": str(cache_summary.entries_path),
        "summary_path": str(summary_path),
        "snapshot_path": str(snapshot_path),
        "cached_entries": int(len(entries)),
        "graph_stats": _graph_stats(features.shape[0], edges),
    }

    if cache_only:
        _progress("cache-only run complete")
        return None, summary

    if not db_path.exists() or refresh_cache:
        _progress(f"writing DuckDB dataset to {db_path}")
        # Reconstruct vectorizer-backed tables if the processed snapshot was reused or the DB is missing.
        corpus = [f"{entry['title']} {entry['abstract']}" for entry in entries]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
        vectorizer.fit(corpus)
        persist_arxiv_to_duckdb(
            db_path=db_path,
            entries=entries,
            features=features,
            label_names=label_names,
            labels=labels,
            edges=edges,
            vectorizer=vectorizer,
            categories=categories,
            graph_stats=summary["graph_stats"],
        )

    rng = np.random.default_rng(seed)
    train_mask, val_mask, test_mask = make_splits(labels, rng)
    adjacency_hat = build_normalized_adjacency(features.shape[0], edges)
    _progress(
        f"dataset ready: {features.shape[0]} nodes, {edges.shape[0]} directed edges, "
        f"train/val/test={int(train_mask.sum())}/{int(val_mask.sum())}/{int(test_mask.sum())}"
    )

    graph = GraphData(
        features=features,
        labels=labels,
        label_names=label_names,
        adjacency_hat=adjacency_hat,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        paper_ids=paper_ids.astype(object),
        edges=edges,
    )
    return graph, summary


def load_arxiv_graph_data(
    *,
    data_dir: Path,
    db_path: Path,
    seed: int,
    categories: list[str],
    max_results: int,
    top_k: int,
    max_features: int,
    page_size: int = 100,
    delay_seconds: float = 3.0,
    refresh_cache: bool = False,
) -> GraphData:
    graph, _ = build_cached_arxiv_dataset(
        data_dir=data_dir,
        db_path=db_path,
        seed=seed,
        categories=categories,
        max_results=max_results,
        top_k=top_k,
        max_features=max_features,
        page_size=page_size,
        delay_seconds=delay_seconds,
        refresh_cache=refresh_cache,
        cache_only=False,
    )
    assert graph is not None
    return graph
