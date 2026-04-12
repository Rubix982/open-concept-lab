"""
R-007: Embedding model evaluation for concept/idea-level search.
Tests SPECTER2 adhoc_query adapter and BGE-small on 500 paper contributions.
"""
import os
import sys
import time
import json
import sqlite3
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
sys.path.insert(0, ".")

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

# ─── Load 500 paper contributions from DB ──────────────────────────────────
conn = sqlite3.connect("data/knowledge/knowledge.db")
rows = conn.execute(
    "SELECT arxiv_id, contribution, domain_tags FROM paper_summaries WHERE contribution IS NOT NULL"
).fetchall()
conn.close()

texts = [r[1] for r in rows]
arxiv_ids = [r[0] for r in rows]
domain_tags = [json.loads(r[2] or "[]") for r in rows]
print(f"Loaded {len(texts)} paper contributions")

# ─── Load L3 claims from DB ─────────────────────────────────────────────────
conn = sqlite3.connect("data/knowledge/knowledge.db")
claim_rows = conn.execute(
    "SELECT claim_id, assertion, claim_type FROM claims LIMIT 20"
).fetchall()
conn.close()
claim_texts = [r[1] for r in claim_rows]
claim_ids = [r[0] for r in claim_rows]
claim_types = [r[2] for r in claim_rows]
print(f"Loaded {len(claim_texts)} claims for cluster test")

results = {}

# ══════════════════════════════════════════════════════════════════════════════
# MODEL 1: SPECTER2 adhoc_query adapter
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("MODEL 1: SPECTER2 adhoc_query adapter")
print("=" * 60)

