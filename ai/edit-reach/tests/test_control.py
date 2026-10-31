"""The control module's job is to refuse. These tests check that it does."""

from __future__ import annotations

import pytest

from editreach.control import Baseline, Reading, Unbaselined, require_baseline


def test_a_reading_without_a_baseline_is_refused() -> None:
    with pytest.raises(Unbaselined):
        require_baseline(1.000, None, label="prefix-sharing probe")


def test_an_empty_baseline_is_refused() -> None:
    with pytest.raises(Unbaselined):
        Baseline.of("different subject", [])


def test_margin_is_measured_against_the_floor_not_zero() -> None:
    floor = Baseline.of("different subject", [0.081, 0.032, 0.153, 0.077])
    r = require_baseline(1.000, floor, label="prefix-sharing probe")
    assert r.margin == pytest.approx(1.000 - 0.079, abs=1e-9)
    assert r.discriminates()


def test_layer_31_is_reported_as_unreadable_not_as_a_null() -> None:
    """[T-075]: c_other reached 0.669 against a c_form of 0.699.

    Without the floor, 0.699 reads as a mild recovery from layer 24's 0.633. It
    is not a recovery, and `discriminates()` returning False must not be taken
    as evidence of absence.
    """
    floor = Baseline.of("different subject", [0.669, 0.660, 0.680])
    r = require_baseline(0.699, floor, label="layer 31")
    assert not r.discriminates()
    assert "floor has risen" in str(r)


def test_spread_survives_so_a_collapsed_floor_is_visible() -> None:
    floor = Baseline.of("different subject", [0.032, 0.081, 0.153])
    assert floor.spread == pytest.approx(0.121)


def test_reading_is_immutable() -> None:
    r = Reading(label="x", value=1.0, baseline=Baseline.of("f", [0.08]))
    with pytest.raises(Exception):
        r.value = 2.0        # type: ignore[misc]
