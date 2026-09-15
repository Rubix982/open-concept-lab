"""E-015 · Inference or country-flavoured content? Hold subject and target, vary relation.

Resolves agents/shared/disputes.md [E-014]. Both arms push the SAME country-valued
vector through the SAME subject's key; only one licenses the inference:

    "X was born in the country of" -> Germany   licenses "born in a German city"
    "X works in the country of"    -> Germany   does not

If `inner_1` relocates into the target country as strongly under the work edit, the
relocation is country-content leaking into any same-subject probe and the "coherent
revision" reading dies. If materially weaker, something relation-specific survives.

Target countries are READ from E-014's output, never redrawn — unmatched arms would
destroy the pairing silently, and the reported quantity is the paired per-chain gap.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
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
WORK_TMPL = "{} works in the country of"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=6)
    args = ap.parse_args()

    src = ROOT / "results" / f"E-014-destination-{MODEL.replace('/', '_')}.json"
    if not src.exists():
        raise SystemExit(f"E-014 output not found at {src} — E-015 is blocked on it")
    e14 = json.loads(src.read_text())
    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    by_id = {c["seed_case_id"]: c for c in chains}
    geo = json.loads((ROOT / "probes" / "geo.json").read_text())
    pt = json.loads((ROOT / "probes" / "place_types.json").read_text())

    pool = e14["pool"]                      # the exact pool E-014 ranked over
    city_country = {c: k for c, k in geo["city_country"].items()
                    if c not in set(pt["not_settlement"])}
    for ctry, cap in geo["capital"].items():
        city_country[cap] = ctry

    specs, rows = [], []
    for r in e14["results"]:
        c = by_id[r["case_id"]]
        subj = c["inner_1"]["subject"]
        specs.append(EditSpec(f"{r['case_id']}|work", WORK_TMPL.format(subj), subj,
                              nat(r["target_country"]), "work"))
        rows.append(r)

    log = setup("run_e015", config={
        "ticket": "E-015", "model": MODEL, "layer": LAYER, "seed": args.seed,
        "n_chains": len(rows), "work_template": WORK_TMPL, "pool": len(pool),
        "targets_from": src.name, "editor": "ROME as configured by EasyEdit (C = I)"})
    log.info("%d chains, targets matched from E-014", len(rows))

    m = connect(MODEL)
    cache = ROOT / "results" / "cache" / f"E015_deltas_L{LAYER}_s{args.seed}.pt"
    deltas: dict[str, torch.Tensor] = torch.load(cache) if cache.exists() else {}
    log.info("delta cache: %d of %d", len(deltas), len(specs))

    todo = [sp for sp in specs if sp.case_id not in deltas]
    for i in range(0, len(todo), args.chunk):
        grp = todo[i : i + args.chunk]
        log.info("v* %d-%d of %d remaining", i + 1, i + len(grp), len(todo))
        deltas.update(compute_v_batch(m, grp))
        cache.parent.mkdir(parents=True, exist_ok=True)
        torch.save(deltas, cache)

    out_rows = []
    for n, r in enumerate(rows, 1):
        cid = r["case_id"]
        c = by_id[cid]
        sp_id = f"{cid}|work"
        k_star, _ = read_key_and_value(m, WORK_TMPL.format(c["inner_1"]["subject"]),
                                       c["inner_1"]["subject"], LAYER)
        sc = score_pairs(m, [(c["inner_1"]["prompt"], city) for city in pool],
                         edit=(LAYER, k_star, deltas[sp_id]))
        top = pool[max(range(len(pool)), key=lambda j: sc[j])]
        in_target = city_country.get(top) == r["target_country"]
        out_rows.append({**r, "top1_work": top, "in_target_work": in_target})
        log.info("%3d/%d %-6s target %-16s birth->%-14s (%s)  work->%-14s (%s)",
                 n, len(rows), cid, r["target_country"], r["top1"]["real"],
                 "HIT" if r["in_target"]["real"] else "miss", top,
                 "HIT" if in_target else "miss")

    birth = [r["in_target"]["real"] for r in out_rows]
    work = [r["in_target_work"] for r in out_rows]
    gap = [b - w for b, w in zip(birth, work)]
    out = ROOT / "results" / f"E-015-relation-{MODEL.replace('/', '_')}.json"
    out.write_text(json.dumps({"ticket": "E-015", "model": MODEL, "layer": LAYER,
                               "work_template": WORK_TMPL, "results": out_rows}, indent=1))

    log.info("")
    log.info("lands in the TARGET country:")
    log.info("   birth-country edit (licenses the inference) : %2d/%d = %.0f%%",
             sum(birth), len(birth), 100 * sum(birth) / len(birth))
    log.info("   work-country edit  (does NOT)               : %2d/%d = %.0f%%",
             sum(work), len(work), 100 * sum(work) / len(work))
    log.info("   PAIRED gap (the quantity)                   : %+.0f pp  "
             "(birth-only %d, work-only %d, both %d, neither %d)",
             100 * st.mean(gap),
             sum(1 for b, w in zip(birth, work) if b and not w),
             sum(1 for b, w in zip(birth, work) if w and not b),
             sum(1 for b, w in zip(birth, work) if b and w),
             sum(1 for b, w in zip(birth, work) if not b and not w))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
