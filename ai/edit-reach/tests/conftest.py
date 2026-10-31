"""A stand-in model, so `coefficient_for` is exercised rather than only imported.

**What this does and does not test.** It tests the parts that were wrong: which
token the coefficient is read at under batching, that padding is added after the
text rather than before it, and that the division by `u*k` is the right way up.
It does **not** test nnsight — the trace here is a plain context manager. Only a
run against a real model tests that, and `tests/test_smoke_remote.py` is where
that lives, skipped unless it is asked for.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch

D_MLP = 8
VOCAB = 50


class _Saveable:
    """nnsight hands back a proxy you call `.save()` on. Here it is already a tensor."""

    def __init__(self, t: torch.Tensor) -> None:
        self._t = t

    def save(self) -> torch.Tensor:
        return self._t


class _Site:
    """Stands for the MLP output projection. Its INPUT is the ROME key."""

    def __init__(self, keys: torch.Tensor) -> None:
        self._keys = keys

    @property
    def input(self) -> "_Keys":
        return _Keys(self._keys)


class _Keys:
    """A proxy for the key tensor. `device` and `dtype` are what the real nnsight
    proxy exposes, and `coefficient_for` moves `u` onto them before the matmul."""

    def __init__(self, t: torch.Tensor) -> None:
        self._t = t

    @property
    def device(self) -> torch.device:
        return self._t.device

    @property
    def dtype(self) -> torch.dtype:
        return self._t.dtype

    def float(self) -> "_Keys":
        """The real proxy supports this, and the code now depends on it: the dot
        product is taken in float32 so that casting u down to bf16 cannot cost
        the ~2**-8 that put 25 of 42 analytic anchors outside their band."""
        return _Keys(self._t.float())

    def save(self) -> torch.Tensor:
        return self._t

    def __matmul__(self, other: torch.Tensor) -> _Saveable:
        return _Saveable(self._t @ other)


class _Tokenizer:
    """One token per character, so a position index is readable by eye."""

    pad_token_id = 0
    eos_token_id = 0

    def __call__(self, text, return_tensors=None, add_special_tokens=True, padding=False):
        if isinstance(text, list):
            raise AssertionError(
                "batched tokenisation would use the tokenizer's padding_side, which "
                "is LEFT for Llama. encode_prompts must right-pad itself."
            )
        ids = torch.tensor([[(ord(c) % (VOCAB - 1)) + 1 for c in text]])
        return SimpleNamespace(input_ids=ids)


class FakeModel:
    """Keys are deterministic in the token id, so the expected answer is computable."""

    def __init__(self, n_layers: int = 6) -> None:
        self.tokenizer = _Tokenizer()
        self.config = SimpleNamespace(
            model_type="llama", num_hidden_layers=n_layers, intermediate_size=D_MLP
        )
        self._ids: torch.Tensor | None = None
        self.model = SimpleNamespace(layers=[SimpleNamespace(mlp=SimpleNamespace(
            down_proj=_LazySite(self, L))) for L in range(n_layers)])

    def keys(self) -> torch.Tensor:
        """[B, T, D_MLP] — key at a position is its token id in every channel."""
        assert self._ids is not None, "trace() was never entered"
        return self._ids.unsqueeze(-1).float().expand(-1, -1, D_MLP).contiguous()

    def trace(self, ids, remote: bool = False):
        self._ids = ids
        return _NullTrace()


class _LazySite:
    def __init__(self, model: FakeModel, layer: int) -> None:
        self._m, self._L = model, layer

    @property
    def input(self):
        return _Keys(self._m.keys())


class _NullTrace:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()
