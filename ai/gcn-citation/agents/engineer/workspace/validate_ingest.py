"""E-014 validation: verify L1 paper ingest pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pandas as pd

from src.knowledge.ingest import ingest_papers
from src.knowledge.schema import get_connection

TEST_DB = Path("/tmp/test_ingest.db")
PARQUET = Path("data/pipeline/arxiv_10k.parquet")
EMBEDDINGS = Path("data/pipeline/embeddings_10k.npy")

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


# Clean up
if TEST_DB.exists():
    TEST_DB.unlink()

df = pd.read_parquet(PARQUET)
embeddings = np.load(str(EMBEDDINGS), mmap_mode="r")
sample = df.head(50).reset_index(drop=True)

# --- Test 1: ingest 50 papers ---
result = ingest_papers(sample, EMBEDDINGS, TEST_DB, batch_size=20)
record("ingested_50_papers", result["ingested"] == 50, f"ingested={result['ingested']}")

# --- Test 2: chunks table has exactly 50 rows ---
conn = get_connection(TEST_DB)
count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
record("chunks_count_50", count == 50, f"got {count}")

# --- Test 3: all arxiv_ids unique ---
unique = conn.execute("SELECT COUNT(DISTINCT arxiv_id) FROM chunks").fetchone()[0]
record("arxiv_ids_unique", unique == 50, f"unique={unique}")

# --- Test 4: chunk_id pattern ---
bad = conn.execute(
    "SELECT COUNT(*) FROM chunks WHERE chunk_id != arxiv_id || '_abstract'"
).fetchone()[0]
record("chunk_id_pattern", bad == 0, f"bad patterns={bad}")

# --- Test 5: embedding_row in range ---
max_row = conn.execute("SELECT MAX(embedding_row) FROM chunks").fetchone()[0]
record(
    "embedding_row_in_range",
    max_row < len(embeddings),
    f"max_row={max_row}, n_embeddings={len(embeddings)}",
)

# --- Test 6: no null text ---
nulls = conn.execute(
    "SELECT COUNT(*) FROM chunks WHERE text IS NULL OR text = ''"
).fetchone()[0]
record("no_null_text", nulls == 0, f"nulls={nulls}")
conn.close()

# --- Test 7: resume — skip_existing=True ---
result2 = ingest_papers(sample, EMBEDDINGS, TEST_DB, skip_existing=True)
record(
    "resume_skips_all",
    result2["skipped"] == 50 and result2["ingested"] == 0,
    f"skipped={result2['skipped']}, ingested={result2['ingested']}",
)

# --- Test 8: total count unchanged after resume ---
conn = get_connection(TEST_DB)
count2 = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
record("count_unchanged_after_resume", count2 == 50, f"got {count2}")
conn.close()

# Cleanup
TEST_DB.unlink()

print()
passed = sum(1 for _, ok, _ in results if ok)
print(f"Results: {passed}/{len(results)} PASS")
if passed == len(results):
    print("ALL PASS")
