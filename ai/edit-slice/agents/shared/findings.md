# Findings — edit-slice

_Owned by: Researcher. Append-only._

---

## [R-001] Finding: RippleEdits' Logical Generalization is NOT a backward probe — but claim 1 must be narrowed

_Date: 2026-09-10_

**Verified metadata (session note §9 required this).** Cohen, Biran, Yoran,
Globerson, Geva, "Evaluating the Ripple Effects of Knowledge Editing in Language
Models," **TACL 2024**, arXiv **2307.12976** (v1 Jul 2023, v2 Dec 2023).
CLAUDE.md's "TACL 2024" is correct. `rome-neighbors/readings/ripple-effects/notes.md`
says "EMNLP 2023" — **that note is wrong and should be corrected.**

**What LG actually is.** Section 3.1 defines six criteria. Logical
Generalization: "Relations in a knowledge graph satisfy certain logical
constraints. For example, the relation Sibling is symmetric and therefore if
(e,Sibling,o) is true then (o,Sibling,e) is also true." Transitive relations
(e.g. Location) are checked likewise. The logical properties are manually
specified per relation.

**The verdict.** LG probes the *logical closure of the edited triple*. It does
not probe grounds. Two cases:

- *Symmetric/inverse* — edit (Eiffel, located-in, Rome), probe (Rome, contains,
  Eiffel). This swaps the arguments of the **same triple**. It is "backward" in
  argument order, not in justification. The probed fact is not a premise of the
  edit; it is the edit restated.
- *Transitive* — (Eiffel, located-in, Rome) + (Rome, located-in, Italy) =>
  (Eiffel, located-in, Italy). This *consumes* a second fact as a premise but
  probes only the **conclusion**. Whether the premise survived is never asked.

Neither reaches the orphan case: "the Eiffel Tower was built for the 1889 Paris
Exposition" is a distinct fact about a distinct entity that made the original
location fact hold. No RippleEdits criterion probes it. Preservation and
Relation Specificity are non-interference checks on the edited subject, not
grounds checks either.

**Consequence — claim 1 is narrowed, not killed.** The defensible form is:

> Existing ripple evaluation probes the *logical closure* of the edited triple,
> forward and lateral. Inverse/symmetric probes exist (RippleEdits LG) and are
> backward in **argument order**. No benchmark probes backward in
> **justification order** — the distinct facts whose truth was a premise for the
> edited fact.

The phrase "backward probing is unexplored," unqualified, is now indefensible
and must not appear in anything Natalie or Arnab reads. This is exactly the
counterexample §9 predicted Arnab would find.

**Unresolved.** Sources disagree on the sixth criterion: ar5iv gives
Preservation (PV) and states Forgetfulness is not defined; secondary sources
list Forgetfulness (FF) and omit PV. Likely an arXiv-v1 -> TACL rename. Does not
affect the verdict (neither is a grounds probe). TODO(verify) against the TACL
version of record before publication.

**Confidence: medium.** LG's definition is confirmed by two independent sources
and the verdict follows directly from it. Downgraded from high because the raw
PDF would not extract (image-heavy) — definitions came via ar5iv, not the TACL
version of record — and the PV/FF discrepancy is open.

---

## [R-002] Finding: Lens 2 clears — not scooped, but must be repositioned against knowledge-conflict and deferral

_Date: 2026-09-10_

**Verdict: PROCEED.** No existing work partitions an edit's affected knowledge by
*whether logic determines the outcome* and surfaces the underdetermined part for
human decision. But two neighbours are closer than design.md assumed, and the
positioning sentence must change.

### What was checked

**1. Backward direction — reconfirmed by a second independent source.**
*Benchmarking Knowledge Editing using Logical Rules*, Moteu Ngoli, Kouagou,
Zahera, Ngonga Ngomo — arXiv **2606.10554**, ISWC 2025 (LNCS 16141). Extracts
logical rules from a KG for an edit, generates multi-hop questions, finds ROME
and FT show up to a **24% gap** between directly edited and *entailed* knowledge.
Entirely forward: "logical consequences", "entailed knowledge". No premises, no
grounds. Independent of Cohen et al., same conclusion — [R-001] holds.

**2. Knowledge-conflict literature — nearest neighbour, different construct.**
*Knowledge Conflicts for LLMs: A Survey*, arXiv **2403.08319**, EMNLP 2024.
Taxonomy: context-memory, inter-context, **intra-memory**. Intra-memory is where
an orphan would live, and **knowledge editing is explicitly named as a cause** of
it. But the definition is:

> "a condition where LLMs exhibit unpredictable behaviors and generate differing
> responses to inputs that are semantically equivalent but syntactically distinct"

That is **paraphrase inconsistency**, not justification contradiction. Our orphan
is not a model giving two answers to one question; it is a model giving one
answer while retaining a coherent set of beliefs entailing its negation. Distinct
construct. Confirmed absent from the survey: (a) no method identifies which facts
conflict after an edit, (b) no method distinguishes conflicts logic can resolve
from ones it cannot, (c) no human routing appears anywhere. Mitigations are
fine-tuning, plugins, output ensembles, contrastive decoding.

**3. Abstention / deferral — the differentiator is the trigger.**
Existing deferral (selective prediction, learning-to-defer, ReDAct arXiv
2604.07036) triggers on **model uncertainty**: confidence below a calibrated
threshold routes to a human or a larger model. Ours triggers on **logical
underdetermination** — the model may be perfectly confident and still be in a
position where coherence demands a choice logic cannot make. Different signal,
different cause.

> **This is exactly what design.md lens 7 baseline 1 tests.** If pre-edit
> confidence and entropy predict the contested set as well as kernel structure
> does, we have reinvented uncertainty-based deferral. Our own baseline is the
> test of whether we are distinct from this literature. That is a good position.

**4. AGM → LLM transfer — unclaimed.** *From Doyle to AGM: A Survey and an
Implementation Roadmap for Belief Change*, Almeida & Casals, arXiv **2608.14567**.
Traces Doyle & London 1980 through AGM to contemporary approaches. **Purely
symbolic** — no mention of LLMs, neural networks, or model editing anywhere.
Useful as the citation for the formalism import; not a competitor.

**5. Unexpected support for T-011.** *One Mask to Rule Them All: On Hidden Facts
after Editing and How to Find Them*, Holmov, Youssef, Schoots, Seifert — arXiv
**2605.28839** (Apr 2026). Trains a binary mask over edited weights that reverses
>70% of edits on held-out data. Key line:

> "Our finding that edits **suppress rather than overwrite** knowledge explains
> why ROME and MEMIT fail to propagate changes to related facts."

This is mechanistic evidence for our structural claim: an expansion operator that
suppresses rather than retracts is exactly what leaves grounds intact. Converges
with *Forgetting is Not Erasure* (2606.02860) on accessibility-vs-destruction.
**Cite it; do not re-derive it.**

### Consequence — the positioning sentence changes

Was: *existing work measures whether an edit propagates; this measures whether an
edit left a decision unmade.* Still true but no longer sufficient, because
intra-memory conflict is adjacent. Now:

> Prior work measures **whether** an edit produced an inconsistency — forward
> entailment gaps (2606.10554), paraphrase inconsistency (2403.08319) — or defers
> on **model uncertainty** (selective prediction). None asks whether the
> inconsistency is one **logic can resolve**, and none surfaces the
> irreducibly-underdetermined remainder for a human. The contribution is the
> partition and the queue, not the detection.

### Unresolved / not checked

- **EasyEdit** and other editing toolkits not inspected directly for a partition
  or discretion signal. Remaining scoop surface.
- **T-003** (RippleBench distance-function swap) still unchecked.
- **Metadata inconsistencies to verify before citing:** 2606.10554 lists ISWC
  **2025** with a June **2026** arXiv date; 2608.14567 carries an Aug-2026 arXiv
  ID but reports "submitted 29 May 2026". Per session-2026-09-08 §9, resolve both
  against arXiv before either enters a document that leaves the repo.

**Confidence: medium-high.** Four abstracts and one survey section read directly,
two independent confirmations of the backward gap. Downgraded from high because
the sweep was search-driven rather than a systematic venue pass, and EasyEdit was
not inspected.

---

## [R-005a] Finding: mined-rule artifact IS available — but on DBpedia and MQuAKE/MLaKE, not Wikidata/CounterFact

_Date: 2026-09-10_

**Gate result: §0 method (e) is FEASIBLE.** The critical-path dependency clears.
Two corrections to what design.md v0.5 asserted, both material.

### The artifact

- **GitHub:** `dice-group/Benchmarking-KE` — **MIT licensed**.
- **Zenodo:** v1.0.0, DOI `10.5281/zenodo.15697400`.
- **Contents of `/evaluate_rules/all_triples/`**, per README: *"The datasets used in
  the experiments, all triples, rules and multihop_qa_pairs for each dataset are
  found in /evaluate_rules/all_triples."* So the **AMIE-generated Horn rules ship
  with the repo** — we do not have to re-derive them to inspect them.
- **Regeneration pipeline is documented and runnable:** `SparqlQuery.py` (fetch
  triples) -> `java -jar amie-dev.jar` (mine rules) -> `generateQA.py` (build
  questions). Repo also vendors a `rome/` submodule.

### Correction 1 — the knowledge graph is **DBpedia**, not Wikidata

design.md v0.5 §0 and §2 say Wikidata. The repo queries **DBpedia** via SPARQL.
The earlier PDF extraction reported Wikidata; the repository is authoritative on
what was actually run. **design.md corrected.** Consequence: rigid/mutable
labelling [T-023, T-027] must be done over the **DBpedia** relation vocabulary,
not Wikidata's. Different vocabularies, different branching factors — which is
precisely the reproducibility clause in CLAUDE.md.

### Correction 2 — their edit sets are **MQuAKE and MLaKE**, not CounterFact

Rules are mined over entities extracted from MQuAKE and MLaKE. design.md lens 8
scopes v1 to CounterFact. Three options:

1. **Re-run their pipeline on CounterFact entities.** MIT licence, documented
   three-step pipeline, DBpedia is a public endpoint. Keeps our edit set, costs a
   SPARQL crawl plus an AMIE run. **Preferred.**
2. **Switch v1's edit set to MQuAKE.** Free rules, but abandons CounterFact and
   its relation inventory work, and MQuAKE is multi-hop by construction, which
   entangles the forward panel.
3. **Intersect** — use only CounterFact edits whose subjects appear in their
   triples. Cheapest, but coverage is unknown and likely thin.

Decision deferred to E-001; option 1 is the working assumption. **Note this
partially reopens [T-023]:** the relation inventory should be run over whatever
vocabulary we end up mining, and DBpedia is now the likelier target.

### RULE-KE checked off — it is a method, not a competitor

*Leveraging Logical Rules in Knowledge Editing: A Cherry on the Top* — Cheng,
Ali, Yang, Lin, Zhai, Fei, Xu, Yu, Hu, Wang; arXiv **2405.15452** (May 2024). Was
an open lead from R-004. RULE-KE *"leverages rule discovery to discover a set of
logical rules. Then, it uses these discovered rules to update knowledge about
facts highly correlated with the edit."*

**Verdict: forward, and a method.** It improves MQA performance under editing by
propagating to correlated facts. It sits in JNO's comparison class, not ours; it
does not touch premises. Lens 2 remains cleared.

But it does further narrow [T-036]: **rule discovery applied to knowledge editing
is now doubly taken** — for evaluation (2606.10554) and for method (2405.15452),
both forward. Our contribution is the **direction** and the **partition**, and
nothing else. No document may imply otherwise.

**Confidence: high** for artifact availability, licence, and contents (README read
directly). **Medium** for the DBpedia/Wikidata correction — repo and paper text
disagree and the paper body should settle it in R-005b.

---

## [R-003] Finding: 35.4% of CounterFact edits use a rigid relation — T-023's gate passes

_Date: 2026-09-10_

**The fear was unfounded.** T-023 worried that CounterFact is so dominated by
mutable relations that a naive 50-edit sample would draw almost entirely from the
row where orphaning is impossible in principle, measure a null, and be misread as
"the asymmetry is not there."

| modality | relations | edits | % |
| --- | ---: | ---: | ---: |
| **rigid** | 11 | **7,770** | **35.4%** |
| ambiguous | 3 | 2,076 | 9.5% |
| mutable | 20 | 12,073 | 55.1% |
| _total_ | 34 | 21,919 | 100% |

Rigid edits exceed the pilot's need by two orders of magnitude, and 12,073
mutable edits are available for the matched control group. **The design's
edit-selection gate passes.** Full contestable table with per-relation rationale:
`probes/relation_modality.md`. Reproducer: `src/relation_inventory.py`.

**Rigid set:** P30 continent (959), P103 native language (919), P495 country of
origin (904), P20 place of death (816), P449 original broadcaster (794), P19
place of birth (779), P740 location of formation (774), P364 original language of
work (751), P178 developer (579), P138 named after (279), P407 language of work
(216).

