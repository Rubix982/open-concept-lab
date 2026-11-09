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

## [E-007] Decision: raw activations are reproducible only within one batch shape; derived ratios are not affected

_Date: 2026-11-03_

**Decision:** The claim "batch composition contributes zero", recorded in [E-006] and generalised in the first draft of `docs/ndif-reproducibility.md`, is **narrowed**. It is true of the derived ratio and false of the raw keys. Any artifact comparing raw activations across runs is bounded at about **2.6% of their magnitude**, not at the 2.2e-04 of [E-006].

**Rationale.** Measured by `tools/ndif_conformance.py`, 8 anchor pairs at layer 5 of Llama-3.1-8B, one connection:

    16 rows -> 22 rows, padded width held at 14
      raw key values   max |difference|   4.297e-02   (2.59% of key magnitude)
      derived ratio    max |difference|   0.000e+00   (bit-identical)

    16 rows, width 14 -> 22, same content, padding only
      raw key values   max |difference|   4.297e-02   (2.59%)

The second arm is zero by the mathematics — padding appended after the text cannot reach a token to its left under causal attention — and is not zero in practice. That is bf16 matmul selecting a different kernel path for a different tensor shape. Both arms returned the identical maximum, which suggests one quantised step on one worst element rather than two independent effects; **not checked further, and recorded as unchecked.**

**How [E-006] came to say otherwise.** It did not. [E-006] measured *floor medians*, which are ratios, and found them bit-identical — which this reproduces. The over-generalisation to "batch composition contributes zero" happened when the result was written into a reference document, one step away from the measurement. The suite caught it on its first run against that document.

**What this strengthens.** The existing preference for a ratio read inside one trace was justified by [E-006] on a 3.11e-06 device effect. It is now justified by an effect four orders of magnitude larger, and the reason is different: not that the ratio averages noise away, but that the two keys share a shape and a trace, so whatever the kernel does it does to both.

**Two faults in the suite, found by running it and left documented in its source:**
1. A bf16 precision check measured the relative error of a dot product between near-orthogonal random vectors and read **4.9e-01**. That is catastrophic cancellation, not precision. Replaced with per-element rounding error, which reads 3.887e-03 against bf16's 2**-8 = 3.906e-03.
2. The arithmetic-site check was read on the **anchors**, whose ratio is analytically 1.000 under either arithmetic, so it read 0.000e+00 and would have reported "the two sites agree" permanently. Moved to non-pinned pairs; the median difference then reproduces [E-006]'s 5.06e-06 as **5.319e-06**.

Both are the same fault: a check evaluated on a quantity that cannot express the thing it was testing. `tools/dryruns/dryrun_conformance.py` asserts against the second by name.

**Alternatives rejected:** quietly correcting the document — a reference that was once wrong should say where, or a reader cannot calibrate the rest of it. Widening the suite's tolerances until everything matched — that is calibrating to the bug.

**Revisit if:** NDIF serves float32, or a kernel change makes the shape effect vanish; either would make the 2.6% bound obsolete rather than merely smaller.

**Not reproduced today:** four fresh connections all landed on GPU 0 and returned one signature, so [E-006]'s partition is consistent with this run and is not demonstrated by it. The documented partition took sixteen connections.

**Artifacts:** `docs/ndif-reproducibility.md`; `tools/ndif_conformance.py`; `tools/dryruns/dryrun_conformance.py`; `results/E-007-conformance.json`

## [E-008] Decision: the structure generalises, the magnitudes do not, and the shape effect is not bfloat16

_Date: 2026-11-03_

**Decision:** The claims in `docs/ndif-reproducibility.md` are split in two. The **structural** ones are stated as properties of the instrument and hold on every model tested. Every **magnitude** is tagged with the model it came from, and `tools/ndif_conformance.py` carries a `PER_MODEL` table so that a correct deployment running a different model is never reported as a difference.

