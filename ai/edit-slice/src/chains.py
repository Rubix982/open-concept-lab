"""Transitive containment chains — the deductive ground family [T-058].

Everything measured so far has been evidential: burial place *supports* place of
death without entailing it, so an edit produces an implausible belief state rather
than a contradictory one [E-002]. To ask whether contraction ever occurs at all
[T-041] we need grounds that genuinely entail, so a coherent model MUST give
something up.

Containment is transitive by definition of the relation:

    inner_1   X located-in Y
    inner_2   Y located-in Z
    ----------------------------- entails
    outer     X located-in Z

Edit `outer` to some Z' != Z and the two inners still entail Z. That is a strict
contradiction. The question is whether the editor retracts either inner, or leaves
both standing.

Chains are mined from Wikidata `P131` (administrative containment) rather than
hand-picked, so membership is decided by a rule rather than by taste — which is
what keeps the §5 circularity objection off a set we build ourselves.

Direction, for the record: RippleEdits' Logical Generalization already covers
transitivity **forward** — edit an inner, check the outer. This edits the outer and
checks the inners [definitions.md declaration 5].
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Iterator

#: Wikidata administrative containment. P17 (country) is deliberately NOT used for
#: the hops: it jumps straight to the country and so cannot form a two-step chain.
CONTAINED_IN: Final[str] = "P131"

#: Prompt templates. Written to be unambiguous between locative and temporal
#: readings — CounterFact's "died at" invites "the age of 90" and a knowing model
#: scores zero [T-044]. Each names the expected type explicitly.
TEMPLATE_INNER: Final[str] = "{} is located in the region of"
TEMPLATE_OUTER: Final[str] = "{} is located in the country of"


@dataclass(frozen=True)
class Fact:
    subject: str
    prompt: str
    answer: str
    qid_subject: str | None = None
    qid_answer: str | None = None


@dataclass(frozen=True)
class Chain:
    """Two premises and the conclusion they entail."""

    inner_1: Fact          # X located-in Y
    inner_2: Fact          # Y located-in Z
    outer: Fact            # X located-in Z   (entailed)
    seed_case_id: str

    @property
    def x(self) -> str:
        return self.inner_1.subject

    @property
    def y(self) -> str:
        return self.inner_2.subject

    @property
    def z(self) -> str:
        return self.outer.answer

    def entailment(self) -> str:
        return (f"{self.x} in {self.y}  &  {self.y} in {self.z}"
                f"  =>  {self.x} in {self.z}")

    def facts(self) -> Iterator[Fact]:
        yield self.inner_1
        yield self.inner_2
        yield self.outer

    def as_dict(self) -> dict:
        return {"seed_case_id": self.seed_case_id,
                "entailment": self.entailment(),
                "inner_1": asdict(self.inner_1),
                "inner_2": asdict(self.inner_2),
                "outer": asdict(self.outer)}


def build_chain(x_label: str, x_qid: str, y_label: str, y_qid: str,
                z_label: str, z_qid: str, seed_case_id: str) -> Chain:
    return Chain(
        inner_1=Fact(x_label, TEMPLATE_INNER.format(x_label), y_label, x_qid, y_qid),
        inner_2=Fact(y_label, TEMPLATE_INNER.format(y_label), z_label, y_qid, z_qid),
        outer=Fact(x_label, TEMPLATE_OUTER.format(x_label), z_label, x_qid, z_qid),
        seed_case_id=seed_case_id,
    )


def is_degenerate(x: str, y: str, z: str) -> str | None:
    """Reject chains where transitivity is trivial or the labels collide.

    A chain like "Paris -> Paris -> France" is not two premises, and one where an
    inner answer repeats the outer answer gives the model the conclusion for free.
    """
    if len({x, y, z}) < 3:
        return "repeated entity in chain"
    if y.lower() in x.lower() or x.lower() in y.lower():
        return "inner-1 answer is a substring of its subject"
    if z.lower() in y.lower() or y.lower() in z.lower():
        return "inner-2 answer is a substring of its subject"
    return None