**Sampling requirement.** Stratify by modality and report per relation: P30 alone
is 12% of the rigid pool and would otherwise dominate a small sample.

**Ambiguous is reported, not cleaned** [T-027]. P176 manufacturer, P136 genre,
P641 sport. 9.5% measures how often the binary we imposed does not fit.

**Incidental observation, possibly useful.** CounterFact's prompt templates
sometimes encode the modality in surface form — P449 "was released on", P364 "The
original language of {} was", P495 "created in" all name a creation event. So
rigidity is partly recoverable from the template, not only from the property. A
cheap cross-check on the labels, and a candidate route to vocabularies we have
not hand-labelled (e.g. DBpedia, per R-005a).

**Threat still open, and it is E-001's job.** Rigidity is *necessary* for an
orphan, not sufficient. A rigid relation with no mined grounds in the KG yields
no kernel and therefore no probe. **Rigid-relation coverage in the DBpedia rule
set is unmeasured** — and DBpedia coverage of, say, P138 "named after" could
easily be thin. The gate that mattered has moved from "are there rigid edits" to
"do rigid edits have mined grounds."

**Confidence: high** for the counts (deterministic over the full 21,919-record
release). **Medium** for the labels, which are judgement and published as such.

---

## [E-001] Finding: §0 method (e) FAILS — the mined rules are alias tautologies

_Date: 2026-09-10 · spike, ~45min of a 3h box, stopped at first failure as designed_

**Verdict: method (e) does not work on the shipped artifact, and the failure looks
structural rather than incidental.** Fall back per design.md §0.

### What was checked

`dice-group/Benchmarking-KE`, files `rules_mquake.txt` (11,897 rules) and
`rules_mlake.txt` (778). Quality filter: support >= 10 and confidence >= 0.5.

- **12,675 rules total; median support = 1.** Most rules rest on a single
  instance, where confidence is meaningless.
- **913 survive the filter (7.2%).**

### Head coverage for our 11 rigid relations — effectively zero

| rigid relation | DBpedia head | all rules | usable |
| --- | --- | ---: | ---: |
| P19 place of birth | `birthPlace` | 22 | 7 |
| P740 location of formation | `hometown`, `locationCity` | 44 | 15 |
| P178 developer | `developer` | 55 | 8 |
| P495 country of origin | `country` | 156 | 2 |
| P20, P103, P364, P407, P138 | — | 23 | **0** |
| P449 orig. broadcaster, P30 continent | *no such predicate* | **0** | **0** |

### The killer: what those 32 "usable" rules actually say

Every single one is an **identity/alias rule**. Representative:

```
?a birthPlace ?h   ?b isPrimaryTopicOf ?h   =>   ?a birthPlace ?b
?a hometown   ?g   ?g commonName       ?b   =>   ?a hometown   ?b
?a developer  ?h   ?b primaryTopic     ?h   =>   ?a developer  ?b
```

Read it: *if a was born in ?h, and ?b is the same entity as ?h under a different
name or its Wikipedia page, then a was born in ?b.* That is **preservation of a
fact under renaming the object** — a tautology about DBpedia's redundant naming
predicates, not a justification. There is **no** justificatory content in the
rigid-head set. Not thin: zero.

### Quantified over all 913 usable rules

| category | count | % |
| --- | ---: | ---: |
| alias tautology (head repeated in body + alias link) | 607 | **66.5%** |
| head is itself an alias predicate (`name`, `isPrimaryTopicOf`, ...) | 194 | 21.2% |
| head repeated in body (self-referential) | 52 | 5.7% |
| alias predicate in body | 39 | 4.3% |
| **substantive candidate** | **21** | **2.3%** |

And the 21 survivors head on `text`, `gdpPppYear`, `p`, `topLevelDomain`,
`iso3166code` — infobox scrapings, not knowledge either.

### Why this probably is not fixable by re-running on CounterFact entities

R-005a's plan was to re-run their pipeline over CounterFact subjects. The
pathology is a property of **DBpedia's schema plus AMIE**, not of the entity set:
DBpedia carries many redundant naming/page predicates (`isPrimaryTopicOf`,
`primaryTopic`, `commonName`, `enName`, `conventionalLongName`, `url`, `voy`), and
AMIE will mine `fact + alias => fact` at confidence 1.0 for any entity set. A
different set of subjects reproduces the same rules with different constants.

### The options now

1. **Wikidata instead of DBpedia.** *New, not in the fallback chain.* CounterFact
   is Wikidata-native (P-codes; objects carry Q-ids). Wikidata keeps labels as
   labels rather than statements, so the alias-predicate explosion largely does
   not exist. Subjects need entity linking (CounterFact stores subject as a
   string), which is tractable. **Recommended next probe** — it is a genuinely
   different proposition, not a retry.
2. **Fall back to method (c)**, in-context counterfactual as discovery, per the
   design's own chain (e) -> (c) -> (b). Now looks relatively better: the model at
   least holds world knowledge, whereas this KG slice holds naming redundancy.
3. Re-run their pipeline on CounterFact entities. **Not recommended** — see above.

### A concern about 2606.10554 that we must not overstate but must record

Their benchmark **generates its multi-hop questions from these rules**. If the
usable rule set is 88%+ naming/aliasing artifacts, then a substantial part of what
that benchmark measures may be **subject-aliasing robustness** — which RippleEdits
already covers as its SA criterion — rather than logical entailment. Their
reported 24% gap between direct and "entailed" knowledge may then not be an
entailment gap.

**This weakens [R-002]'s claim that 2606.10554 independently reconfirms claim 1.**
It still shows nobody probes backward, but as evidence about *forward entailment*
it is softer than recorded. Do not cite the 24% figure as an entailment result
until their generated questions have been inspected directly. Added to R-005b.

**Confidence: high** for the rule statistics (deterministic over the released
files). **Medium** for "not fixable by re-running" — an inference from DBpedia's
schema, not yet tested. **Low-medium** for the concern about their benchmark: I
inspected the rules, not the generated questions.

---

## [E-002] Finding: Wikidata carries real grounds — but they are *evidential*, not deductive

_Date: 2026-09-10 · spike, ~1h of a 3h box_

**Verdict: method (e) is alive on Wikidata.** Steps 1 and 2 pass. But what we
found are not AGM kernels, and that has consequences.

### Step 1 — entity coverage passes decisively

55 rigid-relation edits, 5 per relation, seed 1538.

- **Entity-linked: 54/55 (98%)** by plain `wbsearchentities` on the subject string.
- **Median properties per subject: 14–67**; statements 15–96. Not sparse.
- **Wikidata asserts the edited property for 43/55 (78%)** — 5/5 for P19, P20,
  P407, P740; only 2/5 for P103 and P364. Where Wikidata lacks the fact, it cannot
  supply its grounds either, so effective coverage is ~78% and uneven.
- 928 distinct properties across 54 subjects.

**The alias pathology does not recur, and the filter is principled.** Wikidata's
structural analogue of DBpedia's naming predicates is external identifiers
(P646 Freebase, P214 VIAF, P244 LoC, P345 IMDb) and media (P18, P373) — which
dominate the raw property counts. Restricting to **`wikibase-item` datatype**
statements removes them by datatype rather than by hand-picking. It is a large
cut: Perec 24 item-valued of 192 total, Yakuza 21 of 70, McLane 20 of 52.

### Step 2 — the grounds are there, and they read correctly

| edit | grounds left intact by the edit |
| --- | --- |
| **P20** Louis McLane, died Baltimore -> Barcelona | **P119 place of burial = Green Mount Cemetery** (in Baltimore) |
| **P178** Yakuza, developer Sega -> IBM | **P123 publisher = Sega**; P287 designed by / P162 producer = Nagoshi; P495 origin Japan |
| **P138** London City Airport, named after London -> Hamburg | **P931 place served = London**; P131 in Newham; P7959 historic county London |
| **P103** Georges Perec, native language French -> Russian | **P19 born 19th arr. Paris**; **P27 citizenship France**; P6886 writing language French |
| **P19** Seija Simola, born Helsinki -> Milwaukee | P27 citizenship Finland; P1412 speaks Finnish; P20 died Vantaa |

These are recognisable grounds, not co-occurrence noise. Edit the head and each
one is left standing and now anomalous. **This is the orphan, visible in data,
for the first time in the project.**

### The consequence — and it is conceptual, not technical

**"Buried in Green Mount Cemetery" does not *entail* "died in Baltimore."** It is
strong evidential support. Same for publisher->developer, place-served->named-after.
Almost nothing here is a deductive rule.

So:

1. **AMIE-style rule mining may be the wrong instrument even on Wikidata.** What
   the data supports is **property-pair** statistics (P119 co-varies with P20
   across many subjects), not instance-level Horn rules. That is a simpler and
   more direct method than mining, and it sidesteps E-001's failure mode entirely.
2. **[T-013] is now live, with data.** AGM kernels presuppose entailment. Real
   grounds in a KG are evidential. Either we weaken "kernel" to "evidential
   support set" and lose AGM's crispness, or we restrict to the deductive subset —
   which is small and drifts back toward RippleEdits' territory.
3. **But this strengthens the T-025/T-028 framing rather than weakening it.**
   Evidential support is *precisely* the case where logic underdetermines which
   belief to give up. If grounds were deductive, a machine could compute the
   contraction and there would be no discretion to surface. The design is *more*
   coherent with evidential grounds than with deductive ones. The project's thesis
   survives the loss of its formalism's crispness — and arguably needed it.

### Recommended method change

Replace instance-level Horn mining with **property-pair evidential support**: for
edited property P, find properties Q whose values co-vary with P's across a
Wikidata sample; the ground set for an edit is the subject's Q-statements. Cheaper
than AMIE, no alias pathology, directly interpretable, and publishable as a
contestable table like `probes/relation_modality.md`.

**Confidence: high** for steps 1 and 2 (measured, and the examples are legible).
**Medium** for the recommendation — property-pair co-variation is not yet
computed, only conjectured from five hand-read cases.

---

## [E-003] Finding: possession is real, scale fixes it — and the field's standard test overstates it

> **SUPERSEDED 2026-09-10 — measure contaminated by surface plausibility.**
> Distractors were drawn at random from the relation's value pool, so a model with
> no entity knowledge can score well from morphology and base rates alone:
> "Darrieux" looks French, "Yakuza" looks Japanese. The ordering below may still
> hold, but it is not established by this design. Superseded by E-005, which mines
> hard negatives from the model's own subject-free prior and reports lift over it.
> The **measurement critique** (75% / 61% / 12% disagreement, and the template
> ambiguity behind it) is unaffected — that compares measures on identical items
> and does not depend on distractor quality.

_Date: 2026-09-10 · 165 rigid-relation items, seed 1538, identical distractor sets per item_

**Verdict: [T-039] confirmed and [O-004] empirically vindicated.** Possession is a
genuine gate, GPT-2 fails it, and a large model clears it.

### The headline

| model | top-1 | top-3 |
| --- | ---: | ---: |
| gpt2-medium (355M) | 61% | 79% |
| gpt2-large (774M) | 62% | 83% |
| **Llama-3.1-70B** | **93%** | **98%** |

**Scaling within GPT-2 did nothing (61 -> 62). Scaling 90x did everything (-> 93).**
Worth stating because the medium->large null is easy to misread as "scale does not
fix possession" — it looked flat only because the step was too small. Gains
concentrate where GPT-2 was weakest: P449 original broadcaster 27% -> 93%, P19
place of birth 47% -> 87%, P364 53% -> 93%, P740 60% -> 100%.

**Consequence for edit selection.** At GPT-2 scale ~39% of rigid-relation edits
target facts the model does not hold, and any orphan measured on those is an
artifact of ignorance rather than of editing. At 70B it is 7%. Edit sets must be
filtered by possession before any orphan rate is reported.

### The measurement result, which may matter more

Three measures over the same 165 items disagree wildly:

| measure | gpt2-medium | what it actually measures |
| --- | ---: | --- |
| `P(target_true) > P(target_new)` — **the editing literature's standard pre-edit condition** | 75% | a forced binary choice; too easy |
| **constrained rank, top-1** (ours) | **61%** | possession |
| unconstrained top-1 generation | 12% | possession *and* template ambiguity, confounded |

The unconstrained collapse is not ignorance. CounterFact templates are ambiguous
between temporal and locative readings: *"Karolos Koun died at"* -> `" the age of
90"`, *"El Filibusterismo, formulated in"* -> `" the early 1970s"`. The model
answers a different question and scores zero while knowing the answer — Koun/Athens
ranks **1/10** under constraint on the same model that scored it zero unconstrained.

Constraining candidates to objects attested for the **same relation** fixes both
ends: type-matching means template ambiguity cannot express itself, and the choice
stays hard enough to discriminate at 70B.

**So the standard pre-edit condition overstates possession.** Anyone selecting edit
sets with it is admitting facts the model does not hold. This is cheap to fix and
we should say so.

