"""E-015 · How loose is the Cauchy-Schwarz bound on the coefficient?

ROME adds `delta * c(k)` at the edited layer, where `delta = v* - W k*` is fixed
and only the scalar

    c(k) = (k* . k) / (k* . k*)

varies with the token. `c` is therefore the projection coefficient of `k` onto
`k*`, so Cauchy-Schwarz bounds it for *every* prompt, with no enumeration and no
forward pass through the edited model:

    |c(k)| <= ||k|| / ||k*||,   with equality exactly when k is parallel to k*.

`C = I` throughout this project (see `coefficients()` in `run_e004.py`), so the
norms are Euclidean and no whitening enters the derivation.

The bound is certainly true. This asks whether it is tight enough to forbid
anything -- a bound never approached rules nothing out. Closes C-007.

    python agents/engineer/workspace/run_e015.py

Input is `results/cache/E004_keys.pt`; nothing is read from NDIF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from editreach.logs import setup  # noqa: E402

CACHE = ROOT / "results/cache/E004_keys.pt"
PUBLISHED = ROOT / "results/E-004-far-field-floor.json"
OUT = ROOT / "results/E-015-bound-looseness.json"

SEED = 1538
RESAMPLES = 10_000
#: Below this, |c| is small enough that bound/|c| says more about the denominator
#: than about the bound. A far-field coefficient near zero is the expected case,
#: not an anomaly, so this is a reporting decision and is reported with the result.
C_FLOOR = 1e-6


def boot_median(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """Percentile bootstrap interval for the median."""
    if len(x) < 2:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, len(x), size=(RESAMPLES, len(x)))
    meds = np.median(x[idx], axis=1)
    return (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def main() -> None:
    log = setup("run_e015", config={"cache": str(CACHE), "seed": SEED})
    rows = torch.load(CACHE, map_location="cpu", weights_only=False)
    log.info("loaded %d instances from %s", len(rows), CACHE.name)

    # ---- step 1: the gate. The cache must reproduce the published numbers. ----
    pub = json.load(open(PUBLISHED))["per_question"]
    # The published lists are hop-2 coefficients read at the final token, in the
    # order the instances were written.
    want = None
    for v in pub.values():
        if isinstance(v, list) and len(v) > 2 and all(isinstance(z, float) for z in v):
            want = v
            break
    if want is None:
        log.error("no per-question coefficient list found in %s", PUBLISHED.name)
        sys.exit(1)

    got = []
    for r in rows.values():
        if r["hop"] != 2:
            continue
        ks = r["k_star"].double()
        got += (r["k_final"].double() @ ks / (ks @ ks)).tolist()
        if len(got) >= len(want):
            break

    n_chk = min(len(got), len(want), 16)
    worst = max(abs(got[i] - want[i]) for i in range(n_chk))
    gate = worst < 1e-6
    log.info("gate: %d hop-2 coefficients recomputed, worst deviation %.3e -> %s",
             n_chk, worst, "PASS" if gate else "FAIL")
    if not gate:
        log.error("the cache and the published numbers disagree; nothing else here is "
                  "meaningful. Stopping.")
        sys.exit(1)

    # ---- step 2: c and the bound, every question-position ----
    items = []
    for cid, r in rows.items():
        ks = r["k_star"].double()
        ks_n = float(ks.norm())
        denom = float(ks @ ks)
        for i, named in enumerate(r["names_subject"]):
            # k_natural is the subject's last token where the question names the
            # subject, the final token otherwise; k_final is always the final
            # token. Reading the near field off k_final measures the final-token
            # coefficient and reports it as a subject-position one.
            k = (r["k_natural"] if named else r["k_final"])[i].double()
            c = float(ks @ k / denom)
            bound = float(k.norm() / ks_n)
            items.append({
                "case_id": int(cid) if str(cid).isdigit() else cid,
                "hop": r["hop"], "relation": r["relation"],
                "regime": "near" if named else "far",
                "key": "k_natural" if named else "k_final",
                "c": c, "bound": bound,
            })

    # ---- step 5 (run early: a violation invalidates everything) ----
    viol = [it for it in items if abs(it["c"]) > it["bound"] * (1 + 1e-9)]
    if viol:
        log.error("%d items violate |c| <= bound. This is an implementation error, "
                  "not a finding.", len(viol))
        sys.exit(1)
    log.info("all %d items satisfy |c| <= bound", len(items))

    # ---- steps 3 and 4: looseness, per regime ----
    rng = np.random.default_rng(SEED)
    summary = {}
    for regime in ("near", "far"):
        grp = [it for it in items if it["regime"] == regime]
        kept = [it for it in grp if abs(it["c"]) >= C_FLOOR]
        dropped = len(grp) - len(kept)
        ratios = np.array([it["bound"] / abs(it["c"]) for it in kept])
        for it in kept:
            it["looseness"] = it["bound"] / abs(it["c"])
        lo, hi = boot_median(ratios, rng)
        summary[regime] = {
            "n": len(grp), "n_used": len(kept), "n_dropped_c_below_floor": dropped,
            "median_looseness": float(np.median(ratios)),
            "ci95": [lo, hi],
            "iqr": [float(np.percentile(ratios, 25)), float(np.percentile(ratios, 75))],
            "max_looseness": float(ratios.max()),
            "median_c": float(np.median([abs(it["c"]) for it in kept])),
            "median_bound": float(np.median([it["bound"] for it in kept])),
        }
        s = summary[regime]
        log.info("%s field: n=%d (dropped %d), median looseness %.2f "
                 "(95%% CI %.2f-%.2f), IQR %.2f-%.2f, max %.1f",
                 regime, s["n"], dropped, s["median_looseness"], lo, hi,
                 s["iqr"][0], s["iqr"][1], s["max_looseness"])

    OUT.write_text(json.dumps({
        "ticket": "E-015", "card": "C-007",
        "model": "meta-llama/Llama-3.1-8B", "layer": 5, "covariance": "identity",
        "meta": {
            "input": CACHE.name,
            "gate": {"n_checked": n_chk, "worst_deviation": worst, "passed": gate},
            "c_floor": C_FLOOR, "seed": SEED, "resamples": RESAMPLES,
            "numpy": np.__version__, "torch": torch.__version__,
        },
        "summary": summary,
        "items": items,
    }, indent=1) + "\n")
    log.info("wrote %s (%d items)", OUT, len(items))


if __name__ == "__main__":
    main()
