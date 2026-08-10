"""Representation extraction from GPT-J via NNsight/NDIF.

REMOTE-dependent: every function here runs a remote trace on NDIF. The patterns
(mean-pool / last-token at a layer, cached by prompt) are the ones validated in
the demo scripts (E-007). Confirm on first run in a new environment.
"""

import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

from . import config

_model: "LanguageModel | None" = None
_cache: dict[tuple[str, int, str], torch.Tensor] = {}


def get_model() -> LanguageModel:
    """Load GPT-J once, with the NDIF API key from the environment."""
    global _model
    if _model is None:
        CONFIG.set_default_api_key(config.api_key())
        _model = LanguageModel(config.MODEL_ID)
    return _model


def rep(prompt: str, layer: int = config.DEFAULT_LAYER, how: str = "mean") -> torch.Tensor:
    """Residual-stream representation of `prompt` at `layer`.

    how="mean" → mean-pool over tokens (avoids the last-token attention sink,
                 our 03/12 finding); how="last" → last-token residual.
    Cached by (prompt, layer, how) so shared prompts (e.g. anchors) reuse traces.
    """
    ckey = (prompt, layer, how)
    if ckey in _cache:
        return _cache[ckey]
    model = get_model()
    with model.trace(prompt, remote=True):                        # type: ignore[union-attr]
        resid = model.transformer.h[layer].output[0][0]           # type: ignore[index]  [seq, d]
        vec = (resid.mean(dim=0) if how == "mean" else resid[-1]).save()
    _cache[ckey] = vec
    return vec


def clear_cache() -> None:
    _cache.clear()
