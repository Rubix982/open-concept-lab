"""Re-embed the 10K corpus with SPECTER2 adhoc_query adapter for concept search."""
import os, sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from pathlib import Path
from src.gcn_citation.pipeline.embedder import embed_papers

df = pd.read_parquet("data/pipeline/arxiv_10k.parquet")

# Back up the old proximity embeddings
import shutil

old_path = Path("data/pipeline/embeddings_10k.npy")
backup_path = Path("data/pipeline/embeddings_10k_proximity.npy")
if old_path.exists() and not backup_path.exists():
    shutil.copy2(old_path, backup_path)
    print(f"Backed up proximity embeddings to {backup_path}")

# Re-embed with adhoc_query adapter
embeddings = embed_papers(
    papers=df,
    output_path=Path("data/pipeline/embeddings_10k.npy"),
    checkpoint_path=Path("data/pipeline/embeddings_10k_adhoc_checkpoint.json"),
    api_key=None,
    device="mps",
    batch_size=32,
    adapter_name="allenai/specter2_adhoc_query",
)

print(f"Re-embedding complete: {embeddings.shape}")
sample_norm = np.linalg.norm(embeddings[0])
print(f"Sample L2 norm: {sample_norm:.4f}")
