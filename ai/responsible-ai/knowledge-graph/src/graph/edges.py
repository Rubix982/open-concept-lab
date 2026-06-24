"""NLI-based edge typing for claim pairs.

Uses `transformers` directly with a WordPiece MNLI model
(`typeform/distilbert-base-uncased-mnli`) — chosen over cross-encoder/nli-deberta-v3
because DeBERTa-v3 needs `sentencepiece`, which is absent in this venv, and
sentence-transformers transitively imports the broken `datasets` package (see [E-003]).

Maps NLI verdict on a (premise, hypothesis) claim pair to our edge type:
  entailment    -> SUPPORTS
  contradiction -> CONTRADICTS
  neutral       -> RELATED   (kept only because embedding similarity was already high)

Reads the model's own id2label so logit order is not hard-coded.
"""

from __future__ import annotations

from typing import Any, cast
import numpy as np
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

from ..extraction.model import get_device

_MODEL_NAME = "typeform/distilbert-base-uncased-mnli"

_NLI_TO_EDGE: dict[str, str] = {
    "entailment": "SUPPORTS",
    "contradiction": "CONTRADICTS",
    "neutral": "RELATED",
}

_tok: PreTrainedTokenizerBase | None = None
_model: PreTrainedModel | None = None
_device: torch.device | None = None
_id2label: dict[int, str] | None = None


def _load() -> tuple[PreTrainedTokenizerBase | None, PreTrainedModel | None, torch.device | None]:
    global _tok, _model, _device, _id2label
    if _model is None:
        _device = get_device()
        _tok = cast(PreTrainedTokenizerBase, AutoTokenizer.from_pretrained(_MODEL_NAME))
        model_cls = cast(Any, AutoModelForSequenceClassification)
        loaded_model = cast(
            PreTrainedModel,
            model_cls.from_pretrained(_MODEL_NAME),
        )
        cast(Any, loaded_model).to(device=_device)
        loaded_model.eval()
        _model = loaded_model
        raw = cast(Any, _model.config).id2label
        if raw is None:
            _id2label = {}
        else:
            _id2label = {int(k): str(v).lower() for k, v in raw.items()}
    return _tok, _model, _device


def type_pairs(
    pairs: list[tuple[str, str]], batch_size: int = 32
) -> list[tuple[str, float]]:
    """For each (premise, hypothesis) pair, return (edge_type, probability)."""
    if not pairs:
        return []
    tok, model, device = _load()

    if tok is None or model is None or device is None:
        raise RuntimeError("Failed to load NLI model")

    assert _id2label is not None
    out: list[tuple[str, float]] = []
    for i in range(0, len(pairs), batch_size):
        chunk = pairs[i : i + batch_size]
        enc = tok(
            [p for p, _ in chunk],
            [h for _, h in chunk],
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()
        for row in probs:
            idx = int(np.argmax(row))
            nli_label = _id2label.get(idx, "neutral")
            out.append((_NLI_TO_EDGE.get(nli_label, "RELATED"), float(row[idx])))
    return out
