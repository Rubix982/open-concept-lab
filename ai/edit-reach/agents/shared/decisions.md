# decisions

Owned by the engineer. Append-only; prior entries are never edited.

---

## [E-001] Decision: a coefficient must be read against a `k*` from its own trace

_Date: 2026-10-31_

**Decision:** When the question is whether the pipeline reads the right token, `k*` is read **live, in the same batch as the probe it is compared against**, and the dot product is taken in **float32**. A cached `k*` is correct for applying a cached edit and wrong for checking a reading.

**What forced it.** The anchor gate exists because 42 of the probes are analytic: a prompt beginning with the edited subject has `k = k*` under causal attention, so the coefficient is 1 by arithmetic, and any deviation is an implementation fault rather than a fact about the model. Run against cached `k*` in the activations' own dtype, it came back:

    42 items, worst deviation from 1.000 = 6.382e-03   (25 of 42 outside the band)

Run with `k*` read in the same trace and the arithmetic in float32:

    42 items, worst deviation from 1.000 = 0.000e+00   (gate passed)

**Rationale, both halves.**

1. **Dtype.** `u.to(kk.device, kk.dtype)` rounds a float32 `u` down to the activations' bf16 before a sum over 14336 channels. bf16's relative precision is about `2**-8 = 3.9e-03`, which is the order of the observed error and the entire budget for a quantity that has to read exactly 1.000.
2. **Provenance.** Activations arrive in bf16 and bf16 matmul is not deterministic across batch shapes, so a `k*` written in an earlier session carries that session's shape. [T-075] obtained `min = max = 1.000` across 216 cells precisely by reading `kstar = acts[0, idxs[0]]` from the same trace and doing the arithmetic on the CPU in float32. The construction was load-bearing and it was not obvious that it was.

**What this does not change.** The run itself still reads the cached `k*`, deliberately: the applied edit is the cached `delta_v`, which belongs to that `k*`, so the coefficient must describe the edit actually being applied. A ~1e-03 error there is negligible against a signal that ranges from a 0.082 floor to 1.000. The two uses are different questions and now use different code paths.

**Alternatives rejected:** widen the gate's band to admit 6.4e-03 — that is calibrating a gate to the bug it exists to catch, and the band would then no longer distinguish a dtype error from a genuine failure to pin. Drop the gate as pedantic — it caught two real faults on its first live run, at a cost of 42 traces.

**Revisit if:** NDIF serves activations in float32, at which point the dtype half of this is moot and only provenance remains.

**Artifacts:** `agents/engineer/workspace/run_e001.py` (`read_coefficients(..., edit_prompts=)`); `src/editreach/coefficient.py` (`reference=`); `tests/test_coefficient_runs.py` (three tests, one of which checks the gate can still fail); `logs/E-001-2026-10-31-*.log` — both runs, the failing one kept.

---

## [E-001] Result: the coefficient predicts that a probe is edit-sensitive, not that an edit reaches it

_Date: 2026-10-31_

**Result.** 495 probes over 42 subjects, Llama-3.1-8B, layer 5, edits read from the [E-014] cache.

    overall, raw      rho = 0.522   95% CI (0.450, 0.587)
    overall, excess   rho = 0.085   95% CI (-0.003, 0.172)

    family            n   coef med   move med    ctl med   excess med
    alias            80      0.121      0.007      0.002        0.001
    discrimination   37      0.096      0.022      0.011        0.003
    exposure         42      0.958      0.049      0.022        0.031
    position        210      0.958      0.090      0.066        0.001
    repetition       84      0.981      0.337      0.266        0.000
    semantics        42      0.980      0.180      0.177        0.000

**Decision:** The coefficient is **not** established as a predictor of a particular edit's effect. C-001 closes on the deny branch written before the run. A screen built on it remains a proposal, and the sentence "delivery is not effect" stays in force with a measurement behind it rather than as a caution.

**Rationale.** The raw correlation is real and will be quoted, so it needs its account: a high-coefficient probe does move more. But a **same-subject control edit** — a different property of the same person — already accounts for about 72% of the median movement (|movement| 0.1034, |control| 0.0740). Removing it leaves 0.085 with an interval touching zero. The quantity being predicted is therefore *this probe is sensitive to an edit on this subject*, not *this edit reaches this probe*. No family escapes it; excess medians run 0.000 to 0.031.

