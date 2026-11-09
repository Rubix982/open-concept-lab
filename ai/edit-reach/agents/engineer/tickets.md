# engineer tickets

### E-001 · Predicted-vs-measured run for C-001

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-31
**Updated:** 2026-10-31
**Estimated:** 1 sitting to write, 1 NDIF session to run
**Spent:** 1 sitting — script and dry-run written, not yet run remotely

**Description:**

Produce the one number C-001 asks for: the rank correlation between an edit's **predicted reach** at a token, read from the unedited model, and the **measured movement** at that token after the edit is applied. Everything below is settled; a second engineer should not have to choose anything.

**Inputs, fixed.**

- Probe set: `probes/generated.json` — 491 items, 42 subjects, relation P19, seed 1538. Regenerate with `python -m probes.generate -n 42` if absent; the seed makes it identical. Do not hand-edit it.
- Model: `meta-llama/Llama-3.1-8B`, layer **5**, via NDIF. Layer 5 because every edit-slice number this will be compared against was read there, and `editreach.rome.LAYER` already defaults to it.
- Edits: **read from the [E-014] cache in edit-slice**, not computed. `results/cache/E014_kstar_L5_s1538.pt` and `E014_deltas_L5_s1538.pt` hold `k*` and `delta_v` for 42 subjects under two arms each, keyed `"<case_id>|real"` and `"<case_id>|ctl"`. `u = k*` (`C = I`), matching EasyEdit's shipped configs and therefore [E-013]–[E-015].
- **No `v*` is optimised, and this is forced.** [E-047]: `compute_v` cannot run remotely on nnsight 0.8.1, because NDIF refuses the gradient of any tensor the model consumed, at every depth. **That is read, not assumed** — the behaviour is documented in `nnsight/intervention/backward.py`'s own module docstring, and it reproduces in a two-arm script carrying no project code beyond the connection: `edit-slice/agents/engineer/workspace/nnsight081_backward_repro.py`. Arm 1 (a tensor the intervention block built) is served; arm 2 (module outputs at layers 31, 20 and 5) is refused with the same `OutOfOrderError` every time. The reproducer has not been sent to NDIF; that is Saif's call. The cache is the only set of edits that can be applied at all, so the 42 subjects are not a sample — they are the survivors. The probe set is anchored to those exact case ids with `--case-ids probes/e014_case_ids.json`; a free draw from the same relation under the same seed overlapped them by **2 of 42**.

**Procedure.**

1. **Preflight, and it is a stop condition.** Run `tools/dryruns/dryrun_generated.py probes/generated.json`; it must report 0 failures. Then read coefficients for the `anchor-prefix` items only. Every one must land in `(0.999, 1.001)`. If any does not, **abort and fix the pipeline** — those items are analytic, so a deviation is an implementation fault (padding, position, tokenisation, architecture path) and every other number in the run would be wrong in a way that looks plausible. Record the worst deviation either way.
2. **Predicted reach.** For every item, `coefficient_for(model, prompt, position, u=k_star, denom=float(k_star @ k_star), layer=5)`, with `position = rome.subject_last_index(tok, prompt, subject, occurrence=item.occurrence)`. **Pass the item's own `occurrence`** — the default is the first mention and the repetition family exists precisely because that is sometimes the wrong one. Far-field items are not in this set; `SubjectNotInPrompt` here means a generator bug.
3. **Measured movement.** For every item, score the pre-edit top-1 next token, teacher-forced, with `remote.score_pairs`, in three conditions:
   - `base` — no edit;
   - `real` — the subject's own edit;
   - `control` — a **same-subject** control edit, a different property of the same person (occupation) driven to comparable `norm_ratio`, per `agents/shared/decisions.md` [E-013]. The mandated different-subject control is already in the probe set as `anchor-floor` and is not re-run here.

   Movement is `logp(base) − logp(real)`, signed, and the control's movement is `logp(base) − logp(control)`.
4. **Correlate.** Spearman ρ between the coefficient and movement, with a bootstrap interval (10,000 resamples, seed 1538): overall, within each family, and **partial, with the same-subject control movement removed**. The partial one is the number C-001 turns on; the raw one will be inflated by generic subject-keyed instability.

**Why this movement metric, and what was deferred.** Teacher-forced log-probability of the pre-edit top-1 token: a scalar, computable with `score_pairs` as it stands, and directly comparable with [E-033] and [E-046]. KL over the full next-token distribution is the metric CLAUDE.md prefers and it is **deferred with a reason** — it needs vocabulary-wide logits off the wire, which `remote.py` deliberately avoids after an OOM at batch 400, so it is a change to the transport and not a change to this run. Note also that many items here (`alias-given`, `bystander`) have no meaningful correct answer, which is why the metric is anchored on the model's own pre-edit top-1 rather than on ground truth.

**Cost.** 42 subjects × (1 `k*`/`Wk*` read + 1 `v*` optimisation + 1 control `v*`) plus 3 scoring passes over 491 items, batched at `score_pairs`' default 200 rows. Round trips are the budget, not FLOPs. Log every retry; `logs.setup`, never `print`, and never pipe the run through `tail`.

**Outputs.**

- `results/E-001-predicted-vs-measured.json` — per item: id, family, regime, occurrence, coefficient, the three log-probs, movement, control movement. Plus a `meta` block with the probe-set seed, model, layer, step count, the anchor deviation from step 1, and the library versions.
- `agents/shared/decisions.md` — one entry, whichever way it comes out.
- `CARD.md` — close C-001 with the ρ and its interval, by the two branches already written in field 5.

**Done when** `results/E-001-predicted-vs-measured.json` exists, the anchor gate is recorded as passed, and C-001 is closed with a number rather than a description.

**Blockers:** none *for this ticket*, but it is shaped by one. [E-047] (edit-slice) blocks remote `v*` optimisation and is not resolved; E-001 routes around it by reading the cache rather than waiting. If NDIF answers and backward interleaving is fixed, the subject set stops being forced and this ticket should be re-run on a free sample, because 42 survivors is not a random 42.

