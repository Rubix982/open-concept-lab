# The Card

One card open at a time. Six fields. Nothing starts until all six are filled, nothing else starts until this one is closed.

A card closes with a number, or with a sentence that could have come out the other way. Never with "explored" or "built". Field 6 is the one that kills cards; fill it honestly.

Promotion to the ten-lens Design Protocol happens only when field 4 names a load-bearing published claim, or field 5's two branches cost more than a week apart.

---

## C-003 · Does an edit break the old answer and supply the new one by two different routes?

**Status:** closed
**Opened:** 2026-11-01
**Closed:** 2026-11-01 — **branch 1**, and the two halves separate in opposite directions

**1. WHERE WE ARE.**
[E-002] measured **destruction** over 495 probes: editing *this person rather than someone else* is worth +0.0583 paired median, editing *this fact rather than another fact about the same person* is worth +0.0009 — sixty-five times less. [E-014], on a different probe set and a different metric family, has **destination** at 67% for the real edit against 5% for the same-subject control.

**2. WHAT WE ARE DOING.**
Re-score the same 495 probes of [E-002] for destination — the post-edit top-1 token over the full vocabulary, under the `real`, same-subject `ctl` and different-subject `other` arms — and report, per arm and per family, the fraction whose top-1 token begins a city in that subject's injected target country.

**3. WHY.**
The two-route reading is assembled from three experiments built for other questions, with different probe sets and different metric families. We do not know whether destruction and destination separate **on one probe set under one metric**. After this we have three destination rates on the exact 495 probes that produced the destruction numbers, and the split is measured or it is not.

**4. WHAT IS AFFECTED.**
- T-007 becomes answered or dropped.
- The **[E-013] scope note** appended to `edit-slice/agents/shared/decisions.md`, which currently rests on comparing [E-002] against [E-014] *across* probe sets. This decides whether it can rest on one.
- `edit-slice/notes/email-3-direct-exposure.md`, unsent. Its behavioural leg is destruction only.
- [E-014]'s 67% / 5% is either replicated on a second probe set or contradicted.

**5. CONCLUSION IF WE DO IT.** Three branches, written before the run.

- **If `real` ≫ `ctl` and `real` ≫ `other` on destination, on the same probes where `real ≈ ctl` on destruction:** the split is measured rather than inferred. One rank-one update does two separable things — it breaks the old answer because it touched that subject's key, and it supplies the new one because of what it said.
- **If `real ≈ ctl` on destination too:** there is no split. The apparent one was an artefact of comparing two experiments across probe sets and metrics, and the [E-013] scope note is wrong and is struck rather than left standing.
- **If all three arms sit near zero:** these probes have no measurable destination at all, and the 495-probe set cannot answer the question. That would mean [E-002]'s movement numbers record destruction with nowhere identifiable for the mass to go — which needs recording before anything leans on them. **This is the branch that costs the most.**

**6. CONSEQUENCE OF NOT DOING IT.**
The two-route reading stays a story told across three experiments, the [E-013] scope note stays cross-set, and email 3 goes out with one behavioural leg instead of two.

**Controls, and what could make this wrong. Three were checked before the run rather than after.**

- **Magnitude, `real` against `ctl`.** Never matched, unlike the donor arm in [E-002]. **Checked, and the honest version is narrower than the first one written here:** the *signed* paired median difference in `‖delta_v‖/‖k*‖` is +0.0899 with `ctl` weaker in 20 of 42, so `ctl` is not systematically the weaker edit. But the *unsigned* median difference is 0.7614 over a range of 2.627, so the two arms are **not matched subject by subject** — only unbiased in direction. That is enough for an aggregate hit rate over 495 probes and it is **not** enough for a per-subject claim, which this card therefore does not make.
- **First-token resolution.** The probes ask for a *city* and the edit injects a *country*, so a bare argmax-equals-target test would under-count badly. A hit is instead "the top-1 token begins a city in the target country". **Checked:** the 81-city map gives 80 distinct first tokens, every one resolving to exactly one country. Zero ambiguity, so the mapping adds no slack of its own.
- **The `ctl` arm cannot deliver its own content here, and that bounds the claim.** The control edit injects an occupation (`By profession, {} is a` -> `urban planner`) while these probes ask for a city, so no arm-symmetric "does each arm deliver *its own* target" check exists on this probe set. What this measures is whether **content that can answer the question is what arrives** — not whether every edit delivers its own content somewhere.
- **The anchor gate runs again.** 42 traces, and it has caught two faults.
- **Cost.** Three remote passes over 495 probes, grouped by subject. The `base` arm is not re-run: [E-001] holds `base_token` and `p_base` on disk, so T-007's "four arms" costs three.

