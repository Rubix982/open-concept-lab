"""Exercise [E-037]'s two arms on constructed key geometry.

    .venv/bin/python tools/dryruns/dryrun_e037.py

Arm A's NO SEPARATION branch is the one that must work. It withdraws [E-036]'s headline,
and the branch nobody wants is the branch most likely to ship untested — that is how
[E-036] shipped a verdict line about aliasing computed over 8 near-identical strings.

The geometry is exact, not approximate. Two entries with ORTHOGONAL k* (e1 and e2) mean a
test key `a*e1 + b*e2` has own-coefficient exactly `a` and permuted-coefficient exactly
`b`, so every number in the table below is the number the case asked for.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e037 as E  # noqa: E402
from ripple_forms import CRIT  # noqa: E402


class Args:
    subset, seed = "dry", 1538


def build(same: float, alias: float, floor: float, n_alias_true: int, n: int = 20):
    """Two entries, orthogonal k*, every coefficient placed exactly where asked."""
    e = [torch.tensor([1.0, 0.0]), torch.tensor([0.0, 1.0])]
    picked, keys, rows, partner = [], {}, {}, [1, 0]
    for i, subj in enumerate(("Alpha", "Beta")):
        tests, vecs = [], [e[i]]
        for c in CRIT:
            val = alias if c == E.ALIAS else same
            count = max(n_alias_true, 1) if c == E.ALIAS else n
            for j in range(count):
                is_alias = c == E.ALIAS and j < n_alias_true
                tests.append((c, f"prompt {c} {j}", subj, is_alias))
                # jitter keeps the median off an exact tie without moving it
                d = (j - count / 2) * 1e-4
                vecs.append((val + d) * e[i] + (floor + d) * e[1 - i])
        key = f"{subj}|{len(tests)}"
        picked.append((subj, f"edit {subj}", tests))
        keys[key] = torch.stack(vecs).half()
        rows[key] = [(c, p, ia, r) for r, (c, p, _s, ia) in enumerate(tests, start=1)]
    return picked, partner, keys, rows


def run(picked, partner, keys, rows):
    buf = io.StringIO()
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(buf)]
    root.setLevel(logging.DEBUG)          # the verdict is a .warning on two branches
    E.report(picked, partner, keys, rows, 0, 0, logging.getLogger("dry"), Args())
    return buf.getvalue()


CASES = [
    ("floor low, same-entity high",        (0.95, 0.95, 0.08, 40), "ARM A · CONTROLLED"),
    ("templated corpus — floor near 1",    (0.97, 0.97, 0.88, 40), "ARM A · NO SEPARATION"),
    ("floor in between",                   (0.95, 0.95, 0.45, 40), "ARM A · PARTIAL"),
    ("aliases drop below same-entity",     (0.95, 0.60, 0.08, 40), "ARM B · STRING-KEYED"),
    ("aliases hold",                       (0.95, 0.94, 0.08, 40), "ARM B · ENTITY-KEYED"),
    ("aliases hold but n is 8, as E-036",  (0.95, 0.94, 0.08, 8),  "ARM B · UNDERPOWERED"),
    ("no aliasing prompt differs",         (0.95, 0.94, 0.08, 0),  "ARM B did not run"),
]


def main() -> int:
    bad = []
    for name, args, want in CASES:
        out = run(*build(*args))
        ok = want in out
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<36} -> {want}", file=sys.stderr)
        if not ok:
            bad.append(f"{name}: wanted {want!r}, got "
                       f"{[x.strip() for x in out.splitlines() if 'ARM' in x]}")

    # NO FLOOR: every entry unpartnered. Nothing else in the run changes.
    picked, _partner, keys, rows = build(0.95, 0.95, 0.08, 40)
    out = run(picked, [-1, -1], keys, rows)
    ok = "NO FLOOR" in out
    print(f"  {'ok  ' if ok else 'FAIL'}  {'no admissible partner':<36} -> NO FLOOR",
          file=sys.stderr)
    if not ok:
        bad.append("NO FLOOR branch did not fire")

    # pair_up must reject a partner sharing a token, and say so.
    part, rej = E.pair_up(["Maria Anna of Bavaria", "Maria Anna Leopoldine", "Leo Arons"],
                          1538)
    ok = part[0] == 2 and part[1] == 2 and rej > 0
    print(f"  {'ok  ' if ok else 'FAIL'}  {'near-duplicate subjects rejected':<36} -> "
          f"partners {part}, {rej} rejected", file=sys.stderr)
    if not ok:
        bad.append(f"pair_up paired near-duplicates: {part}, {rej} rejections")

    for b in bad:
        print(f"      {b}", file=sys.stderr)
    stray = ROOT / "results" / "E-037-ripple-floor.json"
    if stray.exists():
        stray.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