**RCA:** —

**Artifacts:** `results/E-001-predicted-vs-measured.json`; `agents/engineer/workspace/run_e001.py`; `tools/dryruns/dryrun_e001.py`; `probes/generated.json`; `agents/shared/decisions.md` → "[E-001] Result: the coefficient predicts that a probe is edit-sensitive, not that an edit reaches it"; `CARD.md` → C-001, denied.

**Closed:** 2026-10-31. Anchor gate passed on all 42 anchor-prefix items, worst deviation exactly 0.0. Raw Spearman 0.522 (95% CI 0.450–0.587) over 495 items; with the same-subject control movement removed the excess falls to 0.085 (95% CI −0.003–0.172), an interval straddling zero. C-001 closed denied on its own pre-stated branches. *Status line corrected 2026-11-09: the work finished on 2026-10-31 and `plan.md` recorded it closed, but this ticket was never marked.*


**Progress, 2026-10-31.**

Written: `agents/engineer/workspace/run_e001.py` and `tools/dryruns/dryrun_e001.py` (36 checks, zero remote calls, all passing). The probe set is regenerated and anchored: `probes/generated.json`, 495 items over the 42 cached subjects, 1,213 structural checks passing.

Three faults were found before any remote call, which is what the dry-run is for:

1. **The probe set was drawn from the wrong subjects.** A free seed-1538 sample of relation P19 overlapped the cached subjects by 2 of 42. Found by comparing the two sets, not by running.
2. **A name is not an identifier.** `Claudio Coello` and `Nikolai Nissen Paus` each hold two CounterFact records, so resolving an owner's name back to a `case_id` silently returned one of them — and would have applied the wrong edit to two subjects without failing. Each item now carries its own `case_id`.
3. **The batched gather.** Replacing E-046's one-prompt-per-trace with right-padded batches of 200 takes 1,485 traces down to about nine, but moves the final real token from `-1` to `length - 1`. Reading `-1` would have scored the padding on every short row. Asserted in the dry-run.

Still untested: the three remote idioms — the batched coefficient read, the inline edit inside a batched trace, and the `probs[rows, want]` gather. The stand-in model exercises the arithmetic and the indexing; only NDIF exercises nnsight. **The anchor gate exists for exactly this** — run `--anchors-only` first, it is cheap, and 42 readings that must pin at 1.000 will catch all three if any is wrong.
---

### E-002 · Different-subject arm for C-002

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-31
**Updated:** 2026-11-08

> **Reconstructed 2026-11-08.** This ticket was never written at the time. The
> work ran, and its record is complete in `agents/shared/decisions.md` and
> `results/`, but the ticket that should have preceded it is missing — a real
> break of the no-work-without-a-ticket rule, repaired here rather than hidden.
> The description below is reconstructed from that record and is not evidence
> that the scope was stated in advance. What *was* stated in advance, and is
> load-bearing, is the pre-registered paired test; see the decision entry.

**Description:**
C-002 asks whether an edit's effect depends on what it said or only on whose key
it touched. Score the same 495 probes under a third arm: subject B's cached edit
applied while probing subject A, with B chosen as the nearest edit magnitude to
A's on `‖delta_v‖/‖k*‖`. Report paired median differences with a 10,000-sample
bootstrap, seed 1538.

Paired, not unpaired — the arms share their probes. The unpaired form overstates
the content effect roughly sixtyfold, which is the difference between a headline
and a footnote.

**Blockers:** none.

**Artifacts:**
- results/E-002-different-subject-arm.json
- results/E-002-summary.md
- agents/engineer/workspace/run_e002.py
- tools/dryruns/dryrun_e002.py (26 checks)
- agents/shared/decisions.md -> "[E-002] Result: movement is keyed on whose key
  the edit touched, not on what it said"

**Closed:** 2026-10-31. Identity is worth about 65x content (paired medians
+0.0583 against +0.0009, both excluding zero). C-002 closed on branch 1.

---

### E-003 · Destination readout: does the new answer land where the edit said?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-01
**Updated:** 2026-11-01
**Card:** C-003

**Description:**

[E-002] scored the 495-item probe set for **destruction** — the probability of the model's own pre-edit top-1 token, after the edit. This ticket scores the same items for **destination** — what the model says *instead* — and reports it per arm, so the two halves are measured on one probe set under one metric.

Concretely, for each arm in `real`, `ctl`, `other`:

1. Take the post-edit **top-1 token over the full vocabulary** at each prompt's final real token (`run_e001.top1_batch` with `edit=` set — it already returns `(token_id, probability)`; nothing new is needed on the wire).
2. Resolve that token to a country: a **hit** is a top-1 token that begins a city in that subject's injected `target_country`, read from `edit-slice/results/E-014-destination-meta-llama_Llama-3.1-8B.json`.
3. Report the hit rate overall and per family, against the destruction numbers already on disk for the same items.

The `base` arm is **not** re-run. [E-001] holds `base_token` and `p_base`; reading them again would buy an answer we have.

**Arms and where their edits come from.** Identical to [E-002], so the comparison is on the readout alone and nothing else: `real` and `ctl` from the [E-014] cache keyed `"<case_id>|real"` / `"<case_id>|ctl"`, `other` from the magnitude-matched donor pairing recorded in `results/E-002-different-subject-arm.json` under `pairing.pairs` — **read from that file, never recomputed**, or the two runs would be comparing different donors.

**The city map.** Built exactly as [E-014] built it, from `edit-slice/probes/geo.json` and `place_types.json`: settlements plus every target country's capital, minus `not_settlement`, with capitals folded in. 81 cities. First tokens are taken as `tokenizer.encode(" " + city)[0]`.

**Three things checked before writing this, recorded so they are not re-derived:**

