# Glossary

_Owned by: all agents. Append-only; do not edit prior entries._

Machine-read by `src/adversary.py` to expand a claim's terms before searching the
record. A claim saying "containment" must reach `P131`, or the containment miss is
not catchable. Lines of the form `- **term**: definition` are parsed; aliases go in
the `_aliases:_` trailer.

- **possession**: whether a model holds a fact at all — the true answer ranks first
  among type-matched candidates AND ranks higher with the real subject than with a
  placeholder. Precondition for any propagation claim. _aliases: holds, held, knows, knowledge_
- **containment**: the `P131` administrative-containment relation, and `P17`
  country. Labelled **mutable** in `probes/relation_modality.md` — boundaries are
  redrawn. _aliases: P131, P17, located-in, located in, admin, region, country_
- **rigid**: a relation no later event can revise — birth, death, creation. The
  outer fact of an entailment chain must be rigid or the edit admits a temporal
  escape. _aliases: P19, P20, P740, time-rigid, immutable_
- **mutable**: a relation whose value can change over time, so an edit admits a
  reconciling world and no contradiction arises. _aliases: relocation, boundaries, changes over time_
- **grounds**: the facts whose truth was a premise for the edited fact. Evidential,
  not deductive [E-002]. Distinct from consequences. _aliases: justification, justifications, premise, premises, inputs, backward_
- **consequences**: what follows from a fact. What existing ripple evaluation
  probes. _aliases: outputs, forward, entailed, downstream_
- **star**: co-predicates of a single subject — where grounds actually live.
  Wikidata asserts **no edge** between them. _aliases: co-predicate, co-predicates, siblings, same subject_
- **chain**: object-becomes-subject traversal — where consequences live, and what
  rule mining finds. _aliases: multi-hop, transitive, traversal, hops_
- **orphan**: the edit left its grounds standing and the resulting belief state is
  jointly **implausible** — graded, never binary, and never called a contradiction.
  _aliases: orphaned, orphaning_
- **template**: a cloze prompt. CounterFact's are ambiguous between temporal and
  locative readings ("died at" invites "the age of 90"), which depresses measured
  knowledge without any ignorance [T-044]. _aliases: prompt, cloze, wording, phrasing_
- **candidate set**: the distractors a true answer is ranked against. Size drives
  measured levels more than cue contamination does [T-051]. _aliases: distractors, candidates, n_candidates_
- **coverage**: the fraction of items actually scored. A rate over a silently
  biased subset is worse than no rate [E-007]. _aliases: attrition, denominator, dropped, skipped_
- **kernel**: a minimal entailing subset, from AGM. **Dropped** — the grounds
  relation is evidential, so no minimal entailing sets exist [E-002]. _aliases: kernels, contraction, AGM, entailment, minimal set_
- **suppression**: edits mask rather than overwrite; a small mask restores the
  pre-edit answer in >70% of cases. _aliases: suppress, overwrite, mask, reversible_
- **existence claim**: what hand-built sets license. A frequency claim is
  illegitimate from them [O-004]. _aliases: frequency claim, rate, hand-built, hand-picked, curated_
- **NDIF**: National Deep Inference Fabric — remote model hosting via nnsight.
  Round trips are the budget, not FLOPs. _aliases: nnsight, remote, batching, round trips_
