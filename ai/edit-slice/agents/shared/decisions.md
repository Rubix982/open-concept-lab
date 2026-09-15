# Decisions — edit-slice

_Owned by: Engineer. Append-only._

---

## [E-002] Decision: grounds are evidential, not deductive — AGM's ordering half, not its closure half

_Date: 2026-09-10_

**Decision:** Model the edit-to-grounds relation as **evidential support**, not
entailment. `orphan` becomes a **graded** quantity: the joint implausibility an
edit introduces, reported with the specific facts carrying it. Kernel contraction
and minimal hitting sets are dropped as machinery. AGM is retained as the account
of the *problem* — revision requires giving something up, logic does not say what —
with its **ordering** side (epistemic entrenchment, Grove spheres, Lewis-Stalnaker
closest-world) replacing its **closure** side (kernels, partial meet).

**Rationale:** E-002 measured it. None of five hand-read rigid-relation cases
produced a strict contradiction — died-Barcelona/buried-Baltimore, developer-IBM/
publisher-Sega, named-after-Hamburg/serves-London, native-Russian/born-Paris,
born-Milwaukee/citizen-Finland are all satisfiable. An earlier claim of ours was
wrong: time-rigidity blocks the *relocation* reconciliation only, and does not
establish contradiction. Strict cross-property contradiction is rare in this data,
so a deductive instrument would find almost nothing and would drift back into
RippleEdits' territory.

The change also strengthens the project's thesis rather than weakening it. If
grounds were deductive, a machine could compute the contraction and human
discretion would be a convenience. Because support is evidential, **logic cannot
adjudicate**, so the decision structurally belongs to a person — which is the
T-025 argument in its strongest form. The tool's output becomes "this edit made
these facts jointly improbable, confirm?" rather than the false claim
"contradiction detected".

**Alternatives rejected:**
- *Keep kernels, restrict to the deductive subset.* Small, mostly definitional,
  and converges on inverse/symmetric relations — which RippleEdits' Logical
  Generalization already covers [R-001].
- *Keep "contradiction" as loose vocabulary over evidential relations.* Rejected:
  a single satisfying world refutes it, and it is the fastest attack surface a
  reviewer has.

**Costs, accepted knowingly:**
- [T-008]'s termination argument weakens. "Kernels are finite so backward needs no
  `k`" presupposed entailment. Evidential support has no natural boundary and needs
  a threshold — a parameter, published contestable like
  `probes/relation_modality.md`. The forward/backward asymmetry we claimed on
  boundedness is partly given back.
- `orphan` is no longer crisp.
- [R-003]'s rigid/mutable table is **reinterpreted, not discarded**: rigidity is a
  plausibility *modifier*, not a contradiction test.

**Revisit if:** the graded measure proves unrankable in practice (no stable
threshold separating "materially implausible" from "slightly moved"), or if a
deductive subset large enough to power a study is found after all.

---

## [O-004] Decision: raise the model to GPT-J-6B via NDIF; hand-build deductive grounds for the pilot

_Date: 2026-09-10_

**Decision:** Amend `CLAUDE.md`'s blanket size cap. The pilot moves from
GPT2-medium to **GPT-J-6B via NDIF**, and the pilot's ground sets are
**hand-built and deliberately deductive** rather than discovered.

**Rationale — two independent reasons, neither of them ambition:**

1. **Possession is a construct requirement [T-039].** A model that never held a
   justification cannot orphan it. If GPT2-medium does not know Perec was born in
   Paris, the "ground" is not left standing — it was never there — and the
   phenomenon is unobservable regardless of whether it is real. The audited system
   must possess the beliefs being audited. NDIF removes the resource objection.
2. **Wikidata's schema is not knowledge's schema.** E-002 concluded grounds are
   evidential from what Wikidata expresses. Wikidata has `place of burial`; it
   cannot express "city-in-France ^ tower-in-city => tower-in-France". Letting a
   KG's property set decide whether deduction exists was a category error.
   Hand-building asks the sharper question directly: **does contraction ever
   occur, even where entailment is explicit?**

**Scope of the claim this licenses — binding.** Hand-picked ground sets support an
**existence** claim and never a **frequency** claim. "Contraction does not occur
even where entailment is explicit" is defensible; "contraction fails in N% of
edits" is not, and these sets may not be reused to estimate a rate. The
circularity of §5 is acceptable for existence and fatal for frequency.