1. **`ctl` is not *systematically* the weaker edit.** Signed paired median difference in `‖delta_v‖/‖k*‖` between `ctl` and `real` is +0.0899, `ctl` weaker in 20 of 42. The unsigned median is 0.7614 over a range of 2.627, so they are unbiased in direction but **not matched per subject**. A destination gap in the aggregate is therefore not a magnitude gap; a per-subject one would be unreadable, and is not claimed. Unlike the donor arm these two were never magnitude-matched, which is why this needed checking.
2. **First-token resolution is unambiguous.** 81 cities give 80 distinct first tokens and every one maps to exactly one country, so the token→country step adds no slack. Assert this in the dry-run rather than trusting it to stay true.
3. **A bare argmax-equals-target test is wrong here** and must not be written: the probes ask for a *city* and the edit injects a *country*.

**Known limit, to be carried into the write-up.** The `ctl` edit injects an occupation and these probes ask for a city, so there is no arm-symmetric "does each arm deliver *its own* target" check available. This measures whether content that *can* answer the question is what arrives — not that every edit delivers its own content somewhere.

**Gate.** The anchor gate runs first and unchanged (`--anchors-only`). 42 readings that must pin inside `ANCHOR_BAND`. It has caught two faults; it is not optional because this run reuses a pipeline that already passed once.

**Cost.** Three remote passes over 495 items, grouped by subject, batched at 200. Resumable per batch, same checkpoint discipline as [E-002].

**Outputs.**

- `results/E-003-destination.json` — per item: id, family, case_id, the three post-edit top-1 token ids and strings and probabilities, the hit flag per arm, and the destruction numbers joined from [E-001]/[E-002] so both halves sit in one file.
- `results/E-003-summary.md`.
- `agents/shared/decisions.md` — one entry, whichever way it comes out.
- `CARD.md` — close C-003 on one of the three branches in field 5.
- If branch 2 fires, the [E-013] scope note in `edit-slice/agents/shared/decisions.md` is struck by an appended correction, not edited.

**Done when** `results/E-003-destination.json` exists, the anchor gate is recorded as passed, and C-003 is closed with three rates rather than a description.

**Blockers:** none.

**RCA:** —**Artifacts:**

- `agents/engineer/workspace/run_e003.py`
- `tools/dryruns/dryrun_e003.py` — 81 checks, zero remote calls, all passing
- `results/E-003-destination.json`, `results/E-003-summary.md`
- `agents/shared/decisions.md` → [E-003]
- `CARD.md` → C-003 closed on branch 1
- `threads.md` → T-007 answered

**Artifacts:** `results/E-003-destination.json`; `results/E-003-summary.md`; `agents/engineer/workspace/run_e003.py`; `agents/shared/decisions.md` → the [E-003] entry; `CARD.md` → C-003. *Added 2026-11-09: this ticket was closed with its planned `**Outputs.**` recorded but no `**Artifacts:**` field at all, which is Discipline rule 1. Found by `tools/dryruns/dryrun_record.py` on its first run; every file above was checked to exist.*

**Closed:** 2026-11-01. Anchor gate passed at 0.000e+00 over 42 readings. Destination hit rates base 1% / real 29% / ctl 1% / other 1%; paired `real - ctl` +0.2828 (CI +0.2424, +0.3232) against destruction's +0.0009 on the same probes.

**What the dry-run and the pre-run checks caught, none of it by running:**

1. **T-007's own cost estimate was wrong in a way that would have produced a fake result.** It said "only the readout changes, from `probs[rows, want]` to an argmax". The probes ask for a *city*; the edit injects a *country*. A literal `top1 == target` test would have scored the real arm near zero, and a near-zero real arm reads as branch 3 — "these probes have no measurable destination at all" — which was a pre-written branch and would have been believed. Found by reading the probe set before writing the hit test.
2. **The pool-restricted readout was costed and rejected rather than attempted.** [E-014]'s criterion is 495 × 75 × 3 teacher-forced pairs, roughly eleven times [E-014]'s own run, which is not one session.
3. **`ctl` had never been magnitude-matched to `real`**, unlike the donor arm. Checked before the run: unbiased in direction, not matched per subject. The claim was narrowed to aggregate *before* the numbers existed, which is the only time narrowing is free.


---

### E-004 · The far-field floor, measured on the far-field prompts

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-01
**Updated:** 2026-11-01
**Card:** C-004
**Thread:** T-005

**Description:**

[E-039] (edit-slice, 2026-10-15) measured the near/far split on MQuAKE-CF-3k: coefficient 0.933 where a question names the edited subject, 0.055 where it does not, 513 single-edit two-hop instances, layer 5, no edit applied. Its floors came from **elsewhere** — 0.069 from a permuted `k*` on RippleEdits [E-038], 0.027 from a different token on MQuAKE. T-005 asked for the floor "on the same prompts", and that is what is missing.

This re-reads those 513 instances keeping the **key vectors** rather than the scalars, and scores every hop-2 question against all 512 other instances' `k*`, each with its own denominator. The floor becomes a distribution measured on the prompt itself.

**The selection is imported from `run_e039.usable`, not reimplemented.** The reproduction of 0.933 / 0.055 is this run's gate; a gate against a set rebuilt from a docstring would check my reading of the docstring.

**New package primitive.** `editreach.coefficient.keys_at` — raw key vectors at given positions, float32, one remote pass. `coefficient_for` answers "how much of *this* edit reaches these tokens"; scoring n prompts against n donors through it would cost n passes. This costs one, and the n² dot products are offline.

**Gate, stated before the run.** hop-1 natural within ±0.02 of 0.933 and hop-2 final within ±0.02 of 0.055. Outside that, branch 3 of C-004: something moved in the path every edit-slice number was read through, and nothing else in the card may be read. The gate additionally refuses to fire below 100 readings per arm — found by the smoke test, where n=3 produced a hop-2 median of 0.0772 and the gate fired on a sample too small to carry it. A gate that can fail for a reason unrelated to what it guards teaches you to ignore it.

**Controls.**