**Rationale.** The suite was run unchanged on three models across two architectures, 36 remote traces:

    check              Llama-3.1-8B   Llama-3.1-70B     GPT-J-6B
    served dtype           bfloat16        bfloat16      float32
    ratio_in_trace        0.000e+00       0.000e+00    0.000e+00
    batch_rows (ratio)    0.000e+00       0.000e+00    0.000e+00
    pad_content           0.000e+00       0.000e+00    0.000e+00
    cached_reference      7.299e-03       6.211e-03    7.353e-03
    batch_width (raw)     4.297e-02       1.953e-03    5.292e-02
       as % of magnitude      2.59%           0.91%        0.92%
    matmul_site (median)  5.319e-06       4.969e-07    7.451e-09

Structure: identical. Magnitude: the arithmetic-site median spans three orders of magnitude, so the 5.06e-06 this project had been quoting is a Llama-3.1-8B fact and was never an NDIF fact.

**The shape effect is diagnosed, not merely measured.** `check_pad_content` fills the same-width pad region with a different token: the keys are **bit-identical** on all three models. So nothing is attending to the padding, causality behaves exactly as documented, and the width effect is kernel path selection. It also appears on **GPT-J, which NDIF serves in float32**, which rules out bfloat16 as its cause. Two readings that would have been equally consistent with the width measurement alone are now excluded by a control that cost two traces.

**An unexpected answer to our own open question.** [E-001] recorded "Revisit if: NDIF serves activations in float32". It does — for GPT-J. The dtype half of that entry does not apply to GPT-J work, and the provenance half still does.

**Alternatives rejected:** keeping one reference table and widening its tolerances until all three models matched — that would report agreement between quantities three orders of magnitude apart, which is worse than reporting nothing. Dropping `matmul_site` as unstable — it is perfectly stable *per model*, and the instability was in our bookkeeping.

**Revisit if:** a fourth model is added, or NDIF changes the dtype it serves for any of these three.

**Still not measured:** any layer other than 5, any batch wider than 22 rows, and the kernel diagnosis is an inference from the pad-content control rather than an observation of the kernel.

**Artifacts:** `tools/ndif_conformance.py`; `docs/ndif-reproducibility.md`; `results/E-007-conformance-*.json`; `results/E-008-summary.md`

## [E-009] Decision: the GPU partition is a property of a deployment on a day, not of the instrument

_Date: 2026-11-03_

**Decision:** Section 2 of `docs/ndif-reproducibility.md` is weakened. NDIF readings *can* partition by serving GPU; they did on 2026-11-01 and did not on 2026-11-03. No tolerance may be justified by the partition alone, and every run records how many distinct devices it saw rather than assuming more than one exists.

**Rationale.** 32 traces at the same 16 connections [E-006] used:

    Llama-3.1-8B    16/16  ->  one signature, GPU 0, spread 0.000e+00
    GPT-J-6B        16/16  ->  one signature, GPU 0, spread 0.000e+00

Not a weaker partition — no partition, because only one device was ever in play. Two models, so this is a condition of the deployment on the day rather than of one model.

**What the negative buys.** [E-006]'s partition was real: 8 readings on GPU 0 and 8 on GPU 2, clean in both directions. What it was not is standing. A reader who took §2 as a property of NDIF would have sized a tolerance against a device effect that, on 2026-11-03, does not exist — and would have had no reason to check.

**It promotes a T-009 candidate from guess to observation.** The device set serving `Llama-3.1-8B` changed between 11-01 (GPUs 0 and 2) and 11-03 (GPU 0 alone). That is a deployment change, observed, sitting between exactly the sessions whose floor medians differ by the unattributed ~2e-04. **This is not a measurement of the drift** — nothing yet shows the two move together — but "the deployment changed between days" is now a thing that demonstrably happens rather than a thing we supposed.

