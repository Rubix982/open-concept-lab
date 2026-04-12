"""E-011 validation: verify arxiv_10k.parquet and embeddings_10k.npy."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

PARQUET_PATH = Path("data/pipeline/arxiv_10k.parquet")
NPY_PATH = Path("data/pipeline/embeddings_10k.npy")

results = []

# Check 1: parquet exists and has 10K rows
df = pd.read_parquet(PARQUET_PATH)
ok = len(df) == 10_000
results.append(("parquet rows == 10000", ok, f"got {len(df)}"))

# Check 2: required columns
required = {
    "arxiv_id",
    "title",
    "abstract",
    "categories",
    "primary_category",
    "is_interdisciplinary",
    "year",
    "month",
}
missing = required - set(df.columns)
results.append(("required columns present", not missing, f"missing: {missing}"))

# Check 3: no null arxiv_ids
ok = df["arxiv_id"].notna().all()
results.append(("no null arxiv_ids", ok, ""))

# Check 4: embedding shape and dtype
emb = np.load(NPY_PATH, mmap_mode="r")
ok = emb.shape == (10_000, 768)
results.append(("embeddings shape (10000, 768)", ok, f"got {emb.shape}"))
ok = emb.dtype == np.float32
results.append(("embeddings dtype float32", ok, f"got {emb.dtype}"))

# Check 5: L2 normalised
sample = [0, 100, 500, 1000, 5000, 9999]
norms = [np.linalg.norm(emb[i]) for i in sample]
ok = all(0.99 < n < 1.01 for n in norms)
results.append(
    ("L2 normalised (norm ≈ 1.0)", ok, f"norms: {[f'{n:.4f}' for n in norms]}")
)

# Check 6: categories are list-like (list or ndarray after parquet round-trip)
ok = all(
    hasattr(v, "__iter__") and not isinstance(v, str)
    for v in df["categories"].head(100)
)
results.append(("categories are list-like", ok, ""))

# Print
print("=" * 55)
print("validate_10k_data.py")
print("=" * 55)
for name, passed, detail in results:
    status = "[PASS]" if passed else "[FAIL]"
    suffix = f" — {detail}" if detail else ""
    print(f"  {status} {name}{suffix}")

n_inter = int(df["is_interdisciplinary"].sum())
print(
    f"\n  Interdisciplinary papers: {n_inter} / {len(df)} ({100*n_inter/len(df):.1f}%)"
)
print(f"  Category sample: {df['primary_category'].value_counts().head(5).to_dict()}")

all_passed = all(p for _, p, _ in results)
print("=" * 55)
print("ALL PASS" if all_passed else "SOME FAILED")