### Open — the gap this creates

Possession was measured on Llama-70B, but the model we intend to **edit** is
GPT-J-6B, whose possession is unmeasured. If GPT-J sits nearer GPT-2 (61%) than
Llama (93%), the possession argument has moved the problem rather than solved it:
we would be editing a model that does not hold its own grounds. Sweep running.

If GPT-J is low the choice is: get ROME working on a 70B model (hyperparameters and
second-moment statistics we do not have), or accept a possession ceiling on the edit
target and report it as a limitation.

### Caveats

- Possession here is of the **edited head**, not of **grounds**. Grounds are more
  obscure than CounterFact's curated facts, so 93% is an optimistic upper bound for
  them. Ground possession is E-004.
- 10 candidates per item. A larger candidate set is harder and would lower all
  three models; the ordering should be stable but the levels are not absolute.
- CounterFact is a curated set of facts models tend to know — not a random sample
  of world knowledge.

**Confidence: high** for the ordering and the measurement critique (paired design,
identical items and distractors). **Medium** for the absolute levels, which depend
on candidate-set size.

---

## [E-003b] Finding: GPT-J-6B possession is 73% — usable as the edit target, with filtering

> **SUPERSEDED 2026-09-10** — same defect as E-003 (random distractors admit
> surface-cue scoring). The *decision* it supported — pilot runs on GPT-J, audit
> model must be the edited model — does not depend on the absolute levels and
> stands. The numbers do not.

_Date: 2026-09-10 · same 165 items, same distractors_

**Answers [T-045].** The hard fork is avoided: we do not need ROME on a 70B model.

| model | params | top-1 | top-3 |
| --- | ---: | ---: | ---: |
| gpt2-medium | 355M | 61% | 79% |
| gpt2-large | 774M | 62% | 83% |
| **EleutherAI/gpt-j-6b** | **6B** | **73%** | **90%** |
| meta-llama/Llama-3.1-70B | 70B | 93% | 98% |

GPT-J sits between the two: +11pp over GPT-2, -20pp under Llama. So it is neither
"nearly GPT-2" (which would have sunk it) nor adequate unfiltered.

**Decision this supports.** Run the pilot **entirely on GPT-J-6B** — possession
filter, edit, and probe on the same model — with edits restricted to facts GPT-J
demonstrably holds. 73% of the 7,770 rigid pool is ~5,700 candidate edits, two
orders of magnitude more than a 50-edit pilot needs. GPT-J has published ROME
hyperparameters and rome-neighbors already runs that stack, so this is both the
path of least resistance and now the empirically justified one.

**A coherence point worth stating explicitly.** Measuring possession on Llama-70B
while editing GPT-J would be incoherent — the audit model must be the edited model.
Llama-70B's role is to establish that possession is **scale-dependent**, which is
context and a control, not the pilot's subject.

**Where GPT-J is weakest, and it is inconvenient.** P19 place of birth 53%, P20
place of death 60%, P740 location of formation 60%. Those are precisely the
relations with the richest grounds (burial place, citizenship, family) — so the
relations most useful for orphan probing are the ones GPT-J holds least reliably.
Edit selection must be stratified by relation *and* filtered by possession, or the
usable pool will be quietly dominated by P138/P495, which are easy but
ground-poor.

**The possession curve.** 61% -> 62% -> 73% -> 93% across 355M -> 774M -> 6B ->
70B. Strongly non-linear, flat inside the GPT-2 family and stepping at scale
boundaries. This is a publishable side-figure in its own right: *possession of
curated factual benchmarks is not saturated at small scale, and benchmark
selection using the standard pre-edit condition hides that* [T-044].

**Confidence: high** for the ordering (paired design, identical items and
distractors across all four models). **Medium** for absolute levels — 10 candidates
per item; a larger candidate set would lower all four.

---

## [E-004] Finding: joint possession is 69% — the pilot has a pool, but the ground number is confounded

> **SUPERSEDED 2026-09-10 — the measure did not discriminate.** Top-3 was 100% on
> every property: a test everything passes separates nothing. Three causes, all
> design faults rather than findings: only 9 distractors, drawn at random rather
> than as hard negatives; no subject-free baseline, so surface plausibility is
> indistinguishable from knowledge; and coarse-grained properties (countries,
> languages) dominating the surviving set. The **attrition analysis** — that
> template coverage, not ground availability, throttles the sample — is unaffected
> and stands. Superseded by E-005.

_Date: 2026-09-10 · GPT-J-6B, 116 (subject, ground) pairs over 89 subjects, 13 properties_

**Verdict: the gate passes.** Joint possession — head held **and** at least one
ground held, same subject, both top-1 by constrained rank — is **61/89 = 69%**,
comfortably above the ~50% threshold the ticket set for pool collapse.

| measure | GPT-J-6B |
| --- | ---: |
| head possession [E-003b] | 73% |
| **ground possession** | **82%** top-1, 100% top-3 |
| **joint (head AND >=1 ground)** | **69%** |

### The prediction was wrong, and the reason matters

The ticket argued 93%/73% were **ceilings** for grounds, because CounterFact was
curated for familiarity while grounds are whatever Wikidata asserts. Grounds came
back **higher** than heads (82% vs 73%). That is not a refutation of the argument —
it is a **granularity confound** in which properties survived the filters.

| surviving ground property | n | top-1 | grain |
| --- | ---: | ---: | --- |
| P495 country of origin | 33 | 85% | coarse |
| P17 country | 12 | 100% | coarse |
| P1412 languages spoken | 13 | 92% | coarse |
| P364 original language | 8 | 100% | coarse |
| P407 language of work | 7 | 100% | coarse |
| P27 country of citizenship | 14 | 71% | coarse |
| **P131 administrative territory** | 15 | **53%** | **fine** |

Grounds skew to **countries and languages** — small answer spaces. Heads skew to
**cities** (P19 birth 53%, P20 death 60%, P740 formation 60%). The single
fine-grained ground property, P131, scores worst of all at 53% — exactly the
pattern the grain hypothesis predicts. **So head-vs-ground is not a fair
comparison as measured, and the 82% must not be reported as "grounds are better
known than heads".**

### Two further caveats that bound the number

1. **Top-3 is 100% across every property.** The measure is at ceiling for grounds
   and therefore not discriminating. With 10 candidates drawn from a pool of
   countries or languages, the task is close to trivial. A larger and
   grain-matched candidate set is needed before the ground figure means much.
2. **Attrition is heavy and template-driven.** 165 subjects -> 89 with any usable
   ground probe; 116 pairs over 13 properties, from 26 written templates. The
   binding constraint is **template coverage, not ground availability** — the
   median subject has 8 grounds (E-004 step 1) but most sit on properties we did
   not template. This is the opposite of what the ticket expected, and it is a
   cheap lever: more templates directly widens the pool.

### What this licenses

- The pilot has an adequate pool. ~69% of possession-filtered rigid edits carry at
  least one held ground, so orphan probing has something to probe.
- It does **not** license a claim that grounds are well known. Grain-matched
  distractors are required first.

**Confidence: high** for the joint figure as defined (paired, same model, same
measure). **Low** for ground possession as an absolute — confounded by grain and
sitting at ceiling on top-3.

---

## [E-005] Finding: possession re-measured — 56/74/79/85 across 6B-405B, and scale buys only the hard relations

_Date: 2026-09-11 · 165 rigid-relation items x 50 candidates x 2 arms, all four models complete_

Replaces the superseded E-003/E-003b/E-004 numbers. Possession = the true answer
ranks **first** among 50 type-matched candidates **and** ranks higher with the real
subject than with the subject replaced by `X` (positive lift). A model riding the
template's base rate scores identically in both arms and earns nothing.

| model | params | naive top-1 | prior alone | **POSSESSED** | median lift |
| --- | ---: | ---: | ---: | ---: | ---: |
| gpt-j-6b | 6B | 59% | 5% | **56%** | +5 |
| Llama-3.1-8B | 8B | 78% | 4% | **74%** | +6 |
| Llama-3.1-70B | 70B | 83% | 4% | **79%** | +7 |
| Llama-3.1-405B | 405B | 90% | 5% | **85%** | +8 |

Monotonic, decelerating, and **not saturated at 405B** — 15% of *curated*
CounterFact facts are still not held by the largest model on NDIF.

### Correction to the E-005 RCA — the diagnosis was partly wrong

The RCA attributed E-003/E-004's inflation to **surface-cue contamination** and
prescribed the lift control as the fix. The data does not support that weighting:
naive top-1 and possessed differ by only **3-5 points** at 50 candidates, so
subtracting the prior corrects almost nothing. The inflation came overwhelmingly
from the **candidate set being 10 instead of 50** — easy negatives, not base rates.

Both defects were real and both needed fixing. The RCA's causal story was wrong
and is corrected here rather than left standing. The lift control is retained on
its merits: it is what establishes that the 4-5% prior baseline is genuinely weak,
so these numbers are not template-guessable. It is simply not where the correction
came from.

### Scale buys the hard relations, not the easy ones

| relation | 6B | 8B | 70B | 405B |
| --- | ---: | ---: | ---: | ---: |
| P103 native language | 80% | 93% | 93% | 93% |
| P407 language of work | 80% | 80% | 80% | 87% |
| P178 developer | 80% | 80% | 80% | 87% |
| **P449 original broadcaster** | **13%** | 40% | 67% | **87%** |
| **P740 location of formation** | **40%** | 67% | 93% | 87% |
| **P495 country of origin** | **47%** | 87% | 93% | 87% |
| **P19 place of birth** | **13%** | 40% | 53% | **53%** |

Relations already known at 6B stay flat. All the movement is in the low
performers. The aggregate curve is therefore not "everything gets better" — it is
a small set of hard relations being acquired.

### The pilot problem, now sharper

**P19 place of birth tops out at 53% even at 405B**, and GPT-J holds **13%**.
P19 and P20 carry the richest grounds — burial place, citizenship, family
(E-004 step 1). So the relation most informative for orphan probing is the one
every model holds worst, and the intended edit target holds it barely at all.

This reopens [E-003b]'s conclusion that GPT-J is usable with filtering. Filtering
GPT-J to what it holds removes most ground-rich relations, which defeats the
purpose of the filter. Live options, neither free:

1. **ROME on Llama-3.1-8B** — possession 74%, P19 at 40%, three times GPT-J's.
   Requires layer-choice hyperparameters and second-moment statistics we do not
   have, but 8B is tractable to compute them for.
2. **Re-select edits toward relations GPT-J holds** (P103, P138, P178, P407 at
   80-87%) and accept that those relations are ground-poor.
3. Abandon the possession filter and report orphan rates contaminated by
   ignorance — rejected; that is the artifact the whole gate exists to prevent.

### Caveats

- 50 candidates, not the full object space. Levels would fall further with more.
- Possession here is of the **head**. Ground possession under the corrected measure
  has not been re-run; E-004's 82% used the superseded design and is withdrawn.
- The measure separates "used the subject" from "used the template". It does not
  separate a memorised fact from inference off the subject's morphology.

**Confidence: high** for the ordering and the per-relation pattern (paired design,
identical items and candidate sets across all four models, complete n=165 each).
**Medium** for absolute levels, which depend on candidate-set size.

---

## [E-006] Finding: ROME on Llama-3.1-8B via NDIF is feasible — both required primitives work

_Date: 2026-09-11 · spike, ~1h of a 4h box_

**Verdict: option 1 of [T-050] is available.** The blocking concern was that NDIF
hosts one shared copy of each model, so a weight edit cannot be persisted. It does
not need to be.

### Unknown 1 — can the edit be applied at all? YES

ROME's update is **rank-one on the MLP output projection**, so its effect on any
input is an additive term at that layer. Applied as an activation intervention
rather than a weight write:

```
baseline  "The Eiffel Tower is in the city of" -> " Paris"
perturbed  (noise added to layers[5].mlp.down_proj output) -> "acons"
```

The intervention lands and propagates. A real rank-one delta substitutes directly
for the noise.

### Unknown 1b — can v* be optimised? YES

ROME fits the target vector by gradient descent through the frozen model. Backward
passes run remotely: gradient norm **17.875** at `layers[5].mlp.down_proj`. So the
optimisation does not require local weights.

### Unknown 2 — second-moment statistics: tractable

Llama-3.1-8B: 32 layers, d_model 4096, **d_mlp 14336**, vocab 128256.

- C is 14336x14336 = 206M entries = **0.82 GB fp32**, computed and held locally.
- Collecting the keys to build it: 0.09 GB for 3k tokens, 0.29 GB for 10k, 2.87 GB
  for the 100k the original ROME used. Chunked downloads, one-time cost.

rome-neighbors' GPT-2 artifact is `...mom2_3000.npz`, so a 3k-sample estimate was
considered adequate there. We should check sensitivity rather than assume.

### Unknown 3 — layer choice: needs determining, not blocking