**A fault in the check, the third of its kind in this suite.** `check_session_partition` returned `clean_partition = True` for sixteen identical readings off one GPU, because "one device per signature" and "one signature per device" are both vacuously true when there is one of each. It now requires at least two of each and otherwise reports `n/a - nothing to partition`. The other two were a precision check measuring cancellation and an arithmetic-site check read on an analytically pinned quantity. All three are the same fault: **a check evaluated on an input that cannot express the thing it tests**, and all three were fixed by naming the degenerate case rather than by moving a number.

**Alternatives rejected:** reporting the single-device run as a match for [E-006] — it is neither a match nor a mismatch, it is a different population. Repeating until a second device appeared — that is sampling until the expected answer arrives, and the date would have been unrecoverable from the result.

**Revisit if:** a run sees two or more devices again, at which point the partition can be tested rather than merely observed.

**Artifacts:** `results/E-009-partition-8b.json`; `results/E-009-partition-gptj.json`; `results/E-009-summary.md`; `docs/ndif-reproducibility.md`; `tools/ndif_conformance.py`

## [E-010] Decision: the structure is depth-independent; the arithmetic-site effect is not, and only in bfloat16

_Date: 2026-11-03_

**Decision:** The structural claims in `docs/ndif-reproducibility.md` are stated without a layer qualifier. The batch-shape bound is stated **relative to key magnitude** and as one number for the whole model. The arithmetic-site figure is stated as growing with depth **in bfloat16 only**.

**Rationale.** 90 traces, five layers on each of two models, six checks each:

    Llama-3.1-8B          L0        L5       L12       L24       L31
    ratio_in_trace   0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
    batch_rows       0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
    pad_content      0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
    batch_width abs  3.91e-03  4.30e-02  1.95e-02  4.69e-02  2.66e-01
      key magnitude      0.75      1.66      1.06      3.41     19.75
      AS % OF MAG       0.52%     2.59%     1.84%     1.38%     1.34%
    matmul_site      8.41e-07  5.32e-06  1.63e-05  2.66e-05  3.68e-05

    GPT-J-6B (float32)    L0        L5       L12       L20       L27
    batch_width % mag    0.00%     0.92%     1.32%     1.27%     0.91%
    matmul_site      1.49e-08  7.45e-09  7.45e-09  1.86e-09  7.45e-09

**The absolute growth was an artefact of the keys, not of the effect.** `batch_width` rises 68-fold from layer 0 to layer 31 while key magnitude rises 26-fold. Relative, it is flat and under 3% everywhere, on both architectures. Had the sweep reported only the absolute figure it would have supported "the shape effect gets much worse with depth", which is false and would have been believed.

**The depth dependence that is real belongs to bfloat16.** The arithmetic-site median grows 44-fold over 31 layers on the 8B and does not move on GPT-J, which NDIF serves in float32 — 1.49e-08 to 7.45e-09 across five layers, float32 epsilon throughout. So it is accumulation error compounding with depth, not a property of depth.

**An internal consistency check, unplanned.** On GPT-J, `cached_reference` reads 0.000e+00 at exactly the layers where `batch_width` does (L0, L20). Caching costs nothing where shape costs nothing, because they are the same effect observed twice. Nothing in the suite enforces this; it fell out.

**Alternatives rejected:** sweeping one model only — [E-008] established that a one-model result here is a model result, and the bfloat16/float32 split is only visible with both. Reporting `batch_width` absolute, as the suite did until this run — it cannot distinguish a growing effect from growing keys, which is the whole question.

**Design note.** The sweep builds a **fresh `Ctx` per layer**. The checks hand each other cached tensors (`alone_keys`, `cached_reference`); a layer-5 tensor compared against a layer-24 reading gives a large, meaningless difference. Same fault class as the three already found in this suite, caught in advance this once.

**Revisit if:** a model is served in a dtype other than bfloat16 or float32, or a layer beyond 31 is read on a deeper model. `Llama-3.1-70B` has 80 layers and was swept at none of them.

