"""E-016 · The whitened ROME update, without ever forming a 14336x14336 matrix.

ROME's update uses `u = C⁻¹k*` where `C` is the second-moment matrix of MLP keys at the
edited layer. [E-013] gate 0 established that EasyEdit ships `mom2_adjustment: false` for
all fourteen of its configs, so everything in [E-013]–[E-015] ran `u = k*`. This module
supplies the other arm.

**Why this is tractable on a 16 GB machine.** `C` is 14336² = 0.82 GB fp32, and inverting
it is worse. But the measured spectrum (E-016 gate, N=2048) puts 50% of variance in 16
dimensions and 99% in 338 — a participation ratio of 26.5 out of 2048. So the right model
is low-rank plus isotropic, `C = KᵀK/N + λI`, and Woodbury gives

    (KᵀK/N + λI)⁻¹ k*  =  (1/λ)[ k* − Kᵀ (λN·I + KKᵀ)⁻¹ K k* ]

in which only `KKᵀ` (N × N) is ever formed. At N = 2048 that is 17 MB.

**What λ is doing, stated plainly.** With N < d the sample covariance is singular, so λ is
not a nuisance parameter — it sets the noise floor the low-variance directions are divided
by, and it therefore controls how aggressively the update is steered. Any result from this
module must be reported with its λ and with a sensitivity sweep. A single λ silently chosen
would be the [E-009b] mistake in a new costume.

**Corpus divergence, recorded:** keys are collected over the CounterFact prompt
distribution, not ROME's Wikipedia. Domain-conditional and arguably better matched to what
we edit, but it is not what ROME does.
"""

from __future__ import annotations

import logging
from typing import Final

import torch

log: Final[logging.Logger] = logging.getLogger("whiten")


class Whitener:
    """Applies `C⁻¹` to a key vector via Woodbury, given a sample key matrix."""

    def __init__(self, K: torch.Tensor, lam: float) -> None:
        """`K` is [N, d] of sampled keys; `lam` is the ridge on the isotropic remainder."""
        self.K = K.double()
        self.N, self.d = K.shape
        self.lam = float(lam)
        # (lam*N*I + K Kᵀ) — N x N, the only matrix ever materialised.
        G = self.K @ self.K.T
        G.diagonal().add_(self.lam * self.N)
        self.chol = torch.linalg.cholesky(G)
        log.info("whitener ready: N=%d d=%d lam=%.3e (solve is %dx%d)",
                 self.N, self.d, self.lam, self.N, self.N)

    def apply(self, k: torch.Tensor) -> torch.Tensor:
        """Return `C⁻¹k` with `C = KᵀK/N + λI`."""
        kd = k.double()
        rhs = (self.K @ kd).unsqueeze(-1)                      # [N, 1]
        sol = torch.cholesky_solve(rhs, self.chol).squeeze(-1)  # [N]
        return ((kd - self.K.T @ sol) / self.lam).float()

    def steer(self, k: torch.Tensor) -> float:
        """Cosine between `k` and `C⁻¹k` — 1.0 means whitening changed nothing.

        The honest one-number summary of whether this arm differs from the C = I arm at
        all, per item rather than in aggregate.
        """
        u = self.apply(k)
        return float(torch.nn.functional.cosine_similarity(
            k.float().unsqueeze(0), u.unsqueeze(0)).item())


def suggested_lambdas(K: torch.Tensor, n: int = 5) -> list[float]:
    """A sweep bracketing the spectrum, so λ is chosen by sensitivity and not by taste.

    Anchored on mean eigenvalue = trace(C)/d, which is the isotropic-equivalent scale.
    """
    trace_over_d = float((K.double() ** 2).sum() / (K.shape[0] * K.shape[1]))
    return [trace_over_d * (10.0 ** e) for e in range(-2, -2 + n)]
