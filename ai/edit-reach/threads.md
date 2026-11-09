# Threads

Open questions, not work. A thread graduates to a ticket when it becomes work. One sentence per line; always record the parent. Parked is not dropped.

---

### T-001 · Can any screen bound an edit's damage from above, or only from below?

**Status:** answered
**Parent:** —
**Opened:** 2026-10-31
**Question:** A benchmark bounds damage from below — it finds what it contains. A computable per-prompt quantity removes the enumeration problem, but it is still evaluated on prompts we happen to have. Is there a construction that bounds reach above (a statement of the form "nothing outside this set receives more than c"), or is an upper bound structurally unavailable, in which case that should be stated once and loudly rather than implied away?

**Reframed, not answered — Premise Dry-Run, 2026-11-09.** The question assumed the upper bound is the hard direction. In activation space it is the easy one, and it is free.

The edit adds `δ · c(k)` at the edited layer, where `δ = v* − Wk*` is **fixed** and only the scalar `c(k) = (k*ᵀC⁻¹k)/(k*ᵀC⁻¹k*)` varies with the token. That is a ratio of inner products under the PSD form `C⁻¹`, so Cauchy–Schwarz in that geometry gives, for **every** prompt, with no enumeration and no forward pass through the edited model:

    |c(k)| ≤ ‖k‖_{C⁻¹} / ‖k*‖_{C⁻¹},   with equality exactly when k ∥ k*.

So a universal upper bound exists and is one line. Three things follow, and the second is the one that matters.

1. **It may be vacuous.** `C` is the second moment of keys, so `E[‖k‖²_{C⁻¹}] = tr(C⁻¹C) = d`: a typical token has `‖k‖_{C⁻¹} ≈ √d`. If `k*` is also typical the bound reads ≈ 1 — the anchor value — so it permits every token to behave like the anchor and forbids nothing. Whether that is what happens is measurable on data already on disk. Spawned **T-010**.
2. **The real obstruction is downstream, and it is not ours.** A bound on `‖Δh‖` at one layer says nothing about logits without a Lipschitz constant for the rest of the network, and dot-product self-attention is reported to have no global Lipschitz bound on an unbounded domain. If that holds, no *deterministic* behavioural upper bound is available through a transformer — a statement about transformers rather than about editing, which is sharper and more defensible than "an upper bound is unavailable". Spawned **T-011**. `TODO(cite)`: that Lipschitz result is from memory and must be read before it is repeated anywhere.
3. **This is certified robustness under another name**, and ours is the easy case. The literature certifies against an adversary free to pick any direction in a ball. A rank-one edit has one direction, chosen in advance and known before the edit is applied. Spawned **T-012**.

**What the reframe breaks.** The paper's *"we can say which facts an edit touches, not how hard"* is imprecise under this frame: how hard **is** boundable in activation space. What cannot be done is converting that to behaviour. The sentence should say which of the two it means.

**Answer (the bounding half): yes, and it is useless where it matters.** [E-015] / C-007, 2026-11-09. The bound holds for all 1,539 question-positions, but its median value in the far field is **1.1456** against a median coefficient of 0.0544 — it permits a question that never names the edited subject to receive more than the near field actually receives. A universal upper bound is available and forbids nothing that happens. T-001's second clause is the live one: **state that once and loudly** rather than imply it away. The remaining half — whether any activation bound crosses into behaviour — is T-011 and is unanswered.

### T-002 · Is subject-string frequency the operative variable, not dependent count?

**Status:** open
**Parent:** T-001
**Opened:** 2026-10-31
**Question:** Carried from `ai/edit-slice/threads.md`. If the edit arrives wherever the subject string sits, then how often that string occurs across the probe bank may predict damage better than how many facts depend on the edited one. Falsifier is written out in the edit-slice ledger. **Check KnowledgeSmith (2510.02392) first — it already tested the out-degree hypothesis, and this thread is only interesting where it departs from that.**
**Answer:** —

### T-003 · The shared prerequisite behind "modify" and "extract"

**Status:** open
**Parent:** —
**Opened:** 2026-10-31
**Question:** Open Problems §3.2.2 (modify internal mechanisms) and §3.5 (extract latent knowledge) both bottom out in the same requirement: a way to tell what the model holds that is independent of what the asker put in. Modify needs it to know what it broke; extract needs it to know the answer was not planted. Is that one instrument or two, and does this project's screen serve both or only the first?
**Answer:** —

### T-004 · A page built from the agent's own self-written reference loses to one built from outside sources

