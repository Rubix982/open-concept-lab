# Where this stands

_Written 2026-10-19 to be read away from the desk. No tasks in it. The record it
summarises is `agents/shared/`, the paper is `web/notebook/edit-slice/review.md`._

---

## One sentence

When you edit a fact into a language model's weights, the edit does not go where people
think it goes — and the tests the field uses to check it cannot tell the difference.

Everything below is evidence for that sentence, or a boundary on it.

---

## What the project established

**The update is delivered by arithmetic, not by inference.** ROME's rank-one edit divides
by `u·k*`. Under causal attention, any prompt sharing the edit prompt's prefix up to the
subject's last token has an identical key at that token, so the coefficient is exactly 1 —
for any `u`, any covariance, any layer, any relation being asked about. This is a
derivation, not a measurement; what was measured is its premise, on four models from 6B to
405B. A prompt about a *different* subject receives 0.082. The distributions do not
overlap.

The consequence that matters: a probe moving after an edit is not evidence the model
reasoned. Editing where someone **works** relocates their **birthplace** at exactly the
same rate as editing their birth country — paired difference +0.0 pp, McNemar p = 1.000 —
and work country entails nothing about birth city.

**That failure is in published benchmarks, measured on their own materials.** RippleEdits
has a test type meant to check whether an edit propagates to a *different* entity reached
through the edited one. Their prompt reads *"the name of the head of government of the
place of death of **Leo Arons** is"* — and the edited subject is sitting in it. Those
prompts receive **0.982** of the update vector, against a floor of **0.070** built by
scoring the same prompts against a stranger's edit. The update arrives by arithmetic. An
editor could score well on that test while generalising nothing.

It is not a law of multi-hop tests, which is what makes it diagnosable rather than a
complaint. MQuAKE names the edited subject when and only when the edit sits on the chain's
first hop: **6,861 of 6,861**, and **0 of 16,506**. Benchmarks that avoid the problem
already exist, in the field's own data, by construction rather than design.

**A standard efficacy metric measures one quantity wearing a comparison's name.** ROME and
MEMIT share a stopping rule — `if loss < 5e-2: break` — where the loss is a sum of
non-negative terms including the target's negative log-probability. So both optimisers halt
once `P(target) > 0.951`. The target is pinned by construction; all the between-subject
variance lives in how far the *true* answer fell. The efficacy margin is therefore
rank-identical to true-answer suppression, at ρ = 1.000 on 42 subjects.

**Renaming the subject changes what is delivered, in proportion.** Across 370 aliases, the
fraction of the update a renamed subject receives tracks its string similarity to the
original at ρ = +0.778, slope +0.847 — close to proportional. `Royal Ontario Museum` and
`ROM` are not the same key.

---

## What it does not establish

**Nothing about how far an edit travels.** Seven candidate predictors were eliminated
against a pre-registered floor with multiple-comparison correction — update size, key size,
their ratio, the belief's strength, the target's prior, the subject's length, the local
residual norm. The best pairing of the two survivors is bounded in closed form at ρ = 0.534,
which is 28.5% of variance. Against the structural ceiling in that setting — 0.932, because
only 13% of the variance lies between probe forms rather than between subjects — that is
about a third of what is reachable. The question is open and it has been searched.

**Nothing about editing being improvable.** Deliberately. The project measures what existing
editors do and does not propose better ones.

**Nothing about whether a formal domain fixes this.** Typeshed signature facts are held at
49.5% against CounterFact's 74% at matched candidate counts — viable on a subset, where the
function's purpose determines the return type (57–100%), and not where the stub author chose
among plausible alternatives (0–28%). And when grounds that *strictly entail* were supplied,
the editor was indifferent to the entailment. A decidable oracle buys a decidable **audit**.
It does not buy a cleaner **edit**.

---

## Limits

- The coefficient result is about **delivery** — what fraction of the update arrives at a
  token. Delivery and effect come apart by 2.96× at a fixed coefficient, so no number here
  says how far an answer moved.
- The coefficient is a property of **a token**, not of a prompt. Within one prompt the
  subject position and the final position differ by a factor of 35, and the answer is
  produced at the final position.
- Hand-built and mined sets license an existence claim and never a rate.
- The novelty position rests on one web-search pass and one neighbouring paper read in
  full. That is enough to ask whether the result is known and not enough to assert it is new.
- **Nothing here has been read by anyone outside the project.** Every finding was produced
  and reviewed by the same two parties. The self-correction record — three cycles caught
  overclaiming before it reached a document — is evidence the process works, not evidence
  the conclusions are right.

---

## The one decision outstanding

A 350-word note is written and unsent. It states the screen, gives the Leo Arons prompt as
the worked example, uses the MQuAKE split to show the problem is avoidable, distinguishes
the nearest published work, and asks one question: *is a cheap pre-run criterion for whether
a propagation item can test propagation something the field would use, or a restatement of
what benchmark authors already do by eye?*

That question cannot be answered from inside the project. It determines whether this is a
paper or a note, and whether the next month goes to the benchmark critique or the code
domain. It is the only input that has been missing the entire time.

The note is at `notes/natalie-packet.md`, under the 2026-10-15 heading.

---

## On pace

The manifesto in `~/.claude/CLAUDE.md` says: *"I do not need to see the finished building.
I need only to lay the right brick after the previous one."*

Between 14 and 16 October, largely unattended, the project gated claim 3, generalised the
efficacy result past ROME, caught two of its own cycles overclaiming, and recovered five
destroyed artifacts with no recorded number changed. That happened across hours nobody was
at the desk.

The bricks are being laid. What is missing is a reader, and that costs one decision rather
than one month.
