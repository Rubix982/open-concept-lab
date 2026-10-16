"""Exercise [E-044]'s three verdicts and the arithmetic of its "divergence removed" column.

    .venv/bin/python tools/dryruns/dryrun_e044.py

CONTEXT NOT NECESSARY is the branch that must work: it says the reorientation is positional
and makes [E-020]'s attention account wrong a second independent way. A branch that
contradicts a written claim is the one least likely to have been exercised before it fires.

The gate itself is tested in the runner, not here — it needs a real forward pass. What is
tested here is that the report cannot silently divide by zero when a form does not diverge.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e044 as E  # noqa: E402


def build(unmasked: float, masked: float, n: int = 16):
    """acc[cond][form][layer] -> per-subject cosines, deepening with layer as the real
    measurement does so the deep-half median the report takes is meaningful."""
    acc = {c: {f: {L: [] for L in E.PROBE} for f in E.NAMES} for c in (0, 1)}
    for f in E.NAMES:
        for L in E.PROBE:
            fall = 1.0 - (L / 31.0)
            for i in range(n):
                j = (i - n / 2) * 0.0005
                if f == "edit form":
                    acc[0][f][L].append(1.0)
                    acc[1][f][L].append(1.0)
                else:
                    acc[0][f][L].append(1 - (1 - unmasked) * (1 - fall) + j)
                    acc[1][f][L].append(1 - (1 - masked) * (1 - fall) + j)
    return acc


def run(acc, n_masked=None):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)       # NOT NECESSARY is a warning
    E.report(acc, n_masked or {f: 3 for f in E.NAMES}, 1e-9, logging.getLogger("dry"),
             out=ROOT / "results" / "E-044-context-ablation-DRYRUN.json")
    return buf.getvalue()


CASES = [
    ("masking restores the key",    build(0.47, 0.99), "VERDICT: CONTEXT NECESSARY"),
    ("divergence survives masking", build(0.47, 0.52), "VERDICT: CONTEXT NOT NECESSARY"),
    ("masking removes about half",  build(0.47, 0.85), "VERDICT: PARTIAL"),
]


def main() -> int:
    bad = []
    for name, acc, want in CASES:
        out = run(acc)
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<30} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip()[:52] for x in out.splitlines() if 'VERDICT' in x]}")

    out = run(build(0.47, 0.99))
    ok = "div removed" in out and "E-020 cos" in out and "0.471" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'table carries both anchors':<30} -> removed + E-020",
          file=sys.stderr)
    if not ok:
        bad.append("the divergence-removed or E-020 anchor column is missing")

    # A form that never diverges would make (1 - cos) zero; the report must not divide by it.
    out = run(build(1.0, 1.0))
    ok = "VERDICT" in out and "nan" not in out.lower().split("verdict")[0][-200:]
    print(f"  {'ok  ' if ok else 'FAIL'}  {'no divergence to remove':<30} -> no divide-by-zero",
          file=sys.stderr)
    if not ok:
        bad.append("a non-diverging form produced a bad division")

    ok = all(f.upper() in out for f in E.NAMES if f != "edit form")
    print(f"  {'ok  ' if ok else 'FAIL'}  {'all forms reported':<30} -> incl. matched filler",
          file=sys.stderr)
    if not ok:
        bad.append("a form is missing from the report")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-044-context-ablation-DRYRUN.json"
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