**Closed:** 2026-11-01. Paired over the same 495 probes, bootstrap 10,000, seed 1538:

    destination   real - ctl     +0.2828   95% CI (+0.2424, +0.3232)
                  ctl  - other   +0.0000   95% CI (-0.0101, +0.0101)

    destruction   real - ctl     +0.0009   95% CI (+0.0004, +0.0024)   [E-002]
                  ctl  - other   +0.0583   95% CI (+0.0472, +0.0732)   [E-002]

Hit rates: base 1%, real 29%, ctl 1%, other 1%. Discordant pairs, real against ctl: **142 to 2**.

**Branch 1.** On the same probes, destruction barely distinguishes the real edit from a different edit on the same person and strongly distinguishes that person from someone else. Destination does the exact reverse. One rank-one update breaks the old answer because it touched that subject's key, and supplies the new one because of what it said.

The same-subject control sits at the **base rate** on destination, so it delivers nothing rather than a little — while destroying the old answer to within +0.0009 of the real edit.

This replicates [E-014]'s 67% / 5% on a second probe set in a different metric family, at 29% / 1%. The levels differ because [E-014] scored a restricted city pool by teacher forcing and this is a free argmax over the whole vocabulary. **The separation carries; the level does not**, and nothing here should be quoted as a rate.

**What it does not settle, carried forward.** The control injects an occupation and these probes ask for a city, so there is no arm-symmetric check that each arm delivers *its own* content. What is measured is that content which can answer the question is what arrives. Aggregate only: the two arms are unbiased in magnitude direction, not matched per subject.

Artifacts: `results/E-003-destination.json`, `results/E-003-summary.md`, `agents/shared/decisions.md` → [E-003].

---

## C-002 · Does an edit's effect depend on what it said, or only on whose key it touched?

**Status:** closed
**Opened:** 2026-10-31
**Closed:** 2026-10-31 — **branch 1**, and the gap is quantified

**1. WHERE WE ARE.**
[E-001] measured a raw correlation of 0.522 between predicted reach and measured movement, which falls to an excess of 0.085 (CI −0.003 to 0.172) once a **same-subject control edit** is removed — that control alone accounting for about 72% of the median movement.

**2. WHAT WE ARE DOING.**
Score the same 495 probes a third time, under a **different subject's** cached edit — subject B's `delta_v` and `k*` applied while probing subject A — and report the three medians side by side against the `real` and same-subject `ctl` arms already measured, per family.

**3. WHY.**
We do not know whether an edit moves a probe because of *what it said* or because of *whose key it touched*. [E-001] is consistent with the second and cannot distinguish them, because both its arms edit the same person. A third arm that changes the person while holding everything else fixed separates them. After this we have three medians and two contrasts.

**4. WHAT IS AFFECTED.**
- The post-hoc reading recorded in [E-001] — that subject-keyed movement may be the phenomenon rather than the confound — either becomes a pre-stated result or dies. It may not be used either way until this closes.
- `notes/email-3-direct-exposure.md`, unsent. Its critique currently rests on **counting** whether the edited subject appears in a prompt. This decides whether it can also rest on behaviour.
- [E-013]'s control design in edit-slice: if movement is subject-keyed, the same-subject control removes signal rather than noise *for this class of question*, which is a scope note that belongs on that decision.