ROME uses layer 5 of GPT-J's 28 (~18% depth). Scaled to 32 layers that is ~layer 6,
but relative depth is a guess; causal tracing would identify it properly. Not a
blocker for feasibility, and it is a parameter to publish contestable [T-027].

### An unexpected advantage of the intervention formulation

Because the edit is re-applied per forward pass rather than persisted, there is no
edited-model artifact to store or reload. Consequences, all favourable:

- **Paired pre/post on identical infrastructure.** Edit on and edit off are two
  traces against the same hosted weights, so nothing drifts between conditions.
  The usual workflow reloads or re-edits a model between arms.
- **Perfectly reproducible** — the edit is a function of its parameters, recomputed
  each time rather than a checkpoint that can silently diverge.
- **No shared-state risk.** We cannot corrupt the model other NDIF users are
  running, because we never write to it.

### Scope note

Applying an existing editing method is not "proposing or tuning an editing method",
which the charter bans. ROME here is the **perturbation whose effects we audit**,
not a contribution.

### What this does NOT establish

The primitives work; a complete ROME edit has not been run. Unverified: that the
fitted v* actually installs the target fact, that the layer choice is right for
this architecture, and that an unwhitened update (skipping mom2) would be
acceptable if the covariance proves expensive.

**Confidence: high** for both primitives (measured directly). **Medium** for the
covariance cost estimate, which assumes chunked collection works at these sizes.

---

## [R-006] Finding: the diagnostic framing is FALSE — CounterFact does verify possession, with a weak test

_Date: 2026-09-11 · executes [T-047], lens 2 against the factual-probing literature_

**Verdict: drop "editing benchmarks measure propagation into knowledge they never
verified was there."** It is not true, and a reviewer would refute it from the ROME
paper itself. What survives is narrower, sharper, and still ours.

### The decisive fact

CounterFact's construction, from Meng et al. (arXiv 2202.05262) verbatim:

> "these counterfactuals start with low scores compared to the correct facts
> (s,r,o^c)"

and their own critique of prior work:

> "standard model-editing benchmarks underestimate difficulty by often testing only
> proposals that the model previously scored as likely"

So records **were** filtered on a possession-like criterion: P(true) > P(counterfactual)
pre-edit. That is exactly the two-way comparison we critiqued in [T-044]. The check
exists. It is simply the weak one.

Efficacy Score is defined post-edit as P(o*) > P(o^c), the same two-way shape.

### What still survives, and it is worth more than the false version

1. **The existing filter overstates possession.** Two-way P(true) > P(counterfactual)
   is a forced binary choice. Under constrained rank against 50 type-matched
   candidates, possession is 56% / 74% / 79% / 85% at 6B / 8B / 70B / 405B [E-005].
   The check the field runs and the thing it is taken to establish are not the same
   quantity.
2. **The filter is model-relative and does not transfer — but the dataset does.**
   CounterFact's 21,919 records were filtered once, against the authors' model in
   2022. Everyone since applies the same fixed records to GPT-J, Llama, Qwen and
   the rest, where that guarantee simply does not hold. Our own data shows the
   consequence directly: GPT-J holds **13%** of P19 place of birth. This is the
   strongest claim we have and it is unclaimed.
3. **Candidate-set size drives the inflation more than cue contamination**
   [T-051]: 10 candidates to 50 moved naive top-1 from 61% to 39% on gpt2-medium,
   while subtracting the subject-free prior moved it only 3-5 points.
4. **CounterFact's templates are ambiguous** between temporal and locative readings
   ("died at" -> "the age of 90"). Novel *for this dataset*; see the caveat below.

### What is taken, and must be cited rather than re-derived

- **Prompt sensitivity and phrasing-over-knowledge** is long established in the
  factual-probing line: LAMA (Petroni et al. 2019) and its critiques, including
  "Factual Probing Is [MASK]: Learning vs. Learning to Recall" (arXiv 2104.05240)
  and causal-view analyses (arXiv 2203.12258). The position that models "predict
  based on correlation between surface forms rather than infer according to facts"
  is published. Our template-ambiguity result is an **instance** of a known
  phenomenon located in CounterFact, not a new phenomenon.
- **"Editing evaluation is flawed" is crowded**: "Benchmarking and Rethinking
  Knowledge Editing for LLMs" (2505.18690), AKEW (2402.18909), UniEdit. Do not
  enter that space generically.
- **Perplexingness** (2406.17253) stratifies edits by conflict with conceptual
  hierarchy — adjacent but a different variable from possession. Not a competitor.

### Consequence for the framing

Adopt the **descriptive** framing, not the diagnostic one:

> **Possession as a precondition: the filter knowledge-editing benchmarks apply is
> model-relative and weaker than assumed, and the facts it admits are not held
> 15-44% of the time on the models actually being edited.**

Less aggressive than "nobody checks". Defensible, and it points at the transfer
problem — a fixed 2022-filtered dataset reused across models — which is concrete,
measurable, and unclaimed.

**Confidence: high** that the diagnostic framing is false (quoted from the source
paper). **Medium** on the survivors' novelty — searched, not systematically
swept, and 2505.18690 would not render for direct reading.

### Open

2505.18690 "Benchmarking and Rethinking Knowledge Editing" could not be read (PDF
would not extract, OpenReview behind a verification wall). It is the nearest
remaining competitor and must be read before any write-up.

---

## [R-007] Finding: 2505.18690 does not take T-054 — and hands us one adversary point

_Date: 2026-09-11 · closes the gap left open by [R-006]_

**Verdict: the nearest competitor does not claim our result.** T-054 stands.

"Benchmarking and Rethinking Knowledge Editing for Large Language Models" — He,
Song, Wang, Sun; arXiv **2505.18690**, May 2025.

### What they actually critique

Their four flaws are: inconsistent evaluation objectives and setups; **teacher-forced
decoding rather than realistic autoregressive inference**; fact-level datasets only;
and insufficient multi-edit assessment. They add event-based (ELKEN) and
general-purpose datasets, evaluate across instruct and reasoning models, and
benchmark everything against a context-based baseline, **Selective Contextual
Reasoning (SCR)**, which beats every parameter-based editor they test.

Models: Llama-2-7B-Chat, Llama-3.1-8B-Instruct, Mistral-7B-Instruct,
DeepSeek-R1-Distill-Llama-8B. Datasets: ZsRE, WikiDatacounterfact, ELKEN.

### What they do not do — verbatim from the read

> "The authors evaluate performance before and after edits but don't analyze
> whether baseline knowledge influenced editing outcomes."

and

> "The paper does not address whether CounterFact construction transfers across
> models or remains model-specific."

So possession is not measured, and the model-relative transfer problem [T-054] is
not raised. **Our claim is unclaimed by the closest paper to it.**

### The adversary point they hand us, and it is sharp

Their second flaw is **teacher-forced decoding**. Our possession measure teacher-forces
candidate continuations to compute log-probs, so a reviewer can say: "2505.18690
shows teacher-forcing overstates performance; your possession numbers inherit that."

**Pre-emption, and we are unusually well placed:** we measured both arms already.

| measure | gpt2-medium | what it is |
| --- | ---: | --- |
| two-way P(true) > P(new) | 75% | the field's filter |
| constrained rank, teacher-forced | 61% | ours |
| unconstrained top-1 **generation** | 12% | fully autoregressive |

The autoregressive number is *far lower*, and we already established it is depressed
by CounterFact's template ambiguity rather than by ignorance [T-044]. So we can
report the spread and argue the case explicitly instead of being caught by it.
Constrained teacher-forcing is the right instrument for **possession** — the
question is whether the knowledge is present, not whether the model would
spontaneously emit it — and the generation number bounds it from below.

### One piece of context worth carrying, not burying

They find **parameter-based editing performs poorly under realistic conditions**
while a simple context-based baseline outperforms it everywhere. That does not
threaten our claim, but it does bear on the project's motivation: if editing is
losing to context on the merits, auditing editing matters less as a deployment
concern and more as a question about where knowledge lives. Our framing should not
lean on editing being the future.

**Confidence: high** that they do not measure possession or raise the transfer
problem (abstract read verbatim, body searched directly for pre-edit/prior-knowledge
discussion). **Medium** on whether some later paper does — this closes the nearest
competitor, not the field.

---

## [T-055] Finding: coordination lift is a set-level type diagnostic, not a per-candidate filter

_Date: 2026-09-11 · GPT-J-6B, two contrast sets_

**Motivation.** The possession measure assumes its distractors are type-matched;
that assumption was never checked. Coordination should test it — same-type
expressions coordinate under one predicate, cross-type ones produce zeugma.

**Measured.** Coordination lift, `log P(c | prompt + anchor + " and") -
log P(c | prompt)`:

| contrast | median SAME | median CROSS | separation |
| --- | ---: | ---: | ---: |
| *"The archivist shredded the filing cabinet and ..."* (genuine zeugma) | +0.55 | −1.84 | **+2.39** |
| *"Karolos Koun died at Naples and ..."* (CounterFact template) | −0.91 | −2.52 | **+1.61** |

The direction is right and the set-level statistic is usable.

**But it does not classify individual candidates.** "dust jacket" (−3.52) and
"spine label" (−2.16) are same-type yet score below *every* cross-type item.
Coordination lift measures the plausibility of **joint predication**, which
includes type agreement but is not limited to it — one does not shred a dust jacket
alongside a filing cabinet for reasons of plausibility, not ontology. The
per-candidate flag produced both false positives and false negatives.

**Second limitation, and it bites where we most wanted the test.** Where a
template's ambiguity is *idiomatic*, coordination is barely anomalous: *"died at
Naples and at the age of 90"* is standard obituary English. Conventionalised
ambiguity — exactly the kind [T-044] found in CounterFact — is the case this test
is weakest on.

**Consequence.** Shipped as a **set-level** diagnostic (`separation`), with
per-candidate flagging demoted to advisory (`suspects`). The design.md claim is
narrowed accordingly: we can report whether a candidate set is homogeneous, not
scrub individual contaminants.

**Two bugs found and fixed in the testing:** the anchor was initially included in
its own candidate list, producing a spurious +4.91 from repetition; and the first
contrast pair was badly chosen for the reason above.

**Confidence: high** for the separation figures (direct measurement, two contrasts).
**Medium** for generality — two prompts, one model.

---

## [D-002] Finding: CounterFact has NO possession filter — R-006 was wrong, verified from the primary source

_Date: 2026-09-14 · read from the ROME paper text, `lookback-research/docs/rome.txt`_

**This reverses [R-006].** I concluded there that "CounterFact does verify
possession, with a weak test", from §3.3's sentence about counterfactuals starting
with low scores. That was a misreading: the sentence states an *aspiration about
difficulty*, and the construction appendix shows how it was actually implemented —
without any model.

### Evidence 1 — Appendix D, construction is model-independent

> "Each record in CounterFact is derived from a corresponding entry in PARAREL
> (Elazar et al., 2021a) containing a knowledge tuple t_c = (s, r, o_c) and
> hand-curated prompt templates T(r) ... **Solely using the PARAREL entry**, we
> derive two elements. A requested rewrite is represented as {s, r, o_c, o*, p*},
> where p* ~ P(s,r) is the sole rewriting prompt, and **o\* is drawn from a
> weighted sample of all PARAREL tuples with the predicate (r, ·)**."

The counterfactual target is obtained by sampling another object of the same
relation. Specificity prompts come from a Wikidata SPARQL query. **No model is
consulted anywhere in construction.** "Solely using the PARAREL entry" is explicit.

So §3.3's "these counterfactuals start with low scores compared to the correct
facts" is a claim about what the sampling yields, not a filtering step — and the
Hase et al. (2021) critique it cites is motivation, not method.

### Evidence 2 — their own table says so

Table 4, the **unedited GPT-2 XL** baseline row: **ES = 22.2**, EM = −4.8.

ES is the fraction of cases with P[o*] > P[o_c]. So on the paper's own primary
model, before any edit, **22.2% of CounterFact records already favour the false
target**. Had records been filtered so the model prefers the true fact, this would
be ~0.

Equivalently: GPT-2-XL prefers the true answer in **77.8%** of records — close to
our 75% two-way figure on gpt2-medium, and consistent with no model-specific
selection having occurred.

### What this settles

**[T-057] is answered without running anything.** The decisive experiment was to
check whether GPT-2-XL passes the two-way test near 100%. The paper reports the
number: it does not. No local run needed.

**[T-054] was wrong in its mechanism.** The story was "a benchmark outliving its
calibration". There was no calibration. The correct statement is simpler and
stronger: **CounterFact contains no possession check at all**, so every propagation
result computed on it is conditional on a premise nobody established — not for
GPT-J, not for Llama, and not for GPT-2-XL either.

**The framing R-006 made me withdraw is restored, and now verified from source
rather than asserted.** "Editing benchmarks measure propagation into knowledge they
never verified was there" is accurate for CounterFact.

### What our measurement adds on top

