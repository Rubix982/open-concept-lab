"""Predictors of edit propagation.

The design (design.md §5) compares three families as predictors, with raw
distance demoted to a BASELINE after E-007 showed it near-flat:
  - raw distance        (baseline)                         — cosine of reps
  - alignment           (Jeong / STEAM)                    — cos to a semantic anchor
  - structured          (Kim bilinear / Function Vectors)  — STUB, v1/v2

All operate on representations from `reps.py`.
"""

import torch

from . import config, reps


def cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


# ── Baseline: raw distance ─────────────────────────────────────────────────────
def raw_distance(base: str, neighbour: str, layer: int = config.DEFAULT_LAYER,
                 how: str = "mean") -> float:
    """cos(rep(base), rep(neighbour)). The confounded baseline (E-007)."""
    return cosine(reps.rep(base, layer, how), reps.rep(neighbour, layer, how))


# ── Alignment (Jeong / STEAM) ──────────────────────────────────────────────────
def anchor(answer: str, ref_prompts: list[str], layer: int = config.DEFAULT_LAYER,
           how: str = "mean", k: int = config.K_ANCHOR) -> torch.Tensor | None:
    """Semantic anchor φ(answer) = mean rep of up to k reference prompts.
    Returns None if fewer than k references are available."""
    if len(ref_prompts) < k:
        return None
    chosen = sorted(ref_prompts)[:k]
    return torch.stack([reps.rep(p, layer, how) for p in chosen]).mean(dim=0)


def alignment(neighbour: str, phi: torch.Tensor, layer: int = config.DEFAULT_LAYER,
              how: str = "mean") -> float:
    """cos(rep(neighbour), anchor). Jeong-style structured/alignment predictor."""
    return cosine(reps.rep(neighbour, layer, how), phi)


# ── Structured (Kim bilinear / Function Vectors) — STUB ────────────────────────
def structured_bilinear(*_args, **_kwargs) -> float:  # noqa: D401
    """TODO (E-009+): Kim bilinear f_r(s,o)=sᵀ M_r o, M_r fit per relation via
    ridge (RESCAL). Also consider Function Vectors (Todd) as an NNsight-native
    basis. See design.md §5 / readings/MAP.md."""
    raise NotImplementedError("structured predictor: implement in E-009+")
