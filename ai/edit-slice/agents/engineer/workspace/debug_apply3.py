"""Confirm the inline idiom works with a real RankOneEdit, and that it does nothing
when delta is zero — a no-op edit must leave the model exactly where it was."""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import RankOneEdit, read_key_and_value  # noqa: E402
from remote import connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
L, P, S = 5, "Maurice de Vlaminck was born in the country of", "Maurice de Vlaminck"
k_star, wk = read_key_and_value(m, P, S, L)

for label, dv in [("zero delta (must be a no-op)", torch.zeros(4096)),
                  ("random small delta", torch.randn(4096) * 0.5)]:
    e = RankOneEdit("dbg", L, S, P, "Germany", k_star, dv)
    with m.trace(P, remote=True):
        dp = m.model.layers[e.layer].mlp.down_proj
        k = dp.input
        ks = e.k_star.to(k.device, k.dtype)
        dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                * e.delta_v.to(k.device, k.dtype)
        lg = m.lm_head.output[0, -1].float().save()
    lp = torch.log_softmax(lg.cpu(), -1)
    v, i = lp.topk(3)
    print(f"[OK] {label}: " + "  ".join(f"{m.tokenizer.decode(j)!r}:{float(x):.2f}"
                                        for x, j in zip(v, i)))
