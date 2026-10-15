"""Exercise [E-041]'s three verdicts on constructed divergence accumulations.

    .venv/bin/python tools/dryruns/dryrun_e041.py

MLP WRITES IT is the branch that must work. It would make the attention account named in
[E-020] and carried in [T-077] wrong, and nothing in the record predicts it — which is
exactly the branch least likely to have been exercised before it fires for real.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e041 as E  # noqa: E402


def build(attn: float, mlp: float, n: int = 16):
    """acc[form][layer] -> per-subject (D_attn, D_mlp), growing with depth as a real
    accumulation does, so the deeper-half median the report takes is meaningful."""
    acc = {f: {L: [] for L in E.PROBE} for f in E.NAMES}
    for f in E.NAMES:
        if f == "edit form":
            continue
        for L in E.PROBE:
            grow = 1.0 + L / 8.0
            for i in range(n):
                jitter = 1.0 + (i - n / 2) * 0.004
                acc[f][L].append((attn * grow * jitter, mlp * grow * jitter))
    return acc


def run(acc):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)      # MLP WRITES IT is a warning
    E.report(acc, logging.getLogger("dry"))
    return buf.getvalue()


CASES = [
    ("attention dominates",   build(10.0, 1.0), "VERDICT: ATTENTION WRITES IT"),
    ("the MLP dominates",     build(1.0, 10.0), "VERDICT: MLP WRITES IT"),
    ("neither separates",     build(5.0, 4.0),  "VERDICT: BOTH"),
    ("exactly at the 2x bar", build(2.0, 1.0),  "VERDICT: ATTENTION WRITES IT"),
]


def main() -> int:
    bad = []
    for name, acc, want in CASES:
        out = run(acc)
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<26} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip()[:48] for x in out.splitlines() if 'VERDICT' in x]}")

    # The table must carry [E-020]'s cosine beside the accumulation — the whole point is
    # reading one against the other, and a table missing it invites reading D_attn alone.
    out = run(build(10.0, 1.0))
    ok = "E-020 cos" in out and "0.471" in out and "0.984" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'cosine column present':<26} -> both endpoints",
          file=sys.stderr)
    if not ok:
        bad.append("the E-020 cosine column is missing or incomplete")

    # Every non-reference form must appear; the padded control is confound 2 and dropping
    # it silently would remove the arm that decides whether this is about context at all.
    ok = all(f.upper() in out for f in E.NAMES if f != "edit form")
    print(f"  {'ok  ' if ok else 'FAIL'}  {'all forms reported':<26} -> incl. padded control",
          file=sys.stderr)
    if not ok:
        bad.append(f"a form is missing from the report: {E.NAMES}")

    # An empty accumulation must say so rather than divide by nothing.
    out = run({f: {L: [] for L in E.PROBE} for f in E.NAMES})
    ok = "nothing to report" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'empty accumulation':<26} -> reports, no crash",
          file=sys.stderr)
    if not ok:
        bad.append("an empty accumulation did not report cleanly")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-041-reorientation.json"
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
