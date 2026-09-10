# Design — Edit Discretion Triage

_edit-slice · structured by the Research Design Protocol (10 lenses)._
_v0.8 — 2026-09-10, O-003. Status: **lens 2 CLEARED [R-002]; §0 gate unresolved (no data).**_
_v0.4: §2a added — suppression-not-overwrite and the output/belief-mismatch attack._
_v0.5: §0 roles flipped — mined Horn rules (e) DISCOVER, directed intervention (c)
VALIDATES. External oracle; claim 2 partially restored._
_v0.6: artifact confirmed available (MIT). KG corrected Wikidata -> **DBpedia**;
their edit sets are MQuAKE/MLaKE, not CounterFact. RULE-KE checked off._
_v0.7: E-001 killed method (e) over DBpedia (alias tautologies); E-002 revived it
over Wikidata and found grounds are **evidential, not deductive** — kernels dropped
for AGM's ordering half, `orphan` regraded. See agents/shared/decisions.md._
_v0.8: model raised to GPT-J-6B via NDIF (possession is a construct requirement,
T-039); grounds hand-built and deductive for the pilot, as an EXISTENCE claim only._
_v0.2: grounds test made directed (inputs/outputs); partition now derives from
direction x modality; association confound folded into the measurement._
_Nothing may be implemented from this document until both clear._

**One-paragraph statement.** A weight edit changes what a model believes, but the
facts that *justified* the old belief are left standing — and the resulting belief
state is jointly **improbable**. Not contradictory: measured, the grounds are
evidential rather than deductive [E-002, decisions.md]. Coherence pressure says
something should give, and logic cannot say what, because there is no entailment to
break. That
choice is currently made by nobody: it is neither performed by the editor nor
surfaced to the operator. This project builds a reusable instrument that, given
an edit, partitions the knowledge it touches into **entailed** (logic determines
the new value), **preserved** (a reconciling world exists; nothing need change),
and **contested** (the edit made these jointly implausible, and logic cannot
adjudicate). The contested set is emitted as a queue for human adjudication —
necessarily so, since evidential support admits no computed contraction. **The instrument never
repairs and never ranks.** Its claim is that an unaccountable epistemic decision
is currently being made silently, and it can be made visible cheaply.

---

## §0 · The gate — T-012, mechanical grounds discovery

Confronted first because everything rests on it. If grounds cannot be discovered
mechanically, the tool needs hand-labels per edit, is not reusable, and the
project reverts to a one-off measurement.

**The requirement.** Obtain, for an edited fact *f*, the set of facts that
justified it — without hand-enumerating them (which is circular, per
session-2026-09-08 §5) and without a compiler (unavailable in CounterFact).

**Working definition.** *g* is a ground of *f* iff intervening on *g*
counterfactually moves *f* **more than** intervening on *f* moves *g*. Causal and
**directed**; discovered, not asserted.

**Why directed.** A fact is a node with **inputs** (its justifications — the a
priori that must hold for it) and **outputs** (its consequences — what follows
from it). A one-sided test detects a *link*, not a *direction*: association is
symmetric, justification is not. So the test is two-sided.

| Observation | Reading |
| --- | --- |
| Δ(*g*→*f*) >> Δ(*f*→*g*) | *g* is an **input** to *f* — a justification |
| Δ(*f*→*g*) >> Δ(*g*→*f*) | *g* is an **output** of *f* — a consequence |
| roughly equal | **undirected association** — topical, not justificational |

The third row matters: the topical-association confound is now *detected by the
measurement* rather than controlled for externally. Symmetry is association;
asymmetry is justification.

**In-degree vs out-degree.** These are separate variables and must never be
conflated. Out-degree (consequences) is the forward propagation burden —
KnowledgeSmith's territory. **In-degree (justifications) is the number of kernels
to break — the contraction burden, and ours.** Report the edge-type vocabulary
alongside each, per CLAUDE.md.

**Methods enumerated (Protocol lens 5a — record what is deferred and why):**

