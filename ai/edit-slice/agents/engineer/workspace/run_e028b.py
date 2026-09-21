"""E-028b · Match layer 20 to layer 5 by BUDGET, then compare propagation. [T-079, T-084]

[E-028a] showed matching by *saturation* is the wrong target: neither layer saturated at
100 steps and layer 5 gained as much as layer 20, so its control refused the verdict.
Matching by **budget** needs neither layer to saturate. [E-028] needs two edits with equal
**belief displacement**, whatever step count each needs to reach it.

    target     6.26 nats -- layer 5 at 25 steps, EasyEdit's shipped config, measured
               on the calibration subjects in [E-028a]
    search     layer 20 at {200, 400} steps; 100 steps gave 4.47 and the trend is
               ~0.93 nats per doubling, so the crossing is near 400
    STOP       if 400 steps does not reach 6.26, do NOT extend. Re-open the ticket.
               An unbounded search for the budget that produces the desired match is
               exactly what pre-registration exists to prevent. Failure to match within
               a 16x budget is itself the reportable answer, in the DEPTH direction.

**Held-out verification comes free.** Confound 2 of the ticket requires checking that the
matched budget transfers off the six subjects it was found on -- [E-028a]'s set is an
unlucky draw (layer-5 displacement 6.25 against the full set's 9.70). Since `compute_v_batch`
costs one round trip per STEP regardless of how many specs ride in it, calibration and
held-out subjects travel in the same batch and the verification costs nothing extra.

**Naming, and it is not cosmetic.** A 400-step layer-20 edit is NOT "ROME as configured by
EasyEdit". The arms are `ROME/EasyEdit L5 (25 steps)` and `ROME's update rule at L20
(N steps, displacement-matched)`. [E-013] gate 0 set the convention of naming the
configuration rather than the method; this is the first run where the two diverge.
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
from edit import EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402
from run_e026 import DEEP, MODEL, SHALLOW, load_items  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
BUDGET_GRID = (200, 400)        # pre-registered; 400 is the hard stop
MATCH_TARGET = 6.26             # layer 5 @ 25 steps on the calibration six, [E-028a]
N_CAL = 6                       # the [E-028a] subjects, so the target is comparable
N_HELD = 6                      # confound 2: does the matched budget transfer?


def optimise(m, specs, layer, steps, log, chunk, stall_wait, max_stalls):
    """`v*` for every spec, auto-halving the batch rather than parking on an OOM.

    The existing stall logic treats every failure as an outage and sleeps ten minutes,
    which is right for a dropped node and wrong for a batch that is simply too large.
    Halving first costs one failed attempt and distinguishes the two.
    """
    out, size = {}, chunk
    i = 0
    while i < len(specs):
        grp = specs[i:i + size]
        for attempt in range(max_stalls):
            try:
                out.update(compute_v_batch(m, grp, layer=layer, steps=steps))
                break
            except Exception as exc:  # noqa: BLE001
                if size > 3 and attempt == 0:
                    size = max(3, size // 2)
                    log.warning("batch of %d failed (%s); halving to %d before "
                                "treating it as an outage", len(grp),
                                type(exc).__name__, size)
                    grp = specs[i:i + size]
                    continue
                if attempt == max_stalls - 1:
                    raise
                log.warning("L%d s%d specs %d-%d failed (%s); parking %.0f min",
                            layer, steps, i + 1, i + len(grp), type(exc).__name__,
                            stall_wait / 60)
                time.sleep(stall_wait)
        i += size
    return out


def displacement(m, items, layer, deltas, kcache, chains, log):
    """Drop in log P(true answer) on the edit prompt — the matching quantity."""
    vals = []
    for it in items:
        ks = kcache[it["cid"]]
        pair = [(it["edit_prompt"], nat(chains[it["cid"]]["outer"]["answer"]))]
        b = retrying(lambda p=pair: score_pairs(m, p), what=f"base {it['cid']}")[0]
        e = retrying(lambda p=pair, k=ks, d=deltas[it["cid"]]:
                     score_pairs(m, p, edit=(layer, k, float(k @ k), d)),
                     what=f"L{layer} {it['cid']}")[0]
        vals.append(b - e)
    return vals


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--stall-wait", type=float, default=120)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    items, _, _ = load_items(args.seed)
    cal, held = items[:N_CAL], items[N_CAL:N_CAL + N_HELD]
    both = cal + held
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}

    log = setup("run_e028b", config={
        "ticket": "E-028b", "thread": "T-084", "stage": "budget search",
        "model": MODEL, "layer": DEEP, "budget_grid": list(BUDGET_GRID),
        "match_target_nats": MATCH_TARGET,
        "match_reference": f"ROME/EasyEdit L{SHALLOW} (25 steps) on the calibration six",
        "n_calibration": len(cal), "n_heldout": len(held),
        "hard_stop": "no budget beyond 400 without re-opening the ticket",
        "arm_naming": "ROME's update rule at L20 (N steps, displacement-matched) — "
                      "NOT ROME as configured by EasyEdit"})
    log.info("calibration: %s", [it["subject"] for it in cal])
    log.info("held out   : %s", [it["subject"] for it in held])

    m = connect(MODEL)
    specs = [EditSpec(it["cid"], it["edit_prompt"], it["subject"], it["target"], "real")
             for it in both]
    kcache = {it["cid"]: retrying(
        lambda it=it: read_key_and_value(m, it["edit_prompt"], it["subject"], DEEP)[0],
        what=f"k* L{DEEP} {it['cid']}") for it in both}

    cache_p = ROOT / "results" / "cache" / f"E028b_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache_p.read_text()) if cache_p.exists() else {}

    for steps in BUDGET_GRID:
        key = f"L{DEEP}|s{steps}"
        if key in done:
            log.info("%s cached", key)
            continue
        log.info("optimising %s for %d specs (%d calibration + %d held out)",
                 key, len(specs), len(cal), len(held))
        t0 = time.time()
        deltas = optimise(m, specs, DEEP, steps, log, args.chunk,
                          args.stall_wait, args.max_stalls)
        log.info("  optimisation took %.0f min", (time.time() - t0) / 60)
        dc = displacement(m, cal, DEEP, deltas, kcache, chains, log)
        dh = displacement(m, held, DEEP, deltas, kcache, chains, log)
        done[key] = {"steps": steps, "cal": dc, "held": dh,
                     "norm": {it["cid"]: float(deltas[it["cid"]].norm()) for it in both}}
        cache_p.write_text(json.dumps(done))
        torch.save(deltas, ROOT / "results" / "cache" /
                   f"E028b_deltas_L{DEEP}_s{steps}_{args.seed}.pt")
        log.info("  %s  calibration %.2f nats   held out %.2f nats   ||dv|| %.2f",
                 key, st.mean(dc), st.mean(dh), st.mean(done[key]["norm"].values()))

    report(done, log)


def report(done: dict, log) -> None:
    prior = {25: 2.61, 50: 3.51, 100: 4.47}          # [E-028a], calibration six
    log.info("")
    log.info("E-028b — layer %d belief displacement against step budget", DEEP)
    log.info("match target: %.2f nats (ROME/EasyEdit L%d, 25 steps, calibration six)",
             MATCH_TARGET, SHALLOW)
    log.info("")
    log.info("%-10s%14s%14s", "steps", "calibration", "held out")
    for s, v in sorted(prior.items()):
        log.info("%-10d%14.2f%14s", s, v, "— [E-028a]")
    curve = dict(prior)
    for k in sorted(done, key=lambda k: done[k]["steps"]):
        d = done[k]
        curve[d["steps"]] = st.mean(d["cal"])
        log.info("%-10d%14.2f%14.2f", d["steps"], st.mean(d["cal"]), st.mean(d["held"]))

    top = max(curve)
    reached = curve[top] >= MATCH_TARGET
    log.info("")
    if reached:
        lo = max((s for s in curve if curve[s] < MATCH_TARGET), default=None)
        hi = min(s for s in curve if curve[s] >= MATCH_TARGET)
        if lo is not None:
            frac = (MATCH_TARGET - curve[lo]) / (curve[hi] - curve[lo])
            n_match = int(lo + frac * (hi - lo))
        else:
            n_match = hi
        held_at = st.mean(done[f"L{DEEP}|s{hi}"]["held"]) if f"L{DEEP}|s{hi}" in done else None
        log.info("MATCHED: layer %d reaches %.2f nats at %d steps; the crossing "
                 "interpolates to ~%d steps. Run step 2 at %d.",
                 DEEP, curve[hi], hi, n_match, hi)
        if held_at is not None:
            gap = abs(held_at - st.mean(done[f"L{DEEP}|s{hi}"]["cal"]))
            if gap > 1.5:
                log.warning("HELD-OUT CHECK FAILS: held-out displacement %.2f vs "
                            "calibration %.2f (gap %.2f nats). The budget does not "
                            "transfer off the six it was fitted on; step 2 would compare "
                            "arms matched only on the calibration set.", held_at,
                            st.mean(done[f"L{DEEP}|s{hi}"]["cal"]), gap)
            else:
                log.info("held-out check passes: %.2f vs %.2f calibration (gap %.2f)",
                         held_at, st.mean(done[f"L{DEEP}|s{hi}"]["cal"]), gap)
    else:
        log.warning("NOT MATCHED at the pre-registered ceiling of %d steps: layer %d "
                    "reaches only %.2f of %.2f nats. Per the ticket this is the STOP "
                    "condition — do not extend the grid. ROME's update at layer %d "
                    "cannot be brought to layer-%d displacement within a %dx budget, "
                    "which answers [T-084] in the DEPTH direction and is the result.",
                    top, DEEP, curve[top], MATCH_TARGET, DEEP, SHALLOW, top // 25)

    out = ROOT / "results" / "E-028b-budget-match.json"
    out.write_text(json.dumps({"ticket": "E-028b", "thread": ["T-079", "T-084"],
                               "layer": DEEP, "match_target": MATCH_TARGET,
                               "budget_grid": list(BUDGET_GRID),
                               "curve_calibration": curve, "matched": reached,
                               "cells": done}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
