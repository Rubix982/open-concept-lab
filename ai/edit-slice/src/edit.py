"""E-013 · Rank-one editing of a remote model, without materialising the weights.

ROME rewrites the MLP output projection `W` at one layer so that a chosen key maps
to a chosen value:

    W' = W + (v* - W k*) uᵀ / (uᵀ k*)        u = C⁻¹k*

[E-013] gate 0 established that the reference implementation runs `C = I` — all 14 of
EasyEdit's shipped ROME configs set `mom2_adjustment: false`, including the ROME
paper's own gpt2-xl and gpt-j-6B, and `compute_u.py` then uses `u = k*` directly. With
`u = k*` the update is

    W' k = W k + (v* - W k*) · (k*·k) / (k*·k*)

so the change to the `down_proj` OUTPUT at any position is a scalar multiple of one
fixed vector, computable inside a trace from that position's observed key. **The
edited weight matrix is never formed.** That is what makes this runnable against a
shared remote model, where we cannot write to weights at all — and it is exact, not an
approximation of the weight edit.

Describe results as "ROME as configured by EasyEdit", never as "ROME" unqualified.
See agents/shared/decisions.md [E-013] Gate 0.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Final

import torch

from remote import BACKOFF_S, MAX_ATTEMPTS, _is_transport_error

log: Final[logging.Logger] = logging.getLogger("edit")

#: EasyEdit's llama3-8b.yaml, verbatim. Changing any of these changes a number, so
#: they belong in the artifact that records a run.
LAYER: Final[int] = 5
V_NUM_GRAD_STEPS: Final[int] = 25
V_LR: Final[float] = 5e-1
V_WEIGHT_DECAY: Final[float] = 1e-3
CLAMP_NORM_FACTOR: Final[float] = 4.0
KL_FACTOR: Final[float] = 0.0625


def subject_last_index(tokenizer, prompt: str, subject: str) -> int:
    """Index of the last token OF THE SUBJECT — ROME's `fact_token: subject_last`.

    Located by re-tokenising the prompt truncated at the subject's end rather than by
    assuming a position: subjects sit mid-prompt ("X was born in the country of") and
    tokenise to a variable number of pieces ("Maurice de Vlaminck" -> 8 tokens).
    """
    cut = prompt.index(subject) + len(subject)
    return len(tokenizer(prompt[:cut]).input_ids) - 1


@dataclass(frozen=True)
class RankOneEdit:
    """Everything needed to apply the edit, and nothing that needs weights."""

    case_id: str
    layer: int
    subject: str
    prompt: str
    target: str
    k_star: torch.Tensor      # [d_mlp]  the key at the subject's last token
    delta_v: torch.Tensor     # [d_model] v* - W k*

    def unpack(self) -> tuple[int, torch.Tensor, torch.Tensor]:
        """Call OUTSIDE the trace. See APPLY_IDIOM for why this exists."""
        return self.layer, self.k_star, self.delta_v

    @property
    def norm_ratio(self) -> float:
        """‖v* − W k*‖ relative to ‖k*‖ — the edit's magnitude, for the control."""
        return float(self.delta_v.norm() / self.k_star.norm())


def read_key_and_value(model, prompt: str, subject: str, layer: int = LAYER
                       ) -> tuple[torch.Tensor, torch.Tensor]:
    """One remote trace: `k*` and `W k*` at the subject's last token."""
    idx = subject_last_index(model.tokenizer, prompt, subject)
    with model.trace(prompt, remote=True):
        k = model.model.layers[layer].mlp.down_proj.input[0, idx].save()
        v = model.model.layers[layer].mlp.down_proj.output[0, idx].save()
    return k.float().cpu(), v.float().cpu()


#: The edit application, as source rather than a function — forced, not stylistic.
#: nnsight builds its intervention graph by reading the source of the frame that
#: entered `model.trace`, and two things break it, both found by bisection on
#: 2026-09-15 and both failing remotely with `'NoneType' object has no attribute
#: '__dict__'` rather than raising anything locally:
#:
#:   1. Proxy operations inside a NESTED CALL are never captured. The identical body
#:      fails as a function in this module and as a function in the caller's module,
#:      and succeeds only inline.
#:   2. ATTRIBUTE ACCESS on a Python object inside the trace fails. `e.k_star` breaks;
#:      the same tensor hoisted to a plain local before the `with` works. Hence
#:      `RankOneEdit.unpack()`.
#:
#: Callers paste this inside their own trace, having called `unpack()` above it.
APPLY_IDIOM: Final[str] = """
    lay, ks_cpu, dv_cpu = e.unpack()            # OUTSIDE the trace
    with model.trace(prompt, remote=True):
        dp = model.model.layers[lay].mlp.down_proj
        k = dp.input
        ks = ks_cpu.to(k.device, k.dtype)
        dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                * dv_cpu.to(k.device, k.dtype)
"""


def _target_ids(tokenizer, target: str) -> list[int]:
    text = target if target.startswith(" ") else " " + target
    return tokenizer(text, add_special_tokens=False).input_ids


