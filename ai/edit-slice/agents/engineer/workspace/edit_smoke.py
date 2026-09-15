"""E-013 · One edit, end to end. Does the machinery work at all?

Vlaminck: born in Paris (inner_1), Paris in France (inner_2), therefore born in
France (outer). Edit the OUTER to Germany and look at all three.

This is a smoke test, not the experiment. n=1 shows nothing about contraction — it
shows whether the edit applies and whether the probes move at all.
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, RankOneEdit, compute_v, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect  # noqa: E402

SUBJ, CITY, COUNTRY, TARGET = "Maurice de Vlaminck", "Paris", "France", "Germany"
OUTER = f"{SUBJ} was born in the country of"
INNER1 = f"{SUBJ} was born in the city of"
INNER2 = f"{CITY} is located in the country of"

log = setup("edit_smoke", config={"ticket": "E-013", "model": "meta-llama/Llama-3.1-8B",
                                  "layer": LAYER, "subject": SUBJ,
                                  "edit": f"{COUNTRY} -> {TARGET}"})
m = connect("meta-llama/Llama-3.1-8B")


def top(prompts, edit=None, k=3):
    out = []
    for p in prompts:
        if edit is None:
            with m.trace(p, remote=True):
                lg = m.lm_head.output[0, -1].float().save()
        else:
            lay, ks_cpu, dv_cpu = edit.unpack()   # OUTSIDE the trace — see APPLY_IDIOM
            with m.trace(p, remote=True):
                dp = m.model.layers[lay].mlp.down_proj
                k = dp.input
                ks = ks_cpu.to(k.device, k.dtype)
                dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                        * dv_cpu.to(k.device, k.dtype)
                lg = m.lm_head.output[0, -1].float().save()
        lp = torch.log_softmax(lg.cpu(), -1)
        vals, idx = lp.topk(k)
        out.append([(m.tokenizer.decode(i), float(v)) for v, i in zip(vals, idx)])
    return out


PROMPTS = [OUTER, INNER1, INNER2]
NAMES = ["outer  (edited)", "inner_1 (ground)", "inner_2 (ground)"]

log.info("=== BEFORE ===")
before = top(PROMPTS)
for n, row in zip(NAMES, before):
    log.info("%-18s %s", n, "  ".join(f"{t!r}:{v:.2f}" for t, v in row))

log.info("optimising v* ...")
delta, losses = compute_v(m, OUTER, SUBJ, TARGET)
log.info("loss %.4f -> %.4f over %d steps, final norm %.2f",
         losses[0], losses[-1], len(losses), float(delta.norm()))

k_star, _ = read_key_and_value(m, OUTER, SUBJ, LAYER)
e = RankOneEdit("smoke", LAYER, SUBJ, OUTER, TARGET, k_star, delta)

log.info("=== AFTER ===")
after = top(PROMPTS, edit=e)
for n, row in zip(NAMES, after):
    log.info("%-18s %s", n, "  ".join(f"{t!r}:{v:.2f}" for t, v in row))

log.info("=== movement of the PRE-EDIT correct answer ===")
for n, p, want, b, a in zip(NAMES, PROMPTS, [COUNTRY, CITY, COUNTRY], before, after):
    bd = dict(b).get(" " + want)
    ad = dict(a).get(" " + want)
    log.info("%-18s %r  before %s  after %s", n, want,
             f"{bd:.2f}" if bd is not None else "not in top-3",
             f"{ad:.2f}" if ad is not None else "not in top-3")
