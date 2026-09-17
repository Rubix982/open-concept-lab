"""E-014 · Scaled edit: WHERE does the probability go?

[E-013] n=12 found log-prob DROP is the wrong statistic — the real edit and the
same-subject control drop `inner_1`'s old answer comparably (8.50 vs 6.82 nats), but
only the real edit sends the mass to a city in the target country. Destination, not
magnitude, is the measurement.

Data hygiene, all of it forced by defects found while building this:
  * pool restricted to SETTLEMENTS plus every target country's capital — `P19` points
    at universities and football clubs, and a pool that cannot express the coherent
    answer scores a correct relocation as a failure ([E-011]'s mistake);
  * 6 chains dropped whose `inner_1` is a US state, a county or a region — "born in
    the city of Wisconsin" is malformed whatever the QID says;
  * capitals taken as CURRENT, not first-listed (P36 carries historical ones: Japan
    resolved to an 8th-century palace).

Resumable: deltas cache after every chunk.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from run_e013 import CONTROL_TMPL, nat, occupations, usable_chains  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=0, help="0 = all clean chains")
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=6)
    ap.add_argument("--stall-wait", type=float, default=600,
                    help="seconds to park when a whole chunk fails (NDIF outage)")
    ap.add_argument("--only-cached", action="store_true",
                    help="skip v* entirely; read out the chains already optimised. "
                         "O-004 licenses an EXISTENCE claim, never a rate, so a "
                         "smaller n costs nothing we are entitled to claim.")
    ap.add_argument("--max-stalls", type=int, default=12,
                    help="give up after this many chunk failures; cache is preserved")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    geo = json.loads((ROOT / "probes" / "geo.json").read_text())
    pt = json.loads((ROOT / "probes" / "place_types.json").read_text())
    snap = Snapshot.load()

    malformed = set(pt["not_settlement"])
    pool = sorted(set(pt["settlement"]) | set(geo["capital"].values()))
    city_country = {c: k for c, k in geo["city_country"].items() if c not in malformed}
    for ctry, cap in geo["capital"].items():
        city_country[cap] = ctry
    countries = sorted(geo["capital"])
    pool_occ = sorted({o for ch in chains
                       for o in occupations(snap, ch["inner_1"]["qid_subject"])})

    picked, specs = [], []
    for c in usable_chains(chains):
        if c["inner_1"]["answer"] in malformed:
            continue
        occs = occupations(snap, c["inner_1"]["qid_subject"])
        if not occs:
            continue
        true_c = c["outer"]["answer"]
        tgt_c = rng.choice([x for x in countries if x != true_c])
        placebo = rng.choice([x for x in countries if x not in (true_c, tgt_c)])
        tgt_o = rng.choice([x for x in pool_occ if x not in occs])
        cid = c["seed_case_id"]
        specs += [
            EditSpec(f"{cid}|real", c["outer"]["prompt"], c["outer"]["subject"],
                     nat(tgt_c), "real"),
            EditSpec(f"{cid}|ctl", CONTROL_TMPL.format(c["inner_1"]["subject"]),
                     c["inner_1"]["subject"], tgt_o, "control"),
        ]
        picked.append({**c, "true_country": true_c, "target_country": tgt_c,
                       "placebo_country": placebo, "target_occ": tgt_o})
        if args.n and len(picked) >= args.n:
            break

    log = setup("run_e014", config={
        "ticket": "E-014", "model": MODEL, "layer": LAYER, "seed": args.seed,
        "n_chains": len(picked), "city_pool": len(pool), "chunk": args.chunk,
        "dropped_malformed": sorted(malformed),
        "editor": "ROME as configured by EasyEdit (C = I)"})
    log.info("%d clean chains, %d cities in the pool", len(picked), len(pool))

    m = connect(MODEL)
    cache_path = ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt"
    deltas: dict[str, torch.Tensor] = torch.load(cache_path) if cache_path.exists() else {}
    log.info("delta cache: %d of %d already computed", len(deltas), len(specs))

    # CHUNK-level resilience, added after a 2h NDIF outage exhausted the per-step
    # retries and killed the process. Per-step backoff is right for a dropped socket,
    # but each attempt itself hangs for minutes before timing out, so 8 attempts
    # consumed two hours rather than the intended ~3 minutes. Deltas already cache per
    # chunk, so a failed chunk should park and retry — that rides out an outage of any
    # length at the cost of one chunk's work.
    if args.only_cached:
        done = {c["seed_case_id"] for c in picked
                if f"{c['seed_case_id']}|real" in deltas
                and f"{c['seed_case_id']}|ctl" in deltas}
        dropped = len(picked) - len(done)
        picked = [c for c in picked if c["seed_case_id"] in done]
        specs = [sp for sp in specs if sp.case_id in deltas]
        log.warning("--only-cached: reading out %d fully-optimised chains, "
                    "deferring %d. Existence claim only; n is NOT a rate.",
                    len(picked), dropped)

    todo = [] if args.only_cached else [sp for sp in specs if sp.case_id not in deltas]
    i, stalls = 0, 0
    while i < len(todo):
        grp = todo[i : i + args.chunk]
        log.info("v* %d-%d of %d remaining", i + 1, i + len(grp), len(todo))
        try:
            deltas.update(compute_v_batch(m, grp))
        except Exception as exc:  # noqa: BLE001 — already classified and retried below
            stalls += 1
            if stalls > args.max_stalls:
                log.error("chunk failed %d times; stopping with %d/%d cached. "
                          "Re-run to resume — nothing is lost.",
                          stalls, len(deltas), len(specs))
                raise
            log.warning("chunk failed (%s); parking %.0f min then retrying. "
                        "%d/%d cached so far.", type(exc).__name__,
                        args.stall_wait / 60, len(deltas), len(specs))
            time.sleep(args.stall_wait)
            continue
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(deltas, cache_path)
        i += args.chunk

    k_star = {sp.case_id: read_key_and_value(m, sp.prompt, sp.subject, LAYER)[0]
              for sp in specs}

    # Readout cache + parking, the same pattern the v* loop already has. This loop was
    # the one place without it, and it wedged for 37 minutes with zero traces before
    # being killed — 126 scoring traces are ~13 minutes of work but hours of exposure
    # to a degraded service, so partial progress must survive.
    read_path = ROOT / "results" / "cache" / f"E014_readout_L{LAYER}_s{args.seed}.json"
    done_rows: dict[str, dict] = (json.loads(read_path.read_text())
                                  if read_path.exists() else {})
    log.info("readout cache: %d chains already scored", len(done_rows))

    results = []
    for n, c in enumerate(picked, 1):
        if c["seed_case_id"] in done_rows:
            results.append(done_rows[c["seed_case_id"]])
            continue
        cid, p1 = c["seed_case_id"], c["inner_1"]["prompt"]
        row = {"case_id": cid, "entailment": c["entailment"], "was": c["inner_1"]["answer"],
               "true_country": c["true_country"], "target_country": c["target_country"],
               "placebo_country": c["placebo_country"], "target_occ": c["target_occ"],
               "top1": {}, "in_target": {}, "in_placebo": {}, "is_capital": {}}
        for attempt in range(args.max_stalls):
            try:
                for cond in ("base", "real", "ctl"):
                    ed = None if cond == "base" else (LAYER, k_star[f"{cid}|{cond}"],
                                                      deltas[f"{cid}|{cond}"])
                    sc = score_pairs(m, [(p1, city) for city in pool], edit=ed)
                    top = pool[max(range(len(pool)), key=lambda j: sc[j])]
                    row["top1"][cond] = top
                    row["in_target"][cond] = city_country.get(top) == c["target_country"]
                    row["in_placebo"][cond] = city_country.get(top) == c["placebo_country"]
                    row["is_capital"][cond] = geo["capital"].get(c["target_country"]) == top
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == args.max_stalls - 1:
                    log.error("chain %s failed %d times; stopping with %d scored. "
                              "Re-run to resume.", cid, attempt + 1, len(done_rows))
                    raise
                log.warning("readout for %s failed (%s); parking %.0f min. "
                            "%d chains scored so far.", cid, type(exc).__name__,
                            args.stall_wait / 60, len(done_rows))
                time.sleep(args.stall_wait)
        results.append(row)
        done_rows[cid] = row
        read_path.parent.mkdir(parents=True, exist_ok=True)
        read_path.write_text(json.dumps(done_rows))
        log.info("%3d/%d %-6s %-14s -> real %-16s (%s) | ctl %-16s",
                 n, len(picked), cid, row["was"], row["top1"]["real"],
                 "IN TARGET" if row["in_target"]["real"] else city_country.get(row["top1"]["real"], "?"),
                 row["top1"]["ctl"])

    out = ROOT / "results" / f"E-014-destination-{MODEL.replace('/', '_')}.json"
    out.write_text(json.dumps({"ticket": "E-014", "model": MODEL, "layer": LAYER,
                               "seed": args.seed, "pool": pool,
                               "editor": "ROME as configured by EasyEdit (C = I)",
                               "results": results}, indent=1))

    log.info("")
    log.info("%-26s%10s%10s%10s", "lands in ...", "base", "real", "ctl")
    for label, key in (("TARGET country", "in_target"), ("placebo country", "in_placebo")):
        log.info("%-26s%9.0f%%%9.0f%%%9.0f%%", label,
                 *[100 * sum(r[key][c] for r in results) / len(results)
                   for c in ("base", "real", "ctl")])
    log.info("%-26s%9s %9.0f%%", "of those, the capital", "",
             100 * sum(r["is_capital"]["real"] for r in results)
             / max(1, sum(r["in_target"]["real"] for r in results)))
    by = defaultdict(list)
    for r in results:
        by[r["target_country"]].append(r["in_target"]["real"])
    log.info("")
    log.info("by target country (real edit), countries with n>=2:")
    for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 2:
            log.info("   %-28s %2d/%-2d = %3.0f%%", k, sum(v), len(v), 100 * sum(v) / len(v))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
