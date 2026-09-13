"""E-008: mine transitive containment chains from Wikidata.

Seeds are CounterFact subjects whose relation is P131 or P17 — those subjects are
places and therefore sit in containment hierarchies. People and works do not, which
is why the wider CounterFact subject pool is not usable here.

Walks P131 twice: X -> Y -> Z. Attrition is recorded at every step and reported,
because a set built by us is only defensible if the selection rule is inspectable.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from chains import CONTAINED_IN, Chain, build_chain, is_degenerate  # noqa: E402
from data import load_counterfact  # noqa: E402
from wikidata import Snapshot, item_statements  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "probes" / "containment_chains.json"


def first_item(claims: dict, pid: str) -> str | None:
    vals = item_statements(claims).get(pid, [])
    return vals[0] if vals else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=120)
    ap.add_argument("--refresh", action="store_true", help="allow network fetches")
    args = ap.parse_args()

    snap = Snapshot.open_or_new() if args.refresh else Snapshot.load()
    seeds = [r for r in load_counterfact()
             if r.rewrite.relation_id in ("P131", "P17")][: args.seeds]
    print(f"{len(seeds)} place-subject seeds\n", flush=True)

    attrition: Counter[str] = Counter()
    chains: list[Chain] = []

    for i, rec in enumerate(seeds):
        x_label = rec.rewrite.subject
        x_qid = snap.link(x_label) if args.refresh else snap.links.get(x_label)
        if not x_qid:
            attrition["subject did not entity-link"] += 1
            continue
        if args.refresh:
            snap.fetch_claims([x_qid])
        y_qid = first_item(snap.claims.get(x_qid, {}), CONTAINED_IN)
        if not y_qid:
            attrition[f"subject has no {CONTAINED_IN}"] += 1
            continue
        if args.refresh:
            snap.fetch_claims([y_qid])
        z_qid = first_item(snap.claims.get(y_qid, {}), CONTAINED_IN)
        if not z_qid:
            attrition[f"mid-entity has no {CONTAINED_IN} (chain ends at one hop)"] += 1
            continue

        if args.refresh:
            snap.fetch_labels([x_qid, y_qid, z_qid])
            snap.save()
        y_label = snap.labels.get(y_qid, y_qid)
        z_label = snap.labels.get(z_qid, z_qid)
        if y_label.startswith("Q") or z_label.startswith("Q"):
            attrition["unlabelled entity in chain"] += 1
            continue

        bad = is_degenerate(x_label, y_label, z_label)
        if bad:
            attrition[bad] += 1
            continue

        chains.append(build_chain(x_label, x_qid, y_label, y_qid,
                                  z_label, z_qid, str(rec.case_id)))
        if args.refresh and i % 20 == 0:
            print(f"  {i}/{len(seeds)}  chains so far: {len(chains)}", flush=True)

    if args.refresh:
        snap.save()

    print(f"\nchains built: {len(chains)} / {len(seeds)} seeds "
          f"({100*len(chains)/len(seeds):.0f}%)\n")
    print("attrition:")
    for reason, n in attrition.most_common():
        print(f"  {n:>4}  {reason}")

    print("\nexamples:")
    for c in chains[:8]:
        print(f"  {c.entailment()}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(
        {"snapshot": snap.ingested,
         "n_seeds": len(seeds),
         "n_chains": len(chains),
         "attrition": dict(attrition),
         "chains": [c.as_dict() for c in chains]}, indent=1))
    print(f"\nwritten: {OUT.relative_to(OUT.parents[1])}")


if __name__ == "__main__":
    main()