| # | Method | Cost | Verdict |
| --- | --- | --- | --- |
| a | Edit *g* with ROME, measure movement in *f* | one edit per candidate | **deferred** — expensive, and the probe inherits ROME's own blast radius, confounding the thing we measure |
| b | Activation patching / causal tracing of *g*'s representations into *f*'s forward pass | moderate; machinery exists in rome-neighbors | **deferred to v2** — mechanistically cleaner, but binds v1 to NNSight and to a localization assumption we do not need yet |
| c | In-context counterfactual: condition on *g* being false, measure shift in *f* | cheap, no weight access | **SELECTED — as VALIDATION, not discovery** (role flipped v0.5) |
| d | Gradient attribution of log p(*f*) to parameters associated with *g* | cheap | **deferred** — weak construct link; attribution is not counterfactual |
| e | **Mined Horn rules read backwards** — body of a rule whose head is *f* | cheap; artifact already exists | **SELECTED for DISCOVERY (v1)** |

### The split — mined rules discover, intervention validates

**(e) Discovery.** [2606.10554] mines Horn rules `body => head` from **DBpedia**
with **AMIE** and uses them *forward*: the edit touches the body, does the head
update? (Corrected from "Wikidata" in v0.5 — the repository queries DBpedia via
SPARQL; see [R-005a].)
Read the same rules the other way and grounds come for free — **if the edit
changes the head, the body is exactly the set of premises that entailed it.**

- **kernel** = the body of a rule whose head is the edited fact
- **in-degree / justification redundancy** [T-009] = number of distinct rules
  sharing that head
- **orphan probe** = does the body still hold after the head was edited?

**(c) Validation.** Mined rules are statistical regularities, not justifications:
a high-confidence rule can be a co-occurrence artifact. So the directed
intervention test is retained — not to *find* grounds, but to check that the model
treats a mined body as an input rather than an output or a mere associate. The
two-sided test (Δ(*g*→*f*) vs Δ(*f*→*g*)) validates **rule direction**, which is
the "mined ≠ justificatory" problem in its exact form.

**Why the flip is an improvement.**

1. **The oracle becomes external.** Discovery no longer rests on the model's own
   in-context reasoning, so the model-derived-oracle weakness largely dissolves —
   a model with poor dependency beliefs no longer gets an easy exam. Substantially
   answers [T-033].
2. **Claim 2 is partially restored.** DBpedia + mined rules is a **decidable
   lower bound** on dependency in precisely the sense `definitions.md`
   declaration 2 already commits to. Not the compiler; far closer to an oracle
   than prompting. The edge-type vocabulary is now DBpedia's and must be recorded
   as such wherever out-degree or `k` is reported.
3. **It is reusable and cheap** — an existing released artifact rather than a
   per-edit procedure. That is what the tool's reusability claim requires.
4. **It is smaller than what it replaces** (Compass: prefer the reframe that
   shrinks the work).

**What it costs — three honest problems.**

1. **Mined is not justificatory.** AMIE finds regularities. Mitigation: (c) as
   validation; report the fraction of mined rules that fail the direction test —
   that number is itself a result about rule mining.
2. **Confidence/support thresholds are a judgement call**, same species as
   rigid/mutable. Publish as contestable parameters, per [T-027].
3. **We inherit their coverage.** AMIE mines only what the KG supports; sparse
   relations get no rules, which interacts with [T-023]'s rigid-relation count.

**What survives from the in-context framing.** The claim that *the contradiction
is reachable* is still what makes the orphan matter, and in-context reachability
is still the natural expression of it. It is now a validation signal rather than
the discovery mechanism.

**The circularity pre-emption still applies, and is now cleaner.** Direction is
established *externally* (mined rules) and *in-context on the UNEDITED model*
(validation); orphaning is measured *parametrically on the EDITED model*. Three
separable stages. If any two collapse into one measurement, the design is circular.

**Falsification of the gate.** Hand-label grounds for ~20 edits. If **mined rule
bodies** do not agree with hand-labelled grounds above chance, (e) fails and we
fall back to (c) as discovery, then to (b), then to a non-reusable v1. Second
check: what fraction of mined bodies pass the (c) direction test — a low fraction
means the rules are associative and (e) is unsafe even where it agrees.

**Status: unresolved.** No data. This is the first spike, not an assumption.

---

# WHY — is it worth doing at all?

## 1 · Significance

**If confirmed** (contested sets are common; editors break ~0 kernels): editing
papers gain a reportable column — *% of edits requiring human discretion*; anyone
deploying weight edits gains an audit step that currently does not exist; and the
implicit claim that weight editing is a clean knowledge-update mechanism is
qualified in a specific, measurable way.

**If denied** (contested sets are rare, or editors do retract grounds): backward
coherence is a smaller problem than argued, the field can stop worrying about it,
and we publish that. A negative here is cheap and genuinely useful — it retires a
concern rather than leaving it as folklore.

