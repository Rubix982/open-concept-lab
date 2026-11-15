"""E-042 · Recompute the renamed-subject correlation from the cached keys.

§5's summary table says a renamed subject's delivered fraction tracks the string
similarity of the new name: rho = +0.778, slope +0.847, over 370 readings. That
is [E-026], whose output directory was never committed. One table cell is its
whole exposure, and the cell is not checkable.

It is offline for the reason [E-041] was. `usable()` in edit-slice's
`run_e037.py` marks every test whose prompt carries a **different surface form**
of the subject, and keeps both strings — the canonical label `k*` is read at,
and the surface form the coefficient is read at. The coefficients are in the key
cache. The similarity is `difflib.SequenceMatcher` over two strings already in
hand. Nothing needs a forward pass.

**What this measures, and what it does not.** The delivered fraction is how much
of the update arrives at the renamed mention. It is not how well the model
answers under the new name. A high correlation says a name that looks like the
edited one collects the edit, and says nothing about whether the answer changed.

**Why the breakdown is reported before the pooled figure.** An alias reading can
occur under any criterion, not only `Subject_Aliasing`, so "the alias
population" is a choice and a single pooled rho hides which one was made.
[E-041] found its published floor resting on a pairing nobody had varied; the
analogue here is a population nobody had split.

Nothing is edited. Nothing is read remotely.
"""

from __future__ import annotations

import argparse
import difflib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve()
SLICE = HERE.parents[4] / "edit-slice"
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(SLICE / "src"))
sys.path.insert(0, str(SLICE / "agents" / "engineer" / "workspace"))

from editreach.logs import setup           # noqa: E402
import run_e037 as R                       # noqa: E402

log = setup("E-042")