**5. CONCLUSION IF WE DO IT.** Three branches, because the third is the one that would hurt and it has to be written down before the run.

- **If `real ≈ ctl` and both ≫ `different-subject`:** movement is keyed on the subject, not the content. Direct exposure is then demonstrable in behaviour and not only in prompt-counting, and email 3 gains a second leg. The same-subject control gets a scope note in [E-013].
- **If `real` is meaningfully above `ctl`:** content does matter, [E-001]'s post-hoc reading is wrong and is struck from the record rather than left standing, and the conclusion that the coefficient fails to predict effect gets *stronger* — it had content to predict and did not.
- **If all three arms are alike, different-subject included:** we are measuring generic instability and nothing is keyed on anything. That would undercut [E-001]'s raw 0.522 as well as the behavioural half of the critique, and it would mean the floor arms in every prior run need re-reading. **This is the branch that costs the most and it is the reason the arm is worth running.**

**6. CONSEQUENCE OF NOT DOING IT.**
[E-001]'s most interesting sentence stays post-hoc and therefore unusable, email 3 goes out resting on arithmetic over prompt strings alone, and we would hold a finding we cannot name without over-reading it.

**Controls and what could make this wrong.**
- **Magnitude.** Edits differ in `norm_ratio`. B's edit must be matched to A's in magnitude or a weak different-subject arm proves nothing. Pair by closest `norm_ratio`, record the residual spread, and report it.
- **Pairing.** Deterministic: subjects sorted by `case_id`, A paired with the nearest-magnitude B that is not A. Recorded in the output.
- **The anchor gate runs again.** It is 42 traces and it has already caught two faults.

**Closed:** 2026-10-31. Paired median differences over 495 probes, bootstrap 10,000, seed 1538:

    real  -  same-subject      +0.0009   95% CI (+0.0004, +0.0024)
    same-subject - diff-subj   +0.0583   95% CI (+0.0472, +0.0732)
    real  -  diff-subject      +0.0842   95% CI (+0.0667, +0.0974)

**Branch 1.** Editing *this person rather than someone else* is worth **0.0583**. Editing *this fact rather than another fact about the same person* is worth **0.0009** — sixty-five times less. Both intervals exclude zero, so content is not irrelevant; it is detectable and small.

Donor edits were matched on magnitude (median |difference| 0.0255 against a range of 2.627), so the different-subject arm is not merely weaker.

**A statistic that would have misled, recorded because it nearly did.** The per-arm medians read 0.0977 / 0.0625 / 0.0016, which makes `real` look 56% above the same-subject control. That is a difference *of medians* over skewed distributions. The paired median *of differences* is +0.0009. The arms are measured on the same probes, so the paired form is the one that answers the question, and the unpaired one overstates the content effect by about sixty-fold.

**What this settles.** The post-hoc reading recorded in [E-001] is now pre-stated and measured: a probe moves because an edit happened to its subject, almost regardless of what the edit said. Direct exposure is demonstrable in behaviour and not only by counting prompt strings.

**What it costs — narrowed after writing the scope note.** The first version of this line said [E-013]'s same-subject control "removes the signal" for this class of question. Reading [E-013] and [E-014] properly does not support the broad form: [E-014] has that same control at **5%** against the real edit's **67%** on whether the answer lands in the injected country.

Both hold because they measure different halves. This card measured **destruction** — what the old answer loses — which is subject-keyed. [E-014] measured **destination** — where the new answer goes — which is content-specific. The same-subject control is the wrong control for the first and the right one for the second. Recorded as **[E-013] Scope note** in edit-slice, appended.

---

## C-001 · Does predicted reach predict measured movement?

**Status:** closed
**Opened:** 2026-10-31
**Closed:** 2026-10-31

**1. WHERE WE ARE.**
The coefficient is exactly 1.000 for probes that begin with the edited subject (216 cells, four models 6B–405B, worst deviation 0.00e+00), falls from about 0.93 at layer 5 to about 0.52 at layer 24 when a preamble precedes the subject, and sits at a 0.082 different-subject baseline — all of it read from the **unedited** model, with no edit ever run at any layer but 5.