The paper's own 22.2% understates the shortfall, because ES is the forced binary
choice. Under constrained rank with a prior control, possession is **56%** on
GPT-J — a **44% shortfall**, twice what the two-way number suggests, and the gap
widens on exactly the relations a propagation study would want (P19 place of birth:
13%).

### My error, recorded

I read §3.3 in isolation and treated an aspiration as a mechanism, then wrote a
findings entry withdrawing a correct claim. The appendix was three pages away in
the same paper. **Two lens-2 passes did not catch it because both searched for
competing work rather than re-reading the primary source.** The lesson is narrow
and practical: when a claim turns on what a paper *did*, read its methods appendix
before concluding from its prose.

**Confidence: high.** Two independent pieces of evidence from the paper itself —
an explicit construction description and a reported baseline number — agreeing.

## [R-010] Finding: the WHY gate narrows sharply — two of three proposed contributions are taken

_Date: 2026-09-18 · verified against sources, not recalled_

Run before building the probing taxonomy the project was about to pivot to. Three
prior-art hits, two of them direct.

### 1 · Surface form competition — E-011's phenomenon is known

**Holtzman, West, Shwartz, Choi, Zettlemoyer — "Surface Form Competition: Why the
Highest Probability Answer Isn't Always Right", EMNLP 2021, arXiv:2104.08315.**

Different surface forms of the same concept compete for finite probability mass, so
ranking answer options by string probability is systematically distorted. Their fix is
**Domain Conditional PMI**: reweight each option by its a priori likelihood in the task
context.

This is [E-011] — `" United States"` losing to bare-name countries because of its form,
not the model's knowledge. And **our placeholder lift test is essentially PMI against a
neutral prompt**: `log P(a|prompt) − log P(a|placeholder)`. [E-012]'s paired-subject
AUROC is a rank-based cousin of the same correction. We re-derived a 2021 result and
its standard remedy. **No artifact may present E-011 as novel.**

### 2 · Knowledge status × edit success — the proposed contribution is taken

**"Diagnosing Model Editing via Knowledge Spectrum", arXiv:2509.17482, 22 Sept 2025.**

Classifies target knowledge by **Popularity** (Wikipedia pageviews), **Familiarity**
(Known/Unknown pre-edit, SliCK-style generation probing) and **Question Type**, then
measures edit success across them. On **LLaMA-3.1-8B** — our model — with MEMIT,
AlphaEdit and FT. Finds **Unknown facts edit more successfully than Known** (0.88 vs
0.84, AlphaEdit) and **Famous more than Unfamous** (0.88 vs 0.82).

That is the "does possession predict editability" experiment, already run. It also
overlaps [T-061]: they find popularity predicts edit success where we found prominence
predicts possession level.

### 3 · ParaRel — closes [R-008]

**Elazar, Kassner, Ravfogel, Ravichander, Hovy, Schütze, Goldberg — "Measuring and
Improving Consistency in Pretrained Language Models", TACL 2021, arXiv:2102.01017.**
**328 paraphrases across 38 relations, explicitly including `X born-in Y`.** So `P19`
is covered and design.md Part II should adopt these rather than hand-write templates.

---

### What survives, and it is narrower but sharper

Read directly, the Knowledge Spectrum paper does **not**:

- **examine grounds, premises or entailment consequences at all** — it measures direct
  edit success plus general ability on ARC/OpenBookQA, never the fact's justifications.
  The backward/grounds question remains unclaimed;
- **ask whether its own Familiarity classification is phrasing-dependent.** It uses
  paraphrases to test *generalisation of the edit*, never to test *the stability of the
  Known/Unknown label*;
- **use a discriminative control.** Familiarity is binary from generation, so it has no
  cell for "the model holds the fact but this phrasing cannot elicit it" — our `MUTE`;
- **analyse destination** — where probability goes after an edit, [E-014]'s 67%/82%.

**The sharpest surviving claim, and it is a critique with teeth.** A Familiarity-style
Known/Unknown axis inherits surface form competition. [E-011] measured the same facts
flipping cell under rendering — rank-1 on modal answers went 21% → 69% from spelling
alone. So facts that are `MUTE` get labelled *Unknown* by generation probing. If
`MUTE` facts edit easily — and a fact the model holds but cannot express is plausibly
easy to overwrite — then **"Unknown facts edit more successfully" may be partly
measuring phrasing rather than knowledge.** That is testable with machinery we already
have, it is falsifiable, and it bears on a live result.

**Confidence: high** on hits 1 and 3 (sources read directly); **high** on hit 2's
content, **medium** on the inference that MUTE misclassification drives their result —
that is our hypothesis, not their claim.

### Consequences

- **The broad framing is dead.** "A taxonomy of knowledge probing" is crowded, and
  "does knowledge status predict editability" is taken. Per the WHY gate's stop
  condition, do not design further on either.
- **Reposition to what is unclaimed:** grounds/premises under editing; the stability of
  the pre-edit knowledge label itself; the `MUTE` cell and what it does to conclusions
  conditioned on Known/Unknown.
- **[R-008] closes.** Adopt ParaRel's templates for design.md Part II.
- Cite `arXiv:2104.08315`, `arXiv:2102.01017`, `arXiv:2509.17482` — all verified here,
  none from memory.

**Artifacts:** this entry; closes R-008 and R-010.

## [R-009] Finding: two ROMEs circulate, and they differ on the term the method is built around

_Date: 2026-09-20 · read from both repositories, not recalled_

Opened by [E-013] gate 0, which found EasyEdit ships `mom2_adjustment: false` in **all
fourteen** of its ROME configs — including `gpt2-xl` and `gpt-j-6B`, the two models the
ROME paper itself used. The question was whether the original implementation agrees.

**It does not.**

| source | `gpt2-xl` | `gpt-j-6B` | `mom2_dataset` | `mom2_n_samples` |
| --- | --- | --- | --- | --- |
| `kmeng01/rome` (original) | `true` | `true` | wikipedia | 100,000 |
| EasyEdit | `false` | `false` | wikipedia (unused) | 100,000 (unused) |

So `u = C⁻¹k*` in one implementation and `u = k*` in the other, under the same name, for
the same models. The whitening term the paper's method section is built around is on by
default in the authors' code and off by default in the toolkit most third-party work
reaches for.

**Confidence: high.** Both values read directly from the raw config files.

**What this changes for us — a qualification, not a retraction.** The paper says
*"`C = I` is what the field runs, not what ROME describes."* The second half is now
verified rather than assumed. The first half is **too strong**: it is what *EasyEdit
users* run. Anyone using the original repo runs the whitened update. Corrected in §6.4.

**What it does not change.** [E-016] measured the whitened arm as well, and [E-021] showed
the mechanism is a property of the `u·k*` normalisation, which is present in **both**
implementations. The central claim does not depend on which `C` is used — that is the
point of [E-016]'s 42/42 identical destinations.

**What it means beyond this project, stated carefully.** Any paper reporting "ROME"
numbers inherits whichever default its toolkit ships, and the two differ on the method's
defining term. Whether published results actually diverge because of it is **not
established here** — we have shown the configs differ, not that the numbers do. That would
need the same benchmark run both ways, and it is not our question.

**Artifacts:** this entry; closes R-009, opened by [E-013] gate 0.

## [T-065] Finding: pairs bound, crossings decompose — and narrowing comes from unfixing a dimension

_Date: 2026-09-20 · meta-analysis of this project's own 17 recorded results_

Tests the thread's two structural claims against the record rather than reasoning about
them. Every result in `decisions.md` hand-classified by the shape of the comparison that
produced it, and by whether the finding survived.

| shape | n | held | narrowed |
| --- | ---: | ---: | ---: |
| single measurement | 1 | 1 | 0 |
| pair (2 conditions) | 5 | 4 | 1 |
| crossing (2+ dimensions) | 7 | 6 | 1 |
| multi-arm (3+ on one dimension) | 4 | 2 | 2 |

**Claim 2 of the thread is refuted.** *"The findings have come from crossings, not pairs"*
does not hold: pairs survived at 80%, crossings at 86%, which is noise at this n. Pairs
produced [E-015]'s +0.0 pp null, [E-018]'s 0.082 floor and [E-023]'s pool correction —
three of the project's load-bearing results.

**What differs is what each shape yields, not whether it yields.**

- **Pairs bound.** They establish that something is present, absent, or equal — a floor, a
  null, a correction. [E-015]: no inference. [E-018]: 0.082. [E-023]: the pool undercounts.
- **Crossings decompose.** They establish what shape an effect has, and an interaction is
  by definition unavailable to a pair. [E-012]: +1, +1, +20. [E-022]: MUTE has two causes.
  [E-025]: a floor plus type-matched displacement.

**Claim 1 — the lattice — survives, in a sharper form.** Four results were narrowed, and
in every case the narrowing came from **varying a dimension that had been held fixed**:

| narrowed | by | dimension unfixed |
| --- | --- | --- |
| [E-009] pair | [E-009b] crossing | answer identity, not just position |
| [E-017] multi | [T-075]/[E-019] crossing | layer |
| [E-024] crossing | [E-025] crossing | type, holding relatedness |
| [E-014] multi | [E-023] **pair** | measurement method itself |

The fourth is the interesting one: a *pair* narrowed a *multi-arm* result, because it
varied something nobody had varied — ranking against generation. **Arity is not the
generative variable; the count of dimensions ever varied is.**

> The productive move is to ask what a design holds fixed, and vary that. Every narrowing
> in this record came from unfixing something, and none from adding arms to a dimension
> already varied.

**Prescriptive, and cheap to apply.** Before running a comparison, list what it holds
fixed — model, layer, relation, template, pool, measurement method, decoding — and ask
which of those has never been varied anywhere in the record. [E-023] came from noticing
that *every* result held "rank a closed pool" fixed, and it corrected a published number.

**Confidence: medium.** n = 17, all from one project, classified by hand by the person who
ran them. The shapes are unambiguous but "held" versus "narrowed" is a judgement about our
own work, and the 80%/86% comparison is underpowered by construction.

**Artifacts:** this entry; answers [T-065].

## [R-011] Finding: the depth result has prior art, and T-086 has a candidate

_Date: 2026-10-03_

Re-ran prior art against where the project **now** is rather than where it started. Four
entries added to the reading list, each verified field-by-field against the paper's own
record. Two of them change what we may say.

### The depth result is not new as a phenomenon

**He et al., arXiv 2601.04600** (January 2026) report, among three ROME failure modes,
that *"generalization ability deteriorates sharply when editing later layers."*

That is [E-028]'s phenomenon, found independently and **published eight months before our
run**. Our depth finding must not be described as new.

