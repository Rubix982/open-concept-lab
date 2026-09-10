# Ground prompt templates

_E-004. Contestable by design — disagree with a phrasing, change it in
`src/ground_templates.py` and re-run. The possession numbers move with it._

CounterFact supplies cloze templates only for its own 34 relations. Grounds are
whatever Wikidata asserts about the subject, so their properties have no templates
and these are hand-written.

## Two rules they follow

**1 · No temporal/locative ambiguity.** E-003 found CounterFact's own templates
carry this bug: *"Karolos Koun died at"* invites `" the age of 90"`, and
*"El Filibusterismo, formulated in"* invites `" the early 1970s"`. The model then
scores zero while knowing the answer perfectly well [T-044]. Every template below
names its expected type explicitly — "in the city of", "of the country of" — so
the slot cannot be read as a date.

**2 · Item-valued is not enough.** `src.wikidata.item_statements` filters to the
`wikibase-item` datatype, which removes external identifiers and media. It does
**not** remove Wikidata's ontological bookkeeping, which is also item-valued:

| excluded | why |
| --- | --- |
| `P31` instance of (99% of subjects) | type assertion, not a fact about the entity |
| `P910` topic's main category (21%) | Wikipedia category housekeeping |
| `P1343` described by source (18%) | bibliographic metadata |
| `P1889` different from (15%) | disambiguation bookkeeping |
| `P279` subclass of, `P361` part of, `P2860` cites | ontology / citation plumbing |

This is the milder Wikidata analogue of the DBpedia alias pathology that killed
E-001: a structural filter is necessary and not sufficient, and the residue has to
be excluded by judgement. Having no template for a property *is* the exclusion, so
this table and the template list are the same artifact viewed twice.

## Templates

| property | name | template |
| --- | --- | --- |
| `P19` | place of birth | `{} was born in the city of` |
| `P20` | place of death | `{} died in the city of` |
| `P119` | place of burial | `{} is buried in the city of` |
| `P27` | country of citizenship | `{} holds citizenship of the country of` |
| `P17` | country | `{} is located in the country of` |
| `P131` | administrative territory | `{} is located in the administrative region of` |
| `P30` | continent | `{} is located on the continent of` |
| `P106` | occupation | `{} works professionally as a` |
| `P1412` | languages spoken | `{} speaks the language of` |
| `P69` | educated at | `{} was educated at the institution of` |
| `P166` | award received | `{} received the award named` |
| `P463` | member of | `{} is a member of the organization of` |
| `P734` | family name | `The family name of {} is` |
| `P735` | given name | `The given name of {} is` |
| `P495` | country of origin | `{} originates from the country of` |
| `P136` | genre | `The genre of {} is` |
| `P364` | original language of work | `The original language of {} is` |
| `P407` | language of work | `{} was written in the language of` |
| `P449` | original broadcaster | `{} was originally broadcast on the network of` |
| `P138` | named after | `{} was named in honour of` |
| `P178` | developer | `{} was developed by the company of` |
| `P86` | composer | `The music of {} was composed by` |
| `P750` | distributed by | `{} was distributed by the company of` |
| `P161` | cast member | `One of the actors appearing in {} is` |
| `P57` | director | `{} was directed by` |
| `P50` | author | `{} was written by the author` |

## Known weaknesses

- `P106` occupation and `P136` genre take an indefinite article, so the template
  ends `a` / `is` and phrasing pressure may dominate content.
- `P734`/`P735` family and given name are near-tautological for well-known people
  (the name is in the prompt). Kept because they are frequent, flagged because a
  high score there means little.
- Templates are English and Western-ordered; subjects are not.
