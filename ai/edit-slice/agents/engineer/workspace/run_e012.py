"""E-012 · Gate the chains under the paired-subject control and compare to the old one.

Re-scores at schema v2, which persists the candidate score vector `run` was already
computing and discarding. The column test then costs no remote calls.

    python agents/engineer/workspace/run_e012.py --model meta-llama/Llama-3.1-8B
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from discrimination import discriminate, held, summarise  # noqa: E402
from gate_chains import POSITIONS, chain_edits  # noqa: E402
from surface_forms import NATURAL  # noqa: E402
from logs import setup  # noqa: E402
from possession import FilterConfig, run  # noqa: E402
from remote import connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CHAINS = ROOT / "probes" / "containment_chains.json"


def freq_class(n: int) -> str:
    return "modal (>=10)" if n >= 10 else "mid (3-9)" if n >= 3 else "rare (1-2)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B")
    ap.add_argument("--n-candidates", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--min-auc", type=float, default=0.8)
    ap.add_argument("--natural", action="store_true",
                    help="render answers as a sentence would ([E-011] NATURAL map). "
                         "The row and control defects are orthogonal, so recovering "
                         "modal answers needs this AND the paired control.")
    args = ap.parse_args()

    chains = json.loads(CHAINS.read_text())["chains"]
    edits = chain_edits(chains)
    if args.natural:
        # Rendering is applied to EVERY answer, so the whole candidate pool moves
        # with it; renaming only the true answer would advantage it for a reason
        # unrelated to the question. Same rule as [E-011].
        edits = [replace(e, true_answer=NATURAL.get(e.true_answer, e.true_answer))
                 for e in edits]
    cfg = FilterConfig(model=args.model, n_candidates=args.n_candidates, seed=args.seed)

    log = setup("run_e012", config={
        "ticket": "E-012", "model": args.model, "n_candidates": args.n_candidates,
        "seed": args.seed, "min_auc": args.min_auc, "facts": len(edits),
        "rendering": "natural" if args.natural else "bare",
        "fingerprint": cfg.fingerprint})
    log.info("E-012: %d chains -> %d facts, schema %s", len(chains), len(edits),
             cfg.fingerprint.split("|")[0])

    model = connect(args.model)
    render_tag = "natural" if args.natural else "bare"
    # The fingerprint covers model/n/seed/placeholder — NOT the rendering. A shared
    # path would serve bare results to a natural run and fake a null result, which
    # is the collision this project has now shipped twice.
    cache = (ROOT / "results" / "cache" /
             f"E012_{render_tag}_{cfg.fingerprint.replace('|', '_')}.json")
    rep = run(edits, cfg, lambda p: score_pairs(model, p), cache_path=cache,
              reference=edits,
              progress=lambda i, n: log.info("scored %d/%d", i, n) if i % 25 == 0 else None)

    discs = discriminate(rep.results)
    by_id = {d.case_id: d for d in discs}
    truth = {e.case_id: e.true_answer for e in edits}

    for pos in POSITIONS:
        items = [it for it in rep.results if it.relation_id == pos]
        s = summarise(items, [by_id[it.case_id] for it in items], min_auc=args.min_auc)
        log.info("")
        log.info("%s — %d items, %d with a defined AUC (%.0f%% of items); "
                 "mean foil coverage %.0f%%",
                 pos, s["n_items"], s["n_measured"],
                 100 * s["item_coverage"], 100 * s["foil_coverage"])
        if not s["n_measured"]:
            log.warning("%s: no item had enough foils — not reporting a rate", pos)
            continue
        log.info("   row test (rank 1)      %.0f%%", 100 * s["row_pass_rate"])
        log.info("   mean column AUC        %.3f   (chance 0.500)", s["mean_auc"])
        log.info("   held (row AND AUC>=%.2f) %.0f%%", args.min_auc, 100 * s["held_rate"])

        # The split that exposed E-009b: is the new measure still frequency-biased?
        freq = Counter(truth[it.case_id] for it in items)
        buckets: dict[str, list] = defaultdict(list)
        for it in items:
            d = by_id[it.case_id]
            if d.auc is not None:
                buckets[freq_class(freq[truth[it.case_id]])].append((it, d))
        log.info("   %-14s%5s%9s%9s%9s", "answer class", "n", "row", "AUC", "held")
        for k in ("modal (>=10)", "mid (3-9)", "rare (1-2)"):
            b = buckets.get(k, [])
            if not b:
                continue
            log.info("   %-14s%5d%8.0f%%%9.3f%8.0f%%", k, len(b),
                     100 * sum(it.rank_subject == 1 for it, _ in b) / len(b),
                     sum(d.auc for _, d in b) / len(b),
                     100 * sum(bool(held(it, d, min_auc=args.min_auc))
                               for it, d in b) / len(b))

    # usable chains under old measure vs new
    old = {it.case_id: it.held(require_lift=cfg.require_lift) for it in rep.results}
    new = {it.case_id: held(it, by_id[it.case_id], min_auc=args.min_auc)
           for it in rep.results if it.case_id in by_id}
    def usable(flags: dict, strict: bool) -> tuple[int, int]:
        ok = unk = 0
        for c in chains:
            vals = [flags.get(f"{c['seed_case_id']}|{p}") for p in POSITIONS]
            if any(v is None for v in vals):
                unk += 1
            elif all(vals):
                ok += 1
        return ok, unk
    o, _ = usable(old, False)
    n, unk = usable(new, True)
    log.info("")
    log.info("usable chains — placeholder control : %d/%d", o, len(chains))
    log.info("usable chains — paired control      : %d/%d  (%d unmeasured)",
             n, len(chains), unk)

    out = (ROOT / "results" /
           f"E-012-discrimination-{render_tag}-{args.model.replace('/', '_')}.json")
    out.write_text(json.dumps({
        "ticket": "E-012", "config": cfg.as_dict(), "min_auc": args.min_auc,
        "rendering": render_tag,
        "per_item": [{"case_id": d.case_id, "position": d.relation_id,
                      "answer": d.true_answer, "auc": d.auc, "n_foils": d.n_foils,
                      "n_foils_possible": d.n_foils_possible,
                      "rank_subject": next(it.rank_subject for it in rep.results
                                           if it.case_id == d.case_id)}
                     for d in discs],
        "usable_old": o, "usable_new": n, "unmeasured": unk,
    }, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