def compute_v(model, prompt: str, subject: str, target: str, *,
              layer: int = LAYER, steps: int = V_NUM_GRAD_STEPS, lr: float = V_LR,
              weight_decay: float = V_WEIGHT_DECAY,
              clamp_norm_factor: float = CLAMP_NORM_FACTOR,
              kl_factor: float = KL_FACTOR) -> tuple[torch.Tensor, list[float]]:
    """Optimise `delta = v* − W k*` by gradient descent through the frozen model.

    The optimiser step happens LOCALLY. `delta` is a local tensor serialised into the
    intervention graph as a constant; the remote side returns d(loss)/d(activation) at
    the subject's last token, which equals d(loss)/d(delta) because the activation
    enters as `out[idx] + delta`. One remote round trip per step. [E-006] verified this
    exact pattern — `requires_grad_`, `retain_grad`, `backward()` inside the trace.

    The KL term is not decoration. Without it the edit is less constrained and does
    more collateral damage, which inflates apparent contraction — the same direction
    of bias as `C = I`. Two biases pointing the same way would make the [E-013]
    existence claim much weaker, so this follows EasyEdit's `kl_factor: 0.0625`.
    """
    tok = model.tokenizer
    idx = subject_last_index(tok, prompt, subject)
    tgt = _target_ids(tok, target)
    full = prompt + (target if target.startswith(" ") else " " + target)
    n_prompt = len(tok(prompt).input_ids)

    essence = f"{subject} is a"
    idx_e = subject_last_index(tok, essence, subject)

    delta = torch.zeros(model.config.hidden_size, dtype=torch.float32)
    _, wk = read_key_and_value(model, prompt, subject, layer)
    max_norm = clamp_norm_factor * float(wk.norm())

    # Build the batch explicitly with RIGHT padding rather than letting `trace` pad.
    # Index positions are computed from unpadded text; left padding would shift every
    # one of them silently, and the edit would be applied to the wrong token.
    ids_full = tok(full).input_ids
    ids_ess = tok(essence).input_ids
    width = max(len(ids_full), len(ids_ess))
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    batch = torch.full((2, width), pad, dtype=torch.long)
    batch[0, : len(ids_full)] = torch.tensor(ids_full)
    batch[1, : len(ids_ess)] = torch.tensor(ids_ess)
    last_ess = len(ids_ess) - 1

    # Pre-edit distribution on the essence prompt, for the KL anchor. One trace.
    with model.trace(batch, remote=True):
        ref_logits = model.lm_head.output[1, last_ess].float().save()
    ref_logp = torch.log_softmax(ref_logits.cpu(), -1)

    losses: list[float] = []
    for step in range(steps):
        with model.trace(batch, remote=True):
            dp = model.model.layers[layer].mlp.down_proj
            out = dp.output
            out.requires_grad_(True)
            out.retain_grad()
            patched = out.clone()
            d = delta.to(out.device, out.dtype)
            patched[0, idx] = patched[0, idx] + d
            patched[1, idx_e] = patched[1, idx_e] + d
            dp.output = patched

            logits = model.lm_head.output.float()
            # Teacher-forced sum over the target's tokens, never position one alone.
            lp = torch.log_softmax(logits[0], -1)
            nll = -sum(lp[n_prompt + j - 1, t] for j, t in enumerate(tgt)) / len(tgt)

            # KL(pre || post) on the essence prompt keeps the subject recognisable.
            post = torch.log_softmax(logits[1, last_ess], -1)
            ref = ref_logp.to(post.device)
            kl = torch.sum(torch.exp(ref) * (ref - post))

            loss = nll + kl_factor * kl + weight_decay * (d * d).sum()
            loss.backward()
            g = out.grad[0, idx].float().save()
            lv = loss.float().save()
            nv = nll.float().save()

        delta = delta - lr * g.cpu()
        if float(delta.norm()) > max_norm:          # ROME's clamp_norm_factor
            delta = delta * (max_norm / float(delta.norm()))
        losses.append(float(lv))
        log.debug("step %2d/%d  loss %.4f  nll %.4f  norm %.2f",
                  step + 1, steps, float(lv), float(nv), float(delta.norm()))

    return delta, losses


@dataclass(frozen=True)
class EditSpec:
    """One requested edit, before `v*` is known."""

    case_id: str
    prompt: str
    subject: str
    target: str
    kind: str = "real"        # "real" | "control"


