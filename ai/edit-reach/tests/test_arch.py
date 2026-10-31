"""Architecture resolution, which used to live in one run script."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from editreach.arch import UnsupportedArchitecture, key_site, resolve_arch


def _cfg(**kw):
    return SimpleNamespace(config=SimpleNamespace(**kw))


def test_llama_is_resolved_from_the_config_not_the_name() -> None:
    m = _cfg(model_type="llama", num_hidden_layers=32, intermediate_size=14336)
    assert resolve_arch(m, "something-else-entirely") == ("llama", 32, 14336)


def test_gptj_uses_n_inner_when_it_has_one() -> None:
    m = _cfg(model_type="gptj", n_layer=28, n_inner=16384, n_embd=4096)
    assert resolve_arch(m) == ("gptj", 28, 16384)


def test_gptj_falls_back_to_four_times_the_width() -> None:
    m = _cfg(model_type="gptj", n_layer=28, n_inner=None, n_embd=4096)
    assert resolve_arch(m) == ("gptj", 28, 16384)


def test_an_unknown_architecture_raises_rather_than_guessing() -> None:
    """A wrong module path returns plausible numbers, so guessing is the worst option."""
    m = _cfg(model_type="mistral", num_hidden_layers=32, intermediate_size=14336)
    with pytest.raises(UnsupportedArchitecture, match="add it to ARCH"):
        resolve_arch(m, "mistralai/Mistral-7B")


def test_key_site_rejects_a_layer_the_model_does_not_have(fake_model) -> None:
    with pytest.raises(IndexError, match="outside 0..5"):
        key_site(fake_model, 6)
