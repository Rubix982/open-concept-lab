"""Exercise [E-039]'s verdict bands and both confound tables on constructed rows.

    .venv/bin/python tools/dryruns/dryrun_e039.py

NO ESCAPE is the branch that must work. It says naming the subject is not what delivers
the update, which would make [E-037]'s reading of Table 11 wrong and force a rewrite of
§4.6 — and a branch that costs us a published paragraph is the one most likely to ship
untested. [E-036] shipped exactly that way.

The confound tables are tested too, because [E-036]'s defect was never in a verdict: it
was in which rows reached the verdict at all.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e039 as E  # noqa: E402


class Args:
    file, chain_len = "dry.json", 0


def build(h1: float, h2: float, n: int = 30, chain_len: int = 2,
          rel1: str = "P27", rel2: str = "P27"):
    """Rows shaped like the cache's, with each arm's median placed where asked."""
    rows = {}
    for i in range(n):
        d = (i - n / 2) * 1e-4          # jitter off an exact tie without moving the median
        for hop, val, rel in ((1, h1, rel1), (2, h2, rel2)):
            rows[f"{hop}-{i}"] = {
                "hop": hop, "chain_len": chain_len, "relation": rel,
                "final": [val + d, val - d], "natural": [val + d, val - d],
                "names_subject": [hop == 1, hop == 1]}
    return rows


def run(rows):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)        # NO ESCAPE is a .warning
    E.report(rows, 0, logging.getLogger("dry"), Args())
    return buf.getvalue()


CASES = [
    ("hop-2+ escapes, hop-1 does not", build(0.95, 0.08), "VERDICT: ESCAPES"),
    ("hop-2+ reached anyway",          build(0.95, 0.88), "VERDICT: NO ESCAPE"),
    ("in between",                     build(0.95, 0.45), "VERDICT: BETWEEN"),
]


def main() -> int:
    bad = []
    for name, rows, want in CASES:
        out = run(rows)
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<34} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: got {[x.strip() for x in out.splitlines() if 'VERDICT' in x]}")

    out = run(build(0.95, 0.08))
    for want in ("CONTROLLED", "RELATION-MATCHED"):
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {'confound tables present':<34} -> {want}",
              file=sys.stderr)
        if not ok:
            bad.append(f"{want} table missing")

    # confound 3 must SAY SO when no relation spans both arms, rather than printing an
    # empty table that reads as a clean control
    out = run(build(0.95, 0.08, rel1="P27", rel2="P495"))
    ok = "UNCONTROLLED" in out and "RELATION-MATCHED" not in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'disjoint relations are flagged':<34} -> UNCONTROLLED",
          file=sys.stderr)
    if not ok:
        bad.append("a disjoint relation mix did not report itself as uncontrolled")

    # a chain-length filter that empties the 2-hop row must not crash the report
    out = run(build(0.95, 0.08, chain_len=4))
    ok = "CONTROLLED" in out and "VERDICT" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'no 2-hop rows survive':<34} -> still reports",
          file=sys.stderr)
    if not ok:
        bad.append("an empty 2-hop row broke the report")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-039-mquake-hops-dry.json"
    assert "dry" in stray.name, stray
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