**What may still be ours is the control, not the observation.** They report that deeper
edits generalize worse. We held *delivery* fixed at a coefficient of exactly 1.000 and
*belief displacement* matched to within 0.3 nats, and measured 1.22 against 0.41 nats of
reach per nat displaced — which separates the effect from edit strength and from
optimisation budget ([E-028d]'s fourth cell). Whether that separation is itself a
contribution is a question for someone outside the project, and it is now question 4 for
the call.

**Unread.** The paper is `to-read`. This entry is written from its abstract, which is
enough to establish the overlap and not enough to size it. **Read it before the call.**

### T-086 has a candidate explanation, and it is the first one

[T-086] asks what sets how far an edit travels — the question nothing in our record
predicts, where displacement and the efficacy margin each reach only ρ ≈ 0.42.

**Ravfogel et al., arXiv 2605.12426** proves, in a controlled single-layer setting, that
subject embeddings encode **linear superpositions of their attribute vectors**, with the
MLP acting as a **relation-conditioned selector** via ReLU gating — explicitly *"not as an
associative key-value mapping."*

If that structure survives past the controlled setting, it predicts both things [E-033]
measured: writing a new attribute vector at the subject position perturbs the whole
superposition (the broad same-subject damage), and perturbs most what lies nearest the
injected direction (displacement following the injected value's **type**).

It also contradicts ROME's own premise. ROME treats the MLP as an associative key-value
store; this argues it is a selector. We edit on ROME's premise throughout.

**Two cautions, both load-bearing.** It is a *theoretical* result in a *single-layer*
setting with random bijections, and we measure Llama-3.1-8B through 405B — the gap is
large and unargued. And it is seductive: it explains our two main behavioural findings at
once, which is exactly when a borrowed frame should be distrusted. It is a candidate for
T-086, not an answer to it.

### What the search did not turn up

**Nobody states the pinned-coefficient result.** Searching for the normalisation directly
returned ROME itself and implementations, not an analysis of `u·k*`. ROME's own paper notes
qualitatively that an edit generalizes to *"new prompts/sentences that include the subject
tokens"* — so the **phenomenon** is observed in the original work. What we have not found
stated anywhere is the **arithmetic**: that the coefficient is exactly 1 on those prompts,
for any `C`, at every layer, whatever relation is asked.

That narrows the novelty question usefully and makes it sharper rather than weaker: not
*"has anyone seen this?"* — ROME's authors did — but *"has anyone said why, and noticed it
is exact?"* That is the form in which it should go to Natalie.

**Confidence: medium.** Four papers verified, one search pass, English-language web search
only. A negative from one sweep is weak evidence of absence, and the assistant's training
cutoff precedes much of the relevant window — which is why every entry here was fetched
rather than recalled.

**Artifacts:** web/data/papers.yml (4 entries, all `verified: true`)

## [R-011b] Finding: the project's founding citations all resolve — two were described wrong

_Date: 2026-10-03_

`CLAUDE.md` has carried eight arXiv identifiers since day one under its own warning:

> Citation IDs above came from search and are **unverified**. Verify against arXiv before
> any of them enters a document that leaves the repo.

Seven of the eight had never been checked and were absent from the reading list. All seven
were fetched and **all seven resolve to real papers**. No phantoms. They are now in
`papers.yml` with `verified: true`.

**Two descriptions did not survive contact, and both were load-bearing.**

### RippleBench is about unlearning, and its distance function is not pluggable

CLAUDE.md says:

> **RippleBench** (2512.04144) — distance-stratified propagation curves, and the distance
> function is pluggable including graph path length. **Check whether a code dependency
> graph can be swapped in. Highest-leverage available move.**

The paper (Rinberg et al.) builds distance from **WikiRAG semantic neighbours** and
generates multiple-choice questions at varying semantic distance. The abstract describes
no pluggable distance metric and no graph path length. It also evaluates **eight unlearning
methods**, not editing methods.

So *"swap in a code dependency graph"* — recorded as the **highest-leverage available
move** — rests on a property the paper does not advertise. It may still be possible by
modifying their pipeline, but it is not the drop-in the note implies, and the note should
not be read as a plan until someone has looked at the code.

**What it gives us instead is better than what we thought we wanted.** Its cross-model
result — delta curves *nearly identical* across four models, read as ripple being a
property of the **method** rather than the base model — is the close parallel to [E-032],
where the pinning is exact across a 68× parameter range and the decay profile is
approximately scale-invariant at matched depth. Two independent routes to the same shape
of claim.

### Forgetting is Not Erasure is a vision result

CLAUDE.md lists it among the knowledge-editing literature, and the orphan arc's framing
leaned on it: if forgetting is interface drift, our `damage` is accessibility loss rather
than destruction.

The evidence is **split CIFAR-100 with a ResNet-style network and a compact vision
transformer**. No language model appears in the abstract. The idea may transfer and the
stitching protocol is suggestive, but the paper does not establish it for LMs, and any
sentence of ours leaning on it must say so.

### The rest check out

KnowledgeSmith (ICLR 2026) reports the consistency-capacity trade-off as described.
EditPropBench is manuscripts and LLM editors rather than weights, exactly as noted. AI
Engram is ICML 2026 oral, and 2607.24805 is indeed its sequential-editing critique —
*"Forgetting Is Not a Fix: Path Dependence in Sequential Engram Editing"*, which falsifies
the commutative-manifold hypothesis while leaving the single-edit results untouched. One
loose end: CLAUDE.md cites CodePlan as *Proc. ACM Softw. Eng. 1 (FSE), 2024*; the arXiv
record does not confirm that venue, so the venue claim stays unverified even though the
paper is real.

### Why this is worth an entry rather than a quiet fix

Both corrections are of the same kind: a citation was summarised from a search result,
the summary was plausible, and the project then **reasoned from the summary** — in one
case naming it the highest-leverage move available. Nothing was fabricated; the drift was
all in the description. That is the failure mode the rule in CLAUDE.md exists to catch,
and it took four months to run the check it asks for.

**Confidence: high** for the resolutions and the two corrections — each read off the
paper's own abstract page. **Medium** for completeness: abstracts only, and a description
can still be wrong in ways an abstract does not reveal.

**Artifacts:** web/data/papers.yml (7 entries, all `verified: true`)

## [R-012] Finding: reading the two papers moved both claims we made from their abstracts

_Date: 2026-10-03_

[R-011] put two papers into §2 on the strength of their abstracts. [R-012] read them. **Both
pre-registered falsification conditions fired**, in opposite directions — one overlap is
larger than we said, one is smaller.

### He et al. (2601.04600) overlap MORE than §2 admits

They edit **GPT-J-6B with ROME at layers 5–20** on MQuAKE and CounterFact. Generalization
is paraphrase accuracy. Their numbers:

| edit layer | MQuAKE edited-hop | CounterFact paraphrase |
| ---: | ---: | ---: |
| 5 | 92.5% | 76.3% |
| 15 | 72.5% | 65.6% |
| 20 | **31.7%** | 65.6% |

That is [E-028]'s phenomenon, as already recorded. **What was not recorded is that they
also measured our mechanism.** They report:

> "the average cosine similarity between subject keys for original and rephrased prompts
> declines steadily from roughly 0.80 at layer 5 to about 0.50 at layer 25"

That is **[E-019] and [E-020]** — the coefficient decay for reordered probes, and the
cosine underneath it. We measured 0.984 → 0.471; they measured 0.80 → 0.50. Same
quantity, same shape, published January 2026. The layer sweep is not new either.

**What survives, and it is sharper than "we had a control and they did not".** They do not
control edit strength across layers. Their warrant for treating the effect as depth is:

> "ROME achieves stable and high edit success rates"

**Edit success is exactly the metric [E-028a] showed cannot measure edit strength** — lift
on the injected target spans **0.17 nats** across two layers and a fourfold step budget
while belief displacement spans **5.70**. It saturates by 25 steps and carries no further
information. So their control is one we independently measured to be uninformative, and
[E-028b] instead matched **belief displacement** at a 16× step budget and found the effect
survives.

That is a real contribution and a narrow one: not the phenomenon, not the mechanism, but
**the demonstration that the field's standard efficacy check cannot license the inference
they draw from it.** §2 and §7 should say that, rather than the vaguer "our control".

**What remains unclaimed by them:** the analytic result. They report cosine *declining*
for rephrased prompts; nothing in what we read states that prefix-sharing prompts sit at
**exactly 1.000**, for any `C`, at every layer. [E-020]'s decomposition — that the norm
ratio carries none of the decay — also appears to be ours.

### Ravfogel et al. (2605.12426) is NOT a T-086 candidate

§2 offers it as the first candidate explanation for type-matched displacement. **Reading it
withdraws that.** Their own limitations section:

> "Our setting treats relations as opaque tokens and attributes as **arbitrary entities**,
> but real factual knowledge carries rich semantic structure, such as correlated relations,
> **typed attributes**, polysemy, multi-token entities, and long-tailed frequencies."

**Typed attributes are explicitly outside their setting.** Our finding is entirely about
attribute type — a country, a profession, a language. Their construction has no notion of
it, so it cannot predict our result, and the sentence in §2 claiming it would is wrong.

Worse for the candidate reading: their subject embedding is a **block vector, one block per
relation**, and the MLP selects the block for the queried relation. Their counterfactual
perturbation experiment swaps one relation's attribute by minimum-norm perturbation and
finds the MLP *"follows"* on the queried relation and stays *"stable"* on the others.

**That is close to the opposite of what we measure.** A per-relation block account predicts
perturbation stays local to the edited relation. [E-033] finds an edit damages everything
about the subject, with the worst damage following the injected value's **type** rather
than the edited relation.

**So the honest framing is a tension, not a candidate.** A theoretical account of
memorisation structure predicts relation-local perturbation; our measurement on real models
finds subject-wide damage. One of: the single-layer construction does not carry to deep
models (their own stated limitation), or ROME's rank-one update does not act on the
structure the construction describes, or the account is incomplete in the way typed
attributes would make it. That is more interesting than a candidate explanation and it is
honest; [T-086] remains without one.

**Not purely synthetic**, in fairness: their §5.3 probes Qwen2.5-0.5B, Qwen3-14B,
Llama-3.1-8B, Llama-3.2-1B and Phi-4 on natural-language relational facts. The theory is
single-layer; the probing is not.

### What this cost and bought

An afternoon of reading moved two claims that were already in the packet — one citation
now covers more of our work than we credited, one supports less than we claimed. Both were
written from abstracts eight hours earlier. **The lesson is not "read before citing", which
we knew; it is that an abstract systematically under-reports overlap and over-reports
applicability**, because abstracts sell the contribution and bury the setting.

**Confidence: high** on both corrections — each rests on quoted sentences from the papers'
own full texts. Both papers move to `skimmed`; neither has been read line by line.

**Artifacts:** web/data/papers.yml (status updates); this entry

## [R-013] Finding: RippleEdits has NO subject-initial prompts — §7's premise is false

_Date: 2026-10-14 · measured on the released benchmark, 1,948 entries, 22,014 test prompts_

§7 item 2 of the write-up — the project's one outward-facing consequence, priced at a week
and unrun since September — rests on this sentence:

> Every propagation benchmark we know of probes with prompts that begin with the subject.

**It is false for RippleEdits**, the canonical ripple benchmark and the one we cite as
`cohen2024ripple`. Downloaded (MIT licence) and measured:

Across all three released subsets — `recent`, `random`, `popular` — **1,948 + entries,
46,754 test prompts**:

| | subject-initial | subject-later | position undetermined |
| --- | ---: | ---: | ---: |
| all three subsets | **44** | 25,277 | 21,433 |
| as a share of the **placed** prompts | **0.17%** | 99.83% | — |

**44 of 46,754 — 0.09% — begin with their subject.** Of the prompts whose position can be
determined at all, 99.8% put the subject *later*. Nearly every prompt has the form
*"The &lt;relation&gt; of &lt;subject&gt; is"*; in `recent.json` alone, 20,759 of 21,052
materialised prompts begin with the literal word **"The"**.

**A correction to this entry's own first draft, left visible.** It originally read "0 of
22,014 — not one begins with its subject", measured on `recent.json` with a stricter
detector. Widening the detector and adding the other two subsets found 44. The claim is
unchanged in substance and was overstated in form, which is the failure this project keeps
making about other people's work and has now made about its own measurement. The
undetermined 21,433 are reported rather than assumed: they are prompts carrying neither an
empty slot nor a label this script could match, and they are **not** counted as
subject-later.

**How it was measured without resolving a single entity.** The released prompts carry the
subject as a Wikidata QID; some are materialised (*"The place of birth of Leo Arons is"*)
and some leave the slot empty (*"The name of the field of work of&nbsp;&nbsp;is"*). Either
way the subject's **position** is visible, which is all the claim is about. Cost: one
download and twenty minutes, against a week.

### What this costs, and what it does not

**Costs.** The sentence comes out of §7, §6 and the packet. We asserted a property of
*every* benchmark having inspected none of them — the same failure as [R-011b]'s
RippleBench description, where a project direction rested on a property the paper did not
claim. Twice now, the thing we have been least careful about is the literature we are
arguing against.

**Does not cost: the consequence itself, which survives in a sharper form.** [E-019]
measured the coefficient for subject-*late* probes at **0.951** (late clause) and **0.962**
(possessive) **at layer 5** — the layer EasyEdit's shipped config edits. So RippleEdits'
own prompt form still receives ~95% of the update at the standard edit layer. The concern
was never really about being subject-initial; that was our probes' shape, not the
mechanism's requirement. The mechanism requires only that the coefficient be high, and at
the layer the field edits it is high for both forms.

What the correction kills is the *depth* half: at layer 20 the same form drops to ~0.58, so
a benchmark of subject-late prompts would be much less affected by a deep edit. That was
never the claim we were making, but it is now foreclosed.

### The experiment this replaces

The priced week was "rewrite the probes subject-final and re-score". **That work no longer
exists** — the benchmark is already subject-final. What replaces it is cheaper and more
direct: take RippleEdits' own templates and measure the coefficient on them, with no edits
and no rewriting. A day, not a week, and it is made with the benchmark's own materials
rather than ours. See [E-036].

**Confidence: high.** Measured on the released `recent.json`, every test prompt of every
criterion, with the counting rule stated above and reproducible from
`data/ripple/recent.json`. Unchecked: the `random` and `popular` subsets, which the same
script covers and which there is no reason to expect to differ.

**Artifacts:** data/ripple/recent.json (19.7 MB, MIT, committed for reproducibility)

## [R-014] Finding: MQuAKE names the edited subject if and only if the edit is on hop 1

_Date: 2026-10-14_

[E-037]'s §4.6 row — RippleEdits' *different-entity* tests sit at a coefficient of 0.982
because their prompts name the edited subject verbatim — was a fact about one benchmark.
This asks whether it is a fact about the field. **MQuAKE answers it, and the answer is a
clean split rather than a tendency.**

Counted over all four released MQuAKE files (`princeton-nlp/MQuAKE`, fetched 2026-10-14),
asking only whether a multi-hop question's string contains the edited subject's string:

| file | questions | names the edited subject | |
| --- | --- | --- | --- |
| MQuAKE-CF | 27,654 | 17,922 | 64.8% |
| MQuAKE-CF-3k-v2 | 9,000 | 5,901 | 65.6% |
| MQuAKE-CF-3k | 9,000 | 5,859 | 65.1% |
| MQuAKE-T | 5,604 | 21 | **0.4%** |
| **ALL** | **51,258** | **29,703** | **57.9%** |

**The aggregate is noise; the structure underneath it is exact.** Restricting to
single-edit instances, where which hop carries the edit is unambiguous:

| hop carrying the edit | questions | names the edited subject |
| --- | --- | --- |
| 1 | 6,861 | **6,861 — 100.0%** |
| 2 | 13,977 | **0 — 0.0%** |
| 3 | 2,313 | **0 — 0.0%** |
| 4 | 216 | **0 — 0.0%** |

Not approximately. **The edited subject appears in the question exactly when the edit sits
on the chain's first hop**, across 23,367 questions with no exceptions in either direction.
The reason is structural: MQuAKE phrases a chain from its head, so an edit on hop 2 is an
edit to an *intermediate* entity the question never mentions —

> chain: *Michael Feinstein → country of citizenship → **United States of America** →
> capital → Washington, D.C.*
> edit on hop 2, subject **United States of America**
> question: *"What is the capital city of the country that Michael Feinstein is a citizen
> of?"*

MQuAKE-T's 0.4% is the same fact, not a different one: 1,861 of its 1,868 single-edit
instances edit hop 2 or later.

**Confidence: high.** It is a string count over released files with a decidable predicate
and no entity resolution, which is why the two cells are exactly 100.0% and 0.0% rather
than nearly so.

### What this does to §4.6

**Both outcomes the ticket pre-stated are wrong, and the real one is more useful than
either.** It is not FIELD-WIDE and not RIPPLEEDITS-SPECIFIC. MQuAKE contains **both**
populations, separated exactly by a property recorded in its own metadata:

- RippleEdits' compositional tests always name the edited subject because its edits are
  always on the head entity. §4.6's 0.982 stands and is **not** a quirk of our reading.
- MQuAKE's hop-2+ questions are the genuine different-entity test the field is assumed to
  have: 16,506 of them, where the edited subject is simply absent from the prompt.

**So MQuAKE is a within-benchmark control nobody has to construct**, and that is the
finding's value. Running [E-036]'s measurement on it compares hop-1 against hop-2+
questions inside one dataset, one prompt register, one set of edits — the confound that
makes a cross-benchmark comparison unreadable is gone by construction. If hop-1 questions
sit near 1 and hop-2+ questions sit near the floor, the mechanism is demonstrated on the
field's standard multi-hop benchmark with its own materials supplying the control.

**What this does not establish.** A subject present in a prompt is not a subject at the
position the coefficient is read; this counts **construction**, never **delivery**. It also
covers one benchmark beyond RippleEdits — RippleBench (2512.04144) and EditPropBench
(2605.02083) are **not** counted here and the ticket stays open for them.

**Artifacts:** agents/engineer/workspace/fetch_mquake.py;
agents/engineer/workspace/mquake_forms.py; results/R-014-mquake-forms.json

## [R-014b] Finding: the other two benchmarks cannot be counted, for two different reasons

_Date: 2026-10-14_

[R-014] left RippleBench (2512.04144) and EditPropBench (2605.02083) uncounted. Both were
chased and neither arm can run; the reasons differ and only one is a blocker.

**RippleBench — no released materials found.** GitHub's repository search returns **zero**
repositories for the name, and the arXiv abstract links no code or data. The paper resolves
and the title is confirmed — *"RippleBench: Capturing Ripple Effects Using Existing
Knowledge Repositories"* — so this is an availability problem, not an identification one.
**The arm is blocked, not answered.** If the data appears, the count is an hour's work and
the script is `mquake_forms.py` with one predicate changed.

**EditPropBench — out of scope, and this project already knew.** The abstract confirms what
`CLAUDE.md`'s literature section records: *"Measuring Factual Edit Propagation in Scientific
Manuscripts"* — manuscripts edited by LLM editors, not weights edited by ROME. There is no
"edited subject's key" to be present or absent in a prompt, so **[R-014]'s question does not
apply to it** and counting it would be a category error dressed as diligence. The arm is
**dropped**, not blocked.

**What this means for the claim.** [R-014]'s finding stands on **two** benchmarks —
RippleEdits and MQuAKE — not the three the ticket scoped. That is enough to establish the
contrast (one construction names the edited subject, the other does so only on hop 1) and
**not** enough to say anything about the field as a whole. §4.6 is written to the two it has.

**Confidence: high** on EditPropBench being out of scope, **medium** on RippleBench having
no public release — absence of a GitHub repository under that name is evidence, not proof,
and the authors may host it elsewhere.

**Artifacts:** none — this is a negative result about data availability, recorded so the
next person does not spend the same hour.

## [R-015] Finding: ROME's ES margin is its own suppression term, and that reopens T-085

_Date: 2026-10-15_

[T-085] closed on [E-029]'s pairing of belief displacement against ES margin — 0.419 and
0.425 against propagation — concluding *"there is nothing ES fails to see that displacement
catches."* [E-035] measured a third quantity on the same 42 subjects, so the conclusion was
re-examined. **It was right about what it tested and wrong as a general claim.**

**ROME saturates its target by construction.** Post-edit `log P(target)` is **0.00** for
most of the 42 subjects — the optimiser runs `v*` until the target reaches criterion:

```
                      sd
base_true           0.74
L5_true             5.68
L5_target           0.02
```

So `es_margin = L5_target − L5_true` is `−L5_true` plus a near-constant, and
`rho(−L5_true, es_margin) = +1.000` **exactly**. `displacement = base_true − L5_true` is the
same quantity with a 0.74-sd contaminant, hence the 0.988 between them.

**A margin that appears to compare two quantities compares one.** [E-029]'s "one weak view
rather than two" was correct; the reason is that between-subject variance lives entirely in
how far the true answer fell, because the target does not vary.

**What this does to [T-085].** Its question was *what does ES fail to distinguish* — and
the only candidate it had to answer with was ES in disguise. [E-035] supplies one that is
not: `‖Δv‖` tracks propagation at **−0.423**, within 0.002 of ES's **+0.425**, while
correlating with ES at only **−0.276**. ES margin measures true-answer suppression and
nothing else, and here is a quantity it does not see that predicts the outcome as well as
it does.

**Confidence: high** on the identity (it is arithmetic over values already on disk, and the
rank correlation is exactly 1.000). **Low** on what follows from it: the −0.423 is
correlational, sits below the effect floor [E-035] pre-registered, and comes from the same
42 subjects that generated the observation. [T-093] is the pre-registered out-of-sample
test and nothing should be claimed before it.

**Limits.** n=42, one relation, one model, layer 5. Existence per [O-004], never a rate.
This concerns the **continuous ES margin** as [E-029] used it, **not** ROME's published
binary Efficacy Score; the two must never be conflated in any document that leaves the repo.

**Artifacts:** none new — arithmetic over results/E-035-propagation-candidates.json and
results/E-026b-edit-prompt.json

## [R-016] Finding: the two-predictor ceiling is 0.534, so T-093 closes without its run

_Date: 2026-10-15_

[T-093] asked whether ES margin and `‖Δv‖` combine past **ρ = 0.60** out of sample. The
out-of-sample run needs `v*` computed for 94 fresh chains — roughly 400 optimisation traces
plus 188 scoring calls. **The cheap bound was computed first and it answers the question.**

The **multiple rank correlation** of propagation on the two rank vectors is **0.534**. That
is the closed-form ceiling for *any* linear combination, fit on the very data it is scored
against — maximally optimistic. It **fails the 0.60 bar by 0.066**, and by **0.101** after
shrinking for two fitted parameters at n=42 (0.499).

Two predictors each at ρ ≈ 0.43 and correlated at 0.27 land near 0.53 together. **That was
computable the moment [E-035] printed its three numbers**, and running 94 edits to discover
it would have been a week's compute spent on arithmetic.

**Confidence: high** on the bound, which is closed-form. **Stated limit:** it covers linear
combinations of the two rank vectors; a nonlinear monotone form could exceed it, none was
pre-registered, and fitting one post-hoc on n=42 is the overfitting [T-093] exists to
prevent.

**What it does to [T-086].** The best combination of everything the record contains
explains about **28%** of rank variance. [E-035] eliminated seven candidates singly; this
eliminates the strongest pairing of the two survivors. The statement is now *"nothing
explains more than ~18% alone or ~28% together,"* and it rests on having searched rather
than on not having looked.

**Artifacts:** none new — arithmetic over results/E-035-propagation-candidates.json

_Narrowed 2026-10-15 by [E-042]._ The `‖Δv‖` this finding leans on is substantial only in
the 8B/birthplace configuration — the same one it was measured in. Across six other cells
it is a near-zero lean (|ρ| ≤ 0.13 in five of six). **So "ES measures true-answer
suppression and nothing else" stands as an observation about the metric's arithmetic, which
is exact; but "and here is a quantity it misses" is narrowed to one configuration and is
not yet a general gap.** The arithmetic half of this finding survives [E-042] untouched;
the consequence half does not.

## [R-017] Finding: two UNFOUND, one ADJACENT with a named neighbour

_Date: 2026-10-15_

Lens-2 pass on the three claims being weighed for outward use. `CLAUDE.md` permits nothing
stronger than *"unclaimed in this setting"*, and this ticket's job is to establish even
that much, which no prior search had.

**1 · The coefficient screen — UNFOUND.** Searched for a pre-run criterion deciding whether
a propagation test can measure propagation, and for predicting edit locality from key
overlap without a forward pass through the edited model. The nearest work goes the other
direction: **SUIT** (2509.24502) isolates entity-specific subspaces *to confine an edit*,
and **SetKE** (2504.20972) addresses overlap between knowledge elements *as a method
problem*. Both treat key overlap as something an editor should manage. **None treats it as
a property of an evaluation item, computable in advance, that decides whether the item is a
valid test.** That inversion — overlap as a benchmark-screening criterion rather than an
editing obstacle — is where our framing sits.

**2 · The ES-margin identity — UNFOUND.** Searched for critiques of Efficacy Score and for
the observation that post-edit `P(target)` is pinned by the optimisation criterion. The
definition is everywhere (*"the fraction of edits for which the model assigns higher average
token probability to the new target than to the original"*), and sequential-editing work
(2401.07453, 2403.07175, 2406.11263) reports ES "almost 100% until it declines" — which is
**consistent with saturation and is not the claim**. Those papers track the *binary rate
across successive edits*. Ours is that the **continuous margin is rank-identical to
true-answer suppression on a single edit** (ρ = 1.000, sd 0.02 against 5.68) because the
optimiser stops when the target saturates. No hit.

**3 · The benchmark construction finding — ADJACENT, and the neighbour must be cited.**
**ChainEdit** (2507.08427) identifies a flaw in compositional evaluation and it is **not
ours**: theirs is that the intermediate fact comes from an external KG and may misalign
with the model's internal belief, so the test partly measures LLM-vs-KG agreement rather
than logical generalisation. Ours is that **the compositional prompt names the edited
subject verbatim, so the update arrives at that token by arithmetic** — 0.982 against a
0.070 floor — independent of whether any intermediate belief is held. Different mechanism,
different fix: they realign the dataset to the model, we would screen or re-site the prompt.

Also adjacent and separate: **He et al.** (2601.04600) on rank-one editing failing at
multi-hop, which argues from the rank-one constraint and proposes no screen; and **INLAY**
(2608.26292), whose negative result concerns scope classification and the absence of
negatives in counterfactual benchmarks, not surface overlap.

### What this licenses

- Claims 1 and 2 may be written as **"we have not found this stated"** — the weakest
  positive and now an evidenced one.
- Claim 3 **must cite ChainEdit and distinguish itself in one sentence**, or a reviewer who
  knows that paper will read ours as a restatement. The distinction is clean and should be
  stated before the result, not after.

**Confidence: medium.** This is a web-search pass over titles and abstracts, which is
exactly the standard [R-011b] showed to be insufficient — *"a description read off a search
snippet is not a verified citation even when the identifier is correct."* ChainEdit in
particular should be **read** before anything leaves the repo, since claim 3 now depends on
a distinction drawn from its abstract.

**Unverified identifiers**, per the standing rule: 2507.08427, 2509.24502, 2504.20972,
2601.04600, 2608.26292, 2401.07453, 2403.07175, 2406.11263 came from search and are not
checked against arXiv records.

**Artifacts:** none — literature only.

## [R-018] Finding: ChainEdit read. The distinction holds, and their own fix illustrates ours

_Date: 2026-10-15_

[R-017] drew claim 3's distinction from ChainEdit's abstract, which [R-011b] established is
not good enough. The paper has now been read — PDF extracted locally, body searched, the
critique and the fix read in full.

**Verified:** *ChainEdit: Propagating Ripple Effects in LLM Knowledge Editing through
Logical Rule-Guided Chains*, Zilu Dong, Xiangqing Shen, Zinong Yang, Rui Xia,
arXiv **2507.08427**. Title and authors confirmed against the arXiv record. **Venue
"ACL 2025 main" came from a search summary and is NOT verified** — do not state it.

### Their flaw, in their own words

> *"their reliance on external KGs for question formulation. As their questions were formed
> using KG-derived knowledge, they requires external knowledge beyond the edited content to
> correctly answer, thereby obscuring the assessment of logical generalization
> capabilities."*

[R-017]'s abstract-derived summary was **correct**: the flaw is that the intermediate fact
comes from an external knowledge graph and may not match the model's own belief, so a
method is penalised for a disagreement that is not about editing.

### Our observation is not theirs — ADJACENT-CONFIRMED

Searched the full body for `surface`, `lexical`, `overlap`, `verbatim`, `shortcut`:
**zero hits.** The word `subject` appears only in template grammar (*"the relation of
subject is object"*), path endpoints, and a binding rule. **Nowhere does the paper observe
that a compositional prompt names the edited subject, or that an edit could reach such a
prompt mechanically rather than by reasoning.**

Their concern is about **what the question requires** (knowledge the model may lack). Ours
is about **what the prompt contains** (a token whose key is the edit's key). Different
mechanism, and they do not touch ours.

### The part worth more than the distinction

Their fix is three LLM-adaptive variants, and **none removes the edited subject from the
prompt**:

| variant | what it does | does our concern survive? |
| --- | --- | --- |
| **Filtered** | drops questions whose intermediate fact the model cannot verify | yes — survivors still name the subject |
| **Replaced** | regenerates the intermediate fact from the model's own state | yes — only the middle entity changes |
| **In-Prompt** | *"employs context augmentation to explicitly inject intermediate knowledge into prompts"* | **yes, and more so** — the prompt gets longer while the subject stays |

**In-Prompt is the sharpest illustration available of why the screen adds something.** It
is a deliberately repaired benchmark, built by authors who had identified a real evaluation
flaw — and every one of its prompts would still fail a coefficient screen, because
augmenting context does not remove the token the update is delivered to. A benchmark can be
fixed for their problem and remain broken for ours.

That is a better framing than "we found a different flaw." It is: **the field has begun
repairing its propagation benchmarks, and the repairs do not address delivery.**

### Also recorded

They evaluate on the **POPULAR** subset of RippleEdits only — the same subset [E-038] found
had just 19 different-surface aliases and [E-043] could not resolve. They merge CI and CII
into a single Reasoning metric following KnowEdit, so a reader of their results cannot
separate the two compositional types that [E-038] measured at 0.982 and 0.955.

### Consequence

Claim 3 stands and **must be written with ChainEdit named first** — their flaw, then ours,
then the one-sentence distinction, then In-Prompt as the illustration. A reviewer who knows
this paper and meets our claim cold will otherwise read it as a restatement.

**Confidence: high.** Read from the body, not a snippet.

**Artifacts:** none — literature only. Extracted text at `/tmp/chainedit.txt` is scratch
and not kept.

## [R-019] Finding: MEMIT stops at the same threshold as ROME, so the ES identity is not a ROME quirk

_Unratified_

_Date: 2026-10-16 · written by an autonomous cycle; see `LOOP.md`_

[T-096] asked whether MEMIT's optimiser saturates its target the way ROME's does, because
[R-015]'s ES-margin identity rests on that and **editing method is the one dimension never
varied anywhere in this record** — 48 mentions of ROME in `decisions.md`, zero of MEMIT.

It looked like a run. It was two files. `LOOP.md` rule 1: ask what arithmetic makes the
expensive version unnecessary.

**The stopping rule is byte-identical in both.** `memit/compute_z.py` and
`rome/compute_v.py`, from `kmeng01/memit@main`:

```python
loss = nll_loss + kl_loss + weight_decay
...
if loss < 5e-2:
    break
```

`nll_loss` is the mean negative log-probability of the target; `kl_loss` is a KL divergence
and `weight_decay` a norm penalty, so **both are non-negative**. Therefore
`loss < 0.05` ⟹ `nll_loss < 0.05` ⟹

> **P(target) > e^(−0.05) = 0.951 at the moment either optimiser stops.**

Step budgets, from the same repository's hparams: ROME 20 for gpt2-xl and gpt-j-6B, MEMIT
20 for gpt2-xl and 25 for gpt-j-6B.

### What this does to [R-015]

[R-015] measured post-edit `log P(target)` with sd **0.02** against the true answer's
**5.68**, making ROME's efficacy *margin* rank-identical to true-answer suppression at
ρ = 1.000. That was an **empirical** observation on our own implementation, which uses a
fixed 25 steps and **no break at all** — so saturation there was something the data
happened to show.

**In the published implementations it is enforced by an explicit threshold, and the same
threshold.** The identity therefore follows for MEMIT by the same argument, with no
measurement: a margin whose first term is pinned above 0.951 by the stopping rule is
carrying the second term alone.

**So [R-015] is not a ROME quirk.** It is a property of the `compute_v`/`compute_z` family
— the objective and its convergence criterion — which ROME, MEMIT and anything else
inheriting that loop share.

### What it does not establish

1. **Only for edits where the optimiser converges.** The break fires only if the loss
   reaches the threshold within the step budget; a non-converging edit leaves the target
   unsaturated and the margin informative again. The published ES rates near 100% suggest
   convergence is the common case, but that is their number, not ours.
2. **This is code reading, not measurement.** We have not run MEMIT, and [E-042] is the
   standing reminder that a mechanism holding by construction can still behave differently
   in practice. The honest claim is about **what the criterion guarantees**, not about what
   a MEMIT run would show.
3. **Our own 0.02 remains empirical**, because `src/edit.py` has no break. It is consistent
   with the threshold and not produced by it.
4. **Unverified**: `kmeng01/memit@main` was read at HEAD on 2026-10-16, not at a tagged
   release, and the hparams may differ from what any given paper reported.

**Confidence: high** on the identity of the two stopping rules, which is quoted source.
**Medium** on the generalisation, which rests on convergence being typical.

**Artifacts:** none — source read, nothing run.

## [R-020] Premise dry-run on T-086: the search was over the wrong level

_Unratified_

_Date: 2026-10-16 · autonomous cycle, `LOOP.md` phase 5 — the generative step_

[T-086] is **stuck-and-flat**, not stuck-and-hard: seven candidates eliminated at a
pre-registered floor ([E-035]), their best combination bounded in closed form at 0.534
([R-016]), the coefficient excluded by construction. More candidates will not help. By
`CLAUDE.md`'s own diagnostic, *"the corrective is not missing, it is suppressed by a
one-sided framing."*

### Move 1 — the structure under the intuition

[T-086] asks *"what sets how far **an edit** travels."* The outcome it is measured against
is a control-differenced drop on **a probe**. So the question names a property of the edit
and the data is a property of an **(edit, probe) pair** — and **every quantity ever tested
is a function of the edit alone**: ‖Δv‖, ‖k*‖, their ratio, baseline log P(true), target
prior, subject token count, residual norm, ES margin, displacement.

### Move 8 — re-run the specs against the new frame

An edit-level quantity is **constant within a subject**. It can therefore track only the
between-subject component of the outcome. [E-033] left three probes per subject across six
cells, which decomposes that directly:

```
cell                              between-subj   within-subj   within share
70B birthplace L13                        4.37          4.36          50%
70B birthplace L5                         6.31          5.41          46%
70B occupation L13                        5.64          5.80          51%
70B occupation L5                         5.05          3.73          42%
8B  birthplace L5                         9.43          9.02          49%
8B  occupation L5                         5.86          9.51          62%
mean                                      6.11          6.30          51%
```

**About half of propagation variance lives within a subject, across probes.** So no
edit-level predictor can exceed **49% of variance — ρ ≈ 0.70** — however clever it is.

### What that does to the record

```
E-029 displacement          0.419    36% of the reachable maximum
E-029/E-035 ES margin       0.425    37%
E-035 ‖Δv‖                  0.423    36%
R-016 best combination      0.534    58%
T-093's pre-registered bar  0.600    73%
```

**The 18%-of-variance framing was measured against 100% and the ceiling is 49%.** Read
correctly, the surviving predictors explain about **a third of what is reachable**, and the
best pairing explains **58%** — which is not the dead end "nothing explains more than 18%"
describes. And **[T-093]'s 0.60 bar was asking for 73% of everything an edit-level quantity
could ever deliver**, set without anyone knowing the ceiling existed.

### The predictor at the right level already exists and was never connected

The other ~51% needs a quantity that varies **across probes within a subject**. The project
has one that works: **[E-033]'s type-matching — an edit displaces probes whose answer type
matches the injected value, 6 of 6 arms.** That is a pair property, it is already measured,
and it has never appeared in [T-086]'s candidate list. `CLAUDE.md`'s own triage buckets —
`shares_subject`, `shares_relation`, `shares_object`, `shares_nothing` — are pair
properties too, and none has been correlated against propagation magnitude.

### Limits, before this becomes a claim

1. **The decomposition is on [E-033]'s probes** (citizenship, language, occupation) while
   [E-029]/[E-035] measured a **city** probe. The 51/49 split is indicative for that
   setting, not exact. **The ceiling should be re-derived on the probe family the claim is
   made about before it is written anywhere outward.**
2. n=29 per cell, six cells, two models, two relations. Existence per [O-004].
3. This reinterprets existing numbers; it measures nothing new and refutes nothing. [E-035]
   and [R-016] are correct as computed — what changes is the denominator they are read
   against.
4. The ~51% is an *upper bound on what pair-level predictors could explain*, not evidence
   that type-matching explains it.

### What this generates

[T-101] — re-derive the ceiling on the [E-029] probe family and restate the T-086 arc
against it. [T-102] — correlate type-matching and the triage buckets against propagation at
pair level, which is the first search at the level where half the variance lives.

**Artifacts:** none — arithmetic over results/E-033-crossover-*.json

## [R-021] Finding: the pair-level predictor reaches 10% of total variance, where nothing else could

_Unratified_

_Date: 2026-10-16 · autonomous cycle, [T-102]'s own cheap bound_

[R-020] found ~51% of propagation variance sits **within** subject, unreachable by any
edit-level quantity. [T-102] asked whether the pair-level predictor the project already has
— [E-033]'s type-matching — reaches it, and specified the cheap bound: correlate the
existing indicator against the existing per-pair drops before designing anything.

**Method: within-subject centring.** Subtract each subject's own mean across its three
probes, then ask whether the type-matched probe sits systematically above it. **This
removes every edit-level effect by construction**, so whatever remains is in the half no
`‖Δv‖`-style quantity can touch.

```
cell                            matched       centred mean   var expl.    n
70B birthplace L13          citizenship              +1.14         15%   29
70B birthplace L5           citizenship              +1.11         11%   29
70B occupation L13           occupation              +1.85         30%   29
70B occupation L5            occupation              +0.96         12%   29
8B  birthplace L5           citizenship              +2.20         27%   29
8B  occupation L5            occupation              +2.21         26%   29
mean                                                 +1.58         20%
```

**6 of 6 cells, mean advantage +1.58 nats, 20% of within-subject variance from a single
binary indicator.**

### The variance budget, assembled

```
between-subject (edit-level reachable)      49%
within-subject  (pair-level only)           51%

best edit-level combination   [R-016]     28.5% of total
type-match indicator alone    [R-021]     10.2% of total   <- unreachable above
together                                  38.7% of total

the framing [T-086] has carried:            18%
```

**So the picture is roughly twice what the thread has been recording** — and the gain comes
from a quantity that was measured in [E-033] a week ago and never entered [T-086]'s
candidate list, because the list was built one level up.

### What this is NOT

**It does not discover type-matching.** [E-033] designed the matched probe deliberately and
reported 6/6. What is new is **locating it in the variance budget**: the thread needed to
know how much of what is reachable anything reaches, and now 10.2% of total variance has a
name and a mechanism.

**It is one binary indicator.** 20% of the within-subject half means **80% of that half is
still unexplained**, and the remaining pair-level structure — the `shares_relation` /
`shares_object` / `shares_nothing` buckets — is untouched. The honest statement is that the
first look at the right level found something, not that the level is now understood.

**Same probe-family caveat as [R-020], and it is the binding one.** This is [E-033]'s
citizenship/language/occupation probes; [E-029] and [E-035] measured a **city** probe.
[T-101] must re-derive both the ceiling and this figure on the family a claim is made about,
and until it does, **none of these percentages may appear in an outward document.**

n=29 per cell, six cells, two models, two relations, two layers. Existence per [O-004].
**Effect, not delivery** — the outcome is a measured drop.

**Artifacts:** none — arithmetic over results/E-033-crossover-*.json
