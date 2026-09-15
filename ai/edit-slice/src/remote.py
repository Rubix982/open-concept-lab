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

import contextlib
import io
import logging
import os
import time
from typing import Final

import torch
from nnsight import CONFIG, LanguageModel

MAX_ATTEMPTS: Final[int] = 8
BACKOFF_S: Final[float] = 5.0

#: Transport-layer failures are retried; anything else propagates. Classifying by
#: exact type name was a bug — `httpx.ConnectTimeout` is neither `ConnectionError`
#: nor `TimeoutError` by name, so it escaped and killed a 165-item run at 28.
#: Classify by originating module (every network client we go through) plus a name
#: pattern, so new transport exceptions are caught by default rather than by luck.
_TRANSPORT_MODULES: Final[tuple[str, ...]] = (
    "httpx", "httpcore", "socketio", "engineio", "websocket", "websockets",
    "urllib3", "requests", "ssl", "socket",
)
_TRANSPORT_NAMES: Final[tuple[str, ...]] = (
    "Timeout", "Connection", "Protocol", "Handshake", "Disconnect", "Closed",
    "RemoteDisconnected", "IncompleteRead",
)


def _is_oom(exc: BaseException) -> bool:
    """NDIF surfaces a remote CUDA OOM as a generic exception carrying the text."""
    text = f"{type(exc).__name__} {exc}"
    return "OutOfMemory" in text or "out of memory" in text.lower()


def _is_transport_error(exc: BaseException) -> bool:
    module = (type(exc).__module__ or "").split(".")[0]
    if module in _TRANSPORT_MODULES:
        return True
    if any(tag in type(exc).__name__ for tag in _TRANSPORT_NAMES):
        return True
    # `score_batch` performs no file I/O, so a bare OSError raised inside it can
    # only have come from the socket layer. Kept explicit rather than implied.
    return isinstance(exc, OSError)

DEFAULT_MODEL: Final[str] = "meta-llama/Llama-3.1-70B"

#: Retries and OOM splits used to happen silently, so a degrading run looked
#: identical to a healthy one. They are WARNINGs now: nothing is wrong enough to
#: stop, and everything is worth knowing afterwards. Callers that run `logs.setup`
#: get these in their file; callers that do not lose nothing they had before.
log: Final[logging.Logger] = logging.getLogger("remote")


@contextlib.contextmanager
def _quiet_stdout():
    """Swallow nnsight's progress spinners, which are stdout, not logging.

    They are carriage-return animations and download bars: 262 of 266 lines in a
    real run's log, which makes the record complete and unreadable at the same
    time. Discarding a spinner is not discarding output — our own logging goes to
    stderr and the log file, and exceptions still propagate. This is what makes the
    kept log analysable rather than merely large.
    """
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        yield


def connect(model_name: str = DEFAULT_MODEL) -> LanguageModel:
    key = os.environ.get("NNSIGHT_API_KEY")
    if not key:
        raise RuntimeError("NNSIGHT_API_KEY not set — get one from login.ndif.us")
    CONFIG.set_default_api_key(key)
    return LanguageModel(model_name)


def _encode_pairs(model: LanguageModel, pairs: list[tuple[str, str]]
                  ) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
    """Right-padded batch of (prompt, continuation) pairs, plus a continuation mask.

    Generalised from a single prompt to arbitrary pairs so that unrelated prompts
    can share one remote round trip. That is the whole cost model here: NDIF
    compute is sub-second while each trace costs ~10s of queue and transfer, so
    round trips — not FLOPs — are the budget.
    """
    tok = model.tokenizer
    cache: dict[str, torch.Tensor] = {}
    rows, masks, lengths = [], [], []
    for prompt, cont in pairs:
        if prompt not in cache:
            cache[prompt] = tok(prompt, return_tensors="pt").input_ids[0]
        p_ids = cache[prompt]
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