Both branches change something. Lens passes.

## 2 · Prior art & positioning — **RUN 2026-09-10 [R-002]. GATE CLEARED.**

Must be searched, not recalled, before anything is built. Required checks:

- **EasyEdit / EditPropBench / RippleBench / RippleEdits / JNO / KnowledgeSmith** —
  does any already emit a partition or a discretion signal rather than a score?
- **Belief revision × LLMs** — AGM/entrenchment applied to neural models. Likely
  exists; must be found.
- **Knowledge-conflict detection** — contradiction detection between parametric
  and contextual knowledge is an active area and is the nearest neighbour.
- **Abstention / deferral / selective prediction** — "when should the model hand
  to a human" is a large literature. If this is a special case of it, say so.

**Findings [R-002].** Backward gap reconfirmed independently by 2606.10554
(ISWC 2025) — forward/entailed only, 24% gap for ROME and FT. Knowledge-conflict
survey 2403.08319 names editing as a cause of *intra-memory conflict*, but defines
that as **paraphrase inconsistency**, not justification contradiction, and
contains no method that identifies post-edit conflicting facts, separates
logic-resolvable from underdetermined, or routes to a human. Deferral literature
triggers on **uncertainty**, not underdetermination. AGM->LLM transfer unclaimed
(2608.14567 is purely symbolic). Bonus: 2605.28839 finds edits **suppress rather
than overwrite** — mechanistic support for T-011, cite rather than re-derive.

**Positioning, revised (the provisional sentence was insufficient — intra-memory
conflict is adjacent):**

> Prior work measures **whether** an edit produced an inconsistency — forward
> entailment gaps, paraphrase inconsistency — or defers on **model uncertainty**.
> None asks whether the inconsistency is one **logic can resolve**, and none
> surfaces the irreducibly-underdetermined remainder for a human. The
> contribution is the **partition and the queue**, not the detection.

**Remaining scoop surface:** EasyEdit and other toolkits not inspected directly.
T-003 (RippleBench distance swap) unchecked.

### 2a · Mechanism note — edits *suppress*, they do not *overwrite* [2605.28839]

Load-bearing for T-011, and it cuts both ways. Recorded here because the design
now leans on it.

**The distinction.** *Overwrite* would mean the parameters encoding
`Eiffel -> Paris` are changed so Paris is no longer retrievable — the old
association destroyed. *Suppress* means the old association remains fully
encoded, and the edit installs something that **outcompetes** it at output time.

**Their evidence, which is close to dispositive.** A compact binary mask over the
edited weights restores the *pre-edit* answer in >70% of held-out cases. Had ROME
overwritten Paris, masking the edit would recover nothing — there would be nothing
left to recover. Recovery by a small mask proves the original was never removed.
Second result, same direction: injecting the mask *during* editing drops edit
success from 98% to 38%, so the mechanism is what the edit depends on to work.
Their stated mechanism is that the mask "reverses edits by eliminating
overattention in later layers."

**Worked example.** Edit `"The Eiffel Tower is located in ___" -> Rome`.
Under overwrite, masking the edit leaves nothing to fall back on. Under
suppression — what they observe — masking returns **"Paris"** immediately. The
override fires on inputs resembling the edit prompt; ask "what *country* is it
in?" and it fires weakly, so intact Paris machinery answers **France**. Ask about
the 1889 Exposition and it never fires at all: that knowledge was never in the
blast radius.

**Consequence 1 — T-011 gains a mechanism.** Contraction requires *removing
support* for a proposition. Suppression *adds an override on top of* the support.
ROME therefore cannot break a kernel even in principle; it can only mask the
conclusion. "Expansion operator with no contraction primitive" now has a concrete
mechanical form. Converges with *Forgetting is Not Erasure* (2606.02860) on
accessibility-vs-destruction from a different direction.

**Consequence 2 — the orphan is WORSE than modelled.** We assumed grounds sit
intact while the conclusion genuinely changed. Under suppression the original
conclusion is *also still live underneath*. The model simultaneously holds the new
answer, the old answer, and the full grounds for the old answer.

**Consequence 3 — a seam in our own ontology.** If the edit only suppresses
output, one can argue the model's *belief* never changed, only its behaviour did —
so is the orphan a contradiction in beliefs or an output/belief mismatch?
`definitions.md` declaration 1 answers by fiat: a fact **is** its probe behaviour;
superposition and mechanism are not our ontology. We are internally consistent,
but this paper puts pressure on the seam and the answer must be ready in advance,
not improvised. See lens 10.

