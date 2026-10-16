"""Exercise [E-045]'s three verdicts on constructed FilterReports.

    .venv/bin/python tools/dryruns/dryrun_e045.py

THIN is the branch that must work: it says the code domain is a wish, which closes a
direction the project has carried as claim 3 since the beginning. A branch that closes a
founding claim is the one least likely to have been exercised before it fires.

Built against the REAL dataclasses rather than mocks, because this runner's first draft
read `rep.items`, `.held` as an attribute and `.rank` — none of which exist — and would
have reported a plausible rate from getattr defaults instead of raising.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e045 as E  # noqa: E402
from possession import FilterConfig, FilterReport, ItemResult  # noqa: E402


def build(frac_held: float, n: int = 200, types=("None", "str", "bool", "int")):
    """A report whose held_rate is `frac_held`, spread across answer types."""
    res, picked = [], []
    for i in range(n):
        t = types[i % len(types)]
        held = i < int(frac_held * n)
        res.append(ItemResult(
            case_id=f"mod.fn{i}", relation_id="return_type", subject=f"mod.fn{i}",
            true_answer=t,
            rank_subject=1 if held else 4,
            rank_prior=3 if held else 2,          # lift > 0 only when held
            n_candidates=50))
        picked.append({"case_id": f"mod.fn{i}", "true_answer": t})
    return FilterReport(config=FilterConfig(model=E.MODEL, n_candidates=50), results=res), picked


class Args:
    seed, n_facts = 1538, 200


def run(rep, picked):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)       # THIN is a warning
    E.report(rep, picked, logging.getLogger("dry"), Args(),
             out=ROOT / "results" / "E-045-typeshed-possession-DRYRUN.json")
    return buf.getvalue()


CASES = [
    ("holds like CounterFact", 0.72, "VERDICT: HELD"),
    ("barely holds at all",    0.12, "VERDICT: THIN"),
    ("in between",             0.45, "VERDICT: BETWEEN"),
]


def main() -> int:
    bad = []
    for name, frac, want in CASES:
        out = run(*build(frac))
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<26} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip()[:46] for x in out.splitlines() if 'VERDICT' in x]}")

    out = run(*build(0.72))
    for want in ("rank-1 only", "template ALONE", "E-005", "answer type"):
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {'all four rows + type table':<26} -> {want}",
              file=sys.stderr)
        if not ok:
            bad.append(f"the {want!r} row is missing")

    # THIN must name the phrasing alternative — confound 2. Without it the verdict
    # overclaims: a flat null cannot distinguish ignorance from a bad prompt.
    out = run(*build(0.05))
    ok = "phrasing" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'THIN names the confound':<26} -> phrasing",
          file=sys.stderr)
    if not ok:
        bad.append("THIN did not name prompt phrasing as the live alternative")

    # An empty report must say so rather than divide by zero.
    empty = FilterReport(config=FilterConfig(model=E.MODEL, n_candidates=50), results=[])
    out = run(empty, [])
    ok = "nothing to report" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'empty report':<26} -> no divide-by-zero",
          file=sys.stderr)
    if not ok:
        bad.append("an empty report did not fail cleanly")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-045-typeshed-possession-DRYRUN.json"
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
