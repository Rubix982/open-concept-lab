"""E-003 step 1: head possession across model sizes.

Does the model hold the fact we intend to edit? For each sampled CounterFact edit,
teacher-force `target_true` against `target_new` and compare summed log-probs. The
standard pre-edit condition is P(target_true) > P(target_new); an edit applied to a
fact the model does not hold is meaningless, and any orphan measured against it is
an artifact [T-039].

Rigid relations are the pilot's pool; mutable ones are carried as a reference
column so possession can be read against relation modality rather than in a vacuum.

Results cached per (model, case_id) so reruns are free.
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
from probing import load, possesses  # noqa: E402

from relation_inventory import MODALITY  # noqa: E402

SEED: Final[int] = 1538
CACHE: Final[Path] = Path(__file__).parent / "possession.json"


def sample(records: list[CounterFactRecord], per_rel: int) -> list[CounterFactRecord]:
    rng = random.Random(SEED)
    by_rel: dict[str, list[CounterFactRecord]] = defaultdict(list)
    for r in records:
        by_rel[r.rewrite.relation_id].append(r)
    out: list[CounterFactRecord] = []
    for rel in sorted(by_rel):
        if MODALITY[rel].modality == "ambiguous":
            continue
        out += rng.sample(by_rel[rel], min(per_rel, len(by_rel[rel])))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", default=["gpt2-medium", "gpt2-large"])
    ap.add_argument("--per-relation", type=int, default=15)
    args = ap.parse_args()

    cache: dict[str, Any] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    recs = sample(load_counterfact(), args.per_relation)
    print(f"{len(recs)} edits, {args.per_relation}/relation, seed {SEED}\n")

    for name in args.models:
        model, tok = load(name)
        for i, rec in enumerate(recs):
            key = f"{name}|{rec.case_id}"
            if key in cache:
                continue
            rw = rec.rewrite
            p = possesses(model, tok, rw.prompt.format(rw.subject), rw.target_true, rw.target_new)
            cache[key] = {
                "model": name, "case_id": rec.case_id, "relation": rw.relation_id,
                "modality": MODALITY[rw.relation_id].modality,
                "margin": p.margin, "holds": p.holds, "top1": p.top1,
                "lp_true": p.true.logprob_sum, "lp_false": p.false.logprob_sum,
            }
            if i % 40 == 0:
                CACHE.write_text(json.dumps(cache))
        CACHE.write_text(json.dumps(cache))

    rows = [v for v in cache.values() if v["model"] in args.models]
    print(f"{'model':<14}{'modality':<11}{'n':>5}{'holds':>8}{'median margin':>15}")
    for name in args.models:
        for mod in ("rigid", "mutable"):
            rs = [r for r in rows if r["model"] == name and r["modality"] == mod]
            if not rs:
                continue
            held = sum(r["holds"] for r in rs)
            med = statistics.median(r["margin"] for r in rs)
            print(f"{name:<14}{mod:<11}{len(rs):>5}{held/len(rs):>7.0%}{med:>15.2f}")

    print(f"\nper rigid relation ({' vs '.join(args.models)}):")
    rigid = sorted({r["relation"] for r in rows if r["modality"] == "rigid"})
    for rel in rigid:
        cells = []
        for name in args.models:
            rs = [r for r in rows if r["model"] == name and r["relation"] == rel]
            cells.append(f"{sum(x['holds'] for x in rs)/len(rs):>5.0%}" if rs else "    -")
        print(f"  {rel:<7}{MODALITY[rel].name[:26]:<28}{''.join(cells)}")


if __name__ == "__main__":
    main()
