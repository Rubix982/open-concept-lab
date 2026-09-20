"""E-024 · Does a birthplace edit disturb attributes that have nothing to do with birth?

[E-021] showed the update reaches any prompt beginning with the edited subject. If that is
what an edit does, the unit it operates on is the SUBJECT and the relation `v*` targeted is
incidental.

Two probes per subject, chosen for a relatedness gradient — occupation is unrelated to a
birthplace edit, citizenship is plausibly inferable from it — plus the same two probes on a
different, unedited subject as control.

Measure is teacher-forced log P(true answer), same probe with and without the edit,
differenced. No candidate pool: [E-023] showed ranking a closed pool undercounts badly and
that only paired contrasts survive it.
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
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
PROBES = {
    "occupation":  ("P106", "By profession, {} is a"),
    "citizenship": ("P27",  "{} is a citizen of"),
}


def first_label(snap, qid, pid):
    for v in snap.claims.get(qid, {}).get(pid, []):
        try:
            vid = v["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        lab = snap.labels.get(vid)
        if lab and lab != vid:
            return lab
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    snap = Snapshot.load()
    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt")
    kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{args.seed}.pt")

    items = []
    for r in e14["results"]:
        cid = r["case_id"]
        if f"{cid}|real" not in deltas:
            continue
        c = chains[cid]
        q, subj = c["inner_1"]["qid_subject"], c["inner_1"]["subject"]
        attrs = {k: first_label(snap, q, pid) for k, (pid, _) in PROBES.items()}
        if all(attrs.values()):
            items.append({"cid": cid, "subject": subj, "attrs": attrs,
                          "target": r["target_country"]})

    log = setup("run_e024", config={
        "ticket": "E-024", "model": MODEL, "layer": LAYER, "n_subjects": len(items),
        "probes": {k: v[1] for k, v in PROBES.items()},
        "measure": "teacher-forced log P(true answer), paired, no candidate pool"})
    log.info("%d subjects with both attributes labelled", len(items))

    m = connect(MODEL)
    cache = ROOT / "results" / "cache" / f"E024_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache.read_text()) if cache.exists() else {}

    for n, it in enumerate(items, 1):
        cid = it["cid"]
        if cid in done:
            continue
        # the control is the next subject in the list, so it is matched on nothing but
        # being a person in the same corpus — a deliberately weak match, which makes a
        # null on the control stronger evidence
        ctl = items[(n) % len(items)]
        pairs, tags = [], []
        for who, obj in (("edited", it), ("control", ctl)):
            for pname, (_, tmpl) in PROBES.items():
                pairs.append((tmpl.format(obj["subject"]), obj["attrs"][pname]))
                tags.append(f"{who}|{pname}")

        ks_cpu, dv_cpu = kstars[f"{cid}|real"], deltas[f"{cid}|real"]
        den = float(ks_cpu @ ks_cpu)
        out = {}
        for cond, ed in (("base", None), ("edited", (LAYER, ks_cpu, den, dv_cpu))):
            for attempt in range(args.max_stalls):
                try:
                    sc = score_pairs(m, pairs, edit=ed)
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == args.max_stalls - 1:
                        raise
                    log.warning("%s %s failed (%s); parking %.0f min", cid, cond,
                                type(exc).__name__, args.stall_wait / 60)
                    time.sleep(args.stall_wait)
            out[cond] = dict(zip(tags, sc))
        done[cid] = {"case_id": cid, "subject": it["subject"], "control": ctl["subject"],
                     "target": it["target"], "attrs": it["attrs"], "scores": out}
        cache.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(items):
            log.info("  %d/%d", n, len(items))

    rs = list(done.values())
    N = len(rs)
    log.info("")
    log.info("drop in log P(true answer) after a BIRTHPLACE edit  (n=%d)", N)
    log.info("%-28s%12s%12s%12s", "probe", "baseline", "mean drop", "median")
    summary = {}
    for who in ("edited", "control"):
        for pname in PROBES:
            tag = f"{who}|{pname}"
            base = [r["scores"]["base"][tag] for r in rs]
            drop = [r["scores"]["base"][tag] - r["scores"]["edited"][tag] for r in rs]
            summary[tag] = {"baseline": st.mean(base), "mean_drop": st.mean(drop),
                            "median_drop": st.median(drop)}
            label = f"{'SAME subject' if who=='edited' else 'other subject'} · {pname}"
            log.info("%-28s%12.2f%12.2f%12.2f", label, st.mean(base), st.mean(drop),
                     st.median(drop))

    log.info("")
    for pname in PROBES:
        d = summary[f"edited|{pname}"]["mean_drop"] - summary[f"control|{pname}"]["mean_drop"]
        log.info("control-differenced drop, %-12s %+.2f nats", pname, d)
    occ = summary["edited|occupation"]["mean_drop"] - summary["control|occupation"]["mean_drop"]
    cit = summary["edited|citizenship"]["mean_drop"] - summary["control|citizenship"]["mean_drop"]
    log.info("")
    if occ < 0.5:
        log.info("DENY: an unrelated attribute of the edited subject is essentially "
                 "untouched — the update is relation-selective and the reframe collapses.")
    elif abs(cit - occ) < 0.5:
        log.info("CONFIRM: both attributes fall alike (%.2f vs %.2f). The editor reaches "
                 "the SUBJECT; the relation v* targeted is incidental.", occ, cit)
    else:
        log.info("GRADED: citizenship %.2f against occupation %.2f. Semantic relatedness "
                 "modulates an effect the arithmetic says should be uniform.", cit, occ)

    out = ROOT / "results" / "E-024-attributes.json"
    out.write_text(json.dumps({"ticket": "E-024", "probes": {k: v[1] for k, v in PROBES.items()},
                               "summary": summary, "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
