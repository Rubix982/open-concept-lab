"""How much of a rank-one edit arrives at a token — read without applying it.

ROME rewrites one MLP output projection so that `W' = W + (v* - W k*) uᵀ / (uᵀ k*)`.
For any token whose key at that layer is `k`, the update that lands on it is
`delta_v` scaled by

    c = (k · u) / (u · k*)

and that scalar is this module's whole subject. Two properties make it worth
having a name of its own:

1. **It needs no edit.** `u`, the denominator and `k` are all read from the
   *unedited* model, so an item can be scored before anything is changed.
2. **It needs no list.** It is defined for any prompt, including prompts nobody
   thought to write down. That is what makes it an alternative to enumerating a
   benchmark rather than another benchmark.

In edit-slice this expression lived inline inside `score_pairs`' edit tuple and
was re-derived in each run script. It is the thing being claimed, so here it is
an object.

**What a coefficient is not.** It measures *delivery*, not *effect*: how much of
the edit vector arrives, never how far the model's answer moves as a result.
Whether the first predicts the second is an open measurement (C-001), and until
it closes, nothing here licenses a behavioural claim.

Two regimes, and they are different kinds of statement:

- A probe that **begins** with the edited subject has `k = k*` under causal
  attention, so `c = 1` by arithmetic. Measuring it tests the implementation
  (padding, position, tokenisation), not the rule — `u` cancels.
- A probe where something **precedes** the subject has no such guarantee. There
  `c` is empirical, and it falls with depth: about 0.93 at layer 5, 0.79 at
  layer 12, 0.52 by layer 24 [T-075].
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Sequence

import torch

from .control import Baseline, Reading, require_baseline
from .arch import key_site, resolve_arch
from .remote import encode_prompts, quiet_stdout, retrying
from .rome import LAYER

class Regime(str, Enum):
    """Probe shapes, kept apart because they license different claims.

    An enum rather than a free string: the two carry different epistemic weight
    and a typo must not quietly turn an analytic reading into an empirical one.
    """

    PREFIX_SHARING = "prefix-sharing"
    PRECEDED = "preceded"


PREFIX_SHARING: Final[Regime] = Regime.PREFIX_SHARING
PRECEDED: Final[Regime] = Regime.PRECEDED


@dataclass(frozen=True, slots=True)
class Coefficient:
    """One reading of `(k·u)/(u·k*)`, with the prompt and position it came from."""

    prompt: str
    position: int
    layer: int
    value: float
    regime: Regime

    @property
    def is_analytic(self) -> bool:
        """True when the value follows from the algebra rather than from the model.

        A 1.000 here is not evidence about the update rule. See the module
        docstring: `u` appears in both numerator and denominator.
        """
        return self.regime is Regime.PREFIX_SHARING

    def against(self, floor: Baseline) -> Reading:
        """Pair this value with the control that makes it readable."""
        return require_baseline(self.value, floor, label=f"{self.regime.value} @ L{self.layer}")


def coefficient_for(
    model,
    prompts: Sequence[str],
    positions: Sequence[int],
    *,
    u: torch.Tensor,
    denom: float,
    layer: int = LAYER,
    regime: Regime = Regime.PRECEDED,
    remote: bool = True,
) -> list[Coefficient]:
    """Score prompts on the UNEDITED model. One remote call for the batch.

    `u` and `denom` come from the edit being screened (`u = C⁻¹k*`,
    `denom = u·k*`); `positions[i]` is the token index in `prompts[i]` to read
    at, normally `rome.subject_last_index`.

    The trace body is written inline rather than factored into a helper: nnsight
    compiles the source of the frame that enters `model.trace`, so an
    intervention written in a called function is silently dropped. See
    `rome.APPLY_IDIOM`.
    """
    if len(prompts) != len(positions):
        raise ValueError(f"{len(prompts)} prompts against {len(positions)} positions")
    if not prompts:
        return []

    if denom == 0:
        raise ValueError("denom is u*k, which is zero only if u is orthogonal to k*")

    # Resolved before the trace: the key site differs by architecture and reading
    # the wrong module returns plausible wrong numbers rather than raising.
    site = key_site(model, layer)
    _, _, d_mlp = resolve_arch(model)
    if u.shape[-1] != d_mlp:
        raise ValueError(f"u has width {u.shape[-1]}, but this model's d_mlp is {d_mlp}")

    ids, lengths = encode_prompts(model, list(prompts))
    for i, (pos, n) in enumerate(zip(positions, lengths)):
        if not 0 <= pos < n:
            raise IndexError(
                f"position {pos} is outside prompt {i}, which is {n} tokens long. "
                f"Indices are computed on the UNPADDED prompt and the batch is "
                f"right-padded, so an index past the end means the wrong tokenizer "
                f"or the wrong prompt, never padding."
            )

    def _run() -> list[float]:
        # Inline, not factored into a helper: nnsight compiles the source of the
        # frame that enters `model.trace`, so an intervention written in a called
        # function is silently dropped. See `rome.APPLY_IDIOM`.
        with quiet_stdout():
            with model.trace(ids, remote=remote):
                kk = site.input
                uu = u.to(kk.device, kk.dtype)
                out = (kk @ uu).save()
        return [float(out[i, p]) / denom for i, p in enumerate(positions)]

    values = retrying(_run, what=f"coefficients at L{layer}")
    return [
        Coefficient(prompt=p, position=int(i), layer=layer, value=v, regime=regime)
        for p, i, v in zip(prompts, positions, values)
    ]
