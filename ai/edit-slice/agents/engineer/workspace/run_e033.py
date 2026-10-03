"""E-033 · The relation crossover — is floor-plus-type-displacement general? [T-081, T-080]

[E-025] found a BIRTHPLACE edit produces a floor plus type-matched displacement:

    occupation   -6.16      not type-matched to a country
    language     -6.20      not type-matched  (0.04 apart, after starting 3.65 apart)
    citizenship  -9.10      TYPE-MATCHED to the injected country

Stated as a general mechanism, measured on one relation. Edited relation is the third of
[T-065]'s never-varied dimensions; the other two are now done ([E-028] layer, [E-032]
model). This is the TEST, not a verification.

**Crossover.** Edit occupation instead — inject a profession — and the prediction inverts:
occupation becomes the type-matched probe and should take the extra displacement, while
citizenship falls back to the floor beside language.

    CROSSOVER     occupation finishes >=1.5 nats below BOTH others, AND the
                  citizenship-language gap collapses below 1 nat (it was 2.90)
    NO CROSSOVER  citizenship stays most displaced even with a profession injected ->
                  the structure is about countries/birthplace, not about type
    NO FLOOR      the two non-matched probes do not converge within 1 nat

**The edit prompt is subject-initial by construction.** [E-014]'s cached `|ctl` deltas are
NOT reused: their prompt is "By profession, {} is a", which does not begin with the subject
(so the coefficient is not pinned as in every other edit here) and is identical to the
occupation PROBE (so scoring it would measure efficacy, not displacement of something else).

**Levels, never drops.** [E-025]'s first headline was computed on drops, said "semantic
relatedness", and was retracted. Baselines here span 3.65 nats. Same trap, one relation over.
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
from edit import EditSpec, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402
from run_e028b import optimise  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
#: EasyEdit's llama3-8b default. Not a constant across models: layer 5 of 32 is depth
#: fraction 0.16, layer 5 of 80 is 0.06, and [E-028] showed layer changes propagation by
#: 3x. Cross-model arms must be matched by FRACTION ([E-032]), so this is now a flag and
#: the matched layer at 70B is 13, not 5.
LAYER = 5
#: Everything below that changes a number goes in the cache key. The first version keyed
#: the scores cache on (model, relation, steps) and omitted the LAYER, so a layer-13 run
#: would have silently loaded layer-5 scores and reported them as new. Same discipline as
#: `possession.FilterConfig.fingerprint`.
#: Both edit prompts are SUBJECT-INITIAL, so the coefficient is pinned at 1.000 in each
#: arm and delivery is held fixed across the crossover by construction. The occupation
#: prompt is deliberately NOT "By profession, {} is a" — that is the occupation PROBE,
#: and editing on it would measure efficacy rather than displacement of something else.
RELATIONS = {
    "occupation": {"prompt": "{} works as a", "type": "a profession",
                   "matches_probe": "occupation"},
    "birthplace": {"prompt": "{} was born in the country of", "type": "a country",
                   "matches_probe": "citizenship"},
}
EDIT_OCC = "{} works as a"          # kept for the [E-025] mirror table below
PROBES = {
    "occupation":  "By profession, {} is a",
    "citizenship": "{} is a citizen of",
    "language":    "The native language of {} is",
}
#: [E-025], birthplace edit at 8B — the arm this one is the mirror of.
BIRTHPLACE_8B = {"occupation": -6.16, "language": -6.20, "citizenship": -9.10}
MATCH_MARGIN, FLOOR_BAND = 1.5, 1.0


def load(seed: int, relation: str):
    e25 = json.loads((ROOT / "results" / "E-025-language.json").read_text())
    e14 = json.loads((ROOT / "results" /
                      "E-014-destination-meta-llama_Llama-3.1-8B.json").read_text())
    key = "target_occ" if relation == "occupation" else "target_country"
    tgt = {r["case_id"]: r.get(key) for r in e14["results"]}
    items = []
    for r in e25["results"]:
        t = tgt.get(r["case_id"])
        if not t:
            continue
        if relation == "birthplace":
            from run_e013 import nat
            t = nat(t)
        items.append({"cid": r["case_id"], "subject": r["subject"],
                      "attrs": r["attrs"], "target": t, "control": r["control"]})
    return items


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B")
    ap.add_argument("--relation", default="occupation", choices=sorted(RELATIONS))
    ap.add_argument("--layer", type=int, default=LAYER,
                    help="edit layer; match by DEPTH FRACTION across models, not index")
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--stall-wait", type=float, default=120)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    rel = RELATIONS[args.relation]
    edit_tmpl = rel["prompt"]
    items = load(args.seed, args.relation)
    tag = f"{args.model.replace('/', '_')}_{args.relation}_L{args.layer}"
    log = setup("run_e033", config={
        "ticket": "E-033", "thread": ["T-081", "T-080"], "model": args.model,
        "layer": args.layer, "steps": args.steps, "n": len(items),
        "relation_edited": args.relation, "edit_prompt": edit_tmpl,
        "injected_type": rel["type"], "type_matched_probe": rel["matches_probe"],
        "probes": PROBES, "reference_arm": "[E-025] birthplace edit at 8B",
        "measure": "teacher-forced log P(true answer); LEVELS, not drops",
        "note": "E-014's |ctl deltas deliberately NOT reused — wrong prompt shape"})
    log.info("%d subjects carried from [E-025] with a target occupation", len(items))

    m = connect(args.model)
    specs = [EditSpec(it["cid"], edit_tmpl.format(it["subject"]), it["subject"],
                      it["target"], "real") for it in items]
    dpath = ROOT / "results" / "cache" / f"E033_deltas_{tag}_s{args.steps}.pt"
    # COMPLETENESS, not existence. `optimise` now checkpoints after every chunk to this
    # same path, so a partial file is the normal state after an interrupted run — and
    # the first version of this check loaded 9 of 29 deltas, reported "cached", skipped
    # optimisation entirely and walked into the scoring loop short. A cache that is
    # trusted because the file exists is how a partial run reports itself as a whole one.
    cached = torch.load(dpath) if dpath.exists() else {}
    want = {sp.case_id for sp in specs}
    if want <= set(cached):
        deltas = cached
        log.info("deltas cached and complete (%d/%d)", len(cached), len(want))
    else:
        log.info("optimising v* for %d %s edits at %d steps (%d already checkpointed)",
                 len(specs), args.relation, args.steps, len(cached))
        t0 = time.time()
        deltas = optimise(m, specs, args.layer, args.steps, log, args.chunk,
                          args.stall_wait, args.max_stalls, checkpoint=dpath)
        torch.save(deltas, dpath)
        log.info("  took %.0f min", (time.time() - t0) / 60)

    kstar = {it["cid"]: retrying(
        lambda it=it: read_key_and_value(m, edit_tmpl.format(it["subject"]),
                                         it["subject"], args.layer)[0],
        what=f"k* {it['cid']}") for it in items}

    cache = ROOT / "results" / "cache" / f"E033_scores_{tag}_s{args.steps}.json"   # tag now carries the layer
    done: dict = json.loads(cache.read_text()) if cache.exists() else {}
    for n, it in enumerate(items, 1):
        if it["cid"] in done:
            continue
        ctl = items[n % len(items)]
        pairs, tags = [], []
        for who, obj in (("self", it), ("control", ctl)):
            for pn, tmpl in PROBES.items():
                pairs.append((tmpl.format(obj["subject"]), obj["attrs"][pn]))
                tags.append(f"{who}|{pn}")
        ks, dv = kstar[it["cid"]], deltas[it["cid"]]
        ed = (args.layer, ks, float(ks @ ks), dv)
        base = retrying(lambda p=pairs: score_pairs(m, p), what=f"base {it['cid']}")
        edit = retrying(lambda p=pairs, e=ed: score_pairs(m, p, edit=e),
                        what=f"edit {it['cid']}")
        done[it["cid"]] = {"subject": it["subject"], "target": it["target"],
                           "base": dict(zip(tags, base)), "edit": dict(zip(tags, edit)),
                           "norm": float(dv.norm()), "kstar_norm": float(ks.norm())}
        cache.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(items):
            log.info("  scored %d/%d", n, len(items))

    report(list(done.values()), args.model, args.steps, log,
           relation=args.relation, matched=rel["matches_probe"], itype=rel["type"],
           layer=args.layer)


def report(rs, model, steps, log, relation="occupation", matched="occupation",
           itype="a profession", layer=LAYER) -> None:
    n = len(rs)
    log.info("")
    log.info("E-033 — a %s edit on %s (n=%d, layer %d, %d steps) — injected value is %s, "
             "so the type-matched probe is %s",
             relation.upper(), model, n, layer, steps, itype, matched)
    log.info("mean ‖dv‖ %.2f · ‖k*‖ %.2f", st.mean(r["norm"] for r in rs),
             st.mean(r["kstar_norm"] for r in rs))
    log.info("")
    log.info("%-14s%12s%12s%12s%14s", "probe", "baseline", "post-edit", "control",
             "type-matched?")
    post = {}
    for pn in PROBES:
        b = st.mean(r["base"][f"self|{pn}"] for r in rs)
        p = st.mean(r["edit"][f"self|{pn}"] for r in rs)
        c = st.mean(r["edit"][f"control|{pn}"] for r in rs)
        post[pn] = p
        log.info("%-14s%12.2f%12.2f%12.2f%14s", pn, b, p, c,
                 "YES" if pn == matched else "no")

    others = [p for k, p in post.items() if k != matched]
    margin = min(others) - post[matched]
    _o = sorted(others)
    gap = abs(_o[0] - _o[-1]) if len(_o) > 1 else 0.0
    log.info("")
    log.info("%s (the type-matched probe) sits %.2f nats below the nearer of the other "
             "two", matched, margin)
    log.info("spread among the two NON-matched probes: %.2f nats", gap)
    log.info("")
    log.info("the mirror, for comparison — [E-025], birthplace edit at 8B:")
    for k, v in BIRTHPLACE_8B.items():
        log.info("   %-13s %6.2f%s", k, v, "   <- type-matched then" if k == "citizenship"
                 else "")

    base_occ = st.mean(r["base"][f"self|{matched}"] for r in rs)
    headroom = abs(post["occupation"] - base_occ)
    log.info("")
    if margin >= MATCH_MARGIN and gap < FLOOR_BAND:
        log.info("VERDICT: CROSSOVER — the displaced probe follows the INJECTED VALUE'S "
                 "TYPE, not the edited relation. %s is %.2f below the others, and the "
                 "non-matched probes have converged to %.2f apart. [E-025]'s mechanism "
                 "holds for this relation.", matched, margin, gap)
    elif min(others) < post[matched]:
        log.warning("VERDICT: NO CROSSOVER — another probe (%.2f) is STILL more displaced "
                    "than %s (%.2f) even though the injected value is %s. The "
                    "displaced probe does NOT follow the injected type, and [E-025]'s "
                    "general reading is withdrawn.",
                    min(others), matched, post[matched], itype)
    elif gap >= FLOOR_BAND:
        log.warning("VERDICT: NO FLOOR — the two non-matched probes are %.2f apart, so "
                    "they have not converged and the two-effect account fails in a third "
                    "way. Needs its own ticket rather than a sentence here.", gap)
    elif headroom < MATCH_MARGIN:
        log.warning("VERDICT: UNINTERPRETABLE — occupation only moved %.2f nats from a "
                    "baseline of %.2f, so it had no room to clear the floor by %.2f. "
                    "Confound 2 fired; this is not a failed crossover.",
                    headroom, base_occ, MATCH_MARGIN)
    else:
        log.info("VERDICT: between the pre-stated bands (margin %.2f, gap %.2f). Report "
                 "the levels and claim neither.", margin, gap)

    out = (ROOT / "results" /
           f"E-033-crossover-{model.replace('/', '_')}-{relation}-L{layer}.json")
    out.write_text(json.dumps({"ticket": "E-033", "model": model, "layer": layer,
                               "steps": steps, "n": n, "relation": relation,
                               "type_matched_probe": matched, "injected_type": itype,
                               "post_edit": post, "margin": margin, "gap": gap,
                               "birthplace_reference_8b": BIRTHPLACE_8B,
                               "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
