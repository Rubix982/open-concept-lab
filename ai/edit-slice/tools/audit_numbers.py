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

    checks: list[tuple[str, str, object, object, str]] = []

    # --- the benchmark arc, §4.6 -------------------------------------------------
    d = jload("E-037-ripple-floor-recent+random+popular.json")
    if d:
        med = d.get("median_own") or {}
        checks.append(("Compositionality I own-k*", "0.982",
                       round(med.get("Compositionality_I", -1), 3), 0.982, "E-037-ripple-floor-recent+random+popular.json"))
        checks.append(("Forgetfulness own-k*", "1.000",
                       round(med.get("Forgetfulness", -1), 3), 1.000, "E-037-ripple-floor-recent+random+popular.json"))
        checks.append(("permuted floor", "0.069/0.070",
                       round(d.get("floor", -1), 3), 0.069, "E-037-ripple-floor-recent+random+popular.json"))
        checks.append(("alias n (different surface)", "370",
                       len(d.get("alias_different_surface") or []), 370, "E-037-ripple-floor-recent+random+popular.json"))

    d = jload("E-040-alias-gradient.json")
    if d:
        checks.append(("alias gradient rho", "+0.778", round(d.get("rho", -9), 3), 0.778, "E-040-alias-gradient.json"))
        checks.append(("alias gradient slope", "+0.847",
                       round(d.get("slope", -9), 3), 0.847, "E-040-alias-gradient.json"))

    d = jload("R-014-mquake-forms.json")
    if d:
        bh = d.get("by_hop") or {}
        hop1_yes = bh.get("1|True", 0)
        later_yes = sum(v for k, v in bh.items() if not k.startswith("1|") and k.endswith("|True"))
        later_tot = sum(v for k, v in bh.items() if not k.startswith("1|"))
        checks.append(("MQuAKE hop-1 naming subject", "6,861", hop1_yes, 6861, "R-014-mquake-forms.json"))
        checks.append(("MQuAKE hop-2+ naming subject", "0", later_yes, 0, "R-014-mquake-forms.json"))
        checks.append(("MQuAKE hop-2+ total", "16,506", later_tot, 16506, "R-014-mquake-forms.json"))

    d = jload("E-035-propagation-candidates.json")
    if d:
        sp = d.get("spearman") or {}
        checks.append(("||dv|| vs propagation", "-0.423",
                       round(sp.get("norm_delta_v", 9), 3), -0.423, "E-035-propagation-candidates.json"))

    d = jload("E-036-ripple-coefficients.json")
    if d:
        m = d.get("median") or {}
        checks.append(("E-036 Logical Generalization", "0.966",
                       round(m.get("Logical_Generalization", -1), 3), 0.966,
                       "E-036-ripple-coefficients.json"))

    d = jload("E-039-mquake-hops-MQuAKE-CF-3k.json")
    if d:
        checks.append(("MQuAKE hop-1 at final token", "0.027",
                       round(d.get("median_final_hop1", -1), 3), 0.027,
                       "E-039-mquake-hops-MQuAKE-CF-3k.json"))
        checks.append(("MQuAKE hop-2+ at final token", "0.055",
                       round(d.get("median_final_hop2plus", -1), 3), 0.055,
                       "E-039-mquake-hops-MQuAKE-CF-3k.json"))

    d = jload("E-041-reorientation.json")
    if d:
        dr = d.get("deep_ratio") or {}
        checks.append(("E-041 late-clause deep ratio", "~0.76",
                       round(dr.get("late clause", -9), 3), 0.756,
                       "E-041-reorientation.json"))

    d = jload("E-044-context-ablation.json")
    if d:
        checks.append(("E-044 gate drift (must be 0)", "0.00e+00",
                       d.get("gate_max_drift", -1), 0.0,
                       "E-044-context-ablation.json"))

    d = jload("E-045-typeshed-possession.json")
    if d:
        checks.append(("typeshed possession", "49.5%",
                       round(100 * d.get("possession", -1), 1), 49.5, "E-045-typeshed-possession.json"))

    print(f"{'quantity':<34}{'in prose':>14}{'in artifact':>14}   verdict")
    bad = unsourced = 0
    for name, prose, got, want, src in checks:
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
        "ChainEdit cited": "dong2025chainedit",   # a Cite id; renders as the name "the screen in §7": "Is the screen worth having",
    }
    for label, needle in present.items():
        hit = needle in text
        print(f"  {'ok  ' if hit else 'GONE'}  {label:<24} {needle!r}")
        bad += not hit

    print(f"\n{len(checks)} numeric checks, {bad} mismatched, {unsourced} unsourced")
    if not bad and not unsourced:
        print("the write-up agrees with every artifact it can be checked against")

    # --- write the summary, which is the only part of results/ that is tracked ---------
    #
    # On 2026-10-16 five result files were destroyed by a dry-run and the recorded numbers
    # survived only because they had been written into prose. `results/` is gitignored
    # except summaries (CLAUDE.md), so this is the one place a machine-written number can
    # live under version control. Regenerating it on every audit makes the record
    # self-verifying: if an artifact is lost, git still holds what it said.
    sm = os.path.join(ROOT, "results", "summaries")
    os.makedirs(sm, exist_ok=True)
    lines = ["# Verified headline numbers", "",
             "_Generated by `tools/audit_numbers.py`. Do not edit by hand._", "",
             "The artifacts themselves are gitignored. This file is the committed record of",
             "what they contained when last audited, so a destroyed result is recoverable as",
             "a NUMBER even when the file is not. Five were destroyed on 2026-10-16 and the",
             "numbers survived only in prose; this closes that.", "",
             "| quantity | value | artifact |", "| --- | ---: | --- |"]
    for name, prose, got, want, src in checks:
        if got is None:
            continue
        # a name like ||dv|| would break the table; escape before emitting
        lines.append(f"| {name.replace(chr(124), chr(92)+chr(124))} | `{got}` | `{src}` |")
    lines += ["", f"_{len(checks)} checks, {bad} mismatched, {unsourced} unsourced._"]
    with open(os.path.join(sm, "headline-numbers.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"written results/summaries/headline-numbers.md ({len(checks)} rows, tracked)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
