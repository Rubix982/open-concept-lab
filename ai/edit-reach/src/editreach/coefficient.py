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
    reference: tuple[str, int] | None = None,
) -> list[Coefficient]:
    """Score prompts on the UNEDITED model. One remote call for the batch.

    `u` and `denom` come from the edit being screened (`u = C⁻¹k*`,
    `denom = u·k*`); `positions[i]` is the token index in `prompts[i]` to read
    at, normally `rome.subject_last_index`.

    `reference` is `(prompt, position)` for reading `k*` **in this same trace**
    instead of using the `u`/`denom` passed in. Use it whenever the question is
    whether the pipeline reads the right token, because a cached `k*` carries
    the dtype and batch shape of the session that wrote it: activations come
    back in bf16, whose relative precision is about 2**-8, and a live reading
    against a cached one deviates by ~1e-3 for that reason alone. Measured: the
    42 analytic anchors, which must pin at exactly 1.000, came back with a worst
    deviation of 6.4e-03 against cached `k*` — the arithmetic, not the model.

    The dot product is taken in **float32**, not in the activations' own dtype.
    `u.to(kk.dtype)` would round a float32 `u` down to bf16 before the sum over
    14336 channels, which is the other half of that 6.4e-03. [T-075] brought the
    keys back and did the arithmetic on the CPU for the same reason, and got
    min = max = 1.000 across 216 cells.

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

    all_prompts = list(prompts)
    all_positions = list(positions)
    if reference is not None:
        # The reference row rides in the same batch, so k* and k share a trace,
        # a dtype and a batch shape. Appended last so indices stay stable.
        all_prompts = all_prompts + [reference[0]]
        all_positions = all_positions + [reference[1]]

    ids, lengths = encode_prompts(model, all_prompts)
    for i, (pos, n) in enumerate(zip(all_positions, lengths)):
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
                # float32 BEFORE the sum over d_mlp. Casting u down to the
                # activations' bf16 costs ~2**-8 relative, which is the whole
                # budget for a quantity that must read exactly 1.000.
                kk = site.input.float()
                if reference is None:
                    uu = u.to(kk.device).float()
                    out = (kk @ uu).save()
                    ref = None
                else:
                    keys = kk.save()
                    out = ref = None
            if reference is not None:
                k_star = keys[len(all_prompts) - 1, all_positions[-1]].float()
                den = float(k_star @ k_star)
                return [float(keys[i, p].float() @ k_star) / den
                        for i, p in enumerate(all_positions[:-1])]
        return [float(out[i, p]) / denom for i, p in enumerate(all_positions)]

    values = retrying(_run, what=f"coefficients at L{layer}")
    return [
        Coefficient(prompt=p, position=int(i), layer=layer, value=v, regime=regime)
        for p, i, v in zip(prompts, positions, values)
    ]


def keys_at(
    model,
    prompts: Sequence[str],
    positions: Sequence[int],
    *,
    layer: int = LAYER,
    remote: bool = True,
) -> torch.Tensor:
    """The raw key vectors at `positions[i]` of `prompts[i]`, as float32 on CPU.

    `coefficient_for` answers "how much of *this* edit reaches these tokens".
    This answers the prior question "what are these tokens' keys", which is what
    you need when the same prompt must be scored against **many** different
    `k*` — a floor read on the prompts themselves, rather than borrowed from
    another corpus. Scoring n prompts against n donors costs one remote pass
    here and n² dot products offline, where `coefficient_for` would cost n
    passes.

    Returned as float32 for the same reason the dot product is taken in float32
    inside `coefficient_for`: activations arrive in bf16, whose relative
    precision is about 2**-8, and that is the whole budget for a quantity read
    against a floor of a few hundredths.
    """
    if len(prompts) != len(positions):
        raise ValueError(f"{len(prompts)} prompts against {len(positions)} positions")
    if not prompts:
        return torch.empty(0)

    # Resolved before the trace. nnsight ships the trace body's source to NDIF,
    # so a call into this package inside the body arrives as a
    # `ModuleNotFoundError`. Same constraint as `rome.APPLY_IDIOM`.
    site = key_site(model, layer)

    ids, lengths = encode_prompts(model, prompts)
    for i, (pos, n) in enumerate(zip(positions, lengths)):
        if not 0 <= pos < n:
            raise IndexError(
                f"position {pos} is outside prompt {i}, which is {n} tokens long. "
                f"Indices are computed on the UNPADDED prompt and the batch is "
                f"right-padded, so an index past the end means the wrong "
                f"tokenizer or the wrong prompt, never padding."
            )
    rows = torch.arange(len(prompts))
    where = torch.tensor(list(positions))

    def _run() -> torch.Tensor:
        with quiet_stdout():
            with model.trace(ids, remote=remote):
                # Gathered inside the trace, so one row per prompt comes back
                # rather than the whole batch — the full keys for a 500-row
                # batch are a d_mlp-wide tensor per token and the wire is the
                # budget.
                got = site.input.float()[rows, where].save()
        return got.detach().cpu().float()

    return retrying(_run, what=f"keys at L{layer} x{len(prompts)}")
