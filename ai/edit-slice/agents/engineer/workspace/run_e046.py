"""E-046 · After an unrelated edit, what does the model say the attribute IS?

[E-024] and [E-033] scored only log P(*correct* answer). They record what the model gave
up, never what it believes instead — and §4.5's claim is about the answer's **type**, so
it has been tested by what the answer stopped being rather than by what it became.

The objection this answers: if the subject is now born in Chile, falling confidence in
"French citizen" could be coherent revision rather than damage. Revision and displacement
make different predictions about the *replacement*, so read the replacement.

Top-K at the first answer token, base and edited, same 37 subjects as [E-024]. No greedy
decode and no new optimisation — deltas and k* come from the [E-014] cache, so this is one
remote call per (subject, probe, condition).

Pools are built from the Wikidata snapshot already in the repo, never hand-listed: an
occupation is any P106 label seen across the chain subjects, a country any P27 label.
Hand-built sets license an existence claim only [O-004]; a derived pool does not have that
problem, but the n is still 37 and no rate about editing in general is claimed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
TOP_K = 8
PROBES = {
    "occupation":  ("P106", "By profession, {} is a"),
    "citizenship": ("P27",  "{} is a citizen of"),
}


def first_label(snap: Snapshot, qid: str, pid: str) -> str | None:
    for v in snap.claims.get(qid, {}).get(pid, []):
        try:
            vid = v["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        lab = snap.labels.get(vid)
        if lab and lab != vid:
            return lab
    return None


def all_labels(snap: Snapshot, qids: list[str], pid: str) -> set[str]:
    """Every label this property takes across the corpus — the pool, derived not written."""
    pool: set[str] = set()
    for q in qids:
        for v in snap.claims.get(q, {}).get(pid, []):
            try:
                vid = v["mainsnak"]["datavalue"]["value"]["id"]
            except (KeyError, TypeError):
                continue
            lab = snap.labels.get(vid)
            if lab and lab != vid:
                pool.add(lab.lower())
    return pool


def classify(token: str, occ_pool: set[str], ctry_pool: set[str]) -> str:
    """Which pool does this token open? Prefix match, because we read one token."""
    t = token.strip().lower()
    if not t:
        return "empty"
    in_occ = any(lab.startswith(t) for lab in occ_pool)
    in_ctry = any(lab.startswith(t) for lab in ctry_pool)
    if in_occ and not in_ctry:
        return "occupation"
    if in_ctry and not in_occ:
        return "country"
    if in_occ and in_ctry:
        return "both"
    return "neither"


def report(rs: list[dict], log, *, out: Path) -> dict:
    """Verdict bands. Separated from the run so the dry-run can exercise them."""
    n = len(rs)
    summary: dict = {"n": n, "by_probe": {}}
    for pname in PROBES:
        rows = [r for r in rs if r["probe"] == pname]
        if not rows:
            continue
        kept = sum(r["top1"]["base"] == r["top1"]["edited"] for r in rows)
        base_cls = Counter(r["cls"]["base"] for r in rows)
        edit_cls = Counter(r["cls"]["edited"] for r in rows)
        to_target = sum(r["edited_is_target_country"] for r in rows)
        summary["by_probe"][pname] = {
            "n": len(rows), "top1_unchanged": kept,
            "base_class": dict(base_cls), "edited_class": dict(edit_cls),
            "edited_top1_is_injected_country": to_target,
            "mean_p_top1_base": sum(r["p_top1"]["base"] for r in rows) / len(rows),
            "mean_p_top1_edited": sum(r["p_top1"]["edited"] for r in rows) / len(rows),
        }
        log.info("")
        log.info("%s  (n=%d)", pname.upper(), len(rows))
        log.info("  top-1 unchanged by the edit      %d/%d", kept, len(rows))
        log.info("  base    top-1 classes            %s", dict(base_cls))
        log.info("  edited  top-1 classes            %s", dict(edit_cls))
        log.info("  edited top-1 IS the injected country  %d/%d", to_target, len(rows))

    occ = summary["by_probe"].get("occupation", {})
    stay = occ.get("edited_class", {}).get("occupation", 0)
    nn = occ.get("n", 0) or 1
    log.info("")
    if occ.get("edited_top1_is_injected_country", 0) >= 0.25 * nn:
        log.info("CONFIRM (displacement): the occupation probe's top answer becomes the "
                 "injected COUNTRY in %d of %d. The replacement is type-mismatched, so "
                 "the fall is displacement and not coherent revision.",
                 occ.get("edited_top1_is_injected_country", 0), nn)
    elif occ.get("top1_unchanged", 0) >= 0.75 * nn:
        log.info("NULL (flattening): the top answer is unchanged in %d of %d while its "
                 "probability falls. The edit lowers confidence without redirecting it; "
                 "neither reading is supported.", occ.get("top1_unchanged", 0), nn)
    elif stay >= 0.75 * nn:
        log.info("DENY (coherent revision): the top answer stays inside the occupation "
                 "pool in %d of %d — a within-type reshuffle. Section 4.5 must narrow "
                 "from 'displaces' to 'suppresses'.", stay, nn)
    else:
        log.info("MIXED: %d/%d stay in the occupation pool, %d/%d become the injected "
                 "country, %d/%d unchanged. No band claims this; read the verbatim table.",
                 stay, nn, occ.get("edited_top1_is_injected_country", 0), nn,
                 occ.get("top1_unchanged", 0), nn)

    out.write_text(json.dumps({"ticket": "E-046", "model": MODEL, "layer": LAYER,
                               "top_k": TOP_K, "probes": {k: v[1] for k, v in PROBES.items()},
                               "summary": summary, "results": rs}, indent=1))
    log.info("written: %s", out)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    snap = Snapshot.load()
    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt")
    kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{args.seed}.pt")

    items, qids = [], []
    for r in e14["results"]:
        cid = r["case_id"]
        if f"{cid}|real" not in deltas:
            continue
        c = chains[cid]
        q, subj = c["inner_1"]["qid_subject"], c["inner_1"]["subject"]
        attrs = {k: first_label(snap, q, pid) for k, (pid, _) in PROBES.items()}
        if all(attrs.values()):
            items.append({"cid": cid, "subject": subj, "attrs": attrs, "qid": q,
                          "target": r["target_country"]})
            qids.append(q)

    # completeness, not existence: every item we intend to score must have both tensors
    want = {f"{it['cid']}|real" for it in items}
    missing = want - set(deltas) | want - set(kstars)
    if missing:
        raise SystemExit(f"cache incomplete: {len(missing)} of {len(want)} absent")

    occ_pool = all_labels(snap, qids, "P106")
    ctry_pool = all_labels(snap, qids, "P27")

    log = setup("run_e046", config={
        "ticket": "E-046", "model": MODEL, "layer": LAYER, "top_k": TOP_K,
        "n_subjects": len(items), "probes": {k: v[1] for k, v in PROBES.items()},
        "occupation_pool": len(occ_pool), "country_pool": len(ctry_pool),
        "measure": "top-K at the first answer token, base vs edited, paired"})
    log.info("%d subjects; pools: %d occupations, %d countries",
             len(items), len(occ_pool), len(ctry_pool))

    m = connect(MODEL)
    tok = m.tokenizer
    cache = ROOT / "results" / "cache" / f"E046_L{LAYER}_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache.read_text()) if cache.exists() else {}

    for n, it in enumerate(items, 1):
        ks_cpu, dv_cpu = kstars[f"{it['cid']}|real"], deltas[f"{it['cid']}|real"]
        den = float(ks_cpu @ ks_cpu)
        for pname, (_, tmpl) in PROBES.items():
            key = f"{it['cid']}|{pname}"
            if key in done:
                continue
            prompt = tmpl.format(it["subject"])
            batch = torch.tensor([list(tok(prompt).input_ids)])
            got = {}
            for cond in ("base", "edited"):
                def step(cond=cond):
                    with _quiet_stdout(), m.trace(batch, remote=True):
                        if cond == "edited":
                            dp = m.model.layers[LAYER].mlp.down_proj
                            kk = dp.input
                            uu = ks_cpu.to(kk.device, kk.dtype)
                            dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                                    * dv_cpu.to(kk.device, kk.dtype)
                        probs = m.lm_head.output[0, -1].softmax(-1)
                        tv = probs.topk(TOP_K).values.save()
                        ti = probs.topk(TOP_K).indices.save()
                    with _quiet_stdout():
                        return [float(x) for x in tv], [int(x) for x in ti]

                for attempt in range(args.max_stalls):
                    try:
                        vals, idx = retrying(step, what=f"{key} {cond}")
                        break
                    except Exception as exc:  # noqa: BLE001
                        if attempt == args.max_stalls - 1:
                            raise
                        log.warning("%s %s failed (%s); parking %.0f min", key, cond,
                                    type(exc).__name__, args.stall_wait / 60)
                        time.sleep(args.stall_wait)
                got[cond] = {"tokens": [tok.decode([i]) for i in idx], "probs": vals}

            rec = {
                "case_id": it["cid"], "subject": it["subject"], "probe": pname,
                "prompt": prompt, "true_answer": it["attrs"][pname],
                "injected_country": it["target"],
                "topk": got,
                "top1": {c: got[c]["tokens"][0] for c in got},
                "p_top1": {c: got[c]["probs"][0] for c in got},
                "cls": {c: classify(got[c]["tokens"][0], occ_pool, ctry_pool) for c in got},
            }
            rec["edited_is_target_country"] = bool(
                it["target"].lower().startswith(got["edited"]["tokens"][0].strip().lower())
                and got["edited"]["tokens"][0].strip())
            done[key] = rec
            cache.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(items):
            log.info("  %d/%d subjects", n, len(items))

    out = Path(args.out) if args.out else ROOT / "results" / "E-046-what-instead.json"
    report(list(done.values()), log, out=out)


if __name__ == "__main__":
    main()
