"""Representation extraction from GPT-J via NNsight/NDIF.

REMOTE-dependent: every function here runs a remote trace on NDIF. The patterns
(mean-pool / last-token at a layer, cached by prompt) are the ones validated in
the demo scripts (E-007). Confirm on first run in a new environment.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

from . import config

_model: "LanguageModel | None" = None
_cache: dict[tuple[str, int, str], torch.Tensor] = {}

MAX_RETRIES = 5
BACKOFF = 4.0     # seconds, exponential
CALL_TIMEOUT = 45  # hard wall-clock cap per trace — NDIF can HANG (not just error)

# ── disk checkpoint cache ──────────────────────────────────────────────────────
# NDIF is flaky; persist fetched vectors so a re-run resumes instead of re-fetching.
_DISK = config.RESULTS_DIR / "rep_cache.pt"


def load_disk_cache() -> int:
    """Load persisted reps into memory. Returns count loaded."""
    global _cache
    if _DISK.exists():
        try:
            _cache = torch.load(_DISK)
            return len(_cache)
        except Exception as e:  # noqa: BLE001
            print(f"    [disk cache unreadable, ignoring: {type(e).__name__}]")
    return 0


def save_disk_cache() -> None:
    _DISK.parent.mkdir(parents=True, exist_ok=True)
    torch.save(_cache, _DISK)


def cache_size() -> int:
    return len(_cache)


def _trace_with_retry(fn):
    """Run a trace-producing fn with a hard per-call TIMEOUT + retry/backoff.
    NDIF failures are transient AND can manifest as indefinite HANGS (a bare retry
    on exceptions never catches a hang) — so each attempt is bounded by
    CALL_TIMEOUT via a worker thread. Raises the last error if all retries fail."""
    last: "Exception | None" = None
    for attempt in range(MAX_RETRIES):
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(fn).result(timeout=CALL_TIMEOUT)
        except FutureTimeout:
            last = TimeoutError(f"NDIF trace hung > {CALL_TIMEOUT}s")
            reason = "HANG"
        except Exception as e:  # noqa: BLE001 — NDIF raises RemoteException et al.
            last = e
            reason = type(e).__name__
        if attempt < MAX_RETRIES - 1:
            wait = BACKOFF * (2 ** attempt)
            print(f"    [retry {attempt+1}/{MAX_RETRIES} in {wait:.0f}s: {reason}]", flush=True)
            time.sleep(wait)
    raise last  # type: ignore[misc]


def get_model() -> LanguageModel:
    """Load GPT-J once, with the NDIF API key from the environment."""
    global _model
    if _model is None:
        CONFIG.set_default_api_key(config.api_key())
        _model = LanguageModel(config.MODEL_ID)
    return _model


# ── Local transformers backend (no NDIF) ──────────────────────────────────────
_local_model = None
_local_tok = None


def _get_local():
    """Load the local transformers model once (output_hidden_states, MPS/CPU)."""
    global _local_model, _local_tok
    if _local_model is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        name = config.LOCAL_MODEL
        print(f"    loading local model {name} (one-time)...", flush=True)
        _local_tok = AutoTokenizer.from_pretrained(name)
        _local_model = AutoModelForCausalLM.from_pretrained(
            name, output_hidden_states=True, torch_dtype=torch.float32
        )
        dev = "mps" if torch.backends.mps.is_available() else "cpu"
        _local_model = _local_model.to(dev).eval()
        print(f"    local model ready on {dev} "
              f"({_local_model.config.n_layer} blocks)", flush=True)
    return _local_model, _local_tok


def _rep_local(prompt: str, layer: int, how: str) -> torch.Tensor:
    """Per-layer residual stream via transformers hidden_states.
    hidden_states[i]: i=0 embeddings, i=L output of block L-1 → we index [layer]
    (consistent across the sweep; not aligned 1:1 with NDIF block indexing)."""
    m, tok = _get_local()
    dev = next(m.parameters()).device
    ids = tok(prompt, return_tensors="pt").to(dev)
    with torch.no_grad():
        out = m(**ids)
    hs = out.hidden_states[layer][0]                              # [seq, d]
    vec = hs.mean(dim=0) if how == "mean" else hs[-1]
    return vec.detach().cpu().float()


def rep(prompt: str, layer: int = config.DEFAULT_LAYER, how: str = "mean") -> torch.Tensor:
    """Residual-stream representation of `prompt` at `layer`.

    how="mean" → mean-pool over tokens (avoids the last-token attention sink);
    how="last" → last-token residual. Cached by (prompt, layer, how).
    Backend selected by config.BACKEND ("local" transformers | "ndif" remote).
    """
    ckey = (prompt, layer, how)
    if ckey in _cache:
        return _cache[ckey]

    if config.BACKEND == "local":
        vec = _rep_local(prompt, layer, how)
    else:
        model = get_model()

        def _run():
            with model.trace(prompt, remote=True):                # type: ignore[union-attr]
                resid = model.transformer.h[layer].output[0][0]   # type: ignore[index]
                return (resid.mean(dim=0) if how == "mean" else resid[-1]).save()

        vec = _trace_with_retry(_run)

    _cache[ckey] = vec
    return vec


def probe_once(timeout: int = 20) -> bool:
    """Single bounded health check (no retries) — for the autolauncher watcher.
    Bypasses the cache so it actually hits NDIF."""
    model = get_model()

    def _run():
        with model.trace("Paris is the capital of", remote=True):   # type: ignore[union-attr]
            return model.transformer.h[15].output[0][0].mean(dim=0).save()  # type: ignore[index]

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            v = ex.submit(_run).result(timeout=timeout)
        return float(v.norm()) > 0
    except Exception:  # noqa: BLE001
        return False


def prewarm(prompt: str, layers: list[int], how: str = "mean") -> None:
    """Fetch ALL `layers` for `prompt` in ONE forward pass / trace (≈Nx cheaper
    than N separate rep() calls), populating the per-(prompt,layer,how) cache."""
    missing = [L for L in layers if (prompt, L, how) not in _cache]
    if not missing:
        return

    # local backend: one forward pass returns every hidden state
    if config.BACKEND == "local":
        m, tok = _get_local()
        dev = next(m.parameters()).device
        ids = tok(prompt, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = m(**ids)
        for L in missing:
            hs = out.hidden_states[L][0]
            vec = hs.mean(dim=0) if how == "mean" else hs[-1]
            _cache[(prompt, L, how)] = vec.detach().cpu().float()
        return

    model = get_model()

    def _run() -> dict[int, "torch.Tensor"]:
        saved: dict[int, "torch.Tensor"] = {}   # before trace (nnsight scoping)
        with model.trace(prompt, remote=True):                    # type: ignore[union-attr]
            for L in missing:
                resid = model.transformer.h[L].output[0][0]       # type: ignore[index]
                saved[L] = (resid.mean(dim=0) if how == "mean" else resid[-1]).save()
        return saved

    for L, v in _trace_with_retry(_run).items():
        _cache[(prompt, L, how)] = v


def clear_cache() -> None:
    _cache.clear()
