"""E-004: does the model hold the GROUNDS, not just the edited head?

E-003 measured head possession (GPT-J 73%). That is a ceiling for grounds, because
CounterFact's relations were curated as facts models know while grounds are
whatever Wikidata happens to assert about the subject.

The number that bounds the pilot is JOINT possession: head held AND at least one
ground held. Neither alone is sufficient — an edit on an unheld head is meaningless,
and an edit whose grounds are all unheld has nothing to orphan.

Same measure as E-003 (constrained rank against type-matched distractors) so the
head and ground numbers are directly comparable. Same model as the pilot would
edit: GPT-J-6B [E-003b].
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import load_counterfact  # noqa: E402
from ground_templates import TEMPLATES, WEAK  # noqa: E402
from wikidata import Snapshot, item_statements  # noqa: E402

sys.path.append(str(Path(__file__).parent))
from possession_rank import build_items  # noqa: E402

SEED: Final[int] = 1538
N_DISTRACTORS: Final[int] = 9
MAX_GROUNDS_PER_SUBJECT: Final[int] = 4  # bound remote calls; sampled, seeded
CACHE: Final[Path] = Path(__file__).parent / "ground_possession.json"


def build_ground_items() -> list[dict[str, Any]]:
    """One entry per (subject, ground property) pair we have a template for."""
    snap = Snapshot.load()
    by_case = {r.case_id: r for r in load_counterfact()}
    rng = random.Random(SEED)

    # value pool per property, for type-matched distractors
    pool: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = snap.labels
    for qid, claims in snap.claims.items():
        for pid, vals in item_statements(claims).items():
            if pid in TEMPLATES:
                pool[pid].update(labels.get(v, v) for v in vals)

    out: list[dict[str, Any]] = []
    for it in build_items(15):
        subj = by_case[it["case_id"]].rewrite.subject
        qid = snap.links.get(subj)
        if not qid:
            continue
        props = item_statements(snap.claims.get(qid, {}))
        usable = [p for p in props if p in TEMPLATES and p != it["relation"]]
        for pid in rng.sample(usable, min(MAX_GROUNDS_PER_SUBJECT, len(usable))):
            true = labels.get(props[pid][0], props[pid][0])
            if true.startswith("Q"):          # unlabelled entity, unusable as text
                continue
            others = sorted(pool[pid] - {true})
            if len(others) < 4:               # too few distractors to rank against
                continue
            out.append({
                "case_id": it["case_id"], "edited_relation": it["relation"],
                "ground_prop": pid, "subject": subj,
                "prompt": TEMPLATES[pid][1].format(subj), "true": true,
                "distractors": rng.sample(others, min(N_DISTRACTORS, len(others))),
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="EleutherAI/gpt-j-6b")
    args = ap.parse_args()

    cache: dict[str, Any] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    items = build_ground_items()
    print(f"{len(items)} (subject, ground) pairs over "
          f"{len({i['case_id'] for i in items})} subjects, "
          f"{len({i['ground_prop'] for i in items})} properties\n", flush=True)

    from remote import connect, rank_among  # noqa: E402
    model = connect(args.model)
    for i, it in enumerate(items):
        key = f"{args.model}|{it['case_id']}|{it['ground_prop']}"
        if key in cache:
            continue
        rank, n, best = rank_among(model, it["prompt"], it["true"], it["distractors"])
        cache[key] = {**{k: it[k] for k in
                         ("case_id", "edited_relation", "ground_prop", "subject", "true")},
                      "model": args.model, "rank": rank, "n": n, "best": best}
        CACHE.write_text(json.dumps(cache))
        if i % 20 == 0:
            print(f"  {i}/{len(items)}", flush=True)

    rows = [v for v in cache.values() if v["model"] == args.model]
    strong = [r for r in rows if r["ground_prop"] not in WEAK]
    print(f"\nGROUND possession, {args.model}")
    print(f"  all pairs        n={len(rows):<5} top-1 {sum(r['rank']==1 for r in rows)/len(rows):.0%}"
          f"  top-3 {sum(r['rank']<=3 for r in rows)/len(rows):.0%}")
    print(f"  excl. weak (P734/P735) n={len(strong):<5} top-1 "
          f"{sum(r['rank']==1 for r in strong)/len(strong):.0%}"
          f"  top-3 {sum(r['rank']<=3 for r in strong)/len(strong):.0%}")

    print("\nby ground property (>=5 pairs):")
    by_prop: dict[str, list] = defaultdict(list)
    for r in rows:
        by_prop[r["ground_prop"]].append(r)
    for pid, rs in sorted(by_prop.items(), key=lambda kv: -len(kv[1])):
        if len(rs) < 5:
            continue
        flag = " (weak)" if pid in WEAK else ""
        print(f"  {pid:<7}{TEMPLATES[pid][0][:26]:<28}n={len(rs):<4}"
              f"top-1 {sum(r['rank']==1 for r in rs)/len(rs):>4.0%}{flag}")

    # joint possession: head held AND >=1 ground held, same subject
    head = {int(k.split("|")[1]): v for k, v in
            json.loads((Path(__file__).parent / "possession_rank.json").read_text()).items()
            if v["model"] == args.model}
    by_case: dict[int, list] = defaultdict(list)
    for r in strong:
        by_case[r["case_id"]].append(r)
    both = [c for c in by_case if head.get(c, {}).get("rank") == 1
            and any(r["rank"] == 1 for r in by_case[c])]
    print(f"\nJOINT possession (head top-1 AND >=1 ground top-1): "
          f"{len(both)}/{len(by_case)} = {100*len(both)/len(by_case):.0f}%")


if __name__ == "__main__":
    main()
