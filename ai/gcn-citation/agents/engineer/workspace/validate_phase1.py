"""E-019: Phase 1 end-to-end validation.

Fires 10 real queries against the populated knowledge DB and evaluates result
quality via automated checks and printed output for manual review.
"""

import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
sys.path.insert(0, ".")

from pathlib import Path

from src.knowledge.query import search_papers

DB = Path("data/knowledge/knowledge.db")
EMB = Path("data/pipeline/embeddings_10k.npy")

QUERIES = [
    "batch normalization deep neural networks",
    "self-supervised contrastive learning representations",
    "transformer attention mechanism long sequences",
    "graph neural network message passing aggregation",
    "diffusion probabilistic generative models",
    "vision transformer image classification",
    "reinforcement learning policy gradient reward",
    "knowledge distillation model compression",
    "adversarial examples robustness neural network",
    "overparameterization generalization implicit bias",
]


def run_validation():
    print("=== Phase 1 End-to-End Validation ===")
    print(f"DB: {DB}")
    print(f"EMB: {EMB}")
    print()

    summary_rows = []

    for q_idx, query in enumerate(QUERIES, 1):
        print(f'Query {q_idx}/10: "{query}"')
        print("-" * 60)

        try:
            results = search_papers(query, DB, EMB, top_k=5)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary_rows.append((query, None, 0, "FAIL"))
            print()
            continue

        if not results:
            print("  No results returned.")
            summary_rows.append((query, None, 0, "FAIL"))
            print()
            continue

        # Print top 3 results for manual review
        for rank, r in enumerate(results[:3], 1):
            arxiv_id = r.get("arxiv_id", "N/A")
            score = r.get("similarity_score", 0.0)
            contribution = r.get("contribution") or "N/A"
            domain_tags = r.get("domain_tags") or []
            title = r.get("title") or "N/A"

            print(f"  [{rank}] {score:.3f} — {arxiv_id}")
            print(f"      Title: {title}")
            print(
                f"      Contribution: {contribution[:200]}{'...' if len(str(contribution)) > 200 else ''}"
            )
            print(f"      Domain: {domain_tags}")

        # Automated checks
        top = results[0]
        top_score = top.get("similarity_score", 0.0)
        top_domains = top.get("domain_tags") or []
        num_results = len(results)

        check1 = num_results >= 1
        check2 = top_score > 0.5
        check3 = len(top_domains) > 0

        auto_pass = check1 and check2 and check3
        status = "PASS" if auto_pass else "FAIL"

        print()
        print(f"  Automated checks:")
        print(
            f"    Results >= 1:           {'OK' if check1 else 'FAIL'} ({num_results} results)"
        )
        print(
            f"    Top score > 0.5:        {'OK' if check2 else 'FAIL'} ({top_score:.3f})"
        )
        print(
            f"    Domain tags not empty:  {'OK' if check3 else 'FAIL'} ({top_domains})"
        )
        print(f"  => Auto: {status}")
        print()

        summary_rows.append((query, top_score, num_results, status))

    # Final summary table
    print()
    print("=" * 80)
    print("=== Phase 1 End-to-End Validation — SUMMARY ===")
    print(f"DB: 500 papers | Queries: {len(QUERIES)}")
    print()
    print(f"{'Query':<45} | {'Top Score':>9} | {'Results':>7} | {'Auto':>4}")
    print("-" * 45 + "-+-" + "-" * 9 + "-+-" + "-" * 7 + "-+-" + "-" * 4)
    pass_count = 0
    for query, top_score, num_results, status in summary_rows:
        short_q = query[:44]
        score_str = f"{top_score:.3f}" if top_score is not None else "N/A"
        print(f"{short_q:<45} | {score_str:>9} | {num_results:>7} | {status:>4}")
        if status == "PASS":
            pass_count += 1

    print()
    print(f"Automated: {pass_count}/{len(QUERIES)} PASS")
    print()
    print("Manual review: see top-3 contributions printed above for each query.")
    print("Phase 1 DONE when: >= 8/10 queries have top result topically relevant.")
    print("=" * 80)


if __name__ == "__main__":
    run_validation()
