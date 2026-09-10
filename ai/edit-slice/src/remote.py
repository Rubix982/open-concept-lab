"""NDIF-backed scoring for models too large to hold locally.

`probing.py` runs models locally. This runs them on NDIF via nnsight, which has a
different cost shape: compute is trivial (sub-second on Llama-70B) but each remote
trace carries ~10-15s of queue and transfer. So the unit of work is a BATCH — all
candidate continuations for an item are scored in one round trip, and the
log-probs are gathered remotely so only scalars come back over the wire, never a
128k-vocab logit tensor.

Requires NNSIGHT_API_KEY in the environment (from login.ndif.us).
"""

from __future__ import annotations

import os
import time
from typing import Final

import torch
from nnsight import CONFIG, LanguageModel

MAX_ATTEMPTS: Final[int] = 5
BACKOFF_S: Final[float] = 4.0

DEFAULT_MODEL: Final[str] = "meta-llama/Llama-3.1-70B"


def connect(model_name: str = DEFAULT_MODEL) -> LanguageModel:
    key = os.environ.get("NNSIGHT_API_KEY")
    if not key:
        raise RuntimeError("NNSIGHT_API_KEY not set — get one from login.ndif.us")
    CONFIG.set_default_api_key(key)
    return LanguageModel(model_name)


def _encode(model: LanguageModel, prompt: str, continuations: list[str]
            ) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
    """Right-padded batch of prompt+continuation, plus a mask over continuation tokens."""
    tok = model.tokenizer
    p_ids = tok(prompt, return_tensors="pt").input_ids[0]
    rows, masks, lengths = [], [], []
    for cont in continuations:
        text = cont if cont.startswith(" ") else " " + cont
        c_ids = tok(text, return_tensors="pt", add_special_tokens=False).input_ids[0]
        rows.append(torch.cat([p_ids, c_ids]))
        m = torch.zeros(len(p_ids) + len(c_ids), dtype=torch.bool)
        m[len(p_ids):] = True
        masks.append(m)
        lengths.append(len(c_ids))
    width = max(len(r) for r in rows)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    ids = torch.full((len(rows), width), pad, dtype=torch.long)
    mask = torch.zeros((len(rows), width), dtype=torch.bool)
    for i, (r, m) in enumerate(zip(rows, masks)):
        ids[i, : len(r)] = r
        mask[i, : len(m)] = m
    return ids, mask, lengths


def score_batch(model: LanguageModel, prompt: str, continuations: list[str]) -> list[float]:
    """Mean log P(continuation | prompt) for each continuation, in ONE remote call.

    NDIF's websocket drops intermittently under load — a run of 165 items reliably
    hits at least one `socketio ConnectionError`. Transport failures are retried
    with linear backoff; anything else propagates, because silently retrying a real
    bug would hide it.
    """
    ids, mask, lengths = _encode(model, prompt, continuations)
    last: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with model.trace(ids, remote=True):
                logits = model.lm_head.output.float()
                logprobs = torch.log_softmax(logits[:, :-1], dim=-1)
                targets = ids[:, 1:].to(logprobs.device)
                gathered = logprobs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
                summed = (gathered * mask[:, 1:].to(gathered.device)).sum(-1).save()
            return [s / n for s, n in zip(summed.tolist(), lengths)]
        except Exception as exc:  # noqa: BLE001 — narrowed by name below
            if type(exc).__name__ not in {"ConnectionError", "TimeoutError", "OSError"}:
                raise
            last = exc
            time.sleep(BACKOFF_S * (attempt + 1))
    raise RuntimeError(f"NDIF unreachable after {MAX_ATTEMPTS} attempts") from last


def rank_among(model: LanguageModel, prompt: str, true_answer: str,
               distractors: list[str]) -> tuple[int, int, str]:
    """(rank of true_answer, n_candidates, best candidate) — one remote call."""
    candidates = [true_answer, *[d for d in distractors if d != true_answer]]
    scores = score_batch(model, prompt, candidates)
    order = [c for c, _ in sorted(zip(candidates, scores), key=lambda kv: -kv[1])]
    return order.index(true_answer) + 1, len(order), order[0]
