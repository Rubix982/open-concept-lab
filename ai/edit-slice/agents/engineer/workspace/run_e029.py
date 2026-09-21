"""E-029 · Does ROME's Efficacy Score predict propagation at the STANDARD edit layer? [T-085]

[E-026] failed as a depth experiment and left one observation intact: edits can pass ROME's
Efficacy Score while leaving the belief standing and propagating to nothing. That was filed
as a depth observation, which is the weaker and more confounded form. The same cell exists
at **layer 5** -- EasyEdit's shipped configuration, the edit the field actually runs.

Two predictors, one outcome, same 42 subjects, no new measurement:

    outcome      propagation      control-differenced drop on the subject-initial city probe
    predictor A  displacement     drop in log P(true answer) on the edit prompt
    predictor B  ES margin        log P(target) - log P(true) on the edit prompt

ES is a threshold on B. The claim is NOT that ES is arbitrary -- it is that B and A come
apart while A and the outcome do not. **Reporting one correlation without the other would
be meaningless**, so both are always printed.

Joins results/E-026b-edit-prompt.json and results/E-026-depth.json. Zero NDIF cost.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
RHO_CONFIRM_A = 0.6
RHO_CONFIRM_B = 0.3


def rank(xs: list[float]) -> list[float]:
    """Average ranks, so ties do not silently bias rho."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(a: list[float], b: list[float]) -> float:
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else float("nan")


def spearman(a: list[float], b: list[float]) -> float:
    return pearson(rank(a), rank(b))


def partial(a: list[float], b: list[float], z: list[float]) -> float:
    """Correlation of a and b with z partialled out, on ranks."""
    ra, rb, rz = rank(a), rank(b), rank(z)
    rab, raz, rbz = pearson(ra, rb), pearson(ra, rz), pearson(rb, rz)
    den = ((1 - raz ** 2) * (1 - rbz ** 2)) ** 0.5
    return (rab - raz * rbz) / den if den else float("nan")


def main() -> None:
    b = json.loads((ROOT / "results" / "E-026b-edit-prompt.json").read_text())
    d = json.loads((ROOT / "results" / "E-026-depth.json").read_text())
    ids, raw = b["case_ids"], b["raw"]
    by_cid = {r["case_id"]: r for r in d["results"]}

    log = setup("run_e029", config={
        "ticket": "E-029", "thread": "T-085", "layer": 5, "n_available": len(ids),
        "outcome": "control-differenced drop on the subject-initial city probe",
        "predictor_A": "belief displacement on the edit prompt",
        "predictor_B": "ES margin on the edit prompt",
        "sources": ["results/E-026b-edit-prompt.json", "results/E-026-depth.json"]})

    prop, disp, marg, base_true = [], [], [], []
    for i, cid in enumerate(ids):
        if cid not in by_cid:
            continue
        s = by_cid[cid]["scores"]
        prop.append((s["base"]["self|initial"] - s["L5"]["self|initial"])
                    - (s["base"]["control|initial"] - s["L5"]["control|initial"]))
        disp.append(raw["base"]["true"][i] - raw["L5"]["true"][i])
        marg.append(raw["L5"]["target"][i] - raw["L5"]["true"][i])
        base_true.append(raw["base"]["true"][i])
    n = len(prop)
    log.info("joined %d subjects at layer 5", n)

    ra = spearman(disp, prop)
    rb = spearman(marg, prop)
    pa = partial(disp, prop, base_true)
    pb = partial(marg, prop, base_true)

    log.info("")
    log.info("%-34s%10s%10s%12s", "", "mean", "spread", "rho w/ prop")
    log.info("%-34s%10.2f%10.2f%12s", "outcome: propagation", st.mean(prop),
             max(prop) - min(prop), "—")
    log.info("%-34s%10.2f%10.2f%12.3f", "A: belief displacement", st.mean(disp),
             max(disp) - min(disp), ra)
    log.info("%-34s%10.2f%10.2f%12.3f", "B: ES margin", st.mean(marg),
             max(marg) - min(marg), rb)
    log.info("")
    log.info("with baseline log P(true) partialled out:  A %.3f   B %.3f", pa, pb)
    log.info("ES margin spread is %.2f nats (min %+.2f, max %+.2f) — a narrow spread "
             "limits what a weak rho can be read to mean, and is the adversary's best "
             "attack here", max(marg) - min(marg), min(marg), max(marg))

    log.info("")
    if ra >= RHO_CONFIRM_A and rb < RHO_CONFIRM_B:
        log.info("VERDICT: CONFIRM — at the STANDARD edit layer, belief displacement "
                 "predicts propagation (rho %.2f) and ES margin does not (rho %.2f). ES is "
                 "a poor proxy for what an edit actually does beyond its own prompt, and "
                 "this is no longer a claim about depth.", ra, rb)
    elif abs(ra - rb) <= 0.2:
        log.info("VERDICT: DENY — the two predictors carry comparable information "
                 "(A %.2f, B %.2f). There is no ES caveat to report at layer 5 and the "
                 "layer-20 observation was about depth after all. [T-085] closes.", ra, rb)
    elif ra < RHO_CONFIRM_A and rb < RHO_CONFIRM_B:
        log.warning("VERDICT: NULL — neither predictor tracks propagation (A %.2f, "
                    "B %.2f). Propagation is driven by something on the edit prompt that "
                    "neither captures. That is a larger finding about [E-021]'s mechanism "
                    "and needs its own ticket, not a sentence here.", ra, rb)
    else:
        log.info("VERDICT: between the pre-stated bands (A %.2f, B %.2f). Report both "
                 "and claim neither.", ra, rb)

    cell = sum(1 for i in range(n) if marg[i] > 0 and disp[i] < 3)
    log.info("")
    log.info("the joint cell at layer 5: passes ES AND displaces the belief <3 nats = "
             "%d/%d", cell, n)
    lo = [prop[i] for i in range(n) if marg[i] > 0 and disp[i] < 3]
    hi = [prop[i] for i in range(n) if not (marg[i] > 0 and disp[i] < 3)]
    if lo and hi:
        log.info("  their mean propagation %.2f nats vs %.2f for the rest", st.mean(lo),
                 st.mean(hi))

    out = ROOT / "results" / "E-029-es-vs-propagation.json"
    out.write_text(json.dumps({
        "ticket": "E-029", "thread": "T-085", "layer": 5, "n": n,
        "spearman": {"displacement": ra, "es_margin": rb},
        "partial_baseline_removed": {"displacement": pa, "es_margin": pb},
        "es_margin_spread": max(marg) - min(marg),
        "joint_cell": cell,
        "per_subject": {"propagation": prop, "displacement": disp, "es_margin": marg,
                        "baseline_true": base_true}}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