**Alternatives rejected:**
- *Stay at GPT2-medium.* Risks measuring a null produced by ignorance rather than
  by the editor — the same trap T-023 raised for relation modality, one level up.
- *Continue with mined evidential grounds only (E-002's plan).* Deferred, not
  rejected: it answers frequency, and frequency is meaningless until existence is
  settled.

**What this does not overturn:** [E-002] stands. Grounds encountered in the wild
are evidential, `orphan` is graded, AGM's ordering half is still the formalism.
This decision adds a deductive *probe* to test a sharper case; it does not restore
kernels as machinery.

**Revisit if:** GPT-J also fails to hold hand-built grounds reliably (then
possession, not editing, is the bottleneck and the domain must change), or if
contraction *does* occur on deductive sets — which would make the frequency
question live again and reopen [E-002]'s deferred half.

---

## [E-007] Decision: candidates come from a reference vocabulary, not the edit set

_Date: 2026-09-13_

**Decision:** `candidate_pool` takes an explicit `reference` set, separate from the
edits being filtered, and every unscoreable item is reported in `skipped` with a
reason rather than dropped.

**Rationale — measured, on the first end-to-end run.** Deriving candidates from the
edit set itself scored only **12 of 40** items and returned **92%** held. The 28
missing items were relations with fewer than three attested answers, and what
survived were the two relations dense enough to be easy. With a reference
vocabulary: **100% coverage, 52% held** — consistent with E-005's 56% for the same
model.

A 40-point inflation produced by a silent denominator change is exactly the
selection artifact this filter exists to detect. Shipping it inside the detector
would have been the worst available outcome, and it was found by running the tool
rather than by reading it.

**Alternatives rejected:**
- *Warn and continue with edit-set candidates.* A warning does not fix a biased
  denominator, and the headline number would still be wrong.
- *Fail on sparse relations.* Too brittle; partial coverage is legitimate provided
  it is reported. Hence `coverage`, plus an explicit warning below 80%.

**Two collisions fixed alongside, both correctness rather than tidiness:**
- Cache keyed on model alone would serve a 50-candidate result to an 8-candidate
  run — same `case_id`, different number. Now keyed on a `fingerprint` over
  everything that changes a value (model, n_candidates, seed, placeholder); date
  excluded, since it records when rather than what.
- Output named per model would let two configs overwrite each other. Now named
  after the config.

**Revisit if:** a user's edit set has relations absent from any available reference
vocabulary. Currently that surfaces as 0% coverage with a clear reason, which is
correct but unhelpful; generating candidates from the relation's value type would
be the fix.


---

## [O-005] Decision: large models only — the size floor replaces the size ceiling

_Date: 2026-09-15_

**Decision:** work only with very large models. From NDIF's ungated set that is
**Llama-3.1-70B** (possession 79%) and **Llama-3.1-405B** (85%). GPT-J-6B and the
8B tier are out.

**Supersedes [O-004]'s rule**, which was *"choose the smallest model that
demonstrably holds the grounds; small and legible still wins every tie."* That rule
was derived to justify moving OFF GPT2-medium and was written as a ceiling-with-a-
floor. It is now a floor only.

**Rationale:** the gate result forced it. On GPT-J only **20 of 136** chains had all
three legs held (15%) — thin for an existence claim and fragile if a few fail the
edit. Possession is 56% on GPT-J against 79% at 70B, so the usable set should
roughly double. Directed by the user 2026-09-15.

**Consequence that is not yet paid for.** [E-003b] established the audit model must
BE the edited model, so gating on 70B commits the edit to 70B. [E-006] verified
editability — intervention plus remote gradients — on **Llama-3.1-8B**, not 70B.
ROME at 70B needs second-moment statistics over d_mlp 28672, roughly 3.3 GB fp32,
which has been neither collected nor costed. 405B is worse: d_mlp 53248, ~11 GB.

**Revisit if:** the covariance collection at 70B proves impractical, in which case
the honest options are to run the edit at a scale we can actually edit and report
the possession ceiling as a limitation, or to drop the edit arm entirely and ship
the audit instrument alone.

---

## [E-009] Result: the gate clears at 70B, and the three legs are not independent

> **Partly superseded the same day — see [E-009b].** The concentration
> explanation for the `outer` deficit is wrong. The measured numbers in this
> entry stand; the mechanism in its last paragraph does not.

_Date: 2026-09-15 · Llama-3.1-70B via NDIF, same 136 chains and same pools as GPT-J_

| position | fact | GPT-J-6B | Llama-3.1-70B |
| --- | --- | ---: | ---: |
| `inner_1` | X born in Y | 35% | 84% |
| `inner_2` | Y in country Z | 61% | 92% |
| `outer` | X born in Z | 21% | 57% |
| — | **usable chain** | **15%** (20/136) | **54%** (74/136) |

**Decision:** the edit arm runs on the 70B set. 74 usable chains is enough for an
existence claim with room for edit-stage attrition; 20 was not.

**[O-005]'s prediction was wrong, and in a way worth keeping.** It read *"possession
is 56% on GPT-J against 79% at 70B, so the usable set should roughly double."* The
usable set went up **3.7×**. The estimate treated a per-fact rate as if it
transferred directly to a per-chain one, which it does not — a chain is a
conjunction over three legs, so its rate moves faster than any single leg.

**And the conjunction is far from independent.** Multiplying the three marginals
predicts 4.5% usable at GPT-J against 14.7% measured — the real joint is **3.27×**
what independence gives. At 70B the same comparison is 43.6% against 54.4%, a lift
of only **1.25**.

| pair | GPT-J lift over independence | 70B lift |
| --- | ---: | ---: |
| `inner_1` & `outer` (share subject X) | **2.10** | 1.15 |
| `inner_2` & `outer` | 1.53 | 1.09 |
| `inner_1` & `inner_2` (share no subject) | 1.26 | 1.00 |

The lift is ordered by shared subject, and it collapses with scale. The reading:
at 6B, possession clusters per entity — a chain about a well-known person tends to
hold at every leg and a chain about an obscure one at none, so the binding variable
is subject familiarity rather than leg difficulty. At 70B nearly every subject is
familiar, that variance is spent, and what remains is the leg-specific deficit
(`outer`, 57%), which is why the pair lifts fall to ~1.

**Why it matters beyond this experiment.** Chain attrition is the cost model for
every longer chain we might build. Under independence a 5-hop chain at 70B would be
unusable; at the measured dependence it is merely expensive. Anyone costing a
multi-hop design off marginals alone will under-build.

**`outer` stays the worst leg at both scales**, which rules out small-model
thinness and leaves candidate-pool concentration — countries have 28 distinct
fillers, US alone 40/136, top four 57%, against 78 cities whose top four reach 16%.
Unmodelled in `possession.py`; same family as the [E-007] denominator bug.

**Revisit if:** the 70B covariance collection for ROME proves impractical — see the
unpaid consequence recorded in [O-005].

**Artifacts:** `probes/chains_gated_meta-llama_Llama-3.1-70B.json`,
`probes/chains_gated_EleutherAI_gpt-j-6b.json`,
`logs/gate_chains-llama-3.1-70b-2026-09-15.log`


---

## [E-009b] Correction: the `outer` deficit is answer surface form, not pool concentration

_Date: 2026-09-15 · re-analysis of data already on disk, no new compute_

**RCA.** [E-009] closed with *"`outer` stays the worst leg at both scales, which rules
out small-model thinness and leaves candidate-pool concentration — countries have 28
distinct fillers, US alone 40/136."* That reasoning inferred a mechanism from a
marginal count without ever joining the held/not-held flag against the answer string.
Joining it dissolves the explanation: the deficit is not spread across a concentrated
pool, it is **two strings**.

| `outer` answer | Llama-3.1-70B held | GPT-J-6B held |
| --- | ---: | ---: |
| United States | **6/40 = 15%** | 0/40 |
| United Kingdom | **2/14 = 14%** | 0/14 |
| France | 13/13 = 100% | 6/13 |
| India · Spain · Japan · Sweden · Finland | 100% each | 20–100% |

Grouped: **15% for article-taking names (n=54)** against **84% for bare names (n=82)**.

Concentration and surface form were perfectly confounded, because the countries that
take a definite article are also the most frequent ones. Frequency was the visible
variable, so it got the credit.

**A second hypothesis, raised and killed in the same pass.** That the placeholder
control was misfiring — ranking a prior-favoured country first regardless of subject,
failing the lift test on facts the model does hold. Checked against `rank_prior` in
the cache: **1 item of 136** fails that way. Not the cause. Recorded because a
discarded hypothesis that was never written down reads later as one never considered.

**Leading explanation, not yet confirmed.** `"X was born in the country of"` followed
by `" United States"` is ungrammatical where `" France"` is fine. We score a Wikidata
label rather than a natural continuation, and the penalty lands exactly on the two
most common answers. **E-011 is the decisive test** — score the same 136 items across
surface variants (`" United States"` / `" the United States"` / `" America"` / `" the
US"`). If rank-1 recovers, it is a template defect and cheap to fix; if it does not,
the model genuinely lacks these facts and that is the more interesting result.

**Size.** 28 chains are blocked *only* by a US/UK `outer` leg. Usable would move
**74/136 → 102/136**, 54% → 75%.

**The pattern worth naming.** This is the third member of one family, after the
[E-007] denominator bug and the template check: a selection effect living inside a
measurement tool, found by re-reading data already on disk rather than by collecting
more. Three for three. Any future surprise should be searched for here first.

**Revisit if:** E-011 shows surface form does not recover rank-1.

---

## [E-011] Result: the possession measure has no operating point for modal answers

_Date: 2026-09-15 · Llama-3.1-70B, 136 `outer` items, two renderings of one 28-country pool_

**The pre-stated Deny branch fired, and it was the wrong dichotomy.** [E-009b]
predicted that rendering countries naturally would recover the article-taking names
to roughly the bare-name rate. Held rate went 19% → **16%**. On the headline number
the hypothesis failed.

The rank data says the opposite, and the two together are the actual result.

| condition | answer class | n | ranks 1st **with subject** | ranks 1st **with placeholder** | held |
| --- | --- | ---: | ---: | ---: | ---: |
| `bare` | article-taking | 58 | 21% | 2% | 19% |
| `bare` | bare-name | 78 | 85% | 0% | 85% |
| `natural` | article-taking | 58 | **69%** | **69%** | **16%** |
| `natural` | bare-name | 78 | 83% | 0% | 83% |

**Surface form was real.** Rendering `" the United States"` instead of the Wikidata
label moves rank-1-with-subject from 21% to 69%. The model was never failing to know
these; it was failing to complete an ungrammatical string.

**And fixing it destroys the control.** Under `natural`, the placeholder prompt ranks
the same answer first at exactly the same rate — 69%. Of the 40 article-taking items
that rank first with the real subject, **31 are rejected by the lift test, and all 31
because `rank_prior == 1`.** `"[X] was born in the country of the United States"` is
the modal completion whether or not `[X]` means anything.

**The finding, which is about our instrument and not about Llama.** The two criteria
are in tension for any answer with a high unconditional prior. A rendering that makes
the answer rankable also makes it prior-favoured; a rendering that suppresses the
prior does so by being ungrammatical. **There is no rendering that satisfies both**,
so `possession.py` cannot certify possession of a fact whose answer is the modal
answer for its relation. Bare-name countries show 0% placeholder rank-1 under both
renderings — the measure is sound there, and undefined here.

This is a scope limitation of the shipped deliverable and must be documented as one.
It is also why the [E-009b] "28 recoverable chains" ceiling of 102/136 was wrong:
under `natural` usable moves 74 → **71**, not up.

**What it implies for the design.** The placeholder control asks *"does the subject
matter at all"*, which a modal answer defeats by construction. The stronger question
is *"does the model track WHICH subject"* — score the true answer against a **paired
real subject whose true answer differs**, and require the model to prefer the right
one. That discriminates knowledge from prior without needing the prior to be low.
Opened as E-012; it is a change to the measure, so it must not be retrofitted
silently into numbers already published.

**Honest note on how this was found.** Three bugs were fixed in the analysis script
before any number here was read, one of which — using `FilterReport.kept()`, which
returns only HELD items, as the set of scored items — would not have crashed. It
would have printed 100% in every cell and read as a spectacular confirmation of the
hypothesis under test. The reporting path was dry-run against the cached `bare`
condition and made to reproduce the [E-009] baseline of 57% before any conclusion was
drawn from it.

**Artifacts:** agents/engineer/workspace/surface_forms.py;
results/E-011-surface-forms-meta-llama_Llama-3.1-70B.json;
logs/surface_forms-2026-09-15-120017.log

---

## [O-006] Decision: the edit arm runs at Llama-3.1-8B

_Date: 2026-09-15 · supersedes [O-005]'s commitment of the edit to 70B_

**The gate at three scales**, same 136 chains, same pools, same seed:

| model | `inner_1` | `inner_2` | `outer` | usable |
| --- | ---: | ---: | ---: | ---: |
| GPT-J-6B | 35% | 61% | 21% | 20/136 = 15% |
| Llama-3.1-8B | 65% | 90% | 49% | **58/136 = 43%** |
| Llama-3.1-70B | 84% | 92% | 57% | 74/136 = 54% |

Restricted to the domain [E-011] shows the measure is defined on — the `outer` answer
is not the modal answer for its relation:

| model | `inner_1` | `inner_2` | `outer` | usable |
| --- | ---: | ---: | ---: | ---: |
| GPT-J-6B | 45% | 92% | 37% | 20/78 = 26% |
| Llama-3.1-8B | 73% | 97% | **77%** | **51/78 = 65%** |
| Llama-3.1-70B | 87% | 99% | 85% | 64/78 = 82% |

**Decision:** run the edit at Llama-3.1-8B. 51 usable chains on the defined domain is
ample for an existence claim, which is the only claim [O-004] licenses from
hand-built sets.

**Rationale.** [O-005] committed the edit to 70B and recorded the unpaid consequence:
ROME at 70B needs second-moment statistics over `d_mlp` 28672, ~3.3 GB fp32, neither
collected nor costed, while [E-006] verified editability only at 8B. That obstacle
existed **solely because nobody had run the gate at 8B**. The assumption that 8B
would be too thin was never tested; it is false. The cheapest way past the problem
was to discover it was not there.

**What 70B buys and what it costs.** A quarter more chains — 64 against 51 on the
defined domain. Against that: an uncosted covariance collection, an unverified
editing path, and a slower loop on every iteration of an experiment that has not run
once. Not worth it for an existence claim. Revisit for any frequency claim, which
would need the larger set and much more besides.

**Supersedes [O-005]** on the choice of edit model. [O-005]'s size *floor* argument
stands — the model must hold the grounds it is audited against — and 8B clears it at
73/97/77%. What does not stand is the inference from "70B possesses more" to "the
edit must happen at 70B".

**Revisit if:** the edit at 8B produces too few surviving items to distinguish
`update` / `damage` / `orphan`, in which case the 70B covariance cost has to be paid
and costed properly rather than assumed.

**Artifacts:** probes/chains_gated_meta-llama_Llama-3.1-8B.json;
logs/gate_chains-2026-09-15-120133.log

---

## [E-012] Result: the two defects are orthogonal, and fixing them beats 60B parameters

_Date: 2026-09-15 · Llama-3.1-8B, 136 chains, full 2x2 over rendering x control_

**Usable chains, same 136 chains, same model, same seed:**

| | placeholder control | paired control |
| --- | ---: | ---: |
| `bare` rendering | 58 | 59 |
| `natural` rendering | 59 | **78** |

Neither fix alone moves anything: +1 and +1. Together, **+20**. This is an
interaction, not two additive improvements, and it is why [E-011] read as a Deny and
why [E-012] on `bare` gained a single chain. Each fix removes a different blocker,
and an item needs both removed to pass.

- **rendering** fixes the **row** test — *given this subject, which answer?*
  `" United States"` after "born in the country of" is ungrammatical, so the true
  answer does not rank first however well the model knows it.
- **paired control** fixes the **control** — *given this answer, which subject?*
  and is required precisely BECAUSE natural rendering makes the answer
  prior-favoured, which is what defeats the placeholder test.

**`outer` position, the leg that was broken all day:**

| condition | row test | mean AUC | held |
| --- | ---: | ---: | ---: |
| `bare` + paired | 50% | 0.894 | 50% |
| `natural` + paired | **74%** | **0.929** | **71%** |

On modal answers specifically (n=77), row goes 25% -> **68%** and held 25% -> **64%**.

**The comparison worth stating.** Llama-3.1-70B under the old instrument gave
**74/136**. Llama-3.1-8B under the fixed instrument gives **78/136**. Repairing the
measurement recovered more chains than an order of magnitude of scale did.

**Why this is not just a looser threshold.** The obvious objection is that the paired
control simply passes more items. The 2x2 answers it: on `bare` rendering the paired
control gives 59 against the placeholder's 58. The criterion is not systematically
more permissive — it is differently *defined*, and the gain appears only where the
old one was undefined.

**Decision:** the paired control plus natural rendering becomes the default measure.
`possession.py` keeps the placeholder path for reproducing published numbers, which
must not be retrofitted.

**Known threats, unresolved.** Foils differ from the item in subject frequency as
well as identity, and [T-061] showed prominence predicts possession level; the AUROC
is not corrected for it. `inner_1` foil coverage is 63% because its 78-city pool
exceeds `n_candidates`, so its AUC rests on a sampled foil set while `outer` and
`inner_2` are dense at 100%. Both belong in any write-up of this number.

**Artifacts:** src/discrimination.py; agents/engineer/workspace/run_e012.py;
agents/engineer/workspace/test_discrimination.py;
results/E-012-discrimination-{bare,natural}-meta-llama_Llama-3.1-8B.json;
logs/run_e012-2026-09-15-144956.log

---

## [E-013] Gate 0 resolved: the covariance term is not used by the reference implementation

_Date: 2026-09-15 · read from a local EasyEdit checkout, not recalled_

**The problem as stated.** ROME's update needs `C⁻¹k*`, the inverse second-moment
matrix of keys. Measured from the model configs: Llama-3.1-8B `d_mlp` = 14336, so `C`
is **0.82 GB** fp32 (70B: 28672 → 3.29 GB, matching [O-005]). [O-005] recorded this as
"neither collected nor costed" and it has been the stated blocker on the edit since.

**It is not a blocker, because the widely-used implementation does not use it.**
EasyEdit ships 14 ROME hparam configs. **Every one sets `mom2_adjustment: false`** —
including `gpt2-xl.yaml` and `gpt-j-6B.yaml`, the two models the ROME paper itself
used. The code path is unambiguous (`easyeditor/models/rome/compute_u.py:112-126`):

    u = cur_repr
    if hparams.mom2_adjustment:
        inv_cov = get_inv_cov(...)
        u = inv_cov @ u.unsqueeze(1)
        u = u.squeeze()

With the flag false, `u = k*`. That is exactly `C = I`.

**Decision:** run the edit with `C = I`, and describe it as *"ROME as configured by
EasyEdit"*, never as *"ROME"* unqualified. This is not the [E-013] fallback being
chosen reluctantly; it is the configuration the reference toolkit ships for every
model it supports.

**What this changes about the confound.** [E-013] warned that a diffuse editor
inflates `damage` and so biases us toward finding contraction. That physical concern
is unchanged — `C = I` is genuinely less targeted. What changes is that we are no
longer making a non-standard choice to get there. The comparable-magnitude control
edit stays **mandatory**; it is what separates contraction from collateral damage,
and with `C = I` it is the only thing that does.

**And it unblocks a remote implementation.** With `u = k*` the update is
`Δ = (v* − W k*) k*ᵀ / (k*ᵀ k*)`, so for any input with key `k` the change to the
`down_proj` output is `(v* − W k*)·(k*ᵀk)/(k*ᵀk*)` — computable inside an nnsight
trace from the observed activation. **The edited weights never need to be
materialised**, which is what makes this runnable against a shared remote model at
all. [E-006] verified both required primitives (additive intervention; gradients flow).

**Open, and not to be assumed either way:** the ORIGINAL ROME repository
(rome.baulab.info) is believed to enable the adjustment, since the paper's method
section centres on it. If so, two implementations circulate under one name and differ
on that term, which is a comparability problem for every paper reporting "ROME"
numbers from EasyEdit — including possibly our own reading of them. **Verify before
claiming it.** Opened as R-009.

**Artifacts:** /Users/saifulislam/code/EasyEdit/hparams/ROME/*.yaml;
easyeditor/models/rome/compute_u.py