**2. WHAT WE ARE DOING.**
For each of the 42 subjects used in [E-014]/[E-016] and a fixed probe set, compute the layer-5 coefficient on the unedited model, then apply the ROME edit and measure the movement of the same (subject, probe) pair, and report the Spearman correlation between the two with the per-probe baseline removed.

**3. WHY.**
We do not currently know whether the coefficient carries any behavioural content. After this we have a correlation with an interval, over 42 × k pairs, and we know whether a threshold can be set on it at all.

**4. WHAT IS AFFECTED.**
- The email sent to Natalie and Arnab on 2026-10-31 (`ai/edit-slice/notes/email-3-direct-exposure.md`), which proposes a pre-edit screen.
- `ai/edit-slice/CLAUDE.md`, "Probe generation": *"If predicted and measured rankings correlate, cheap predictor plus mechanistic story. If they diverge, that divergence is the finding."*
- The standing sentence "a screen built on it is a proposal, not an instrument" either resolves or hardens into a permanent limit.

**5. CONCLUSION IF WE DO IT.**
- **If the correlation holds** (ρ ≥ 0.5 after removing the per-probe baseline): the coefficient is a usable pre-edit triage signal, a cut can be chosen, and the next card reports false-positive and false-negative rates at that cut. Only then is the word "screen" earned.
- **If it does not** (ρ near zero, or the interval spans zero): the coefficient is a delivery statistic with no behavioural meaning. The screen proposal is withdrawn with Natalie and Arnab in writing. Note what survives either way: the direct-exposure critique of RippleEdits falls back to **counting** whether the edited subject appears in the prompt, which needs no coefficient and is unaffected by this result.

**6. CONSEQUENCE OF NOT DOING IT.**
We would keep recommending a gate with no threshold and no error rates — an instruction with a verb and an object that nobody, including us, can carry out. Email 3's ask to Natalie cannot be answered by anyone until this number exists.

**Closed:** 2026-10-31 — **deny branch**, on the number written in field 5 before the run.

    overall, raw         rho = 0.522   95% CI (0.450, 0.587)
    overall, excess      rho = 0.085   95% CI (-0.003, 0.172)

The test was always the second line: movement in excess of what a **different edit on the same person** produces. It does not reach 0.5, and its interval touches zero. By the branch written in advance, the coefficient is not established as a predictor of a particular edit's effect, and a screen built on it stays a proposal.

What the raw number means, since 0.522 is real and will be quoted. A high-coefficient probe does move more. But the same-subject control already accounts for about **72%** of the median movement (|movement| 0.1034, |control| 0.0740), so what the coefficient tracks is *this probe is sensitive to an edit on this subject*, not *this edit reaches this probe*.

Per family, the excess medians are 0.000–0.031. `exposure` is the largest at 0.031 — the item where the edited subject sits in the prompt while the question is about someone else.

**What survives, as field 5 said it would.** The direct-exposure critique of RippleEdits rests on **counting** whether the edited subject appears in a prompt. That needs no coefficient and is untouched by this result.

**An unresolved tension, recorded rather than resolved.** The same-subject control was introduced in [E-013] to separate contraction from subject-keyed leakage. Here subject-keyed leakage may *be* the phenomenon: if an item moves because an edit happened to this subject rather than because of what the edit said, that is the direct-exposure claim, and controlling it away removes the signal. That reading is **post-hoc** and licenses nothing. It needs its own card with its branches written first.

---

## Closed cards

### C-001 · Does predicted reach predict measured movement? — DENIED

Closed 2026-10-31. `results/E-001-predicted-vs-measured.json`. 495 probes, 42 subjects, Llama-3.1-8B at layer 5, edits from the [E-014] cache. Anchor gate passed at 0.000e+00 after two faults were fixed ([E-001] in decisions.md).

Independent replication worth noting: the `anchor-floor` family — same prompt shape, different person — came back at a median coefficient of **0.0809**, against [E-018]'s floor of 0.082.
