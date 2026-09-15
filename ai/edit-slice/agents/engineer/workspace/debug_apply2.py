"""Is the failure that apply_delta lives in another module?"""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import RankOneEdit, apply_delta  # noqa: E402
from remote import connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
L, P = 5, "Maurice de Vlaminck was born in the country of"
e = RankOneEdit("dbg", L, "x", P, "y", torch.randn(14336), torch.randn(4096) * 0.01)


def local_apply(model, edit):
    """Same body, defined in THIS file rather than src/edit.py."""
    dp = model.model.layers[edit.layer].mlp.down_proj
    k = dp.input
    ks = edit.k_star.to(k.device, k.dtype)
    dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) * edit.delta_v.to(k.device, k.dtype)


for name, fn in [("helper in src/edit.py", apply_delta), ("helper in THIS file", local_apply)]:
    try:
        with m.trace(P, remote=True):
            fn(m, e)
            t = m.lm_head.output[0, -1].argmax(-1).save()
        print(f"[OK]   {name}: {m.tokenizer.decode(t)!r}")
    except Exception as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {str(exc)[:110]}")