**Caveat — status of this note.** Everything above rests on the **abstract only**.
"Overattention" is their term with our gloss. Before this enters any external
document or is relied on in the T-011 argument, the paper must be read properly
and "suppression" checked against their actual analysis rather than a headline
simplification. Ticket **R-005**.

---

# WHAT — what exactly is the claim?

## 3 · Completeness — the question family

One contested rate is an anecdote. For the result to be believed:

1. Does it hold across **editors** (ROME, MEMIT, FT)? If ROME only, it is an
   artifact of a rank-one update, not a property of editing.
2. Does it vary with **relation modality** (rigid vs mutable)? Required — it is
   also the control.
3. Does it scale with **kernel count / justification redundancy** (T-009)?
4. Do **humans actually disagree** on the contested set and agree outside it?
   Without this the partition is unvalidated.
5. Does it survive a **second model**? Deferred to v2, but named.

## 4 · Falsification — stated in advance

- **Confirm:** contested sets are large; editors retract approximately nothing;
  annotators disagree on flagged items and agree on unflagged ones.
- **Deny:** editors *do* break kernels at meaningful rates — grounds fall where
  coherence demands. Orphaning is then not a real phenomenon and §0 was moot.
- **Null:** the partition does not predict annotator disagreement. The tool is
  then not measuring discretion, whatever else it measures.

**Pre-committed:** our prediction is partly a *non-difference* (rigid grounds
behave like mutable ones). That requires equivalence testing, not a failed
significance test, and it needs the forward panel alongside to show the same
model does move where it should.

---

# HOW — can it be measured cleanly?

## 5 · Method & construct validity

Grounds discovery: §0. **Partition rule: direction splits first, modality
second** — the buckets derive from graph position rather than being stipulated:

| | rigid relation | mutable relation |
| --- | --- | --- |
| **out-edge** (consequence) | `entailed` | `entailed` |
| **in-edge** (justification) | **`contested`** — largest implausibility | `preserved` — cheap reconciliation exists |

**Revised by [E-002].** Rigidity is a **plausibility modifier, not a contradiction
test**: it blocks the *relocation* reconciliation only, and other reconciliations
survive (repatriation, emigration, distant naming). So the in-edge row is a
gradient, not a dichotomy, and `contested` membership is a threshold on introduced
implausibility — published as a contestable parameter.

**Boundary — show structure, never ranking.** In-degree and input-depth are
structural facts the tool reports. The moment they are sorted into "this is the
one to give up," the tool has built an entrenchment ordering and is deciding on
the operator's behalf (T-025). Report the structure; the human ranks. Measurement: **sign-free** — *was any kernel broken at
all* — never *should this particular ground have fallen* (T-010, amended).
Sign-free measurement is what removes the need for per-ground ground truth, and
it is also what keeps the instrument out of the adjudication business.

**Construct validity of "contested."** There is no ground truth for this bucket
by construction. Its validation is annotator disagreement (lens 3.4) — the
subjectivity is the signal, not a defect to apologise for.

**Construct validity of "rigid."** A judgement imposed on a continuum
(citizenship, `capital-of`, `works-for` are genuinely unclear). Mitigation: label
per **relation type**, not per fact; publish the table as contestable data; report
the ambiguous fraction as a result in its own right (T-027).

## 6 · Confounds & controls

| Confound | Control |
| --- | --- |
| Generic instability — every edit jiggles everything | **Matched groups:** rigid vs mutable grounds, same edits, same templates. Instability cannot know which relations are time-rigid. |
| Topical association masquerading as justification | **Detected, not merely controlled:** symmetric Δ classifies as association (§0). Matched groups as independent second check. |
| Edit magnitude | A different edit of comparable magnitude, swept identically (existing CLAUDE.md requirement). |
| Prompt fragility / frequency / fluency | Template-matched probes across groups; report per-template. |
| Annotator priming | Blind annotators to the tool's label and to which condition an item came from. |

## 7 · Baseline — the dumbest explanation

**Baseline 1 (the real threat):** contested items are simply facts the model was
never confident about. Predict "contested" from **pre-edit log-prob and entropy of
the ground alone**. If that predicts as well as kernel structure, we have nothing.

**Baseline 2:** the lexical triage buckets already in `CLAUDE.md` —
`shares_subject` / `shares_relation` / `shares_object`. If string overlap with the
edit predicts the partition, the justification machinery is decoration.

