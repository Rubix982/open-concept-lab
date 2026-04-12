"""Validation script for E-024: Hybrid FTS5 + embedding re-ranking in query.py.

Steps:
1. Build (or rebuild) the FTS5 search index from paper_summaries.
2. Run the 10 Phase 1 benchmark queries.
3. For each query report: FTS5 result count, hybrid top-1, and topical relevance.
4. Print PASS/FAIL for each query.

Usage:
    source .venv/bin/activate
    python agents/engineer/workspace/validate_hybrid_query.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

DB_PATH = Path("data/knowledge/knowledge.db")
EMB_PATH = Path("data/pipeline/embeddings_10k.npy")

# ---------------------------------------------------------------------------
# Phase 1 benchmark queries and their expected topic keywords
# ---------------------------------------------------------------------------

PHASE1_QUERIES = [
    ("batch normalization", ["batch norm", "normalization", "batch"]),
    (
        "graph neural network",
        ["graph", "gnn", "node classification", "gcn", "message passing"],
    ),
    ("diffusion model", ["diffusion", "denoising", "score", "ddpm"]),
    ("transformer attention", ["transformer", "attention", "self-attention"]),
    ("contrastive learning", ["contrastive", "self-supervised", "representation"]),
    ("knowledge distillation", ["distillation", "teacher", "student", "compression"]),
    ("reinforcement learning policy", ["reinforcement", "policy", "reward", "agent"]),
    ("variational autoencoder", ["variational", "vae", "latent", "encoder", "decoder"]),
    (
        "object detection",
        ["detection", "object", "bounding box", "yolo", "faster rcnn"],
    ),
    (
        "natural language processing",
        ["language", "nlp", "text", "bert", "llm", "pretrain"],
    ),
]


def is_topically_relevant(result: dict, keywords: list[str]) -> bool:
    """Return True if the top result contains at least one expected keyword."""
    fields = [
        result.get("title") or "",
        result.get("contribution") or "",
    ]
    findings = result.get("key_findings") or []
    if isinstance(findings, list):
        fields.extend(findings)
    combined = " ".join(fields).lower()
    return any(kw.lower() in combined for kw in keywords)


def main() -> None:
    # --- Sanity check: DB and embeddings must exist ---
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}. Run ingest pipeline first.")
        sys.exit(1)
    if not EMB_PATH.exists():
        print(f"ERROR: Embeddings not found at {EMB_PATH}. Run embedder first.")
        sys.exit(1)

    # --- Step 1: Build / rebuild FTS5 search index ---
    print("=" * 60)
    print("Step 1: Building FTS5 search index...")
    from src.knowledge.ingest import build_search_index
    from src.knowledge.schema import get_connection

    count = build_search_index(DB_PATH)
    print(f"  Indexed {count} papers into FTS5 search_index.")

    # --- Sanity check: topic coverage in paper_summaries ---
    print("\nStep 2: Topic coverage sanity check (paper_summaries.contribution):")
    conn = get_connection(DB_PATH)
    for term in ["batch norm", "graph neural", "diffusion", "transformer"]:
        n = conn.execute(
            "SELECT COUNT(*) FROM paper_summaries WHERE LOWER(contribution) LIKE ?",
            (f"%{term}%",),
        ).fetchone()[0]
        print(f"  '{term}': {n} papers")

    # Also check FTS5 index coverage
    print("\nStep 3: FTS5 index coverage check:")
    for term in ["batch norm", "graph neural", "diffusion", "transformer"]:
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM search_index WHERE search_index MATCH ?",
                (term,),
            ).fetchone()[0]
            print(f"  FTS5 '{term}': {n} hits")
        except Exception as exc:
            print(f"  FTS5 '{term}': ERROR — {exc}")
    conn.close()

    # --- Step 4: Run the 10 Phase 1 queries ---
    print("\nStep 4: Running hybrid search on 10 Phase 1 queries...")
    print("=" * 60)

    from src.knowledge.query import search_papers

    passed = 0
    failed = 0
    results_summary = []

    for query, keywords in PHASE1_QUERIES:
        print(f"\nQuery: {query!r}")
        try:
            results = search_papers(
                query,
                DB_PATH,
                EMB_PATH,
                top_k=5,
                text_weight=0.6,
                embed_weight=0.4,
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            failed += 1
            results_summary.append((query, "ERROR", str(exc)))
            continue

        if not results:
            print("  No results returned.")
            failed += 1
            results_summary.append((query, "FAIL", "No results"))
            continue

        top = results[0]
        relevant = is_topically_relevant(top, keywords)
        status = "PASS" if relevant else "FAIL"
        if relevant:
            passed += 1
        else:
            failed += 1

        print(
            f"  Top result: arxiv:{top['arxiv_id']}  score={top['similarity_score']:.4f}"
        )
        print(f"  Title: {top.get('title', 'N/A')}")
        contrib = (top.get("contribution") or "")[:120]
        print(f"  Contribution: {contrib}")
        print(f"  [{status}] (keywords checked: {keywords[:3]})")
        results_summary.append((query, status, top.get("title") or top["arxiv_id"]))

    # --- Summary table ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for query, status, detail in results_summary:
        marker = "✓" if status == "PASS" else "✗"
        print(f"  [{marker}] {status:5s}  {query!r:45s}  → {detail[:60]}")

    total = passed + failed
    print(f"\n  {passed}/{total} queries PASSED topical relevance check.")

    if passed >= 7:
        print("\nOVERALL: PASS (≥7/10 relevant)")
    else:
        print("\nOVERALL: FAIL (<7/10 relevant — check FTS5 index coverage)")


if __name__ == "__main__":
    main()