- The floor is a **distribution over 512 donors**, median per question, not one arbitrary pairing.
- Each donor uses **its own** `k*·k*`. Using the subject's denominator with a donor's numerator manufactures a floor out of a norm mismatch; the dry-run asserts the 1/‖k*‖ scaling that would break there.
- The benchmark property the card rests on is asserted, not assumed: **hop-1 questions name their subject 639 of 639 times, hop-2 questions 0 of 900.**
- **Delivery, not effect** [E-028d]. A floor result says this measure does not see far-field propagation at layer 5. It does not say an edit fails to reach the answer.

**Cost.** 513 remote traces, no edits and no gradients. Resumable per instance via a key cache.

**Outputs.**

- `results/E-004-far-field-floor.json`, `results/E-004-summary.md`
- `agents/shared/decisions.md` → one entry either way
- `CARD.md` → C-004 closed on one of its three branches; `threads.md` → T-005 answered

**Done when** the reproduction gate is recorded as passed and C-004 is closed with a paired excess over the same-prompt floor rather than a description.

**Blockers:** none.

**RCA:** —**Artifacts:**

- `agents/engineer/workspace/run_e004.py`
- `tools/dryruns/dryrun_e004.py` — 539 checks, zero remote calls, all passing
- `src/editreach/coefficient.py` → `keys_at`
- `results/E-004-far-field-floor.json`, `results/E-004-summary.md`
- `agents/shared/decisions.md` → [E-004]; `CARD.md` → C-004 branch 1; `threads.md` → T-005 answered

**Artifacts:** `results/E-004-far-field-floor.json`; `results/E-004-summary.md`; `results/cache/E004_keys.pt`; `agents/engineer/workspace/run_e004.py`; `agents/shared/decisions.md` → the [E-004] entry; `CARD.md` → C-004. *Added 2026-11-09, same omission as E-003 and found the same way. The cached keys are listed because [E-015] later ran entirely off them.*

**Closed:** 2026-11-01. Gate passed: hop-1 0.9334, hop-2 0.0544 against [E-039]'s 0.933 and 0.055. Far-field excess over a same-relation donor floor **+0.0002** (CI +0.0001, +0.0004) against the near field's +0.8439.

**What nearly shipped as the result.** Against all 512 donors the far-field excess is +0.0232 with an interval excluding zero, which is branch 2 — "far-field signal after all". The card did not list the confound: a hop-2 subject is the chain's middle entity, so topical overlap alone produces that excess, and since nearly every donor carries a different relation the all-donor floor *was* the different-relation floor. Found by asking what else a hop-2 subject is, not by anything in the measurement. The relation split was computed offline from the key cache at zero remote cost, which is the argument for `keys_at` saving vectors rather than scalars: [E-039] saved scalars and could not have run this control without re-buying 513 traces.

**Two faults in my own instruments, both caught before they mattered:**

1. **The dry-run's scaling assertion was wrong, the code was right.** It asserted that scaling a donor's `k*` leaves its coefficient unchanged. It does not — `(k·ck*)/((ck*)·(ck*))` is `1/c` times the original, which is correct and is exactly what breaks if a donor numerator is paired with the subject's denominator. The assertion now states the real property.
2. **The reproduction gate fired on a sample too small to carry it.** At n=3 the hop-2 median read 0.0772 against 0.055 and the gate failed — not a pipeline fault, a gate applied to three readings. `MIN_GATE_READINGS = 100` now refuses rather than passing or failing. A gate that can fail for a reason unrelated to what it guards teaches you to ignore it.


---

### E-005 · Loader parity: `LanguageModel` against `TransformersModel`

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-11-01
**Updated:** 2026-11-01
**Card:** C-005
**Thread:** T-006

**Description:**

nnsight 0.8.1 deprecates `LanguageModel`. Every number in this repo and in edit-slice, and every cached tensor on disk, was read through it. Compare the two loaders on module paths, raw activations at the edit layer's key site and at `lm_head`, and the two gate quantities — anchors pinning at 1.000 and the floor median reproducing [E-001]'s 0.0809.

`connect` gained a `loader=` keyword rather than being swapped, so the alternative is reachable by name and the default is unchanged for the 79 scripts that depend on it.

**Closed:** 2026-11-01. Branch 1: the loaders are the same instrument. Module paths identical; within-loader spread equals between-loader spread; gates hold under both. The switch is safe and was deliberately not taken — see the card.

**Artifacts:**

- `agents/engineer/workspace/run_e005.py`, `tools/dryruns/dryrun_e005.py` (27 checks)
- `src/editreach/remote.py` → `connect(loader=...)`, `LOADERS`
- `results/E-005-loader-parity.json`, `results/E-005-summary.md`
- `agents/shared/decisions.md` → [E-005]; `CARD.md` → C-005; `threads.md` → T-006 answered, **T-008 opened**

**RCA:** not a re-open, but the design was wrong twice before it was right, and both are worth keeping.

> **1. The gate measured something it was not asking about.** The anchor coefficient was computed against the **cached** `k*` rather than one read in the same trace, so it reported "anchors pinned False, worst 4.806e-03" under *both* loaders. That is the bf16 cached-`k*` effect [E-001] had already documented, not a loader difference. A false alarm sitting in a result file is worse than no gate.
>
> **2. The pre-stated pass criterion was unsatisfiable.** Field 5 asked for `torch.equal` bit-identity between loaders. Two readings through the *same* loader differ on 94% of elements, so no loader could ever have passed. The first run returned "branch 2 — do not switch", which was wrong and wrong in the direction that feels responsible. Fixed by varying the loader on its own: three readings each, within-spread against between-spread. The criterion was **not** relaxed to `allclose` — the dry-run forbids that call by name, because relaxing it is exactly how a re-baseline gets filed as an upgrade.

**Three faults in my own checks, caught by running them:**

