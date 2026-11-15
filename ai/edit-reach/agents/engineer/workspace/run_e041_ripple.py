"""E-041 · Recompute the RippleEdits exposure result from the keys it already wrote.

§5.5 reports that RippleEdits items receive a median **0.982** of the update
against a **0.065** floor from a stranger's edit on the same prompts, over
23,505 readings, and offers the measure as a contamination screen on that basis.
The run behind it is [E-038], whose output directory was never committed and is
on no machine. The contributions list rests on a number nobody can open.

It does not have to be re-run. `edit-slice`'s `run_e037.py` — the script whose
own comment says *"Comma-separated for [E-038]"* — persists every key it reads,
and that cache **is** committed machinery: 2,557 entries, each a tensor whose
row 0 is the edit prompt's `k*` and whose remaining rows are its test prompts.
Both arms of the measurement are dot products over those rows. So this is an
offline recomputation and it touches NDIF for nothing.

**The selection is imported, not reimplemented.** `usable()` decides which
entries have a recoverable subject label and `pair_up()` decides which stranger
scores which prompt; both live in `run_e037` and both are reproduced here by
calling them. Rewriting either would be the fastest way to get a number that
looks right and is not the published one.

One property of the cache's key scheme is worth stating rather than discovering
later: it is `f"{subject}|{len(tests)}"`, so two entries sharing a subject name
and a test count share a cached tensor. 2,578 selected entries map to 2,557
keys. The original run read the same cache under the same scheme, so this
reproduces what it did — but it is a reason the count of entries and the count
of cached tensors do not match, and not a sign that something is missing.

Nothing is edited. Nothing is read remotely.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
SLICE = HERE.parents[4] / "edit-slice"
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(SLICE / "src"))
sys.path.insert(0, str(SLICE / "agents" / "engineer" / "workspace"))

from editreach.logs import setup           # noqa: E402
import run_e037 as R                       # noqa: E402

log = setup("E-041")

SUBSETS = ("recent", "random", "popular")
#: What §5.5 publishes for the RippleEdits row, and the criterion it belongs to.
#: The row is captioned "built to test two-hop propagation", which is
#: Compositionality — not the pooled figure over all six criteria, whose own
#: median is 0.9758. The 23,505 is the run's total readings, not that row's n.
E038_OWN, E038_FLOOR = 0.982, 0.065
PROPAGATION = "Compositionality_I"
E038_N_TOTAL = 23_505
TOLERANCE = 0.002

#: Seeds the floor is re-paired under. The own-k* median cannot move with the
#: pairing — it never touches a partner — so a spread here is a property of the
#: floor alone, and the floor is what the published number is compared against.
FLOOR_SEEDS = (1538, 1, 7, 42, 2024)


def coefficient(k: torch.Tensor, star: torch.Tensor) -> float:
    """`(k · k*) / (k* · k*)` in float32, for the reason `keys_at` returns float32."""
    k, star = k.float(), star.float()
    return float(k @ star) / float(star @ star)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538,
                    help="must match the run being reproduced; it fixes the pairing")
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--out", type=Path,
                    default=Path("results/E-041-ripple-exposure.json"))
    a = ap.parse_args()

    if a.cache is None:
        a.cache = (SLICE / "results" / "cache" /
                   f"E037_keys_{'+'.join(SUBSETS)}_L{R.LAYER}.pt")

    entries = [(s, e) for s in SUBSETS for e in
               json.loads((SLICE / "data" / "ripple" / f"{s}.json").read_text())]
    picked, origin, skipped = [], [], 0
    for sub, e in entries:
        u = R.usable(e)
        if u is None:
            skipped += 1
            continue
        picked.append(u)
        origin.append(sub)
    log.info("%d usable entries of %d, %d skipped for want of a recoverable label",
             len(picked), len(entries), skipped)

    partner, rejected = R.pair_up([s for s, _, _ in picked], a.seed)
    log.info("%d candidate partners rejected for sharing a token with their own subject",
             rejected)

    keys: dict[str, torch.Tensor] = torch.load(a.cache, map_location="cpu",
                                               weights_only=False)
    log.info("cache %s — %d entries", a.cache.name, len(keys))

    own: list[float] = []
    floor: list[float] = []
    by_criterion: dict[str, list[float]] = defaultdict(list)
    floor_by_criterion: dict[str, list[float]] = defaultdict(list)
    by_subset: dict[str, list[float]] = defaultdict(list)
    floor_by_subset: dict[str, list[float]] = defaultdict(list)
    missing = 0
    no_partner = 0

    for i, ((subj, _edit, tests), sub) in enumerate(zip(picked, origin)):
        key = f"{subj}|{len(tests)}"
        rows = keys.get(key)
        if rows is None or len(rows) != len(tests) + 1:
            missing += 1
            continue
        star = rows[0]
        j = partner[i]
        # A `-1` means no admissible stranger was found, so this entry
        # contributes an own-k* reading and no floor reading. Counted rather
        # than skipped entirely: dropping it from both arms would silently
        # change the own-k* median too.
        pstar = None
        if j == -1:
            no_partner += 1
        else:
            pkey = f"{picked[j][0]}|{len(picked[j][2])}"
            prows = keys.get(pkey)
            pstar = prows[0] if prows is not None else None

        for (crit, _p, _s, _alias), k in zip(tests, rows[1:]):
            c = coefficient(k, star)
            own.append(c)
            by_criterion[crit].append(c)
            by_subset[sub].append(c)
            if pstar is not None:
                f = coefficient(k, pstar)
                floor.append(f)
                floor_by_criterion[crit].append(f)
                floor_by_subset[sub].append(f)

    log.info("")
    log.info("%d own-k* readings, %d floor readings, %d entries uncached, "
             "%d without a partner", len(own), len(floor), missing, no_partner)
    log.info("  own k*   median %.4f", st.median(own))
    log.info("  floor    median %.4f", st.median(floor))
    log.info("  gap      %+.4f", st.median(own) - st.median(floor))

    log.info("")
    log.info("by criterion — the compositional ones are what §5.5 is about")
    for crit in sorted(by_criterion, key=lambda c: -len(by_criterion[c])):
        f = floor_by_criterion.get(crit)
        log.info("  %-26s n=%-6d own %.4f   floor %s", crit, len(by_criterion[crit]),
                 st.median(by_criterion[crit]),
                 f"{st.median(f):.4f}" if f else "—")

    log.info("")
    log.info("by subset — pooling three subsets hides which one supplies the readings")
    for sub in SUBSETS:
        if by_subset[sub]:
            log.info("  %-10s n=%-6d own %.4f   floor %.4f", sub, len(by_subset[sub]),
                     st.median(by_subset[sub]), st.median(floor_by_subset[sub]))

    # --- the floor under other pairings ------------------------------------
    # The floor is the one half of the comparison that depends on which
    # stranger scored which prompt. Re-pairing is free here — the keys are
    # already in memory — so the spread is measured rather than assumed absent.
    prop_own = by_criterion[PROPAGATION]
    floor_spread: dict[int, float] = {}
    for seed in FLOOR_SEEDS:
        part, _ = R.pair_up([s for s, _, _ in picked], seed)
        vals: list[float] = []
        for i, (subj, _e, tests) in enumerate(picked):
            rows = keys.get(f"{subj}|{len(tests)}")
            j = part[i]
            if rows is None or len(rows) != len(tests) + 1 or j == -1:
                continue
            prows = keys.get(f"{picked[j][0]}|{len(picked[j][2])}")
            if prows is None:
                continue
            for (crit, _p, _s, _a), k in zip(tests, rows[1:]):
                if crit == PROPAGATION:
                    vals.append(coefficient(k, prows[0]))
        floor_spread[seed] = st.median(vals)
    lo, hi = min(floor_spread.values()), max(floor_spread.values())

    log.info("")
    log.info("%s — the row §5.5 publishes", PROPAGATION)
    log.info("  own k*   %.4f   (published %.3f)", st.median(prop_own), E038_OWN)
    log.info("  floor under five pairings  %.4f .. %.4f   (published %.3f)",
             lo, hi, E038_FLOOR)
    for seed, v in floor_spread.items():
        log.info("    seed %-6d %.4f%s", seed, v, "   <- the pinned seed"
                 if seed == a.seed else "")

    d_own = abs(st.median(prop_own) - E038_OWN)
    own_holds = d_own <= TOLERANCE
    floor_in_range = lo - TOLERANCE <= E038_FLOOR <= hi + TOLERANCE
    reproduces = own_holds and missing == 0

    log.info("")
    if own_holds and abs(floor_spread[a.seed] - E038_FLOOR) <= TOLERANCE:
        verdict = (f"reproduces §5.5 outright: own {st.median(prop_own):.4f} against "
                   f"{E038_OWN} and floor {floor_spread[a.seed]:.4f} against "
                   f"{E038_FLOOR}, both at the pinned seed.")
    elif own_holds and floor_in_range:
        verdict = (
            f"the number that carries the claim reproduces and the one it is read "
            f"against does not pin down. Own k* is {st.median(prop_own):.4f} against "
            f"a published {E038_OWN}, and it cannot move with the pairing because it "
            f"never touches a partner. The floor does move: {lo:.4f} to {hi:.4f} over "
            f"five pairings, {floor_spread[a.seed]:.4f} at the seed this project pins "
            f"everywhere, against a published {E038_FLOOR}. So {E038_FLOOR} is a value "
            f"this measurement produces, not the value it produces at seed {a.seed}, "
            f"and §5.5 prints it as though a floor were a fixed property of the "
            f"corpus. It is a property of a pairing, and it needs its spread quoted "
            f"beside it.")
    elif own_holds:
        verdict = (f"own k* reproduces at {st.median(prop_own):.4f}, but the published "
                   f"floor {E038_FLOOR} lies outside {lo:.4f}..{hi:.4f} over five "
                   f"pairings. It did not come from this selection and §5.5 cannot "
                   f"cite it.")
    else:
        verdict = (f"does NOT reproduce. Own k* {st.median(prop_own):.4f} against a "
                   f"published {E038_OWN}, off by {d_own:.4f}, with {missing} entries "
                   f"uncached. The published figures stand unverified.")
    log.info("VERDICT: %s", verdict)

    result = {
        "ticket": "E-041", "model": R.MODEL, "layer": R.LAYER, "seed": a.seed,
        "reproduces_e038": reproduces,
        "source": "offline over edit-slice/results/cache/" + a.cache.name,
        "subsets": list(SUBSETS),
        "entries_usable": len(picked), "entries_skipped": skipped,
        "entries_uncached": missing, "entries_without_partner": no_partner,
        "partner_rejections": rejected,
        "propagation_criterion": PROPAGATION,
        "propagation_n": len(by_criterion[PROPAGATION]),
        "propagation_own_median": st.median(by_criterion[PROPAGATION]),
        "propagation_floor_by_seed": {str(k): v for k, v in floor_spread.items()},
        "propagation_floor_min": lo, "propagation_floor_max": hi,
        "published_floor_inside_pairing_spread": floor_in_range,
        "n_own": len(own), "n_floor": len(floor),
        "own_median": st.median(own), "floor_median": st.median(floor),
        "gap_median": st.median(own) - st.median(floor),
        "e038_own_median": E038_OWN, "e038_floor_median": E038_FLOOR,
        "e038_n_total": E038_N_TOTAL, "tolerance": TOLERANCE,
        "by_criterion": {c: {"n": len(v), "own_median": st.median(v),
                             "floor_median": (st.median(floor_by_criterion[c])
                                              if floor_by_criterion.get(c) else None)}
                         for c, v in by_criterion.items()},
        "by_subset": {s: {"n": len(by_subset[s]),
                          "own_median": st.median(by_subset[s]),
                          "floor_median": st.median(floor_by_subset[s])}
                      for s in SUBSETS if by_subset[s]},
        "per_reading": {"own": own, "floor": floor},
        "verdict": verdict,
        "note": ("DELIVERY, not effect. A coefficient says how much of the update "
                 "arrives at a token, never how far the answer moves. Nothing is "
                 "edited and nothing is read remotely."),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0 if reproduces else 1


if __name__ == "__main__":
    raise SystemExit(main())
