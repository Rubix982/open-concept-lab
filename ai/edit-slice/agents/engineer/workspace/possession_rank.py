"""E-003 step 1b: possession by constrained rank, paired across model scale.

Same sampled items and the same fixed distractor sets for every model, so
differences are attributable to the model rather than to the draw. Distractors are
other `target_true` values ATTESTED FOR THE SAME RELATION, which makes them
type-matched by construction: when the relation wants a place, every candidate is
a place, so CounterFact's ambiguous templates ("died at" -> "the age of 90") cannot
express themselves.

Local models are scored through src/probing; Llama-70B through src/remote (NDIF),
one remote call per item.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import CounterFactRecord, load_counterfact  # noqa: E402

from relation_inventory import MODALITY  # noqa: E402

SEED: Final[int] = 1538
N_DISTRACTORS: Final[int] = 9
CACHE: Final[Path] = Path(__file__).parent / "possession_rank.json"


def build_items(per_rel: int) -> list[dict[str, Any]]:
    """Sampled rigid-relation edits with a fixed, type-matched distractor set each."""
    records = load_counterfact()
    rng = random.Random(SEED)
    by_rel: dict[str, list[CounterFactRecord]] = defaultdict(list)
    for r in records:
        by_rel[r.rewrite.relation_id].append(r)

    items: list[dict[str, Any]] = []
    for rel in sorted(by_rel):
        if MODALITY[rel].modality != "rigid":
            continue
        pool = sorted({r.rewrite.target_true for r in by_rel[rel]})
        for rec in rng.sample(by_rel[rel], min(per_rel, len(by_rel[rel]))):
            others = [o for o in pool if o != rec.rewrite.target_true]
            items.append({
                "case_id": rec.case_id, "relation": rel,
                "prompt": rec.rewrite.prompt.format(rec.rewrite.subject),
                "true": rec.rewrite.target_true,
                "distractors": rng.sample(others, min(N_DISTRACTORS, len(others))),
            })
    return items


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-relation", type=int, default=15)
    ap.add_argument("--local", nargs="*", default=["gpt2-medium", "gpt2-large"])
    ap.add_argument("--remote", default="meta-llama/Llama-3.1-70B")
    ap.add_argument("--skip-remote", action="store_true")
    args = ap.parse_args()

    cache: dict[str, Any] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    items = build_items(args.per_relation)
    print(f"{len(items)} rigid-relation items, {N_DISTRACTORS + 1} candidates each, seed {SEED}\n", flush=True)

    def record(model: str, it: dict, rank: int, n: int, best: str) -> None:
        cache[f"{model}|{it['case_id']}"] = {
            "model": model, "case_id": it["case_id"], "relation": it["relation"],
            "true": it["true"], "rank": rank, "n": n, "best": best,
        }

    for name in args.local:
        from probing import load, rank_among  # noqa: E402
        model, tok = load(name)
        for i, it in enumerate(items):
            if f"{name}|{it['case_id']}" in cache:
                continue
            r = rank_among(model, tok, it["prompt"], it["true"], it["distractors"])
            record(name, it, r.true_rank, r.n_candidates, r.best)
            if i % 25 == 0:
                CACHE.write_text(json.dumps(cache))
        CACHE.write_text(json.dumps(cache))
        print(f"local done: {name}", flush=True)

    if not args.skip_remote:
        from remote import connect, rank_among as remote_rank  # noqa: E402
        model = connect(args.remote)
        for i, it in enumerate(items):
            if f"{args.remote}|{it['case_id']}" in cache:
                continue
            rank, n, best = remote_rank(model, it["prompt"], it["true"], it["distractors"])
            record(args.remote, it, rank, n, best)
            CACHE.write_text(json.dumps(cache))
            if i % 10 == 0:
                print(f"  remote {i}/{len(items)}", flush=True)
        print(f"remote done: {args.remote}", flush=True)

    rows = list(cache.values())
    models = [*args.local] + ([] if args.skip_remote else [args.remote])
    print(f"\n{'model':<28}{'n':>5}{'top1':>8}{'top-3':>8}{'median rank':>13}")
    for m in models:
        rs = [r for r in rows if r["model"] == m]
        if not rs:
            continue
        print(f"{m:<28}{len(rs):>5}{sum(r['rank']==1 for r in rs)/len(rs):>7.0%}"
              f"{sum(r['rank']<=3 for r in rs)/len(rs):>8.0%}"
              f"{statistics.median(r['rank'] for r in rs):>13.1f}")

    print("\ntop-1 by relation:")
    for rel in sorted({r["relation"] for r in rows}):
        cells = []
        for m in models:
            rs = [r for r in rows if r["model"] == m and r["relation"] == rel]
            cells.append(f"{sum(x['rank']==1 for x in rs)/len(rs):>8.0%}" if rs else "       -")
        print(f"  {rel:<7}{MODALITY[rel].name[:24]:<26}{''.join(cells)}")


if __name__ == "__main__":
    main()