1. A grep for `"allclose" not in src` **matched its own warning** in the docstring. Now greps for the call, `torch.allclose`.
2. A floor-probe check ended in `or True` and could not fail. A check that cannot fail is worse than no check, because it reports a pass. Replaced with three real ones.
3. A check for `worst_abs_difference` kept passing by name after the field was renamed in the repeat-design rewrite. Now checks both the magnitude and the extent fields.

**Blockers:** none.

---

### E-006 · Session variation: does it partition by the serving GPU?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-01
**Updated:** 2026-11-01
**Card:** C-006
**Thread:** T-008

**Description:**

[E-005] found readings of one batch differing between NDIF connections on 94% of elements, deterministic within a connection, two distinct values across six readings. Test the routing hypothesis with the metadata nnsight already exposes: `tracer.backend.meta` carries `max_mem_by_gpu`, keyed by GPU index. Read the same batch through 16 fresh connections; record a content hash of the raw keys, the device, the runtime, and two derived quantities.

**Closed:** 2026-11-01. Branch 1. Perfect partition — GPU 0 → one value ×8, GPU 2 → one value ×8. Floor median spread 0.000e+00 within a device, 3.110e-06 across. Anchors 0.000e+00 on all 16.

**The card's question was answered and was not the whole question.** Four floor medians now exist for the same probes across two days, range 2.16e-04, of which the device is 1.4%. Batch composition was tested: zero. Arithmetic location was tested: 5.06e-06 at the median, 2.98e-03 per item. Remainder unattributed → T-009.

**Design notes worth keeping:**

- **The hash is of the raw keys, never of a derived scalar.** The anchor coefficient reads `k` and `k*` in one trace, so the ratio cancels the whole effect; hashing it would have shown perfect stability and concluded nothing was wrong.
- **Two quantities, chosen for how they differ.** The anchor ratio is immune (same-trace), the floor is not (cached `k*`). A card owing a tolerance has to measure the one that does not cancel.
- **All three prompt groups ride in one trace**, so the tolerance arm cost no extra remote pass. Asserted in the dry-run by counting `keys_at(` calls.
- `keys_at` gained `meta_out: dict | None` — additive, no global state, and the dict is cleared before filling so a reused one cannot carry a previous device forward.

**Artifacts:**

- `agents/engineer/workspace/run_e006.py`, `tools/dryruns/dryrun_e006.py` (23 checks)
- `src/editreach/coefficient.py` → `keys_at(..., meta_out=)`
- `results/E-006-session-variation.json`, `results/E-006-summary.md`
- `agents/shared/decisions.md` → [E-006]; `CARD.md` → C-006; `threads.md` → T-008 answered, **T-009 opened**

**Blockers:** none.

### E-007 · NDIF reproducibility reference and conformance suite

**Status:** closed
**Type:** document
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** 1 sitting to draft, 1 short NDIF session to self-check
**Spent:** —

**Description:**
Turn what [E-001], [E-005] and [E-006] measured about the NDIF/nnsight
instrument into an artifact someone outside this project can use. Two
deliverables, both at edit-reach root.

1. `docs/ndif-reproducibility.md` — a reference stating each behaviour, the
   measurement behind it, and the consequence for anyone writing a gate. Every
   number in it must already exist in `agents/shared/decisions.md`; this ticket
   measures nothing new. Facts in scope:
   - a ratio read inside one trace is exact (0.000e+00 over 216 cells, four
     models); a cached `k*` costs up to 6.382e-03 ([E-001])
   - bf16 relative precision ~2**-8 over `d_mlp` channels is the whole budget
   - readings partition by serving GPU; floor-median spread 0.000e+00 within a
     GPU, 3.110e-06 across ([E-006])
   - total observed drift across four sessions 2.16e-04, of which the device is
     1.4%; the remainder is unattributed (T-009)
   - batch composition contributes zero (bit-identical)
   - where the dot product runs: 5.06e-06 at the median, 2.98e-03 per item
   - a trace body has no source on stdin (`WithBlockNotFoundError`); a local
     package referenced inside a trace body arrives as `ModuleNotFoundError`
   - `compute_v`/backward gradients refused on 0.8.1 ([E-047], edit-slice)

2. `tools/ndif_conformance.py` — a SINGLE standalone file that re-measures each
   of the above on the reader's own connection and prints, per check, the
   observed value against the documented one. It must not import `editreach`,
   so it can be copied out of this repo and run by anyone with an
   `NNSIGHT_API_KEY`. Verdict vocabulary is **matches reference / differs**, not
   pass/fail: the suite documents a deployment, it does not grade it.

**Scope boundary.** No new claim about knowledge editing. Nothing here depends
on a judgement about what the coefficient means. If a check cannot be stated as
"the documented number is X, yours is Y", it does not belong in this ticket.

**Blockers:** none. [E-047]'s reproducer is referenced by description only —
whether it is sent anywhere remains Saif's call and is not part of this ticket.

**Artifacts:**
- docs/ndif-reproducibility.md
- tools/ndif_conformance.py (standalone; imports nothing from editreach)
- tools/dryruns/dryrun_conformance.py
- results/E-007-conformance.json
- agents/shared/decisions.md -> "[E-007] Decision: raw activations are
  reproducible only within one batch shape"

**Closed:** 2026-11-03. The suite was run against the document it documents and
produced three corrections: the batch-composition claim was too broad (true of
ratios, false of raw keys, which move 4.297e-02); padding width had never been
measured and moves the same amount; and the arithmetic-site figure reproduces at
the median (5.319e-06 against 5.06e-06) but not per item, which is
sample-dependent. Two faults in the suite itself were found the same way and are
documented in its source rather than silently fixed. 11 remote traces, 57s.
9/9 dry-runs pass.

### E-008 · Does the conformance suite's picture hold on other models?

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** 1 sitting, ~35 remote traces
**Spent:** 1 sitting, 36 traces

**Description:**
[E-007]'s document and suite rest on one model, one architecture and one day.
Run the same suite unchanged on `meta-llama/Llama-3.1-70B` and
`EleutherAI/gpt-j-6b` and decide, per check, whether it states a property of
the INSTRUMENT or a property of the model. Anything model-specific must be
tagged with its model in both the document and the suite, or a correct
deployment running a different model will be reported as a difference.

