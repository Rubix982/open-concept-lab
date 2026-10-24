"""Exercise [E-047]'s three verdicts on constructed country sweeps.

    .venv/bin/python tools/dryruns/dryrun_e047.py

DENY-stereotype is the branch that must work, because it is the one that keeps the
project's current claim alive — so it is the branch I am least likely to have tested
honestly. CONFIRM-stereotype is the branch that costs us a sentence in notes/myself.md.
Both are built here, against the real `report`, before any data exists.
"""
from __future__ import annotations

import io
import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e047 as E  # noqa: E402

CS = E.COUNTRIES[:12]


def sweep(edited_for, prior_for, prior_rest=("writer", "teacher", "soldier")):
    """Build (results, priors) with the given country -> answer mappings."""
    rs = [{"country": c,
           "base": {"tokens": [" painter"], "probs": [0.71]},
           "edited": {"tokens": [" " + edited_for(c)] + [" x"] * 7,
                      "probs": [0.4] + [0.01] * 7}} for c in CS]
    priors = {c: {"tokens": [" " + prior_for(c)] + [" " + t for t in prior_rest],
                  "probs": [0.3, 0.1, 0.1, 0.1]} for c in CS}
    return rs, priors


def run(rs, priors):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.INFO)
    with tempfile.TemporaryDirectory() as td:
        E.report(rs, priors, logging.getLogger("dry"),
                 out=Path(td) / "E-047-country-sweep-DRYRUN.json")
    return buf.getvalue()


# A distinct, country-specific stereotype per country, measured and matched.
STEREO = {c: f"pro{i}" for i, c in enumerate(CS)}

CASES = [
    # the replacement ignores the country entirely -> damage
    ("country carries nothing",
     lambda c: "poet", lambda c: STEREO[c], "DENY-stereotype"),
    # the replacement IS the country's own measured prior -> inference
    ("replacement is the stereotype",
     lambda c: STEREO[c], lambda c: STEREO[c], "CONFIRM-stereotype"),
    # varies with country, but never matches that country's prior -> third thing
    ("varies but unrelated",
     lambda c: f"other{CS.index(c)}", lambda c: STEREO[c], "MIXED"),
]


def main() -> int:
    bad = []
    for name, ed, pr, want in CASES:
        out = run(*sweep(ed, pr))
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<32} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[l.strip()[:50] for l in out.splitlines() if ':' in l and l[:1].isupper()][-1:]}")

    # Both tests must always be printed, whatever the verdict — a verdict without
    # its floor beside it is the shape [E-030] shipped and had to withdraw.
    out = run(*sweep(lambda c: STEREO[c], lambda c: STEREO[c]))
    for want in ("TEST 1", "TEST 2", "floor", "country's own prior"):
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {'both tests + floor shown':<32} -> {want!r}",
              file=sys.stderr)
        if not ok:
            bad.append(f"the {want!r} line is missing")

    # A near-constant answer must DENY even when one country happens to differ,
    # otherwise a single outlier flips a damage result into an inference result.
    one_off = run(*sweep(lambda c: ("poet" if c != CS[0] else "sailor"),
                         lambda c: STEREO[c]))
    ok = "DENY-stereotype" in one_off
    print(f"  {'ok  ' if ok else 'FAIL'}  {'one outlier does not flip it':<32} -> DENY-stereotype",
          file=sys.stderr)
    if not ok:
        bad.append("a single differing country flipped DENY into something else")

    # An empty sweep must say so rather than IndexError on most_common(1)[0].
    ok = "nothing to report" in run([], {})
    print(f"  {'ok  ' if ok else 'FAIL'}  {'empty sweep':<32} -> no IndexError",
          file=sys.stderr)
    if not ok:
        bad.append("an empty sweep did not fail cleanly")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
