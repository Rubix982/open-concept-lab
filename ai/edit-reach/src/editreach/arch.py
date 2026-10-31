"""Where the ROME key lives, per architecture.

The key `k` is the **input** to the MLP output projection at the edited layer,
and every architecture spells that path differently. In edit-slice this map was
written inside `run_e027.py` — one run script — while `remote.py` and every
other script hard-coded Llama's path. The headline claim covers four models
including GPT-J, so the resolution belongs in shared code or the claim is only
true in the one script that happened to know about it.

Reading the wrong module does not raise. It returns plausible wrong numbers,
which is the failure mode worth paying to avoid, so the shape is asserted.
"""

from __future__ import annotations

from typing import Callable, Final

#: How to reach the MLP output projection, whose INPUT is the ROME key.
ARCH: Final[dict[str, Callable]] = {
    "llama": lambda m, L: m.model.layers[L].mlp.down_proj,
    "gptj": lambda m, L: m.transformer.h[L].mlp.fc_out,
}


class UnsupportedArchitecture(KeyError):
    """Raised rather than guessed. A wrong module path returns plausible numbers."""


def resolve_arch(model, name: str = "") -> tuple[str, int, int]:
    """`(arch key, n_layers, d_mlp)` read from the config, never from the name.

    Lifted from `edit-slice/agents/engineer/workspace/run_e027.py` unchanged
    except for raising instead of calling `SystemExit`, which a library may not do.
    """
    cfg = model.config
    n = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    mt = (getattr(cfg, "model_type", "") or "").lower()
    if "llama" in mt:
        return "llama", n, cfg.intermediate_size
    if "gptj" in mt or "gpt_j" in mt:
        return "gptj", n, getattr(cfg, "n_inner", None) or 4 * cfg.n_embd
    raise UnsupportedArchitecture(
        f"unsupported architecture {mt!r} for {name!r}; add it to ARCH with the "
        f"path to its MLP output projection"
    )


def key_site(model, layer: int, *, name: str = ""):
    """The module whose input is the ROME key at `layer`."""
    arch, n_layers, _ = resolve_arch(model, name)
    if not 0 <= layer < n_layers:
        raise IndexError(f"layer {layer} outside 0..{n_layers - 1} for a {arch} model")
    return ARCH[arch](model, layer)