**Artifacts:** `results/E-010-layers-8b.json`; `results/E-010-layers-gptj.json`; `results/E-010-summary.md`; `tools/ndif_conformance.py`; `docs/ndif-reproducibility.md`

## [E-011] Decision: the arithmetic-site effect has no consistent direction in depth, and [E-010]'s wording is withdrawn

_Date: 2026-11-03_

**Decision:** [E-010]'s sentence "the arithmetic-site median grows with depth in bfloat16" is **withdrawn**. What is supported is that in bfloat16 it spans two to three orders of magnitude across depth with no predictable direction, and in float32 it does not move. The instruction that follows changes from "be careful when reading deep" to "measure it at the layer you read".

**Rationale.** `Llama-3.1-70B` at layers 0, 5, 20, 40, 79, 45 traces:

    model          L0        L5   L20/L12   L40/L24   L79/L31/L27
    8B  (bf16) 8.41e-07  5.32e-06  1.63e-05  2.66e-05      3.68e-05
    70B (bf16) 4.84e-06  4.97e-07  9.13e-08  2.72e-05      1.65e-05
    GPTJ(fp32) 1.49e-08  7.45e-09  7.45e-09  1.86e-09      7.45e-09

The 8B rises monotonically, 44-fold. The 70B **falls 53-fold to layer 20 and then rises 298-fold to layer 40**. [E-010] read the direction off one model, which is the same fault [E-008] fixed for magnitudes and [E-009] for routing, now in its third costume.

**What did hold, and now holds firmly.** All three structural checks read 0.000e+00 at every one of **fifteen layer-model pairs**, across two architectures, three model sizes and depths 0 to 79. The batch-shape bound held at 0.38%-1.54% on the 70B, inside the sub-3% band, with its 448-fold absolute rise over 79 layers fully accounted for by keys growing 113-fold — the same decomposition [E-010] found on the 8B, now confirmed on a model with 2.5x the depth.

**A prediction recorded before the run and found half wrong.** The ticket said the sweep would "add a row and break nothing". It did not break the structure and it did break a claim one run old. Recorded because a prediction that is never written down can never be wrong, and this one was useful precisely by being wrong.

**Alternatives rejected:** sampling more layers until the 70B looked monotone — that is sampling until the expected answer arrives. Calling the 70B anomalous — two models disagree and there is no third bfloat16 model to break the tie, so neither is the anomaly.

**Revisit if:** a third bfloat16 model is swept, or anyone samples densely enough to describe the shape between layers rather than at five points on it.

**Artifacts:** `results/E-011-layers-70b.json`; `results/E-011-summary.md`; `docs/ndif-reproducibility.md`

## [E-012] Decision: the 2.16e-04 is not drift; it is four discrete replica values, each exact

_Date: 2026-11-03_

**Decision:** T-009's "unattributed remainder" is withdrawn as a description. The quantity does not drift. It takes one of a small number of **exact** values, reproducing bit-for-bit across runs, across nnsight loaders and across days, and which one you get is routing. A comparison between **device-matched** readings needs **no tolerance at all**. The 2.2e-04 from [E-006] is retained only for comparing readings whose devices differ or were never recorded — which is every artifact this project made before 2026-11-01.

**Rationale.** The first daily reading, taken 2026-11-03, returned content hash `edd2b2b152de2098` and floor median `0.08109002151514136` — the **same hash and the same bits** as [E-006]'s eight GPU 0 readings on 2026-11-01. A census over every reading of this quantity ever recorded:

    value                    readings   GPUs          days
    0.08087725                      1   unrecorded    10-31
    0.08094214687103357             1   unrecorded    11-01
    0.08109002151514136             9   0             11-01, 11-03
    0.08109313181234508            13   2             11-01

    4 distinct values over 24 readings
    spread WITHIN a device set        0.000e+00
    spread ACROSS everything          2.159e-04

