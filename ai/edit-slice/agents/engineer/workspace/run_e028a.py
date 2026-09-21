"""E-028a · Route 1 — is the weak edit at depth under-optimisation, or depth itself? [T-084]

[E-026] measured layer-20 edits suppressing the true answer by 1.81 nats against layer 5's
9.70, at comparable target lift. Every depth claim in the project waits on which of two
readings is right:

    UNDER-OPTIMISATION  EasyEdit's 25 steps / lr 0.5 are LAYER-5 hyperparameters, applied
                        unchanged at layer 20. The optimiser finished the cheap half of
                        the objective and ran out of steps for the expensive half.
    DEPTH               With twelve layers left to act through, no rank-one update at the
                        subject position can displace a belief the way it can from layer
                        5, and more steps will not help.

Flat suppression against step count means DEPTH. Rising means HYPERPARAMETERS.

**This is a 2x3 crossing, not the 3-cell sweep the ticket specified.** Layer 5 is run at
the same step counts, because a rising layer-20 curve is uninterpretable without it: if
layer 5 also rises, more optimisation simply helps everywhere and the layers are never
matched at any budget. [T-065] found every narrowing in this project came from unfixing a
dimension; step count is the dimension [E-026] held fixed without noticing.

PRE-REGISTERED BEFORE THE RUN, and reported cell by cell whatever happens:
  * step grid           {25, 50, 100}
  * displacement bar    6.79 nats = 70% of layer 5's measured 9.70 at 25 steps
  * subjects            the first 6 of [E-026]'s set, no selection on outcome

"You tuned until the answer came out" is the obvious attack. The grid and the bar are
fixed here, in the file, and every cell is logged — including the ones that fail.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402
from run_e026 import DEEP, MODEL, SHALLOW, load_items  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
STEP_GRID = (25, 50, 100)
BAR_NATS = 6.79                 # 70% of layer 5's 9.70 at 25 steps, measured in [E-026b]
LAYER_5_REFERENCE = 9.70


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=120)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    items, _, _ = load_items(args.seed)
    items = items[: args.n]
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}

    log = setup("run_e028a", config={
        "ticket": "E-028a", "thread": "T-084", "model": MODEL, "seed": args.seed,
        "layers": [SHALLOW, DEEP], "step_grid": list(STEP_GRID), "n": len(items),
        "bar_nats": BAR_NATS, "layer5_reference_nats": LAYER_5_REFERENCE,
        "measure": "suppression of log P(true answer) on the edit prompt",
        "preregistered": "grid and bar fixed in the source before the run"})
    log.info("2x3 crossing: layers %s x steps %s, n=%d subjects",
             [SHALLOW, DEEP], list(STEP_GRID), len(items))

    m = connect(MODEL)
    specs = [EditSpec(it["cid"], it["edit_prompt"], it["subject"], it["target"], "real")
             for it in items]
    true_pairs = [(it["edit_prompt"], nat(chains[it["cid"]]["outer"]["answer"]))
                  for it in items]
    tgt_pairs = [(it["edit_prompt"], it["target"]) for it in items]

    base = retrying(lambda: score_pairs(m, true_pairs + tgt_pairs), what="baseline")
    base_true, base_tgt = base[: len(items)], base[len(items):]
    log.info("baseline  log P(true) %.2f   log P(target) %.2f",
             st.mean(base_true), st.mean(base_tgt))

    cache_p = ROOT / "results" / "cache" / f"E028a_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    kcache: dict[int, dict] = {}

    for layer in (SHALLOW, DEEP):
        for steps in STEP_GRID:
            cell = f"L{layer}|s{steps}"
            if cell in done:
                log.info("%s cached", cell)
                continue
            log.info("optimising %s (%d specs x %d steps)", cell, len(specs), steps)
            for attempt in range(args.max_stalls):
                try:
                    deltas = compute_v_batch(m, specs, layer=layer, steps=steps)
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == args.max_stalls - 1:
                        raise
                    log.warning("%s failed (%s); parking %.0f min", cell,
                                type(exc).__name__, args.stall_wait / 60)
                    time.sleep(args.stall_wait)

            if layer not in kcache:
                kcache[layer] = {
                    it["cid"]: retrying(
                        lambda it=it: read_key_and_value(
                            m, it["edit_prompt"], it["subject"], layer)[0],
                        what=f"k* L{layer} {it['cid']}")
                    for it in items}

            true_s, tgt_s = [], []
            for j, it in enumerate(items):
                ks, dv = kcache[layer][it["cid"]], deltas[it["cid"]]
                ed = (layer, ks, float(ks @ ks), dv)
                sc = retrying(lambda p=[true_pairs[j], tgt_pairs[j]], e=ed:
                              score_pairs(m, p, edit=e), what=f"{cell} {it['cid']}")
                true_s.append(sc[0])
                tgt_s.append(sc[1])

            done[cell] = {
                "layer": layer, "steps": steps,
                "suppression": [base_true[i] - true_s[i] for i in range(len(items))],
                "lift": [tgt_s[i] - base_tgt[i] for i in range(len(items))],
                "margin": [tgt_s[i] - true_s[i] for i in range(len(items))],
                "delta_norm": [float(deltas[it["cid"]].norm()) for it in items]}
            cache_p.write_text(json.dumps(done))
            d = done[cell]
            log.info("  %s  suppression %5.2f   lift %5.2f   margin %+5.2f   "
                     "||dv|| %5.2f", cell, st.mean(d["suppression"]), st.mean(d["lift"]),
                     st.mean(d["margin"]), st.mean(d["delta_norm"]))

    report(done, log, len(items))


def report(done: dict, log, n: int) -> None:
    log.info("")
    log.info("E-028a — suppression of log P(true answer) on the edit prompt (n=%d)", n)
    log.info("bar = %.2f nats (70%% of layer 5's %.2f at 25 steps, [E-026b])",
             BAR_NATS, LAYER_5_REFERENCE)
    log.info("")
    log.info("%-10s%s", "layer", "".join(f"{str(s)+' steps':>14}" for s in STEP_GRID))
    sup = {}
    for layer in (SHALLOW, DEEP):
        row = []
        for s in STEP_GRID:
            v = st.mean(done[f"L{layer}|s{s}"]["suppression"])
            sup[(layer, s)] = v
            row.append(f"{v:>13.2f}{'*' if v >= BAR_NATS else ' '}")
        log.info("%-10s%s", f"L{layer}", "".join(row))
    log.info("(* clears the bar)")

    log.info("")
    for layer in (SHALLOW, DEEP):
        lo, hi = sup[(layer, STEP_GRID[0])], sup[(layer, STEP_GRID[-1])]
        gain = 100 * (hi - lo) / abs(lo) if lo else float("nan")
        log.info("L%-3d %d -> %d steps: %.2f -> %.2f nats (%+.0f%%)",
                 layer, STEP_GRID[0], STEP_GRID[-1], lo, hi, gain)

    deep_gain = sup[(DEEP, STEP_GRID[-1])] - sup[(DEEP, STEP_GRID[0])]
    shal_gain = sup[(SHALLOW, STEP_GRID[-1])] - sup[(SHALLOW, STEP_GRID[0])]
    cleared = sup[(DEEP, STEP_GRID[-1])] >= BAR_NATS
    log.info("")
    if cleared:
        log.info("VERDICT: HYPERPARAMETERS. Layer %d reaches %.2f nats at %d steps and "
                 "clears the bar. [E-026]'s weak deep edit was under-optimised, not a "
                 "property of depth; [E-028] route 1 is viable and must report the step "
                 "count beside every number.", DEEP, sup[(DEEP, STEP_GRID[-1])],
                 STEP_GRID[-1])
    elif deep_gain < 1.0:
        log.info("VERDICT: DEPTH. Layer %d gains only %.2f nats across a 4x step budget "
                 "and never clears %.2f. More optimisation does not help, so the weak "
                 "deep edit is a property of depth. Route 1 is dead; [E-028] goes to "
                 "route 2 (match by selection).", DEEP, deep_gain, BAR_NATS)
    else:
        log.info("VERDICT: PARTIAL. Layer %d gains %.2f nats but reaches only %.2f "
                 "against a bar of %.2f. Neither reading is clean; report the grid and "
                 "extend it before claiming either.", DEEP, deep_gain,
                 sup[(DEEP, STEP_GRID[-1])], BAR_NATS)
    # The control has to be able to INVALIDATE the verdict above, not merely sit beside
    # it. If layer 5 climbs over the same grid, more optimisation helps everywhere, the
    # two layers are not matched at any budget here, and even a HYPERPARAMETERS reading
    # would be comparing an under-optimised arm against a saturated one.
    if shal_gain > 2.0:
        log.warning("CONTROL FAILS: layer %d ALSO gains %.2f nats over the same grid, so "
                    "more optimisation helps everywhere and the two layers are not "
                    "matched at any budget in this grid. The verdict above is not "
                    "supported — extend the grid until layer %d saturates first.",
                    SHALLOW, shal_gain, SHALLOW)
    else:
        log.info("control holds: layer %d gains only %.2f nats over the same grid, so it "
                 "is saturated at 25 steps and any layer-%d climb is about depth rather "
                 "than about optimisation budget.", SHALLOW, shal_gain, DEEP)

    out = ROOT / "results" / "E-028a-step-sweep.json"
    out.write_text(json.dumps({"ticket": "E-028a", "thread": "T-084", "n": n,
                               "step_grid": list(STEP_GRID), "bar_nats": BAR_NATS,
                               "layers": [SHALLOW, DEEP],
                               "suppression_mean": {f"L{k[0]}|s{k[1]}": v
                                                    for k, v in sup.items()},
                               "cells": done}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
