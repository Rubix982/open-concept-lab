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