**Pre-stated branches.**
- If the structural checks hold on all three: the document's claims generalise
  and the magnitudes get per-model tables.
- If a structural check fails on one: that claim is Llama-specific and the
  document says so in its own section, not in a footnote.

**Artifacts:**
- results/E-007-conformance-llama-3.1-8b.json, -70b.json, -gpt-j-6b.json
- tools/ndif_conformance.py -> `PER_MODEL`, `check_pad_content`, `check_served_dtype`
- docs/ndif-reproducibility.md -> "The second run, across three models"
- agents/shared/decisions.md -> "[E-008] Decision: the structure generalises,
  the magnitudes do not"

**Closed:** 2026-11-03. Structure held on all three across two architectures;
every magnitude was model-specific. One hypothesis in the document
("revisit if NDIF serves float32") turned out to be already true for GPT-J.

### E-009 · Does the serving-GPU partition reproduce at 16 connections?

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** ~32 traces
**Spent:** 32 traces, ~3 min

**Description:**
[E-006] saw a clean partition at 16 connections; [E-007] and [E-008] saw none
at 4, which is too few to distinguish "no partition" from "did not land on a
second device". Run `session_partition` at the same 16 connections [E-006]
used, on `Llama-3.1-8B`, and on a second small model to tell a deployment-wide
condition from a model-specific one.

**Pre-stated branches.**
- Partition reproduces: §2 stands as written and the device tolerance is
  justified.
- One device throughout: §2 is weakened to a property of a deployment on a day,
  and the fact that the device set CHANGED between 11-01 and 11-03 becomes an
  observed candidate for T-009's unattributed drift.

**Artifacts:**
- results/E-009-partition-8b.json, results/E-009-partition-gptj.json
- results/E-009-summary.md
- docs/ndif-reproducibility.md -> rewritten section 2, "The third run"
- tools/ndif_conformance.py -> `check_session_partition` degenerate-case guard
- agents/shared/decisions.md -> "[E-009] Decision: the GPU partition is a
  property of a deployment on a day"

**Closed:** 2026-11-03 on the second branch. 32/32 connections landed on GPU 0
across two models. The check's own `clean_partition = True` on that input was a
fault and is fixed.

### E-010 · Does the conformance picture hold away from layer 5?

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** ~90 traces
**Spent:** 90 traces, ~6 min

**Description:**
Every number in [E-007] through [E-009] was read at layer 5. Add a sweep mode
to `tools/ndif_conformance.py` taking `--layer 0,5,12,24,31`, with a FRESH
context per layer — the checks hand each other cached tensors, and comparing a
layer-5 tensor against a layer-24 reading would produce a large meaningless
difference. Run it on `Llama-3.1-8B` and `EleutherAI/gpt-j-6b` and decide, per
check, whether it states something about the instrument or about the depth.

Report `batch_width` RELATIVE to key magnitude as well as absolute: key
magnitude grows with depth, so an absolute figure cannot distinguish "the
effect grows" from "the keys grow".

**Pre-stated branches.**
- Structural checks read 0 at every layer: the document's claims are
  depth-independent and say so.
- Any structural check nonzero away from layer 5: that claim is layer-5
  specific and the document's scope shrinks to one layer.

**Artifacts:**
- results/E-010-layers-8b.json, results/E-010-layers-gptj.json
- results/E-010-summary.md
- tools/ndif_conformance.py -> `--layer` sweep, per-layer `Ctx`, matrix output
- docs/ndif-reproducibility.md -> "The fourth run: across depth"
- agents/shared/decisions.md -> "[E-010] Decision: the structure is
  depth-independent; the arithmetic-site effect is not, and only in bfloat16"

**Closed:** 2026-11-03 on the first branch. All three structural checks read
0.000e+00 at all ten layer-model pairs.

### E-011 · Sweep Llama-3.1-70B across depth

**Status:** closed
**Type:** review
**Priority:** medium
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** ~45 traces
**Spent:** 45 traces, ~4.5 min

**Description:**
[E-010] swept `Llama-3.1-8B` and `GPT-J-6B`. `Llama-3.1-70B` has 80 layers and
had been read at layer 5 only, so it is both the deepest model available and
the one with the least coverage. Run the same six checks at 0, 5, 20, 40, 79.

**Prediction recorded before the run:** adds a row, breaks nothing, because the
structure had already held on three models. Recorded so that it can be wrong.

**Pre-stated branches.**
- Structure holds: the claims reach fifteen layer-model pairs and the depth
  qualifier comes off for good.
- Structure fails anywhere: that claim is model- or depth-specific and the
  document's scope shrinks to where it was measured.

**Artifacts:**
- results/E-011-layers-70b.json, results/E-011-summary.md
- docs/ndif-reproducibility.md -> "The fifth run: the 70B refused the shape of
  the fourth", revised section 3
- agents/shared/decisions.md -> "[E-011] Decision: the arithmetic-site effect
  has no consistent direction in depth"

**Closed:** 2026-11-03 on the first branch for the structure, and the
prediction was **half wrong**: it broke a claim made one run earlier about the
arithmetic-site effect's direction in depth.

### E-012 · T-009's daily reading, and what the first one said

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** 1 sitting, 1 trace a day thereafter
**Spent:** 1 sitting, 1 trace

**Description:**
Build the falsifier T-009 has been carrying since [E-006]: one reading a day of
the same 42 floor probes, recording the device set and the median at FULL
precision, appended to a ledger that is never rewritten. Reuse [E-006]'s exact
code path so the values are comparable to the four already published.

The analyser must refuse to answer when the data cannot support an answer —
one device set, or too few days — rather than answering weakly.

