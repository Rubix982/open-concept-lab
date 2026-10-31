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