**What is unaffected.** The direct-exposure critique of RippleEdits rests on counting whether the edited subject appears in a prompt (and on MQuAKE's 6,861/6,861 against 0/16,506). That is arithmetic over prompt strings and needs no coefficient. Field 5 of C-001 said so in advance, which is the only reason it can be claimed now.

**A tension held, not resolved.** [E-013] introduced the same-subject control to separate contraction from subject-keyed leakage. In *this* question subject-keyed leakage may be the phenomenon rather than the confound: an item that moves because an edit happened to its subject, regardless of what the edit said, is the direct-exposure claim stated in movement rather than in prompt-counting. If so the same-subject control removes the signal. **This reading is post-hoc and licenses nothing.** It gets its own card with its branches written first, or it does not get used.

**Alternatives rejected:** report the raw 0.522 as the headline — it is the number the control exists to discount, and reporting it would reproduce exactly the error [E-013] was written to prevent. Widen the success threshold below 0.5 after seeing 0.085 — that is choosing the bar to clear.

**Threats to this result, stated rather than left for a reviewer.**

1. **The 42 subjects are survivors, not a sample.** [E-047] blocks remote `v*`, so these are the subjects whose edits were already cached. If NDIF's backward interleaving is fixed, re-run on a free draw before trusting the magnitude.
2. **Movement is `p(pre-edit top-1)`, not KL.** Chosen because it is a scalar computable with the existing transport and comparable with [E-033]/[E-046]; KL needs vocabulary-wide logits off the wire, which `remote.py` avoids after an OOM. A distributional metric could in principle separate what this one merges.
3. **The excess interval's lower bound is −0.003.** This is "cannot be distinguished from zero", not "is zero". A larger n could move it off zero without changing the conclusion that it is far below 0.5.

**Replication worth recording:** the `anchor-floor` family — same prompt shape, different person — returned a median coefficient of **0.0809** against [E-018]'s independently measured floor of **0.082**.

**Artifacts:** `results/E-001-predicted-vs-measured.json`; `agents/engineer/workspace/run_e001.py`; `tools/dryruns/dryrun_e001.py` (49 checks); `probes/generated.json`; `logs/E-001-2026-10-31-*.log`.

---

## [E-002] Result: movement is keyed on whose key the edit touched, not on what it said

_Date: 2026-10-31_

**Result.** The same 495 probes scored under a third arm — subject B's cached edit applied while probing subject A, B chosen as the nearest edit magnitude to A's. Paired median differences, bootstrap 10,000, seed 1538:

    real  -  same-subject      +0.0009   95% CI (+0.0004, +0.0024)
    same-subject - diff-subj   +0.0583   95% CI (+0.0472, +0.0732)
    real  -  diff-subject      +0.0842   95% CI (+0.0667, +0.0974)

    median movement by arm, per family
    family             real   same-subj   diff-subj
    ALL              0.0977      0.0625      0.0016
    alias            0.0065      0.0020      0.0001
    discrimination   0.0223      0.0114      0.0067
    exposure         0.0489      0.0217     -0.0005
    position         0.0900      0.0659      0.0037
    repetition       0.3373      0.2656     -0.0076
    semantics        0.1795      0.1767      0.0070

**Decision:** Changing *whose* key the edit touches is worth about **65 times** more than changing *what the edit says*. C-002 closes on branch 1. The reading recorded post-hoc in [E-001] is now established on a pre-stated test and may be used.

**Rationale.** A magnitude-matched edit on a different person produces a median movement of 0.0016 — within noise of nothing, and negative in two families. The same edit magnitude aimed at the probe's own subject produces 0.0625. The content of the edit adds 0.0009 on top of that. Both differences exclude zero, so this is not "content is irrelevant"; it is "content is detectable and roughly 1.5% of the effect of identity".

**A statistic that nearly misled, recorded for that reason.** Per-arm medians are 0.0977 / 0.0625 / 0.0016, which reads as `real` being 56% above the same-subject control. That is a difference of medians across skewed distributions. The arms share their probes, so the paired median of differences is the estimator that answers the question, and it is +0.0009. The unpaired form overstates the content effect by about sixtyfold. **Report paired quantities for paired designs** — the difference here is between a headline and a footnote.

**What this changes elsewhere.**

1. **`notes/email-3-direct-exposure.md` gains a second leg.** Its critique rested on counting whether the edited subject appears in a prompt. It can now also rest on behaviour: an item moves because an edit touched its subject, nearly independent of the edit's content, which is what "the item measures exposure rather than propagation" predicts.
2. **[E-013]'s same-subject control needs a scope note** in edit-slice. It was built to separate contraction from subject-keyed leakage. Where subject-keyed leakage is the phenomenon under study, it removes the signal, which is what produced [E-001]'s excess of 0.085.
3. **[E-001] stands unchanged.** The coefficient still fails to predict an edit's specific effect. It now has a reason: there is very little specific effect to predict.

**Threats, stated.**

1. **Magnitude matching is on `‖delta_v‖/‖k*‖`, one scalar.** Two edits of equal norm can still differ in direction relative to the probe's key. A directional control is the obvious next refinement and is not run here.
2. **Same 42 survivors as [E-001]** ([E-047]), so the magnitude generalises no further than that set.
3. **`semantics` shows real/ctl of 1.02** — content contributing essentially nothing there — while `alias` shows 3.34. Those are unpaired ratios and carry the caveat above; a per-family paired analysis is not done.

**Artifacts:** `results/E-002-different-subject-arm.json`; `results/E-002-summary.md`; `agents/engineer/workspace/run_e002.py`; `tools/dryruns/dryrun_e002.py` (26 checks); `logs/E-002-2026-10-31-*.log`.

---

## [E-002] Correction: the claim about [E-013]'s control was too broad

_Date: 2026-10-31_

The entry above said [E-013]'s same-subject control "removes the signal" for this class of question, and that the scope note belonged on [E-013]. Writing that note required reading [E-013] and [E-014] properly, and the broad form does not survive it.

[E-014] reports the same-subject control at **5%** against the real edit's **67%** on "does `inner_1` land in the target country". There the control is at floor and separates cleanly.

Both are right because they measure different halves. [E-002] measures **destruction** — what the pre-edit answer loses — which is subject-keyed. [E-014] measures **destination** — where the new answer goes — which is content-specific. The same-subject control is the wrong control for the first and the right one for the second.

So the correct statement is narrower: *for a destruction measure*, the same-subject control reproduces 98.5% of the effect and the different-subject arm is the one that separates. Nothing above licenses dropping it from a destination measure.

Recorded in edit-slice as **[E-013] Scope note**, appended rather than edited, since that surface is append-only.

## [E-003] Decision: destruction and destination are two separable effects of one rank-one update

_Date: 2026-11-01_

**Decision:** The two-route reading of T-007 is adopted as a measured result rather than a cross-experiment story. One ROME update **breaks** the pre-edit answer because it touched that subject's key, and **supplies** the new answer because of what it said. These are separable, and they were separated on one probe set under one metric.

**Rationale:** Measured on the same 495 probes and the same three arms as [E-002], changing only the readout (named-token probability → full-vocabulary argmax). Paired, bootstrap 10,000, seed 1538:

    destination   real - ctl    +0.2828   95% CI (+0.2424, +0.3232)
                  ctl  - other  +0.0000   95% CI (-0.0101, +0.0101)
    destruction   real - ctl    +0.0009   95% CI (+0.0004, +0.0024)
                  ctl  - other  +0.0583   95% CI (+0.0472, +0.0732)

The two halves separate in **opposite directions on the same probes**. Discordant pairs for destination, real against ctl: 142 to 2. The same-subject control lands in the injected country at 1%, which is the base rate, so it delivers nothing rather than a little.

**Alternatives rejected:** A pool-restricted teacher-forced readout, which is [E-014]'s and is directly comparable to its 67%/5% — rejected on cost: 495 × 75 × 3 scored pairs is not one NDIF session. A bare `top1 == injected country token` test — rejected as **wrong**, not merely coarse: the probes ask for a city and the edit injects a country, so it would have scored the real arm near zero and that zero would have looked like a result.

**What this does not establish.** The control edit injects an occupation and these probes ask for a city, so no arm-symmetric "does each arm deliver *its own* target" check exists here. The claim is that content which *can* answer the question is what arrives, not that every edit delivers its own content somewhere. Also aggregate only: `real` and `ctl` are unbiased in magnitude direction (weaker in 20 of 42) but not matched per subject (unsigned median difference 0.7614 over a range of 2.627), so no per-subject claim is made.

**Revisit if:** a readout that *can* express the control's own content shows it delivering there — which would turn "content-specific destination" into "each edit delivers its own content", a stronger claim this run cannot reach. Or if the restricted-pool readout, run on a subsample, puts the separation somewhere other than between the arms.

**Confirms rather than overturns:** the [E-013] scope note in `edit-slice/agents/shared/decisions.md` — destruction is subject-keyed, destination is not — which until now rested on reading [E-002] against [E-014] across two probe sets. It now rests on one.

## [E-004] Decision: the coefficient is a contamination detector, not a propagation detector

_Date: 2026-11-01_

**Decision:** The instrument's scope is narrowed, by us, in writing. The coefficient `(k·u)/(u·k*)` at layer 5 has **no subject-specific dynamic range in the far field** — prompts that never name the edited subject, which is where multi-hop propagation lives. It detects (a) that an edited subject is named in a prompt, and (b) the relation. It does not detect propagation.

**Rationale:** MQuAKE-CF-3k, 513 single-edit two-hop instances, no edit applied, every hop-2 question scored against all 512 other instances' `k*`:

    hop-2 far field (question never names the subject)    n=900
      own k*                        0.0543
      floor, SAME-relation donors   0.0481   excess +0.0002  CI (+0.0001, +0.0004)
      floor, DIFF-relation donors   0.0294   excess +0.0244  CI (+0.0215, +0.0271)

    hop-1 near field (question names it)                  n=639
      own k*                        0.9334
      floor, SAME-relation donors   0.0506   excess +0.8439  CI (+0.8379, +0.8500)

A stranger's edit on the same relation reaches a far-field question as much as the real subject's edit does, to within **+0.0002**. The same control barely touches the near field (+0.8439 of +0.8754). Reproduction gate: hop-1 0.9334 and hop-2 0.0544 against [E-039]'s 0.933 and 0.055, inside the ±0.02 stated before the run.

**The first floor would have given the opposite answer.** Against *all* donors the far-field excess is +0.0232 with an interval excluding zero, which reads as "there is far-field signal after all". Nearly all donors carry a different relation, so that floor is the different-relation floor under another name. The confound was found by asking what else a hop-2 subject is — the chain's middle entity, which the question is about indirectly — and not by anything in the measurement.

**Alternatives rejected:** A single magnitude-matched donor, as [E-002] used — rejected because one arbitrary pairing cannot be checked for the relation confound, and the confound is the result. A graded relation-similarity control — deferred; the split here is categorical and how *close* two relations are is not measured.

**What this does not establish.** Delivery, not effect ([E-028d], 2.96×). A floor result says this measure does not see far-field propagation at layer 5; it does not say an edit fails to reach the answer, because the layer-5 alteration travels onward through attention on a path this measure cannot see. Two-hop chains, single-edit instances, one model, one layer.

**Revisit if:** a graded relation-similarity control shows the +0.0002 moving with relation distance, or a layer sweep finds dynamic range in the far field at a depth other than 5.

**Supersedes nothing in [E-039], and completes it.** Its two convergent floors (0.069, 0.027) bracket the same-prompt all-donor floor of 0.0298, so that convergence was sound. Neither floor controlled for the relation, which is where the apparent far-field signal lived.

## [E-005] Decision: `LanguageModel` and `TransformersModel` are the same instrument; NDIF sessions are not

_Date: 2026-11-01_

**Decision:** The two nnsight loaders are interchangeable. `connect(loader=...)` is switchable and the **default stays `"language"`**; the switch is safe and is deliberately not taken here.

**Rationale:** Module paths identical (`llama`, 32 layers, `d_mlp` 14336, same `Envoy`). Three readings per loader over 84 prompts:

    comparison              pairs   worst |d|   max fraction differing
    WITHIN  language            3   6.250e-01        0.9394
    WITHIN  transformers        3   0.000e+00        0.0000
    BETWEEN the two             9   6.250e-01        0.9394

Two readings through the **same** loader differ as much as two through different ones, so the loader is not the variable. Gates hold under both across all six readings: anchors pin at exactly 1.000, floor median within 2e-4 of [E-001]'s 0.0809.

**Why the switch is not taken although it is safe:** it would change the loader every recorded number was read through on the same day the instrument was found to vary between sessions — two changes at once, one of them unmeasured. It is a one-line change whenever wanted.

**The pre-stated criterion was wrong and is recorded as such.** The card asked for `torch.equal` bit-identity. That is unsatisfiable on this platform. It was not relaxed to `allclose` — the dry-run forbids that call by name, because relaxing it is how a re-baseline gets filed as an upgrade. The criterion was replaced with a repeat design and the error recorded.

**Alternatives rejected:** one reading per loader, which is what the card originally specified — it cannot distinguish a loader difference from a session difference, and it returned "branch 2, do not switch" on evidence that does not support it.

**Revisit if:** nnsight removes `LanguageModel`, at which point the switch is forced and this entry says it is safe. Or if a surface other than the key site and `lm_head` is found to differ between loaders.

**Spawned T-008** — readings differ between NDIF serving sessions on byte-identical inputs, 94% of elements, up to 6.250e-01, deterministic within a session. [E-001]'s published floor of 0.0809 is a first-connection value; later connections give 0.081093.

## [E-006] Decision: NDIF readings partition by serving GPU; gates need a tolerance of 2.2e-04, not an equality

_Date: 2026-11-01_

**Decision:** The session variation [E-005] found is **routing**. Values partition cleanly by the serving GPU. No gate in this project may assert bit-identity across readings; cross-session comparisons of a cross-trace quantity use a tolerance of at least **2.2e-04**, and ratios read inside a single trace are preferred wherever the question allows, because they cancel the effect entirely.

**Rationale:** 16 readings of one 126-prompt batch through fresh connections:

    value               readings   served by
    edd2b2b152de2098           8   GPU 0
    54a1755349e607dc           8   GPU 2

Perfect partition in both directions. Floor median spread **0.000e+00 within a GPU**, **3.110e-06 across** them. Anchor coefficients read 1.000 with deviation 0.000e+00 on all 16 readings and both devices, because `k` and `k*` share a trace and the ratio cancels whatever the device does.

**The device is 1.4% of the drift, and this is the part worth carrying.** Four floor medians for the same 42 probes: 0.08087725 ([E-001], 10-31), 0.08094215 ([E-005] first reading), 0.08109000 (GPU 0), 0.08109313 (GPU 2). Observed range 2.16e-04 against a device spread of 3.11e-06.

Two further sources were tested rather than assumed:

- **Batch composition: zero.** Floors read alone and inside a 126-row batch, one connection, are bit-identical.
- **Where the dot product runs: 5.06e-06 at the median, 2.98e-03 per item.** `coefficient_for` multiplies inside the trace on the GPU; `keys_at` returns the keys and multiplies on the CPU over 14336 channels. Per-item coefficients move by up to 3e-3 between them; the median barely does, which is a property of the median and not of the arithmetic.

The remaining ~2e-04 is **not attributed**. Logged as T-009.

**Alternatives rejected:** recording the device on existing artifacts — rejected because it accounts for 1.4% of the observed drift and relabelling results by it would imply a precision we do not have. New runs capture it via `keys_at(..., meta_out=d)`.

**Revisit if:** a third serving device appears, or an artifact needs reproducibility tighter than 2.2e-04 — at which point the unattributed remainder has to be resolved first.

**What this retroactively explains.** Every anchor gate in edit-slice and edit-reach survived this without anyone knowing it existed, because the anchor ratio is read inside one trace. [E-004]'s ±0.02 reproduction gate sits comfortably above the 2.2e-04 drift and was right for a reason it did not state. [E-005]'s pre-stated `torch.equal` was unsatisfiable for this reason.