**Artifacts:**
- agents/engineer/workspace/run_t009.py
- tools/dryruns/dryrun_t009.py
- results/T-009-ledger.md (committed), results/T-009-ledger.jsonl
- docs/ndif-reproducibility.md -> rewritten section 3
- agents/shared/decisions.md -> "[E-012] Decision: the drift is not drift"

**Closed:** 2026-11-03. The first reading answered most of T-009 on its own: it
came back bit-identical to [E-006]'s GPU 0 value from two days earlier.

### E-013 · 80% of the kept log record was content-free

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-03
**Updated:** 2026-11-03
**Estimated:** 1 sitting
**Spent:** 1 sitting

**Description:**
`logs.setup()` announces the run as its last act, and every run module calls it
at IMPORT. So importing a run module creates a log file containing one line
naming itself. The dry-runs import every run module, and five scripts import
`run_e001` as a library, so each dry-run pass left eight such files.

Measured before fixing: **124 of 155 committed log files** were header-only.
84 of them were E-001's.

Fix both halves — the header must be HELD until a real record arrives, and the
file handler opened with `delay=True`. Either alone does nothing: `delay=True`
is defeated by `setup()` immediately logging, and holding the header without
`delay=True` still creates an empty file.

Do not suppress the header. A log that does not say what ran is the fault
`logs.py` exists to prevent.

**Artifacts:**
- src/editreach/logs.py -> `_DeferredHeader`, `_DeferredFileHandler`,
  `_DeferredStreamHandler`; `EDITREACH_LOGS` path fix
- tools/dryruns/dryrun_logging.py (new)
- tools/dryruns/dryrun_e004.py -> sends its own logs to a temp directory
- 124 header-only log files removed (recoverable from git history)

**Closed:** 2026-11-03. 11/11 dry-runs pass and leave the project's log
directory unchanged; a real run still opens with its header and config.

---

### E-014 · Repair the E-002 record gap

**Status:** closed
**Type:** review
**Priority:** low
**Created:** 2026-11-08
**Updated:** 2026-11-08

**Description:**
Found while surveying the project for the documentation effort (`agents/documentor/tickets.md`): `decisions.md` carries two [E-002] entries and `results/` carries its artifacts, but this file has no E-002 ticket. Thirteen tickets exist in the record and twelve in the ledger.

Write the missing ticket in its place, marked plainly as reconstructed, so that a reader counting tickets against decisions finds them equal and finds the discrepancy explained rather than absent.

Do not back-date it and do not present the reconstructed description as a pre-registration. The scope stated in advance for E-002 was the paired test, and that lives in the decision entry.

**Blockers:** none.

**Artifacts:**
- agents/engineer/tickets.md -> E-002, reconstructed

**Closed:** 2026-11-08. E-001 through E-014 now present; every decision has a ticket.

### E-015 · The looseness of the Cauchy–Schwarz bound, per regime

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1 sitting. No NDIF, no edits, no gradients.

**Description:**

Close C-007 with two medians and their intervals. Everything below is settled; a second engineer should not have to choose anything.

**Why there is a bound at all.** ROME adds `δ · c(k)` at the edited layer, where `δ = v* − Wk*` is fixed and only `c(k) = (k*·k)/(k*·k*)` varies with the token. `c` is therefore a projection coefficient, and Cauchy–Schwarz bounds it: `|c(k)| ≤ ‖k‖/‖k*‖`, with equality exactly when `k ∥ k*`. `C = I` throughout this project, so the norms are Euclidean and no whitening enters. **This is analytic and must ship its derivation** in the decisions entry, not just its result.

**Input, fixed.** `results/cache/E004_keys.pt` — 513 instances written by `run_e004.py`, each carrying `case_id`, `hop`, `relation`, `names_subject` (one flag per question), `k_star` (d=14336, float32), `k_natural` (nq × d) and `k_final` (nq × d). Llama-3.1-8B, layer 5. Do not re-read from NDIF; this file is the input.

**Which key for which regime, and it matters.** `run_e004.py` lines 95–112: `k_natural` is read at the **subject's last token** when `names_subject[i]` is true, and at the final token otherwise. `k_final` is always the final token. So:

- **near field** — items where `names_subject[i]` is true, read at `k_natural[i]`
- **far field** — items where `names_subject[i]` is false, read at `k_final[i]`

Using `k_final` for the near field is the mistake available here: it silently measures the final-token coefficient and reports it as a subject-position one. The eight-item peek recorded on C-007 made exactly that slip and its numbers are not comparable to the near-field figures elsewhere.

**Procedure.**

1. **Gate, and it is a stop condition.** Recompute `c` for case 3's hop-2 questions and compare against the first entries of `per_question` in `results/E-004-far-field-floor.json`. They must agree to float32. Two are known: `0.06878352910280228` and `0.077170230448246`. If they do not agree, the cache and the published numbers disagree and **nothing else in this ticket is meaningful** — stop and report that instead.
2. Compute `c = (k*·k)/(k*·k*)` and `bound = ‖k‖/‖k*‖` in float64 for every question-position, carrying `case_id`, `hop`, `relation`, `names_subject`, and which key was used.
3. Looseness ratio `bound/|c|`. **Report how many items have `|c|` below 1e-6 and exclude them**, rather than letting a near-zero denominator manufacture an unbounded ratio — a far-field coefficient near zero is the expected case, not an anomaly, so this threshold is a reporting decision and must be stated with the result.
4. Median and IQR per regime, with a bootstrap interval (10,000 resamples, seed 1538). Also report the **maximum** ratio per regime: the median says whether the bound is typically useful, the maximum says whether it ever is not.
5. Sanity check that cannot be skipped: every item must satisfy `|c| ≤ bound`. A violation is an implementation error, not a finding.

**Outputs.**

- `results/E-015-bound-looseness.json` — per item, plus a `meta` block with the gate result, the excluded-item count, library versions and seed.
- `agents/shared/decisions.md` — one entry, whichever way it comes out, carrying the three-line derivation.
- `CARD.md` — close C-007 on the branch its field 5 already names.