try:
    import torch
    import adapters
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model_sp = adapters.AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model_sp.load_adapter("allenai/specter2_adhoc_query", source="hf", set_active=True)
    model_sp.eval()
    device = torch.device("mps")
    model_sp = model_sp.to(device)
    print("SPECTER2 adhoc_query loaded on MPS")

    def embed_specter(texts_in, batch_size=32):
        all_vecs = []
        for i in range(0, len(texts_in), batch_size):
            batch = texts_in[i : i + batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
                return_token_type_ids=False,
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.no_grad():
                out = model_sp(**enc)
            vecs = out.last_hidden_state[:, 0, :].cpu().float().numpy()
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            all_vecs.append(vecs / np.maximum(norms, 1e-12))
        return np.vstack(all_vecs)

    # Embed 500 papers (timed)
    t0 = time.time()
    paper_vecs_sp = embed_specter(texts)
    t_papers = time.time() - t0
    ms_per_paper = (t_papers / len(texts)) * 1000

    print(
        f"Embedded {len(texts)} papers in {t_papers:.1f}s ({ms_per_paper:.1f}ms/paper)"
    )

    # Embed queries
    query_vecs_sp = embed_specter(QUERIES)

    # Score distribution check
    scores_all = paper_vecs_sp @ query_vecs_sp.T  # (500, 10)
    print(f"Score distribution across all queries:")
    print(
        f"  min={scores_all.min():.4f}  max={scores_all.max():.4f}  mean={scores_all.mean():.4f}  std={scores_all.std():.4f}"
    )

    # Top-5 results per query
    sp_query_results = []
    total_relevance = 0
    print("\nTop-3 results per query:")
    for qi, query in enumerate(QUERIES):
        sims = paper_vecs_sp @ query_vecs_sp[qi]
        top5_idx = np.argsort(sims)[::-1][:5]
        top3 = top5_idx[:3]
        print(f"\n  Q{qi+1}: '{query}'")
        hits = []
        for rank, idx in enumerate(top3):
            entry = {
                "rank": rank + 1,
                "arxiv_id": arxiv_ids[idx],
                "contribution": texts[idx][:100],
                "domain_tags": domain_tags[idx],
                "score": float(sims[idx]),
            }
            hits.append(entry)
            print(
                f"    [{rank+1}] score={sims[idx]:.4f} {arxiv_ids[idx]}: {texts[idx][:80]}"
            )
            print(f"         tags: {domain_tags[idx]}")
        sp_query_results.append({"query": query, "hits": hits})

    # Claim embedding test
    claim_vecs_sp = embed_specter(claim_texts)
    print(f"\nClaim-to-claim cosine matrix (first 5 claims):")
    claim_sims = claim_vecs_sp[:5] @ claim_vecs_sp[:5].T
    for i in range(5):
        print(
            f"  claim[{i}] ({claim_types[i]}): "
            + " ".join([f"{claim_sims[i,j]:.3f}" for j in range(5)])
        )

    results["specter2_adhoc"] = {
        "status": "success",
        "ms_per_paper": round(ms_per_paper, 2),
        "score_stats": {
            "min": float(scores_all.min()),
            "max": float(scores_all.max()),
            "mean": float(scores_all.mean()),
            "std": float(scores_all.std()),
        },
        "query_results": sp_query_results,
    }
    print(f"\nSPECTER2 adhoc_query: {ms_per_paper:.1f}ms/paper on MPS")

    # Free model memory
    del model_sp
    torch.mps.empty_cache()

except Exception as e:
    print(f"SPECTER2 adhoc_query FAILED: {e}")
    results["specter2_adhoc"] = {"status": "failed", "error": str(e)}

# ══════════════════════════════════════════════════════════════════════════════
# MODEL 2: BGE-small-en-v1.5
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("MODEL 2: BAAI/bge-small-en-v1.5")
print("=" * 60)

try:
    from sentence_transformers import SentenceTransformer

    bge = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print("BGE-small loaded")

    # Embed papers (timed)
    t0 = time.time()
    paper_vecs_bge = bge.encode(
        texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True
    )
    t_papers_bge = time.time() - t0
    ms_per_paper_bge = (t_papers_bge / len(texts)) * 1000

    print(
        f"Embedded {len(texts)} papers in {t_papers_bge:.1f}s ({ms_per_paper_bge:.1f}ms/paper)"
    )

    # BGE recommends query prefix
    query_texts_bge = [f"Represent this sentence: {q}" for q in QUERIES]
    query_vecs_bge = bge.encode(query_texts_bge, normalize_embeddings=True)

    scores_all_bge = paper_vecs_bge @ query_vecs_bge.T
    print(f"Score distribution across all queries:")
    print(
        f"  min={scores_all_bge.min():.4f}  max={scores_all_bge.max():.4f}  mean={scores_all_bge.mean():.4f}  std={scores_all_bge.std():.4f}"
    )

    bge_query_results = []
    print("\nTop-3 results per query:")
    for qi, query in enumerate(QUERIES):
        sims = paper_vecs_bge @ query_vecs_bge[qi]
        top5_idx = np.argsort(sims)[::-1][:5]
        top3 = top5_idx[:3]
        print(f"\n  Q{qi+1}: '{query}'")
        hits = []
        for rank, idx in enumerate(top3):
            entry = {
                "rank": rank + 1,
                "arxiv_id": arxiv_ids[idx],
                "contribution": texts[idx][:100],
                "domain_tags": domain_tags[idx],
                "score": float(sims[idx]),
            }
            hits.append(entry)
            print(
                f"    [{rank+1}] score={sims[idx]:.4f} {arxiv_ids[idx]}: {texts[idx][:80]}"
            )
            print(f"         tags: {domain_tags[idx]}")
        bge_query_results.append({"query": query, "hits": hits})

    # Claim embedding
    claim_texts_bge = [f"Represent this sentence: {c}" for c in claim_texts]
    claim_vecs_bge = bge.encode(claim_texts_bge, normalize_embeddings=True)
    print(f"\nClaim-to-claim cosine matrix (first 5 claims):")
    claim_sims_bge = claim_vecs_bge[:5] @ claim_vecs_bge[:5].T
    for i in range(5):
        print(
            f"  claim[{i}] ({claim_types[i]}): "
            + " ".join([f"{claim_sims_bge[i,j]:.3f}" for j in range(5)])
        )

    results["bge_small"] = {
        "status": "success",
        "ms_per_paper": round(ms_per_paper_bge, 2),
        "score_stats": {
            "min": float(scores_all_bge.min()),
            "max": float(scores_all_bge.max()),
            "mean": float(scores_all_bge.mean()),
            "std": float(scores_all_bge.std()),
        },
        "query_results": bge_query_results,
    }
    print(f"\nBGE-small: {ms_per_paper_bge:.1f}ms/paper")

except Exception as e:
    print(f"BGE-small FAILED: {e}")
    results["bge_small"] = {"status": "failed", "error": str(e)}

# ══════════════════════════════════════════════════════════════════════════════
# Save results
# ══════════════════════════════════════════════════════════════════════════════
results["metadata"] = {
    "num_papers": len(texts),
    "num_claims": len(claim_texts),
    "queries": QUERIES,
    "date": "2026-03-29",
}

out_path = "agents/researcher/findings/r007_embedding_eval.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {out_path}")
print("Done.")