Thirteen readings return `0.08109313181234508` to the last bit, across **two different nnsight loaders** and two separate experiments. That is not a distribution with a width. It is a small set of fingerprints.

**What this corrects, and the shape of the error.** [E-006] reported a device spread of 3.11e-06 and called the rest unattributed. Both halves were artefacts of sampling: its 16 connections happened to reach two replicas, so 3.11e-06 is the distance between **those two**, and the "unattributed" residue is simply the other replicas it did not reach. The error was reporting a **spread** for a quantity that is **discrete** — a summary of the wrong shape, which made a four-point set look like a noisy measurement.

**A second error, in the ledger's own first draft, which nearly hid this.** `HISTORY` was seeded with the 8-decimal figures that had been quoted in prose. Against those, today's reading looked 2.15e-08 away from [E-006]'s GPU 0; against the full-precision values it is exactly equal. **A ledger built to detect bit-identity cannot be seeded with rounded numbers.** `dryrun_t009.py` now fails any history entry carrying fewer than eight decimals without a written note saying why.

**What remains open, and it is narrower than T-009 was opened for.** Not *what causes the drift* — there is no drift — but *how many replicas exist*. Two of the four values predate the habit of recording the device and **cannot be attributed now**; that information is gone. The practical rule does not depend on recovering it.

**Alternatives rejected:** keeping "unattributed drift" and widening tolerances — it describes the wrong shape and would have had us tolerate 2.2e-04 on comparisons that are exact. Declaring the replica count to be four — four is the number of values **seen**, and [E-009] showed the reachable set changes between days.

**Revisit if:** a device-matched pair of readings ever differs. That single observation would restore a time component and reopen T-009 as originally framed.

**Artifacts:** `agents/engineer/workspace/run_t009.py`; `tools/dryruns/dryrun_t009.py`; `results/T-009-ledger.md`; `docs/ndif-reproducibility.md`

## [E-013] Decision: the run header is held until a real record arrives

_Date: 2026-11-03_

**Decision:** `logs.setup()` no longer writes anything. It holds the run header, and the config line when given, and emits them immediately before the first real record. The file handler is opened with `delay=True`. Importing a module that calls `setup()` now costs nothing on disk; running it still produces a self-describing log.

**What was measured first.** 124 of 155 committed log files in this project were a single line naming themselves and nothing else — **80% of the kept record was content-free**. By run name: E-001 84, E-005 13, E-002/E-003/E-006 9 each. By date: 10 on 10-31, 43 on 11-01, 71 on 11-03. The files were removed; they remain in git history.

**Why E-001 dominates.** Five run scripts import `run_e001` as a library for its loaders, and `run_e001` calls `setup()` at module scope. So every dry-run pass, and every run of five other scripts, created an E-001 log recording nothing.

**Both halves of the fix are required.** `delay=True` alone is defeated by `setup()` logging a line immediately. Holding the header alone still leaves `FileHandler` creating an empty file at construction. Neither is sufficient and that is why the obvious single fix would not have worked.

**The header is deferred, not dropped.** `logs.py` exists because a run whose parameters are not in its log cannot be interpreted later. Suppressing the announcement to stop the noise would have traded one blindness for another.

**A second bug, found by the dry-run written for the first.** `setup()` called `path.relative_to(ROOT)` to display the log path, which **raises** when the path is outside the project — so setting `EDITREACH_LOGS`, a documented feature, crashed `setup()` itself. Nobody had used it. Now falls back to the absolute path.

**A third fault, in the dry-run's own first assertion.** It redirected the log directory to a temp dir and asserted the temp dir was empty, which conflates *writes no log at all* with *does not write into the repository*. Only the second is the rule: `dryrun_e004` legitimately exercises logging code and sends its output to a temp directory of its own. The check now runs the dry-runs with `EDITREACH_LOGS` unset, as a person would, and asserts the **project's** log directory is unchanged.

