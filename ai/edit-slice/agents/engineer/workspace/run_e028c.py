"""E-028c · The propagation comparison, at matched belief displacement. [T-079]

Step 2 of [E-028b]. The arms:

    ROME/EasyEdit L5 (25 steps)                    displacement 7.26 nats over 12 subjects
    ROME's update rule at L20 (400 steps)          displacement 6.97 nats over 12 subjects

The second is NOT "ROME at layer 20" and no artifact may call it that. EasyEdit's shipped
config reaches 2.61 nats at layer 20; matching layer 5 took a 16x step budget ([E-028b]).

**What [E-026] could not ask, and this can.** Both arms deliver a coefficient of exactly
1.000 to a subject-initial probe (analytic, [T-075]) and 0.962 / 0.615 to a possessive one.
If the coefficient governs effect, the subject-initial arm must be damaged identically and
the possessive arm measurably less at depth. [E-026] could not test this because its arms
differed in edit strength; they no longer do.

**The matching is AGGREGATE, not per-subject** — median absolute per-subject gap 2.29 nats,
max 6.88. The design is within-subject paired, so that is a real limitation and is why the
subject-initial arm remains the adjudicator: the coefficient says it must be identical at
both layers, so unequal damage there means the arms are not behaviourally matched whatever
the displacement bookkeeping says. Read it before reading anything else.

Pre-stated outcomes are [E-026]'s, unchanged:
    CONFIRM   possessive weakens >=40% at depth while subject-initial holds within 20%
    DENY      possessive moves <20%
    UNIFORM   both weaken similarly — a refutation, not partial support
    UNMATCHED subject-initial moves >=20% — the arms are not matched and nothing is read
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from run_e026 import C_PREDICTED, DEEP, FORMS, MODEL, SHALLOW, load_items  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DEEP_STEPS = 400
N = 12


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=120)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    items, d5, k5 = load_items(args.seed)
    items = items[:N]
    dD = torch.load(ROOT / "results" / "cache" /
                    f"E028b_deltas_L{DEEP}_s{DEEP_STEPS}_{args.seed}.pt")
    match = json.loads((ROOT / "results" / "E-028b-budget-match.json").read_text())
    cell = match["cells"][f"L{DEEP}|s{DEEP_STEPS}"]
    disp20 = dict(zip([it["cid"] for it in items], cell["cal"] + cell["held"]))
    b26 = json.loads((ROOT / "results" / "E-026b-edit-prompt.json").read_text())
    disp5 = {c: b26["raw"]["base"]["true"][i] - b26["raw"]["L5"]["true"][i]
             for i, c in enumerate(b26["case_ids"])}

    log = setup("run_e028c", config={
        "ticket": "E-028c", "thread": "T-079", "model": MODEL, "n": len(items),
        "arm_shallow": f"ROME/EasyEdit L{SHALLOW} (25 steps)",
        "arm_deep": f"ROME's update rule at L{DEEP} ({DEEP_STEPS} steps, "
                    f"displacement-matched) — NOT ROME as configured by EasyEdit",
        "forms": FORMS, "matching": "aggregate, not per-subject; median |gap| 2.29 nats",
        "measure": "teacher-forced log P(true city), paired, no candidate pool"})

    m = connect(MODEL)
    cache = ROOT / "results" / "cache" / f"E028c_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache.read_text()) if cache.exists() else {}

    for n, it in enumerate(items, 1):
        cid = it["cid"]
        if cid in done:
            continue
        ctl = items[n % len(items)]
        pairs, tags = [], []
        for who, obj in (("self", it), ("control", ctl)):
            for fname, tmpl in FORMS.items():
                pairs.append((tmpl.format(obj["subject"]), obj["true_city"]))
                tags.append(f"{who}|{fname}")
        ks5, dv5 = k5[f"{cid}|real"], d5[f"{cid}|real"]
        ksD, dvD = None, dD[cid]
        kpath = ROOT / "results" / "cache" / f"E026_kstar_L{DEEP}_s{args.seed}.pt"
        ksD = torch.load(kpath)[cid]
        conds = {"base": None,
                 f"L{SHALLOW}": (SHALLOW, ks5, float(ks5 @ ks5), dv5),
                 f"L{DEEP}": (DEEP, ksD, float(ksD @ ksD), dvD)}
        out = {}
        for cond, ed in conds.items():
            for attempt in range(args.max_stalls):
                try:
                    out[cond] = dict(zip(tags, score_pairs(m, pairs, edit=ed)))
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == args.max_stalls - 1:
                        raise
                    log.warning("%s %s failed (%s); parking %.0f min", cid, cond,
                                type(exc).__name__, args.stall_wait / 60)
                    time.sleep(args.stall_wait)
        done[cid] = {"case_id": cid, "subject": it["subject"], "control": ctl["subject"],
                     "true_city": it["true_city"], "scores": out,
                     "displacement": {f"L{SHALLOW}": disp5.get(cid),
                                      f"L{DEEP}": disp20[cid]},
                     "norm": {f"L{SHALLOW}": float(dv5.norm()),
                              f"L{DEEP}": float(dvD.norm())}}
        cache.write_text(json.dumps(done))
        log.info("  scored %d/%d  %s", n, len(items), it["subject"])

    report(list(done.values()), log)


def report(rs: list[dict], log) -> None:
    n = len(rs)
    log.info("")
    log.info("E-028c — propagation at MATCHED belief displacement (n=%d)", n)
    log.info("")
    log.info("arms, and the matching that licenses comparing them:")
    for lay, name in ((SHALLOW, f"ROME/EasyEdit L{SHALLOW} (25 steps)"),
                      (DEEP, f"ROME update rule L{DEEP} ({DEEP_STEPS} steps)")):
        d = [r["displacement"][f"L{lay}"] for r in rs if r["displacement"][f"L{lay}"]]
        log.info("  %-44s displacement %5.2f   ||dv|| %5.2f", name, st.mean(d),
                 st.mean(r["norm"][f"L{lay}"] for r in rs))
    gaps = [abs(r["displacement"][f"L{DEEP}"] - r["displacement"][f"L{SHALLOW}"])
            for r in rs if r["displacement"][f"L{SHALLOW}"]]
    log.info("  per-subject |gap| median %.2f, max %.2f — the matching is AGGREGATE",
             st.median(gaps), max(gaps))

    log.info("")
    log.info("%-14s%-8s%10s%10s%10s%10s", "form", "layer", "baseline", "post-edit",
             "drop", "c (pred)")
    D, end = {}, {}
    for fname in FORMS:
        base = st.mean(r["scores"]["base"][f"self|{fname}"] for r in rs)
        for lay in (SHALLOW, DEEP):
            col = f"L{lay}"
            post = st.mean(r["scores"][col][f"self|{fname}"] for r in rs)
            ctl = st.mean(r["scores"]["base"][f"control|{fname}"]
                          - r["scores"][col][f"control|{fname}"] for r in rs)
            end[(fname, lay)] = post
            D[(fname, lay)] = (base - post) - ctl
            log.info("%-14s%-8s%10.2f%10.2f%10.2f%10.3f", fname, col, base, post,
                     D[(fname, lay)], C_PREDICTED[(fname, lay)])

    init_pct = abs(100 * (D[("initial", SHALLOW)] - D[("initial", DEEP)])
                   / D[("initial", SHALLOW)])
    poss_pct = 100 * (D[("possessive", SHALLOW)] - D[("possessive", DEEP)]) / D[
        ("possessive", SHALLOW)]
    inter = ((D[("possessive", SHALLOW)] - D[("possessive", DEEP)])
             - (D[("initial", SHALLOW)] - D[("initial", DEEP)]))
    log.info("")
    log.info("INTERACTION CONTRAST = %+.2f nats  (possessive weakens %.0f%% at depth, "
             "subject-initial %.0f%%)", inter, poss_pct, init_pct)
    log.info("")
    if init_pct >= 20:
        log.warning("VERDICT: UNMATCHED — the subject-initial arm moved %.0f%% (>=20%%). "
                    "The coefficient is exactly 1.000 at both layers for that probe, so "
                    "equal delivery did NOT give equal effect and the arms are not "
                    "behaviourally matched despite matched displacement. Nothing about "
                    "the possessive arm may be read from this run.", init_pct)
    elif poss_pct >= 40:
        log.info("VERDICT: CONFIRM — at matched displacement the coefficient PREDICTS "
                 "effect. The possessive arm weakens %.0f%% at depth while the pinned arm "
                 "holds within %.0f%%. [T-079] answered.", poss_pct, init_pct)
    elif poss_pct < 20:
        log.info("VERDICT: DENY — at matched displacement and matched delivery the "
                 "possessive arm moved only %.0f%%. The coefficient BOUNDS delivery and "
                 "does not predict effect; the [E-016]-[E-021] arc is about delivery "
                 "only and the write-up must say so. [T-079] answered.", poss_pct)
    else:
        log.info("VERDICT: between the pre-stated bands (possessive %.0f%%, "
                 "subject-initial %.0f%%). Report the numbers, claim neither.",
                 poss_pct, init_pct)
    log.warning("n=%d and the matching is aggregate. Whatever the verdict, it is an "
                "EXISTENCE-grade statement per [O-004] — no rate, and a replication at "
                "the full 42 would cost another 400-step batch.", n)

    out = ROOT / "results" / "E-028c-matched-propagation.json"
    out.write_text(json.dumps(
        {"ticket": "E-028c", "thread": "T-079", "n": n,
         "arms": {f"L{SHALLOW}": "ROME/EasyEdit (25 steps)",
                  f"L{DEEP}": f"ROME update rule, {DEEP_STEPS} steps, matched"},
         "interaction_contrast": inter,
         "drops": {f"{f}|L{ly}": v for (f, ly), v in D.items()},
         "post_edit": {f"{f}|L{ly}": v for (f, ly), v in end.items()},
         "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
