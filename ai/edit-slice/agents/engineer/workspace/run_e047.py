"""E-047 · Hold the man fixed, vary the country: does the replacement profession track it?

[E-046] varied subject and country together, so its "the country does not matter"
conclusion is confounded: Chile's two subjects were different people, and one was
already `composer` at base. This varies ONLY the country, on the one subject the model
demonstrably knew (Vlaminck, painter at 71%).

The hypothesis is Saif's: the profession becomes the country's highest cultural export,
i.e. the model infers rather than breaks.

The stereotype mapping is MEASURED off the base model, never hand-written — writing
"Brazil -> footballer" in advance lets the analyst find a mapping after seeing results.
The country's own prior comes from `By profession, a famous person from {C} is a`, and
the test is whether Vlaminck's edited answer matches THAT, against a permuted floor built
from every other country's prior.

One `compute_v_batch` over all countries (k* is shared — same prompt, same subject), then
one remote call per country for the readout.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
TOP_K = 8

SUBJECT = "Maurice de Vlaminck"
EDIT_PROMPT = "Maurice de Vlaminck was born in the country of"
OCC_PROBE = "By profession, Maurice de Vlaminck is a"
#: The country's own profession association, read off the BASE model so the
#: "cultural export" mapping is measured rather than asserted.
PRIOR_PROBE = "By profession, a famous person from {} is a"

#: [E-046]'s 19, plus five carrying unusually strong single-profession associations.
#: The hypothesis is given its best shot deliberately; a failure here is worth more.
COUNTRIES = [
    "Australia", "Austria", "Canada", "Chile", "Czech Republic", "Denmark",
    "Finland", "France", "India", "Iran", "Italy", "Japan", "New Zealand",
    "Poland", "Portugal", "Spain", "Sweden", "Switzerland", "United States",
    "Argentina", "Brazil", "Jamaica", "Kenya", "Russia",
]


def topk(m, prompt_ids, *, edit=None):
    """Top-K tokens and probabilities at the first answer token."""
    def once():
        with _quiet_stdout(), m.trace(prompt_ids, remote=True):
            if edit is not None:
                ks_cpu, den, dv_cpu = edit
                dp = m.model.layers[LAYER].mlp.down_proj
                kk = dp.input
                uu = ks_cpu.to(kk.device, kk.dtype)
                dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                        * dv_cpu.to(kk.device, kk.dtype)
            probs = m.lm_head.output[0, -1].softmax(-1)
            tv = probs.topk(TOP_K).values.save()
            ti = probs.topk(TOP_K).indices.save()
        return [float(x) for x in tv], [int(x) for x in ti]
    return retrying(once, what="topk")


def report(rs, priors, log, *, out: Path) -> dict:
    """Primary test (does it vary?), then the floor test. Order is pre-stated."""
    n = len(rs)
    if not n:
        log.info("nothing to report — no countries completed")
        return {}

    def norm(t): return t.strip().lower()

    edited = {r["country"]: norm(r["edited"]["tokens"][0]) for r in rs}
    prior1 = {c: norm(p["tokens"][0]) for c, p in priors.items()}
    prior_k = {c: {norm(t) for t in p["tokens"]} for c, p in priors.items()}

    counts = Counter(edited.values())
    distinct = len(counts)
    modal, modal_n = counts.most_common(1)[0]

    log.info("")
    log.info("subject held fixed: %s   (base top-1 was %r)", SUBJECT, rs[0]["base"]["tokens"][0])
    log.info("")
    log.info("%-18s%-20s%-20s%s", "injected country", "Vlaminck becomes", "country's own prior", "match")
    for r in rs:
        c = r["country"]
        e, p = edited[c], prior1[c]
        mark = "TOP-1" if e == p else ("top-8" if e in prior_k[c] else "")
        log.info("%-18s%-20s%-20s%s", c, e[:18], p[:18], mark)

    log.info("")
    log.info("TEST 1 (mapping-free): distinct edited answers %d across %d countries", distinct, n)
    log.info("                       most common answer %r in %d/%d", modal, modal_n, n)

    hit1 = sum(edited[c] == prior1[c] for c in edited)
    hitk = sum(edited[c] in prior_k[c] for c in edited)
    # Permuted floor: score each country's edited answer against every OTHER
    # country's prior. This is the chance rate for a generically common profession.
    pairs = [(a, b) for a in edited for b in prior1 if a != b]
    floor1 = sum(edited[a] == prior1[b] for a, b in pairs) / len(pairs)
    floork = sum(edited[a] in prior_k[b] for a, b in pairs) / len(pairs)

    log.info("")
    log.info("TEST 2 (against a permuted floor)")
    log.info("  edited answer == that country's own prior top-1   %d/%d = %.1f%%   floor %.1f%%",
             hit1, n, 100 * hit1 / n, 100 * floor1)
    log.info("  edited answer within that country's prior top-8   %d/%d = %.1f%%   floor %.1f%%",
             hitk, n, 100 * hitk / n, 100 * floork)

    rate1, ratek = hit1 / n, hitk / n
    log.info("")
    if distinct <= max(2, n // 8):
        verdict = "DENY-stereotype"
        log.info("DENY-stereotype: the edited answer is %r in %d of %d countries. The "
                 "injected country carries no content in the replacement; it is a "
                 "property of the perturbation. [E-046] stands, now on a clean design.",
                 modal, modal_n, n)
    elif rate1 > 2 * floor1 or ratek > 2 * floork:
        verdict = "CONFIRM-stereotype"
        log.info("CONFIRM-stereotype: the replacement matches the country's OWN measured "
                 "prior at %.1f%% (top-1) / %.1f%% (top-8) against floors of %.1f%% / "
                 "%.1f%%. Saif's reading wins — the model is inferring from the country, "
                 "not breaking. notes/myself.md must retract 'the replacement has nothing "
                 "to do with the country we injected'.", 100 * rate1, 100 * ratek,
                 100 * floor1, 100 * floork)
    else:
        verdict = "MIXED"
        log.info("MIXED: the answer varies with the country (%d distinct) but matches that "
                 "country's own prior at the floor (%.1f%% vs %.1f%%). The delta carries "
                 "country-dependent content that is NOT the stereotype — neither reading, "
                 "and the result worth following.", distinct, 100 * rate1, 100 * floor1)

    payload = {"ticket": "E-047", "model": MODEL, "layer": LAYER, "subject": SUBJECT,
               "probes": {"occupation": OCC_PROBE, "country_prior": PRIOR_PROBE},
               "verdict": verdict,
               "summary": {"n": n, "distinct_edited": distinct, "modal": modal,
                           "modal_n": modal_n, "hit_top1": hit1, "hit_topk": hitk,
                           "floor_top1": floor1, "floor_topk": floork},
               "priors": priors, "results": rs}
    out.write_text(json.dumps(payload, indent=1))
    log.info("written: %s", out)
    return payload


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--steps", type=int, default=25)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    log = setup("run_e047", config={
        "ticket": "E-047", "parent": "E-046", "model": MODEL, "layer": LAYER,
        "subject": SUBJECT, "n_countries": len(COUNTRIES), "top_k": TOP_K,
        "design": "subject fixed, country varied; stereotype prior MEASURED off base",
        "v_steps": args.steps})
    log.info("%s, %d injected countries, one v* each", SUBJECT, len(COUNTRIES))

    m = connect(MODEL)
    tok = m.tokenizer
    cache = ROOT / "results" / "cache" / f"E047_L{LAYER}_s{args.seed}.pt"

    ks, w_ks = read_key_and_value(m, EDIT_PROMPT, SUBJECT, layer=LAYER)
    den = float(ks @ ks)
    log.info("k* read once and shared — same prompt and subject for every country")

    if cache.exists():
        vs = torch.load(cache)
        log.info("loaded %d cached v* from %s", len(vs), cache.name)
    else:
        specs = [EditSpec(case_id=c, prompt=EDIT_PROMPT, subject=SUBJECT, target=c)
                 for c in COUNTRIES]
        vs = compute_v_batch(m, specs, layer=LAYER, steps=args.steps)
        torch.save(vs, cache)
        log.info("optimised %d v* in one batch", len(vs))

    missing = set(COUNTRIES) - set(vs)
    if missing:
        raise SystemExit(f"v* incomplete: {len(missing)} of {len(COUNTRIES)} absent")

    occ_ids = tok(OCC_PROBE, return_tensors="pt").input_ids
    bv, bi = topk(m, occ_ids)
    base = {"tokens": [tok.decode([i]) for i in bi], "probs": bv}
    log.info("base: %s", [(t.strip(), round(p * 100, 1)) for t, p in
                          zip(base["tokens"][:3], base["probs"][:3])])

    rs = []
    for n, c in enumerate(COUNTRIES, 1):
        dv = vs[c] - w_ks
        ev, ei = topk(m, occ_ids, edit=(ks, den, dv))
        rs.append({"country": c, "base": base,
                   "edited": {"tokens": [tok.decode([i]) for i in ei], "probs": ev}})
        if n % 6 == 0 or n == len(COUNTRIES):
            log.info("  %d/%d countries", n, len(COUNTRIES))

    priors = {}
    for n, c in enumerate(COUNTRIES, 1):
        pids = tok(PRIOR_PROBE.format(c), return_tensors="pt").input_ids
        pv, pi = topk(m, pids)
        priors[c] = {"tokens": [tok.decode([i]) for i in pi], "probs": pv}
        if n % 6 == 0 or n == len(COUNTRIES):
            log.info("  %d/%d country priors", n, len(COUNTRIES))

    report(rs, priors, log, out=ROOT / "results" / "E-047-country-sweep.json")


if __name__ == "__main__":
    main()
