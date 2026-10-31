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