**Status:** open
**Parent:** T-003
**Opened:** 2026-10-31
**Question:** Cross-project, from `~/code/style` C-002: the agent's own account of what it knows produced a worse artifact than knowledge brought in from human sources, on both blind questions (414 words against 1,649). If that reproduces, it is an elicitation result — what a model reports about its knowledge understates what it can use — and belongs to §3.5. Logged here so it does not go cold; the work, if any, stays in `style`.
**Answer:** —

### T-005 · Is the coefficient blind in exactly the regime propagation lives in?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-10-31
**Question:** `(k·u)/(u·k*)` is large when a token's key resembles `k*`, which happens when that token *is* the edited subject. So the measure has dynamic range in the **near field** — prompts containing the subject, 0.93–1.000 — and by construction little or none in the **far field**, prompts that never name the subject, where [E-018]'s different-subject floor is 0.082. Genuine multi-hop propagation lives in the far field. If so the instrument is a contamination detector rather than a propagation detector, which is a narrower and more defensible thing to claim, and it should be claimed that way rather than discovered by a reviewer.
**Falsifier, and it is cheap:** read coefficients for MQuAKE's later-hop items (0 of 16,506 name the edited subject) against the different-subject floor on the same prompts. No edits, no gradients, one forward pass per batch. If they sit at floor and flat, the blindness is established and the claim narrows. If a meaningful fraction sits above floor, the far field is visible after all and the instrument is more than a screen. **Either answer is worth having, which is what makes it worth running.**
**Do not run before C-001.** If predicted reach does not track measured movement where the coefficient *does* vary, the far-field question does not arise.
**Answer:** **Yes — blind to the subject, sighted only on the relation.** [E-004] / C-004, 2026-11-01. Most of this was already measured by [E-039] on 2026-10-15 (0.933 near, 0.055 far, n=513); what was missing was the floor *on those prompts*, which this supplied. Far-field excess over a same-relation donor floor is **+0.0002** (CI +0.0001, +0.0004) against the near field's **+0.8439**. A stranger's edit on the same relation reaches a far-field question as much as the real subject's does. The instrument is a contamination detector plus a relation detector. Note the near-miss: against *all* donors the excess is +0.0232 and reads as far-field signal — nearly all donors carry a different relation, so that floor was the different-relation floor under another name. See `results/E-004-summary.md`.

### T-006 · `LanguageModel` is deprecated, and every number so far was read through it

**Status:** answered
**Parent:** —
**Opened:** 2026-10-31
**Question:** `editreach.remote.connect` calls `nnsight.LanguageModel`, which now warns: *"LanguageModel is deprecated; use TransformersModel(repo_id, task='text-generation') instead."* Every reading in edit-slice and in [E-001] came through it. Two things need separating before anything is changed: whether `TransformersModel` resolves the same module paths (`arch.py` depends on them), and whether it produces bit-identical activations — because if it does not, numbers read through the two are not comparable and the switch is a re-baseline rather than an upgrade.
**Do not change this mid-question.** Changing the loader while C-002 is open would put a possible re-baseline inside a running comparison. The anchor gate is the cheap test: 42 readings that must pin at exactly 1.000 under both loaders, and `anchor-floor` reproducing 0.0809 under both.
**Why it is logged rather than done:** a deprecation warning is the quiet kind of dependency failure. [E-047] was the loud kind and still cost six wrong diagnoses; this one gives notice and the notice should not be spent.
**Answer:** **The loaders are the same instrument; the switch is safe and was deliberately not taken.** [E-005] / C-005, 2026-11-01. Module paths identical; within-loader spread equals between-loader spread over three readings each, so the loader is not the variable. Gates hold under both. `connect(loader=...)` is switchable with `"language"` still the default, because switching on the same day T-008 was found would be two changes with one unmeasured. Both questions this thread asked are answered: same module paths **yes**, bit-identical activations **no — and not between two readings through one loader either**, which is T-008. See `results/E-005-summary.md`.

### T-007 · Does an edit break the old answer and supply the new one by two different routes?