The claim must be stated as *kernel structure predicts discretion **after**
removing confidence and lexical overlap*.

---

# HOW MUCH — can it actually be done?

## 8 · Scope & feasibility

**In v1 (revised 2026-09-10, model confirmed by [E-003b]):** **GPT-J-6B via NDIF**, possession-filtered; ROME; CounterFact
restricted to the labelled rigid/mutable subset (**T-023**); **hand-built
deductive ground sets** rather than mined discovery; sign-free measurement;
annotation study of ~50 contested items.

**Why the model grew — now measured, not argued [E-003/E-003b].** Possession
top-1 by constrained rank: gpt2-medium 61%, gpt2-large 62%, **GPT-J-6B 73%**,
Llama-3.1-70B 93%. Flat inside the GPT-2 family, stepping at scale boundaries. A
model that never held a ground cannot orphan it, so at GPT-2 scale ~39% of
rigid-relation edits would be artifacts of ignorance. GPT-J is the smallest model
that clears the bar with filtering, which is exactly the amended rule.

**The audit model must BE the edited model.** Measuring possession on Llama while
editing GPT-J would be incoherent. Llama-70B establishes that possession is
scale-dependent — context and control, not the pilot's subject.

**Selection constraint [E-003b].** GPT-J is weakest exactly where grounds are
richest: P19 birth 53%, P20 death 60%, P740 formation 60%. Edit selection must be
stratified by relation *and* possession-filtered, or the usable pool silently
collapses onto P138/P495 — easy, and ground-poor.

**Why grounds are hand-built here.** E-002 showed grounds *as expressed in
Wikidata* are evidential. That is a property of Wikidata's schema, not of
knowledge — the schema has `place of burial` but cannot express
"city-in-France ^ tower-in-city => tower-in-France". Hand-building tests whether
deduction exists at all rather than whether a KG encodes it.

