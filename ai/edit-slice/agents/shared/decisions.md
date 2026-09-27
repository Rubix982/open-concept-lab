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

---

## [E-013] Smoke test, n=1: the mandated control is too weak, and this is why

_Date: 2026-09-15 · Llama-3.1-8B, layer 5, ROME-as-EasyEdit (`C = I`), one chain_

Vlaminck: born in Paris, Paris in France, therefore born in France. Edited the
conclusion to Germany. `v*` optimisation drove NLL 5.68 → 0.02 over 25 steps.

| probe | before | after |
| --- | --- | --- |
| `outer` — born in the country of | `' France'` −1.94 | **`' Germany'` −0.02** |
| `inner_1` — born in the **city** of | `' Paris'` −0.31 | **`' Germany'` −1.44**, `' Munich'` −2.69, `' Berlin'` −2.75 |
| `inner_2` — Paris is located in the country of | `' France'` −0.07 | `' France'` **−0.08** |

**n=1 establishes nothing about contraction.** It establishes something about the
design, which is worth more right now.

**The ground that shares the subject moved; the ground that does not was inert.**
That is exactly what ROME's mechanism predicts: the update is keyed on `k*` at the
subject's last token, so any prompt containing *"Maurice de Vlaminck"* routes through
the edited direction, while *"Paris is located in..."* never touches it. The most
likely reading of `inner_1`'s movement is **subject-keyed leakage, not contraction**.

**The tell is a type error.** `' Germany'` ranks FIRST for *"born in the **city**
of"*. A model that coherently accepted "born in Germany" would name a German city, not
a country. It is genuinely ambiguous — `' Munich'` and `' Berlin'` did surface at
−2.69/−2.75, which is what coherent relocation looks like — and n=1 cannot separate
them. That ambiguity is the whole reason the control is mandatory.

**Consequence: CLAUDE.md's mandated control is necessary but NOT sufficient here.**
"A different edit of comparable magnitude on the same base model" controls for generic
instability. It does not control for subject-keyed leakage, because an edit on a
*different subject* will not touch our subject's key direction at all, and so will
show no movement on `inner_1` — making leakage look like signal.

**The control [E-013] will use instead, added to and not replacing the mandated one:**

1. **Same-subject control (new, and the load-bearing one).** Edit an unrelated
   property of the SAME subject — occupation, say — to a comparable magnitude, then
   probe `inner_1` identically. If `inner_1` moves as much under that as under ours,
   its movement is keyed on the subject and carries no evidence about contraction.
   Only movement in EXCESS of the same-subject control is a candidate.
2. **Different-subject control (as mandated).** Retained for generic instability.
3. **Type-coherence read.** Record whether the post-edit top-1 for `inner_1` is
   type-correct (a city). A type error is leakage; a type-correct answer that changed
   country is the thing we are actually looking for. This is cheap and it is the only
   signal that distinguishes the two readings directly.

**Revisit if:** the same-subject control moves `inner_1` as much as the real edit on
most chains. Then subject-keyed leakage dominates at this magnitude, no contraction
signal is separable, and the honest report is the Null branch of [E-013] —
a statement about the method's resolution, not about the model.

**Artifacts:** agents/engineer/workspace/edit_smoke.py; src/edit.py;
logs/edit_smoke-2026-09-15-162616.log

---

## [E-014] Result: the edit displaces the premise, country-specifically, at 67%

_Date: 2026-09-17 · Llama-3.1-8B, layer 5, 42 chains · recorded 2026-09-20_

**Written late.** This result was referenced by [E-015], [E-016] and the published paper
for three days without an entry of its own — found when cross-linking the paper to the
ledger produced a link with no target. The run that supplies the headline number had no
record; that is a process failure, not a data one, and the numbers below come from
`results/E-014-destination-meta-llama_Llama-3.1-8B.json` rather than from recollection.

**Setup.** Edit `outer` to a counterfactual country, then rank the full 75-city pool at
`inner_1`. Three conditions: baseline, the real edit, and a magnitude-matched
same-subject control editing the person's occupation. A per-chain **placebo country**
gives the null rate for "lands in country X".

| `inner_1` lands in… | baseline | real edit | same-subject control |
| --- | ---: | ---: | ---: |
| the **target** country | 5% | **67%** | 5% |
| the placebo country | 2% | 0% | 7% |

Twenty-eight of 42 chains relocate into the edited country against a 5% control, with the
placebo at floor. Edinburgh → Hamburg for Germany; Paris → Santiago for Chile.

**But 82% of the hits are the capital**, so the model is largely emitting the target
country's most salient city rather than choosing a plausible birthplace. Coherent and
country-specific, but shallower than "revised the premise" would imply.

**Per country, unevenly.** India 4/4, Denmark 3/3, United States 3/3, Chile 2/2, Sweden
2/2, Italy 2/2 — against New Zealand 0/3, Australia 0/2, Czech Republic 1/5. The failures
cluster by country rather than scattering, which usually indicates a data property.

**The attractor.** `Washington, D.C.` takes **14 of 42** destinations (33%), the
next-largest being Copenhagen at 3. It is the pool's highest-prior city and the sink when
no coherent relocation occurs. Third instance of a concentrated pool shaping a result here,
and the reason [T-073] made attractor mass a standard reported field.

**n.** 71 clean chains were prepared; 42 were read out. The remaining 29 were lost to NDIF
outages, not excluded by any criterion — see [O-007] for what that week's infrastructure
did. Existence claim only, per [O-004].

**What it does NOT show.** That the relocation is an inference. [E-015] tested that by
holding subject and target fixed and varying only the relation, and found a paired gap of
+0.0 pp.

**Artifacts:** agents/engineer/workspace/run_e014.py;
results/E-014-destination-meta-llama_Llama-3.1-8B.json

---

## [E-015] Result: DENY — the relocation carries no inference

_Date: 2026-09-18 · Llama-3.1-8B, 42 chains, subject and target country held fixed_

Resolves agents/shared/disputes.md [E-014]. Both arms push the same country-valued
vector through the same subject's key; only the birth edit licenses "born in a city of
that country".

| arm | lands in target country |
| --- | ---: |
| `X was born in the country of` → T (licenses the inference) | **28/42 = 67%** |
| `X works in the country of` → T (licenses nothing) | **28/42 = 67%** |
| **paired gap** | **+0.0 pp** |

Exact McNemar on the discordant pairs: **p = 1.000** (9 birth-only, 9 work-only).
Capital share among hits identical at **82%** in both arms. Where both land in target,
the destination is the **same city 84%** of the time (16/19).

**The pre-stated Deny fired.** Editing where a person WORKS relocates their BIRTHPLACE
into the new country exactly as often as editing where they were born. There is no
birth-specific inference. The relocation is country-flavoured content leaking into any
probe that shares the subject.

**What this retracts.** The [E-013] pilot reading — that the model revises the
defeasible premise while retaining the necessary one — is **withdrawn**. It was stated
in a commit message and in the running write-up and must be corrected in both. The
[E-014] result stands as measured (67% target vs 5% baseline and control, placebo at
floor) but its *interpretation* changes: it demonstrates that rank-one editing at this
configuration produces country-specific displacement, not that the model reasons about
what its edit implies.

**The dispute was raised before the number existed and was right.** `src/adversary.py`
surfaced `definitions.md` declaration 6 while checking a claim I was about to publish,
which produced the cheaper mechanism and then this control. That is the adversary agent
doing the job it was built for.

**The 43% discordance is not evidence for inference.** 18 of 42 chains disagree between
arms, but symmetrically — 9 each way — which is noise around a common mechanism, not a
systematic advantage. Reporting the two marginal rates without the pairing would have
hidden that both readings are wrong.

**Edge worth recording: a single destination attractor.** `Washington, D.C.` absorbs
**14/42 (33%)** of birth-arm destinations and 11/42 of work-arm. It is the high-prior
city of the pool, and it is where probability goes when no coherent relocation occurs.
Same family as [E-009b] and [E-011]: a concentrated pool with one dominant attractor
shapes the measurement. Any future pool must report its attractor mass.

**Consequences for design.md Part III.** Layer 2's `role in entailment` axis loses its
only supporting datum and must be marked unsupported, not merely unmeasured. Layer 3's
`ground response` axis survives as a measurement but not as evidence of revision. The
Layer-1 stability critique — the [R-010] lever — is untouched and is now the project's
strongest remaining claim.

**Revisit if:** a whitened editor (`mom2_adjustment: true`) or a different layer
produces a non-zero paired gap. `C = I` is a destructive regime ([E-013]: ~8 nat drops
on unrelated same-subject facts), and a more targeted editor is the obvious place a
genuine inference effect could still hide.

**Artifacts:** agents/engineer/workspace/run_e015.py;
results/E-015-relation-meta-llama_Llama-3.1-8B.json; logs/run_e015-2026-09-18-090608.log

---

## [E-016] Gate: whitening is a near-no-op by cosine and a 50x change in targeting

