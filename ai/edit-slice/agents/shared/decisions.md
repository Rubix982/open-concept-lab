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
