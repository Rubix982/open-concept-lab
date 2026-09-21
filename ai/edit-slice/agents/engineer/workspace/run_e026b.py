"""E-026b · Is the layer-20 edit a real belief change, or a degenerate logit hack?

[E-026] found the layer-20 edit achieves the SAME lift on its injected target as the
layer-5 one (+9.37 vs +9.52 nats, gate ratio 0.98) while damaging other probes 13x less
(0.80 vs 10.19 nats) -- at a coefficient of exactly 1.000 in both cases. Before that is
written down as "delivery does not predict effect", one alternative has to be closed.

    A genuine edit RAISES the target AND SUPPRESSES the true answer, because the two
    compete for the same next-token slot. A degenerate one bolts the target's logit up
    and leaves everything else where it was.

The gate measured only the lift. If the layer-20 edit leaves the TRUE country untouched on
its own edit prompt, its apparent success is a logit artifact and [E-026]'s headline is
unsupported. If it suppresses the true country as hard as layer 5 does, the edit is real
on the prompt it was optimised for and genuinely fails to travel -- which is the finding.

Three remote calls, batched over all subjects. Reuses [E-026]'s caches; no optimisation.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402
from run_e026 import DEEP, MODEL, SHALLOW, load_items  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    items, d5, k5 = load_items(1538)
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    dD = torch.load(ROOT / "results" / "cache" / f"E026_deltas_L{DEEP}_s1538.pt")
    kD = torch.load(ROOT / "results" / "cache" / f"E026_kstar_L{DEEP}_s1538.pt")
    items = [it for it in items if it["cid"] in dD]

    log = setup("run_e026b", config={
        "ticket": "E-026b", "thread": "T-079", "model": MODEL,
        "layers": [SHALLOW, DEEP], "n": len(items),
        "question": "does the deep edit suppress the TRUE answer on its own edit prompt, "
                    "or only raise the target?"})

    m = connect(MODEL)
    # Same prompt, two continuations: the injected target and the true answer.
    true_pairs = [(it["edit_prompt"], nat(chains[it["cid"]]["outer"]["answer"]))
                  for it in items]
    tgt_pairs = [(it["edit_prompt"], it["target"]) for it in items]

    out = {}
    for cond in ("base", f"L{SHALLOW}", f"L{DEEP}"):
        true_s, tgt_s = [], []
        for j, it in enumerate(items):
            if cond == "base":
                ed = None
            elif cond == f"L{SHALLOW}":
                ks, dv = k5[f"{it['cid']}|real"], d5[f"{it['cid']}|real"]
                ed = (SHALLOW, ks, float(ks @ ks), dv)
            else:
                ks, dv = kD[it["cid"]], dD[it["cid"]]
                ed = (DEEP, ks, float(ks @ ks), dv)
            sc = retrying(lambda p=[true_pairs[j], tgt_pairs[j]], e=ed:
                          score_pairs(m, p, edit=e),
                          what=f"{cond} {it['cid']}")
            true_s.append(sc[0])
            tgt_s.append(sc[1])
        out[cond] = {"true": true_s, "target": tgt_s}
        log.info("%-6s  log P(true answer) %7.2f   log P(injected target) %7.2f",
                 cond, st.mean(true_s), st.mean(tgt_s))

    log.info("")
    log.info("On the EDIT PROMPT ITSELF (n=%d):", len(items))
    log.info("%-8s%14s%14s%14s", "layer", "true drop", "target lift", "margin t-T")
    verdict = {}
    for lay in (SHALLOW, DEEP):
        c = f"L{lay}"
        td = st.mean(out["base"]["true"][i] - out[c]["true"][i] for i in range(len(items)))
        tl = st.mean(out[c]["target"][i] - out["base"]["target"][i]
                     for i in range(len(items)))
        marg = st.mean(out[c]["target"][i] - out[c]["true"][i] for i in range(len(items)))
        verdict[c] = {"true_drop": td, "target_lift": tl, "margin": marg}
        log.info("%-8s%14.2f%14.2f%14.2f", c, td, tl, marg)

    ratio = (verdict[f"L{DEEP}"]["true_drop"] / verdict[f"L{SHALLOW}"]["true_drop"]
             if verdict[f"L{SHALLOW}"]["true_drop"] else 0.0)
    log.info("")
    log.info("deep/shallow suppression of the true answer = %.2f", ratio)
    if ratio >= 0.5:
        log.info("REAL: the layer-%d edit suppresses the true answer comparably. Its "
                 "success on its own prompt is not a logit artifact, so [E-026]'s "
                 "finding stands -- the edit is real and does not travel.", DEEP)
    else:
        log.warning("DEGENERATE: the layer-%d edit raises the target (+%.2f) without "
                    "suppressing the true answer (%.2f vs %.2f at layer %d). Its apparent "
                    "efficacy is a logit artifact and [E-026]'s headline is NOT supported "
                    "-- the deep edit may simply be a weaker edit.", DEEP,
                    verdict[f"L{DEEP}"]["target_lift"], verdict[f"L{DEEP}"]["true_drop"],
                    verdict[f"L{SHALLOW}"]["true_drop"], SHALLOW)

    p = ROOT / "results" / "E-026b-edit-prompt.json"
    p.write_text(json.dumps({"ticket": "E-026b", "n": len(items), "verdict": verdict,
                             "deep_shallow_suppression_ratio": ratio,
                             "raw": out,
                             "case_ids": [it["cid"] for it in items]}, indent=1))
    log.info("written: %s", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
