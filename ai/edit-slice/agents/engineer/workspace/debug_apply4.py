"""Is it attribute access on a Python object inside the trace?"""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import RankOneEdit, read_key_and_value  # noqa: E402
from remote import connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
L, P, S = 5, "Maurice de Vlaminck was born in the country of", "Maurice de Vlaminck"
k_star, wk = read_key_and_value(m, P, S, L)
e = RankOneEdit("dbg", L, S, P, "Germany", k_star, torch.randn(4096) * 0.5)

print("--- A: dataclass attributes used INSIDE the trace ---")
try:
    with m.trace(P, remote=True):
        dp = m.model.layers[e.layer].mlp.down_proj
        k = dp.input
        ks = e.k_star.to(k.device, k.dtype)
        dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                * e.delta_v.to(k.device, k.dtype)
        lg = m.lm_head.output[0, -1].argmax(-1).save()
    print("  [OK]", repr(m.tokenizer.decode(lg)))
except Exception as exc:
    print(f"  [FAIL] {type(exc).__name__}: {str(exc)[:90]}")

print("--- B: attributes HOISTED to plain locals before the trace ---")
lay, kv, dvv = e.layer, e.k_star, e.delta_v
try:
    with m.trace(P, remote=True):
        dp = m.model.layers[lay].mlp.down_proj
        k = dp.input
        ks = kv.to(k.device, k.dtype)
        dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                * dvv.to(k.device, k.dtype)
        lg = m.lm_head.output[0, -1].argmax(-1).save()
    print("  [OK]", repr(m.tokenizer.decode(lg)))
except Exception as exc:
    print(f"  [FAIL] {type(exc).__name__}: {str(exc)[:90]}")
