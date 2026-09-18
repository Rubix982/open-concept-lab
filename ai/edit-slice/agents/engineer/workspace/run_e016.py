"""E-016 · Re-run the [E-015] paired test with the WHITENED update.

[E-015] found a paired gap of +0.0 pp under `C = I`: a work-country edit relocates the
birthplace exactly as often as a birth-country edit, so the relocation carries no
inference. `C = I` is a blunt update ([E-013]: ~8 nat drops on unrelated same-subject
facts), so this asks whether a targeted one behaves differently.

**No new `v*` work.** The whitened update still produces exactly `v*` at `k*` — only the
coefficient at OTHER inputs changes — so every cached delta from [E-014]/[E-015] is
already correct. This re-runs the readout only.

Reports the gap at several λ, because [E-016]'s gate showed λ sets how aggressively the
update is steered and a single silently-chosen λ would be the [E-009b] mistake again.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import LAYER, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from run_e013 import nat  # noqa: E402
from run_e015 import WORK_TMPL  # noqa: E402
from whiten import Whitener  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
#: The gate's rule: smallest λ at which in-sample and held-out selectivity agree.
#: PRIMARY first, so a mid-run NDIF failure still leaves the headline number.
LAMBDAS = [7.2e-03, 7.2e-04, 7.2e-02]
PRIMARY = 7.2e-03


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    e15 = json.loads((ROOT / "results" /
                      f"E-015-relation-{MODEL.replace('/', '_')}.json").read_text())
    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    geo = json.loads((ROOT / "probes" / "geo.json").read_text())
    pt = json.loads((ROOT / "probes" / "place_types.json").read_text())
    pool = e14["pool"]
    city_country = {c: k for c, k in geo["city_country"].items()
                    if c not in set(pt["not_settlement"])}
    for ctry, cap in geo["capital"].items():
        city_country[cap] = ctry

    K = torch.load(ROOT / "results" / "cache" / "E016_keys_L5.pt").float()
    d14 = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt")
    d15 = torch.load(ROOT / "results" / "cache" / f"E015_deltas_L{LAYER}_s{args.seed}.pt")
    ks14 = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{args.seed}.pt")

    rows = [r for r in e15["results"]
            if f"{r['case_id']}|real" in d14 and f"{r['case_id']}|work" in d15]
    log = setup("run_e016", config={
        "ticket": "E-016", "model": MODEL, "layer": LAYER, "lambdas": LAMBDAS,
        "primary_lambda": PRIMARY, "n_chains": len(rows), "keys": tuple(K.shape),
        "corpus": "CounterFact prompts (NOT Wikipedia)",
        "editor": "ROME whitened, C = K^T K/N + lam I via Woodbury"})
    log.info("%d chains; reusing cached v* — the whitened update still yields exactly "
             "v* at k*, so only the coefficient changes", len(rows))

    m = connect(MODEL)

    # work-arm k* was never cached by E-015; cache it now.
    ksw_path = ROOT / "results" / "cache" / f"E016_kstar_work_L{LAYER}_s{args.seed}.pt"
    ksw: dict[str, torch.Tensor] = torch.load(ksw_path) if ksw_path.exists() else {}
    todo = [r for r in rows if r["case_id"] not in ksw]
    if todo:
        log.info("reading %d work-arm k* vectors", len(todo))
        for j, r in enumerate(todo, 1):
            subj = chains[r["case_id"]]["inner_1"]["subject"]
            ksw[r["case_id"]] = read_key_and_value(m, WORK_TMPL.format(subj), subj, LAYER)[0]
            if j % 10 == 0 or j == len(todo):
                torch.save(ksw, ksw_path)
                log.info("  k* work %d/%d", j, len(todo))

    cache_path = ROOT / "results" / "cache" / f"E016_readout_L{LAYER}_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    whit = {lam: Whitener(K, lam) for lam in LAMBDAS}

    for lam in LAMBDAS:
        W = whit[lam]
        for n, r in enumerate(rows, 1):
            cid = r["case_id"]
            key = f"{cid}|{lam}"
            if key in done:
                continue
            c = chains[cid]
            p1 = c["inner_1"]["prompt"]
            out = {}
            for arm, deltas, kstar in (("birth", d14, ks14[f"{cid}|real"]),
                                       ("work", d15, ksw[cid])):
                dv = deltas[f"{cid}|" + ("real" if arm == "birth" else "work")]
                u = W.apply(kstar.float())
                den = float(u @ kstar.float())
                for attempt in range(args.max_stalls):
                    try:
                        sc = score_pairs(m, [(p1, city) for city in pool],
                                         edit=(LAYER, u, den, dv))
                        break
                    except Exception as exc:  # noqa: BLE001
                        if attempt == args.max_stalls - 1:
                            raise
                        log.warning("%s %s lam=%.1e failed (%s); parking %.0f min",
                                    cid, arm, lam, type(exc).__name__, args.stall_wait / 60)
                        time.sleep(args.stall_wait)
                top = pool[max(range(len(pool)), key=lambda j: sc[j])]
                out[arm] = {"top1": top,
                            "in_target": city_country.get(top) == r["target_country"]}
            done[key] = {"case_id": cid, "lam": lam, "target": r["target_country"],
                         "was": r["was"], **out}
            cache_path.write_text(json.dumps(done))
            if n % 10 == 0 or n == len(rows):
                log.info("  lam=%.1e  %d/%d", lam, n, len(rows))

    log.info("")
    log.info("%-12s%10s%10s%12s%10s", "lambda", "birth", "work", "paired gap", "n")
    summary = {}
    for lam in LAMBDAS:
        rs = [v for v in done.values() if v["lam"] == lam]
        b = sum(v["birth"]["in_target"] for v in rs)
        w = sum(v["work"]["in_target"] for v in rs)
        summary[lam] = {"birth": b, "work": w, "n": len(rs)}
        log.info("%-12.1e%9d%10d%+10.1f pp%10d", lam, b, w,
                 100 * (b - w) / max(1, len(rs)), len(rs))
    log.info("")
    log.info("for reference, C = I ([E-015]): birth 28, work 28, gap +0.0 pp, n 42")

    out_path = ROOT / "results" / f"E-016-whitened-{MODEL.replace('/', '_')}.json"
    out_path.write_text(json.dumps({"ticket": "E-016", "model": MODEL, "layer": LAYER,
                                    "lambdas": LAMBDAS, "primary": PRIMARY,
                                    "summary": {str(k): v for k, v in summary.items()},
                                    "results": list(done.values())}, indent=1))
    log.info("written: %s", out_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
