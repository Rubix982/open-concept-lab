"""Check E-002 offline. The pairing is where this one can go quietly wrong."""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))

import run_e001 as R1                                             # noqa: E402
import run_e002 as R2                                             # noqa: E402

EDIT_SLICE = ROOT.parent / "edit-slice"


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    ks, dv = R1.load_edit_cache(EDIT_SLICE)
    ratios = R2.norm_ratios(ks, dv)
    check(len(ratios) == 42, f"a magnitude for every subject, got {len(ratios)}")
    check(all(v > 0 for v in ratios.values()), "every magnitude is positive")

    pairs = R2.pair_by_magnitude(ratios)
    check(len(pairs) == 42, "every subject is paired")
    check(all(a != b for a, b in pairs.items()), "nobody is paired with themselves")
    check(set(pairs) == set(ratios), "the pairing covers exactly the cached subjects")

    # Deterministic: the same input must give the same pairing, or the run is
    # not reproducible and the arm cannot be compared across sessions.
    check(pairs == R2.pair_by_magnitude(dict(ratios)), "pairing is deterministic")

    # The control that matters. A different-subject arm that is merely weaker
    # would answer a question nobody asked.
    diffs = [abs(ratios[b] - ratios[a]) for a, b in pairs.items()]
    rng = max(ratios.values()) - min(ratios.values())
    check(st.median(diffs) < rng / 10,
          f"paired magnitudes are close: median |diff| {st.median(diffs):.4f} "
          f"against a range of {rng:.3f}")
    check(max(diffs) < rng / 2, f"even the worst pair is matched: {max(diffs):.4f}")

    # The donor's edit must be a real edit, not the subject's own under a new name.
    for a, b in list(pairs.items())[:10]:
        check(not dv[f"{a}|real"].equal(dv[f"{b}|real"]),
              f"{a}'s donor {b} carries a different edit")

    # It extends [E-001] rather than re-running it: 1,485 traces already bought.
    prior = ROOT / "results" / "E-001-predicted-vs-measured.json"
    check(prior.exists(), "[E-001] output is on disk to extend")
    if prior.exists():
        items = json.loads(prior.read_text())["items"]
        check(all("p_base" in i and "p_real" in i and "p_ctl" in i for i in items),
              "every item already carries its three arms")
        check(all("base_token" in i for i in items),
              "and the pre-edit top-1 token, which the new arm is scored against")
        check(len(items) == 495, f"495 items, got {len(items)}")

    src = (ROOT / "agents" / "engineer" / "workspace" / "run_e002.py").read_text()
    check("key_site(" not in src.split("def step")[-1] if "def step" in src else True,
          "no package call inside a trace body")
    check("R.prob_of" in src, "scoring reuses [E-001]'s primitive rather than a copy")
    check("anchors_only" in src, "the gate can be run alone")
    check("checkpoint" in src, "the run is resumable")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\nPairing: median |magnitude diff| {st.median(diffs):.4f}, "
              f"worst {max(diffs):.4f}, over a range of {rng:.3f}.")
        print("Extends [E-001]; only the fourth arm is bought. Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
