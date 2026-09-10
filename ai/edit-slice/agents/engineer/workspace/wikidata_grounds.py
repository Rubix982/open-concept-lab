"""E-002 step 2: are co-present Wikidata properties plausibly GROUNDS?

Step 1 showed subjects are rich. Richness is not justification. This prints, for
one rigid-relation edit per relation, the item-valued statements with labels, so
the grounds question can be judged by reading.

Restricted to `wikibase-item` statements (src/wikidata.item_statements) — that
drops external identifiers, media and URLs by DATATYPE, which is Wikidata's
structural analogue of the DBpedia naming predicates behind E-001's tautologies.

Reads a dated snapshot; no network calls unless --refresh.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import load_counterfact  # noqa: E402
from wikidata import Snapshot, item_statements  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    snap = Snapshot.open_or_new() if args.refresh else Snapshot.load(args.snapshot)
    cov = json.loads((Path(__file__).parent / "wikidata_coverage.json").read_text())
    records = load_counterfact()

    picks: dict[str, dict] = {}
    for row in cov:
        if row["has_edited_prop"] and row["relation"] not in picks:
            picks[row["relation"]] = row

    print(f"snapshot: {snap.ingested}\n")
    for rel, row in sorted(picks.items()):
        rec = next(r for r in records
                   if r.rewrite.subject == row["subject"] and r.rewrite.relation_id == rel)
        items = item_statements(snap.claims.get(row["qid"], {}))
        ids = [row["qid"], *items, *[v for vs in items.values() for v in vs]]
        lab = snap.fetch_labels(ids) if args.refresh else {i: snap.labels.get(i, i) for i in ids}

        print("=" * 78)
        print(f"EDIT  {rel}  {rec.rewrite.subject} ({row['qid']})")
        print(f'      "{rec.rewrite.prompt.format(rec.rewrite.subject)}"')
        print(f"      {rec.rewrite.target_true}  ->  {rec.rewrite.target_new}")
        print(f"      item-valued properties: {len(items)} of {len(snap.claims.get(row['qid'], {}))}")
        for pid, vals in sorted(items.items()):
            mark = " <== EDITED" if pid == rel else ""
            shown = ", ".join(lab.get(v, v) for v in vals[:3])
            print(f"        {pid:<7}{lab.get(pid,pid)[:34]:<36}{shown[:44]}{mark}")
        print()
    if args.refresh:
        snap.save()


if __name__ == "__main__":
    main()
