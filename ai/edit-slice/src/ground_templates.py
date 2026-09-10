"""Hand-written prompt templates for Wikidata ground properties.

CounterFact templates its own 34 relations only. Grounds use whatever properties
Wikidata asserts, so these are written by hand — a judgement call, published
contestable at `probes/ground_templates.md`.

Two rules, both earned the hard way:
  1. No temporal/locative ambiguity. CounterFact's "died at" invites "the age of
     90" and a knowing model scores zero [T-044]. Every template names its type.
  2. `wikibase-item` filtering is necessary, not sufficient. Wikidata's ontological
     bookkeeping (P31 instance-of, P910 category, P1343 described-by, P1889
     different-from) is item-valued and carries no grounding. Having no template
     for a property is how it is excluded.
"""

from __future__ import annotations

from typing import Final

#: Item-valued but not factual grounding — the Wikidata analogue of DBpedia's
#: alias predicates that killed E-001, milder but the same shape.
BOOKKEEPING: Final[frozenset[str]] = frozenset(
    {"P31", "P910", "P1343", "P1889", "P279", "P361", "P2860", "P921", "P1424", "P5008"}
)

TEMPLATES: Final[dict[str, tuple[str, str]]] = {
    "P19": ("place of birth", "{} was born in the city of"),
    "P20": ("place of death", "{} died in the city of"),
    "P119": ("place of burial", "{} is buried in the city of"),
    "P27": ("country of citizenship", "{} holds citizenship of the country of"),
    "P17": ("country", "{} is located in the country of"),
    "P131": ("administrative territory", "{} is located in the administrative region of"),
    "P30": ("continent", "{} is located on the continent of"),
    "P106": ("occupation", "{} works professionally as a"),
    "P1412": ("languages spoken", "{} speaks the language of"),
    "P69": ("educated at", "{} was educated at the institution of"),
    "P166": ("award received", "{} received the award named"),
    "P463": ("member of", "{} is a member of the organization of"),
    "P734": ("family name", "The family name of {} is"),
    "P735": ("given name", "The given name of {} is"),
    "P495": ("country of origin", "{} originates from the country of"),
    "P136": ("genre", "The genre of {} is"),
    "P364": ("original language of work", "The original language of {} is"),
    "P407": ("language of work", "{} was written in the language of"),
    "P449": ("original broadcaster", "{} was originally broadcast on the network of"),
    "P138": ("named after", "{} was named in honour of"),
    "P178": ("developer", "{} was developed by the company of"),
    "P86": ("composer", "The music of {} was composed by"),
    "P750": ("distributed by", "{} was distributed by the company of"),
    "P161": ("cast member", "One of the actors appearing in {} is"),
    "P57": ("director", "{} was directed by"),
    "P50": ("author", "{} was written by the author"),
}

#: Templates that are near-tautological because the answer appears in the prompt.
#: A high score here means little; reported separately rather than dropped.
WEAK: Final[frozenset[str]] = frozenset({"P734", "P735"})


def prompt_for(pid: str, subject: str) -> str | None:
    tpl = TEMPLATES.get(pid)
    return tpl[1].format(subject) if tpl else None
