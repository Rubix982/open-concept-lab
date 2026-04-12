"""E-011: Download 10K arXiv papers via HuggingFace streaming and embed with SPECTER2."""

from __future__ import annotations

import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

TARGET_CATEGORIES = {"cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"}
MAX_PAPERS = 10_000
OUTPUT_DIR = Path("data/pipeline")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_PATH = OUTPUT_DIR / "arxiv_10k.parquet"
EMBED_PATH = OUTPUT_DIR / "embeddings_10k.npy"
CHECKPOINT_PATH = OUTPUT_DIR / "embeddings_10k_checkpoint.json"


def download_papers() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        print(
            f"[E-011] Parquet already exists at {PARQUET_PATH}, loading...", flush=True
        )
        return pd.read_parquet(PARQUET_PATH)

    print("[E-011] Streaming arXiv metadata from HuggingFace...", flush=True)
    from datasets import load_dataset

    ds = load_dataset(
        "librarian-bots/arxiv-metadata-snapshot", split="train", streaming=True
    )

    records = []
    for record in ds:
        raw_cats = record.get("categories", "") or ""
        categories = [c.strip() for c in raw_cats.split() if c.strip()]
        if not any(c in TARGET_CATEGORIES for c in categories):
            continue

        update_date = record.get("update_date")
        try:
            if hasattr(update_date, "year"):  # datetime object
                year, month = update_date.year, update_date.month
            else:
                update_date = str(update_date) if update_date else ""
                year = int(update_date[:4])
                month = int(update_date[5:7])
        except (ValueError, IndexError, AttributeError):
            year, month = 0, 0

        records.append(
            {
                "arxiv_id": record.get("id", ""),
                "title": (record.get("title", "") or "").strip(),
                "abstract": (record.get("abstract", "") or "").strip(),
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "is_interdisciplinary": len(categories) >= 2,
                "year": year,
                "month": month,
            }
        )

        if len(records) % 1000 == 0:
            print(
                f"[E-011] Collected {len(records)} / {MAX_PAPERS} papers...", flush=True
            )

        if len(records) >= MAX_PAPERS:
            break

    df = pd.DataFrame(records)
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"[E-011] Saved {len(df)} papers to {PARQUET_PATH}", flush=True)
    return df


def embed_papers(df: pd.DataFrame) -> np.ndarray:
    from src.gcn_citation.pipeline.embedder import embed_papers as _embed

    print("[E-011] Starting SPECTER2 embedding (local MPS inference)...", flush=True)
    embeddings = _embed(
        papers=df,
        output_path=EMBED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        api_key=None,
        cache_dir=None,
        batch_size=32,
        device="mps",
        model_name="allenai/specter2_base",
    )
    print(f"[E-011] Embedding complete. Shape: {embeddings.shape}", flush=True)
    return embeddings


if __name__ == "__main__":
    df = download_papers()
    print(f"[E-011] Papers loaded: {len(df)}", flush=True)
    embeddings = embed_papers(df)
    sample_norm = np.linalg.norm(embeddings[0])
    print(f"[E-011] Sample L2 norm (row 0): {sample_norm:.4f}", flush=True)
    print("[E-011] Done.", flush=True)
