"""Does compute_v_batch reproduce compute_v on the edit whose answer we know?

The smoke test drove Vlaminck -> Germany to NLL 0.02 with the sequential path. The
batched path must land in the same place, or the batching is silently wrong — the
failure mode would be indices crossing between rows, which produces plausible
numbers rather than an error.
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect  # noqa: E402

log = setup("verify_batch", config={"ticket": "E-013", "check": "batched == sequential"})
m = connect("meta-llama/Llama-3.1-8B")

SPECS = [
    EditSpec("vlaminck", "Maurice de Vlaminck was born in the country of",
             "Maurice de Vlaminck", "Germany"),
    EditSpec("natsuki", "Rio Natsuki was born in the country of", "Rio Natsuki", "Brazil"),
    EditSpec("vlaminck_ctl", "By profession, Maurice de Vlaminck is a",
             "Maurice de Vlaminck", "chef", kind="control"),
]

deltas = compute_v_batch(m, SPECS, progress=lambda i, n: log.info("step %d/%d", i, n)
                         if i % 5 == 0 else None)

for sp in SPECS:
    dv = deltas[sp.case_id]
    k_star, _ = read_key_and_value(m, sp.prompt, sp.subject, LAYER)
    lay = LAYER
    ks_cpu, dv_cpu = k_star, dv
    with m.trace(sp.prompt, remote=True):
        dp = m.model.layers[lay].mlp.down_proj
        k = dp.input
        ks = ks_cpu.to(k.device, k.dtype)
        dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                * dv_cpu.to(k.device, k.dtype)
        lg = m.lm_head.output[0, -1].float().save()
    lp = torch.log_softmax(lg.cpu(), -1)
    v, i = lp.topk(3)
    log.info("%-14s target %-9r -> %s", sp.case_id, sp.target,
             "  ".join(f"{m.tokenizer.decode(j)!r}:{float(x):.2f}" for x, j in zip(v, i)))
    log.info("%-14s ‖delta‖ %.2f", "", float(dv.norm()))
