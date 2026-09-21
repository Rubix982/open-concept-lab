"""E-026 · Does the delivered coefficient predict displacement, or only bound it?

Everything from [E-016] to [E-021] measures DELIVERY -- what fraction of the edit vector
arrives at a position. Nothing measures whether delivery predicts EFFECT. [T-075] named
this gap in its own scope paragraph, and [E-016]'s scale test is why it cannot be assumed:
the map from coefficient to destination is not linear.

It is also the one dimension never varied. An edit has been applied at layer 5 and nowhere
else in this entire record; [E-019] varied the layer for COEFFICIENTS only.

The prediction is a dissociation, which is what makes it worth running. From [T-075]:

    probe form                          c @ L5    c @ L20
    "{} was born in the city of"         1.000     1.000   (analytic -- shares the
                                                            edit prompt's prefix up to
                                                            the subject's last token)
    "The birthplace of {} is the city of"  0.962     0.615

So editing at L20 must damage the SUBJECT-INITIAL probe identically and the POSSESSIVE
probe measurably less. No competing account predicts that pattern: "deep edits are weaker"
predicts a uniform reduction, and "the coefficient is delivery only" predicts no
systematic difference. The interaction is the claim; neither main effect is.

Possessive, not late clause: [E-017] found "The city where {} was born is" fails at
baseline in 34 of 42 chains, and an unanswerable probe cannot show a drop.

OUT OF SCOPE, explicitly. This asks whether the coefficient is a PREDICTOR. It does not
recommend an edit layer. [T-075] already recorded "a deeper edit layer would leak less to
reformulated probes" as a method-design observation and declined to chase it; CLAUDE.md
scopes this project to measuring what existing editors do. Nothing here may recommend a
layer.

REPORTING. Endpoints before drops, always. [E-025]'s drop-based headline was wrong and had
to be retracted, and that confound had been named in its own ticket while the code still
computed on drops. Naming a confound is not controlling for it.
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
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
SHALLOW = LAYER          # 5 -- EasyEdit's llama3-8b.yaml, and the whole existing record
DEEP = 20                # taken from [E-019]'s published table, run BEFORE this ticket

#: Both probes ask the SAME question with the SAME true answer (the chain's inner_1 city).
#: Only the subject's position differs, which is the whole independent variable.
FORMS = {
    "initial":    "{} was born in the city of",
    "possessive": "The birthplace of {} is the city of",
}
#: [T-075]'s measured coefficients, for the predicted-vs-observed column. Not used in any
#: computation -- printed beside the result so the prediction is legible next to the test.
C_PREDICTED = {("initial", SHALLOW): 1.000, ("initial", DEEP): 1.000,
               ("possessive", SHALLOW): 0.962, ("possessive", DEEP): 0.615}


def load_items(seed: int) -> tuple[list[dict], dict, dict]:
    """Chains that [E-014] already optimised at L5, so the two layers share subjects."""
    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    deltas5 = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{SHALLOW}_s{seed}.pt")
    kstar5 = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{SHALLOW}_s{seed}.pt")

    items = []
    for r in e14["results"]:
        cid = r["case_id"]
        if f"{cid}|real" not in deltas5:
            continue
        c = chains[cid]
        items.append({"cid": cid, "subject": c["outer"]["subject"],
                      "edit_prompt": c["outer"]["prompt"],
                      "true_city": c["inner_1"]["answer"],
                      "target": nat(r["target_country"])})
    return items, deltas5, kstar5


def deep_edit_vectors(m, items, log, seed, chunk, stall_wait, max_stalls):
    """`v*` and `k*` at the DEEP layer. Cached per chunk so a stall resumes."""
    dpath = ROOT / "results" / "cache" / f"E026_deltas_L{DEEP}_s{seed}.pt"
    kpath = ROOT / "results" / "cache" / f"E026_kstar_L{DEEP}_s{seed}.pt"
    deltas = torch.load(dpath) if dpath.exists() else {}
    kstar = torch.load(kpath) if kpath.exists() else {}

    specs = [EditSpec(it["cid"], it["edit_prompt"], it["subject"], it["target"], "real")
             for it in items if it["cid"] not in deltas]
    log.info("deep v* cache: %d of %d present; optimising %d at layer %d",
             len(deltas), len(items), len(specs), DEEP)
    stalls = 0
    for i in range(0, len(specs), chunk):
        grp = specs[i:i + chunk]
        while True:
            try:
                deltas.update(compute_v_batch(m, grp, layer=DEEP))
                break
            except Exception as exc:  # noqa: BLE001
                stalls += 1
                if stalls >= max_stalls:
                    log.error("giving up after %d stalls; %d/%d cached",
                              stalls, len(deltas), len(items))
                    raise
                log.warning("chunk %d-%d failed (%s: %s); parking %.0f min",
                            i + 1, i + len(grp), type(exc).__name__, exc, stall_wait / 60)
                time.sleep(stall_wait)
        torch.save(deltas, dpath)
        log.info("  v* %d/%d", len(deltas), len(items))

    for it in items:
        if it["cid"] in kstar:
            continue
        kstar[it["cid"]] = read_key_and_value(m, it["edit_prompt"], it["subject"], DEEP)[0]
        torch.save(kstar, kpath)
    log.info("deep k*: %d cached", len(kstar))
    return deltas, kstar


def gate(m, items, deltas5, kstar5, deep, kdeep, log, n):
    """Mandatory efficacy gate. A failed edit cannot dissociate anything.

    Does the DEEP edit take at all? Measured on the edit prompt itself: log P(injected
    target) with and without the edit, at both layers. If the deep edit moves the target
    by less than HALF of what the shallow one does, the run is INFEASIBLE and is reported
    as a feasibility result -- NOT as a Deny. Those are different claims.
    """
    sub = items[:n]
    pairs = [(it["edit_prompt"], it["target"]) for it in sub]
    base = score_pairs(m, pairs)
    lifts = {}
    for name, lay, dv, ks in (("shallow", SHALLOW, deltas5, kstar5),
                              ("deep", DEEP, deep, kdeep)):
        per = []
        for j, it in enumerate(sub):
            key = f"{it['cid']}|real" if name == "shallow" else it["cid"]
            k, d = ks[key], dv[key]
            sc = score_pairs(m, [pairs[j]], edit=(lay, k, float(k @ k), d))
            per.append(sc[0] - base[j])
        lifts[name] = per
        log.info("gate %-8s layer %2d  mean lift on the injected target %+.2f nats  %s",
                 name, lay, st.mean(per), [f"{x:+.1f}" for x in per])

    ratio = st.mean(lifts["deep"]) / st.mean(lifts["shallow"]) if st.mean(
        lifts["shallow"]) else 0.0
    log.info("gate ratio deep/shallow = %.2f", ratio)
    if ratio < 0.5:
        log.error("GATE FAILED: the layer-%d edit does not take (ratio %.2f < 0.50). "
                  "This is INFEASIBLE, not a Deny -- report it as a feasibility result.",
                  DEEP, ratio)
    else:
        log.info("GATE PASSED: the layer-%d edit takes comparably; proceed.", DEEP)
    return ratio, lifts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=6)
    ap.add_argument("--gate-n", type=int, default=4)
    ap.add_argument("--gate-only", action="store_true")
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    items, deltas5, kstar5 = load_items(args.seed)
    log = setup("run_e026", config={
        "ticket": "E-026", "thread": "T-079", "model": MODEL, "seed": args.seed,
        "layers": [SHALLOW, DEEP], "forms": FORMS, "n_subjects": len(items),
        "measure": "teacher-forced log P(true city), paired, no candidate pool",
        "editor": "ROME as configured by EasyEdit (C = I)"})
    log.info("%d subjects carried over from [E-014]'s optimised set", len(items))

    m = connect(MODEL)
    gate_items = items[:args.gate_n]
    deep, kdeep = deep_edit_vectors(m, gate_items if args.gate_only else items, log,
                                    args.seed, args.chunk, args.stall_wait,
                                    args.max_stalls)

    ratio, lifts = gate(m, items, deltas5, kstar5, deep, kdeep, log, args.gate_n)
    if args.gate_only:
        json.dump({"ticket": "E-026", "stage": "gate", "n": args.gate_n,
                   "layers": [SHALLOW, DEEP], "ratio": ratio, "lifts": lifts},
                  (ROOT / "results" / "E-026-gate.json").open("w"), indent=1)
        log.info("gate-only run complete; written results/E-026-gate.json")
        return

    # --- full 2 (layer) x 2 (form) x 2 (self/control) -------------------------------
    cache = ROOT / "results" / "cache" / f"E026_s{args.seed}.json"
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

        ks5, dv5 = kstar5[f"{cid}|real"], deltas5[f"{cid}|real"]
        ksD, dvD = kdeep[cid], deep[cid]
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
                     "true_city": it["true_city"], "target": it["target"],
                     "norm_ratio": {f"L{SHALLOW}": float(dv5.norm() / ks5.norm()),
                                    f"L{DEEP}": float(dvD.norm() / ksD.norm())},
                     "scores": out}
        cache.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(items):
            log.info("  scored %d/%d", n, len(items))

    report(list(done.values()), ratio, log)


def report(rs: list[dict], gate_ratio: float, log) -> None:
    """Endpoints first, drops second. See the module docstring."""
    N = len(rs)
    D = {}          # control-differenced drop, per (form, layer)
    end = {}        # post-edit level -- the confound-free quantity

    log.info("")
    log.info("E-026 -- log P(true city) under a country edit, n=%d", N)
    log.info("norm ratio ||dv||/||k*||:  L%d %.2f   L%d %.2f   (a large gap is a live "
             "alternative explanation)", SHALLOW,
             st.mean(r["norm_ratio"][f"L{SHALLOW}"] for r in rs), DEEP,
             st.mean(r["norm_ratio"][f"L{DEEP}"] for r in rs))
    log.info("")
    log.info("%-14s%-8s%10s%10s%10s%10s", "form", "layer", "baseline", "post-edit",
             "drop", "c (pred)")
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

    log.info("")
    for fname in FORMS:
        a, b = D[(fname, SHALLOW)], D[(fname, DEEP)]
        pct = 100 * (a - b) / a if a else float("nan")
        log.info("%-14s L%d %.2f -> L%d %.2f   (%+.0f%% at depth)",
                 fname, SHALLOW, a, DEEP, b, -pct)

    inter = ((D[("possessive", SHALLOW)] - D[("possessive", DEEP)])
             - (D[("initial", SHALLOW)] - D[("initial", DEEP)]))
    init_pct = abs(100 * (D[("initial", SHALLOW)] - D[("initial", DEEP)])
                   / D[("initial", SHALLOW)]) if D[("initial", SHALLOW)] else float("nan")
    poss_pct = 100 * (D[("possessive", SHALLOW)] - D[("possessive", DEEP)]) / D[
        ("possessive", SHALLOW)] if D[("possessive", SHALLOW)] else float("nan")

    log.info("")
    log.info("INTERACTION CONTRAST = %+.2f nats   "
             "(possessive weakens by %.0f%%, subject-initial by %.0f%%)",
             inter, poss_pct, init_pct)
    if gate_ratio < 0.5:
        log.error("VERDICT: INFEASIBLE -- the deep edit failed its efficacy gate "
                  "(ratio %.2f). Do not read the table above as a Deny.", gate_ratio)
    elif init_pct >= 20:
        log.warning("VERDICT: NOT INTERPRETABLE as a dissociation -- the subject-initial "
                    "arm moved %.0f%% (>=20%%), so the two edits are not matched. A "
                    "coefficient of exactly 1.000 at both layers did NOT give equal "
                    "effect, which is itself the finding.", init_pct)
    elif poss_pct >= 40:
        log.info("VERDICT: CONFIRM -- the coefficient PREDICTS effect. The possessive arm "
                 "weakens %.0f%% at depth while the pinned arm holds within %.0f%%.",
                 poss_pct, init_pct)
    elif poss_pct < 20:
        log.info("VERDICT: DENY -- the coefficient BOUNDS delivery and does not predict "
                 "effect (possessive moved %.0f%%). Every claim from [E-016] onward is a "
                 "claim about delivery only, and the paper must say so.", poss_pct)
    else:
        log.info("VERDICT: between the pre-stated bands (possessive %.0f%%, "
                 "subject-initial %.0f%%). Report the numbers, claim neither.",
                 poss_pct, init_pct)

    out = ROOT / "results" / "E-026-depth.json"
    out.write_text(json.dumps(
        {"ticket": "E-026", "thread": "T-079", "layers": [SHALLOW, DEEP], "forms": FORMS,
         "gate_ratio": gate_ratio, "n": N,
         "interaction_contrast": inter,
         "drops": {f"{f}|L{ly}": v for (f, ly), v in D.items()},
         "post_edit": {f"{f}|L{ly}": v for (f, ly), v in end.items()},
         "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