**Done when** the two medians exist with intervals, the gate is recorded as passed, and C-007 is closed with numbers rather than a description.

**Blockers:** none. The input is on disk.

**RCA:** —

**Artifacts:** `results/E-015-bound-looseness.json`; `agents/engineer/workspace/run_e015.py`; `logs/run_e015-2026-11-09-223351.log`; `agents/shared/decisions.md` → "[E-015] Result: the upper bound is tight where the subject is named and vacuous where it is not"; `CARD.md` → C-007, branch 2.

**Closed:** 2026-11-09. Gate passed at 2.390e-08 against the published [E-004] values; all 1,539 items satisfy `|c| ≤ bound`; none dropped for a near-zero denominator. Near field median looseness 1.05, far field 21.12 (95% CI 20.16–22.14, max 1715.3).

One thing the ticket did not foresee, and it is the part worth keeping: the dry-run predicted the far-field bound would read ≈ 1 and forbid nothing. It reads 1.15 and forbids nothing — but the reason given was `E[‖k‖²_{C⁻¹}] = d`, which assumes `C` is the key second moment. `C = I` here, so that argument does not apply at all. Right number, wrong derivation. Recorded in [E-015] because the derivation is the half that would have generalised.

### E-016 · Prominence and dependent count against per-subject damage

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-11-09
**Updated:** 2026-11-09
**Estimated:** 1 sitting. One Wikidata call; everything else is on disk.

**Description:**

Close C-008 with two regression coefficients and their intervals. Everything below is settled.

**Inputs, fixed.**

- **Damage:** `results/E-001-predicted-vs-measured.json`, 495 probes over **42** subjects keyed by `owner`. Per subject, damage is the **median `excess`** — real movement minus same-subject control movement. Use `excess`, not `movement`: the control is what removes generic subject-keyed instability, and [E-002] showed that instability is 65× the content effect, so raw movement would measure the control's job rather than the subject's.
- **Dependent count:** `../edit-slice/data/wikidata/2026-09-20/snapshot.json.gz`, already cached. `labels` maps QID → label; invert it to find each subject. `claims[qid]` is the property → statements map; dependent count is **the number of distinct properties**, and the alternative — total statements across properties — must be computed and reported alongside, because they are different variables and nothing yet says which is meant. **41 of 42 subjects resolve by label; name the one that does not and carry n=41.**
- **Prominence:** the number of Wikipedia language editions for each QID, fetched once via `wbgetentities` with `props=sitelinks`. 41 ids in one call. **Persist the result** next to the snapshot so the run is repeatable without the network.

**Confounds, each with its control. None is optional.**

1. **Prominence and dependent count are not independent** — a well-documented person has more statements. Report their Spearman correlation first, and report each predictor's effect **partialled for the other**. If they correlate above 0.8 the partial coefficients are unstable at n=41 and the run must say so rather than present them.
2. **Headroom.** A subject the model knows well has a higher pre-edit probability and more room to fall. Carry per-subject median `p_base` and report the regression **with and without** it as a covariate. A prominence effect that vanishes under headroom control is a headroom effect wearing prominence's name.
3. **Uneven probe composition.** The six families are not equally represented per subject (210 position, 84 repetition, 80 alias, 42 exposure, 42 semantics, 37 discrimination). Report each subject's family counts, and recompute the medians over the **two families every subject has** as a sensitivity check. If the ranking changes between the two, report both and claim neither.

**Procedure.**

1. **Gate, and it is a stop condition.** Per-subject median `excess` over all 42 must reproduce [E-002]'s headline paired median of **+0.0583** for identity against **+0.0009** for content when aggregated as [E-002] aggregated it. If it does not, the two runs disagree about what `excess` means and nothing below is meaningful — stop and report that.
2. Build the per-subject table: label, QID, median excess, median `p_base`, distinct-property count, total-statement count, sitelink count, family counts, n probes.
3. Spearman for each predictor against median excess, with a bootstrap interval (10,000 resamples, seed 1538). Then partial Spearman, each controlling the other, and again controlling headroom.
4. Report **all** of it, including the branches that came out null. A single reported correlation out of six computed is a cherry-pick; the table is the deliverable.

**What this cannot show, and must be written into the summary.** n=41 subjects, one relation family, one model, one layer. Sitelink count is a proxy for corpus frequency, not a measurement of it — the falsifier in `edit-slice/threads.md` asks for corpus frequency and this is the closest thing obtainable without a corpus. Say so rather than letting a proxy pass as the quantity.

**Outputs.**

- `results/E-016-subject-properties.json` and `results/E-016-summary.md`
- `agents/shared/decisions.md` — one entry, whichever way it comes out
- `CARD.md` — close C-008 on one of the three branches in field 5
- `threads.md` — T-002 answered

**Done when** both coefficients exist with intervals, the gate is recorded, all three confound controls are reported, and C-008 is closed on a branch.

**Blockers:** none.

**RCA:** —

**Artifacts:** `results/E-016-subject-properties.json`; `results/E-016-summary.md`; `results/cache/E016_sitelinks.json`; `agents/engineer/workspace/run_e016.py`; `logs/run_e016-2026-11-09-230245.log`; `agents/shared/decisions.md` → the [E-016] entry; `CARD.md` → C-008, branch 3.

**Closed:** 2026-11-09. Branch 3: neither predictor moves. Prominence +0.005 (CI −0.315, +0.314), dependent count −0.053 (−0.366, +0.270); all three confound controls ran and changed nothing. n=41 — `Joey BadA$$` does not resolve by label and is named rather than dropped silently.

Two things the ticket did not foresee. **The gate was only half checkable:** [E-002]'s content figure reproduces exactly (median excess 0.0009 over 495 probes) but its identity figure is a different contrast this run does not recompute, so one of the two numbers was checked. Recorded rather than glossed. **And the detectable-effect floor is the result here**, not a footnote: at n=41 the widest interval spans 0.64, so an effect of 0.2 would have been invisible, and a null reported without that sentence would overclaim.
