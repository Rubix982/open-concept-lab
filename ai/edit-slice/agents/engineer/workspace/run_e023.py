"""E-023 · What does ranking a closed pool hide? [T-066]

Every number in this project comes from ranking a type-matched pool. [E-014]'s headline —
an edit relocates the birth city into the target country 67% of the time — was measured
that way over 75 cities. If the edited model left to itself generates something outside
the pool, part of that 67% is the pool forcing a choice.

Greedy-decodes four tokens, baseline and under the real edit, and compares to the ranked
answer. `.all()` is unavailable in this nnsight build, so the edit is applied per decoding
step in its own trace.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
N_TOK = 4


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    geo = json.loads((ROOT / "probes" / "geo.json").read_text())
    pt = json.loads((ROOT / "probes" / "place_types.json").read_text())
    pool = e14["pool"]
    cc = {c: k for c, k in geo["city_country"].items()
          if c not in set(pt["not_settlement"])}
    for ctry, cap in geo["capital"].items():
        cc[cap] = ctry
    # longest first, so "New Delhi" is not matched as "New"
    pool_sorted = sorted(pool, key=len, reverse=True)

    deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt")
    kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{args.seed}.pt")
    rows = [r for r in e14["results"] if f"{r['case_id']}|real" in deltas][: args.n]

    log = setup("run_e023", config={
        "ticket": "E-023", "thread": "T-066", "model": MODEL, "layer": LAYER,
        "n_chains": len(rows), "n_tokens": N_TOK, "pool": len(pool),
        "note": "greedy decode vs ranked answer; edit applied per decoding step"})
    log.info("%d chains, greedy %d tokens, baseline and edited", len(rows), N_TOK)

    m = connect(MODEL)
    tok = m.tokenizer
    cache = ROOT / "results" / "cache" / f"E023_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache.read_text()) if cache.exists() else {}

    for n, r in enumerate(rows, 1):
        cid = r["case_id"]
        if cid in done:
            continue
        p1 = chains[cid]["inner_1"]["prompt"]
        ks_cpu = kstars[f"{cid}|real"]
        dv_cpu = deltas[f"{cid}|real"]
        den = float(ks_cpu @ ks_cpu)

        gens = {}
        for cond in ("base", "real"):
            ids = list(tok(p1).input_ids)
            for _ in range(N_TOK):
                batch = torch.tensor([ids])

                def step():
                    if cond == "base":
                        with _quiet_stdout(), m.trace(batch, remote=True):
                            nxt = m.lm_head.output[0, -1].argmax(-1).save()
                    else:
                        with _quiet_stdout(), m.trace(batch, remote=True):
                            dp = m.model.layers[LAYER].mlp.down_proj
                            kk = dp.input
                            uu = ks_cpu.to(kk.device, kk.dtype)
                            dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                                    * dv_cpu.to(kk.device, kk.dtype)
                            nxt = m.lm_head.output[0, -1].argmax(-1).save()
                    with _quiet_stdout():
                        return int(nxt)

                for attempt in range(args.max_stalls):
                    try:
                        ids.append(retrying(step, what=f"{cid} {cond}"))
                        break
                    except Exception as exc:  # noqa: BLE001
                        if attempt == args.max_stalls - 1:
                            raise
                        log.warning("%s %s failed (%s); parking %.0f min", cid, cond,
                                    type(exc).__name__, args.stall_wait / 60)
                        time.sleep(args.stall_wait)
            gens[cond] = tok.decode(ids[-N_TOK:])

        def match(text: str) -> str | None:
            t = text.strip()
            for city in pool_sorted:
                if t.startswith(city):
                    return city
            return None

        rec = {"case_id": cid, "prompt": p1, "target": r["target_country"],
               "was": r["was"], "gen": gens,
               "gen_city": {c: match(g) for c, g in gens.items()},
               "ranked": {"base": r["top1"]["base"], "real": r["top1"]["real"]}}
        rec["in_pool"] = {c: rec["gen_city"][c] is not None for c in gens}
        rec["agrees"] = {c: rec["gen_city"][c] == rec["ranked"][c] for c in gens}
        rec["gen_in_target"] = cc.get(rec["gen_city"]["real"] or "") == r["target_country"]
        done[cid] = rec
        cache.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(rows):
            log.info("  %d/%d", n, len(rows))

    rs = list(done.values())
    N = len(rs)
    log.info("")
    log.info("%-26s%12s%12s", "", "baseline", "edited")
    log.info("%-26s%11.0f%%%11.0f%%", "generation starts with a pool city",
             100 * sum(r["in_pool"]["base"] for r in rs) / N,
             100 * sum(r["in_pool"]["real"] for r in rs) / N)
    log.info("%-26s%11.0f%%%11.0f%%", "generation == ranked answer",
             100 * sum(r["agrees"]["base"] for r in rs) / N,
             100 * sum(r["agrees"]["real"] for r in rs) / N)
    log.info("")
    ranked_hit = sum(1 for r in rs if cc.get(r["ranked"]["real"], "") == r["target"])
    log.info("lands in the TARGET country — ranked %.0f%%  vs  generated %.0f%%  (n=%d)",
             100 * ranked_hit / N, 100 * sum(r["gen_in_target"] for r in rs) / N, N)
    log.info("")
    log.info("out-of-pool generations under the edit, verbatim:")
    shown = 0
    for r in rs:
        if not r["in_pool"]["real"] and shown < 10:
            log.info("   %-6s target %-16s -> %r", r["case_id"], r["target"],
                     r["gen"]["real"])
            shown += 1
    if not shown:
        log.info("   none — every edited generation began with a pool city")

    out = ROOT / "results" / "E-023-generation.json"
    out.write_text(json.dumps({"ticket": "E-023", "n_tokens": N_TOK,
                               "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