**Alternatives rejected:** gitignoring `logs/` — the record is kept on purpose. Deleting stubs periodically — treats the symptom and leaves the next reader counting noise. Moving `setup()` into each `main()` — correct but touches six scripts and does not stop the next one from repeating it.

**Revisit if:** a run is ever found to have produced no log because it crashed before its first record. That is now indistinguishable from never having been started, which is the one thing this trade gives up.

**Artifacts:** `src/editreach/logs.py`; `tools/dryruns/dryrun_logging.py`; `tools/dryruns/dryrun_e004.py`

## [E-015] Result: the upper bound is tight where the subject is named and vacuous where it is not

_Date: 2026-11-09 · Llama-3.1-8B, layer 5, 513 instances, 1,539 question-positions · offline over `results/cache/E004_keys.pt`, no NDIF · closes C-007 on branch 2_

**The bound, and its derivation.** ROME adds `δ · c(k)` at the edited layer, where `δ = v* − Wk*` is fixed and only `c(k) = (k*·k)/(k*·k*)` varies with the token. So `c` is the projection coefficient of `k` onto `k*`, and Cauchy–Schwarz gives, for every prompt, with no enumeration and no forward pass through the edited model:

    |c(k)| ≤ ‖k‖ / ‖k*‖,   with equality exactly when k ∥ k*.

`C = I` throughout this project, so the norms are Euclidean and no whitening enters. **This is analytic.** It is refuted by an error in the three lines above, or by its premise — that the update is rank-one with a fixed direction — failing. It is not refuted by any measurement.

**What was measured** is whether the bound is *informative*, which is a different question and an empirical one. Looseness is `bound/|c|`; a bound never approached forbids nothing.

| regime | n | median &#124;c&#124; | median bound | median looseness | 95% CI | IQR | max |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| near field (question names the subject, read at its last token) | 639 | 0.9334 | 0.9881 | **1.05** | 1.05–1.06 | 1.04–1.09 | 10.6 |
| far field (question never names it, read at the final token) | 900 | 0.0544 | 1.1456 | **21.12** | 20.16–22.14 | 16.11–32.75 | 1715.3 |

Gate passed: 16 hop-2 coefficients recomputed from the cache against the published `E-004` values, worst deviation **2.390e-08**. All 1,539 items satisfy `|c| ≤ bound`; none was dropped for a near-zero denominator.

**Decision: the bound is real, and it is useless in the regime anyone cares about.** State it that way rather than reporting that an upper bound exists.

The number that carries this is **the far field's median bound of 1.1456**. The far-field coefficient is 0.054, and the bound permits 1.15 — which is more than the *near* field actually receives. So the bound cannot distinguish a token that never names the edited subject from one that is the edited subject. It forbids nothing that happens.

**The near field's 1.05 is not a second finding.** In the near field `k ≈ k*`, which is the same prefix-sharing that pins the anchor coefficient at exactly 1.000 — so Cauchy–Schwarz is near-equality by construction there. Reporting "tight in the near field" as a positive result would be reporting the anchor result a second time under a new name. It is recorded because it confirms the implementation, not because it is news.

**A prediction that came out right for the wrong reason, recorded because the distinction is the point.** The dry-run on T-001 predicted the far-field bound would read ≈ 1 and therefore forbid nothing. It reads 1.15 and forbids nothing. But the *reason* given was `E[‖k‖²_{C⁻¹}] = tr(C⁻¹C) = d`, which assumes `C` is the key second moment. `C = I` here, so that argument does not apply. The observed ≈ 1 comes from keys having comparable Euclidean norms, which is a different fact. Right number, wrong derivation, and the derivation is what would have generalised.

**Alternatives rejected.** Reporting the mean looseness — the far-field maximum is 1715, so a mean describes the tail rather than the typical case. Excluding small `|c|` — none fell below 1e-6, and a far-field coefficient near zero is the expected case rather than an anomaly, so excluding it would have removed the evidence.