**Scope of the resulting claim — binding.** Hand-picked sets support an
**existence** claim ("contraction never occurs even where entailment is
explicit") and NOT a **frequency** claim. No rate may be estimated from them.

**v1 dependency — RESOLVED [R-005a].** `dice-group/Benchmarking-KE`, **MIT
licensed**; Zenodo v1.0.0 DOI `10.5281/zenodo.15697400`. The AMIE-mined rules ship
with the repo (`/evaluate_rules/all_triples/`), and the regeneration pipeline is
documented and runnable (`SparqlQuery.py` -> `amie-dev.jar` -> `generateQA.py`).
Their models are GPT-2 medium/large/XL and their editors ROME/MEMIT — the setting
matches ours closely enough to reuse.

**But their edit sets are MQuAKE and MLaKE, not CounterFact.** Options, decided at
E-001, with (1) the working assumption:

1. **Re-run their pipeline over CounterFact entities** — MIT licence, public
   DBpedia endpoint, three documented steps. Keeps our edit set. *Preferred.*
2. Switch v1 to MQuAKE — free rules, but abandons the CounterFact relation work
   and MQuAKE is multi-hop by construction, entangling the forward panel.
3. Intersect CounterFact with their triples — cheapest, coverage unknown, likely
   thin.

**Partially reopens T-023:** the rigid/mutable inventory must be run over
whichever vocabulary we mine, and that is now more likely DBpedia than Wikidata.

**Deferred to v2, explicitly:** MEMIT and FT; a second model family; the code
domain and compiler oracle; activation-patching grounds discovery (§0 method b);
RippleBench distance-function integration (T-003); the movement sweep.

**Feasibility.** Compute is not the constraint — NDIF provides GPT-J-6B, and the
pilot is ~50 edits. **The annotation study is** — it needs 2-3 people who will
actually do it, and none are identified. Still the most likely thing to stall
this, and still no technical fix. Name them before building.

**New dependency:** ROME on GPT-J via NDIF. rome-neighbors already runs this
stack, so it is reuse rather than new infrastructure [T-005].

---

# CHECK — would it survive contact?

## 9 · Deliverable — design backward from this

**One number:** the **contested rate** — the fraction of edits leaving at least
one intact justification set that coherence required breaking — reported beside
its validation, the annotator agreement inside versus outside the flagged set.

**One figure:** two panels. Forward — the model updates where it should.
Backward — rigid and mutable grounds are indistinguishable, i.e. nothing was
retracted where something had to be. The asymmetry between panels is the claim;
the backward panel being null is informative only because the forward one is not.

Every experiment must serve one of these. Anything that serves neither is cut.

## 10 · Adversary — pre-emptions

| Attack | Answer |
| --- | --- |
| "Your grounds are hand-picked." | §0 discovers them from mined Horn rules (external artifact); hand-labels appear only as the gate's validation set. |
| "Mined rules are correlations, not justifications." | Conceded, and measured: every mined body is checked with the directed intervention test, and the **fraction failing** is reported as a result about rule mining rather than hidden. Thresholds published as contestable parameters. |
| "Rigid/mutable is your opinion." | Published as a contestable table, labelled per relation type; ambiguous fraction reported. |
| "Contested is unfalsifiable." | Validated against annotator disagreement (3.4, 4-null). |
| "This is just low-confidence facts." | Baseline 1, lens 7. |
| "This is just lexical overlap." | Baseline 2, lens 7. |
| "You are arguing from a null." | Equivalence testing plus the forward panel. |
| "AGM does not apply to a probabilistic model." | The graph is a **normative audit spec**, not a model of the network (definitions.md §4). We import the norm, not the mechanism. |
| "Isn't this abstention / selective prediction?" | Deferral triggers on model **uncertainty**; we trigger on **logical underdetermination** — a confident model can still face a choice logic cannot make. **Baseline 1 (lens 7) is precisely the test:** if confidence/entropy predicts the contested set as well as kernel structure, we have reinvented selective prediction and should say so. |
| "These are not contradictions — a satisfying world exists for every case." | **Conceded, and it is now the claim.** The measured relation is evidential, so we assert joint *implausibility*, not inconsistency (declaration 6). Claiming contradiction would be refutable by one satisfying world; claiming implausibility is not, and it is what makes human adjudication structurally necessary rather than convenient. |
| "Isn't this intra-memory conflict (2403.08319)?" | That is defined as paraphrase inconsistency — differing answers to semantically equivalent inputs. An orphan is one answer held alongside a coherent set entailing its negation. Different construct; the survey lists no method that partitions or routes. |
| "GPT2-medium is a toy." | **Superseded 2026-09-10** — moved to GPT-J-6B via NDIF, because possession is a construct requirement [T-039], not because scale is impressive. |
| "Edits only suppress output (2605.28839), so the belief never changed — your 'contradiction' is an output/belief mismatch, not an inconsistency." | `definitions.md` declaration 1: a fact **is** its probe set. Behaviour is the ontology; mechanism is not. Under suppression the orphan is *worse*, not milder — new answer, old answer, and old grounds are all simultaneously live. **This is the sharpest available attack; answer must be pre-written, not improvised.** See §2a. |
| "You are proposing a method — beat JNO." | It partitions, it does not edit or repair. Different question; JNO is not a comparator. Boundary: **outputs a queue, never a repair.** |

---

## What would stop this

1. ~~Lens 2 finds it done.~~ **Cleared 2026-09-10 [R-002]** — not scooped;
   positioning revised against intra-memory conflict and uncertainty-based
   deferral. Residual risk: EasyEdit not inspected.
2. **§0 fails** — no mechanical grounds discovery. Falls back to a hand-labelled
   one-off; the reusability claim dies.
3. **T-023 finds too few rigid relations** in CounterFact to power the study.
4. **No annotators.** Lens 8. Non-technical and currently unsolved.

## Next actions, in order

1. ~~R-002 — run lens 2.~~ **Done 2026-09-10, gate cleared.**
2. **E-001 (spike)** — the §0 gate on ~20 hand-labelled edits: do **mined rule
   bodies** agree with hand-labelled grounds, and what fraction pass the directed
   direction test? Time-boxed. The single thing between this design and its first
   data.
3. **R-003** — T-023, the CounterFact relation inventory, rigid/mutable labelled.
4. **R-004** — close the residual scoop surface: EasyEdit and T-003. ~~RULE-KE~~
   **checked [R-005a]**: 2405.15452 uses rule discovery to *improve* editing —
   forward, and a method, so it sits in JNO's class, not ours.
5. **R-005a** — ~~artifact obtainable?~~ **Done: yes, MIT, rules included.**
6. **R-005b** — still open: read 2605.28839 properly (§2a rests on its abstract
   and the design leans on it twice); recover 2606.10554's 24% figure from the
   body; extract concrete example rules; settle the DBpedia-vs-Wikidata
   discrepancy between the repo and the paper text.

Per confidence gating, R-001 is **medium**, so dependent work opens as spikes.