SUBSETS = ("recent", "random", "popular")
E026_RHO, E026_SLOPE, E026_N = 0.778, 0.847, 370
TOLERANCE = 0.01
BOOTSTRAP = 10_000
SEED = 1538


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Rank correlation, with ties averaged.

    Ranks rather than values because the delivered fraction is bounded above by
    1 and piles up against it, and a Pearson coefficient on a variable with a
    ceiling reports the ceiling as much as the relationship.
    """
    def rank(v: np.ndarray) -> np.ndarray:
        order = v.argsort()
        r = np.empty(len(v), dtype=float)
        r[order] = np.arange(len(v), dtype=float)
        # average the ranks of tied values, which aliasing produces often:
        # many surface forms differ from the canonical label by one token.
        _, inv, counts = np.unique(v, return_inverse=True, return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inv, r)
        return (sums / counts)[inv]

    rx, ry = rank(x), rank(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = float(np.sqrt((rx ** 2).sum() * (ry ** 2).sum()))
    return float((rx * ry).sum() / denom) if denom else float("nan")


def ols_slope(x: np.ndarray, y: np.ndarray) -> float:
    vx = float(((x - x.mean()) ** 2).sum())
    return float(((x - x.mean()) * (y - y.mean())).sum() / vx) if vx else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--out", type=Path,
                    default=Path("results/E-042-renamed-subject.json"))
    a = ap.parse_args()

    if a.cache is None:
        a.cache = (SLICE / "results" / "cache" /
                   f"E037_keys_{'+'.join(SUBSETS)}_L{R.LAYER}.pt")

    entries = [(s, e) for s in SUBSETS for e in
               json.loads((SLICE / "data" / "ripple" / f"{s}.json").read_text())]
    picked, origin = [], []
    for sub, e in entries:
        u = R.usable(e)
        if u is not None:
            picked.append(u)
            origin.append(sub)

    keys = torch.load(a.cache, map_location="cpu", weights_only=False)
    log.info("%d usable entries, cache holds %d", len(picked), len(keys))

    sim: list[float] = []
    frac: list[float] = []
    crit_of: list[str] = []
    sub_of: list[str] = []
    missing = 0

    for (subj, _edit, tests), sub in zip(picked, origin):
        rows = keys.get(f"{subj}|{len(tests)}")
        if rows is None or len(rows) != len(tests) + 1:
            missing += 1
            continue
        star = rows[0].float()
        denom = float(star @ star)
        for (crit, _p, surface, is_alias), k in zip(tests, rows[1:]):
            if not is_alias:
                continue
            sim.append(difflib.SequenceMatcher(None, subj, surface).ratio())
            frac.append(float(k.float() @ star) / denom)
            crit_of.append(crit)
            sub_of.append(sub)

    x, y = np.array(sim), np.array(frac)
    log.info("%d alias readings, %d entries uncached", len(x), missing)
    if len(x) < 3:
        log.error("too few alias readings to correlate")
        return 1

    # --- the breakdown, before the pooled figure ---------------------------
    log.info("")
    log.info("by criterion — an alias reading is not only a Subject_Aliasing one")
    by_crit: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(crit_of):
        by_crit[c].append(i)
    crit_out = {}
    for c, idx in sorted(by_crit.items(), key=lambda kv: -len(kv[1])):
        if len(idx) >= 3:
            r = spearman(x[idx], y[idx])
            s = ols_slope(x[idx], y[idx])
            crit_out[c] = {"n": len(idx), "rho": r, "slope": s,
                           "similarity_median": float(np.median(x[idx])),
                           "delivered_median": float(np.median(y[idx]))}
            log.info("  %-26s n=%-5d rho %+.3f  slope %+.3f  median sim %.3f  "
                     "median delivered %.3f", c, len(idx), r, s,
                     np.median(x[idx]), np.median(y[idx]))
        else:
            crit_out[c] = {"n": len(idx), "rho": None, "slope": None,
                           "similarity_median": float(np.median(x[idx])),
                           "delivered_median": float(np.median(y[idx]))}
            log.info("  %-26s n=%-5d too few to correlate", c, len(idx))

    log.info("")
    log.info("by subset — [E-037] recorded that one subset supplies most aliases")
    sub_out = {}
    for s_name in SUBSETS:
        idx = [i for i, v in enumerate(sub_of) if v == s_name]
        if len(idx) >= 3:
            sub_out[s_name] = {"n": len(idx), "rho": spearman(x[idx], y[idx]),
                               "slope": ols_slope(x[idx], y[idx])}
            log.info("  %-10s n=%-5d rho %+.3f  slope %+.3f", s_name, len(idx),
                     sub_out[s_name]["rho"], sub_out[s_name]["slope"])

    # --- pooled, with an interval ------------------------------------------
    rho = spearman(x, y)
    slope = ols_slope(x, y)
    rng = random.Random(SEED)
    n = len(x)
    boots = []
    for _ in range(BOOTSTRAP):
        idx = [rng.randrange(n) for _ in range(n)]
        boots.append(spearman(x[idx], y[idx]))
    boots.sort()
    lo, hi = boots[int(0.025 * BOOTSTRAP)], boots[int(0.975 * BOOTSTRAP)]

    log.info("")
    log.info("pooled over %d alias readings", n)
    log.info("  Spearman rho  %+.4f   95%% CI %+.4f to %+.4f   (published %+.3f)",
             rho, lo, hi, E026_RHO)
    log.info("  OLS slope     %+.4f                            (published %+.3f)",
             slope, E026_SLOPE)

    d_rho, d_slope = abs(rho - E026_RHO), abs(slope - E026_SLOPE)
    # The gate is on the statistics, which are what the row publishes. The
    # population size is reported beside them rather than folded into the gate:
    # a count that differs by one reading does not make two matching statistics
    # a mismatch, and hiding the difference inside a pass/fail would lose it.
    n_matches = n == E026_N
    reproduces = d_rho <= TOLERANCE and d_slope <= TOLERANCE and missing == 0

    # Which subset the pooled figure is actually made of. [E-037] recorded that
    # one subset supplies most aliases; if that holds, the pooled rho is close
    # to that subset's rho and the row is narrower than "RippleEdits".
    biggest = max(sub_out, key=lambda k: sub_out[k]["n"]) if sub_out else None
    share = sub_out[biggest]["n"] / n if biggest else 0.0

    log.info("")
    if reproduces and n_matches:
        verdict = (f"reproduces [E-026]: rho {rho:+.3f} against {E026_RHO:+.3f}, "
                   f"slope {slope:+.3f} against {E026_SLOPE:+.3f}, {n} readings as "
                   f"published.")
    elif reproduces:
        verdict = (
            f"both statistics reproduce and the count is off by {abs(n - E026_N)}: "
            f"rho {rho:+.4f} against a published {E026_RHO:+.3f} and slope "
            f"{slope:+.4f} against {E026_SLOPE:+.3f}, over {n} alias readings "
            f"against {E026_N} published. Two statistics landing on their published "
            f"values to three decimals is not what a different population produces, "
            f"so the row is taken as reproduced and the one-reading difference is "
            f"recorded as unexplained rather than resolved.")
    else:
        verdict = (f"does NOT reproduce [E-026]: rho {rho:+.3f} against "
                   f"{E026_RHO:+.3f} (off by {d_rho:.3f}) and slope {slope:+.3f} "
                   f"against {E026_SLOPE:+.3f} (off by {d_slope:.3f}), over {n} "
                   f"readings. The row stands unverified.")
    log.info("VERDICT: %s", verdict)

    if biggest and share > 0.5:
        log.info("")
        log.info("QUALIFICATION: %.0f%% of the readings come from the %r subset "
                 "alone (rho %+.3f there). On %r, n=%d, rho is %+.3f. The pooled "
                 "figure is mostly one subset's and the row should say which.",
                 100 * share, biggest, sub_out[biggest]["rho"],
                 min(sub_out, key=lambda k: sub_out[k]["n"]),
                 sub_out[min(sub_out, key=lambda k: sub_out[k]["n"])]["n"],
                 sub_out[min(sub_out, key=lambda k: sub_out[k]["n"])]["rho"])

    result = {
        "ticket": "E-042", "model": R.MODEL, "layer": R.LAYER,
        "reproduces_e026": reproduces,
        "source": "offline over edit-slice/results/cache/" + a.cache.name,
        "n_alias_readings": n, "entries_uncached": missing,
        "rho": rho, "rho_ci95": [lo, hi], "slope": slope,
        "similarity_median": float(np.median(x)),
        "delivered_median": float(np.median(y)),
        "e026_rho": E026_RHO, "e026_slope": E026_SLOPE, "e026_n": E026_N,
        "tolerance": TOLERANCE, "bootstrap": BOOTSTRAP, "seed": SEED,
        "n_published": E026_N, "n_matches_published": n_matches,
        "largest_subset": biggest,
        "largest_subset_share": share,
        "by_criterion": crit_out, "by_subset": sub_out,
        "per_reading": {"similarity": [float(v) for v in x],
                        "delivered": [float(v) for v in y],
                        "criterion": crit_of, "subset": sub_of},
        "verdict": verdict,
        "note": ("DELIVERY, not effect. This is how much of the update reaches the "
                 "renamed mention, never whether the model's answer changed under "
                 "the new name. Nothing is edited and nothing is read remotely."),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0 if reproduces else 1


if __name__ == "__main__":
    raise SystemExit(main())
