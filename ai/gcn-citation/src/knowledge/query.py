"""Semantic search over L1 + L2 knowledge using SPECTER2 + numpy cosine similarity.

Embeds a free-text query with ``allenai/specter2_base`` (same MPS path as
:mod:`src.gcn_citation.pipeline.embedder` Path 3), then performs brute-force
cosine similarity against a pre-built L2-normalised embedding matrix to retrieve
the top-k most similar papers from the knowledge database.

**Critical constraint (E-012):** Never import ``faiss`` in this module.
FAISS and PyTorch cannot coexist in the same process on macOS Apple Silicon due
to conflicting OpenMP runtimes.  Numpy dot-product search is used instead.

The SPECTER2 model is loaded once per process and cached in ``_MODEL_CACHE``.
"""

from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path

import numpy as np

from .schema import get_connection, json_loads

# ---------------------------------------------------------------------------
# Module-level model cache — loaded once per process
# ---------------------------------------------------------------------------

_MODEL_CACHE: dict = {}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_model(model_name: str, device: str):
    """Load (or return cached) SPECTER2 tokenizer and model.

    Uses the ``adapters`` library (same as embedder.py Path 3).  The model is
    kept in ``_MODEL_CACHE`` so subsequent calls in the same process pay zero
    load cost.

    Args:
        model_name: HuggingFace model identifier for the SPECTER2 base model.
        device: PyTorch device string — ``"mps"``, ``"cuda"``, or ``"cpu"``.

    Returns:
        Tuple of ``(tokenizer, model)`` ready for inference.

    Raises:
        ImportError: If ``torch``, ``transformers``, or ``adapters`` are not
            installed.
    """
    key = (model_name, device)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    try:
        import torch
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "query.py requires torch and transformers. "
            "Install with: pip install torch transformers"
        ) from exc

    try:
        from adapters import AutoAdapterModel
    except ImportError as exc:
        raise ImportError(
            "query.py requires the 'adapters' library. "
            "Install with: pip install adapters"
        ) from exc

    t0 = time.monotonic()
    print(f"[query] Loading SPECTER2 ({model_name}) on {device} ...", file=sys.stderr)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoAdapterModel.from_pretrained(model_name)
    model.load_adapter(
        "allenai/specter2", source="hf", load_as="specter2", set_active=True
    )
    model = model.to(device)
    model.eval()

    elapsed = time.monotonic() - t0
    print(f"[query] SPECTER2 loaded in {elapsed:.1f}s", file=sys.stderr)

    _MODEL_CACHE[key] = (tokenizer, model)
    return tokenizer, model