def score_pairs(model: LanguageModel, pairs: list[tuple[str, str]],
                *, max_rows: int = 200,
                edit: tuple[int, torch.Tensor, torch.Tensor] | None = None
                ) -> list[float]:
    """Mean log P(continuation | prompt) for arbitrary pairs, in ONE remote call.

    `edit` is an optional `(layer, k_star, delta_v)` rank-one update, applied inline
    inside this function's own trace. It has to be inline: nnsight builds its graph
    from the source of the frame that entered `model.trace`, so an intervention
    written in a helper called from the caller's trace is silently dropped — see
    `edit.APPLY_IDIOM`. Putting the trace HERE is what makes it expressible without
    duplicating the OOM-splitting and retry logic below.

    NDIF's websocket drops intermittently under load — a run of 165 items reliably
    hits at least one `socketio ConnectionError`. Transport failures are retried
    with linear backoff; anything else propagates, because silently retrying a real
    bug would hide it.
    """
    # NDIF hosts are shared and enforce a per-process memory budget, so an
    # oversized batch fails for reasons unrelated to correctness. Split rather
    # than fail: round trips still amortise far better than one call per pair.
    if len(pairs) > max_rows:
        # BALANCED chunks, not greedy ones. Greedy splitting of 224 rows gives
        # 200 + 24, and that 24-row tail costs a full round trip — ~4s of queue and
        # transfer to carry a tenth of a batch. Round trips are the budget here, so
        # the same two calls carry 112 rows each instead, at no extra cost and with
        # more headroom against the host's memory ceiling.
        n_chunks = -(-len(pairs) // max_rows)
        size = -(-len(pairs) // n_chunks)
        log.debug("splitting %d pairs into %d chunks of <=%d (cap %d)",
                  len(pairs), n_chunks, size, max_rows)
        out: list[float] = []
        for i in range(0, len(pairs), size):
            out += score_pairs(model, pairs[i : i + size], max_rows=max_rows, edit=edit)
        return out

    ids, mask, lengths = _encode_pairs(model, pairs)
    last: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            t0 = time.monotonic()
            # Plain Python conditionals run at graph-BUILD time, not as proxy
            # branches, so this is safe inside a trace.
            lay = edit[0] if edit is not None else None
            ks_cpu = edit[1] if edit is not None else None
            dv_cpu = edit[2] if edit is not None else None
            with _quiet_stdout(), model.trace(ids, remote=True):
                if lay is not None:
                    dp = model.model.layers[lay].mlp.down_proj
                    kk = dp.input
                    ks = ks_cpu.to(kk.device, kk.dtype)
                    dp.output = dp.output + ((kk @ ks) / (ks @ ks)).unsqueeze(-1) \
                                            * dv_cpu.to(kk.device, kk.dtype)
                # log P(t) = logit[t] - logsumexp(logits). Computing it this way
                # avoids materialising a second [B, T, V] tensor, which is what
                # torch.log_softmax does and what OOM'd the shared GPU at batch 400.
                # Only [B, T] intermediates are allocated.
                logits = model.lm_head.output[:, :-1]
                targets = ids[:, 1:].to(logits.device)
                chosen = logits.gather(-1, targets.unsqueeze(-1)).squeeze(-1).float()
                denom = torch.logsumexp(logits, dim=-1).float()
                summed = ((chosen - denom) * mask[:, 1:].to(logits.device)).sum(-1).save()
            # `.tolist()` is where nnsight actually FETCHES the saved value, and it
            # sits outside the `with` block — so the first version of this redirect
            # caught the spinner and missed every "Downloading:" bar. Materialise
            # inside the suppressed region, not after it.
            with _quiet_stdout():
                values = summed.tolist()
            # The spinner we suppress carried exactly one fact worth keeping: how
            # long the round trip took. Round trips, not FLOPs, are this project's
            # budget, so it is recorded structurally instead of as animation.
            log.debug("trace ok: %d rows, %d tok, %.1fs",
                      len(pairs), int(mask.sum().item()), time.monotonic() - t0)
            return [s / n for s, n in zip(values, lengths)]
        except Exception as exc:  # noqa: BLE001 — narrowed below
            if _is_oom(exc):
                # Deployments differ in per-process budget, and Llama's 128k vocab
                # costs ~2.5x GPT-J's per row. Rather than tune a constant per
                # model, halve and recurse until it fits.
                if len(pairs) == 1:
                    log.error("OOM on a single pair — cannot split further")
                    raise
                mid = len(pairs) // 2
                log.warning("remote OOM at %d pairs; halving to %d + %d",
                            len(pairs), mid, len(pairs) - mid)
                return (score_pairs(model, pairs[:mid], max_rows=mid)
                        + score_pairs(model, pairs[mid:], max_rows=len(pairs) - mid))
            if not _is_transport_error(exc):
                log.error("non-transport failure, not retrying: %s: %s",
                          type(exc).__name__, exc)
                raise
            last = exc
            log.warning("transport failure (%s) on attempt %d/%d; retrying in %.0fs",
                        type(exc).__name__, attempt + 1, MAX_ATTEMPTS,
                        BACKOFF_S * (attempt + 1))
            time.sleep(BACKOFF_S * (attempt + 1))
    log.error("NDIF unreachable after %d attempts; last error %s",
              MAX_ATTEMPTS, type(last).__name__ if last else "unknown")
    raise RuntimeError(f"NDIF unreachable after {MAX_ATTEMPTS} attempts") from last


def score_batch(model: LanguageModel, prompt: str, continuations: list[str]) -> list[float]:
    """Score many continuations against one prompt. Thin wrapper over score_pairs."""
    return score_pairs(model, [(prompt, c) for c in continuations])


def rank_among(model: LanguageModel, prompt: str, true_answer: str,
               distractors: list[str]) -> tuple[int, int, str]:
    """(rank of true_answer, n_candidates, best candidate) — one remote call."""
    candidates = [true_answer, *[d for d in distractors if d != true_answer]]
    scores = score_batch(model, prompt, candidates)
    order = [c for c, _ in sorted(zip(candidates, scores), key=lambda kv: -kv[1])]
    return order.index(true_answer) + 1, len(order), order[0]
