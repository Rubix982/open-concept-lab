"""E-016 · Where along the probe does the displacement actually enter?

Two mechanistic guesses have now failed. Guess 1: the probe key is aligned with k* and
whitening preserves it — refuted, cos = 0.034. Guess 2: the destination is invariant to
the displacement's scale — refuted, x0.27 breaks relocation in 3 of 4 chains.

So measure instead of predicting. The edit applies at EVERY position, and the `inner_1`
prompt contains the same subject as the edit prompt. If the displacement enters at the
SUBJECT tokens, the key there is near-identical to k* — and ROME normalises by `u·k*`, so
that position's coefficient is ~1 by construction under ANY `C`. That would explain why no
whitening can change the outcome while a uniform rescale can.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying  # noqa: E402
from whiten import Whitener  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LAM = 7.2e-03

log = setup("coeff_profile", config={"ticket": "E-016", "lam": LAM, "layer": LAYER})
chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
K = torch.load(ROOT / "results" / "cache" / "E016_keys_L5.pt").float()
ks14 = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
W = Whitener(K, LAM)

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer

for cid in ("254", "273", "345"):
    c = chains[cid]
    p1, subj = c["inner_1"]["prompt"], c["inner_1"]["subject"]
    kstar = ks14[f"{cid}|real"].float()
    u = W.apply(kstar)
    den_w = float(u @ kstar)
    den_i = float(kstar @ kstar)

    def once():
        with m.trace(p1, remote=True):
            k = m.model.layers[LAYER].mlp.down_proj.input[0].half().save()
        return k

    keys = retrying(once, what=f"probe keys {cid}").float()
    ids = tok(p1).input_ids
    s_idx = subject_last_index(tok, p1, subj)
    log.info("")
    log.info("chain %s — %r  (subject ends at token %d)", cid, p1, s_idx)
    log.info("   %-4s%-14s%12s%12s%9s", "pos", "token", "coeff C=I", "coeff C^-1", "ratio")
    for j in range(len(ids)):
        ci = float((keys[j] @ kstar) / den_i)
        cw = float((keys[j] @ u) / den_w)
        mark = "  <- subject-last" if j == s_idx else ""
        if abs(ci) > 0.05 or j == s_idx or j == len(ids) - 1:
            log.info("   %-4d%-14r%12.4f%12.4f%9.2fx%s", j, tok.decode([ids[j]]),
                     ci, cw, cw / ci if ci else float("nan"), mark)
    tot_i = float(sum(abs((keys[j] @ kstar) / den_i) for j in range(len(ids))))
    tot_w = float(sum(abs((keys[j] @ u) / den_w) for j in range(len(ids))))
    log.info("   total |coeff| over the prompt: C=I %.3f  C^-1 %.3f  (%.2fx)",
             tot_i, tot_w, tot_w / tot_i)
