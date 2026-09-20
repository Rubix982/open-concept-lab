# The deletion list

Derived from R-001's negative space (verified by measurement, below) and the
R-002 exemplar passages. Each entry: **the construction, an invented example, the
replacement.** A ban with no replacement re-houses nothing and will be ignored.

Two tiers, and the split matters more than the entries. **Tier 1 is lintable and
nearly worthless on its own. Tier 2 is what actually separates research writing
from competent filler, and no word list will catch it.**

---

## What the measurement showed

Fifteen probes, run over three bodies of text (`scratchpad/negspace.py`,
`control.py`):

| Body | Words | Hits per 10k |
| --- | ---: | ---: |
| Saif's corpus (5 documents) | 20,481 | **0.0** |
| Published exemplars (ROME, Lookbacks, SFC) | 50,819 | **9.6** |
| AI-generated reports (3, `rome-neighbors/`) | 38,773 | **14.7** |

Two readings, and the second is the uncomfortable one.

**Saif's corpus is at literal zero.** Not "almost none" as R-001 estimated — zero
across all fifteen probes in 20k words. The three apparent hits were `<!-- truncate
-->` HTML comments (×2) and one descriptive use of "showcased". This is a stricter
standard than the published literature he is writing toward, and it is his own.

**But the exemplar/anti-exemplar separation is only 1.5×, and that is not a usable
signal.** ROME, Lookbacks and Sparse Feature Circuits collectively use "crucial"
13 times, "Furthermore" 9 times, and pre-announce sections 6 times. A lint tuned
to flag the AI reports would flag three ICLR/NeurIPS papers almost as hard.

So: **the deletion list is Saif's house standard, not a quality detector.** What
makes the AI reports useless is structural, and Tier 1 cannot see it. Anyone
shipping the word list alone and calling it a writing skill has built a spell
checker with opinions. Tier 2 is the actual deliverable.

---

## Tier 1 — lintable. Verified zero in the corpus.

Cheap to enforce, and worth enforcing as a floor. Just do not mistake passing it
for writing well.

**1. Throat-clearing before the point**
> ~~It is important to note that the effect disappears above layer 20.~~
**Replace with:** the sentence itself. "The effect disappears above layer 20." If
it were not worth noting it would not be in the draft.