**Status:** answered
**Parent:** T-003
**Opened:** 2026-10-31
**Question:** Three results line up and none was designed to test this. [E-002] (edit-reach): destruction of the pre-edit answer is subject-keyed — a magnitude-matched edit on a different person moves it by 0.0016 against 0.0625 for your own subject, almost regardless of content. [E-014] (edit-slice): the destination of the new answer is content-specific — the same-subject control lands in the injected country 5% of the time against the real edit's 67%. [E-046]: the replacement is confident and specific rather than flat. Together they suggest an edit does two separable things — breaks the old answer because it touched that subject's key, supplies a new one because of what it said.
**Why this is a thread and not a claim:** it is read across three experiments built for other questions, with different probe sets and different metric families. A reading that fits three results it was not tested against is the cheapest kind of story to tell.
**Falsifier, and it is one run:** score the [E-002] probe set for *destination* — post-edit top-1, not the probability of the pre-edit top-1 — under all four arms. If destination separates real from same-subject control on the same probes where destruction does not, the split is measured rather than inferred. If both halves behave alike on one probe set, the apparent split was an artefact of comparing two experiments.
**Cost:** one NDIF session. The arms and the probe set already exist; only the readout changes, from `probs[rows, want]` to an argmax.
**Answer:** **Yes, measured.** [E-003] / C-003, 2026-11-01. On the same 495 probes: destination `real - ctl` is **+0.2828** (CI +0.2424, +0.3232) where destruction `real - ctl` is **+0.0009**; destination `ctl - other` is **+0.0000** where destruction `ctl - other` is **+0.0583**. Opposite directions on one probe set under one metric, so the split is measured rather than read across three experiments. One correction to this thread's own framing: "only the readout changes" was too optimistic — the probes ask for a city and the edit injects a country, so the hit test had to become "the top-1 token begins a city in the injected country" rather than an equality. See `results/E-003-summary.md`.

### T-008 · Readings differ between NDIF serving sessions, on byte-identical inputs

**Status:** answered
**Parent:** T-006
**Opened:** 2026-11-01
**Question:** Found while answering T-006, and larger than it. Two readings of the same prompts at the same positions, with byte-identical input ids, differ on **93.94% of elements** — up to 6.250e-01 at `lm_head` and 3.125e-02 at the layer-5 key site, against a median |key| of 1.135e-02. Only ~6% of differing elements sit within one bf16 ulp of their own value, so it is not rounding on the wire. Within a session it is deterministic: repeated reads agree bit-for-bit. The grouping follows contiguous runs of connections rather than the loader, which fits routing to one of several replicas and is **not tested**.
**Why it matters more than it looks:** every "reproduces [E-039]" or "pins at 1.000" check in this repo is reading a single session. The anchor gate survives because `k` and `k*` share a trace, so the ratio cancels whatever the session does — that is luck in the gate's design, not foresight. [E-001]'s published floor median of **0.0809** is a first-connection value; later connections give **0.081093**. A spread of 1.5e-4 on a number quoted to four decimals.
**Falsifier, and it is cheap:** read the same batch across N fresh processes and record which value each returns, with the NDIF request/host metadata the client exposes. If the values partition by host, the replica hypothesis is established and the fix is to record the host alongside seed and layer. If they do not, the cause is elsewhere and every cross-session comparison needs a tolerance rather than an equality.
**What to do meanwhile:** no artifact should claim bit-identity across sessions, and anything comparing readings taken at different times needs a stated tolerance. [E-004]'s ±0.02 reproduction gate was right for this reason without knowing it.
**Answer:** **It is routing, and it partitions cleanly by serving GPU.** [E-006] / C-006, 2026-11-01. 16 readings, two devices, 8 each, one value per device and one device per value. Floor median spread 0.000e+00 within a GPU and **3.110e-06** across. The replica hypothesis this thread floated is established. **But the device is only 1.4% of the drift actually observed** (range 2.16e-04 over four readings across two days), so the thread's implied fix — record the device and numbers become comparable — is not sufficient. Batch composition contributes zero; where the dot product runs contributes 5.06e-06 at the median and 2.98e-03 per item. The remainder is **T-009**. Practical rule adopted: no bit-identity across readings, tolerance ≥ 2.2e-04 for cross-trace quantities, and prefer a ratio read inside one trace. See `results/E-006-summary.md`.

### T-009 · The serving GPU accounts for 1.4% of the observed drift. What accounts for the rest?

**Status:** open — narrowed
**Parent:** T-008
**Opened:** 2026-11-01
**Question:** [E-006] established that NDIF readings partition cleanly by serving GPU, and priced it: floor median spread **3.110e-06** across devices, 0.000e+00 within one. But four values of that same quantity have been observed over two days — 0.08087725 ([E-001], 10-31), 0.08094215 ([E-005] first reading), 0.08109000 (GPU 0), 0.08109313 (GPU 2) — an observed range of **2.16e-04**, some sixty times the device spread. Batch composition was tested and contributes **zero**. Where the dot product runs contributes 5.06e-06 at the median (though **2.98e-03 per item**, which is its own finding). The remaining ~2e-04 separates October 31 from November 1 and is unattributed.
**Candidates, none tested:** a model redeployment or weight reload between the two days; a third serving device not sampled in 16 readings; a server-side library or driver change; something in how [E-001] batched at 200 rows that [E-006] does not reproduce at 126.
**Falsifier:** re-read the 42 floor probes daily for a week, recording the GPU and the exact median. If values cluster by day rather than by device, it is deployment state and the fix is to record a server fingerprint per run. If they scatter within a day, a third source is live and the 2.2e-04 tolerance is a floor rather than a bound.
**Why it is logged rather than chased now:** 2.2e-04 is already below every tolerance this project relies on, and the anchor gate — the one quantity known analytically — is immune by construction. This is worth knowing, not worth blocking on. **It becomes blocking the moment any claim needs reproducibility tighter than 2.2e-04.**
**Answer:** —

