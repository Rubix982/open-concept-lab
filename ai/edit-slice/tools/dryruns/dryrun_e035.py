"""Exercise [E-035]'s verdict bands on constructed data whose answer is known.

Run by `tools/preflight.py` before the real run, and standalone:

    .venv/bin/python tools/dryruns/dryrun_e035.py

The first case is the one that matters: a candidate set built to correlate at ~0 must
return NOTHING BEATS IT, because that is the outcome the ticket expects and therefore the
one most likely to be waved through without checking the code can produce it.
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

N = 42
RNG = random.Random(1538)


def noise(n=N):
    return [RNG.gauss(0, 1) for _ in range(n)]


def along(prop, strength):
    """A candidate correlated with `prop` at roughly `strength`."""
    return [strength * p + (1 - strength) * RNG.gauss(0, 3) for p in prop]


def names(vals):
    """Seven candidates under the real names, so NORM_GROUP matching is exercised."""
    keys = ["||dv||", "||k*||", "||dv||/||k*||", "baseline log P(true)",
            "target prior log P(target)", "subject token count",
            "residual norm at subject, L5"]
    return dict(zip(keys, vals))


def run(cand, prop):
    """Capture report()'s output.

    `setLevel(INFO)` is load-bearing: root defaults to WARNING, so without it only the
    MULTICOLLINEAR branch — the one that logs at warning — reaches the buffer, and the
    other three cases "pass" by producing nothing to check. A single-case dry-run would
    have been green and worthless.
    """
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.INFO)
    E.report(cand, prop, logging.getLogger("dry"))
    return buf.getvalue()


def main() -> int:
    prop = [RNG.gauss(10, 4) for _ in range(N)]
    cases = []

    # 1 — everything uncorrelated. The expected real outcome, so the branch most at risk
    #     of never being exercised.
    cases.append(("all candidates uncorrelated", names([noise() for _ in range(7)]),
                  "NOTHING BEATS IT"))

    # 2 — one strong, distinct candidate (not in the norm group)
    v = [noise() for _ in range(7)]
    v[6] = along(prop, 0.92)
    cases.append(("one strong distinct candidate", names(v), "FOUND"))

    # 3 — two strong candidates that are near-copies of each other
    v = [noise() for _ in range(7)]
    v[3] = along(prop, 0.9)
    v[4] = [x + RNG.gauss(0, 0.01) for x in v[3]]
    cases.append(("two strong, near-identical", names(v), "MULTICOLLINEAR"))

    # 4 — the norm group alone must NOT count as three hits
    v = [noise() for _ in range(7)]
    v[0] = along(prop, 0.9)
    v[1] = [x + RNG.gauss(0, 0.01) for x in v[0]]
    v[2] = [a / (b + 50) for a, b in zip(v[0], v[1])]
    cases.append(("the algebraically-related norm group", names(v), "FOUND"))

    bad = []
    for name, cand, want in cases:
        out = run(cand, prop)
        ok = f"VERDICT: {want}" in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name} -> expected {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: wanted {want}, got "
                       f"{[ln.strip() for ln in out.splitlines() if 'VERDICT' in ln]}")
    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-035-candidates.json"
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
