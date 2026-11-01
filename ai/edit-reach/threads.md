# Threads

Open questions, not work. A thread graduates to a ticket when it becomes work. One sentence per line; always record the parent. Parked is not dropped.

---

### T-001 · Can any screen bound an edit's damage from above, or only from below?

**Status:** open
**Parent:** —
**Opened:** 2026-10-31
**Question:** A benchmark bounds damage from below — it finds what it contains. A computable per-prompt quantity removes the enumeration problem, but it is still evaluated on prompts we happen to have. Is there a construction that bounds reach above (a statement of the form "nothing outside this set receives more than c"), or is an upper bound structurally unavailable, in which case that should be stated once and loudly rather than implied away?
**Answer:** —

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

**Status:** open
**Parent:** T-008
**Opened:** 2026-11-01
**Question:** [E-006] established that NDIF readings partition cleanly by serving GPU, and priced it: floor median spread **3.110e-06** across devices, 0.000e+00 within one. But four values of that same quantity have been observed over two days — 0.08087725 ([E-001], 10-31), 0.08094215 ([E-005] first reading), 0.08109000 (GPU 0), 0.08109313 (GPU 2) — an observed range of **2.16e-04**, some sixty times the device spread. Batch composition was tested and contributes **zero**. Where the dot product runs contributes 5.06e-06 at the median (though **2.98e-03 per item**, which is its own finding). The remaining ~2e-04 separates October 31 from November 1 and is unattributed.
**Candidates, none tested:** a model redeployment or weight reload between the two days; a third serving device not sampled in 16 readings; a server-side library or driver change; something in how [E-001] batched at 200 rows that [E-006] does not reproduce at 126.
**Falsifier:** re-read the 42 floor probes daily for a week, recording the GPU and the exact median. If values cluster by day rather than by device, it is deployment state and the fix is to record a server fingerprint per run. If they scatter within a day, a third source is live and the 2.2e-04 tolerance is a floor rather than a bound.
**Why it is logged rather than chased now:** 2.2e-04 is already below every tolerance this project relies on, and the anchor gate — the one quantity known analytically — is immune by construction. This is worth knowing, not worth blocking on. **It becomes blocking the moment any claim needs reproducibility tighter than 2.2e-04.**
**Answer:** —