**2. Section pre-announcement**
> ~~In this section, we will describe our evaluation methodology.~~
**Replace with:** a named commitment the reader can check off (SFC P2: "two
challenges: First… Second…"), then deliver them in order. Structure comes from
promises kept, not from narrating the document.

**3. Additive connectives as paragraph openers**
> ~~Furthermore, the attention heads also contribute.~~
**Replace with:** nothing, or a connective that names the *relation*. If the
paragraph genuinely only adds, the reader can tell. "Moreover" is a transition
that carries no information about direction.

**4. Distributed hedge adverbs**
> ~~This potentially suggests the mechanism may be somewhat localized.~~
**Replace with:** the unhedged claim, plus a specific limit in the limits section.
"The mechanism is localized to layers 3–8." / *Honest limits:* "Measured on
GPT-2-medium only; whether it holds at scale is unrun."

**5. Register verbs — delve, leverage, utilize**
> ~~We leverage causal tracing to delve into the mechanism.~~
**Replace with:** the plain verb. use, apply, examine. ROME says "We use two
approaches."

**6. Importance adjectives — crucial, pivotal, vital, paramount**
> ~~Layer 15 plays a crucial role.~~
**Replace with:** the quantity that makes it important. "Layer 15 carries AIE
8.7%, the largest of any single state."

**7. Abstraction nouns — landscape, realm, tapestry, space (as metaphor)**
> ~~the landscape of knowledge editing~~
**Replace with:** the actual set. "the eleven editing methods published since
ROME."

**8. Assertive evidentiary verbs — underscores, showcases, highlights the**
> ~~This result underscores the importance of mid-layer MLPs.~~
**Replace with:** what the result licenses, and what it does not. These verbs
claim evidential force without supplying any.

**9. Reaction adverbs — Interestingly, Surprisingly, Notably, Remarkably**
> ~~Interestingly, the effect reverses at layer 30.~~
**Replace with:** either delete, or say *to whom* it was surprising and *why*,
which is a real claim about prior expectation. ROME does the licensed version:
"is unsurprising, but … is a new discovery."

**10. Deferred numbers**
> ~~As can be seen in Table 4, performance degrades.~~
**Replace with:** the number, inline, in the sentence making the claim. "Efficacy
falls from 22.2 to 8.1." The table supports the number; it does not house it.

**11. Summary sections and recap paragraphs**
> ~~In conclusion, we have shown that…~~
**Replace with:** an artifact and a self-implicating admission (R-001 move 13), or
nothing. If the reader needs the argument restated, the argument failed.

**12. "plays a ___ role"**
> ~~Attention plays a significant role in the late site.~~
**Replace with:** the verb that says what it does. "Attention at the last token
carries the prediction."

---

## Tier 2 — structural. Not lintable. This is the actual list.

Each is stated as a **question to ask the draft**, because that is the only form
that works when no regex will do.

**13. The topic heading**
*Ask: can this heading be rewritten as a sentence with a truth value?*
> ~~## Background: localization methods and evaluation goals~~
**Replace with:** a heading that asserts, or at minimum a plain question the
section answers. "What made me withdraw it" / "Where does a language model store
its facts?" A heading that only names a subject area means the section is a
survey, not an argument. *(Anti-exemplar A1.)*

**14. The unfalsifiable paragraph**
*Ask: what in this paragraph could turn out to be false?*
> ~~Several approaches have been proposed to address edit locality, each with
> distinct trade-offs between specificity and generalization.~~
**Replace with:** a claim that takes a position and can be wrong. "MEMIT's
locality gain comes entirely from batching, and disappears at n=1." Zero is a
failing answer to this question — and it is the single defining property of the
anti-exemplar. *(A2.)*

**15. The unpriced gap**
*Ask: which gap, what would closing it cost, what would change?*
> ~~Open gaps remain in scalability and certification.~~
**Replace with:** named gap, named fix, named cost. "No standard pipeline reports
possession. The fix is cheap: report it alongside efficacy, measured on your
model." *(A3; R-001 move 20.)*

**16. The naked symbol**
*Ask: was this object named in English, by its function, before it got a symbol?*
> ~~Let δ = P\*ᵢ(o) − Pᵢ(o) for mediator i at layer l.~~
**Replace with:** ROME's ladder — name each object by what it does, bind the
symbol explicitly, define the quantity as arithmetic on already-named things,
give one concrete instance, then gloss why it means what it claims. *(ROME
P2/P3.)*

**17. The silent simplification**
*Ask: is every suppressed term acknowledged where it is suppressed?*
> *(writing f(h) throughout after having defined f(h, x), without comment)*
**Replace with:** one clause at the point of abuse. "dependence on the input x is
omitted for notational simplicity." Unannounced suppression makes the
mathematics un-checkable — the reader cannot tell an omission from an error.
*(ROME P4.)*

**18. The coined name**
*Ask: does an existing vocabulary already denote this structure exactly?*
> ~~We term this the Deferred Retrieval Coefficient (DRC).~~
**Replace with:** the borrowed word, if the borrowing is exact. Lookbacks uses
pointer, address, payload, dereference — semantics arrive installed. **Caveat
(T-009): the borrowing must be exact, not evocative.** An inexact borrowing is
worse than a coinage because it imports wrong intuitions silently.

**19. Hedging distributed instead of quarantined**
*Ask: is any qualification appearing outside the limits section?*
> ~~Results suggest the method may generalize, though further work is needed.~~
**Replace with:** the unhedged finding in the body, and every specific limit
collected in one named section, each stated as a fact about what was not done.
"I have not run the constrained measure on GPT-2-XL." *(R-001's central finding.)*

**20. Criticism delivered without bounds**
*Ask: has the scope of this criticism been fixed before the damage is described?*
> ~~CounterFact fails to verify whether models hold the facts being edited.~~
**Replace with:** bound first, then deliver. "CounterFact was built to make
insertion hard, and it does that. Possession is a different question, and it was
never the one being asked. The problem is downstream." *(R-001 move 21; SFC P1.)*

---

## How to use this

Tier 1 runs as a pass over the finished draft and takes seconds. Tier 2 is eight
questions asked of the draft's *structure* before the prose is polished — closer
to the design lenses than to copy-editing, and it is where the work is.

If only one thing survives into the skill, it is **#14**.
