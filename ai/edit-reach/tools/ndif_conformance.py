#!/usr/bin/env python3
"""Re-measure this project's NDIF reproducibility numbers on YOUR connection.

Companion to `docs/ndif-reproducibility.md`. Each check prints the number that
document records beside the number your deployment gives, and says whether they
agree. The vocabulary is deliberately **matches / differs**, never pass / fail:
this suite documents a deployment, it does not grade one.

It is one file on purpose. It imports nothing from `editreach`, so you can copy
it out of this repository and run it anywhere. You need `nnsight`, `torch`, and
an `NNSIGHT_API_KEY` from login.ndif.us.

    python ndif_conformance.py                      # default checks
    python ndif_conformance.py --dry-run            # no remote calls at all
    python ndif_conformance.py --connections 16     # a sharper partition read
    python ndif_conformance.py --include backward   # the opt-in checks too
    python ndif_conformance.py --json out.json

Default cost is about 10 remote traces, each ~10-25s of queue and transfer.

**A note on what "differs" means.** Every documented number came off one
deployment over two days. A difference is more likely to be news about your
deployment than a fault in either. The number worth your attention is the LAST
one -- the total spread across sessions -- because that is the one a gate has to
be sized against.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics as st
import sys
import time
from dataclasses import dataclass, asdict, field
from typing import Callable, Final

import torch

# --------------------------------------------------------------------------- #
# What the reference document records. Edit nothing here to make a run agree.
# --------------------------------------------------------------------------- #

DOC: Final[str] = "docs/ndif-reproducibility.md"
DEFAULT_MODEL: Final[str] = "meta-llama/Llama-3.1-8B"
DEFAULT_LAYER: Final[int] = 5

#: Prompt pairs (subject, subject + continuation). The continuation must EXTEND
#: the subject, so that under causal attention the key at the subject's last
#: token is identical in both -- which makes their ratio 1 by arithmetic, not by
#: measurement. Any deviation is padding, position or tokenisation, i.e. yours.
ANCHORS: Final[tuple[tuple[str, str], ...]] = (
    ("Maurice de Vlaminck", " was a painter associated with"),
    ("The Eiffel Tower", " was built for the exposition of"),
    ("Danielle Darrieux", " spoke the language of"),
    ("Mount Kilimanjaro", " rises above the plains of"),
    ("The Louvre", " holds the collection of"),
    ("Hokkaido", " is the northernmost island of"),
    ("Leonhard Euler", " made his reputation in the field of"),
    ("The Bosphorus", " separates the continents of"),
)

#: Unrelated prompts, used where a check needs a batch rather than a pairing.
FILLER: Final[tuple[str, ...]] = (
    "The capital of Portugal is",
    "Water boils at a temperature of",
    "The largest desert in the world is",
    "Chess is played on a board of",
    "The currency of Japan is",
    "Photosynthesis takes place in the",
)


@dataclass(frozen=True, slots=True)
class Reference:
    """One documented number, and how close yours has to be to agree with it."""

    label: str
    value: float
    #: Absolute tolerance for "matches". Generous on purpose: these are
    #: measurements of hardware, and a tight band here would manufacture
    #: disagreement out of exactly the noise the document is about.
    tol: float
    unit: str = ""


@dataclass
class Observation:
    name: str
    verdict: str                      # matches | differs | skipped | error
    documented: float | None = None
    observed: float | None = None
    unit: str = ""
    traces: int = 0
    seconds: float = 0.0
    note: str = ""
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Standalone infrastructure. Deliberately duplicated from `editreach` so that
# this file has no project dependency; keep it boring.
# --------------------------------------------------------------------------- #

#: Where the ROME key lives: the INPUT to the MLP output projection. Reading the
#: wrong module does not raise, it returns plausible wrong numbers, so the two
#: supported families are named rather than guessed.
ARCH: Final[dict[str, Callable]] = {
    "llama": lambda m, L: m.model.layers[L].mlp.down_proj,
    "gptj": lambda m, L: m.transformer.h[L].mlp.fc_out,
}


def connect(model_name: str):
    from nnsight import CONFIG, LanguageModel

    key = os.environ.get("NNSIGHT_API_KEY")
    if not key:
        raise SystemExit("NNSIGHT_API_KEY not set -- get one from login.ndif.us")
    CONFIG.set_default_api_key(key)
    return LanguageModel(model_name)


def key_site(model, layer: int):
    cfg = model.config
    mt = (getattr(cfg, "model_type", "") or "").lower()
    n = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    family = "llama" if "llama" in mt else "gptj" if "gpt" in mt and "j" in mt else ""
    if not family:
        raise SystemExit(f"unsupported architecture {mt!r}; add it to ARCH")
    if not 0 <= layer < n:
        raise SystemExit(f"layer {layer} outside 0..{n - 1}")
    return ARCH[family](model, layer)


def d_mlp_of(model) -> int:
    cfg = model.config
    return getattr(cfg, "intermediate_size", None) or getattr(cfg, "n_inner", None) \
        or 4 * getattr(cfg, "n_embd", 0)


def encode(model, prompts: list[str]) -> tuple[torch.Tensor, list[int]]:
    """RIGHT-padded ids, plus each prompt's unpadded length.

    Right padding is not a detail. A token index computed on an unpadded prompt
    stays valid only if padding is added AFTER the text. Llama's tokenizer pads
    LEFT by default, which would silently shift every index by the pad width and
    read at the wrong token -- without raising, and without looking wrong.
    """
    tok = model.tokenizer
    rows = [tok(p, return_tensors="pt").input_ids[0] for p in prompts]
    width = max(len(r) for r in rows)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    ids = torch.full((len(rows), width), pad, dtype=torch.long)
    for i, row in enumerate(rows):
        ids[i, : len(row)] = row
    return ids, [len(r) for r in rows]


def anchor_batch(model) -> tuple[list[str], list[int]]:
    """Subject prompts then extended prompts, with the shared last-subject index.

    Row i and row i + n are the pair. Both are read at the subject's final token,
    which the extension does not move because it is appended.
    """
    subjects = [s for s, _ in ANCHORS]
    extended = [s + c for s, c in ANCHORS]
    tok = model.tokenizer
    where = [len(tok(s, return_tensors="pt").input_ids[0]) - 1 for s in subjects]
    return subjects + extended, where + where


def signature(t: torch.Tensor) -> str:
    return hashlib.sha1(t.to(torch.float32).numpy().tobytes()).hexdigest()[:16]


def gpu_of(meta: dict) -> str:
    by_gpu = (meta or {}).get("max_mem_by_gpu") or {}
    return ",".join(sorted(str(k) for k in by_gpu)) if by_gpu else "?"


#: NDIF's websocket drops intermittently under load. A suite that dies on the
#: fourth of ten traces reports nothing, which is worse than reporting a
#: difference. Deliberately minimal -- classify by name, retry, move on.
_TRANSPORT: Final[tuple[str, ...]] = (
    "Timeout", "Connection", "Protocol", "Handshake", "Disconnect", "Closed",
    "handshake", "socket", "ssl",
)


def retrying(fn, *, what: str, tries: int = 4, backoff: float = 4.0):
    last: Exception | None = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:          # noqa: BLE001 -- narrowed just below
            text = f"{type(exc).__name__} {exc}"
            if attempt == tries - 1 or not any(t in text for t in _TRANSPORT):
                raise
            last = exc
            wait = backoff * (attempt + 1)
            print(f"  [{what}] {type(exc).__name__}, attempt {attempt + 1}/{tries}; "
                  f"retrying in {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
    raise last                            # unreachable


def read_keys_ids(model, site, ids, positions, meta_out: dict | None = None):
    """Keys at `positions[i]` of row i of an ALREADY-BUILT id tensor.

    Separate from `read_keys` because two checks below need to vary the batch's
    shape while holding its content fixed, which is impossible if the padding is
    computed from the prompts each time.
    """
    rows = torch.arange(ids.shape[0])
    where = torch.tensor(list(positions))

    def _once():
        with model.trace(ids, remote=True) as tracer:
            got = site.input.float()[rows, where].save()
        if meta_out is not None:
            meta_out.clear()
            meta_out.update(getattr(tracer.backend, "meta", None) or {})
        return got.detach().cpu().float()

    return retrying(_once, what=f"{ids.shape[0]}x{ids.shape[1]}")


def widen(ids: torch.Tensor, extra: int, pad: int) -> torch.Tensor:
    """The same rows, the same content, a wider pad region. Shape alone varies."""
    return torch.cat([ids, torch.full((ids.shape[0], extra), pad, dtype=ids.dtype)], 1)


def read_keys(model, site, prompts, positions, meta_out: dict | None = None):
    """Keys at `positions[i]` of `prompts[i]`, float32 on CPU, in ONE trace.

    `site` is resolved by the CALLER, before the trace. nnsight ships the trace
    body's source to the server, so anything the body references must already be
    a plain local -- a call back into your own package arrives as
    `ModuleNotFoundError`. Check `trace_source` below measures that directly.
    """
    ids, lengths = encode(model, prompts)
    for i, (p, n) in enumerate(zip(positions, lengths)):
        if not 0 <= p < n:
            raise SystemExit(f"position {p} outside prompt {i} of {n} tokens")
    return read_keys_ids(model, site, ids, positions, meta_out)


def ratios(keys: torch.Tensor) -> torch.Tensor:
    """(k . k*) / (k* . k*) for the anchor layout: second half against first."""
    n = keys.shape[0] // 2
    ref, probe = keys[:n], keys[n:]
    return (probe * ref).sum(-1) / (ref * ref).sum(-1)


# --------------------------------------------------------------------------- #
# The checks
# --------------------------------------------------------------------------- #

def check_dtype_budget(ctx) -> Observation:
    """The precision budget bf16 gives you. Local arithmetic, no model, no network.

    This is a constant of the dtype, not a property of your deployment, so it is
    **recorded rather than compared** -- it will read the same on every machine.
    It is here because every other deviation in this suite has to be read against
    it: an error of this order is arithmetic, not NDIF.

    The first version of this check measured the relative error of a dot product
    between two random vectors, got 4.9e-01, and that number said nothing about
    bf16. Random vectors of 14336 channels are near-orthogonal, so their dot
    product is a small difference of large terms and the relative error is
    dominated by cancellation. Activations are not near-orthogonal and the
    quantity at issue is a ratio of aligned vectors, so the budget that actually
    binds is the PER-ELEMENT rounding error, which is what is measured now.
    """
    g = torch.Generator().manual_seed(1538)
    x = torch.randn(1 << 16, generator=g)
    x = x[x.abs() > 1e-6]
    err = ((x.to(torch.bfloat16).float() - x) / x).abs()
    worst = float(err.max())
    eps = float(torch.finfo(torch.bfloat16).eps)
    return Observation(
        name="dtype_budget", verdict="recorded", observed=worst,
        unit="max per-element relative error",
        extra={"bfloat16_eps": eps, "float32_eps": float(torch.finfo(torch.float32).eps),
               "channels_summed": ctx.d_mlp or 14336},
        note="a constant of the dtype, the same everywhere; cast to float32 "
             "BEFORE the dot product and this stops mattering",
    )


def check_ratio_in_trace(ctx) -> Observation:
    """Both terms read in ONE trace, float32. Documented: exactly 1.000."""
    prompts, where = anchor_batch(ctx.model)
    meta: dict = {}
    keys = read_keys(ctx.model, ctx.site, prompts, where, meta_out=meta)
    dev = float((ratios(keys) - 1.0).abs().max())
    ctx.cached_reference = keys[: len(keys) // 2].clone()
    ctx.first_gpu = gpu_of(meta)
    return Observation(
        name="ratio_in_trace", verdict="", observed=dev, unit="deviation from 1.000",
        traces=1, extra={"gpu": ctx.first_gpu, "anchors": len(ANCHORS)},
        note="an analytic quantity: the extension cannot move the subject's key "
             "under causal attention, so any deviation is your pipeline",
    )


def check_cached_reference(ctx) -> Observation:
    """The same ratio, with k* from an earlier trace and the dot in bf16.

    Both hazards at once, which is what a pipeline that caches its reference
    tensors actually does. Documented worst: 6.382e-03.
    """
    if ctx.cached_reference is None:
        return Observation(name="cached_reference", verdict="skipped",
                           note="needs ratio_in_trace to have run first")
    prompts, where = anchor_batch(ctx.model)
    n = len(prompts) // 2
    fresh = read_keys(ctx.model, ctx.site, prompts[n:], where[n:])
    ref = ctx.cached_reference.to(torch.bfloat16)
    probe = fresh.to(torch.bfloat16)
    num = (probe * ref).sum(-1).float()
    den = (ref * ref).sum(-1).float()
    dev = float((num / den - 1.0).abs().max())
    return Observation(
        name="cached_reference", verdict="", observed=dev, unit="deviation from 1.000",
        traces=1,
        note="k* from the previous trace, arithmetic in bf16 -- dtype and "
             "provenance together, which is what caching actually costs",
    )


def check_batch_rows(ctx) -> Observation:
    """More rows in the batch, the SAME padded width. Documented: bit-identical.

    Split out of a single "batch composition" check after that check reported
    4.297e-02 against a documented zero. The cause was the check, not NDIF: the
    filler prompts were longer than the anchors, so adding them widened the
    tensor, and the arm was measuring shape while claiming to measure
    neighbours. Those are different questions and they get different arms now.
    """
    prompts, where = anchor_batch(ctx.model)
    tok = ctx.model.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    ids, _ = encode(ctx.model, prompts)
    width = ids.shape[1]
    # Filler truncated to the anchors' width, so the shape is held fixed and only
    # the row count moves.
    filler_ids, _ = encode(ctx.model, list(FILLER))
    if filler_ids.shape[1] >= width:
        filler_ids = filler_ids[:, :width]
    else:
        filler_ids = widen(filler_ids, width - filler_ids.shape[1], pad)
    alone = read_keys_ids(ctx.model, ctx.site, ids, where)
    ctx.alone_keys, ctx.alone_ids, ctx.alone_where = alone, ids, where
    both = torch.cat([ids, filler_ids], 0)
    together = read_keys_ids(ctx.model, ctx.site, both, list(where) + [0] * len(FILLER))
    seen = together[: len(prompts)]
    raw = float((alone - seen).abs().max())
    # The quantity you DERIVE is not the quantity you read. A ratio of two keys
    # read in the same trace can survive a perturbation that moves both keys,
    # and that difference is the whole practical point of this suite -- so both
    # are reported and the reference is on the ratio.
    ratio_delta = float((ratios(alone) - ratios(seen)).abs().max())
    scale = float(alone.abs().max())
    return Observation(
        name="batch_rows", verdict="", observed=ratio_delta,
        unit="max |difference| in the derived ratio", traces=2,
        extra={"raw_key_difference": raw,
               "raw_bit_identical": torch.equal(alone, seen),
               "key_magnitude": scale,
               "raw_relative": (raw / scale) if scale else 0.0,
               "rows": f"{ids.shape[0]} -> {both.shape[0]}", "width": width},
        note="unrelated neighbours in the batch, width held fixed; compare the "
             "raw difference against the ratio one",
    )


def check_batch_width(ctx) -> Observation:
    """The SAME rows and the same content, a wider pad region. Shape alone varies.

    Under causal attention, padding appended after the text cannot reach a token
    to its left, so this is zero by the mathematics. Whether it is zero in
    practice is a question about bf16 matmul kernels, which are shape-dependent.
    This arm has no documented reference: it was not measured before this suite.
    """
    if ctx.alone_keys is None:
        return Observation(name="batch_width", verdict="skipped",
                           note="needs batch_rows to have run first")
    tok = ctx.model.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    wider = widen(ctx.alone_ids, 8, pad)
    got = read_keys_ids(ctx.model, ctx.site, wider, ctx.alone_where)
    diff = (ctx.alone_keys - got).abs()
    delta = float(diff.max())
    scale = float(ctx.alone_keys.abs().max())
    # WHERE the difference sits decides what it is. Concentrated in the rows
    # with the most padding points at padding handling; spread evenly across
    # rows points at kernel shape-dependence. These are different diagnoses and
    # a single max cannot tell them apart.
    per_row = diff.max(dim=-1).values
    n_rows = per_row.shape[0]
    pad_after = [int(ctx.alone_ids.shape[1] - 1 - w) for w in ctx.alone_where]
    rows_touched = int((per_row > 0).sum())
    return Observation(
        name="batch_width", verdict="recorded", observed=delta, unit="max |difference|",
        traces=1,
        extra={"bit_identical": torch.equal(ctx.alone_keys, got),
               "key_magnitude": scale,
               "relative": (delta / scale) if scale else 0.0,
               "width": f"{ctx.alone_ids.shape[1]} -> {wider.shape[1]}",
               "rows_touched": f"{rows_touched}/{n_rows}",
               "per_row_max": [round(float(v), 8) for v in per_row],
               "pad_tokens_after_read_position": pad_after},
        note="pad width only; causally this cannot matter, so anything nonzero "
             "here is kernel shape-dependence and it bounds every cross-run "
             "comparison you make on raw activations",
    )


def check_pad_content(ctx) -> Observation:
    """The control that makes `batch_width` interpretable: content, not width.

    `batch_width` shows that widening the pad region moves the keys. Two things
    could do that, and they call for opposite responses:

      the model is attending to the pads  -> a usage fault, fix your masking
      the kernel path depends on shape    -> nothing to fix, size your tolerance

    Filling the same-width pad region with a DIFFERENT token tells them apart.
    If the keys move, the pads are being read. If they do not, only the shape
    matters. Measured 2026-11-03 on Llama-3.1-8B: bit-identical, so causality
    holds and the diagnosis is the kernel.
    """
    if ctx.alone_ids is None:
        return Observation(name="pad_content", verdict="skipped",
                           note="needs batch_rows to have run first")
    tok = ctx.model.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    other = tok(" zebra", add_special_tokens=False).input_ids[0]
    if other == pad:
        return Observation(name="pad_content", verdict="skipped",
                           note="filler token collides with the pad token")
    a = read_keys_ids(ctx.model, ctx.site, widen(ctx.alone_ids, 8, pad), ctx.alone_where)
    b = read_keys_ids(ctx.model, ctx.site, widen(ctx.alone_ids, 8, other), ctx.alone_where)
    delta = float((a - b).abs().max())
    return Observation(
        name="pad_content", verdict="", observed=delta, unit="max |difference|",
        traces=2, extra={"bit_identical": torch.equal(a, b),
                         "pad_id": int(pad), "other_id": int(other)},
        note="same width, different trailing content; zero here means causality "
             "holds and the width effect is kernel shape-dependence, not masking",
    )


def check_matmul_site(ctx) -> Observation:
    """GPU-inside-the-trace against CPU-after-the-trace, same keys.

    Documented: 5.06e-06 at the median, 2.98e-03 per item. The gap between those
    two is the point -- a median hides this and a per-item value does not.
    """
    # NOT the anchors. An anchor ratio is analytically 1.000, so both arms return
    # exactly 1.000 and their difference is zero whatever the arithmetic does --
    # the first version of this check read 0.000e+00 for precisely that reason
    # and would have reported "the two sites agree" forever.
    subjects = [s for s, _ in ANCHORS]
    n = min(len(subjects), len(FILLER))
    prompts = subjects[:n] + list(FILLER)[:n]
    tok = ctx.model.tokenizer
    where = [len(tok(p, return_tensors="pt").input_ids[0]) - 1 for p in prompts]
    ids, _ = encode(ctx.model, prompts)
    rows = torch.arange(len(prompts))
    col = torch.tensor(list(where))
    site = ctx.site
    with ctx.model.trace(ids, remote=True):
        kk = site.input[rows, col]
        ref, probe = kk[:n], kk[n:]
        num = (probe * ref).sum(-1).float()
        den = (ref * ref).sum(-1).float()
        on_gpu = (num / den).save()
    gpu_vals = on_gpu.detach().cpu().float()
    fetched = read_keys(ctx.model, ctx.site, prompts, where)
    ref32, probe32 = fetched[:n], fetched[n:]
    cpu_vals = (probe32 * ref32).sum(-1) / (ref32 * ref32).sum(-1)
    per_item = float((gpu_vals - cpu_vals).abs().max())
    med = abs(float(st.median(gpu_vals.tolist())) - float(st.median(cpu_vals.tolist())))
    return Observation(
        name="matmul_site", verdict="", observed=med, unit="|difference| of medians",
        traces=2, extra={"max_per_item_difference": per_item, "pairs": n},
        note="pick one site and stay with it; read the per-item figure in extra, "
             "which the median understates by orders of magnitude",
    )


def check_session_partition(ctx) -> Observation:
    """N fresh connections, identical input. Documented: partitions by serving GPU.

    The expensive check, and the only one whose sharpness scales with what you
    spend. Four connections can show that variation exists; it takes more to show
    the partition is clean.
    """
    prompts, where = anchor_batch(ctx.model)
    seen: dict[str, list[str]] = {}
    floors: dict[str, list[float]] = {}
    for _ in range(ctx.connections):
        model = connect(ctx.model_name)
        site = key_site(model, ctx.layer)
        meta: dict = {}
        keys = read_keys(model, site, prompts, where, meta_out=meta)
        sig = signature(keys)
        seen.setdefault(sig, []).append(gpu_of(meta))
        floors.setdefault(sig, []).append(float(st.median(ratios(keys).tolist())))
    # A clean partition means every signature maps to exactly one device AND no
    # device carries two signatures. Both directions, because only one of them
    # is what "partition" means and checking one is how you report it wrongly.
    sig_to_gpu = {s: set(g) for s, g in seen.items()}
    gpu_to_sig: dict[str, set[str]] = {}
    for s, gs in seen.items():
        for g in gs:
            gpu_to_sig.setdefault(g, set()).add(s)
    # A partition needs at least two of each to be a partition at all. With one
    # signature on one device both conditions above are vacuously true, and the
    # first version of this check happily reported `clean_partition = True` for
    # sixteen identical readings off a single GPU -- a pass on an input that
    # cannot fail, which is the fault this project keeps paying to find.
    devices = {g for gs in seen.values() for g in gs}
    if len(seen) < 2 or len(devices) < 2:
        clean = None
    else:
        clean = all(len(v) == 1 for v in sig_to_gpu.values()) and \
            all(len(v) == 1 for v in gpu_to_sig.values())
    meds = [m for v in floors.values() for m in v]
    spread = (max(meds) - min(meds)) if meds else 0.0
    return Observation(
        name="session_partition", verdict="", observed=float(len(seen)),
        unit="distinct readings", traces=ctx.connections,
        extra={
            "connections": ctx.connections,
            "distinct_devices": sorted(devices),
            "clean_partition": "n/a - nothing to partition" if clean is None else clean,
            "spread_across_readings": spread,
            "by_signature": {s: sorted(set(g)) for s, g in seen.items()},
        },
        note="a clean partition requires BOTH directions AND something to "
             "partition: one device per reading, one reading per device, and at "
             "least two of each. One device means the device explains nothing "
             "that day -- not that it never does",
    )


def check_trace_source(ctx) -> Observation:
    """A trace body compiled from a string has no source. Costs no remote call.

    nnsight builds the graph from the source of the frame that entered
    `model.trace`, so a heredoc, a `python -c`, or an `exec` of a string cannot
    carry a trace. This fails client-side, before anything is sent.
    """
    src = "with ctx.model.trace(ids, remote=True):\n    pass\n"
    ids, _ = encode(ctx.model, list(FILLER[:2]))
    try:
        exec(compile(src, "<string>", "exec"), {"ctx": ctx, "ids": ids})
    except Exception as exc:          # noqa: BLE001 -- the exception IS the result
        name = type(exc).__name__
        return Observation(
            name="trace_source", verdict="", observed=None,
            extra={"raised": name, "expected": "WithBlockNotFoundError"},
            note=f"raised {name}; write traces in a real .py file",
        )
    return Observation(
        name="trace_source", verdict="", extra={"raised": None},
        note="no exception -- your nnsight resolves trace source differently "
             "from the one documented here, which is worth reporting",
    )


def check_served_dtype(ctx) -> Observation:
    """What dtype your deployment actually serves activations in. One trace.

    Everything in section 1 of the reference is conditional on bf16. If your
    deployment serves float32 the dtype half stops applying and only provenance
    remains, so this is the first thing to read, not the last.
    """
    ids, _ = encode(ctx.model, list(FILLER[:2]))
    site = ctx.site

    def _once():
        with ctx.model.trace(ids, remote=True):
            # `.dtype` is a plain attribute of the proxied tensor, not a tensor
            # operation, so it has to come back as a saved tensor to be read --
            # a zero-length slice in the native dtype is the cheapest carrier.
            probe = site.input[:1, :1, :1].save()
        return probe

    got = retrying(_once, what="dtype probe")
    dt = str(getattr(got, "dtype", "unknown")).replace("torch.", "")
    return Observation(
        name="served_dtype", verdict="recorded", traces=1,
        extra={"dtype": dt, "d_mlp": ctx.d_mlp,
               "section_1_applies": dt.startswith("bfloat") or dt.startswith("float16")},
        note=f"activations arrive as {dt}; the dtype half of section 1 applies "
             f"only below float32",
    )


def check_local_import_in_trace(ctx) -> Observation:
    """Reference a module inside the trace body. Opt-in: sends a doomed trace."""
    site = ctx.site
    ids, _ = encode(ctx.model, list(FILLER[:2]))
    try:
        with ctx.model.trace(ids, remote=True):
            _ = site.input.float()[:, 0] * torch.tensor(os.cpu_count() or 1)
            _ = sys.maxsize                           # a stdlib name in the body
            out = site.input.float()[:, 0].sum().save()
        _ = out.detach().cpu()
        return Observation(
            name="local_import_in_trace", verdict="", extra={"raised": None},
            traces=1, note="a stdlib reference survived; the documented failure "
                           "is for YOUR OWN package, which the server lacks",
        )
    except Exception as exc:          # noqa: BLE001
        return Observation(
            name="local_import_in_trace", verdict="", traces=1,
            extra={"raised": type(exc).__name__},
            note=f"raised {type(exc).__name__}; bind everything to plain locals "
                 f"before the with block",
        )


CHECKS: Final[dict[str, tuple[Callable, Reference | None, bool]]] = {
    # name: (fn, reference, in_default_set)
    "dtype_budget": (check_dtype_budget, None, True),
    "ratio_in_trace": (check_ratio_in_trace, Reference("worst deviation", 0.0, 1e-06), True),
    "cached_reference": (check_cached_reference, Reference("worst deviation", 6.382e-03, 4e-03), True),
    "batch_rows": (check_batch_rows, Reference("max |difference|", 0.0, 1e-09), True),
    "batch_width": (check_batch_width, None, True),
    "pad_content": (check_pad_content, Reference("max |difference|", 0.0, 1e-09), True),
    # Model-SPECIFIC: see PER_MODEL. The entry here is the Llama-3.1-8B value
    # the reference document was written from, and it is replaced at run time
    # for a model that has its own. A model with neither is recorded, not judged.
    "matmul_site": (check_matmul_site, Reference("|difference| of medians", 5.06e-06, 4e-06), True),
    "served_dtype": (check_served_dtype, None, True),
    "session_partition": (check_session_partition, None, True),
    "trace_source": (check_trace_source, None, True),
    "local_import_in_trace": (check_local_import_in_trace, None, False),
}


#: Quantities whose magnitude depends on the model rather than on NDIF. Keeping
#: them in one place is the difference between "your deployment differs from
#: ours" and "you are running a different model", which the first version of
#: this suite could not tell apart: it reported `matmul_site` as "differs" on
#: 70B and GPT-J purely because the documented number came from 8B.
PER_MODEL: Final[dict[str, dict[str, Reference]]] = {
    "meta-llama/Llama-3.1-8B": {
        "matmul_site": Reference("|difference| of medians", 5.06e-06, 4e-06),
    },
    "meta-llama/Llama-3.1-70B": {
        "matmul_site": Reference("|difference| of medians", 4.969e-07, 4e-07),
    },
    "EleutherAI/gpt-j-6b": {
        "matmul_site": Reference("|difference| of medians", 7.451e-09, 7e-09),
    },
}


@dataclass
class Ctx:
    model_name: str
    layer: int
    connections: int
    model: object = None
    site: object = None
    d_mlp: int = 0
    cached_reference: torch.Tensor | None = None
    alone_keys: torch.Tensor | None = None
    alone_ids: torch.Tensor | None = None
    alone_where: list | None = None
    first_gpu: str = "?"


def verdict_for(obs: Observation, ref: Reference | None) -> Observation:
    if obs.verdict:
        return obs
    if ref is None or obs.observed is None:
        obs.verdict = "recorded"
        return obs
    obs.documented, obs.unit = ref.value, obs.unit or ref.unit
    obs.verdict = "matches" if abs(obs.observed - ref.value) <= ref.tol else "differs"
    return obs


def fmt(x: float | None) -> str:
    return "-" if x is None else (f"{x:.3e}" if x else "0.000e+00")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--layer", default=str(DEFAULT_LAYER),
                    help="one layer, or a comma-separated list to sweep "
                         "(e.g. 0,5,12,24,31). A sweep prints a matrix.")
    ap.add_argument("--connections", type=int, default=4,
                    help="fresh connections for session_partition (documented run used 16)")
    ap.add_argument("--include", nargs="*", default=[],
                    help="opt-in checks: " + " ".join(k for k, v in CHECKS.items() if not v[2]))
    ap.add_argument("--only", nargs="*", default=[], help="run just these checks")
    ap.add_argument("--dry-run", action="store_true",
                    help="exercise the local paths and make NO remote call")
    ap.add_argument("--json", default="", help="write results here")
    args = ap.parse_args(argv)

    try:
        layers = [int(x) for x in str(args.layer).split(",") if x.strip()]
    except ValueError:
        raise SystemExit(f"--layer must be an int or a comma-separated list, "
                         f"not {args.layer!r}")
    if not layers:
        raise SystemExit("--layer named no layers")

    chosen = [k for k, (_, _, dflt) in CHECKS.items() if dflt or k in args.include]
    if args.only:
        unknown = [k for k in args.only if k not in CHECKS]
        if unknown:
            raise SystemExit(f"unknown checks: {unknown}; have {list(CHECKS)}")
        chosen = list(args.only)

    ctx = Ctx(args.model, layers[0], args.connections)

    if args.dry_run:
        # Everything that does not touch the network, plus the tokenisation and
        # indexing the remote checks depend on -- which is where the mistakes
        # that cost a remote call actually live.
        ctx.d_mlp = 14336
        obs = verdict_for(check_dtype_budget(ctx), CHECKS["dtype_budget"][1])
        assert obs.observed is not None and 0 < obs.observed < 0.05, (
            f"bf16 per-element rounding read {obs.observed} -- a value near 0.5 means\n"
            "the check is measuring cancellation between near-orthogonal vectors,\n"
            "which is the fault this check was rewritten to remove")
        assert len(ANCHORS) >= 4, "too few anchors to say anything"
        assert all(c.startswith(" ") for _, c in ANCHORS), \
            "an extension must begin with a space or it re-tokenises the subject"
        assert len(set(s for s, _ in ANCHORS)) == len(ANCHORS), "duplicate subjects"
        for name, (fn, ref, _) in CHECKS.items():
            assert fn.__doc__, f"{name} has no docstring, so its result is unreadable"
            if ref is not None:
                assert ref.tol > 0, f"{name} has a zero tolerance, which cannot match"
        # A reference whose tolerance exceeds its own value would call anything
        # a match. Allowed only where the documented value IS zero.
        # A band that reaches zero calls "the effect is absent" a match with
        # "the effect is as documented". Those are the two answers the check
        # exists to tell apart, so the band must not contain both.
        for name, (_, ref, _) in CHECKS.items():
            if ref and ref.value and ref.tol >= abs(ref.value):
                raise SystemExit(
                    f"{name}: tolerance {ref.tol:g} reaches zero from value "
                    f"{ref.value:g}, so an absent effect would read as a match")
        assert len(layers) >= 1
        print(f"dry run ok -- {len(CHECKS)} checks declared, {len(chosen)} selected, "
              f"{len(layers)} layer(s) {layers}, 0 remote calls")
        print(f"  dtype_budget observed {fmt(obs.observed)} ({obs.verdict})")
        return 0

    model = connect(args.model)
    _, n_layers, _ = (lambda c: (None, getattr(c, "num_hidden_layers", None)
                                 or getattr(c, "n_layer"), None))(model.config)
    bad = [L for L in layers if not 0 <= L < n_layers]
    if bad:
        raise SystemExit(f"layers {bad} outside 0..{n_layers - 1} for {args.model}")

    by_layer: dict[int, list[Observation]] = {}
    for layer in layers:
        # A FRESH context per layer. The checks hand each other cached tensors
        # (`alone_keys`, `cached_reference`), and a tensor read at layer 5
        # compared against one read at layer 24 would silently produce a large,
        # meaningless difference -- the same class of fault as every other one
        # this suite has found.
        ctx = Ctx(args.model, layer, args.connections)
        ctx.model = model
        ctx.site = key_site(model, layer)
        ctx.d_mlp = d_mlp_of(model)
        results: list[Observation] = []
        for name in chosen:
            fn, ref, _ = CHECKS[name]
            over = PER_MODEL.get(args.model, {})
            if name in over:
                ref = over[name]
            elif name in {k for v in PER_MODEL.values() for k in v}:
                ref = None          # model-specific, and we have no value for THIS model
            if len(layers) > 1 and ref is not None and layer != DEFAULT_LAYER:
                # Every documented number was read at layer 5. Comparing a
                # layer-24 reading against it would report "differs" for a
                # correct deployment, which is the bookkeeping fault [E-008]
                # already fixed once for models. Analytic checks are exempt:
                # their reference is 0 by arithmetic at every layer.
                if ref.value != 0.0:
                    ref = None
            t0 = time.monotonic()
            try:
                obs = fn(ctx)
            except Exception as exc:  # noqa: BLE001 -- one bad check must not end the run
                obs = Observation(name=name, verdict="error",
                                  note=f"{type(exc).__name__}: {exc}")
            obs.seconds = time.monotonic() - t0
            results.append(verdict_for(obs, ref))
        by_layer[layer] = results

    traces = sum(r.traces for rs in by_layer.values() for r in rs)
    secs = sum(r.seconds for rs in by_layer.values() for r in rs)
    width = max(len(n) for n in chosen)

    if len(layers) == 1:
        results = by_layer[layers[0]]
        print(f"\n{args.model}  layer {layers[0]}  {traces} traces  {secs:.0f}s\n")
        print(f"{'check'.ljust(width)}  {'documented':>11}  {'yours':>11}  verdict")
        print("-" * (width + 40))
        for r in results:
            print(f"{r.name.ljust(width)}  {fmt(r.documented):>11}  "
                  f"{fmt(r.observed):>11}  {r.verdict}")
        print()
        for r in results:
            if r.note:
                print(f"  {r.name}: {r.note}")
            for k, v in r.extra.items():
                print(f"      {k} = {v}")
    else:
        print(f"\n{args.model}  layers {layers}  {traces} traces  {secs:.0f}s\n")
        head = "".join(f"{('L' + str(L)):>13}" for L in layers)
        print(f"{'check'.ljust(width)}{head}")
        print("-" * (width + 13 * len(layers)))
        for name in chosen:
            row = ""
            for L in layers:
                r = next(x for x in by_layer[L] if x.name == name)
                row += f"{fmt(r.observed):>13}" if r.observed is not None \
                    else f"{(r.extra.get('dtype') or r.verdict)[:12]:>13}"
            print(f"{name.ljust(width)}{row}")
        print()
        bad_v = [(L, r) for L, rs in by_layer.items() for r in rs
                 if r.verdict in ("differs", "error")]
        if bad_v:
            for L, r in bad_v:
                print(f"  L{L} {r.name}: {r.verdict} -- {r.note}")
        else:
            print("  every check carrying a reference matched at every layer")
        print("\n  raw detail per layer is in the --json output")

    print(f"\nreference: {DOC}")
    results = [r for rs in by_layer.values() for r in rs]

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"model": args.model, "layers": layers,
                       "by_layer": {str(L): [asdict(r) for r in rs]
                                    for L, rs in by_layer.items()}}, fh, indent=2)
        print(f"written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
