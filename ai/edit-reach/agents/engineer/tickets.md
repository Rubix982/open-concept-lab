# engineer tickets

### E-001 · Predicted-vs-measured run for C-001

**Status:** open
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

**Artifacts:** — (fill on close)

**Closed:** —


**Progress, 2026-10-31.**

Written: `agents/engineer/workspace/run_e001.py` and `tools/dryruns/dryrun_e001.py` (36 checks, zero remote calls, all passing). The probe set is regenerated and anchored: `probes/generated.json`, 495 items over the 42 cached subjects, 1,213 structural checks passing.

Three faults were found before any remote call, which is what the dry-run is for:

1. **The probe set was drawn from the wrong subjects.** A free seed-1538 sample of relation P19 overlapped the cached subjects by 2 of 42. Found by comparing the two sets, not by running.
2. **A name is not an identifier.** `Claudio Coello` and `Nikolai Nissen Paus` each hold two CounterFact records, so resolving an owner's name back to a `case_id` silently returned one of them — and would have applied the wrong edit to two subjects without failing. Each item now carries its own `case_id`.
3. **The batched gather.** Replacing E-046's one-prompt-per-trace with right-padded batches of 200 takes 1,485 traces down to about nine, but moves the final real token from `-1` to `length - 1`. Reading `-1` would have scored the padding on every short row. Asserted in the dry-run.

Still untested: the three remote idioms — the batched coefficient read, the inline edit inside a batched trace, and the `probs[rows, want]` gather. The stand-in model exercises the arithmetic and the indexing; only NDIF exercises nnsight. **The anchor gate exists for exactly this** — run `--anchors-only` first, it is cheap, and 42 readings that must pin at 1.000 will catch all three if any is wrong.
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

**Closed:** 2026-11-01. Anchor gate passed at 0.000e+00 over 42 readings. Destination hit rates base 1% / real 29% / ctl 1% / other 1%; paired `real - ctl` +0.2828 (CI +0.2424, +0.3232) against destruction's +0.0009 on the same probes.

**What the dry-run and the pre-run checks caught, none of it by running:**

1. **T-007's own cost estimate was wrong in a way that would have produced a fake result.** It said "only the readout changes, from `probs[rows, want]` to an argmax". The probes ask for a *city*; the edit injects a *country*. A literal `top1 == target` test would have scored the real arm near zero, and a near-zero real arm reads as branch 3 — "these probes have no measurable destination at all" — which was a pre-written branch and would have been believed. Found by reading the probe set before writing the hit test.
2. **The pool-restricted readout was costed and rejected rather than attempted.** [E-014]'s criterion is 495 × 75 × 3 teacher-forced pairs, roughly eleven times [E-014]'s own run, which is not one session.
3. **`ctl` had never been magnitude-matched to `real`**, unlike the donor arm. Checked before the run: unbiased in direction, not matched per subject. The claim was narrowed to aggregate *before* the numbers existed, which is the only time narrowing is free.