_Date: 2026-09-18 · Llama-3.1-8B, layer 5, 2048 keys over the CounterFact prompt
distribution (NOT ROME's Wikipedia — divergence recorded)_

**Anisotropy — the gate clears.** Spectrum of the layer-5 key second moment:

| | |
| --- | ---: |
| participation ratio | **26.5** of 2048 sampled dims (1.3%) |
| 50% of variance in | **16 dims** |
| 90% / 99% of variance in | 164 / 338 dims |

The keys live on an effectively ~26-dimensional manifold inside 14336. **Do not quote the
condition number** (5.4e21): with N=2048 < d=14336 the sample covariance is rank-deficient
by construction and its smallest "nonzero" eigenvalue is numerical noise.

**Consequence for feasibility.** The right model is low-rank-plus-isotropic,
`C = KᵀK/N + λI`, not a full 14336² matrix. Estimating a ~338-dim subspace needs N ≫ 338,
not N ≫ 14336 — which is why ROME needs 100k samples and we do not. Woodbury then gives
`C⁻¹k*` while forming only an N×N matrix (17 MB at N=2048). Verified against the explicit
inverse on a synthetic case: relative error 1e-5 to 1e-7.

**The finding, and it is a methodological one.**

| statistic | value | reading |
| --- | ---: | --- |
| `cos(k*, C⁻¹k*)` | **0.97** | whitening barely rotates the update |
| mean abs. coefficient on **held-out** keys, `C = I` | 0.0260 | — |
| same, `C⁻¹` at λ=7.2e-03 | **0.0013** | **5% — a ~20x narrower reach** |
| same, `C⁻¹` at λ=7.2e-06 | 0.0004 | 2%, but in-sample 0.0000 ⇒ overfit |

**Cosine hid the entire effect.** ROME's update changes an arbitrary input by
`(v* − Wk*)·(u·k)/(u·k*)`, so what whitening does is shrink that coefficient on unrelated
inputs — and a 0.97 cosine is perfectly compatible with a 20x change in it. Had the gate
stopped at the cosine it would have closed E-016 with the wrong answer. Same shape as
[E-015]'s lesson: the aggregate statistic and the component statistic disagreed, and the
component was right.

**λ chosen by a rule, not by taste.** Take the smallest λ at which in-sample and held-out
selectivity agree — the least regularisation that is not fitting noise. That is
**λ = 7.2e-03** (0.0011 vs 0.0013). Smaller λ shows a 10x in/out gap and is overfitting the
1400 fitting keys. Every E-016 number is reported with its λ and a sweep.

**Circularity caught and removed.** The first measurement evaluated selectivity on the same
2048 keys that defined `C`, giving a spurious 100–1000x. Refit on 1400, evaluated on 665
held-out; the honest figure is ~20x. The in-sample figure would have been the [E-007]
denominator bug again.

**Decision:** the gate clears and [E-016]'s experiment is worth running. The whitened
editor is a materially more targeted update, which is exactly the regime where an
inference effect could hide that a blunt one would smear away.

**Artifacts:** src/whiten.py; agents/engineer/workspace/collect_keys.py;
results/cache/E016_keys_L5.pt; logs/collect_keys-2026-09-18-*.log

---

## [E-016] Result: whitening cannot reduce same-subject leakage, and the reason is analytic

_Date: 2026-09-18 · Llama-3.1-8B, layer 5, 42 chains, three λ_

**The experiment.** Re-ran [E-015]'s paired test with `u = C⁻¹k*`, where `C` is the
low-rank-plus-ridge key second moment (Woodbury, N=2048, CounterFact prompt corpus).

| condition | birth | work | paired gap | McNemar |
| --- | ---: | ---: | ---: | --- |
| `C = I` ([E-015]) | 28 | 28 | +0.0 pp | p = 1.000 |
| `C⁻¹`, λ = 7.2e-03 *(primary)* | 28 | 28 | **+0.0 pp** | p = 1.000 |
| `C⁻¹`, λ = 7.2e-04 | 28 | 29 | −2.4 pp | p = 1.000 |
| `C⁻¹`, λ = 7.2e-02 | 28 | 28 | +0.0 pp | p = 1.000 |

Birth-arm top-1 destination **identical to `C = I` in 42/42 chains at every λ**, despite
the gate measuring the whitened update as ~20x more selective on held-out keys.

**Why — and this is the finding, not the null.** The coefficient profile along the probe
prompt shows the coefficient at the subject's last token is **exactly 1.0000 under both
editors**:

    pos  token      coeff C=I   coeff C⁻¹   ratio
     8   'ck'          1.0000      1.0000    1.00x    <- subject-last
     9   ' was'        0.1156      0.1040    0.90x
    14   ' of'         0.0305      0.0086    0.28x

`k*` is read at the subject's last token of the edit prompt. Any probe sharing that prefix
— *"X was born in the **city** of"* against *"X was born in the **country** of"* — has an
**identical key at that position under causal attention**. ROME's coefficient there is
`(k·u)/(u·k*) = (k*·u)/(u·k*) = 1` for **any** `u`, hence for any `C`.

> **ROME's normalisation guarantees that every prompt sharing the edited subject's prefix
> receives the full, unattenuated edit vector at the subject position, for any choice of
> `C`. The whitening term can only reduce leakage to prompts that do not share the prefix.**

That is analytic, not statistical, and it accounts for every measurement in this arc:

| observation | explained by |
| --- | --- |
| `inner_1` displaced, 67% ([E-014]) | shares the prefix → pinned coefficient 1.0 |
| `inner_2` inert, −0.02 ([E-013]) | *"Paris is located in…"* shares no prefix → nothing pinned |
| whitening changes nothing, 42/42 | cannot touch a coefficient fixed at 1 by construction |
| a uniform ×0.27 rescale **does** break relocation (3 of 4) | that scales the pinned term too |

**Two wrong mechanisms, recorded rather than quietly dropped.** (1) "The probe key is
aligned with `k*` so whitening preserves it" — refuted, cos = 0.034, near-orthogonal.
(2) "The destination is scale-invariant" — refuted, ×0.27 breaks relocation in 3 of 4
chains. The third guess was measured rather than predicted, and only the per-position
profile revealed it. The earlier "3.7x attenuation" figure was measured at the probe's
FINAL token, which contributes 0.03 of a 1.66 total — 2% of the mass — so it described a
negligible part of the update.

**Consequences.**
- [E-015]'s null is **not** an artifact of a blunt editor. It is structural: no choice of
  `C` could have produced a different answer.
- `mom2_adjustment: false` matters less than [E-013] gate 0 implied for same-subject
  effects, and this is a defensible reason rather than a shrug.
- Any method proposing to limit an edit's blast radius by reweighting `u` inherits this
  limit. Reducing same-subject leakage requires changing the normalisation or the key
  selection, not the covariance. **Out of scope to pursue** — CLAUDE.md forbids proposing
  methods — but it is the sharpest thing this project has produced and belongs in writing.

**Threat to the claim.** It rests on the probe sharing a prefix with the edit prompt up to
the subject's last token, which is true of our `inner_1`/`outer` pair by construction. A
probe that mentions the subject LATER ("The city where X was born is") would not share the
prefix, and the coefficient there is not pinned. Untested, and the obvious next probe.

**Artifacts:** agents/engineer/workspace/{run_e016,why_whitening_null,scale_invariance,
coeff_profile}.py; src/whiten.py; results/E-016-whitened-meta-llama_Llama-3.1-8B.json

---

## [E-017] Result: same-subject leakage is structural — no probe form escapes it

> **Narrowed 2026-09-20 by [T-075].** The claim holds at layer 5, the layer EasyEdit
> edits. It does NOT generalise across depth: reordered probes fall to ~0.58 by L20.
> The word "structural" is withdrawn as a statement about ROME; it remains correct as a
> statement about prefix-sharing probes, which are pinned at exactly 1.000 at every layer.

_Date: 2026-09-19 · Llama-3.1-8B, layer 5, 16 chains for the coefficient sweep_

Tests [T-074], the threat [E-016] left standing: its analytic account required the probe to
share the edit prompt's prefix, which our probes do by construction.

**Part 1 — the relocation comparison is UNRUN, not negative.** The late-subject probe
*"The city where X was born is"* holds the true city at baseline in only **8/42** chains
against **29/42** for the early form. The comparison was restricted to chains where both
hold, leaving 8, below the pre-stated floor of 10. **Reported as unrun.** Without that
baseline control the late form's weaker relocation would have read as confirmation of the
hypothesis under test, when the cause is that the probe does not work — [E-011]'s lesson
applied prospectively rather than learned again.

**Part 2 — the coefficient sweep, which does not depend on the probe working.**
Coefficient at the subject's last token against the edit's `k*` (1.0 = full delta):

| probe form | mean | median | min |
| --- | ---: | ---: | ---: |
| early, the edit form | **1.000** | 1.000 | 0.998 |
| **different relation** — `X died in the city of` | **1.000** | 1.000 | 0.998 |
| late clause — `The city where X was born is` | 0.935 | 0.954 | 0.670 |
| possessive — `The birthplace of X is the city of` | 0.934 | 0.966 | 0.483 |
| long preamble | 0.925 | 0.946 | 0.707 |

**[E-016]'s analytic account is confirmed on a case it did not construct.** A *different
relation* scores exactly 1.000 against a birth edit's `k*`, because the subject sits at the
start and causal attention makes the key identical. The relation asked about is irrelevant.

**And the hypothesis this ticket was opened to test is refuted.** Moving the subject later
was predicted to break the pinning; it attenuates it by ~7% on average. The layer-5 key at a
subject's last token is largely determined by the subject tokens themselves, not by
preceding context, so no natural reformulation escapes.

> **Same-subject leakage in ROME is structural.** Any prompt containing the subject receives
> 93–100% of the edit vector at the subject's last token — regardless of the relation asked
> about, where the subject sits, how much preamble precedes it, and (per [E-016]) regardless
> of `C`. The only probe that escaped in this project is `inner_2`, which does not mention
> the subject at all.

**This closes the mechanistic account of [E-015].** The work-country edit and the birth-city
probe both begin with the subject, so the probe receives the work edit's full unattenuated
delta. The +0.0 pp gap was not a null to be explained away — it was structurally required.

**Scope, stated rather than implied.** 16 chains for the sweep, one model, one layer, one
relation family, and the minima (0.48, 0.67, 0.71) show some subjects DO attenuate
materially — so this is an existence-and-tendency claim, never a rate. Per [O-004], it
licenses no frequency statement.

**What would falsify it:** a probe form that mentions the subject and scores materially
below ~0.9 across chains, or the same sweep at a different layer showing context-sensitivity
in the subject key. Both are cheap and neither was run.

**Artifacts:** agents/engineer/workspace/{run_e017,coeff_forms}.py;
results/E-017-form-meta-llama_Llama-3.1-8B.json; logs/coeff_forms-2026-09-19-053*.log

---

## [O-007] Correction: four "nnsight constraints" were one flaky NDIF node

_Date: 2026-09-20 · retracts the constraint list committed earlier the same day_

**What I claimed.** A commit on 2026-09-20 documented four constraints discovered while
building the [T-075] layer sweep: that a list comprehension inside a trace loses its proxy
saves; that `list.append` on a proxy is not whitelisted; that two `.save()` calls reading
different layers fail; and that a layer index passed as a default argument or set via
`globals()` fails where a module constant works.

**All four are wrong.** NDIF rejects roughly half of all traces with `Module
nnsight.intervention.batching is not whitelisted`, depending on which node serves the
request. Measured directly: the **identical unchanged call, six times, succeeded 3/6** —
alternating. `coeff_forms.py` succeeded at 05:32 and failed at 09:31 with no edit between.

**How the error was made.** Each time a run failed I changed one thing, re-ran, and hit a
~50% coin flip. A pass looked like confirmation and a fail looked like a new constraint. I
produced four causal stories in a row without once re-running the *unchanged* code, which
is the one test that separates a code bug from a flaky dependency. The lesson is narrow and
mechanical: **before attributing a failure to a change, re-run the thing that worked.**

**The fix.** `remote._is_flaky_remote` matches `"is not whitelisted"` and
`_is_transport_error` returns True for it, so `retrying()` absorbs it with the existing
linear backoff. Verified: the same call that went 3/6 bare goes **6/6** through `retrying`.

**What is NOT affected.** Prior results stand. This failure is loud — it raises — so it
cannot silently corrupt a completed run. Every result in [E-013] through [E-017] came from
a run that finished and wrote its artifact.

**What this says about the last week.** NDIF has now produced three distinct failure modes:
transport timeouts (38 in one day), multi-hour stalls, and now node-dependent rejections.
The instrument is sound; the dependency is not. Any future long run on this backend should
assume ~50% per-call failure as a design parameter rather than an incident.

**Artifacts:** src/remote.py (`_is_flaky_remote`);
agents/engineer/workspace/{is_it_flaky,what_broke,test_retry_flaky}.py;
agents/engineer/workspace/layer_sweep.py is retained as the record of the wrong diagnosis

---

## [T-075] Result: the pinning is exact for prefix-sharing probes at every depth, and
## decays with depth for reordered ones

_Date: 2026-09-20 · Llama-3.1-8B, 12 subjects, 7 layers, coefficient only_

Mean coefficient at the subject's last token against the edit's `k*` (1.0 = full delta):

| probe form | L0 | L5 | L10 | L15 | L20 | L25 | L31 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| edit form | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| same-prefix probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| different relation | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| late clause | 0.992 | 0.951 | 0.858 | 0.791 | **0.577** | 0.584 | 0.598 |
| possessive | 0.997 | 0.962 | 0.833 | 0.807 | **0.615** | 0.570 | 0.628 |

Worst case across subjects is sharper still: the possessive form reaches **0.129** at L20.

**Two behaviours, cleanly separated.**

1. **Prefix-sharing probes are pinned at exactly 1.000 at every depth.** Analytic: causal
   attention makes the key at the subject's last token identical, so `(k*·u)/(u·k*) = 1`
   for any `u` at any layer. No escape exists at any depth. This is the part of [E-016]
   and [E-017] that holds without qualification.
2. **Reordered probes escape progressively with depth.** 0.95 at L5 decaying to ~0.58 by
   L20. The subject key IS context-sensitive deeper in the network — it simply is not at
   layer 5.

**This narrows [E-017], and the narrowing is a correction.** [E-017] concluded *"same-subject
leakage in ROME is structural — no natural reformulation escapes."* That is true at layer 5,
which is the layer EasyEdit's `llama3-8b.yaml` edits, and it is **not** a property of the
method. At L20+ a reformulated prompt receives roughly half the delta, and for some subjects
an eighth. The defensible statement is **structural given the layer choice**, not structural
given ROME. "Structural" was overreach and is withdrawn in that form.

**What survives unqualified, and is stronger for being narrower:**

> Any probe beginning with the edited subject receives the **full, unattenuated** edit
> vector at the subject position — at every layer, for any `C`, and regardless of which
> relation it asks about.

**Scope.** 12 subjects, one model, one relation family, coefficient only — no edits applied
and no behavioural readout. Whether the decayed coefficient at L20 actually produces less
displacement is untested; [E-016]'s scale test showed the mapping from coefficient to
destination is not linear, so this cannot be assumed.

**Explicitly not pursued.** That a deeper edit layer would leak less to reformulated probes
is a method-design observation, and CLAUDE.md scopes this project to measuring what existing
editors do. Recorded, not chased.

**Artifacts:** agents/engineer/workspace/layer_one.py; results/T-075-layer-sweep.json;
logs/layer_one_L*.log

---

## [E-018] Result: the different-subject floor is 0.082 — [E-017] stands, and the floor is now measured

_Date: 2026-09-20 · Llama-3.1-8B, layer 5, 16 chains, coefficients only_

Tests [T-076], the control [E-017] never ran. Every prior control held the subject
fixed and varied the form; this one varies the subject and holds the form fixed —
chain *i*'s `k*` scored against chain *i+1*'s subject in the edit-form template,
paired by rotation.

**Gate passed before reading the control.** The five [E-017] forms reproduce:

| probe form | [E-017] published | [E-018] re-run |
| --- | ---: | ---: |
| early (edit form) | 1.000 | 0.999 |
| different relation | 1.000 | 0.999 |
| late clause | 0.935 | 0.935 |
| possessive | 0.934 | 0.934 |
| long preamble | 0.925 | 0.924 |

**The result.**

| | mean | median | min | max |
| --- | ---: | ---: | ---: | ---: |
| same-subject forms (all five) | **0.958** | — | 0.483 | 1.008 |
| **different subject** | **0.082** | 0.081 | 0.032 | **0.153** |

**Gap 0.877, and the distributions do not overlap.** The highest different-subject
coefficient (0.153) sits below the lowest same-subject one (0.483, a possessive).
Pre-stated threshold was ≤0.3 to confirm; the measurement is **nearly four times
below it**.

**[E-017] is confirmed, and its claim is now stronger than when published.** "Any
prompt containing the subject receives 93–100% of the edit vector" rested on an
untested assumption that a non-subject prompt would receive little. That floor is
now measured at 0.082 rather than assumed, and the separation is the cleanest in
this project's record.

**The anisotropy worry was well-founded and wrong.** [E-016] measured these keys at
participation ratio 26.5 of 2048, and the design argued that vectors on a narrow
manifold have substantial cosine by construction, so the floor might be high. It is
not. A ~26-dimensional manifold still leaves ample room for different subjects to
be near-orthogonal at this layer. **Recording the prediction and its failure** —
the reasoning was a correct reason to run the control and an incorrect forecast of
its outcome, and those are different things.

**Noise floor, worth stating.** The edit form should be exactly 1.000 by
construction — its key *is* `k*`. It measures 0.999 with range 0.995–1.003, so
half-precision activations put the measurement noise at roughly ±0.005. That is two
orders of magnitude below the 0.877 gap and does not bear on the reading.

**What this does not establish.** Layer 5 only, 16 chains, one model, one relation
family, and one pairing (rotation). A different pairing — say, subjects matched on
token length or nationality — could in principle score higher, and was not run. The
claim is that *these* different subjects score 0.082, and the generalisation to
"different subjects generally" is an inference from a clean separation, not a
measurement of the space.

**Consequence for [T-075].** The layer sweep's first job is discharged. It reverts
to the question the thread actually asked — does the pinning hold away from layer 5
— with `c_other` retained as a per-layer floor rather than as the point of the
experiment. design.md Part IV amended accordingly.

**Provenance.** 15 NDIF transport failures absorbed by `retrying()` across 16
chains, consistent with [O-007]'s ~50% per-call rejection rate. One completed run.

**Artifacts:** agents/engineer/workspace/coeff_other_subject.py;
logs/coeff_other_subject-2026-09-20-103132.log

---

## [O-008] Correction to a correction: one of [O-007]'s four retracted constraints is real

_Date: 2026-09-20 · partially reinstates a claim [O-007] retracted the same day_

**What [O-007] said.** Four "nnsight constraints" documented while building the
[T-075] sweep were all wrong, and all four were the same thing: NDIF rejects roughly
half of all traces node-dependently, so a pass looked like confirmation and a fail
looked like a new constraint. The fix was `retrying()`, and the lesson was *before
attributing a failure to a change, re-run the thing that worked.*

**That reasoning was right and the conclusion was too broad.** One of the four is
real:

> **A `for` loop or comprehension inside a trace body does not execute. It raises
> nothing and produces zero saves.**

**Evidence, gathered the way [O-007] prescribed.** Both patterns run back to back,
in one session, through `retrying()`, same node conditions, single prompt:

| pattern | result |
| --- | ---: |
| three explicit `.save()` calls at layers 0, 5, 31 | three tensors, `[1, 11, 14336]` each |
| the same three saves written as `for L in (0, 5, 31)` | **`len(saved) == 0`** |

The explicit form also disposes of a second retracted constraint — *"two `.save()`
calls reading different layers fail"* — which was flakiness, correctly retracted.
The eight-layer unrolled trace in `layer_sweep_t075.py` works.

**Why this was hard to see, and why it is dangerous.** The failure is **silent**.
No exception, no warning, an empty result that looks like a successful trace. Under
a 50% transport failure rate a silent zero is indistinguishable from a rejection
until you assert on the save count — which is why `once()` now raises if it gets
fewer layers than it asked for.

**What went wrong in my own reasoning.** [O-007] found a common cause for four
observations and retracted all four. The common cause was real and explained most of
them, so the remaining one was absorbed by an explanation that fit. **A correction
that retracts more than it tested is the same error as the original, run backwards.**
The original attributed four failures to four causes without re-running; the
correction attributed four failures to one cause without re-running each.

**Not affected.** No completed result changes. This failure mode produces zero saves
and raises downstream, so like [O-007]'s it cannot silently corrupt a finished run.
[E-013] through [E-018] all wrote artifacts.

**Standing guidance, replacing [O-007]'s list of four with one item:**

1. **Unroll loops inside trace bodies.** Write the saves out. Assert the count after.
2. Everything else [O-007] retracted stays retracted — multiple saves, default
   arguments, module constants were all flakiness, and `retrying()` handles them.

**Artifacts:** agents/engineer/workspace/layer_sweep_t075.py (unrolled, with the
assert); the two-pattern probe was a scratch script, its result recorded in the table
above rather than committed.

---

## [E-019] Result: the analytic half is layer-invariant; the empirical half is an early-layer fact

_Date: 2026-09-20 · Llama-3.1-8B, 8 layers, 16 chains, coefficients only_

Runs [T-075] per design.md Part IV. **DENY** in the mid-deep range and **NULL** at
layer 31 — both pre-stated outcomes fired, at different depths, which is exactly
why the floor was carried per layer.

**Gate passed.** Layer 5 reproduces [E-018] from a freshly computed `k*`: late
clause 0.935, possessive 0.934, long preamble 0.924, different subject 0.082 —
matching the published 0.935 / 0.934 / 0.925 / 0.082 to ±0.001. Dropping the
`E014_kstar_L5` cache is validated.

| layer | `c_form` (4 forms) | `c_other` | gap |
| ---: | ---: | ---: | ---: |
| 0 | 0.989 | 0.053 | 0.936 |
| 3 | 0.968 | 0.056 | 0.912 |
| 5 | 0.948 | 0.082 | 0.867 |
| 8 | 0.891 | 0.124 | 0.767 |
| 12 | 0.838 | 0.257 | 0.581 |
| 16 | 0.768 | 0.255 | 0.514 |
| 24 | **0.633** | 0.168 | 0.465 |
| 31 | 0.699 | **0.669** | **0.030** |

### The finding splits [E-017]'s claim in two, and only one half survives

**The analytic half is layer-invariant, as it must be.** The *different relation*
probe — *"X died in the city of"* against a birth edit — scores **exactly 1.000 at
every one of the eight layers, min = max = 1.000**. It shares the edit prompt's
prefix up to the subject's last token, so under causal attention its key *is* `k*`
and the coefficient is `(k*·u)/(u·k*) = 1` by construction. [E-016]'s result is
algebra and the sweep confirms it is not a layer-5 accident.

**The empirical half is not.** The three probes that do *not* share the prefix —
late clause, possessive, long preamble — decay monotonically with depth:

| | L0 | L5 | L12 | L24 |
| --- | ---: | ---: | ---: | ---: |
| late clause | 0.986 | 0.935 | 0.795 | 0.524 |
| possessive | 0.990 | 0.934 | 0.794 | 0.564 |
| long preamble | 0.979 | 0.924 | 0.764 | 0.444 |

So **[E-017]'s "any prompt containing the subject receives 93–100%" is an
early-layer fact.** It holds at layers 0–5, is marginal at 8 (0.85–0.86), and is
gone by 24, where a reformulated probe receives roughly half the edit vector. The
layer-5 key at a subject's last token is largely determined by the subject tokens
themselves; by layer 24 it is not.

**Layer 31 is unreadable, and the floor is what says so.** `c_other` reaches 0.669
against a `c_form` of 0.699 — a gap of 0.030. Everything scores about the same
regardless of whose name is in the prompt, so the measure has lost discrimination
rather than the key having become context-sensitive. Without the per-layer floor,
31's 0.699 would have looked like a mild recovery from 24's 0.633. It is not a
recovery; it is noise. **This is the NULL arm firing, and carrying `c_other` at
every layer is the only reason it is distinguishable.**

### What this changes in what was published

`web/blog/2026-09-15-five-days.mdx` says *"Same-subject leakage in ROME is
structural. Any prompt containing the subject receives 93–100% … regardless of the
relation asked about, where the subject sits, how much preamble precedes it."*

**"Regardless of the relation asked about" survives at every layer** — that is the
prefix-sharing case and it is analytic. **"Where the subject sits" and "how much
preamble precedes it" do not survive past the early layers.** The post is corrected
rather than amended, since a scope note would understate it: the claim as written is
true at the layer EasyEdit edits and false at layer 24.

### What this does not establish

- **Delivery, never effect.** A coefficient is how much of the edit vector arrives.
  [E-016] showed a ×0.27 rescale breaks relocation in 3 of 4 chains, so a fall from
  0.93 to 0.52 is likely to matter behaviourally — but that is an inference, and no
  edit was run at any layer but 5.
- **Eight layers is a shape, not a per-layer claim.** The monotone decay is read off
  eight points; nothing here licenses a statement about layer 20 specifically.
- 16 chains, one model, one relation family, one pairing for the floor.
- **Why the decay happens is unmeasured.** That the subject key becomes
  context-sensitive with depth is a description of the measurement, not a mechanism.

### Out of scope, and stated so it is not mistaken for a proposal

An editor targeting a deeper layer would deliver less of its update to reformulated
probes. That is a consequence of the measurement, not a recommendation about where
to edit — per CLAUDE.md this project does not propose methods, and the behavioural
half is unrun in any case.

**Provenance.** 16 NDIF transport failures absorbed by `retrying()` across 16
chains. Saves unrolled per [O-008].

**Artifacts:** agents/engineer/workspace/layer_sweep_t075.py;
logs/layer_sweep_t075-2026-09-20-104950.log

---

## [E-020] Result: the decay is direction, not magnitude — and layer 31 is convergence, not noise

_Date: 2026-09-20 · Llama-3.1-8B, 8 layers, 16 chains, same harness as [E-019]_

Runs [T-077]. [E-019] measured the decay and explained nothing about it. The
coefficient is not a cosine — `c = (|k|/|k*|) · cos(k, k*)` — so it can fall two
ways, and they are different claims about the network.

**Gate passed.** `c` reproduces [E-019] exactly: layer 5 at 0.935 / 0.934 / 0.924
for the reformulated forms and 0.082 for the control; layer 24 at 0.524 / 0.564 /
0.444 and 0.168. The independently computed cosine satisfies
`|c − ratio · cos| < 1e-4` in every one of the 768 cells.

### DIRECTION. The norm ratio carries none of the decay.

Reformulated probes — late clause, possessive, long preamble — averaged:

| layer | `c` | `cos` | `\|k\|/\|k*\|` |
| ---: | ---: | ---: | ---: |
| 0 | 0.985 | 0.984 | 1.000 |
| 5 | 0.931 | 0.925 | 1.008 |
| 12 | 0.784 | 0.740 | 1.064 |
| 24 | **0.511** | **0.471** | **1.091** |
| 31 | 0.598 | 0.609 | 0.986 |

**The cosine falls from 0.984 to 0.471 while the norm ratio never leaves
0.97–1.24.** Pre-stated: cos ≲0.7 at layer 24 with ratio near 1 is DIRECTION. The
measurement is 0.471 against 1.091.

**Magnitude works slightly *against* the decay.** The ratio drifts *up* with depth,
so the direction change is larger than `c` alone suggests — at layer 24 the
coefficient is 0.511 but the underlying alignment is 0.471, propped up by keys that
are 9% longer than `k*`.

**Norm carries no information anywhere in this measurement.** Across all 8 layers,
6 forms and 16 chains, `|k|/|k*|` sits within about 10% of unity — including for a
completely different person. Subject-position keys have essentially the same
magnitude regardless of whose name is in the prompt or how the prompt is worded.
Everything that distinguishes them is orientation.

### Layer 31's rise is convergence, and that was pre-stated

[E-019] filed the different-subject jump (0.082 → 0.669) as the measure losing
discrimination, which was accurate and uninformative. The decomposition says what
kind of loss:

| layer | `c` | `cos` | ratio |
| ---: | ---: | ---: | ---: |
| 5 | 0.082 | 0.081 | 1.008 |
| 12 | 0.257 | 0.256 | 1.006 |
| 24 | 0.168 | 0.168 | 1.019 |
| 31 | **0.669** | **0.660** | 1.009 |

The rise is **cosine**, with the ratio flat at 1.009. At the final layer the
subject-position keys of *different people* point 0.66 of the way toward each
other. That is representational convergence toward a shared direction near the
output, not a scaling artifact — and it is a better account of layer 31 than
"noise", which is what [E-019] could say.

The trajectory is also non-monotonic: 0.05 → 0.26 at layer 12, back to 0.17 at 24,
then 0.66 at 31. Unexplained, and worth one line of caution — a single measurement
at eight layers cannot distinguish a real mid-network bump from sampling noise at
n=16.

### What this does and does not license

**Does:** rule out a pure magnitude account of the depth decay. Whatever happens to
the subject key with depth, it is a change of orientation, and the delivered
magnitude is nearly constant.

**Does not:** demonstrate that attention mixes context into the subject position.
That is the leading candidate and it remains untested — it needs the attention
patterns themselves, which were not run. **"cos fell" is not "context was mixed
in".** A falling cosine is consistent with attention mixing, with MLP writes at the
subject position, and with anything else that reorients the residual stream.

**Also unmeasured:** 16 chains, one model, one relation family, delivery not effect.
The per-chain spread is wide at depth — layer-24 late clause ranges 0.144–0.781 in
[E-019] — so the means describe a tendency across subjects, not a per-subject law.

### Consequence

[T-077] is answered at the level it asked and re-opens one level down. The decay is
directional; *what* reorients the key is now the question, and the cheapest next cut
is the one this ticket deferred — attention at the subject position, layer by layer.
Spawns [T-078].

**Provenance.** Same harness as [E-019] with saves unrolled per [O-008]; three
metrics logged per cell instead of one, with the identity asserted independently
rather than derived from `c`.

**Artifacts:** agents/engineer/workspace/decompose_t077.py;
logs/decompose_t077-2026-09-20-*.log

---

## [E-021] Result: the subject-token delta is sufficient and necessary — the mechanism is causal

_Date: 2026-09-20 · Llama-3.1-8B, layer 5, 42 chains, five arms, coefficients cached from [E-014]_

Runs [T-067], the hole §6 of the paper names first. Everything from [E-013] to [E-020] is
behavioural — vary an input, read an output. [E-016] showed the coefficient at the
subject's last token is analytically 1, but a coefficient of 1 at a position contributing
nothing produces identical numbers. This intervenes on the mechanism instead.

| arm | positions receiving δ | mass | in target |
| --- | --- | ---: | ---: |
| **A** full | all | 100% | 28/42 = **67%** |
| **B** only | the subject's last token alone | 67% | 29/42 = **69%** |
| **C** except | all but it | 33% | 2/42 = 5% |
| **E** except, **mass restored** | all but it, rescaled to 100% | 100% | 5/42 = **12%** |
| **D** none | — | 0% | 2/42 = 5% |

**Gate passed.** Arm A reproduces [E-014]'s 67% exactly, so the masking did not change the
full-edit result and the other four arms are interpretable.

**Sufficiency.** A vs B: 28 against 29, one discordant pair, p = 1.000. One position out of
roughly twelve reproduces the entire effect.

**Necessity, with the confound removed.** The ticket predicted the problem before the run:
the subject's last token carries **66.8%** of the coefficient mass, so arm C strips
magnitude along with position, and [E-016]'s scale test already showed 0.27× breaks
relocation unaided. Arm E restores the magnitude to the surviving positions. It reaches
**12%** against a 5% baseline — not significantly above it (p = 0.25, and the test is
underpowered to exclude a small effect).

**The comparison that carries the claim is B against E.** Arm B has *less* mass (67%) at
one position; arm E has *more* (100%) spread over every other position. **29 against 5, 24
discordant pairs, none in the other direction, p < 0.0001.**

> Less magnitude in the right place beats more magnitude everywhere else, on 24 of 42
> chains and on no chain the reverse.

**What this upgrades.** [E-016]'s account moves from *analytically true and consistent with
the data* to *the position where the work demonstrably happens*. The paper's §4.1 can state
a causal claim rather than an analytic one supported by correlation, and §6.5 — "everything
is behavioural, no activation patching" — is now partly answered rather than wholly open.

**What it does not show.** This is a position ablation inside ROME's own update, not
activation patching of the model's computation. It establishes which part of *the edit*
matters, never which part of *the model* represents the fact. That distinction stays in
§6.5. Also: one layer, one model, one relation family, 42 chains — existence claim, per
[O-004].

**Mass varies more than the mean suggests:** 31% to 80% across chains, mean 66.8%. Arm E's
rescaling is per-chain, so each chain's restoration is exact rather than averaged.

**Artifacts:** src/remote.py (position mask and gain);
agents/engineer/workspace/run_e021.py;
results/E-021-positions-meta-llama_Llama-3.1-8B.json

---

## [E-022] Result: possession IS a fact-level property — and MUTE has two causes, not one

_Date: 2026-09-20 · Llama-3.1-8B, 60 facts × 8 templates = 480 cells, ParaRel P19 patterns_

Runs [T-062] and [T-064] from one measurement.

**[T-062] — CONFIRM, and it refutes the expectation this ticket was opened on.**
Modal-cell share per fact, where 1.0 means the label is a property of the fact and 0.125
is chance over eight templates:

| | |
| --- | ---: |
| mean | **0.923** |
| median | **1.000** |
| all eight cells identical | 39/60 = **65%** |
| ≥ 7 of 8 | 50/60 = 83% |
| ≥ 4 of 8 | 60/60 = **100%** |

A fact-level predicate exists. Single-template probing is a **noisy estimator** of a real
property, not a category error. The Deny branch — *no fact-level predicate, every per-fact
possession number is a template-level quantity under a fact-level name* — was pre-stated
as the more important outcome and did not fire. **Every possession number in this repo,
and the ones in the editing literature that [R-010] found, are more defensible than this
ticket assumed.**

**Confound checked and clean.** All eight templates sit between 65% and 72% HELD, so no
single bad probe is carrying the stability. Templates were ParaRel's, not ours — seven of
its thirteen P19 patterns, the six with prenominal `[Y]` excluded before scoring because a
continuation-based scorer cannot reach a mid-sentence slot.

**[T-064] — MUTE is 27% of cells, and it inverts its own predicted cause.**

| answer frequency | MUTE rate |
| --- | ---: |
| rare (1–2 occurrences) | **35%** of 352 cells |
| common (≥3) | **5%** of 128 cells |

`PRIOR` is **0%** throughout. The label-form account, built on [E-011]'s countries,
predicted MUTE would track *modal* answers. With cities it tracks **rarity** — the
opposite direction.

**Both are true, and pool concentration decides which appears:**

| pool | top filler | what fails |
| --- | --- | --- |
| 28 countries ([E-011], [E-012]) | 29% | `PRIOR` and `MUTE` from surface form on a high-prior answer |
| 78 cities (here) | 6% | `MUTE` from **rarity** — hard to rank first among 50, subject still tracked |

So MUTE is not one phenomenon. It is the cell where the row test fails for *any* reason
while discrimination survives, and at least two reasons populate it. An account of MUTE
that names only surface form is incomplete — which is what [E-012]'s entry implies and is
corrected here.

**Third appearance of pool concentration as the hidden variable**, after [E-009b] and
[E-014]'s Washington attractor. [T-073] made attractor mass a standard reported field for
exactly this reason; this entry is evidence the field was worth adding.

**Scope.** 60 facts, one relation, one model, eight templates. The stability result is an
existence claim about *this* relation; a relation whose answers are all near-modal could
still scatter.

**Artifacts:** agents/engineer/workspace/run_e022.py; results/E-022-cells.json

---

## [E-023] Result: the closed pool undercounts relocation badly — and the Washington attractor was ours

_Date: 2026-09-20 · Llama-3.1-8B, 30 chains, greedy 4 tokens, baseline and edited_

Runs [T-066]. Every number in this project comes from ranking a closed type-matched pool.
This asks what that hides by letting the edited model generate instead.

| measure | rate |
| --- | ---: |
| ranked over the 75-city pool ([E-014]'s method) | **67%** |
| generated, scored *via the pool* | 43% |
| generated, scored on the text | 73% |
| **generated, hand-adjudicated** | **30/30 = 100%** |

**Every one of the thirty edited generations names a city in the target country.** The
eight the automated checks called misses are Gisborne (New Zealand), Ahmedabad (India),
Lausanne (Switzerland), Viseu (Portugal), New York and Washington DC (United States),
Prostějov and Plzeň (Czech Republic). None is a contested fact; the adjudication is by hand
and is recorded as such.

**Two of the three automated figures above are my own measurement bugs**, and both are the
[E-007] denominator error in new costumes. Scoring generations *via the pool* resolves a
city's country through a pool-derived lookup, so any city outside the pool returns nothing
and counts as a failure — inside the very experiment built to find pool artifacts. Scoring
on the text only catches generations that happen to name the country.

**What this does to [E-014].** Its 67% is a substantial undercount. The model relocates
essentially always; the pool cannot express where it goes. Of 75 candidate cities, drawn
from our own chain answers plus capitals, most of the world is missing — so Hamburg,
Sydney, Adelaide, Zurich, Milan, Delhi, Gisborne and Plzeň are all unreachable answers.

**And it explains the Washington attractor.** [E-014] found `Washington, D.C.` taking 33%
of ranked destinations and read it as the model's fallback when no coherent relocation
occurred. It is not. It is the **ranking's** fallback: the model's actual answer is off the
menu, so the highest-prior item on the menu wins. Chain 61 generates *"Hamburg, Germany"*
and ranks `Washington, D.C.`; chain 1315 generates *"Zurich, Switzerland"* and ranks
`Washington, D.C.` The attractor was a property of our instrument.

**The pool removed a correct answer through our own cleaning.** Hamburg is absent because
`place_types.json` classified it `not_settlement` — its Wikidata QID resolves to Hamburger
SV, the football club. The filter added to remove universities and clubs from the city pool
removed a city with them. Fourth entity-linking artifact in this project, after the P36
historical capitals, the P106 first-occupation labels, and the six malformed chains — and
the first caused by a fix.

**What survives untouched, and why.** [E-015], [E-016] and [E-021] are **paired**
comparisons that use the same pool for both arms. A pool artifact shifts both arms equally
and cancels in the difference:

| result | affected? |
| --- | --- |
| [E-015] work vs birth, +0.0 pp | **no** — same pool both arms |
| [E-016] whitened vs unwhitened, 42/42 identical | **no** — same pool both arms |
| [E-021] B vs E, 29 vs 5, p < 0.0001 | **no** — same pool all arms |
| [E-014] 67% as an absolute level | **yes** — undercount, true rate ≈ 100% |
| [E-014] Washington attractor at 33% | **yes** — an artifact of ranking, not a model behaviour |

So the central claims stand and the levels do not. **Differences survive a bad pool;
absolute rates do not.** That distinction should govern how every rate in this project is
read, and it is now the strongest argument for reporting paired contrasts rather than
levels.

**Scope and confound.** 30 chains, greedy decoding, four tokens, one model, one relation.
Greedy is itself a choice: a model can rank one answer and sample another, so this compares
greedy generation against rank and not "what the model would say" in general.

**Artifacts:** agents/engineer/workspace/run_e023.py; results/E-023-generation.json

---

## [E-024] Result: an edit reaches the whole subject, but damages in proportion to type overlap

_Date: 2026-09-20 · Llama-3.1-8B, layer 5, 37 subjects, paired log-prob, no candidate pool_

Tests whether a birthplace edit disturbs attributes that have nothing to do with birth.
Two probes give a relatedness gradient; the control is the same two probes on a different,
unedited subject.

| probe | baseline | mean drop | control-differenced |
| --- | ---: | ---: | ---: |
| same subject · **occupation** (unrelated) | −4.19 | 1.63 | **+1.60** |
| same subject · **citizenship** (related) | −2.05 | 6.63 | **+6.58** |
| other subject · occupation | −4.19 | 0.03 | — |
| other subject · citizenship | −2.07 | 0.05 | — |

**The control is a clean zero.** 0.03 and 0.05 nats. The edit is unambiguously
subject-keyed, corroborating [E-018]'s 0.082 floor by an unrelated measure — that one was a
coefficient, this is a behavioural log-prob.

**The reframe is half right.** An unrelated attribute of the edited subject does fall —
1.60 nats against the control's 0.03. Editing where someone was born measurably disturbs
what the model holds about their profession. "Editing a fact" does not describe what
happens.

**But the damage is not uniform, and that is the result.** Citizenship falls **4× harder**
than occupation. [E-021] established the *coefficient* is identical regardless of relation
— the different-relation probe scored exactly 1.000 — so the update's **reach** is uniform
while its **damage** is graded.

> An edit reaches the whole subject uniformly, and damages each probe in proportion to how
> much the injected content competes with that probe's answer space.

The delta encodes a country. A citizenship probe asks for a country and is hit hard; an
occupation probe asks for a profession and is hit less. This also subsumes [E-015]: the
displacement is country-flavoured, so country-valued probes move and others do not.

**The confound, which blocks the obvious phrasing.** Citizenship is *both* semantically
related to birth country *and* type-matched to it. "Semantic relatedness modulates the
damage" and "type overlap modulates the damage" both fit these two points, and they are
different claims. **Do not write the former.** The discriminating probe is **language**:
semantically related to country, typed as a language. If language falls like occupation the
gradient is type overlap; if like citizenship, semantic relatedness. Opened as [E-025].

**Method note.** No candidate pool anywhere in this measurement — teacher-forced log-prob
on the same string with and without the edit. [E-023] showed a closed pool undercounts
badly and that only paired contrasts survive it; this design took that lesson rather than
repeating the mistake.

**Scope.** 37 subjects, one model, one layer, one edited relation, two probes. The
baselines differ (−4.19 vs −2.05), so the control-differenced column is the one to read.

**Artifacts:** agents/engineer/workspace/run_e024.py; results/E-024-attributes.json

---

## [E-025] Result: a floor plus type-matched displacement — not a relatedness gradient

_Date: 2026-09-20 · Llama-3.1-8B, layer 5, 29 subjects, paired log-prob, no candidate pool_

Separates the two accounts [E-024] could not: language is semantically related to country
of origin but typed as a language, so it shares relatedness with citizenship and type with
occupation.

| probe | relatedness | type match | baseline | **post-edit** | drop |
| --- | --- | --- | ---: | ---: | ---: |
| occupation | no | no | −4.36 | **−6.16** | 1.80 |
| language | **yes** | no | −0.71 | **−6.20** | 5.49 |
| citizenship | yes | **yes** | −1.97 | **−9.10** | 7.13 |

Control subject: 0.10 / 0.07 / 0.04 nats. Subject-keying reconfirmed.

**The run's own headline statistic was wrong and is retracted here.** It reported language
sitting "69% of the way from occupation to citizenship" and concluded *semantic
relatedness*. That statistic is the **drop**, which is dominated by where each probe
started. On endpoints the picture inverts: occupation and language finish **0.04 nats
apart** after starting **3.65 apart**. Language's large drop is the distance it had to
fall, not evidence it was targeted.

**Two effects, not a gradient.**

1. **Uniform suppression.** The edit drives everything about the subject to a common floor
   near −6.2, reached by occupation and language alike. Semantic relatedness does not
   modulate it: language (related) and occupation (unrelated) are indistinguishable at the
   endpoint. Per-item correlation between baseline and post-edit is **−0.15** for language
   — fully floored — against **+0.72** for occupation, which has not reached it.
2. **Type-matched displacement.** Only citizenship goes below the floor, by **2.95 nats**.
   Its answers are countries, competing directly with the injected country value.

**This is what [E-021] predicts.** Uniform *reach* gives uniform suppression; the extra
citizenship damage comes from `v*`'s *content* rather than the update's spread. It also
subsumes [E-015]: the displacement is country-flavoured, so country-valued probes move
further and others merely collapse.

> An edit suppresses everything about the edited subject to a floor, and additionally
> displaces probes whose answer type matches the injected value.

**Method note, and the lesson repeated.** Third time today a headline statistic and its
components disagreed, after [E-011] and [E-023]. The confound was pre-registered in
[E-024]'s ticket — *"report the baseline beside every delta"* — and the ticket still
computed the summary on drops. **Naming a confound is not controlling for it.**

**Scope.** 29 subjects, one model, one layer, one edited relation, three probes. The floor
value (−6.2) is specific to this setup and is not a constant to be quoted elsewhere.

**Artifacts:** agents/engineer/workspace/run_e025.py; results/E-025-language.json

---

## [E-027] Result: the pinning is a ROME fact — and the different-subject floor is not

_Date: 2026-09-20 · EleutherAI/gpt-j-6b, 12 subjects, 6 layers, coefficient only, no edits_

Runs [T-080]. Every coefficient in this project had been measured on one model.

### The analytic half transfers exactly, and that was the point of running it

| form | f=0.00 (L0) | 0.15 (L4) | 0.37 (L10) | 0.63 (L17) | 0.85 (L23) | 1.00 (L27) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| edit form | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| same-prefix probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| different relation | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

**Worst deviation from 1.000 across all 216 prefix-sharing cells: 0.00e+00.** Different
architecture (GPT-J vs Llama), different tokenizer, different width (`d_mlp` 16384 vs
14336), different depth (28 blocks vs 32). The claim

> any probe beginning with the edited subject receives the full, unattenuated edit vector
> at the subject position, at every layer, for any `C`

is a claim about **ROME's `u·k*` normalisation and causal attention**, not about
Llama-3.1-8B. This was expected — the derivation never mentioned an architecture — and it
is now measured rather than assumed. Confirmatory, cheap, and the first thing an external
reader asks.

### The empirical half also transfers, which was NOT expected

The decay of reordered probes with depth is not derived and had no reason to carry over.
Compared **at matched fraction of depth**, because layer 20 is a different place in a
28-block network than in a 32-block one:

| depth fraction | Llama late clause | GPT-J late clause | Llama possessive | GPT-J possessive |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0.992 | 1.000 | 0.997 | 1.000 |
| ~0.15 | 0.951 | 0.861 | 0.962 | 0.881 |
| ~0.35 | 0.858 | 0.749 | 0.833 | 0.777 |
| ~0.64 | 0.577 | 0.597 | 0.615 | 0.715 |
| ~0.83 | 0.584 | 0.456 | 0.570 | 0.581 |
| 1.00 | 0.598 | 0.482 | 0.628 | 0.533 |

Same shape in both: pinned at the input, monotone decay through the first two-thirds,
flat at roughly 0.5 thereafter. GPT-J decays slightly earlier and slightly further. Two
architectures reorienting the subject key on the same *relative* schedule is a stronger
statement than either model alone, and it is the part of [E-019] that could have failed.

### The different-subject floor does NOT transfer, and this is the component that matters

[E-018] measured Llama's floor at **0.082** at the edit layer, against a same-subject mean
of 0.958 — non-overlapping, gap 0.877. That measurement is what licensed [E-017].

| depth fraction | 0.00 | 0.15 | 0.37 | 0.63 | 0.85 | 1.00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-J different-subject floor | 0.304 | **0.155** | 0.353 | 0.422 | 0.335 | **0.524** |

GPT-J's floor is roughly **twice Llama's at the edit layer and never drops below 0.155**.
At the final layer it reaches 0.524 — **above** that layer's late-clause coefficient of
0.482. A *different person's* subject key is then better aligned with `k*` than the *same
person's* key in a reordered prompt, so the coefficient has stopped discriminating
subjects entirely. Llama shows the same collapse ([E-020]: floor 0.669 at L31); GPT-J's
begins earlier and runs higher throughout.

**What this narrows.** "Different subjects are near-orthogonal at the subject position" is
a **Llama-3.1-8B** statement, not a ROME statement — narrowed exactly the way [E-019]
narrowed [E-017]. The anisotropy reasoning that motivated [T-076] was dismissed on Llama
because the measurement came back 0.082; on GPT-J that reasoning looks live.

**What survives.** At the layer ROME actually edits the margin is clean on both models:
Llama 0.95 vs 0.082 (gap 0.87), GPT-J 0.87 vs 0.155 (gap 0.71). The headline claim is
untouched at the layer that matters. Only its *generality across depth* is model-dependent.

### An unforced observation worth one line

Both models' floors are **non-monotonic with a minimum near depth fraction 0.15** — Llama
0.082 at L5, GPT-J 0.155 at L4 — rising in the middle and again near the output. That is
approximately where ROME edits in both. Whether the edit layer is chosen *because* subjects
are maximally separated there, or the coincidence is an artifact of two samples, is
unanswered. Spawns [T-083].

### Confounds, one of them serious

1. **Subject familiarity — uncontrolled, and a live alternative explanation for the whole
   floor result.** The 12 subjects were gated for possession on **Llama-3.1-8B**
   (`chains_gated_meta-llama_Llama-3.1-8B.json`) and are used here **without a GPT-J
   possession filter**, which the ticket required to be stated rather than mixed. GPT-J is
   6B and Pile-trained; if it does not know these people, their name tokens may share a
   generic "unfamiliar person" direction, which would inflate the different-subject floor
   by construction. **The floor finding is therefore PLAUSIBLE, not CONFIRMED.** Spawns
   [T-082], which is cheap and should run before the floor claim is repeated anywhere.
   Note this confound does **not** touch the analytic result: 1.000 is exact regardless of
   whether the model knows the subject.
2. **Tokenisation** — cleared, not assumed. `subject_last_index` was verified on three
   subjects across all five forms by decoding the token at the computed index: `'ck'` for
   Vlaminck, `'atsuki'` for Natsuki, `'ice'` for Lunice. A silent off-by-one here yields
   plausible wrong numbers, which is the dangerous kind.
3. **Module path** — the read tensor's width is asserted against the config's `d_mlp`
   (16384) at every layer, so reading the wrong module fails loudly instead of quietly.

**Scope.** n=12, one relation family, coefficient only, no edits applied on this model, no
possession filter. Nothing here licenses a rate.

**Artifacts:** agents/engineer/workspace/run_e027.py; results/E-027-second-model.json;
logs/run_e027-2026-09-20-182210.log

---

## [E-026] Result: the experiment failed, its gate was mis-specified, and one existence claim survives

_Date: 2026-09-20 · Llama-3.1-8B, 42 subjects, layers 5 and 20, ROME as configured by EasyEdit_

Runs [T-079]. **The pre-stated question is UNANSWERED and the first headline this run
produced was wrong.** Both are recorded before the surviving finding, because the order
matters: the finding is a by-product of a failed design, not a result the design earned.

### What was asked

If the coefficient governs effect, a layer-20 edit must damage subject-initial probes
**identically** (pinned at exactly 1.000 at both layers, analytic) and possessive probes
**measurably less** (0.962 vs 0.615). The interaction was the claim; neither main effect
was. Pre-stated bands: CONFIRM if possessive weakens >=40% while subject-initial holds
within 20%; DENY if possessive moves <20%.

### What came back

| form | layer | baseline | post-edit | control-differenced drop | coefficient |
| --- | --- | ---: | ---: | ---: | ---: |
| subject-initial | L5 | −1.64 | −12.09 | **10.19** | 1.000 |
| subject-initial | L20 | −1.64 | −2.43 | **0.80** | 1.000 |
| possessive | L5 | −2.15 | −11.09 | 8.75 | 0.962 |
| possessive | L20 | −2.15 | −2.32 | 0.18 | 0.615 |

Controls are null at both layers (+0.25/+0.19 at L5, −0.01 at L20) and the effect is not
carried by outliers: 42/42 subjects drop >1 nat at L5, 9/42 at L20.

The subject-initial arm moved **92%**, far outside the 20% matching band, so by the
ticket's own pre-registration this is **NOT INTERPRETABLE as a dissociation**. The two
edits are not matched and the experiment cannot speak to its question.

### The first headline, and its retraction

The run's shape invited the reading *"identical delivery, 13x difference in effect,
therefore the coefficient does not predict effect"*, and that was stated before the
confound check finished. **It is withdrawn.** The check below shows the two edits differ in
edit strength, so there is no held-fixed delivery to reason from.

### RCA — the efficacy gate measured the wrong quantity

The ticket made a 4-chain gate mandatory, on the grounds that a failed edit cannot
dissociate anything. The gate measured **lift on the injected target** and returned a ratio
of 0.98 (+9.37 deep vs +9.52 shallow), so the run proceeded.

**That criterion cannot tell an edit from a logit nudge.** A real edit raises the target
*and* suppresses the true answer, because they compete for one slot. [E-026b] scored both
continuations on the edit prompt itself, n=42:

| layer | true-answer drop | target lift | margin (target − true) |
| --- | ---: | ---: | ---: |
| L5 | **9.70** | 7.09 | +10.81 |
| L20 | **1.81** | 6.16 | +2.00 |

Deep/shallow suppression ratio **0.19**. The layer-20 edit does ~87% of the target
promotion and ~19% of the belief displacement. Its failure to reach other probes follows
directly from never having displaced the belief — no breakdown between delivery and effect
is needed to explain the table above, and the ticket named this as its lens-7 baseline
("the dumbest explanation is that the L20 edit is weaker at everything"). The baseline won.

**The gate at n=4 also overstated both arms** (+9.37/+9.52 against +6.16/+7.09 at n=42).
A 4-subject gate was too small for the quantity it was gating on.

### What survives, as an EXISTENCE claim only

ROME's own Efficacy Score is `P(target) > P(true)` on the edit prompt:

| condition | ES | mean margin | true-answer drop >2 nats |
| --- | ---: | ---: | ---: |
| base | 0.0% | −5.97 | — |
| L5 | 100.0% | +10.81 | 38/42 |
| L20 | **76.2%** | +2.00 | **14/42** |

> **24 of 42 layer-20 edits pass ROME's efficacy criterion while leaving the true answer
> within 3 nats of where it started** — and those edits propagate to nothing. At layer 5
> the same cell holds 8/42.

An edit reported as working by the field's standard efficacy metric can therefore leave the
model's belief essentially intact. This is a statement about **what ES fails to
distinguish**, which is in scope — we measure what existing editors and their metrics do.
It is not a claim about ROME as normally run, and no rate is asserted: per [O-004] a
constructed set licenses existence, never frequency.

### Confound on the surviving claim, stated not buried

EasyEdit's `llama3-8b.yaml` hyperparameters (25 steps, lr 0.5, `clamp_norm_factor` 4.0)
are **layer-5 hyperparameters**, used unchanged at layer 20. This is "ROME's layer-5
configuration applied at layer 20", not "ROME at layer 20". The weak belief displacement is
plausibly under-optimisation — the optimiser getting the cheap part done and running out of
steps for the expensive part — rather than anything intrinsic to depth. That does not touch
the existence claim (those 24 edits pass ES and leave the belief standing, whatever made
them weak) and it does block any claim about depth.

### Consequence

[T-079] is **unanswered** and the design is corrected rather than abandoned: match the two
edits on **belief displacement**, not target lift, before comparing propagation. Opens
[E-028] and [T-084]. Nothing in the [E-016]–[E-021] arc is narrowed by this run, because
the run did not measure what it needed to.

**Artifacts:** agents/engineer/workspace/run_e026.py, run_e026b.py;
results/E-026-gate.json, E-026-depth.json, E-026b-edit-prompt.json;
logs/run_e026-2026-09-20-182859.log, logs/run_e026b-*.log

---

## [E-029] Result: the ES caveat does not exist at the standard edit layer — [T-085] closes

_Date: 2026-09-20 · Llama-3.1-8B, layer 5, 42 subjects, no new measurement_

Runs [T-085]. [E-026] left an observation its failure did not touch — edits passing ROME's
Efficacy Score while leaving the belief standing and propagating to nothing — and it was
worth asking whether that lived at **layer 5**, the configuration the field actually runs.
Had it, the finding would have stopped being about depth and become a general caveat on ES:
more defensible, and the form that would have gone into §6 of the write-up.

**It does not. The answer is Deny, and the line closes.**

### Two predictors, one outcome, same 42 subjects

| | mean | spread | Spearman rho with propagation | partial, baseline removed |
| --- | ---: | ---: | ---: | ---: |
| outcome: propagation | 10.19 | 15.45 | — | — |
| A: belief displacement | 9.70 | 23.04 | **0.419** | 0.432 |
| B: ES margin | 10.81 | 22.15 | **0.425** | 0.428 |

The two predictors are indistinguishable — 0.419 against 0.425, a gap of 0.006 against a
pre-stated Deny band of 0.2. ES carries the same information about propagation that belief
displacement does, so there is nothing at layer 5 that ES fails to see and displacement
catches.

**The joint cell exists and does nothing.** 8 of 42 layer-5 edits pass ES while displacing
the belief by less than 3 nats — and they propagate **8.86 nats against 10.51 for the
rest**. At layer 5 the edit reaches the other probes whether or not it moved the belief on
its own prompt, so membership in the cell predicts almost nothing.

### The confound I pre-registered was real; the one I predicted was not

*Familiarity* was controlled and is not driving anything: partialling out baseline
`log P(true answer)` moves both correlations by less than 0.015.

*Range restriction* — flagged in the ticket as "the adversary's best attack" — **was not a
problem, and predicting it was wrong.** The ES margin spans 22.15 nats (+2.29 to +24.44).
Its moderate rho is a real property of the predictor, not an artifact of a narrow window.
Recorded because a pre-registered worry that fails to materialise is as much a part of the
record as one that does.

### What this costs, and it is a claim of mine rather than a number

[E-026]'s 24/42 observation **stays a statement about weak or deep edits and must not be
promoted to a general critique of ES.** It was on its way to being written up as the more
valuable, more general form; this run says that form is unsupported. The cheap version of
the test killed the expensive version of the claim, which is the whole reason it ran first.

### What it opens

Neither predictor explains much: rho ~0.42 is roughly 18% of variance. **Most of what
determines whether a layer-5 edit propagates to a reformulated probe is captured by neither
the belief displacement on the edit prompt nor the ES margin.** [E-021] established the
subject-token delta is causally necessary and sufficient for relocation; it did not
establish what sets the *magnitude*. Spawns [T-086].

**Scope.** Layer 5, 42 subjects, one relation, one model, observational join of two prior
runs. Existence per [O-004]; no rate claimed.

**Artifacts:** agents/engineer/workspace/run_e029.py;
results/E-029-es-vs-propagation.json; logs/run_e029-2026-09-20-215433.log

---

## [E-028a] Result: T-084 unanswered — and target lift is worthless as a measure of edit strength

_Date: 2026-09-20 · Llama-3.1-8B, layers 5 and 20, steps {25,50,100}, 6 subjects_

Runs [T-084]: is [E-026]'s weak layer-20 edit under-optimisation, or depth? Grid and bar
were fixed in the source before the run and every cell is reported.

### The grid

Suppression of `log P(true answer)` on the edit prompt:

| layer | 25 steps | 50 steps | 100 steps | gain |
| --- | ---: | ---: | ---: | ---: |
| L5 | 6.26 | 7.18 | **8.31** | +2.05 (+33%) |
| L20 | 2.61 | 3.51 | **4.47** | +1.86 (+71%) |

**The verdict is PARTIAL and the control overrides it.** Layer 20 reaches 4.47 against a
bar of 6.79, and layer 5 gains 2.05 nats over the same grid — so more optimisation helps
everywhere, neither layer saturates, and the two are not matched at any budget in this
grid. **[T-084] is not answered.** The 2x3 crossing was added to this ticket precisely so
the run could say that instead of reporting a confident PARTIAL; the three-cell sweep the
ticket originally specified would have claimed a depth effect it has not earned.

### Target lift is constant everywhere, and that is the reportable finding

| | L5 s25 | L5 s50 | L5 s100 | L20 s25 | L20 s50 | L20 s100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| lift on injected target | 8.36 | 8.36 | 8.36 | 8.19 | 8.30 | 8.35 |
| suppression of true answer | 6.26 | 7.18 | 8.31 | 2.61 | 3.51 | 4.47 |

**Lift spans 0.17 nats across two layers and a fourfold step budget while suppression
spans 5.70.** It saturates by 25 steps and carries no information about edit strength
thereafter.

This is an independent confirmation of [E-026]'s RCA arriving from the opposite direction.
That gate was diagnosed as wrong by reasoning about what a logit nudge can do; this
measures it. **Any gate, metric, or report built on target promotion alone is blind to
everything that separates a 2.61-nat edit from an 8.31-nat one.**

### EasyEdit's shipped 25 steps are under-converged at the STANDARD layer

Layer 5 gains 33% more belief displacement from four times the steps, and layer 20 gains
71%. `hparams/ROME/llama3-8b.yaml` ships `v_num_grad_steps: 25`. That is a fact about the
configuration the field actually runs, it holds at the layer the field actually edits, and
it is independent of how the depth question resolves.

### The extra optimisation is DIRECTION at layer 5 and partly MAGNITUDE at layer 20

| | 25 | 50 | 100 |
| --- | ---: | ---: | ---: |
| L5 ‖Δv‖ | 7.20 | 7.23 | **7.25** |
| L20 ‖Δv‖ | 5.77 | 6.41 | **6.90** |

At layer 5 the delta's norm is flat to within 0.7% while suppression climbs 33% — the
optimiser is turning the vector, not growing it. The same direction-not-magnitude structure
[E-020] found for the depth decay, now in the optimisation trajectory. At layer 20 the norm
grows 20%, so the two layers differ in *how* they improve, not only in how far they get.

### The norm clamp is not binding, so the grid can be extended

`clamp_norm_factor: 4.0` gives ceilings of 13.55 at L5 and 20.90 at L20. Measured
occupancy: **54% at L5 and 33% at L20, with 0 of 6 subjects at the cap in any cell.** No
route-1 result is an artifact of the clamp, and more steps remain available.

### A trend, stated as a trend

The L20/L5 suppression ratio rises **0.42 -> 0.49 -> 0.54** across the grid. That leans
toward under-optimisation over depth. It is three points on six subjects and is recorded
as a direction to test, not as a finding.

### Consequence

Matching by *saturation* is expensive — neither layer had saturated at 100 steps. Matching
by *budget* is cheap and sufficient: find the step count at which layer 20 reaches layer
5's 25-step displacement (6.26 on these subjects) and compare there. Extrapolating ~0.93
nats per doubling puts it near 400 steps. Opens [E-028b].

**A calibration error worth recording.** The pre-registered bar of 6.79 came from [E-026b]'s
n=42 measurement of 9.70, but this sweep runs on 6 subjects whose layer-5 suppression is
6.25 — so **layer 5 fails its own bar at 25 steps**. The bar was not moved; the within-run
layer-5 arm is the correct matched reference and exists only because the crossing was
added. The general lesson is the same class as [E-026]'s gate error one level up: **a
threshold calibrated on one sample does not transfer to a subsample of it, and a gate
should be defined against a within-run reference.**

Cross-check worth keeping: E-028a's fresh layer-5 optimisation at 25 steps reproduces
[E-026b]'s cached [E-014] deltas on the same 6 subjects to **0.01 nats** (6.26 vs 6.25),
confirming `compute_v_batch` is deterministic and reproduces the published vectors.

**Artifacts:** agents/engineer/workspace/run_e028a.py; results/E-028a-step-sweep.json;
logs/run_e028a-2026-09-20-203859.log; logs/clamp_check-2026-09-20-221953.log

---

## [E-028c] Result: T-084 answered — and equal delivery still does not give equal effect

_Date: 2026-09-21 · Llama-3.1-8B, layers 5 and 20, 12 subjects_

### [E-028b] — the budget match, and [T-084]

| steps at L20 | calibration | held out |
| ---: | ---: | ---: |
| 25 (EasyEdit's shipped config) | 2.61 | — |
| 100 | 4.47 | — |
| 200 | 5.46 | 6.23 |
| **400** | **6.50** | **7.43** |

Target was 6.26 nats — ROME/EasyEdit at layer 5 with 25 steps. Layer 20 crosses it at
~353 steps, and the held-out six confirm the budget transfers (gap 0.93 against a 1.5
threshold), so it was not fitted to noise.

**[T-084] answers toward UNDER-OPTIMISATION.** ROME's update rule at layer 20 *can* reach
layer-5 belief displacement; it needs a **16x step budget** to do it. [E-026]'s weak deep
edit was an artifact of applying EasyEdit's layer-5 hyperparameters unchanged at depth,
exactly as that ticket's confound warned. The pre-registered stop at 400 was not reached.

### [E-028c] — propagation at matched displacement

| arm | displacement on edit prompt | ‖Δv‖ |
| --- | ---: | ---: |
| ROME/EasyEdit L5 (25 steps) | 7.26 | 7.27 |
| ROME update rule L20 (400 steps, matched) | 6.97 | 7.52 |

| form | layer | baseline | post-edit | drop | coefficient |
| --- | --- | ---: | ---: | ---: | ---: |
| subject-initial | L5 | −1.12 | −10.99 | **9.66** | 1.000 |
| subject-initial | L20 | −1.12 | −4.69 | **3.59** | 1.000 |
| possessive | L5 | −1.45 | −10.11 | 8.43 | 0.962 |
| possessive | L20 | −1.45 | −1.73 | 0.31 | 0.615 |

**VERDICT: UNMATCHED**, by this ticket's own pre-registration — the subject-initial arm
moved 63%, far outside the 20% band, so the possessive arm may not be read.

**But the UNMATCHED outcome is now the finding, and it is not the one [E-026] produced.**
That run's deep arm was simply weak: 1.81 nats of displacement against 9.70. This one is
not. The two arms match on belief displacement (6.97 vs 7.26), on delta norm (7.52 vs
7.27), and on delivered coefficient (exactly 1.000 at both layers, analytic). **They still
differ 63% in how far the edit travels to a prompt sharing the edit's prefix.**

That is a dissociation between delivery and effect with the "weaker edit" account largely
removed — which is precisely the claim [E-026] asserted without having earned it.

### The confound that is now load-bearing, and it is mine by construction

**Step budget is perfectly collinear with layer in this design.** Displacement was matched
by giving the deep arm 16x the optimisation. So "applied at layer 20" and "optimised for
400 steps" cannot be separated, and a heavily optimised edit may simply be more specific to
the prompt it was optimised on — more steps, more overfitting to that continuation,
independent of depth.

This is not a footnote; it is the whole alternative explanation, and nothing in [E-028c]
addresses it. **The control is to run layer 5 at 400 steps** and read its propagation. If
L5@400 propagates like L5@25, budget is not the driver and layer is. If L5@400 also
collapses, the effect is overfitting and has nothing to do with depth. Opens [E-028d].

### Scope

n=12; the displacement matching is **aggregate, not per-subject** (median absolute gap 2.29
nats, max 6.88) while the design is within-subject paired. One model, one relation, one
pair of layers. Existence per [O-004]; no rate.

**Naming.** The deep arm is *ROME's update rule at layer 20, 400 steps,
displacement-matched*. It is **not** "ROME at layer 20" — EasyEdit's shipped config reaches
2.61 nats there. [E-013] gate 0 set the convention of naming the configuration rather than
the method; this is the first run where the two genuinely diverge.

**Artifacts:** agents/engineer/workspace/run_e028b.py, run_e028c.py;
results/E-028b-budget-match.json, E-028c-matched-propagation.json;
logs/run_e028b-2026-09-21-070632.log, logs/run_e028c-2026-09-21-093658.log

---

## [E-028d] Result: it is the LAYER — and the coefficient does not predict effect

_Date: 2026-09-21 · Llama-3.1-8B, 12 subjects · completes the [E-026] → [E-028] arc_

The fourth cell, bought to break the collinearity [E-028c] built in. **The coefficient at
the subject's last token is exactly 1.000 in every cell below** — analytic, all four share
the edit prompt's prefix.

| cell | belief displacement | propagation | propagation per nat displaced |
| --- | ---: | ---: | ---: |
| L5, 25 steps (EasyEdit's shipped config) | 7.26 | 9.66 | **1.33** |
| L5, 400 steps | 11.74 | 12.96 | **1.10** |
| L20, 25 steps | 2.61 | 0.80 | **0.31** |
| L20, 400 steps (displacement-matched) | 6.97 | 3.59 | **0.52** |

### The budget account is refuted, and refuted twice

Pre-registered: LAYER if `P(L5,400) >= 7.73`, BUDGET if `<= 4.31`. Measured **12.96**.

More optimisation makes an edit reach **further**, not less far — **+34% at layer 5 and
+349% at layer 20**. That is the opposite sign to the overfitting account, so BUDGET fails
on the band test *and* on the direction of its own predicted mechanism. The clamp did not
bind (62% of ceiling, 0/12 at cap), so nothing here is capped.

### What the arc establishes

Normalising propagation by belief displacement removes edit strength from the comparison:

> **1.22 nats of reach per nat displaced at layer 5, against 0.41 at layer 20 — a factor
> of 2.96, holding across a 16x range of optimisation budget.**

The layer gap survives within every budget (12.1x at 25 steps, 3.6x at 400) and the budget
gap reverses direction, so the two are cleanly separated.

**[T-079] is answered, and the answer is DENY.** The delivered coefficient is exactly 1.000
at the subject's last token at both layers, for the same probe, with matched displacement
and comparable ‖Δv‖ — and the same delivered vector produces three times the effect from
layer 5. **The coefficient bounds delivery. It does not predict effect.**

### What this costs the project's central arc

Everything from [E-016] to [E-021] measures **delivery**, and must be described that way.
The claim that survives is unchanged in content and narrower in reach:

> Any probe beginning with the edited subject receives the full, unattenuated edit vector
> at the subject position — at every layer, for any `C`, regardless of relation.

What may **no longer** be inferred from it is how much that probe's answer will move.
[E-021]'s causal result — the subject-token delta is necessary and sufficient for
relocation — stands as a **layer-5** claim. [E-026]'s withdrawn headline said exactly this
conclusion before it was earned; it is now earned, through matched displacement ([E-028c]),
matched norm, and a budget control that breaks the collinearity ([E-028d]).

### Scope and one recorded defect

n=12, one model, one relation, two layers, one probe form for the headline. Displacement
matching in [E-028c] is aggregate rather than per-subject (median |gap| 2.29 nats).
Existence per [O-004]; no rate.

**Defect in the run's own reporting, fixed.** `run_e028d.py` closed with a line reading
"a fall in reach alongside a rise in strength", written while anticipating the BUDGET
outcome. It fired on the LAYER outcome and described the data backwards — the numbers it
printed were correct and the sentence around them was not. The direction is now read from
the data rather than assumed by the author. Same family as [E-025]'s retracted headline:
prose written in advance of a result will describe the result the author expected.

**Artifacts:** agents/engineer/workspace/run_e028d.py;
results/E-028d-budget-control.json; logs/run_e028d-2026-09-21-094454.log

---

## [E-030] Result: the GPT-J floor is architectural — [E-027]'s narrowing is confirmed

_Date: 2026-09-27 · GPT-J-6B, 36 subjects re-gated on GPT-J, coefficient only_

Runs [T-082]. §4.3 of the paper narrows [E-018]'s "different subjects are near-orthogonal
at the subject position" to a **Llama-3.1-8B statement**, on the strength of GPT-J's higher
floor. That narrowing was published flagged **plausible, not confirmed**, because the
subjects had been possession-gated on *Llama* and run on GPT-J unfiltered: unfamiliar names
might share a generic direction and inflate the floor by construction.

**They do not. The flag comes off.**

| layer | HELD floor (n=21) | NOT-HELD floor (n=15) | gap | gap / SEM |
| --- | ---: | ---: | ---: | ---: |
| L4 (f=0.15, the edit layer) | 0.146 ± 0.017 | 0.146 ± 0.021 | **−0.000** | −0.01 |
| L17 (f=0.63) | 0.411 ± 0.034 | 0.388 ± 0.032 | −0.024 | −0.50 |
| L27 (f=1.00) | 0.527 ± 0.038 | 0.460 ± 0.055 | −0.067 | −0.99 |

Pre-stated ARCHITECTURAL band was a gap below 0.05 at the edit layer. Measured **0.000**.

### Three strands, and the headline is the weakest of them

1. **The gap is zero** at the edit layer — 0.146 against 0.146.
2. **Every gap has the wrong sign.** Familiarity predicts NOT-HELD *above* HELD at every
   layer. NOT-HELD is *lower* at all three. All three are within 1 SEM, so the reversal is
   not itself a finding — but a hypothesis that predicts a positive gap and gets a
   consistently negative one is not weakly supported, it is unsupported.
3. **The premise was shaky to begin with.** GPT-J holds **21 of 36** of these subjects
   (58%). The worry was that GPT-J does not know these people; it knows most of them.

**Confound 3 did not fire.** The same-subject coefficients are 0.865 (HELD) against 0.846
(NOT-HELD) at the edit layer, so the split is not picking up some other property of the
subjects.

### The caveat that survives, and its limit

The pool confound is asymmetric and it weakens **this** direction specifically: [E-023]
showed candidate pools undercount, which moves subjects from HELD into NOT-HELD and
**dilutes** the contrast. A zero gap is therefore the outcome a bad pool would also
produce, and that objection is not answered by strand 1.

It is partially answered by strands 2 and 3. Dilution drives a gap toward zero; it does not
naturally drive it negative at every layer, and it says nothing about GPT-J holding 58% of
the subjects outright. The honest position: **no difference, and certainly not in the
predicted direction**, with the residual risk that a better pool would reveal a small
positive gap we cannot currently see.

### Consequence

> "Different subjects are near-orthogonal at the subject position" is a **Llama-3.1-8B**
> statement, not a ROME one. GPT-J's floor is roughly twice as high at the edit layer and
> reaches 0.527 at the last layer, where it exceeds the same-subject value — and this is a
> property of the architecture, not of which subjects we happened to feed it.

§4.3's margin note is updated: the narrowing is confirmed and the plausible-not-confirmed
flag is removed. The claim in §4.3's body was already correctly scoped and does not change.

**Scope.** 36 subjects, one relation family, three depths, coefficient only, no edits.
Possession measured with the shipped filter and its pool. Existence per [O-004].

**Artifacts:** agents/engineer/workspace/run_e030.py;
results/E-030-floor-by-possession.json; logs/run_e030-2026-09-27-103338.log

---

## [E-031] Result: NO DIP — and the observation dies for a better reason than significance

_Date: 2026-09-27 · Llama-3.1-8B and GPT-J-6B, 20 subjects, 8 depths, coefficient only_

Runs [T-083]. [E-027] noticed both models' different-subject floors dipping near depth
fraction 0.15 — roughly where ROME edits in both — on 4 and 6 points at n = 12–16. This
put five points below fraction 0.25 where there had been two.

| depth fraction | 0.00 | 0.06 | 0.10 | 0.16 | 0.23 | 0.32 | 0.55 | 1.00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama-3.1-8B | 0.067 | **0.048** | 0.061 | 0.095 | 0.168 | 0.234 | 0.326 | 0.697 |
| GPT-J-6B | 0.303 | 0.244 | **0.144** | 0.153 | 0.221 | 0.309 | 0.426 | 0.543 |

**VERDICT: NO DIP**, by the pre-registered test.

### The test failed on a technicality, and that is recorded as a defect

The criterion required the minimum to sit below **both** neighbours by more than one SEM.
GPT-J's minimum has a **flat bottom across two adjacent samples** — 0.144 at f=0.11 and
0.153 at f=0.15, well within each other's error — so no single point can be below both
neighbours. **Finer spacing defeats the criterion**, which is a flaw in the test rather
than evidence about the world, and it would have been visible before the run.

### The observation dies anyway, for a reason that needs no threshold

1. **The minima are in different places.** Llama at fraction **0.06**, GPT-J at **0.11**.
   Not the same location, so there is no shared phenomenon to explain.
2. **Neither sits where ROME edits.** Llama's edit layer is L5, fraction **0.16**, where
   the floor is **0.095** — roughly **twice** its minimum of 0.048.

So *"ROME edits where subjects are maximally separated"* is **false on its own terms**,
before any question of significance. The narrative [T-083] was opened warning about — "too
satisfying not to over-read" — is dead, and the warning was warranted.

### What survives, and it needs no threshold at all

> The floor is lowest in the **first fifth** of the network and rises monotonically
> thereafter — Llama 0.048 → 0.697, a **14×** range across depth.

That is a statement about representations, it holds in both models, and it is what §4.3
should say instead. The dip sentence comes out of the margin.

**Artifacts:** agents/engineer/workspace/run_e031.py; results/E-031-floor-curve.json;
logs/run_e031-2026-09-27-*.log

---

## [E-032] Result: the pinning is exact from 6B to 405B — the floor is not a scale law

_Date: 2026-09-27 · Llama-3.1-70B (base) and Llama-3.1-405B-Instruct, 12 subjects, coefficient only_

Runs [T-080] at scale. Coefficient measurement needs **no gradients**, so this cost ~24
traces where an *edit* at 405B would have cost days.

### The analytic claim holds at every scale tested

| model | params | layers | prefix-sharing probes |
| --- | ---: | ---: | --- |
| GPT-J-6B | 6B | 28 | **1.000**, worst deviation 0.0e+00 |
| Llama-3.1-8B | 8B | 32 | **1.000** |
| Llama-3.1-70B | 70B | 80 | **1.000**, worst deviation 0.0e+00 |
| Llama-3.1-405B-Instruct | 405B | 126 | **1.000**, worst deviation 0.0e+00 |

Four models, a **68× parameter range**, two architectures, base and instruction-tuned.
Expected — the derivation mentions neither scale nor training — and now measured.

### The decay is approximately scale-invariant, and only just

Reordered probes at matched depth fraction, against Llama-3.1-8B:

| model | 0.00 | 0.06 | 0.10 | 0.16 | 0.23 | 0.32 | 0.55 | 1.00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8B (reference) | 0.992 | 0.960 | 0.930 | 0.951 | 0.900 | 0.858 | 0.700 | 0.598 |
| 70B | 0.964 | 0.956 | 0.970 | 0.950 | 0.961 | 0.922 | 0.569 | 0.549 |
| 405B-Instruct | 0.916 | 0.966 | 1.000 | 0.968 | 0.971 | 0.901 | 0.556 | 0.601 |

Worst deviations **0.131** and **0.144** against a pre-stated band of 0.15. That is a pass,
and it is close enough to the threshold that it should be reported as *approximately*
invariant rather than as a clean result. The deviation is concentrated at fraction 0.55,
where the larger models fall further and faster; through the first third all four profiles
sit within about 0.07 of one another.

### The floor is NOT a scale law, and the tidy story is refused

Mean floor at depth fractions 0.10–0.23:

| model | floor | best contrast against same-subject |
| --- | ---: | ---: |
| GPT-J-6B | 0.144 | 6× |
| Llama-3.1-8B | 0.061 | 16× |
| Llama-3.1-70B | **0.110** | 27× |
| Llama-3.1-405B-Instruct | **0.012** | **108×** |

405B's separation is extraordinary — floor **0.009** at fraction 0.10 with a maximum across
all 12 subjects of **0.042**, so it is not outlier-driven, against a same-subject value of
0.992. Different people's subject keys are very nearly orthogonal there.

**But 70B (0.110) is worse than 8B (0.061), so this is not monotone in scale and no scale
law may be claimed from it.** Four points, non-monotone, and the 405B arm is
instruction-tuned — it varies scale *and* post-training together, and instruction tuning is
exactly the sort of thing that could move subject representations. The honest statement is
that **floor magnitude is model-specific**, with 405B-Instruct showing by far the cleanest
separation of anything measured.

### Two structures that do hold in all four models

1. **The floor is high at layer 0** (70B 0.465, 405B 0.844) — before contextualisation the
   key is embedding-driven and names share subword statistics.
2. **The measure stops discriminating near the output.** At fraction 1.00 the floor
   *exceeds* the same-subject value on 70B (0.633 against 0.507) and GPT-J, as [E-020]
   found on 8B at layer 31. Representational convergence near the output is general.

**Scope.** n=12, one relation family, coefficient only, no edits applied at any scale.
The 405B arm confounds scale with instruction tuning and must never be cited for scale
alone. Existence per [O-004].

**Artifacts:** agents/engineer/workspace/run_e032.py; results/E-032-scale.json;
logs/run_e032-2026-09-27-*.log

---

## [E-033] Decision: editing at scale was blocked by a one-line device bug, not by NDIF

_Date: 2026-09-27 · found while scoping the relation crossover_

**Decision:** editing experiments may now run at 70B and 405B. The blocker was ours.

`compute_v_batch`'s loss accumulated `weight_decay * (Dd[i] * Dd[i]).sum()` — computed on
the device holding the edited layer — together with `nll` and `kl`, which derive from
`lm_head`. On a model small enough for one GPU those are the same device. On a sharded
model they are not, and the sum raises

    RuntimeError: Expected all tensors to be on the same device,
    but found at least two devices, cuda:3 and cuda:0!

**Rationale for recording it rather than just fixing it:** the failure is invisible at
every size this project had run, so it would have been read as "NDIF cannot do gradients at
70B" by anyone who probed once and stopped. That is the [O-007] pattern exactly — a
platform blamed for a local defect. The fix is `decay.to(nll.device)`.

**Measured after the fix**, two gradient steps, one spec:

| model | time | ‖Δv‖ | d_model |
| --- | ---: | ---: | ---: |
| Llama-3.1-8B | 19s | 1.97 | 4096 |
| Llama-3.1-70B | **21s** | 3.66 | 8192 |
| Llama-3.1-405B-Instruct | **24s** | 1.74 | 16384 |

**Round trips dominate, not compute.** A 68x parameter increase costs 26% more wall clock
per optimisation step, because the budget is queue and transfer. Editing at 70B is
therefore about as expensive as editing at 8B, which changes what this project can afford:
[E-028]'s whole arc could be re-run at 70B for roughly its original cost.

**Revisit if:** a larger batch changes the picture — these are single-spec probes, and
transfer scales with batch while queue does not.

**Artifacts:** src/edit.py (the `decay.to(nll.device)` fix and its comment)

---

## [E-033] Interim: type matching is the mechanism — the "floor" was one pairing

_Date: 2026-09-27 · Llama-3.1-8B and Llama-3.1-70B · **4 of 6 arms complete, 2 in flight**_

Runs [T-081], the third and last of [T-065]'s never-varied dimensions. **Recorded as
interim**: the 8B birthplace replication and the 70B occupation arm at layer 5 are still
running. Neither can overturn what is below — both are confirmation cells — but this entry
is not a close.

[E-025] reported two effects from a birthplace edit: a **floor** (everything about the
subject suppressed to one level) plus **type-matched displacement** (extra penalty where
the probe's answer type matches the injected value). Stated as a general mechanism,
measured on one relation. **One half generalises. The other does not.**

### The crossover holds: swap the injected type and the displaced probe swaps with it

| Llama-3.1-8B · layer 5 | birthplace edit | occupation edit | swing |
| --- | ---: | ---: | ---: |
| occupation | 1.80 | **6.59** | **+4.80** |
| citizenship | **7.13** | 3.87 | −3.27 |
| language | 5.49 | 2.40 | −3.09 |

**Difference-in-differences +8.06 nats.** At Llama-3.1-70B layer 13, **+5.42**.

**In 5 of 5 completed arms the type-matched probe moved most**, with no exceptions:
8B/birthplace, 8B/occupation, 70B-L13/birthplace, 70B-L13/occupation, and
70B-L5/birthplace. The last of those matters separately — it shows the result surviving a
**layer** change within a model, not only a model change.

**Depth is matched by fraction, not index.** Layer 13 of 80 is fraction 0.165 against 8B's
layer 5 of 32 at 0.161. A first pass used layer 5 on both, which is fraction 0.06 at 70B —
[E-028] showed layer changes propagation threefold, so that pairing was not a comparison.
Its numbers are retained as the second-depth cell rather than discarded.

### The floor does not generalise, and [E-025]'s cell is the outlier

Post-edit levels of the two **non**-matched probes, which a floor account says should
coincide:

| arm | non-matched levels | spread |
| --- | --- | ---: |
| 8B L5 birthplace | language −6.20, occupation −6.16 | **0.04** |
| 8B L5 occupation | citizenship −5.83, language −3.11 | **2.73** |
| 70B L13 birthplace | language −4.82, occupation −5.94 | 1.11 |
| 70B L13 occupation | citizenship −4.18, language −3.16 | 1.02 |
| 70B L5 birthplace | language −5.23, occupation −6.79 | 1.56 |

[E-025]'s **0.04** is the outlier, not the rule. Every other arm sits 1.0–2.7 nats apart,
and all four returned the pre-stated **NO FLOOR** verdict. The convergence that named the
effect was a property of that one relation on that one model.

**What this costs:** [E-025]'s two-effect account is narrowed to one effect. "An edit
suppresses everything about the subject to a floor" is withdrawn as a general claim;
"an edit displaces probes whose answer type matches the injected value" survives, and is
now the strongest behavioural result in the project — a crossover, in two models, at two
depths.

### Two engineering defects found on the way, both mine

1. **`optimise()` halved the batch on any first failure**, without classifying it. A
   node-dependent whitelist rejection ([O-007]) was read as an oversized batch: it shrank
   a batch that was never too big, hit another flaky node, and parked for minutes. A
   2-spec probe succeeding while a 12-spec batch "failed" looked exactly like a size
   limit. It now classifies before resizing, and logs the message rather than only the
   type — the second time in one day that omission cost a run.
2. **The scores cache omitted the layer from its key.** A layer-13 run would have loaded
   layer-5 scores and reported them as new numbers, with no error anywhere, and the output
   filename would have overwritten the other arm. Caught before the re-run. Layer is now
   in the deltas cache, the scores cache and the filename — the
   `possession.FilterConfig.fingerprint` discipline, applied late.

**Scope.** n=29, two relations, two models, two depths, layer-5-equivalent only for the
matched comparison. Existence per [O-004].

**Artifacts:** agents/engineer/workspace/run_e033.py;
results/E-033-crossover-*.json; logs/run_e033-2026-09-27-*.log