def compute_v_batch(model, specs: list[EditSpec], *, layer: int = LAYER,
                    steps: int = V_NUM_GRAD_STEPS, lr: float = V_LR,
                    weight_decay: float = V_WEIGHT_DECAY,
                    clamp_norm_factor: float = CLAMP_NORM_FACTOR,
                    kl_factor: float = KL_FACTOR,
                    progress=None) -> dict[str, torch.Tensor]:
    """Optimise every spec's `delta` in ONE remote trace per step, not one per edit.

    Sequentially this is `len(specs) * steps` round trips — 78 chains x 2 edits x 25
    steps is 3900 traces, about five hours at the measured 4s each. Batched it is
    `steps` traces, because each row of the batch carries its own prompt, its own
    subject-last index and its own delta, and the returned gradient is per-row.
    Round trips are this project's budget; this is the same move as batching the
    possession scorer.

    Rows are [rewrite_0, essence_0, rewrite_1, essence_1, ...] so each edit's KL
    anchor travels with it. Right padding only — index positions come from unpadded
    text and left padding would silently shift every one of them.
    """
    tok = model.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    rows, meta = [], []
    for sp in specs:
        full = sp.prompt + (sp.target if sp.target.startswith(" ") else " " + sp.target)
        essence = f"{sp.subject} is a"
        ids_f, ids_e = tok(full).input_ids, tok(essence).input_ids
        meta.append({
            "case_id": sp.case_id,
            "idx": subject_last_index(tok, sp.prompt, sp.subject),
            "idx_e": subject_last_index(tok, essence, sp.subject),
            "n_prompt": len(tok(sp.prompt).input_ids),
            "tgt": _target_ids(tok, sp.target),
            "last_e": len(ids_e) - 1,
        })
        rows += [ids_f, ids_e]

    width = max(len(r) for r in rows)
    batch = torch.full((len(rows), width), pad, dtype=torch.long)
    for i, r in enumerate(rows):
        batch[i, : len(r)] = torch.tensor(r)

    # Pre-edit essence distributions, all in one trace.
    with model.trace(batch, remote=True):
        ref_all = model.lm_head.output.float().save()
    ref_logp = {m["case_id"]: torch.log_softmax(ref_all[2 * i + 1, m["last_e"]].cpu(), -1)
                for i, m in enumerate(meta)}

    d_model = model.config.hidden_size
    deltas = {m["case_id"]: torch.zeros(d_model) for m in meta}
    max_norm: dict[str, float] = {}
    for sp in specs:
        _, wk = read_key_and_value(model, sp.prompt, sp.subject, layer)
        max_norm[sp.case_id] = clamp_norm_factor * float(wk.norm())

    for step in range(steps):
        D = torch.stack([deltas[m["case_id"]] for m in meta])        # [n_specs, d_model]
        # Transport retry, which this path lacked until a run died overnight on the
        # third `engineio.client packet queue is empty`. `score_pairs` has classified
        # and retried transport failures since the httpx.ConnectTimeout incident; the
        # edit path called `model.trace` bare, so one dropped socket killed a chunk and
        # then the process. Same classifier, same linear backoff — no new policy.
        for attempt in range(MAX_ATTEMPTS):
            try:
                g_all, lv = _grad_step(model, batch, meta, D, layer, ref_logp,
                                       kl_factor, weight_decay)
                break
            except Exception as exc:  # noqa: BLE001 — narrowed by the classifier
                if not _is_transport_error(exc) or attempt == MAX_ATTEMPTS - 1:
                    raise
                wait = BACKOFF_S * (attempt + 1)
                log.warning("transport failure (%s) on v* step %d attempt %d/%d; "
                            "retrying in %.0fs", type(exc).__name__, step + 1,
                            attempt + 1, MAX_ATTEMPTS, wait)
                time.sleep(wait)

        for i, mm in enumerate(meta):
            cid = mm["case_id"]
            d = deltas[cid] - lr * g_all[2 * i, mm["idx"]].cpu()
            n = float(d.norm())
            deltas[cid] = d * (max_norm[cid] / n) if n > max_norm[cid] else d
        log.debug("batch step %2d/%d  summed loss %.4f", step + 1, steps, float(lv))
        if progress:
            progress(step + 1, steps)

    return deltas


def _grad_step(model, batch, meta, D, layer, ref_logp, kl_factor, weight_decay):
    """One optimisation step. Separate function ONLY so the retry above can call it.

    Every proxy operation stays inline in this frame's own `with` — nnsight reads the
    source of the frame that enters `model.trace`, so a nested helper would be
    silently dropped. See APPLY_IDIOM.
    """
    if True:
        with model.trace(batch, remote=True):
            dp = model.model.layers[layer].mlp.down_proj
            out = dp.output
            out.requires_grad_(True)
            out.retain_grad()
            patched = out.clone()
            Dd = D.to(out.device, out.dtype)
            for i, mm in enumerate(meta):
                patched[2 * i, mm["idx"]] = patched[2 * i, mm["idx"]] + Dd[i]
                patched[2 * i + 1, mm["idx_e"]] = patched[2 * i + 1, mm["idx_e"]] + Dd[i]
            dp.output = patched

            logits = model.lm_head.output.float()
            total = 0.0
            for i, mm in enumerate(meta):
                lp = torch.log_softmax(logits[2 * i], -1)
                nll = -sum(lp[mm["n_prompt"] + j - 1, t]
                           for j, t in enumerate(mm["tgt"])) / len(mm["tgt"])
                post = torch.log_softmax(logits[2 * i + 1, mm["last_e"]], -1)
                ref = ref_logp[mm["case_id"]].to(post.device)
                kl = torch.sum(torch.exp(ref) * (ref - post))
                total = total + nll + kl_factor * kl + weight_decay * (Dd[i] * Dd[i]).sum()
            total.backward()
            g_all = out.grad.float().save()
            lv = total.float().save()
    return g_all, lv
