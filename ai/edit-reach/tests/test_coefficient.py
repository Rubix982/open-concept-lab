"""The coefficient object, and the distinction it has to keep straight."""

from __future__ import annotations

from editreach.coefficient import PRECEDED, PREFIX_SHARING, Coefficient
from editreach.control import Baseline


def _c(value: float, regime: str, layer: int = 5) -> Coefficient:
    return Coefficient(prompt="p", position=3, layer=layer, value=value, regime=regime)


def test_prefix_sharing_is_flagged_analytic() -> None:
    """u cancels, so 1.000 here is arithmetic and not evidence about the rule."""
    assert _c(1.000, PREFIX_SHARING).is_analytic


def test_a_preceded_subject_is_not_analytic() -> None:
    assert not _c(0.982, PRECEDED).is_analytic


def test_a_coefficient_only_becomes_a_reading_with_a_floor() -> None:
    r = _c(0.982, PRECEDED).against(Baseline.of("different subject", [0.065, 0.070]))
    assert r.label == "preceded @ L5"
    assert r.margin > 0.9


def test_a_coefficient_is_immutable() -> None:
    c = _c(1.0, PREFIX_SHARING)
    try:
        c.value = 0.5        # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Coefficient should be frozen")
