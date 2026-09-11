"""Type-matching validation for candidate sets, by coordination [T-055].

The possession measure in `probing.py` / `possession_lift.py` assumes its
distractors are type-matched with the true answer — that is what prevents
CounterFact's ambiguous templates from expressing themselves ("died at" invites
"the age of 90" as readily as a city). The assumption was never checked, so a
contaminated candidate set would pass silently and the measure would quietly
become the artifact it claims to remove.

Coordination tests it. Two expressions are the same semantic type iff they
coordinate under one predicate without anomaly:

    "Koun died at Athens and at Naples"        natural   -> same type
    "Koun died at Athens and at the age of 90" zeugmatic -> different types

Operationally, **coordination lift**:

    lift(c) = log P(c | prompt + anchor + " and") - log P(c | prompt)

An anchor of the intended type raises the probability of same-type continuations
(it has established what kind of thing fills the slot) and does much less for
cross-type ones. Candidates with low lift relative to the set are contaminants.

MEASURED BEHAVIOUR, and it is weaker than the motivation suggests. On a genuine
zeugma ("the archivist shredded the filing cabinet and the {X}") same-type and
cross-type candidates separate by **+2.39** median lift; on CounterFact's ambiguous
"died at" template, by **+1.61**. The direction is right and the set-level statistic
is usable. But **individual candidates are not reliably classified**: "dust jacket"
and "spine label" are same-type yet score below every cross-type item, because
coordination lift measures the plausibility of *joint predication*, which includes
type agreement but is not limited to it — you do not shred a dust jacket alongside a
filing cabinet for reasons of plausibility, not ontology.

So this is a **set-level diagnostic**, not a per-candidate filter. Use `separation`
to ask whether a candidate set is homogeneous; treat `suspects` as advisory only.

A second limitation, found the same way: corpus attestation defeats the test where
the ambiguity is idiomatic. "Died at Naples and at the age of 90" is standard
obituary English, so the coordination is barely anomalous even though the types
differ. Templates whose ambiguity is *conventional* will not be caught this way.

This is a diagnostic over the instrument, not a claim about models.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Callable, Final

#: Candidates scoring this many stdevs below the set median are flagged.
#: A judgement call, published contestable like probes/relation_modality.md [T-027].
OUTLIER_SIGMA: Final[float] = 1.0

#: Scores (prompt, continuation) pairs. Satisfied by remote.score_pairs and by a
#: local wrapper over probing.score, so the diagnostic is backend-agnostic.
Scorer = Callable[[list[tuple[str, str]]], list[float]]


@dataclass(frozen=True)
class TypeMatch:
    """Coordination lift for one candidate against an anchor of the intended type."""

    candidate: str
    base: float
    coordinated: float

    @property
    def lift(self) -> float:
        return self.coordinated - self.base


@dataclass(frozen=True)
class SetReport:
    """Verdict over a whole candidate set."""

    prompt: str
    anchor: str
    matches: list[TypeMatch]

    @property
    def lifts(self) -> list[float]:
        return [m.lift for m in self.matches]

    @property
    def median_lift(self) -> float:
        return statistics.median(self.lifts)

    def separation(self, group_a: list[str], group_b: list[str]) -> float:
        """Median lift of one putative type group minus the other — THE product.

        Positive means group_a coordinates more naturally with the anchor, i.e. the
        groups are different types. Measured at +2.39 on a genuine zeugma and +1.61
        on an ambiguous CounterFact template.
        """
        lift = {m.candidate: m.lift for m in self.matches}
        return (statistics.median(lift[c] for c in group_a)
                - statistics.median(lift[c] for c in group_b))

    @property
    def suspects(self) -> list[TypeMatch]:
        """Low-lift candidates — ADVISORY ONLY, not a reliable classifier.

        Measured false positives (same-type items scoring low because the joint
        predication is implausible rather than ill-typed) and false negatives. Use
        for triage by eye, never as an automatic filter.
        """
        if len(self.matches) < 4:
            return []
        med = self.median_lift
        sigma = statistics.pstdev(self.lifts) or 1e-9
        return sorted(
            (m for m in self.matches if (m.lift - med) / sigma < -OUTLIER_SIGMA),
            key=lambda m: m.lift,
        )

    @property
    def homogeneous(self) -> bool:
        """Advisory: no candidate is a clear low-lift outlier. See `suspects`."""
        return not self.suspects


def coordination_lift(scorer: Scorer, prompt: str, anchor: str,
                      candidates: list[str]) -> SetReport:
    """Two scoring calls: uncoordinated baseline, then coordinated with the anchor."""
    coord_prompt = f"{prompt} {anchor.strip()} and"
    base = scorer([(prompt, c) for c in candidates])
    coord = scorer([(coord_prompt, c) for c in candidates])
    return SetReport(
        prompt=prompt,
        anchor=anchor,
        matches=[TypeMatch(c, b, k) for c, b, k in zip(candidates, base, coord)],
    )
