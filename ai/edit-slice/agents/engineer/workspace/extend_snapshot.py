"""E-004 step 1: extend the Wikidata snapshot to cover the possession-sweep subjects.

E-002 ingested 55 subjects (5 per rigid relation); E-003 measured possession on a
different 165 (15 per relation). Joint possession — head AND ground held — requires
both measurements on the SAME subjects, so the snapshot is extended to the E-003
set. Same calendar date means the existing dated snapshot is appended to, which is
correct: it is one day's ingestion.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from wikidata import Snapshot, item_statements  # noqa: E402

sys.path.append(str(Path(__file__).parent))
from possession_rank import build_items  # noqa: E402


def main() -> None:
    items = build_items(15)
    snap = Snapshot.open_or_new()
    print(f"snapshot {snap.ingested}: {len(snap.links)} subjects before", flush=True)

    import json
    recs = json.loads(Path(__file__).parent.joinpath("possession_rank.json").read_text())
    subjects = {}
    for it in items:
        row = recs.get(f"EleutherAI/gpt-j-6b|{it['case_id']}")
        if row:
            subjects[it["case_id"]] = it["prompt"]

    from data import load_counterfact  # noqa: E402
    by_case = {r.case_id: r for r in load_counterfact()}
    names = [by_case[c].rewrite.subject for c in subjects]

    qids = []
    for i, name in enumerate(names):
        qids.append(snap.link(name))
        if i % 25 == 0:
            snap.save()
            print(f"  linked {i}/{len(names)}", flush=True)
    snap.fetch_claims([q for q in qids if q])
    snap.save()

    linked = [q for q in qids if q]
    print(f"\nlinked {len(linked)}/{len(names)}")
    props: Counter[str] = Counter()
    for q in linked:
        props.update(item_statements(snap.claims.get(q, {})).keys())
    print(f"distinct item-valued properties: {len(props)}")
    print("\nmost common (candidates for hand-written templates):")
    for pid, n in props.most_common(30):
        print(f"  {pid:<8}{n:>5}  ({100*n/len(linked):.0f}% of subjects)")


if __name__ == "__main__":
    main()
