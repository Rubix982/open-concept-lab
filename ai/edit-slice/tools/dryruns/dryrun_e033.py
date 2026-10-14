"""Exercise [E-033]'s verdict bands on constructed data whose answer is known.

Run by `tools/preflight.py` before the real run, and standalone:

    .venv/bin/python tools/dryruns/dryrun_e033.py

Kept in the repository, not a scratch directory. A dry-run that lives in /tmp is one the
next person cannot re-run, which makes it a claim rather than a check — and the claim this
one backs is the only thing standing between a wrong band and a published number.

The baseline case is the one that matters: fed [E-025]'s PUBLISHED numbers, `report` must
reproduce its published verdict. Synthetic cases exercise the other branches.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e033 as E  # noqa: E402


BASE = {"self|occupation": -4.36, "self|citizenship": -1.97, "self|language": -0.71,
        "control|occupation": -4.36, "control|citizenship": -1.97,
        "control|language": -0.71}


def rows(occ, cit, lang, n=29):
    """n identical subjects at the given post-edit levels. Controls sit at baseline, so
    the control-differenced drop is exactly `baseline - post` and the arithmetic in
    `report` is checkable by hand against these numbers."""
    return [{"subject": "S", "target": "x", "norm": 7.0, "kstar_norm": 4.0,
             "base": dict(BASE),
             "edit": {"self|occupation": occ, "self|citizenship": cit,
                      "self|language": lang, "control|occupation": BASE["control|occupation"],
                      "control|citizenship": BASE["control|citizenship"],
                      "control|language": BASE["control|language"]}}
            for _ in range(n)]


CASES = [
    # (name, rows, relation, matched, injected, the verdict that must appear)
    ("E-025 published birthplace numbers — the baseline",
     rows(-6.16, -9.10, -6.20), "birthplace", "citizenship", "a country", "CROSSOVER"),
    ("occupation edit, type-matched collapses",
     rows(-9.20, -6.10, -6.30), "occupation", "occupation", "a profession", "CROSSOVER"),
    ("the displaced probe does not follow the injected type",
     rows(-6.20, -9.10, -6.30), "occupation", "occupation", "a profession",
     "NO CROSSOVER"),
    ("non-matched probes fail to converge",
     rows(-9.20, -6.10, -8.00), "occupation", "occupation", "a profession", "NO FLOOR"),
    ("type-matched probe had no room to fall",
     rows(-5.00, -4.90, -4.95), "occupation", "occupation", "a profession",
     "UNINTERPRETABLE"),
]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    log = logging.getLogger("dry")
    failures = []
    for name, rs, rel, matched, itype, want in CASES:
        import io
        buf = io.StringIO()
        h = logging.StreamHandler(buf)
        logging.getLogger().handlers = [h]
        E.report(rs, "dryrun/model", 25, log, relation=rel, matched=matched, itype=itype)
        out = buf.getvalue()
        ok = f"VERDICT: {want}" in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}  -> expected {want}", file=sys.stderr)
        if not ok:
            got = [ln for ln in out.splitlines() if "VERDICT" in ln]
            failures.append(f"{name}: wanted {want}, got {got}")
    for f in failures:
        print(f"      {f}", file=sys.stderr)
    # the dry-run writes a results file; it must not be mistaken for a real one
    for stray in (ROOT / "results").glob("E-033-crossover-dryrun*"):
        stray.unlink()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