**2026-11-03 [E-009]:** one candidate promoted from guess to observation. The set of GPUs serving `Llama-3.1-8B` changed between 11-01 (GPUs 0 and 2) and 11-03 (GPU 0 alone, 16/16 connections; `GPT-J-6B` likewise). A deployment change demonstrably happens between days, and it sits between exactly the sessions whose floor medians differ. Nothing yet shows the two move together — the falsifier is unchanged: read the same 42 floor probes daily for a week, recording device set and exact median, and see whether the median moves when the device set does.

**2026-11-03 [E-012]: the framing was wrong, and most of the question dissolves with it.** The first daily reading came back **bit-identical** to [E-006]'s GPU 0 value from two days earlier — same content hash, same median to the last bit. A census over all 24 recorded readings gives **four distinct values, each exact and each repeating**, with a within-device spread of **0.000e+00** and an across-everything spread of 2.159e-04. Thirteen readings return one value to the last bit across two nnsight loaders.

So there is **no time component**. The quantity is not drifting; it is discrete, and routing picks which value you see. [E-006]'s 3.11e-06 "device spread" was the distance between the two replicas its 16 connections happened to reach, and the "unattributed" residue was the replicas it did not reach.

**What is still open:** how many replicas exist. Two of the four values were recorded before the device was being captured and cannot be attributed now. **What would reopen the original question:** a device-matched pair of readings that differs. One such observation restores a time component. The daily reading continues for that reason and no longer for the original one.


### T-010 · How loose is the Cauchy–Schwarz bound on the coefficient, in each regime?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-11-09
**Question:** `|c(k)| ≤ ‖k‖_{C⁻¹}/‖k*‖_{C⁻¹}` holds for every prompt. A bound that is never approached forbids nothing. Measure the looseness ratio `bound/|actual|` per prompt, in the near field (prompts naming the edited subject, `c` 0.93–1.000) and the far field (prompts that never name it, floor 0.082), on the probe sets already on disk.
**Falsifier, and both branches carry a consequence:** if the ratio stays within about an order of magnitude in both regimes, the screen carries a usable upper bound — a positive result this project does not currently have. If it is loose by orders in the far field, the bound is real and vacuous exactly where propagation lives, which is the contamination-detector finding arriving a second time by a different route and worth reporting as such.
**Cost:** no edits, no gradients, no new reads. `C` and `k*` are cached and `k` is already recorded per probe.
**Answer:** **Far field 21.12 (95% CI 20.16–22.14), near field 1.05.** [E-015], 2026-11-09, 1,539 question-positions. Branch 2. The near-field tightness is not independent news — there `k ≈ k*` by the same prefix-sharing that pins the anchor — and is reported as an implementation check rather than a result.

### T-011 · Can an activation-space bound cross into a behavioural one through a transformer?

**Status:** open
**Parent:** T-001
**Opened:** 2026-11-09
**Question:** T-001's bound is on `‖Δh‖` at the edited layer. Every claim anyone cares about is about output. Crossing needs a Lipschitz constant for layers L→end, and dot-product self-attention is reported to lack a global one on an unbounded domain. Is a deterministic behavioural bound therefore unavailable in principle, available on a bounded input domain at a constant too loose to use, or replaceable by a probabilistic certificate from randomized smoothing?
**Read before designing:** the self-attention Lipschitz literature and the certified-robustness line (interval bound propagation, CROWN, randomized smoothing). `TODO(cite)` throughout — none of it has been read, and T-001's claim that self-attention has no global Lipschitz bound is from memory and unverified.
**Why it is not the next card:** it is a literature question before it is a measurement, and answering it from memory is exactly how this project has been bitten before.
**Answer:** —

### T-012 · Is weight-space certification easier than input-space, and has anyone taken that?

**Status:** open
**Parent:** T-001
**Opened:** 2026-11-09
**Question:** Certified robustness is hard partly because the adversary picks a direction in a ball. A rank-one weight edit perturbs along **one** direction, fixed and known before the edit is applied, with only a scalar varying per input. That is a strictly smaller problem than the one the literature attacks. Either someone has already made the observation for weight edits — in which case it is a citation, not a contribution — or the lane is open.
**Positioning rule applies:** a wrong "the lane is open" surfaces later when the paper turns up. A wrong "we were scooped" kills the work silently and leaves no evidence it was wrong. Verify before shelving; never shelve on a search snippet.
**Answer:** —
