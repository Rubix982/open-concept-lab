"""E-049 · Is donor spread a valid yardstick for a permuted floor?

[E-048] pre-stated its verdict as `margin > floor_spread`, where `floor_spread` is the
standard deviation of the per-donor match rates. That measures how much donors differ
from EACH OTHER. It is not the sampling error of the observed rate, which is what the
question "is this margin real" actually needs. On the real data the two disagreed, so
the gate is unsettled -- and the permuted floor is used beyond [E-048].

This settles it by simulation, because simulation is the only place the right answer is
known in advance. Two worlds, built so the answer is true by construction:

    null     the edited top-1 is drawn from the shared vocabulary, unrelated to the
             subject's own list. Any gate that fires here is a false positive.
    effect   the edited top-1 is drawn from the subject's OWN base top-k with
             probability p. A gate silent here has no power.

Donor heterogeneity is varied INDEPENDENTLY of effect size, by changing how peaked the
shared vocabulary is. That separation is the whole experiment: it is what distinguishes
a yardstick that tracks the effect from one that tracks something else entirely.

No remote calls, no cached tensors. Seeded, so two runs of this file agree -- a
measurement that changes between runs is not a measurement [lessons].
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from logs import setup  # noqa: E402

TICKET = "E-049"
TOP_K = 8
N_SUBJECTS = 33          # [E-048]'s scored n, so the answer transfers directly
N_TRIALS = 400
VOCAB = 60


def make_world(rng: random.Random, *, p_effect: float, concentration: float,
               vocab: int = VOCAB) -> list[dict]:
    """One synthetic cohort.

    `vocab` and `concentration` together set the regime. What matters is not either one
    but the pair (floor, spread/floor) they produce, because that pair is observable on
    REAL data and is therefore the only thing that lets a real result be located here.

    Two earlier versions of this file missed that. The first varied concentration alone
    and topped out at spread/floor = 0.60 while [E-048] sits at 1.15 and 1.59 -- it
    calibrated a regime the data is not in. The second added a per-donor exponent to fix
    it, which did nothing at all, because at concentration 0 every weight is 1.0 and
    1.0**alpha is 1.0. A knob that cannot move the quantity it was added for is worse
    than no knob, so it is gone rather than left in.
    """
    base_w = [(1.0 / (1 + i)) ** (3 * concentration) for i in range(vocab)]
    pool = list(range(vocab))

    rows = []
    for _ in range(N_SUBJECTS):
        base: list[int] = []
        guard = 0
        while len(base) < TOP_K and guard < 2000:
            guard += 1
            tok = rng.choices(pool, weights=base_w, k=1)[0]
            if tok not in base:
                base.append(tok)
        if rng.random() < p_effect:
            edited = rng.choice(base)                       # from his OWN list
        else:
            edited = rng.choices(pool, weights=base_w, k=1)[0]
        rows.append({"base": base, "edited": edited})
    return rows


def measure(rows: list[dict]) -> dict:
    """The two gates, computed exactly as [E-048] computes them."""
    hits = sum(r["edited"] in r["base"] for r in rows)
    rate = hits / len(rows)

    per_donor, total, floor_hits = [], 0, 0
    for i, a in enumerate(rows):
        h = n = 0
        for j, b in enumerate(rows):
            if i == j:
                continue
            n += 1
            h += a["edited"] in b["base"]
        per_donor.append(h / n)
        total += n
        floor_hits += h
    floor = floor_hits / total
    spread = statistics.pstdev(per_donor)

    n = len(rows)
    tail = sum(comb(n, k) * floor**k * (1 - floor)**(n - k) for k in range(hits, n + 1))
    return {"rate": rate, "floor": floor, "spread": spread, "margin": rate - floor,
            "hits": hits, "n": n, "binomial_p": tail,
            "fires_spread": (rate - floor) > spread,
            "fires_binomial": tail < 0.05}


def report(grid: list[dict], log, *, out: Path) -> dict:
    """Pooled verdict first, then the stratified read the grid was built to allow."""
    def rates(cells):
        nulls = [g for g in cells if g["p_effect"] == 0.0]
        effs = [g for g in cells if g["p_effect"] > 0.0]
        f = lambda rows, k: sum(g[k] for g in rows) / max(len(rows), 1)  # noqa: E731
        return (f(nulls, "fire_rate_spread"), f(nulls, "fire_rate_binomial"),
                f(effs, "fire_rate_spread"), f(effs, "fire_rate_binomial"))

    fp_spread, fp_binom, pw_spread, pw_binom = rates(grid)
    agree = sum(g["agree"] for g in grid)

    log.info("")
    log.info("                      donor spread    binomial")
    log.info("  false positive rate    %6.1f%%      %6.1f%%", 100 * fp_spread, 100 * fp_binom)
    log.info("  power (real effect)    %6.1f%%      %6.1f%%", 100 * pw_spread, 100 * pw_binom)
    log.info("  cells where they agree  %d of %d", agree, len(grid))
    log.info("")
    for g in grid:
        log.info("  p_eff %.2f  %-24s floor %4.1f%%  ratio %4.2f   "
                 "fires: spread %5.1f%%  binom %5.1f%%  %s",
                 g["p_effect"], g["regime"], 100 * g["mean_floor"],
                 g["spread_over_floor"], 100 * g["fire_rate_spread"],
                 100 * g["fire_rate_binomial"], "agree" if g["agree"] else "DIFFER")

    if fp_spread > fp_binom + 0.02:
        band, why = "MISCALIBRATED-LOOSE", (
            f"donor spread fires under the null {100*fp_spread:.1f}% of the time against "
            f"the binomial's {100*fp_binom:.1f}%. It is not conservative, and any past "
            f"CONFIRM resting on it has to be re-read.")
    elif pw_spread < pw_binom - 0.10:
        band, why = "MISCALIBRATED-CONSERVATIVE", (
            f"donor spread holds the null ({100*fp_spread:.1f}% vs {100*fp_binom:.1f}%) but "
            f"catches real effects only {100*pw_spread:.1f}% of the time against the "
            f"binomial's {100*pw_binom:.1f}%. [E-048]'s DENY is underpowered rather than "
            f"wrong, every past use of this gate is a lower bound on sensitivity, and the "
            f"band should be restated for future tickets.")
    else:
        band, why = "AGREE", (
            f"the two gates track each other: false positives {100*fp_spread:.1f}% vs "
            f"{100*fp_binom:.1f}%, power {100*pw_spread:.1f}% vs {100*pw_binom:.1f}%. Donor "
            f"spread is a usable conservative proxy, [E-048]'s DENY stands unqualified, and "
            f"[T-106] closes.")

    summary: dict = {"ticket": TICKET, "n_subjects": N_SUBJECTS, "top_k": TOP_K,
                     "trials_per_cell": N_TRIALS,
                     "false_positive": {"spread": fp_spread, "binomial": fp_binom},
                     "power": {"spread": pw_spread, "binomial": pw_binom},
                     "cells_agreeing": agree, "cells": len(grid),
                     "verdict": band, "verdict_text": why, "by_regime": {}, "grid": grid}

    log.info("")
    log.info("%s (pre-stated band, pooled over the whole grid): %s", band, why)

    # The grid carries regimes BECAUSE one pooled number cannot answer what this ticket
    # asks. The pre-stated band stands exactly as it fired; what follows is the
    # stratified read the design called for, not a second gate invented after the fact.
    like = [g for g in grid if "E-048-like" in g["regime"]]
    far = [g for g in grid if "E-048-like" not in g["regime"]]
    for key, name, cells in (("regime_e048_like", "E-048's own regime", like),
                             ("regime_far", "the far regime", far)):
        if not cells:
            continue
        fs, fb, ps, pb = rates(cells)
        log.info("")
        log.info("  %s", name)
        log.info("    false positives   spread %5.1f%%   binomial %5.1f%%", 100 * fs, 100 * fb)
        log.info("    power             spread %5.1f%%   binomial %5.1f%%", 100 * ps, 100 * pb)
        summary["by_regime"][key] = {"false_positive": {"spread": fs, "binomial": fb},
                                     "power": {"spread": ps, "binomial": pb}}

    out.write_text(json.dumps(summary, indent=1))
    log.info("")
    log.info("written: %s", out)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--trials", type=int, default=N_TRIALS)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    log = setup("run_e049", config={
        "ticket": TICKET, "n_subjects": N_SUBJECTS, "top_k": TOP_K, "vocab": VOCAB,
        "trials_per_cell": args.trials, "seed": args.seed, "remote_calls": 0,
        "measure": "false-positive rate and power of (margin > donor spread) against "
                   "a binomial on the same counts, over a grid that varies effect size "
                   "and donor heterogeneity independently"})

    # Regimes are named by the (floor, spread/floor) they produce. "far" is kept as a
    # reference point precisely because it is NOT where [E-048] lives -- without it there
    # is nothing to show that the gate behaves differently in different regimes.
    REGIMES = {"far (ratio 0.44)": (60, 0.0),
               "E-048-like (ratio 1.31)": (400, 0.3),
               "E-048-like (ratio 1.49)": (900, 0.3)}
    grid = []
    for p_effect in (0.0, 0.15, 0.30, 0.50):
        for regime, (vocab, concentration) in REGIMES.items():
            rng = random.Random(args.seed + int(1000 * p_effect) + vocab)
            fs = fb = ag = 0
            floors, spreads = [], []
            for _ in range(args.trials):
                m = measure(make_world(rng, p_effect=p_effect,
                                       concentration=concentration, vocab=vocab))
                fs += m["fires_spread"]
                fb += m["fires_binomial"]
                ag += m["fires_spread"] == m["fires_binomial"]
                floors.append(m["floor"])
                spreads.append(m["spread"])
            # spread/floor is the only observable that says which regime a REAL dataset
            # sits in, so it is what lets [E-048] be located on this grid at all.
            mf = sum(floors) / len(floors)
            ms = sum(spreads) / len(spreads)
            grid.append({"p_effect": p_effect, "regime": regime,
                         "mean_floor": mf, "mean_spread": ms,
                         "spread_over_floor": ms / mf if mf else None,
                         "fire_rate_spread": fs / args.trials,
                         "fire_rate_binomial": fb / args.trials,
                         "agreement": ag / args.trials,
                         "agree": ag / args.trials >= 0.90})
    out = Path(args.out) if args.out else ROOT / "results" / "E-049-floor-gate-calibration.json"
    report(grid, log, out=out)


if __name__ == "__main__":
    main()
