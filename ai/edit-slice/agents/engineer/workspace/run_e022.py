"""E-022 · Does a possession label belong to the fact, or to the (fact, template) pair?

Runs [T-062] and [T-064] from one measurement.

Declaration 1 of notes/definitions.md is binding — a fact is a behavioral unit defined by
its probe set — and every possession number here used a probe set of size one. This scores
60 facts under 8 templates and asks whether the [E-012] cell (HELD / PRIOR / MUTE /
ABSENT) is a property of the fact or of the pairing.

Templates are ParaRel's P19 patterns, not ours. Six of its thirteen place the answer
mid-sentence and cannot be scored by a continuation-based scorer; they are excluded on
that ground, decided before scoring. Our published form is the eighth.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from discrimination import discriminate  # noqa: E402
from logs import setup  # noqa: E402
from possession import Edit, FilterConfig, run  # noqa: E402
from remote import connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"

#: ParaRel P19, the seven patterns whose answer slot is sentence-final. The six excluded
#: are the "[X] was a [Y]-born person" family: prenominal [Y], unscoreable as a
#: continuation. Plus our own published form, so existing numbers have a referent here.
TEMPLATES = {
    "pararel_born_in":     "{} was born in",
    "pararel_orig_from":   "{} is originally from",
    "pararel_was_orig":    "{} was originally from",
    "pararel_native_to":   "{} is native to",
    "pararel_was_native":  "{} was native to",
    "pararel_originated":  "{} originated from",
    "pararel_originates":  "{} originates from",
    "ours_city_of":        "{} was born in the city of",
}


def cell(rank1: bool, auc) -> str:
    col = auc is not None and auc >= 0.8
    return ("HELD" if rank1 and col else "PRIOR" if rank1
            else "MUTE" if col else "ABSENT")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-facts", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    facts = [{"cid": c["seed_case_id"], "subject": c["inner_1"]["subject"],
              "answer": c["inner_1"]["answer"]} for c in chains][: args.n_facts]
    freq = Counter(f["answer"] for f in facts)

    log = setup("run_e022", config={
        "ticket": "E-022", "threads": ["T-062", "T-064"], "model": MODEL,
        "n_facts": len(facts), "templates": list(TEMPLATES),
        "excluded": "6 ParaRel P19 patterns with prenominal [Y], unscoreable as continuations",
        "seed": args.seed})
    log.info("%d facts x %d templates = %d cells", len(facts), len(TEMPLATES),
             len(facts) * len(TEMPLATES))

    m = connect(MODEL)
    cache = ROOT / "results" / "cache" / f"E022_s{args.seed}.json"
    done: dict[str, str] = json.loads(cache.read_text()) if cache.exists() else {}
    aucs: dict[str, float] = {}

    for tname, tmpl in TEMPLATES.items():
        if all(f"{f['cid']}|{tname}" in done for f in facts):
            log.info("%s: cached", tname)
            continue
        edits = [Edit(case_id=f"{f['cid']}|{tname}", prompt=tmpl.format(f["subject"]),
                      subject=f["subject"], true_answer=f["answer"],
                      relation_id=tname) for f in facts]
        cfg = FilterConfig(model=MODEL, n_candidates=50, seed=args.seed)
        tcache = ROOT / "results" / "cache" / f"E022_{tname}_{cfg.fingerprint.replace('|','_')}.json"
        for attempt in range(args.max_stalls):
            try:
                rep = run(edits, cfg, lambda p: score_pairs(m, p), cache_path=tcache,
                          reference=edits,
                          progress=lambda i, n: log.info("  %s %d/%d", tname, i, n)
                          if i % 20 == 0 else None)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == args.max_stalls - 1:
                    raise
                log.warning("%s failed (%s); parking %.0f min", tname,
                            type(exc).__name__, args.stall_wait / 60)
                time.sleep(args.stall_wait)
        by_id = {d.case_id: d for d in discriminate(rep.results)}
        for r in rep.results:
            d = by_id.get(r.case_id)
            done[r.case_id] = cell(r.rank_subject == 1, d.auc if d else None)
            if d and d.auc is not None:
                aucs[r.case_id] = d.auc
        cache.write_text(json.dumps(done))
        log.info("%s done", tname)

    # ---- T-062: is the label a property of the fact? -------------------------
    per_fact = defaultdict(list)
    for key, c in done.items():
        cid, tname = key.split("|")
        if tname in TEMPLATES:
            per_fact[cid].append(c)
    shares = []
    for cid, cells in per_fact.items():
        if len(cells) == len(TEMPLATES):
            shares.append(Counter(cells).most_common(1)[0][1] / len(cells))
    shares.sort()
    n = len(shares)
    log.info("")
    log.info("T-062 — modal-cell share per fact (1.0 = the label is a property of the fact,")
    log.info("        %.3f = chance over %d templates)", 1 / len(TEMPLATES), len(TEMPLATES))
    log.info("   facts with all %d cells : %d", len(TEMPLATES), n)
    if n:
        log.info("   mean %.3f   median %.3f   min %.3f   max %.3f",
                 sum(shares) / n, shares[n // 2], shares[0], shares[-1])
        for t in (1.0, 0.875, 0.75, 0.5):
            log.info("   share >= %.3f : %2d/%d = %3.0f%%", t,
                     sum(x >= t - 1e-9 for x in shares), n,
                     100 * sum(x >= t - 1e-9 for x in shares) / n)

    # ---- the confound: template difficulty ----------------------------------
    log.info("")
    log.info("per-template cell distribution (a template ABSENT for nearly everything is")
    log.info("a bad probe, not evidence about facts)")
    log.info("%-20s%8s%8s%8s%8s", "template", "HELD", "PRIOR", "MUTE", "ABSENT")
    for tname in TEMPLATES:
        cs = Counter(c for k, c in done.items() if k.endswith("|" + tname))
        tot = sum(cs.values()) or 1
        log.info("%-20s%7.0f%%%7.0f%%%7.0f%%%7.0f%%", tname,
                 100 * cs["HELD"] / tot, 100 * cs["PRIOR"] / tot,
                 100 * cs["MUTE"] / tot, 100 * cs["ABSENT"] / tot)

    # ---- T-064: MUTE ---------------------------------------------------------
    allc = Counter(c for k, c in done.items() if k.split("|")[1] in TEMPLATES)
    tot = sum(allc.values()) or 1
    log.info("")
    log.info("T-064 — cell rates over all %d cells: HELD %.0f%%  PRIOR %.0f%%  "
             "MUTE %.0f%%  ABSENT %.0f%%", tot,
             100 * allc["HELD"] / tot, 100 * allc["PRIOR"] / tot,
             100 * allc["MUTE"] / tot, 100 * allc["ABSENT"] / tot)
    byfreq = defaultdict(Counter)
    ans = {f["cid"]: f["answer"] for f in facts}
    for k, c in done.items():
        cid, tname = k.split("|")
        if tname in TEMPLATES and cid in ans:
            f = freq[ans[cid]]
            byfreq["common (>=3)" if f >= 3 else "rare (1-2)"][c] += 1
    log.info("   MUTE by answer frequency:")
    for k, cs in byfreq.items():
        t = sum(cs.values()) or 1
        log.info("     %-14s %3.0f%% of %d cells", k, 100 * cs["MUTE"] / t, t)

    out = ROOT / "results" / "E-022-cells.json"
    out.write_text(json.dumps({"ticket": "E-022", "templates": TEMPLATES,
                               "cells": done, "modal_shares": shares}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
