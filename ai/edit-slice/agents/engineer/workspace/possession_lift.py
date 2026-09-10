"""E-005: possession as LIFT over the model's subject-free prior.

RCA on E-003/E-004: ranking a true answer against randomly-sampled type-matched
distractors cannot separate stored knowledge from surface plausibility. "Darrieux"
looks French; "Yakuza" looks Japanese. Type-matching is not cue-matching, and no
control condition was run.

The fix is a paired design. For each item, the SAME ~50 candidates are scored
twice:

    with subject     "The mother tongue of Danielle Darrieux is"
    subject-free     "The mother tongue of X is"

`rank_prior` is what the template and base rates alone deliver. `rank_subject` is
what the entity adds. Possession requires the true answer to rank first AND to
have moved up because the subject was present — a model that scores from the
template's base rate gets no credit, because it scores identically in both arms.

Reported:
  rank_subject  rank of the true answer with the real subject
  rank_prior    rank of the same answer with the subject replaced by "X"
  lift          rank_prior - rank_subject (positive = the entity helped)
  possessed     rank_subject == 1 AND lift > 0

50 candidates rather than 10, so top-3 no longer saturates [E-004].

Honest limit, stated in the findings too: this separates "the model used the
subject" from "the model used the template". It does NOT fully separate memorised
fact from inference off the subject's morphology — a French-looking name genuinely
does carry information. That is a weaker claim than "the model knows the fact", and
must not be reported as the stronger one.
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
N_CANDIDATES: Final[int] = 50
PLACEHOLDER: Final[str] = "X"
#: Items packed into a single remote trace. Each item contributes 2 arms x 50
#: candidates = 100 short sequences, so 4 items is a ~400-sequence batch. NDIF
#: compute is sub-second; the ~10s per trace is queue and transfer, so round trips
#: are the budget and packing them is a near-linear speedup.
ITEMS_PER_CALL: Final[int] = 4
CACHE_DIR: Final[Path] = Path(__file__).parent / "lift"


def build_items(per_rel: int) -> list[dict[str, Any]]:
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
            rw = rec.rewrite
            others = [o for o in pool if o != rw.target_true]
            cands = [rw.target_true, *rng.sample(others, min(N_CANDIDATES - 1, len(others)))]
            items.append({
                "case_id": rec.case_id, "relation": rel, "true": rw.target_true,
                "subject": rw.subject,
                "prompt": rw.prompt.format(rw.subject),
                "prompt_prior": rw.prompt.format(PLACEHOLDER),
                "candidates": cands,
            })
    return items


def _rank(scores: list[float], candidates: list[str], true: str) -> int:
    order = [c for c, _ in sorted(zip(candidates, scores), key=lambda kv: -kv[1])]
    return order.index(true) + 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="EleutherAI/gpt-j-6b")
    ap.add_argument("--per-relation", type=int, default=15)
    args = ap.parse_args()

    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / f"{args.model.replace('/', '_')}.json"
    cache: dict[str, Any] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    items = build_items(args.per_relation)
    print(f"{len(items)} items x {N_CANDIDATES} candidates x 2 arms "
          f"| model={args.model}\n", flush=True)

    from remote import connect, score_pairs  # noqa: E402
    model = connect(args.model)

    todo = [it for it in items if f"{args.model}|{it['case_id']}" not in cache]
    print(f"  {len(items) - len(todo)} cached, {len(todo)} to do "
          f"({-(-len(todo) // ITEMS_PER_CALL)} remote calls)\n", flush=True)

    for start in range(0, len(todo), ITEMS_PER_CALL):
        chunk = todo[start : start + ITEMS_PER_CALL]
        pairs: list[tuple[str, str]] = []
        for it in chunk:                      # both arms of every item, one trace
            pairs += [(it["prompt"], c) for c in it["candidates"]]
            pairs += [(it["prompt_prior"], c) for c in it["candidates"]]
        scores = score_pairs(model, pairs)

        off = 0
        for it in chunk:
            k = len(it["candidates"])
            rs = _rank(scores[off : off + k], it["candidates"], it["true"])
            rp = _rank(scores[off + k : off + 2 * k], it["candidates"], it["true"])
            off += 2 * k
            cache[f"{args.model}|{it['case_id']}"] = {
                "model": args.model, "case_id": it["case_id"],
                "relation": it["relation"], "true": it["true"],
                "rank_subject": rs, "rank_prior": rp, "lift": rp - rs, "n": k}
        cache_path.write_text(json.dumps(cache))
        print(f"  {min(start + ITEMS_PER_CALL, len(todo))}/{len(todo)}", flush=True)

    rows = [v for v in cache.values() if v["model"] == args.model]
    poss = [r for r in rows if r["rank_subject"] == 1 and r["lift"] > 0]
    top1_naive = [r for r in rows if r["rank_subject"] == 1]
    print(f"\n{args.model}  n={len(rows)}  ({N_CANDIDATES} candidates)")
    print(f"  rank_subject == 1 (naive top-1)        {len(top1_naive)/len(rows):>5.0%}")
    print(f"  rank_prior   == 1 (template alone)     "
          f"{sum(r['rank_prior']==1 for r in rows)/len(rows):>5.0%}")
    print(f"  POSSESSED (top-1 AND lift > 0)         {len(poss)/len(rows):>5.0%}")
    print(f"  median rank_subject {statistics.median(r['rank_subject'] for r in rows):>4.0f}"
          f"   median rank_prior {statistics.median(r['rank_prior'] for r in rows):>4.0f}"
          f"   median lift {statistics.median(r['lift'] for r in rows):>+5.0f}")

    print("\nby relation:  naive-top1 / prior-top1 / possessed")
    for rel in sorted({r["relation"] for r in rows}):
        rs = [r for r in rows if r["relation"] == rel]
        n = len(rs)
        print(f"  {rel:<7}{MODALITY[rel].name[:24]:<26}"
              f"{sum(r['rank_subject']==1 for r in rs)/n:>7.0%}"
              f"{sum(r['rank_prior']==1 for r in rs)/n:>10.0%}"
              f"{sum(r['rank_subject']==1 and r['lift']>0 for r in rs)/n:>11.0%}")


if __name__ == "__main__":
    main()
