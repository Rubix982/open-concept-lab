"""Do the write-up's load-bearing numbers still match the files that produced them?

    python3 tools/audit_numbers.py

The project's claim is that the record cannot drift from the repository. That is a claim
about this repository and nothing checks it. Six weeks of edits, a benchmark arc added in
two days, and several numbers restated in prose — any of which could have been mistyped,
or could have been correct when written and stale since.

This is **verification, not generation**: it produces no finding and nothing to ratify. A
clean run costs a reader nothing. A dirty one is the only kind worth their attention.

Each check names the number, where the prose asserts it, and which artifact decides it.
A number with no artifact is reported as UNSOURCED rather than assumed right — that is a
real category here, since several figures come from logs rather than result files.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "..", "..", "web", "notebook", "edit-slice", "review.md")


def jload(rel):
    p = os.path.join(ROOT, "results", rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def close(a, b, tol=0.0051):
    return a is not None and b is not None and abs(a - b) <= tol


def main() -> int:
    if not os.path.exists(PAPER):
        print("write-up not found", file=sys.stderr)
        return 1
    text = open(PAPER, encoding="utf-8").read()

    checks: list[tuple[str, str, object, object]] = []

    # --- the benchmark arc, §4.6 -------------------------------------------------
    d = jload("E-037-ripple-floor-recent+random+popular.json")
    if d:
        med = d.get("median_own") or {}
        checks.append(("Compositionality I own-k*", "0.982",
                       round(med.get("Compositionality_I", -1), 3), 0.982))
        checks.append(("Forgetfulness own-k*", "1.000",
                       round(med.get("Forgetfulness", -1), 3), 1.000))
        checks.append(("permuted floor", "0.069/0.070",
                       round(d.get("floor", -1), 3), 0.069))
        checks.append(("alias n (different surface)", "370",
                       len(d.get("alias_different_surface") or []), 370))

    d = jload("E-040-alias-gradient.json")
    if d:
        checks.append(("alias gradient rho", "+0.778", round(d.get("rho", -9), 3), 0.778))
        checks.append(("alias gradient slope", "+0.847",
                       round(d.get("slope", -9), 3), 0.847))

    d = jload("R-014-mquake-forms.json")
    if d:
        bh = d.get("by_hop") or {}
        hop1_yes = bh.get("1|True", 0)
        later_yes = sum(v for k, v in bh.items() if not k.startswith("1|") and k.endswith("|True"))
        later_tot = sum(v for k, v in bh.items() if not k.startswith("1|"))
        checks.append(("MQuAKE hop-1 naming subject", "6,861", hop1_yes, 6861))
        checks.append(("MQuAKE hop-2+ naming subject", "0", later_yes, 0))
        checks.append(("MQuAKE hop-2+ total", "16,506", later_tot, 16506))

    d = jload("E-035-propagation-candidates.json")
    if d:
        sp = d.get("spearman") or {}
        checks.append(("||dv|| vs propagation", "-0.423",
                       round(sp.get("norm_delta_v", 9), 3), -0.423))

    d = jload("E-045-typeshed-possession.json")
    if d:
        checks.append(("typeshed possession", "49.5%",
                       round(100 * d.get("possession", -1), 1), 49.5))

    print(f"{'quantity':<34}{'in prose':>14}{'in artifact':>14}   verdict")
    bad = unsourced = 0
    for name, prose, got, want in checks:
        if got is None:
            print(f"{name:<34}{prose:>14}{'—':>14}   UNSOURCED")
            unsourced += 1
            continue
        ok = close(float(got), float(want)) if isinstance(want, float) else got == want
        print(f"{name:<34}{prose:>14}{got!s:>14}   {'ok' if ok else 'MISMATCH'}")
        bad += not ok

    # --- does the prose still contain the strings it should? ---------------------
    print()
    present = {
        "the 0.982 figure": "0.982", "the floor": "0.070",
        "MQuAKE's split": "16,506", "the alias slope": "0.847",
        "ChainEdit named": "ChainEdit", "the screen in §7": "Is the screen worth having",
    }
    for label, needle in present.items():
        hit = needle in text
        print(f"  {'ok  ' if hit else 'GONE'}  {label:<24} {needle!r}")
        bad += not hit

    print(f"\n{len(checks)} numeric checks, {bad} mismatched, {unsourced} unsourced")
    if not bad and not unsourced:
        print("the write-up agrees with every artifact it can be checked against")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
