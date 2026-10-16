"""Exercise [E-036]'s verdict bands on constructed coefficient distributions.

    .venv/bin/python tools/dryruns/dryrun_e036.py

The NOT MECHANICAL case is the one that must work. It is the outcome that would close the
project's one outward-facing claim, and an outcome nobody wants is the branch most likely
to be shipped untested.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e036 as E  # noqa: E402
from ripple_forms import CRIT  # noqa: E402


def acc(same, alias, diff, n=40):
    out = {}
    for c in CRIT:
        v = same if c in E.SAME_ENTITY else (diff if c in E.DIFFERENT_ENTITY else alias)
        out[c] = [v + (i - n / 2) * 0.001 for i in range(n)]
    return out


def run(a):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.INFO)
    E.report(a, 200, 50, logging.getLogger("dry"))
    return buf.getvalue()


CASES = [
    ("same-entity high, different-entity at the floor", acc(0.95, 0.40, 0.09), "MECHANICAL"),
    ("same-entity below half — closes the claim", acc(0.30, 0.25, 0.08), "NOT MECHANICAL"),
    ("every criterion alike", acc(0.60, 0.62, 0.58), "UNDIFFERENTIATED"),
    ("high but the floor is not low", acc(0.95, 0.90, 0.70), "between the pre-stated"),
]


def main() -> int:
    bad = []
    for name, a, want in CASES:
        out = run(a)
        ok = f"VERDICT: {want}" in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip() for x in out.splitlines() if 'VERDICT' in x]}")
    # the alias line must say STRING when aliases drop and ENTITY when they do not
    drops = run(acc(0.95, 0.40, 0.09))
    holds = run(acc(0.95, 0.94, 0.09))
    for label, text, want in (("aliases drop", drops, "STRING"),
                              ("aliases hold", holds, "ENTITY")):
        ok = want in text
        print(f"  {'ok  ' if ok else 'FAIL'}  {label} -> reports {want}", file=sys.stderr)
        if not ok:
            bad.append(label)
    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-036-ripple-coefficients-DRYRUN.json"
    # A dry-run must never be able to name a real artifact. [E-037]'s cleanup deleted a
    # 40-minute result on 2026-10-15; that one file was fixed and the CLASS was not, and on
    # 2026-10-16 running every dryrun as a health check destroyed four more. The assertion
    # is the fix — a path without "DRYRUN" in it now raises instead of unlinking.
    assert "DRYRUN" in stray.name, f"refusing to unlink a non-dryrun path: {stray}"
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
