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
from dataclasses import dataclass
from typing import Final

import torch

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
