"""E-028d · Is it the layer, or the step budget? The collinearity control. [T-079]

[E-028c] found two edits matched on belief displacement (6.97 vs 7.26), on delta norm
(7.52 vs 7.27) and on delivered coefficient (exactly 1.000, analytic) still differ **63%**
in how far they travel to a prompt sharing the edit's prefix.

**One alternative remains, and the design built it in.** Displacement was matched by giving
the deep arm a 16x step budget, so *layer 20* and *400 steps* are perfectly collinear. A
heavily optimised rank-one update may simply be fitted more tightly to the prompt it was
optimised on, with depth contributing nothing.

This buys the fourth cell. Three exist:

    P(L5,  25) = 9.66      P(L20, 400) = 3.59      P(L20, 25) = 0.80 [E-026]
    P(L5, 400) = ?

Pre-registered:
    LAYER   P(L5,400) >= 7.7  (within 20% of P(L5,25))  -> budget is not the driver
    BUDGET  P(L5,400) <= 4.3  (within 20% of P(L20,400)) -> depth is not the driver, and
            every depth statement in [E-028b/c] is withdrawn
    BOTH    between -> report the split, claim neither

**BUDGET is not a null.** "More optimisation makes an edit more local" is a finding about
ROME's own hyperparameter -- the one [E-028a] showed is under-set at 25 steps -- and it
connects to the field's generalisation/specificity tradeoff. Report it with the same weight.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import CLAMP_NORM_FACTOR, EditSpec, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402
from run_e026 import FORMS, MODEL, SHALLOW, load_items  # noqa: E402
from run_e028b import optimise  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
STEPS = 400
N = 12
P_L5_25, P_L20_400 = 9.66, 3.59          # [E-028c]
LAYER_BAND, BUDGET_BAND = 0.8 * P_L5_25, 1.2 * P_L20_400


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--stall-wait", type=float, default=120)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    items, _, _ = load_items(args.seed)
    items = items[:N]
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}

    log = setup("run_e028d", config={
        "ticket": "E-028d", "thread": "T-079", "model": MODEL, "n": N,
        "arm": f"ROME's update rule at L{SHALLOW} ({STEPS} steps) — the collinearity "
               f"control, NOT EasyEdit's shipped config",
        "bands": {"LAYER": f">= {LAYER_BAND:.2f}", "BUDGET": f"<= {BUDGET_BAND:.2f}"},
        "known_cells": {"P(L5,25)": P_L5_25, "P(L20,400)": P_L20_400}})

    m = connect(MODEL)
    specs = [EditSpec(it["cid"], it["edit_prompt"], it["subject"], it["target"], "real")
             for it in items]
    dpath = ROOT / "results" / "cache" / f"E028d_deltas_L{SHALLOW}_s{STEPS}_{args.seed}.pt"
    if dpath.exists():
        deltas = torch.load(dpath)
        log.info("deltas cached")
    else:
        log.info("optimising L%d at %d steps for %d specs", SHALLOW, STEPS, len(specs))
        t0 = time.time()
        deltas = optimise(m, specs, SHALLOW, STEPS, log, args.chunk,
                          args.stall_wait, args.max_stalls)
        torch.save(deltas, dpath)
        log.info("  took %.0f min", (time.time() - t0) / 60)

    kstar, caps = {}, {}
    for it in items:
        k, wk = retrying(
            lambda it=it: read_key_and_value(m, it["edit_prompt"], it["subject"], SHALLOW),
            what=f"k* {it['cid']}")
        kstar[it["cid"]] = k
        caps[it["cid"]] = CLAMP_NORM_FACTOR * float(wk.norm())

    # Confound 2: does the clamp bind at 400 steps? If it does, the cell is capped and
    # the comparison is limited rather than clean.
    frac = [float(deltas[it["cid"]].norm()) / caps[it["cid"]] for it in items]
    at_cap = sum(1 for f in frac if f > 0.98)
    log.info("clamp occupancy %.0f%% of ceiling; %d/%d at cap", 100 * st.mean(frac),
             at_cap, len(items))
    if at_cap:
        log.warning("the clamp BINDS for %d subjects — this cell is capped and the "
                    "comparison is limited, not clean", at_cap)

    out, disp = {}, []
    for n, it in enumerate(items, 1):
        cid = it["cid"]
        ctl = items[n % len(items)]
        pairs, tags = [], []
        for who, obj in (("self", it), ("control", ctl)):
            for fname, tmpl in FORMS.items():
                pairs.append((tmpl.format(obj["subject"]), obj["true_city"]))
                tags.append(f"{who}|{fname}")
        tp = (it["edit_prompt"], nat(chains[cid]["outer"]["answer"]))
        ks, dv = kstar[cid], deltas[cid]
        ed = (SHALLOW, ks, float(ks @ ks), dv)
        base = retrying(lambda p=pairs + [tp]: score_pairs(m, p), what=f"base {cid}")
        edit = retrying(lambda p=pairs + [tp], e=ed: score_pairs(m, p, edit=e),
                        what=f"edit {cid}")
        out[cid] = {"base": dict(zip(tags, base)), "edit": dict(zip(tags, edit)),
                    "norm": float(dv.norm()), "clamp_frac": frac[n - 1]}
        disp.append(base[-1] - edit[-1])
        log.info("  scored %d/%d  %s", n, len(items), it["subject"])

    rs = list(out.values())
    D = {}
    log.info("")
    log.info("E-028d — ROME's update rule at L%d, %d steps (n=%d)", SHALLOW, STEPS, N)
    log.info("belief displacement on the edit prompt %.2f nats   ||dv|| %.2f   "
             "(L5@25 was 7.26 / 7.27)", st.mean(disp), st.mean(r["norm"] for r in rs))
    log.info("")
    log.info("%-14s%10s%10s%10s", "form", "baseline", "post-edit", "drop")
    for fname in FORMS:
        b = st.mean(r["base"][f"self|{fname}"] for r in rs)
        p = st.mean(r["edit"][f"self|{fname}"] for r in rs)
        c = st.mean(r["base"][f"control|{fname}"] - r["edit"][f"control|{fname}"]
                    for r in rs)
        D[fname] = (b - p) - c
        log.info("%-14s%10.2f%10.2f%10.2f", fname, b, p, D[fname])

    p400 = D["initial"]
    log.info("")
    log.info("the 2x2 on subject-initial propagation:")
    log.info("%-12s%14s%14s", "", "25 steps", "400 steps")
    log.info("%-12s%14.2f%14.2f", f"L{SHALLOW}", P_L5_25, p400)
    log.info("%-12s%14.2f%14.2f", "L20", 0.80, P_L20_400)
    log.info("")
    if p400 >= LAYER_BAND:
        log.info("VERDICT: LAYER — L%d at %d steps still propagates %.2f nats (>= %.2f). "
                 "Step budget does not drive propagation, so the collinearity in "
                 "[E-028c] breaks in favour of depth and its dissociation stands as a "
                 "LAYER effect.", SHALLOW, STEPS, p400, LAYER_BAND)
    elif p400 <= BUDGET_BAND:
        log.warning("VERDICT: BUDGET — L%d at %d steps propagates only %.2f nats "
                    "(<= %.2f), collapsing to the deep arm's level. The effect is "
                    "OPTIMISATION BUDGET, not depth. Every depth statement in [E-028b/c] "
                    "is withdrawn. This is a finding about ROME's own hyperparameter, not "
                    "a null — more optimisation makes an edit more local.",
                    SHALLOW, STEPS, p400, BUDGET_BAND)
    else:
        log.info("VERDICT: BOTH — L%d at %d steps propagates %.2f, between the bands "
                 "(%.2f, %.2f). Budget explains part of [E-028c]'s gap and depth the "
                 "rest; claim neither cleanly and report the split.",
                 SHALLOW, STEPS, p400, BUDGET_BAND, LAYER_BAND)
    # Written anticipating the BUDGET outcome, where propagation FALLS. It fired on the
    # LAYER outcome, where propagation rose, and described the data backwards. The
    # direction is now read from the numbers instead of assumed by the author.
    direction = "fell" if p400 < P_L5_25 else "ROSE"
    log.info("displacement went 7.26 -> %.2f at %d steps while propagation %s %.2f -> "
             "%.2f. More optimisation buying MORE reach is the opposite of the "
             "overfitting account, and is evidence against BUDGET independently of the "
             "band test above.", st.mean(disp), STEPS, direction, P_L5_25, p400)

    f = ROOT / "results" / "E-028d-budget-control.json"
    f.write_text(json.dumps({"ticket": "E-028d", "thread": "T-079", "n": N,
                             "layer": SHALLOW, "steps": STEPS,
                             "displacement": st.mean(disp),
                             "clamp_occupancy": st.mean(frac), "at_cap": at_cap,
                             "drops": D, "grid": {"L5|25": P_L5_25, "L5|400": p400,
                                                  "L20|25": 0.80, "L20|400": P_L20_400},
                             "results": rs}, indent=1))
    log.info("written: %s", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
