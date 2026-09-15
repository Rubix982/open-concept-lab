"""E-012 · The paired-subject control: does the answer prefer THIS subject?

[E-011] established that the possession filter has no operating point for an answer
that is the modal answer for its relation. Its control asks *"does the subject matter
at all"* — the true answer must rank higher with the real subject than with a
placeholder. A modal answer defeats that by construction: under a natural rendering,
`"[X] was born in the country of the United States"` is the top completion whether or
not `[X]` means anything, so the lift test rejected 31 of the 40 items the model
demonstrably ranked correctly.

This asks the discriminating question instead. One score matrix, read two ways:

    row test     s(c | p_i) over candidates c   -> "given this subject, which answer?"
    column test  s(a_i | p_j) over prompts p_j  -> "given this answer, which subject?"

The column statistic is the fraction of FOIL prompts (those whose true answer differs)
that the true pair outscores. It is an AUROC: 0.5 is chance, 1.0 is perfect
discrimination. Crucially it is indifferent to how high the answer scores overall, and
therefore defined exactly where the placeholder control is not.

Costs no remote calls. `possession.run` always computed the row vector and discarded
it; schema v2 persists it, and the matrix is assembled from what is already on disk.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Final, Iterable, Sequence

from possession import ItemResult

#: Below this many usable foils an item's column statistic is not reported. Averaging
#: over three foils and calling it an AUROC would be the [E-007] denominator bug in a
#: new costume: a number whose precision comes from its own sparsity.
MIN_FOILS: Final[int] = 10


@dataclass(frozen=True)
class Discrimination:
    case_id: str
    relation_id: str
    true_answer: str
    #: AUROC over foil prompts; None when foil coverage is below MIN_FOILS.
    auc: float | None
    n_foils: int
    #: Foils available in principle (differing true answer) vs actually scorable.
    #: They differ because a sampled candidate pool does not contain every answer.
    n_foils_possible: int

    @property
    def coverage(self) -> float:
        return self.n_foils / self.n_foils_possible if self.n_foils_possible else 0.0


def _score_of(item: ItemResult, answer: str) -> float | None:
    """`item`'s score for `answer`, or None if that answer was not in its pool."""
    try:
        return item.scores_subject[item.candidates.index(answer)]
    except (ValueError, IndexError):
        return None


def discriminate(items: Sequence[ItemResult],
                 *, min_foils: int = MIN_FOILS) -> list[Discrimination]:
    """Column-wise AUROC per item, computed within each relation.

    Foils are restricted to the SAME relation, which holds the template and answer
    type fixed. Subject frequency is not controlled and remains a stated threat —
    see [T-061] for the prominence handle on it.
    """
    by_relation: dict[str, list[ItemResult]] = defaultdict(list)
    for it in items:
        by_relation[it.relation_id].append(it)

    out: list[Discrimination] = []
    for rel, group in by_relation.items():
        for it in group:
            own = _score_of(it, it.true_answer)
            foils = [o for o in group if o.true_answer != it.true_answer]
            scored = [s for s in (_score_of(o, it.true_answer) for o in foils)
                      if s is not None]
            if own is None or len(scored) < min_foils:
                out.append(Discrimination(it.case_id, rel, it.true_answer,
                                          None, len(scored), len(foils)))
                continue
            # Ties count as half, which is the standard AUROC convention and the
            # honest one: a tie is not evidence of discrimination in either
            # direction, and counting it as a win inflates every degenerate case.
            wins = sum(1.0 if own > s else 0.5 if own == s else 0.0 for s in scored)
            out.append(Discrimination(it.case_id, rel, it.true_answer,
                                      wins / len(scored), len(scored), len(foils)))
    return out


def held(item: ItemResult, disc: Discrimination, *, min_auc: float = 0.8) -> bool | None:
    """Row test AND column test. None where the column test is undefined.

    None is deliberate and must not be coerced to False. An item whose foil coverage
    is too thin is *unmeasured*, not *unpossessed*; folding the two together is how
    [E-007] reported 92% from 12 scored items of 40.
    """
    if disc.auc is None:
        return None
    return item.rank_subject == 1 and disc.auc >= min_auc


def summarise(items: Iterable[ItemResult], discs: Iterable[Discrimination],
              *, min_auc: float = 0.8) -> dict:
    by_id = {d.case_id: d for d in discs}
    rows = [(it, by_id[it.case_id]) for it in items if it.case_id in by_id]
    measured = [(it, d) for it, d in rows if d.auc is not None]
    return {
        "n_items": len(rows),
        "n_measured": len(measured),
        # TWO different coverages, kept apart on purpose. `item_coverage` is the
        # fraction of items whose AUC is defined at all; `foil_coverage` is how much
        # of each item's foil set was actually scorable. Reporting one under the
        # other's name is how a sparse measurement passes for a dense one.
        "item_coverage": len(measured) / len(rows) if rows else 0.0,
        "foil_coverage": (sum(d.coverage for _, d in measured) / len(measured))
                         if measured else 0.0,
        "row_pass_rate": (sum(it.rank_subject == 1 for it, _ in measured)
                          / len(measured)) if measured else None,
        "mean_auc": (sum(d.auc for _, d in measured) / len(measured))
                    if measured else None,
        "held_rate": (sum(bool(held(it, d, min_auc=min_auc)) for it, d in measured)
                      / len(measured)) if measured else None,
        "min_auc": min_auc,
    }
