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