**Revisit if:** the covariance is ever something other than the identity. The bound's form is unchanged but `‖k‖_{C⁻¹}` is a different quantity, and whitening is exactly the operation that could make the far-field bound small. [E-016] in edit-slice found whitening a near-no-op by cosine and a 50x change in targeting, so this is not idle.

**What this does not show.** Nothing about behaviour. The bound is on `‖Δh‖` at one layer; crossing to logits needs a Lipschitz constant for the rest of the network, which is T-011 and is unread.

**Artifacts:** `results/E-015-bound-looseness.json`; `agents/engineer/workspace/run_e015.py`; `logs/run_e015-2026-11-09-223351.log`

## [E-016] Result: neither prominence nor dependent count predicts how hard an edit hits

_Date: 2026-11-09 · 41 subjects, 495 probes, Llama-3.1-8B layer 5 · closes C-008 on branch 3, answers T-002_

**Decision: report a null with its detectable-effect floor, and make the published absence-sentence specific rather than general.**

Per-subject damage is the median `excess` (real minus same-subject control movement). Against it, Spearman with 10,000-resample bootstrap intervals, seed 1538:

| relationship | ρ | 95% CI |
| --- | ---: | --- |
| prominence (Wikipedia language editions) | **+0.005** | −0.315, +0.314 |
| dependent count (distinct Wikidata properties) | **−0.053** | −0.366, +0.270 |
| total statements | −0.055 | −0.370, +0.259 |
| headroom (`p_base`) | −0.130 | −0.399, +0.171 |
| prominence, partialled for dependent count | +0.059 | −0.228, +0.336 |
| dependent count, partialled for prominence | −0.079 | −0.355, +0.211 |
| prominence, partialled for both | +0.038 | −0.266, +0.327 |
| dependent count, partialled for both | −0.047 | −0.340, +0.264 |

All eight reported; six were computed and reporting a subset would be a cherry-pick. Confound controls all ran and all came back clean: the two predictors correlate at ρ = 0.701 (below the 0.8 line set in advance, so the partials are stable); controlling headroom moves prominence from +0.059 to +0.038; and over the four families every subject shares, prominence reads +0.015 and dependent count −0.039.

**Rationale for the branch.** Field 5 named three outcomes in advance and this is the third. Nothing here is a surprise reading of a borderline number — the point estimates are within 0.13 of zero and no interval excludes it.

**The limit, stated with the result rather than after it.** At n = 41 the widest interval spans 0.64, so this excludes a monotone relationship of about **|ρ| > 0.37** and nothing smaller. **No evidence of an effect; not evidence of no effect.** An effect of 0.2 would be invisible to this study.

**Alternatives rejected.** Raw `movement` instead of `excess` — [E-002] put generic subject-keyed instability at 65× the content effect, so raw movement would have measured the control's job. Reporting only the headline pair — six correlations were computed. Dropping `Joey BadA$$` silently — it does not resolve by label against the cached snapshot and is named in the output.

**Prominence is a proxy and is labelled as one.** T-002's falsifier asks for corpus frequency of the subject string; Wikipedia language-edition count measures documentation, not textual frequency. Its range is 0 to 67 so it is not degenerate, but it is not the named quantity.

**Half a gate, recorded as such.** The ticket asked for [E-002]'s paired medians, +0.0583 identity against +0.0009 content. The content figure reproduces exactly (median excess 0.0009 over 495 probes); the identity figure is a different contrast this run does not recompute. One of two numbers checked. A gate that checks half of what it claims is the fault already paid for three times here.

**Revisit if:** a corpus frequency source becomes available, or n grows past ~150 subjects, where |ρ| ≈ 0.2 becomes detectable. [E-047] in edit-slice is what holds n at 42.

**Artifacts:** `results/E-016-subject-properties.json`; `results/E-016-summary.md`; `results/cache/E016_sitelinks.json`; `agents/engineer/workspace/run_e016.py`; `logs/run_e016-2026-11-09-230245.log`
