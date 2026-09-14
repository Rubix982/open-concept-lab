"""Transitive containment chains — the deductive ground family [T-058].

Everything measured so far has been evidential: burial place *supports* place of
death without entailing it, so an edit produces an implausible belief state rather
than a contradictory one [E-002]. To ask whether contraction ever occurs at all
[T-041] we need grounds that genuinely entail, so a coherent model MUST give
something up.

**The outer fact must be RIGID.** The first version of this module anchored on
containment at both steps:

    X located-in Y  &  Y located-in Z  =>  X located-in Z

and claimed a strict contradiction. It is not one. `probes/relation_modality.md`
labels `P131` **mutable** — "boundaries are redrawn" — so editing the outer admits
a temporal reconciliation ("it is in Italy *now*"), which is precisely the escape
that made E-002's cases non-contradictory. Our own table predicted this and the
first version did not check it.

The family now anchors on **place of birth**, which is rigid:

    inner_1   X born-in Y        P19  — RIGID
    inner_2   Y in country Z     P17
    -------------------------------------- entails
    outer     X born-in Z

Edit the outer to some Z' != Z. Birth cannot be relocated, so the temporal escape
closes on the edited fact: the model must either give up that X was born in Y, or
claim Y was in Z' at the time of birth. Both are specific, probeable, and narrow.

`P17` also fixes a type bug by construction. Walking `P131` terminates wherever the
administrative hierarchy stops — "Gracie Mansion is located in the country of" ->
"New York City", the same error class as CounterFact's "died at" -> "the age of 90"
[T-044]. `P17` is defined to take a country, so the outer template's type is
guaranteed rather than filtered for.

Chains are mined by rule rather than hand-picked, so membership is inspectable —
which is what keeps the §5 circularity objection off a set we build ourselves.

Direction, for the record: RippleEdits' Logical Generalization already covers
transitivity **forward** — edit an inner, check the outer. This edits the outer and
checks the inners [definitions.md declaration 5].
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Iterator

#: Wikidata place of birth — the RIGID anchor for the outer fact.
BORN_IN: Final[str] = "P19"
#: Wikidata country. Defined to take a country, so the outer template's expected
#: type holds by construction rather than by a post-hoc filter.
COUNTRY: Final[str] = "P17"
#: Dissolution date. Presence on any chain entity means the answer depends on which
#: era the model is recalling — Soviet Union, Federal Republic of Yugoslavia.
DISSOLVED: Final[str] = "P576"

#: Prompt templates. Written to be unambiguous between locative and temporal
#: readings — CounterFact's "died at" invites "the age of 90" and a knowing model
#: scores zero [T-044]. Each names the expected type explicitly.
TEMPLATE_BIRTH_CITY: Final[str] = "{} was born in the city of"      # inner-1, P19
TEMPLATE_IN_COUNTRY: Final[str] = "{} is located in the country of"  # inner-2, P17
TEMPLATE_BIRTH_COUNTRY: Final[str] = "{} was born in the country of" # outer, entailed


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
        """The person whose birth country the outer fact asserts."""
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
    """X (person) born in Y (city), Y in country Z — entailing X born in Z."""
    return Chain(
        inner_1=Fact(x_label, TEMPLATE_BIRTH_CITY.format(x_label), y_label, x_qid, y_qid),
        inner_2=Fact(y_label, TEMPLATE_IN_COUNTRY.format(y_label), z_label, y_qid, z_qid),
        outer=Fact(x_label, TEMPLATE_BIRTH_COUNTRY.format(x_label), z_label, x_qid, z_qid),
        seed_case_id=seed_case_id,
    )


#: Tokens shorter than this are ignored when checking label overlap — otherwise
#: "X" matches "Bordeaux" and every chain looks degenerate.
MIN_TOKEN: Final[int] = 3


def _tokens(label: str) -> set[str]:
    keep = {"of", "the", "city", "district", "region", "province", "state", "county"}
    return {t for t in "".join(c if c.isalnum() else " " for c in label.lower()).split()
            if len(t) >= MIN_TOKEN and t not in keep}


def is_degenerate(x: str, y: str, z: str) -> str | None:
    """Reject chains where transitivity is trivial or a label gives the answer away.

    "Paris -> Paris -> France" is not two premises. And a shared token — "Mexico
    City" / "Mexico" — hands the model the conclusion from surface form alone, the
    same contamination the possession work had to design around [E-005].

    Overlap is checked on TOKENS, not substrings. Substring matching fires on
    single characters: "X" is inside "Bordeaux", which made every chain look
    degenerate in the first version of this check.
    """
    if len({x, y, z}) < 3:
        return "repeated entity in chain"
    tx, ty, tz = _tokens(x), _tokens(y), _tokens(z)
    if tx & ty:
        return f"person and birth city share a token: {sorted(tx & ty)}"
    if ty & tz:
        return f"birth city and country share a token: {sorted(ty & tz)}"
    if tx & tz:
        return f"person and country share a token: {sorted(tx & tz)}"
    return None
