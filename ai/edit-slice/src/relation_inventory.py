"""CounterFact relation inventory with time-rigidity labels.

Executes R-003 / thread T-023. design.md establishes that orphaning requires the
EDITED fact's relation to be rigid over time: if a later event can reconcile the
old and new values (the tower was moved, the job changed), no contradiction
arises and no orphan is possible in principle.

Labels are applied per RELATION TYPE, never per fact. That is what keeps this out
of the circularity described in notes/session-2026-09-08.md section 5 — we are not
enumerating which probes we believe depend on a fact, we are classifying a closed
vocabulary of 34 Wikidata properties.

The labels are a judgement call and are published as contestable data. Anyone who
disputes one can re-run with their own MODALITY table and get a different number.

Usage:
    python src/relation_inventory.py            # uses the pinned data/ copy
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias

from data import DEFAULT_COUNTERFACT, CounterFactRecord, load_counterfact

Modality: TypeAlias = Literal["rigid", "ambiguous", "mutable"]


@dataclass(frozen=True)
class RelationLabel:
    """A time-rigidity judgement about one Wikidata property."""

    name: str
    modality: Modality
    rationale: str


#: Labels for every relation appearing in CounterFact. Contestable by design.
#: rigid     — no later event reconciles the old and new value; orphan is forced
#: mutable   — a reconciling world exists; no contradiction, so no orphan
#: ambiguous — genuinely unclear; reported as a result, never silently resolved
MODALITY: Final[dict[str, RelationLabel]] = {
    "P19": RelationLabel("place of birth", "rigid", "birth happens once; nothing later relocates it"),
    "P20": RelationLabel("place of death", "rigid", "death happens once"),
    "P103": RelationLabel("native language", "rigid", "fixed at acquisition; later languages are P1412"),
    "P495": RelationLabel("country of origin", "rigid", "origin is a creation event"),
    "P740": RelationLabel("location of formation", "rigid", "formation happens once"),
    "P364": RelationLabel("original language of work", "rigid", "fixed at creation; 'original' is explicit"),
    "P407": RelationLabel("language of work", "rigid", "fixed at creation"),
    "P178": RelationLabel("developer / created by", "rigid", "authorship of a creation event"),
    "P138": RelationLabel("named after", "rigid", "the naming is a historical event"),
    "P449": RelationLabel("original broadcaster", "rigid", "'original' is explicit; later networks do not revise it"),
    "P30": RelationLabel("continent", "rigid", "geographic, not political; places do not change continent"),
    "P176": RelationLabel("manufacturer", "ambiguous", "fixed for one artifact, mutable for a product line"),
    "P136": RelationLabel("genre", "ambiguous", "fixed for a work, changeable for a person; prompt is person-oriented"),
    "P641": RelationLabel("sport", "ambiguous", "switching sports is rare but possible"),
    "P27": RelationLabel("citizenship", "mutable", "naturalisation"),
    "P413": RelationLabel("position on team", "mutable", "changes across a career"),
    "P1412": RelationLabel("languages spoken", "mutable", "languages can be learned"),
    "P37": RelationLabel("official language", "mutable", "changes by legislation"),
    "P17": RelationLabel("country", "mutable", "borders and sovereignty change"),
    "P937": RelationLabel("work location", "mutable", "people relocate"),
    "P106": RelationLabel("occupation", "mutable", "careers change"),
    "P159": RelationLabel("headquarters location", "mutable", "companies move"),
    "P131": RelationLabel("admin territorial entity", "mutable", "boundaries are redrawn"),
    "P190": RelationLabel("twin city", "mutable", "twinnings are added and dropped"),
    "P276": RelationLabel("location", "mutable", "things move"),
    "P101": RelationLabel("field of work", "mutable", "fields change"),
    "P1303": RelationLabel("instrument", "mutable", "instruments can be learned"),
    "P39": RelationLabel("position held", "mutable", "offices are held for terms"),
    "P127": RelationLabel("owned by", "mutable", "ownership transfers"),
    "P140": RelationLabel("religion", "mutable", "conversion"),
    "P108": RelationLabel("employer", "mutable", "people change jobs"),
    "P463": RelationLabel("member of", "mutable", "memberships begin and end"),
    "P36": RelationLabel("capital", "mutable", "capitals are moved"),
    "P264": RelationLabel("record label", "mutable", "artists change labels"),
}

#: CounterFact ships Wikidata P-codes. The mined-rule vocabulary is DBpedia
#: (R-005a). Both must be recorded wherever out-degree or k is reported.
EDIT_VOCABULARY: Final[str] = "wikidata-property"


def inventory(
    records: list[CounterFactRecord],
) -> tuple[Counter[str], dict[str, str]]:
    """Return per-relation edit counts and one example prompt template each."""
    counts: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for record in records:
        rid = record.rewrite.relation_id
        counts[rid] += 1
        examples.setdefault(rid, record.rewrite.prompt)
    return counts, examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterfact", type=Path, default=DEFAULT_COUNTERFACT)
    args = parser.parse_args()

    records = load_counterfact(args.counterfact)
    counts, examples = inventory(records)

    unlabelled = set(counts) - set(MODALITY)
    if unlabelled:
        raise SystemExit(f"unlabelled relations, refusing to report: {sorted(unlabelled)}")

    total = sum(counts.values())
    by_modality: Counter[Modality] = Counter()
    for rid, n in counts.items():
        by_modality[MODALITY[rid].modality] += n

    print(f"vocabulary: {EDIT_VOCABULARY}")
    print(f"relations: {len(counts)}  edits: {total}")
    for modality in ("rigid", "ambiguous", "mutable"):
        n = by_modality[modality]
        nrel = sum(1 for r in counts if MODALITY[r].modality == modality)
        print(f"  {modality:<10} {nrel:>3} relations  {n:>6} edits  {100 * n / total:5.1f}%")


if __name__ == "__main__":
    main()
