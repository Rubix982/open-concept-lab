"""E-002 step 1: does Wikidata carry enough about CounterFact subjects to ground them?

E-001 killed method (e) over DBpedia: 66.5% of usable mined rules were alias
tautologies (`fact + alias => fact`) because DBpedia stores many redundant naming
predicates. Wikidata stores labels as labels, not statements, so the pathology
should not recur. Before mining anything we check the cheaper precondition: are
subjects rich enough for grounds to exist at all?

Reads a dated snapshot (src/wikidata.py) rather than the live API, so the numbers
stay reproducible as Wikidata changes underneath. Re-running against an existing
snapshot makes no network calls.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import CounterFactRecord, load_counterfact  # noqa: E402
from wikidata import Snapshot  # noqa: E402

SEED: Final[int] = 1538
PER_RELATION: Final[int] = 5
RIGID: Final[list[str]] = [
    "P19", "P20", "P103", "P495", "P740", "P364", "P407", "P178", "P138", "P449", "P30",
]


def sample(records: list[CounterFactRecord]) -> dict[str, list[CounterFactRecord]]:
    rng = random.Random(SEED)
    by_rel: dict[str, list[CounterFactRecord]] = defaultdict(list)
    for r in records:
        if r.rewrite.relation_id in RIGID:
            by_rel[r.rewrite.relation_id].append(r)
    return {rel: rng.sample(rs, min(PER_RELATION, len(rs))) for rel, rs in by_rel.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", default=None, help="YYYY-MM-DD; default = latest")
    ap.add_argument("--refresh", action="store_true",
                    help="allow network fetches into today's snapshot")
    args = ap.parse_args()

    snap = Snapshot.open_or_new() if args.refresh else Snapshot.load(args.snapshot)
    chosen = sample(load_counterfact())

    rows: list[dict[str, Any]] = []
    for rel, recs in sorted(chosen.items()):
        qids = {r.case_id: (snap.link(r.rewrite.subject) if args.refresh
                            else snap.links.get(r.rewrite.subject))
                for r in recs}
        if args.refresh:
            snap.fetch_claims([q for q in qids.values() if q])
        for rec in recs:
            qid = qids[rec.case_id]
            cl = snap.claims.get(qid, {}) if qid else {}
            rows.append({
                "relation": rel, "subject": rec.rewrite.subject, "qid": qid,
                "n_props": len(cl), "n_statements": sum(len(v) for v in cl.values()),
                "has_edited_prop": rel in cl, "props": sorted(cl),
            })
    if args.refresh:
        snap.save()

    linked = [r for r in rows if r["qid"]]
    print(f"snapshot: {snap.ingested}")
    print(f"sampled {len(rows)} rigid-relation edits ({PER_RELATION}/relation, seed {SEED})")
    print(f"entity-linked: {len(linked)}/{len(rows)} ({100*len(linked)/len(rows):.0f}%)\n")
    print(f"{'rel':<6}{'linked':>7}{'med props':>11}{'med stmts':>11}{'has edited prop':>17}")
    for rel in sorted(chosen):
        rs = [r for r in rows if r["relation"] == rel]
        lk = [r for r in rs if r["qid"]]
        med_p = sorted(r["n_props"] for r in lk)[len(lk) // 2] if lk else 0
        med_s = sorted(r["n_statements"] for r in lk)[len(lk) // 2] if lk else 0
        print(f"{rel:<6}{len(lk):>3}/{len(rs):<3}{med_p:>11}{med_s:>11}"
              f"{sum(r['has_edited_prop'] for r in rs):>13}/{len(rs)}")

    allprops: Counter[str] = Counter()
    for r in linked:
        allprops.update(r["props"])
    print(f"\ndistinct properties across linked subjects: {len(allprops)}")
    print("most common:", ", ".join(f"{p}({n})" for p, n in allprops.most_common(15)))
    (Path(__file__).parent / "wikidata_coverage.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
