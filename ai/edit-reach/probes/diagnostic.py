"""A set built to BREAK the instrument, not to score a method.

Every item carries a prediction. That is the whole difference between this and a
benchmark: a benchmark tells you how well something did, and this tells you
whether the reading can be trusted at all. An item whose coefficient lands
outside its predicted band is a defect in the measurement, not a finding about
the model — and that is the only kind of conclusion this file licenses.

**Zero edits are needed.** Every quantity here is read from the unedited model,
so the whole set costs forward passes and nothing else. It is deliberately prior
to C-001: if the instrument reads the wrong token under aliasing or repeated
mentions, every correlation downstream is measuring the bug.

Bands are wide on purpose. A narrow band dressed up as a prediction would be
fitting the number we already have ([T-075]: 0.93 at L5, 0.52 at L24, 0.082 for
a different subject). Where no prior reading exists the band is marked OPEN and
the item is a question rather than a check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from editreach.coefficient import Regime

SUBJECT: Final[str] = "Maurice de Vlaminck"
OTHER: Final[str] = "Hiroshi Nakamura"          # the different-subject floor


@dataclass(frozen=True, slots=True)
class Item:
    """One diagnostic probe, its prediction, and why that prediction."""

    id: str
    family: str
    prompt: str
    subject: str
    regime: Regime
    band: tuple[float, float] | None            # None == OPEN, no prior reading
    why: str
    occurrence: int = 0                         # which mention the key is read at
    case_id: str = ""                           # the CounterFact record this came from

    # A NAME is not an identifier. Two subjects in CounterFact -- "Claudio Coello"
    # and "Nikolai Nissen Paus" -- appear under two case ids each, so resolving a
    # name back to a record silently picks one. The id travels with the item.

    @property
    def is_open(self) -> bool:
        return self.band is None

    @property
    def subject_occurrences(self) -> int:
        return self.prompt.count(self.subject)

    @property
    def reads_at_prefix(self) -> bool:
        """Is the mention this item reads at the one the prompt begins with?

        The dry-run caught the repetition family labelled PRECEDED while its
        prompts began with the subject. Both were true of the prompt and neither
        was true of the reading, because the regime is a property of WHICH
        MENTION is read, not of the prompt alone.
        """
        idx = self.occurrence if self.occurrence >= 0 else self.subject_occurrences + self.occurrence
        return idx == 0 and self.prompt.startswith(self.subject)


P, R = Regime.PREFIX_SHARING, Regime.PRECEDED

ITEMS: Final[tuple[Item, ...]] = (
    # ---- 1. the analytic anchor. If this is not 1.000, the pipeline is broken.
    Item("anchor-prefix", "position", f"{SUBJECT} was born in the country of", SUBJECT, P,
         (0.999, 1.001),
         "Causal attention has read nothing before the subject, so k IS k* and the "
         "ratio is 1 by arithmetic. A deviation here is an implementation fault "
         "(padding, position, tokenisation), never a fact about the model."),
    Item("anchor-floor", "position", f"{OTHER} was born in the country of", OTHER, P,
         (0.0, 0.20),
         "Same shape, different person. This is what makes the 1.000 above mean "
         "something: a pipeline hard-wired to return 1 cannot produce this."),

    # ---- 2. position. T-075 measured these shapes at depth; here at L5.
    Item("late-clause", "position", f"The city where {SUBJECT} was born is", SUBJECT, R,
         (0.85, 1.00),
         "Four tokens precede the subject. T-075 read 0.935 at L5 for this shape."),
    Item("possessive", "position", f"The birthplace of {SUBJECT} is the city of", SUBJECT, R,
         (0.85, 1.00),
         "T-075's possessive form, which read 0.934 at L5. Carried alongside the late "
         "clause because the two differ in what precedes the subject -- a noun phrase "
         "against a subordinating clause -- and T-075 found them within 0.001 of each "
         "other, which is worth confirming rather than assuming."),
    Item("long-preamble", "position",
         "In a study of early twentieth-century European painting that has been "
         f"cited many times since, the scholar notes that {SUBJECT} was born in", SUBJECT, R,
         (0.80, 1.00),
         "T-075's long preamble read 0.924 at L5, with a much shorter preamble than "
         "this. If a longer one falls further, the decay is a function of preamble "
         "LENGTH and not merely of its presence, which T-075 could not separate."),

    # ---- 3. surface form. E-040 measured an alias gradient, rho 0.778.
    Item("alias-surname", "alias", "Vlaminck was born in the country of", "Vlaminck", P, None,
         "OPEN. A shorter surface form of the same entity. E-040 found the coefficient "
         "tracks surface similarity, so this should sit below the anchor — but the "
         "anchor is prefix-sharing and so is this, and prefix-sharing is supposed to "
         "pin at 1.000. Those two expectations conflict, which is why it is here."),
    Item("alias-initial", "alias", "M. de Vlaminck was born in the country of",
         "M. de Vlaminck", P, None,
         "OPEN. The same conflict as alias-surname, with a tokenisation change on top: "
         "an initial and a full stop tokenise differently from a given name, so this "
         "separates surface similarity from token-boundary effects."),
    Item("alias-possessive-s", "alias", f"{SUBJECT}'s birth country is", SUBJECT, P, None,
         "OPEN. The subject is still at the prefix, but the token after it binds "
         "tightly. Tests whether subject_last_index lands before the apostrophe."),

    # ---- 4. repetition. The same prompt read two ways. The PAIR is the item:
    #        one prompt, two mentions, two regimes, and a difference that should
    #        be large. If it is not, `subject_last` is not doing what it says.
    Item("repeat-first", "repetition",
         f"{SUBJECT} painted in Chatou. {SUBJECT} was born in the country of", SUBJECT, P,
         (0.999, 1.001),
         "Read at the FIRST mention, which the prompt begins with, so the analytic "
         "pinning applies and this must be 1.000. This is also what the default "
         "`str.index` behaviour silently gives you — the number is right and it is "
         "attached to the wrong mention, which is the dangerous combination.",
         occurrence=0),
    Item("repeat-last", "repetition",
         f"{SUBJECT} painted in Chatou. {SUBJECT} was born in the country of", SUBJECT, R,
         None,
         "OPEN. The same prompt read at the SECOND mention, which the question "
         "actually hangs off. Eight tokens precede it, so the analytic guarantee is "
         "gone. The gap between this and `repeat-first` is the cost of the default, "
         "and until it is measured nobody knows whether the default ever mattered.",
         occurrence=-1),
    Item("repeat-distant-last", "repetition",
         f"{SUBJECT} is discussed below. Several painters of the period, including "
         f"Derain and Matisse, worked alongside him. {SUBJECT} was born in", SUBJECT, R,
         None,
         "OPEN. The same pair with far more text between the mentions, to ask whether "
         "the gap in `repeat-last` tracks distance or merely the presence of a preamble.",
         occurrence=-1),

    # ---- 5. a near-miss subject. The floor's real test is not a random name.
    Item("confusable", "discrimination", "Maurice Denis was born in the country of",
         "Maurice Denis", P, None,
         "OPEN. A different French painter sharing a given name. If the coefficient "
         "cannot separate this from the anchor, the 0.082 floor was measured against "
         "an easy negative and overstates the measure's discrimination."),
    Item("same-surname", "discrimination", "Charles Vlaminck was born in the country of",
         "Charles Vlaminck", P, None,
         "OPEN. Shares the surname, which is where most of the subject's tokens live. "
         "If confusable and same-surname differ, the measure is sensitive to which "
         "part of a name is shared and not merely to how much of it is."),

    # ---- 6. the subject present, but the QUESTION about someone else.
    #        High delivery where no effect should occur: the cleanest C-001 case.
    Item("bystander", "exposure",
         f"Picasso admired {SUBJECT}. Picasso was born in the country of", SUBJECT, R, None,
         "OPEN, and the item C-001 most needs. The edited subject is in the prompt so "
         "delivery should be high, while the question is about a different person so "
         "the answer should not move. If it does not move, delivery-is-not-effect is "
         "demonstrated rather than asserted. If it does, that is damage by exposure."),

    # ---- 7. the far field. T-005.
    Item("hop-two", "far-field",
         "The head of government of the place where the painter of 'The River Seine "
         "at Chatou' was born is", SUBJECT, R, (0.0, 0.25),
         "The subject is never named; it is reached by description. Genuine two-hop "
         "propagation lives here. Predicted at floor — and if it IS at floor while "
         "the model's answer still moves under an edit, the instrument is blind in "
         "exactly the regime that matters. T-005."),

    # ---- 8. negation. The key is driven by the subject token, not by the logic.
    Item("negated", "semantics",
         f"It is not true that {SUBJECT} was born in the country of", SUBJECT, R, None,
         "OPEN. Semantically this reverses the claim while leaving the subject token "
         "untouched. If the coefficient is unchanged, it is confirmed to be a "
         "lexical-position quantity and not a semantic one — worth stating plainly, "
         "because readers will assume otherwise."),
)

FAMILIES: Final[tuple[str, ...]] = tuple(dict.fromkeys(i.family for i in ITEMS))
