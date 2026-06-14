"""Sentence embeddings for claims (all-MiniLM-L6-v2, per R-002).

Uses `transformers` directly (not sentence-transformers, which transitively imports the
`datasets` package — broken under this venv's Python 3.14.0+; see [E-002]). We replicate
sentence-transformers' all-MiniLM-L6-v2: mean-pool the token embeddings over the
attention mask, then L2-normalize. Lazy-loaded singleton.
"""

from __future__ import annotations

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from ..extraction.model import get_device

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

_tok: AutoTokenizer | None = None
_model: AutoModel | None = None
_device: torch.device | None = None


def _load() -> tuple[AutoTokenizer, AutoModel, torch.device]:
    global _tok, _model, _device
    if _model is None:
        _device = get_device()
        _tok = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = AutoModel.from_pretrained(_MODEL_NAME).to(_device).eval()
    return _tok, _model, _device


def _mean_pool(last_hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    mask_f = mask.unsqueeze(-1).float()
    summed = (last_hidden * mask_f).sum(dim=1)
    counts = mask_f.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def embed(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Return an (n, 384) float32 array of L2-normalized embeddings."""
    tok, model, device = _load()
    chunks: list[np.ndarray] = []
    for i in range(0, len(texts), batch_size):
        enc = tok(
            texts[i : i + batch_size],
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            out = model(**enc)
        emb = _mean_pool(out.last_hidden_state, enc["attention_mask"])
        emb = torch.nn.functional.normalize(emb, p=2, dim=1)
        chunks.append(emb.cpu().numpy())
    return np.concatenate(chunks, axis=0).astype(np.float32)
