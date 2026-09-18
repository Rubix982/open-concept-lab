"""E-016 · Why did a 20x more selective update produce identical outputs?

Whitening shrinks the update's reach on UNRELATED inputs. The `inner_1` probe is not
unrelated — it shares the subject with the edit, so its key should be aligned with `k*`,
and an aligned direction is exactly what whitening preserves. If that is right, the
coefficient on `inner_1` is untouched while the coefficient on random keys collapses,
and [E-015]/[E-016]'s null is not merely robust but mechanically expected.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying  # noqa: E402
from whiten import Whitener  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LAM = 7.2e-03

log = setup("why_whitening_null", config={"ticket": "E-016", "lam": LAM, "layer": LAYER})
chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
e15 = json.loads((ROOT / "results" /
                  "E-015-relation-meta-llama_Llama-3.1-8B.json").read_text())["results"][:12]
K = torch.load(ROOT / "results" / "cache" / "E016_keys_L5.pt").float()
ks14 = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

prompts = [chains[r["case_id"]]["inner_1"]["prompt"] for r in e15]
ids = [tok(p).input_ids for p in prompts]
width = max(len(x) for x in ids)
batch = torch.full((len(ids), width), pad, dtype=torch.long)
for j, x in enumerate(ids):
    batch[j, : len(x)] = torch.tensor(x)

def once():
    with m.trace(batch, remote=True):
        k = m.model.layers[LAYER].mlp.down_proj.input.half().save()
    return k

got = retrying(once, what="inner_1 keys")
probe_keys = torch.stack([got[j, len(ids[j]) - 1].float() for j in range(len(ids))])
log.info("read %d inner_1 keys at the final position", probe_keys.shape[0])

W = Whitener(K, LAM)
log.info("")
log.info("%-8s%14s%16s%16s%14s", "chain", "cos(k*,probe)", "coeff C=I", "coeff C^-1", "ratio")
rows = []
for j, r in enumerate(e15):
    kstar = ks14[f"{r['case_id']}|real"].float()
    pk = probe_keys[j]
    u = W.apply(kstar)
    c_i = float((pk @ kstar) / (kstar @ kstar))
    c_w = float((pk @ u) / (u @ kstar))
    cos = float(torch.nn.functional.cosine_similarity(
        pk.unsqueeze(0), kstar.unsqueeze(0)).item())
    rows.append((cos, c_i, c_w))
    log.info("%-8s%14.3f%16.4f%16.4f%13.2fx",
             r["case_id"], cos, c_i, c_w, c_w / c_i if c_i else float("nan"))

# the same two coefficients on genuinely unrelated keys
rnd = K[torch.randperm(K.shape[0])[:512]]
u0 = W.apply(ks14[f"{e15[0]['case_id']}|real"].float())
k0 = ks14[f"{e15[0]['case_id']}|real"].float()
u_i = float(((rnd @ k0) / (k0 @ k0)).abs().mean())
u_w = float(((rnd @ u0) / (u0 @ k0)).abs().mean())
log.info("")
log.info("mean |coeff| on SAME-SUBJECT inner_1 probes : C=I %.4f  C^-1 %.4f  (%.2fx)",
         sum(abs(c) for _, c, _ in rows) / len(rows),
         sum(abs(c) for _, _, c in rows) / len(rows),
         (sum(abs(c) for _, _, c in rows) / len(rows))
         / (sum(abs(c) for _, c, _ in rows) / len(rows)))
log.info("mean |coeff| on UNRELATED random keys      : C=I %.4f  C^-1 %.4f  (%.2fx)",
         u_i, u_w, u_w / u_i)
log.info("")
log.info("If the same-subject ratio is ~1 while the unrelated ratio is ~0.05, whitening")
log.info("cannot touch subject-keyed displacement: it preserves exactly the direction")
log.info("the displacement travels along.")
