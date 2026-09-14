"""E-008: mine birth-place entailment chains [T-058].

    inner-1   X born-in Y        P19  — RIGID, no relocation escape
    inner-2   Y in country Z     P17  — country by definition, so the outer
    ------------------------------------ template's type holds by construction
    outer     X born-in Z        entailed

The first version anchored on P131 containment at both steps and claimed a strict
contradiction. It was not one: relation_modality.md labels P131 mutable, so editing
the outer admitted a temporal escape. Birth does not relocate, which is what makes
this family deductive where the previous one was not.

Seeds are CounterFact P19 records (779 available). Attrition is recorded at every
step and reported: a set we build ourselves is only defensible if the selection
rule is inspectable.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from chains import (BORN_IN, COUNTRY, DISSOLVED, Chain, build_chain,  # noqa: E402
                    is_degenerate)
from data import load_counterfact  # noqa: E402
from wikidata import Snapshot, item_statements  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "probes" / "containment_chains.json"


def first_item(claims: dict, pid: str) -> str | None:
    vals = item_statements(claims).get(pid, [])
    return vals[0] if vals else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--refresh", action="store_true", help="allow network fetches")
    args = ap.parse_args()

    snap = Snapshot.open_or_new() if args.refresh else Snapshot.load()
    seeds = [r for r in load_counterfact()
             if r.rewrite.relation_id == BORN_IN][: args.seeds]
    print(f"{len(seeds)} P19 (place of birth) seeds\n", flush=True)

    attrition: Counter[str] = Counter()
    chains: list[Chain] = []

    def link(label: str) -> str | None:
        return snap.link(label) if args.refresh else snap.links.get(label)

    for i, rec in enumerate(seeds):
        x_label, y_label = rec.rewrite.subject, rec.rewrite.target_true

        x_qid, y_qid = link(x_label), link(y_label)
        if not x_qid:
            attrition["person did not entity-link"] += 1
            continue
        if not y_qid:
            attrition["birth city did not entity-link"] += 1
            continue

        if args.refresh:
            snap.fetch_claims([x_qid, y_qid])
        z_qid = first_item(snap.claims.get(y_qid, {}), COUNTRY)
        if not z_qid:
            attrition[f"birth city has no {COUNTRY} (country)"] += 1
            continue
        if args.refresh:
            snap.fetch_claims([z_qid])

        # Dissolved states make the answer depend on which era the model recalls.
        dissolved = [q for q in (y_qid, z_qid)
                     if DISSOLVED in snap.claims.get(q, {})]
        if dissolved:
            attrition["chain routes through a dissolved state"] += 1
            continue

        if args.refresh:
            snap.fetch_labels([x_qid, y_qid, z_qid])
            snap.save()
        z_label = snap.labels.get(z_qid, z_qid)
        if z_label.startswith("Q"):
            attrition["country unlabelled"] += 1
            continue

        bad = is_degenerate(x_label, y_label, z_label)
        if bad:
            attrition[bad.split(":")[0]] += 1
            continue

        chains.append(build_chain(x_label, x_qid, y_label, y_qid,
                                  z_label, z_qid, str(rec.case_id)))
        if args.refresh and i % 25 == 0:
            print(f"  {i}/{len(seeds)}  chains: {len(chains)}", flush=True)

    if args.refresh:
        snap.save()

    print(f"\nchains built: {len(chains)} / {len(seeds)} seeds "
          f"({100*len(chains)/max(1,len(seeds)):.0f}%)\n")
    print("attrition:")
    for reason, n in attrition.most_common():
        print(f"  {n:>4}  {reason}")

    print("\nexamples:")
    for c in chains[:10]:
        print(f"  {c.entailment()}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(
        {"snapshot": snap.ingested, "family": "P19 birth place + P17 country",
         "n_seeds": len(seeds), "n_chains": len(chains),
         "attrition": dict(attrition),
         "chains": [c.as_dict() for c in chains]}, indent=1))
    print(f"\nwritten: probes/{OUT.name}")


if __name__ == "__main__":
    main()
