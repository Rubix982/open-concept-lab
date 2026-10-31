"""Instantiate the diagnostic families over many subjects, mechanically.

`diagnostic.py` is sixteen hand-written items about one man. That licenses an
existence claim and nothing else — `[O-004]`, and it is the rule this project
inherits. To say anything about how OFTEN a family bites, the items have to come
from a pool rather than from me.

So: the **shapes** are enumerated (there are finitely many ways a subject can
sit in a prompt) while the **subjects** are drawn from pinned CounterFact. That
is the split CLAUDE.md asks for — templates give coverage, the pool gives the
part I could not have chosen in advance.

**One family cannot be generated and is not faked.** A far-field probe reaches
its entity by description instead of by name, and CounterFact has no
descriptions. Generating one would mean writing the description myself, which
puts the item back in the hand-built category while looking like data. Far-field
stays hand-built, existence-only, and the path to scale is MQuAKE's later-hop
items (T-005), which already name no subject in 16,506 of 16,506 cases.

Deterministic: the seed is recorded in the output and nothing else is random.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Final, Iterator

from editreach.coefficient import Regime
from editreach.data import CounterFactRecord, load_counterfact

from .diagnostic import Item

SEED: Final[int] = 1538                 # the project's fixed seed
RELATION: Final[str] = "P19"            # place of birth: E-016's relation, so the
                                        # readings stay comparable with [E-016]/[E-033]
P, R = Regime.PREFIX_SHARING, Regime.PRECEDED

#: Bands come from prior readings, not from taste. [T-075] at layer 5:
#: late clause 0.935, possessive 0.934, long preamble 0.924; [E-018] floor 0.082.
BAND_PINNED: Final[tuple[float, float]] = (0.999, 1.001)
BAND_PRECEDED: Final[tuple[float, float]] = (0.80, 1.00)
BAND_FLOOR: Final[tuple[float, float]] = (0.0, 0.20)


def _name_parts(subject: str) -> tuple[str, str] | None:
    """`(given, family)` for a two-or-more-part name, else None."""
    parts = subject.split()
    return (parts[0], parts[-1]) if len(parts) >= 2 else None


def _confusables(records: list[CounterFactRecord]) -> dict[str, list[str]]:
    """Subjects sharing a given name or a surname with another subject.

    A floor measured against a random unrelated name is an easy negative. These
    are the hard ones, and they are found in the pool rather than invented.
    """
    by_given: dict[str, list[str]] = defaultdict(list)
    by_family: dict[str, list[str]] = defaultdict(list)
    for r in records:
        parts = _name_parts(r.rewrite.subject)
        if parts:
            by_given[parts[0]].append(r.rewrite.subject)
            by_family[parts[1]].append(r.rewrite.subject)
    out: dict[str, list[str]] = defaultdict(list)
    for bucket in (by_given, by_family):
        for names in bucket.values():
            if len(names) > 1:
                for n in names:
                    out[n] += [m for m in names if m != n]
    return {k: sorted(set(v)) for k, v in out.items()}


def _items_for(subject: str, *, case_id: str, other: str,
               confusable: str | None) -> Iterator[Item]:
    """Every family that can be generated, for one subject."""
    sid = subject.replace(" ", "_")
    parts = _name_parts(subject)
    # Every item from this subject carries its case id, so nothing downstream
    # has to resolve one from a name.
    mk = partial(Item, case_id=case_id)

    yield mk(f"{sid}/anchor-prefix", "position", f"{subject} was born in the city of",
               subject, P, BAND_PINNED,
               "Nothing precedes the subject, so k is k* and the ratio is 1 by "
               "arithmetic. A deviation is an implementation fault, not a fact.")
    yield mk(f"{sid}/anchor-floor", "position", f"{other} was born in the city of",
               other, P, BAND_FLOOR,
               "The same shape with a different person. This is what makes the "
               "pinned reading above mean anything.")
    yield mk(f"{sid}/late-clause", "position", f"The city where {subject} was born is",
               subject, R, BAND_PRECEDED,
               "Four tokens precede the subject. T-075 read 0.935 at L5 for this shape.")
    yield mk(f"{sid}/possessive", "position",
               f"The birthplace of {subject} is the city of", subject, R, BAND_PRECEDED,
               "T-075's possessive form, 0.934 at L5. Differs from the late clause in "
               "what precedes the subject, and the two were within 0.001 of each other.")
    yield mk(f"{sid}/long-preamble", "position",
               "In a survey of the period that has been cited many times since, the "
               f"author notes in passing that {subject} was born in the city of",
               subject, R, None,
               "OPEN. T-075's preamble was much shorter. If this falls further, the "
               "decay tracks preamble LENGTH, which T-075 could not separate from "
               "mere presence.")

    if parts:
        given, family = parts
        yield mk(f"{sid}/alias-surname", "alias", f"{family} was born in the city of",
                   family, P, None,
                   "OPEN. A shorter surface form at the prefix. E-040 found the "
                   "coefficient tracks surface similarity, while prefix-sharing is "
                   "supposed to pin at 1.000. Those two expectations conflict.")
        yield mk(f"{sid}/alias-given", "alias", f"{given} was born in the city of",
                   given, P, None,
                   "OPEN. The other half of the name, to separate which PART of a name "
                   "carries the key from how much of it is shared. Note that a bare "
                   "given name often does not refer to anyone in particular -- three "
                   "subjects in a 42-subject draw were called John -- so a high reading "
                   "here would say the coefficient responds to tokens rather than to "
                   "entities, which is worth knowing and is why the item stays.")

    yield mk(f"{sid}/repeat-first", "repetition",
               f"{subject} is the subject here. {subject} was born in the city of",
               subject, P, BAND_PINNED,
               "Read at the FIRST mention, which is at the prefix, so the pinning "
               "applies. This is also what the default silently gives: a correct "
               "number attached to the wrong mention.", occurrence=0)
    yield mk(f"{sid}/repeat-last", "repetition",
               f"{subject} is the subject here. {subject} was born in the city of",
               subject, R, None,
               "OPEN. The same prompt read at the SECOND mention, which the question "
               "hangs off. The gap between the two is the cost of the default.",
               occurrence=-1)

    if confusable:
        yield mk(f"{sid}/confusable", "discrimination",
                   f"{confusable} was born in the city of", confusable, P, None,
                   "OPEN. A different person sharing a name part with the subject, "
                   "found in the pool rather than invented. If the measure cannot "
                   "separate this from the anchor, the 0.082 floor was measured "
                   "against an easy negative and overstates its discrimination.")

    yield mk(f"{sid}/bystander", "exposure",
               f"{other} admired {subject}. {other} was born in the city of",
               subject, R, None,
               "OPEN, and the item C-001 most needs. The edited subject is in the "
               "prompt so delivery should be high, while the question is about "
               "someone else so the answer should not move. Either outcome is a "
               "result: no movement demonstrates delivery-is-not-effect, movement "
               "is damage by exposure.")
    yield mk(f"{sid}/negated", "semantics",
               f"It is not true that {subject} was born in the city of", subject, R, None,
               "OPEN. Reverses the claim while leaving the subject token untouched. "
               "If the coefficient is unchanged, it is a lexical-position quantity "
               "and not a semantic one, which readers will otherwise assume.")


def generate(n_subjects: int = 42, *, seed: int = SEED,
             case_ids: list[int] | None = None,
             counterfact: Path | None = None) -> tuple[list[Item], dict]:
    """Items for `n_subjects` drawn from the pinned pool, deterministically.

    `case_ids` anchors the draw instead of sampling. Pass it whenever the run
    downstream reads a cache: `v*` cannot be optimised remotely on nnsight 0.8.1
    ([E-047]), so the only subjects that can be edited at all are the ones whose
    deltas are already cached. A free sample from the same relation and the same
    seed overlapped those by **2 of 42** — which would have been discovered after
    booking the remote session, not before.
    """
    corpus = load_counterfact(counterfact)
    # Named subjects only, for the confusable index and the free-sampling path.
    # The ANCHORED path draws from the whole corpus, because a cached subject may
    # be a single-word name — the alias family simply skips those rather than
    # excluding the subject from every other family.
    everyone = [r for r in corpus if _name_parts(r.rewrite.subject)]
    records = [r for r in everyone if r.rewrite.relation_id == RELATION]
    records.sort(key=lambda r: r.case_id)            # the pool's own order, not a hash

    # Confusables are drawn from the WHOLE corpus, not just this relation. A
    # coefficient reading needs no ground truth about the confusable person — it
    # is a key, not an answer — and restricting to P19 found a near-name for only
    # 14 of 42 subjects, which would have made the family an anecdote.
    conf = _confusables(everyone)
    rng = random.Random(seed)
    if case_ids is not None:
        by_id = {r.case_id: r for r in corpus}
        missing = [c for c in case_ids if c not in by_id]
        if missing:
            raise KeyError(f"case_ids not in CounterFact: {missing[:5]}")
        chosen = [by_id[c] for c in case_ids]
        merged = {r.case_id: r for r in records}
        merged.update({r.case_id: r for r in chosen})
        records = sorted(merged.values(), key=lambda r: r.case_id)
    else:
        chosen = rng.sample(records, k=min(n_subjects, len(records)))

    # The floor must name someone who is NOT one of the subjects under test, and
    # no two subjects may draw the same one. Without both, a floor item turns out
    # to be another subject's pinned anchor measured a second time — which the
    # dry-run caught, three times in a 42-subject draw.
    chosen_names = {r.rewrite.subject for r in chosen}
    outsiders = [r.rewrite.subject for r in records if r.rewrite.subject not in chosen_names]
    rng.shuffle(outsiders)
    if len(outsiders) < len(chosen):
        raise ValueError(f"pool has {len(outsiders)} names outside the {len(chosen)} "
                         f"subjects; cannot give each a distinct floor")

    items: list[Item] = []
    seen_alias: set[str] = set()
    # Two subjects sharing a given name can otherwise draw the same confusable:
    # 'Jacob Katz' served both Jacob Holdt and Jacob Wallenberg, which is one
    # reading counted twice under two different subjects' names.
    used_confusables: set[str] = set()
    for rec, other in zip(chosen, outsiders):
        subject = rec.rewrite.subject
        cands = [c for c in conf.get(subject, [])
                 if c != subject and c not in chosen_names and c not in used_confusables]
        confusable = rng.choice(cands) if cands else None
        if confusable:
            used_confusables.add(confusable)
        for item in _items_for(subject, case_id=str(rec.case_id), other=other,
                               confusable=confusable):
            # A bare given name is shared: keep the first, so one reading is not
            # counted once per person who happens to have that name.
            if item.family == "alias" and item.id.endswith("/alias-given"):
                if item.prompt in seen_alias:
                    continue
                seen_alias.add(item.prompt)
            items.append(item)

    meta = {
        "seed": seed, "relation": RELATION,
        "anchored_to_case_ids": case_ids is not None,
        "pool_size": len(records), "confusable_pool": len(everyone),
        "subjects": len(chosen), "items": len(items),
        "subjects_with_a_confusable": sum(1 for i in items if i.family == "discrimination"),
        "distinct_floor_names": len({i.subject for i in items if i.id.endswith("/anchor-floor")}),
        "families_generated": sorted({i.family for i in items}),
        "families_not_generated": ["far-field"],
        "single_name_subjects": sum(1 for r in chosen if not _name_parts(r.rewrite.subject)),
        "note": ("far-field is hand-built only: CounterFact has no descriptions, so "
                 "generating one would mean writing it myself while it looked like "
                 "data. Scale for that family comes from MQuAKE later-hop items."),
    }
    return items, meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-n", "--subjects", type=int, default=42)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("-o", "--out", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--counterfact", type=Path, default=None,
                    help="pinned corpus; defaults to EDITREACH_DATA or a search upwards")
    ap.add_argument("--case-ids", type=Path, default=None,
                    help="JSON list of CounterFact case_ids to anchor the draw to. "
                         "Use this whenever the run reads a delta cache.")
    a = ap.parse_args()

    ids = json.loads(a.case_ids.read_text()) if a.case_ids else None
    items, meta = generate(a.subjects, seed=a.seed, case_ids=ids,
                           counterfact=a.counterfact)
    payload = {"meta": meta, "items": [
        {**asdict(i), "regime": i.regime.value} for i in items]}
    a.out.write_text(json.dumps(payload, indent=1))

    print(f"{meta['items']} items over {meta['subjects']} subjects -> {a.out}")
    counts: dict[str, int] = defaultdict(int)
    for i in items:
        counts[i.family] += 1
    for fam, n in sorted(counts.items()):
        print(f"  {fam:<16} {n:>4}")
    banded = sum(1 for i in items if not i.is_open)
    print(f"\n{banded} with a band to violate, {len(items) - banded} open. "
          f"{meta['subjects_with_a_confusable']} subjects had a confusable in the pool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
