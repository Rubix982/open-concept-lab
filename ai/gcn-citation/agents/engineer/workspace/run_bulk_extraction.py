"""E-018: Bulk L2 extraction on 500 filtered papers.

Run this script to populate data/knowledge/knowledge.db with L2 summaries
for the quality-filtered corpus. Expected runtime: ~52 minutes.

Usage:
    source .venv/bin/activate
    KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 \\
        python agents/engineer/workspace/run_bulk_extraction.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pandas as pd

from src.knowledge.filter_corpus import filter_quality_papers, corpus_stats
from src.knowledge.ingest import ingest_papers
from src.knowledge.extract_l2 import extract_batch

DB_PATH = Path("data/knowledge/knowledge.db")
PARQUET = Path("data/pipeline/arxiv_10k.parquet")
EMBEDDINGS = Path("data/pipeline/embeddings_10k.npy")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("E-018: Bulk L2 extraction — 500 papers")
print("=" * 60)

# Step 1 — load and filter
print("\n[1/4] Loading and filtering corpus...")
df = pd.read_parquet(PARQUET)
filtered = filter_quality_papers(df, max_papers=500, seed=42)
stats = corpus_stats(filtered)
print(f"  Total after filter: {stats['total']}")
print(f"  Year range: {stats['year_range']}")
print(f"  Top categories: {stats['top_categories']}")
print(f"  Avg abstract words: {stats['avg_abstract_words']}")

# Step 2 — L1 ingest
print("\n[2/4] Ingesting L1 chunks...")
t0 = time.time()
l1_result = ingest_papers(filtered, EMBEDDINGS, DB_PATH)
print(
    f"  ingested={l1_result['ingested']}, skipped={l1_result['skipped']}, "
    f"errors={l1_result['errors']} ({time.time()-t0:.1f}s)"
)

# Step 3 — L2 extraction (the slow part)
print(
    f"\n[3/4] Extracting L2 summaries (~{stats['total'] * 6.3 / 60:.0f} min estimated)..."
)
t0 = time.time()
l2_result = extract_batch(filtered, DB_PATH)
elapsed = time.time() - t0
print(
    f"  extracted={l2_result['extracted']}, skipped={l2_result['skipped']}, "
    f"errors={l2_result['errors']} ({elapsed:.0f}s, "
    f"{elapsed/max(l2_result['extracted'],1):.1f}s/paper)"
)

# Step 4 — summary
print("\n[4/4] Final counts:")
from src.knowledge.schema import get_connection

conn = get_connection(DB_PATH)
n_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
n_summaries = conn.execute("SELECT COUNT(*) FROM paper_summaries").fetchone()[0]
conn.close()
print(f"  chunks: {n_chunks}")
print(f"  paper_summaries: {n_summaries}")

print("\n" + "=" * 60)
print("DONE. Run E-016 query interface to search the corpus.")
print("=" * 60)
