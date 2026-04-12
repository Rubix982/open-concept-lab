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
    model_name: str = "allenai/specter2_base",
    device: str = "mps",
) -> list[dict]:
    """Semantic search over the knowledge database using SPECTER2 embeddings.

    Steps:

    1. Load (or return cached) SPECTER2 model.
    2. Embed the query into a 768-d L2-normalised float32 vector.
    3. Load ``embeddings_path`` as a read-only memory-mapped numpy array.
    4. Run brute-force cosine search (numpy dot product) to find ``top_k``
       nearest rows.
    5. For each row index, look up the corresponding ``arxiv_id`` from the
       ``chunks`` table (via ``embedding_row``).
    6. Fetch ``paper_summaries`` for those arxiv IDs.
    7. Return results as dicts, sorted by descending similarity score.

    Args:
        query: Free-text query string (no special formatting required).
        db_path: Path to the SQLite knowledge database (must exist and have
            tables populated by :mod:`src.knowledge.ingest` and
            :mod:`src.knowledge.extract_l2`).
        embeddings_path: Path to the ``.npy`` embedding matrix (shape
            ``[N, 768]``, L2-normalised float32) produced by
            :mod:`src.gcn_citation.pipeline.embedder`.
        top_k: Number of results to return.  If fewer than ``top_k`` papers
            have embeddings, returns however many exist.
        model_name: HuggingFace model identifier for the SPECTER2 base model.
        device: PyTorch device string — ``"mps"``, ``"cuda"``, or ``"cpu"``.

    Returns:
        List of dicts, sorted by ``similarity_score`` descending.  Each dict
        contains keys: ``arxiv_id``, ``title``, ``contribution``, ``method``,
        ``key_findings`` (list), ``domain_tags`` (list), ``similarity_score``
        (float).  Fields absent from the DB are ``None`` / ``[]``.

    Raises:
        FileNotFoundError: If ``embeddings_path`` does not exist.
    """
    db_path = Path(db_path)
    embeddings_path = Path(embeddings_path)

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Knowledge DB not found: {db_path}")

    # --- Step 1 + 2: Embed query ---
    query_vec = _embed_query(query, model_name, device)

    # --- Step 3: Load embeddings (mmap, read-only) ---
    embeddings = np.load(str(embeddings_path), mmap_mode="r")

    # --- Step 3b: Constrain search to rows that exist in the DB ---
    # The embedding array has 10K rows but the DB may only have 500 papers.
    # Searching all 10K rows would return mostly papers not in the DB.
    conn = get_connection(db_path)
    db_rows = conn.execute(
        "SELECT embedding_row, arxiv_id FROM chunks ORDER BY embedding_row"
    ).fetchall()
    conn.close()

    if not db_rows:
        return []

    valid_rows = np.array([r["embedding_row"] for r in db_rows], dtype=np.int64)
    row_to_arxiv_full: dict[int, str] = {
        int(r["embedding_row"]): r["arxiv_id"] for r in db_rows
    }

    # Build a dense sub-matrix of only the valid rows
    embeddings_subset = np.array(embeddings[valid_rows], dtype=np.float32)

    # --- Step 4: Cosine search within DB subset ---
    local_idx, top_scores = _cosine_search(query_vec, embeddings_subset, top_k)
    # Map local indices back to real embedding row numbers
    top_idx = valid_rows[local_idx]

    if len(top_idx) == 0:
        return []

    # --- Step 5: Resolve row indices → arxiv_ids (already fetched above) ---
    row_to_arxiv = row_to_arxiv_full

    # --- Step 6: Fetch paper_summaries ---
    arxiv_ids_ordered = []
    score_by_arxiv: dict[str, float] = {}
    for idx, score in zip(top_idx, top_scores):
        arxiv_id = row_to_arxiv.get(int(idx))
        if arxiv_id and arxiv_id not in score_by_arxiv:
            arxiv_ids_ordered.append(arxiv_id)
            score_by_arxiv[arxiv_id] = float(score)

    if not arxiv_ids_ordered:
        return []

    conn = get_connection(db_path)
    try:
        placeholders = ",".join("?" for _ in arxiv_ids_ordered)
        summary_rows = conn.execute(
            f"SELECT arxiv_id, title, contribution, method, "
            f"key_findings, domain_tags "
            f"FROM paper_summaries "
            f"WHERE arxiv_id IN ({placeholders})",
            arxiv_ids_ordered,
        ).fetchall()
    finally:
        conn.close()

    # Build a lookup by arxiv_id (summaries may be absent for uncompleted extraction)
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

    # --- Step 7: Build result list in score order ---
    results: list[dict] = []
    for arxiv_id in arxiv_ids_ordered:
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
