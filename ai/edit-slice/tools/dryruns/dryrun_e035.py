"""Exercise [E-035]'s four verdicts, its Holm correction and its magnitude-group rule.

    .venv/bin/python tools/dryruns/dryrun_e035.py

NOTHING BEATS IT is the branch that must work. The ticket names it as the outcome to
expect and the useful one — and a branch that reports a null is the branch nobody checks,
which is how [E-036] shipped a verdict line computed over the wrong sample.

MULTICOLLINEAR matters nearly as much: it is the only branch that stops two names for one
quantity being reported as two findings.
"""
from __future__ import annotations

import io
import logging
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e035 as E  # noqa: E402

CANDS = ("norm_delta_v", "norm_k_star", "ratio_dv_over_k", "baseline_true",
         "target_prior", "residual_norm")


def build(n: int = 42, seed: int = 7, **targets: float):
    """Rows whose named candidates track propagation at roughly the requested strength."""
    import math
    import statistics as stt
    rng = random.Random(seed)
    y = [rng.gauss(10, 3) for _ in range(n)]
    # Standardise before mixing. The first version scaled the noise by (1 - |t|), which
    # gives a far stronger correlation than requested — a target of 0.62 produced 0.934,
    # and the BETWEEN case silently tested FOUND instead. x = t*z + sqrt(1-t^2)*e is the
    # construction that actually delivers the requested correlation.
    my, sy = stt.mean(y), stt.pstdev(y) or 1.0
    z = [(v - my) / sy for v in y]
    rows = []
    for i in range(n):
        r = {"case_id": str(i), "subject": "A" * (1 + i % 4) + " B",
             "propagation": y[i],
             "es_margin": 0.45 * z[i] + math.sqrt(1 - 0.45 ** 2) * rng.gauss(0, 1),
             "displacement": 0.42 * z[i] + math.sqrt(1 - 0.42 ** 2) * rng.gauss(0, 1)}
        for c in CANDS:
            t = targets.get(c, 0.0)
            r[c] = t * z[i] + math.sqrt(max(0.0, 1 - t * t)) * rng.gauss(0, 1)
        rows.append(r)
    return rows


def run(rows):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)      # NOTHING BEATS IT and MULTICOLLINEAR are warnings
    E.report([dict(r) for r in rows], logging.getLogger("dry"))
    return buf.getvalue()


CASES = [
    ("nothing tracks propagation", build(), "VERDICT: NOTHING BEATS IT"),
    ("one strong candidate",       build(residual_norm=0.95), "VERDICT: FOUND"),
    ("two names, one quantity",    build(residual_norm=0.95, baseline_true=0.95),
     "VERDICT: MULTICOLLINEAR"),
    ("clears the floor, not the bar", build(residual_norm=0.48), "VERDICT: BETWEEN"),
]


def main() -> int:
    bad = []
    for name, rows, want in CASES:
        out = run(rows)
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<32} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip()[:60] for x in out.splitlines() if 'VERDICT' in x]}")

    # Confound 3: the magnitude trio is algebraically one quantity. Three of them clearing
    # must NOT read as multicollinear evidence across distinct quantities.
    out = run(build(norm_delta_v=0.95, norm_k_star=0.95, ratio_dv_over_k=0.95))
    ok = "MULTICOLLINEAR" not in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'magnitude trio counts once':<32} -> not multicollinear",
          file=sys.stderr)
    if not ok:
        bad.append("the magnitude group was counted as several distinct quantities")

    # Confound 1: the Holm threshold must be printed and must be stricter than alpha.
    out = run(build(residual_norm=0.95))
    ok = "Holm thr" in out and "outcome spread" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'Holm + outcome spread shown':<32} -> both printed",
          file=sys.stderr)
    if not ok:
        bad.append("the Holm column or the outcome-spread line is missing")

    # A candidate strong on the unadjusted test but not after correction must read "no".
    ps = {f"c{i}": p for i, p in enumerate([0.001, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07])}
    thr = E.holm(ps)
    ok = thr["c0"] < 0.05 and abs(thr["c0"] - 0.05 / 7) < 1e-12
    print(f"  {'ok  ' if ok else 'FAIL'}  {'Holm divides by m, not m-1':<32} -> {thr['c0']:.5f}",
          file=sys.stderr)
    if not ok:
        bad.append(f"Holm's first threshold is {thr['c0']}, expected {0.05/7}")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-035-propagation-candidates.json"
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
