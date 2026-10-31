"""`coefficient_for` end to end against a stand-in model.

Every assertion here corresponds to something that was wrong in the first draft
of this function, so the file is also the record of what the hacks were.
"""

from __future__ import annotations

import pytest
import torch

from editreach.coefficient import Regime, coefficient_for

D_MLP = 8


def _u(scale: float = 1.0) -> torch.Tensor:
    return torch.full((D_MLP,), scale)


def test_it_reads_the_position_it_was_given(fake_model) -> None:
    """The key at position p is p's token id in every channel, so c is computable.

    This is the bug the first draft had: the batch was tokenised with
    `padding=True`, which pads LEFT on Llama, so every index was shifted.
    """
    prompts = ["abcdef", "xy"]          # different lengths force padding
    positions = [5, 1]
    denom = 4.0
    got = coefficient_for(fake_model, prompts, positions, u=_u(), denom=denom, layer=0,
                          remote=False)
    for c, p, pos in zip(got, prompts, positions):
        token_id = (ord(p[pos]) % 49) + 1
        assert c.value == pytest.approx(token_id * D_MLP / denom)


def test_the_short_prompt_is_not_read_in_its_padding(fake_model) -> None:
    """Right padding is what keeps an unpadded index valid. Left padding would
    put prompt 2's position 1 inside the pad region and return the pad key."""
    got = coefficient_for(fake_model, ["abcdefghij", "xy"], [0, 0], u=_u(), denom=1.0,
                          layer=0, remote=False)
    assert got[1].value == pytest.approx(((ord("x") % 49) + 1) * D_MLP)
    assert got[1].value != 0.0          # a pad token id of 0 would give exactly this


def test_a_position_past_the_prompt_is_refused_with_a_useful_message(fake_model) -> None:
    with pytest.raises(IndexError, match="never padding"):
        coefficient_for(fake_model, ["abc"], [7], u=_u(), denom=1.0, layer=0, remote=False)


def test_a_zero_denominator_is_refused(fake_model) -> None:
    with pytest.raises(ValueError, match="orthogonal"):
        coefficient_for(fake_model, ["abc"], [0], u=_u(), denom=0.0, layer=0, remote=False)


def test_a_u_of_the_wrong_width_is_refused_before_the_trace(fake_model) -> None:
    """d_mlp comes from the config. A mismatched u would otherwise broadcast or
    fail deep inside the trace with an unreadable message."""
    with pytest.raises(ValueError, match="d_mlp"):
        coefficient_for(fake_model, ["abc"], [0], u=torch.ones(3), denom=1.0, layer=0,
                        remote=False)


def test_a_layer_outside_the_model_is_refused(fake_model) -> None:
    with pytest.raises(IndexError, match="outside"):
        coefficient_for(fake_model, ["abc"], [0], u=_u(), denom=1.0, layer=99, remote=False)


def test_the_regime_is_carried_through(fake_model) -> None:
    got = coefficient_for(fake_model, ["abc"], [0], u=_u(), denom=1.0, layer=0,
                          regime=Regime.PREFIX_SHARING, remote=False)
    assert got[0].is_analytic