def _embed_query(
    query: str,
    model_name: str,
    device: str,
) -> np.ndarray:
    """Embed a free-text query string into a 768-d L2-normalised float32 vector.

    For a query string (not a paper), the text is passed as-is without the
    ``sep_token + abstract`` format — the query is treated as a short document.

    Args:
        query: Free-text query string.
        model_name: HuggingFace model identifier for SPECTER2.
        device: PyTorch device string.

    Returns:
        Float32 numpy array of shape ``[768]``, L2-normalised to unit norm.
    """
    import torch

    tokenizer, model = _get_model(model_name, device)

    encoded = tokenizer(
        [query],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        outputs = model(**encoded)
        # CLS token representation (first token of last hidden state)
        vec = outputs.last_hidden_state[0, 0, :].to(dtype=torch.float32)
        vec_np = vec.cpu().numpy()  # shape [768]

    # L2-normalise the query vector
    norm = np.linalg.norm(vec_np)
    if norm > 0:
        vec_np = vec_np / norm

    return vec_np


def _cosine_search(
    query_vec: np.ndarray,
    embeddings: np.ndarray,
    top_k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Find the top-k most similar rows via dot-product (= cosine on L2-normed vecs).

    The embeddings matrix is expected to be L2-normalised (as produced by
    :func:`src.gcn_citation.pipeline.embedder.embed_papers`), so the dot product
    is equivalent to cosine similarity.

    Args:
        query_vec: 1-D float32 array of shape ``[768]``, L2-normalised.
        embeddings: 2-D float32 array of shape ``[N, 768]``, L2-normalised.
        top_k: Number of top results to return.  Clamped to ``N`` if larger.

    Returns:
        Tuple of:
        - ``indices``: Int64 array of shape ``[k]`` — row indices into
          ``embeddings``, sorted by descending similarity score.
        - ``scores``: Float32 array of shape ``[k]`` — cosine similarity scores
          in ``[−1, 1]`` (expected range ``[0, 1]`` for semantically similar docs).
    """
    actual_k = min(top_k, len(embeddings))
    scores = embeddings @ query_vec  # shape [N]
    top_idx = np.argsort(scores)[::-1][:actual_k]
    return top_idx, scores[top_idx]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search_papers(
    query: str,
    db_path: Path,
    embeddings_path: Path,
    *,
    top_k: int = 10,
    text_weight: float = 0.6,
    embed_weight: float = 0.4,
    model_name: str = "allenai/specter2_base",
    device: str = "mps",
) -> list[dict]:
    """Hybrid BM25 + embedding search over the knowledge database.

    Two-stage retrieval:

    1. **FTS5 text search** (Porter-stemmed BM25) over ``search_index`` to
       find up to 50 candidate papers.
    2. **Embedding re-ranking** — embed the query with SPECTER2, compute
       cosine similarity for the candidates only, then combine BM25 and
       cosine scores into a hybrid score.

    If the FTS5 index returns no results (e.g. query terms have no text match
    or the index is empty), falls back to a pure embedding search over all
    papers in the DB.

    **BM25 normalization:** SQLite FTS5 returns negative BM25 scores (lower =
    better).  These are normalised to ``[0, 1]`` and flipped so that 1 = best
    match.

    **Hybrid score:** ``text_weight * norm_bm25 + embed_weight * cosine``

    Args:
        query: Free-text query string (no special formatting required).
        db_path: Path to the SQLite knowledge database (must exist and have
            tables populated by :mod:`src.knowledge.ingest` and
            :mod:`src.knowledge.extract_l2`).
        embeddings_path: Path to the ``.npy`` embedding matrix (shape
            ``[N, 768]``, L2-normalised float32) produced by
            :mod:`src.gcn_citation.pipeline.embedder`.
        top_k: Number of results to return.  If fewer than ``top_k`` papers
            are available, returns however many exist.
        text_weight: Weight for the normalised BM25 score in the hybrid
            formula.  Must sum with ``embed_weight`` to 1 (not enforced).
        embed_weight: Weight for the cosine similarity score in the hybrid
            formula.
        model_name: HuggingFace model identifier for the SPECTER2 base model.
        device: PyTorch device string — ``"mps"``, ``"cuda"``, or ``"cpu"``.

    Returns:
        List of dicts, sorted by ``similarity_score`` descending.  Each dict
        contains keys: ``arxiv_id``, ``title``, ``contribution``, ``method``,
        ``key_findings`` (list), ``domain_tags`` (list), ``similarity_score``
        (float).  Fields absent from the DB are ``None`` / ``[]``.

    Raises:
        FileNotFoundError: If ``embeddings_path`` or ``db_path`` does not
            exist.
    """
    db_path = Path(db_path)
    embeddings_path = Path(embeddings_path)

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Knowledge DB not found: {db_path}")

    # --- Embed query ---
    query_vec = _embed_query(query, model_name, device)

    # --- Load embeddings (mmap, read-only) ---
    embeddings = np.load(str(embeddings_path), mmap_mode="r")

    # --- Load all valid DB rows (embedding_row → arxiv_id) ---
    conn = get_connection(db_path)
    try:
        db_rows = conn.execute(
            "SELECT embedding_row, arxiv_id FROM chunks ORDER BY embedding_row"
        ).fetchall()
    finally:
        conn.close()

    if not db_rows:
        return []

    valid_rows = np.array([r["embedding_row"] for r in db_rows], dtype=np.int64)
    row_to_arxiv: dict[int, str] = {
        int(r["embedding_row"]): r["arxiv_id"] for r in db_rows
    }
    # Reverse map for candidate selection
    arxiv_to_local: dict[str, int] = {r["arxiv_id"]: i for i, r in enumerate(db_rows)}

    # --- Stage 1: FTS5 text search → candidates ---
    # FTS5 reserved words (AND, OR, NOT, NEAR, etc.) and hyphens break raw queries.
    # Extract only alphanumeric tokens >= 3 chars, join with AND for precise matching.
    _STOPWORDS = {
        "and",
        "or",
        "not",
        "the",
        "a",
        "an",
        "in",
        "of",
        "for",
        "to",
        "is",
        "are",
        "was",
        "with",
        "that",
        "this",
        "on",
        "at",
    }
    import re as _re

    _tokens = [
        t
        for t in _re.sub(r"[^a-zA-Z0-9 ]", " ", query).lower().split()
        if len(t) >= 3 and t not in _STOPWORDS
    ]
    # Use at most 2 key tokens with AND — requiring all 5+ tokens is too strict
    # and returns 0 results. 2-token AND gives precision with coverage.
    _key_tokens = _tokens[:2] if len(_tokens) >= 2 else _tokens
    fts_query = " AND ".join(_key_tokens) if _key_tokens else None

    conn = get_connection(db_path)
    fts_results = []
    if fts_query:
        try:
            fts_results = conn.execute(
                """
                SELECT arxiv_id, bm25(search_index) AS bm25_score
                FROM search_index
                WHERE search_index MATCH ?
                ORDER BY bm25_score
                LIMIT 50
                """,
                (fts_query,),
            ).fetchall()
        except Exception as exc:
            print(
                f"[query] FTS5 search error (falling back to pure embedding): {exc}",
                file=sys.stderr,
            )
    conn.close()

    if fts_results:
        print(
            f"[query] FTS5 returned {len(fts_results)} candidates; re-ranking with embeddings.",
            file=sys.stderr,
        )
        # --- Stage 2: Hybrid re-ranking over FTS5 candidates ---
        candidate_arxiv_ids = [r["arxiv_id"] for r in fts_results]
        bm25_scores_raw = np.array(
            [r["bm25_score"] for r in fts_results], dtype=np.float64
        )

        # Normalise BM25: FTS5 returns negative scores (lower = better match)
        # Flip so that 1.0 = best match, 0.0 = worst among candidates.
        min_s = bm25_scores_raw.min()
        max_s = bm25_scores_raw.max()
        norm_bm25 = (bm25_scores_raw - min_s) / (max_s - min_s + 1e-9)
        norm_bm25 = 1.0 - norm_bm25  # flip: most negative raw → closest to 1.0

        # Gather embedding rows for candidates (skip those absent from chunks)
        candidate_local_indices = []
        candidate_order = []  # position in fts_results that has an embedding
        for i, arxiv_id in enumerate(candidate_arxiv_ids):
            local_idx = arxiv_to_local.get(arxiv_id)
            if local_idx is not None:
                candidate_local_indices.append(local_idx)
                candidate_order.append(i)

        if candidate_local_indices:
            cand_embedding_rows = valid_rows[candidate_local_indices]
            cand_embeddings = np.array(
                embeddings[cand_embedding_rows], dtype=np.float32
            )
            cand_cosine = (cand_embeddings @ query_vec).astype(np.float64)

            # Build hybrid scores for candidates that have embeddings
            hybrid_scores: dict[str, float] = {}
            for order_pos, local_pos, cosine_score in zip(
                candidate_order, candidate_local_indices, cand_cosine
            ):
                arxiv_id = candidate_arxiv_ids[order_pos]
                hybrid = text_weight * float(
                    norm_bm25[order_pos]
                ) + embed_weight * float(cosine_score)
                hybrid_scores[arxiv_id] = hybrid

            # Candidates without embeddings get text-only score
            for i, arxiv_id in enumerate(candidate_arxiv_ids):
                if arxiv_id not in hybrid_scores:
                    hybrid_scores[arxiv_id] = text_weight * float(norm_bm25[i])

        else:
            # No candidates have embeddings — use BM25 score only
            hybrid_scores = {
                arxiv_id: text_weight * float(norm_bm25[i])
                for i, arxiv_id in enumerate(candidate_arxiv_ids)
            }

        # Sort by hybrid score descending and take top_k
        ranked = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        top_arxiv_ids = [arxiv_id for arxiv_id, _ in ranked[:top_k]]
        score_by_arxiv: dict[str, float] = {
            arxiv_id: score for arxiv_id, score in ranked[:top_k]
        }

    else:
        # --- Fallback: pure embedding search over all DB papers ---
        print(
            "[query] FTS5 returned no results; falling back to pure embedding search.",
            file=sys.stderr,
        )
        embeddings_subset = np.array(embeddings[valid_rows], dtype=np.float32)
        local_idx, top_scores = _cosine_search(query_vec, embeddings_subset, top_k)
        top_embedding_rows = valid_rows[local_idx]

        if len(top_embedding_rows) == 0:
            return []

        top_arxiv_ids = []
        score_by_arxiv = {}
        for emb_row, score in zip(top_embedding_rows, top_scores):
            arxiv_id = row_to_arxiv.get(int(emb_row))
            if arxiv_id and arxiv_id not in score_by_arxiv:
                top_arxiv_ids.append(arxiv_id)
                score_by_arxiv[arxiv_id] = float(score)

    if not top_arxiv_ids:
        return []

    # --- Fetch paper_summaries ---
    conn = get_connection(db_path)
    try:
        placeholders = ",".join("?" for _ in top_arxiv_ids)
        summary_rows = conn.execute(
            f"SELECT arxiv_id, title, contribution, method, "
            f"key_findings, domain_tags "
            f"FROM paper_summaries "
            f"WHERE arxiv_id IN ({placeholders})",
            top_arxiv_ids,
        ).fetchall()
    finally:
        conn.close()

    # Build lookup by arxiv_id
    summary_by_arxiv: dict[str, dict] = {}
    for row in summary_rows:
        arxiv_id = row["arxiv_id"]
        summary_by_arxiv[arxiv_id] = {
            "arxiv_id": arxiv_id,
            "title": row["title"],
            "contribution": row["contribution"],
            "method": row["method"],
            "key_findings": json_loads(row["key_findings"]) or [],
            "domain_tags": json_loads(row["domain_tags"]) or [],
        }

    # --- Build result list in hybrid score order ---
    results: list[dict] = []
    for arxiv_id in top_arxiv_ids:
        score = score_by_arxiv[arxiv_id]
        base = summary_by_arxiv.get(arxiv_id) or {
            "arxiv_id": arxiv_id,
            "title": None,
            "contribution": None,
            "method": None,
            "key_findings": [],
            "domain_tags": [],
        }
        results.append({**base, "similarity_score": score})

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query_str = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query_str:
        print("Usage: python -m src.knowledge.query <query text>")
        sys.exit(1)

    DB = Path("data/knowledge/knowledge.db")
    EMB = Path("data/pipeline/embeddings_10k.npy")

    if not DB.exists():
        print(f"DB not found: {DB}. Run bulk extraction first.")
        sys.exit(1)

    results = search_papers(query_str, DB, EMB, top_k=5)

    if not results:
        print("No results (DB may be empty — run E-018 bulk extraction first).")
        sys.exit(0)

    print(f"\nQuery: {query_str!r}\n{'='*60}")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['similarity_score']:.3f} — arxiv:{r['arxiv_id']}")
        if r.get("title"):
            print(f"    Title: {r['title']}")
        print(f"    Contribution: {r.get('contribution', 'N/A')}")
        if r.get("key_findings"):
            print(f"    Key findings: {r['key_findings'][0]}")
        if r.get("domain_tags"):
            print(f"    Domain: {r['domain_tags']}")
