"""Does the rank-one intervention apply during generation, not just a single trace?

T-066 needs free generation UNDER the edit. Generation runs several forward passes, so an
intervention written for one may or may not persist. Test before designing around it.
"""
import json
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
m = connect("meta-llama/Llama-3.1-8B")
deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s1538.pt")
kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
e14 = json.loads((ROOT / "results" /
                  "E-014-destination-meta-llama_Llama-3.1-8B.json").read_text())
r = e14["results"][0]
cid = r["case_id"]
chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
P = chains[cid]["inner_1"]["prompt"]
ks_cpu = kstars[f"{cid}|real"]
dv_cpu = deltas[f"{cid}|real"]
den = float(ks_cpu @ ks_cpu)
print(f"chain {cid}: {P!r}  target {r['target_country']}  ranked top-1 {r['top1']['real']!r}")

def base():
    with _quiet_stdout(), m.generate(P, remote=True, max_new_tokens=6):
        o = m.generator.output.save()
    with _quiet_stdout():
        return m.tokenizer.decode(o[0][-6:])

def edited_all():
    with _quiet_stdout(), m.generate(P, remote=True, max_new_tokens=6):
        with m.model.layers[LAYER].mlp.down_proj.all():
            dp = m.model.layers[LAYER].mlp.down_proj
            kk = dp.input
            uu = ks_cpu.to(kk.device, kk.dtype)
            dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                    * dv_cpu.to(kk.device, kk.dtype)
        o = m.generator.output.save()
    with _quiet_stdout():
        return m.tokenizer.decode(o[0][-6:])

for name, fn in (("baseline generate", base), ("edited generate (.all())", edited_all)):
    try:
        print(f"[OK]   {name}: {retrying(fn, what=name)!r}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e).splitlines()[-1][:100]}")
