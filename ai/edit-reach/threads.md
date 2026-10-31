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

**Status:** open
**Parent:** T-001
**Opened:** 2026-10-31
**Question:** `(k·u)/(u·k*)` is large when a token's key resembles `k*`, which happens when that token *is* the edited subject. So the measure has dynamic range in the **near field** — prompts containing the subject, 0.93–1.000 — and by construction little or none in the **far field**, prompts that never name the subject, where [E-018]'s different-subject floor is 0.082. Genuine multi-hop propagation lives in the far field. If so the instrument is a contamination detector rather than a propagation detector, which is a narrower and more defensible thing to claim, and it should be claimed that way rather than discovered by a reviewer.
**Falsifier, and it is cheap:** read coefficients for MQuAKE's later-hop items (0 of 16,506 name the edited subject) against the different-subject floor on the same prompts. No edits, no gradients, one forward pass per batch. If they sit at floor and flat, the blindness is established and the claim narrows. If a meaningful fraction sits above floor, the far field is visible after all and the instrument is more than a screen. **Either answer is worth having, which is what makes it worth running.**
**Do not run before C-001.** If predicted reach does not track measured movement where the coefficient *does* vary, the far-field question does not arise.
**Answer:** —

### T-006 · `LanguageModel` is deprecated, and every number so far was read through it

**Status:** open
**Parent:** —
**Opened:** 2026-10-31
**Question:** `editreach.remote.connect` calls `nnsight.LanguageModel`, which now warns: *"LanguageModel is deprecated; use TransformersModel(repo_id, task='text-generation') instead."* Every reading in edit-slice and in [E-001] came through it. Two things need separating before anything is changed: whether `TransformersModel` resolves the same module paths (`arch.py` depends on them), and whether it produces bit-identical activations — because if it does not, numbers read through the two are not comparable and the switch is a re-baseline rather than an upgrade.
**Do not change this mid-question.** Changing the loader while C-002 is open would put a possible re-baseline inside a running comparison. The anchor gate is the cheap test: 42 readings that must pin at exactly 1.000 under both loaders, and `anchor-floor` reproducing 0.0809 under both.
**Why it is logged rather than done:** a deprecation warning is the quiet kind of dependency failure. [E-047] was the loud kind and still cost six wrong diagnoses; this one gives notice and the notice should not be spent.
**Answer:** —
