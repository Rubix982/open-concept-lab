# The seven structural questions

Pass 2 of the skill, expanded. These cannot be linted — they are asked of the
draft's structure, which is why they carry the effect.

---

## 1 · Headings — can this be rewritten as a sentence with a truth value?

A heading naming only a subject area means the section is a survey, not an
argument.

> ✗ `## Background: localization methods and evaluation goals`
> ✓ `## GradSim predicts which edits break their neighbours; nothing certifies that one did not`
> ✓ `## What made me withdraw it` *(a question the section answers)*
> ✓ `## Where does a large language model store its facts?` *(ROME §1)*

**Exempt:** structural labels that carry navigation rather than argument — Limits,
References, Appendix, Method, Acknowledgements.

---

## 2 · Gaps — which gap, what cost, what changes?

> ✗ "Open gaps remain in scalability and certification."
> ✓ "Certifying that all entailed neighbours survive an edit requires enumerating
> them first. That enumeration does not exist and is not cheap: entailment is
> open-ended, so the set is either hand-written per edit — which does not scale and
> builds in the author's assumptions — or discovered by intervention, which costs a
> forward pass per candidate. Until someone prices that, 'certification layer'
> names a wish rather than a programme."

Name the gap, the requirement, the cost, and the cheaper thing available now.

---

## 3 · Symbols — see `mathematics.md`

---

## 4 · Suppression — is every dropped term acknowledged where it is dropped?

One clause at the point of abuse. See `mathematics.md`.

---

## 5 · Naming — does an existing vocabulary denote this exactly?

See `mathematics.md`. Borrow if exact; coin only if nothing fits.

---

## 6 · Hedging — is any qualification outside the Limits section?

> ✗ "Results suggest the method may generalize, though further work is needed."
> ✓ Body: "The method generalizes to the three relations tested."
> ✓ Limits: "Tested on three of CounterFact's 34 relations, all rigid. Whether
> mutable relations behave the same is unmeasured."

The vague version is *less* honest — it never names which limit applies.

---

## 7 · Criticism — is the scope fixed before the damage?

> ✗ "CounterFact fails to verify whether models hold the facts being edited."
> ✓ "CounterFact was built to make insertion hard, and it does that. Sampling a
> plausible-but-wrong object of the same relation is a sound way to get difficult
> targets. Possession of the fact being displaced is a different question, and it
> was simply never the one being asked. The problem is downstream."

Bounding first makes the criticism land harder, not softer — a reviewer cannot
dismiss it as a misreading of the target's purpose.

Same move at abstract length, from Sparse Feature Circuits:

> "Circuits identified in prior work consist of polysemantic and
> difficult-to-interpret units like attention heads or neurons, rendering them
> unsuitable for many downstream applications. In contrast, sparse feature circuits
> enable detailed understanding…"

One sentence naming a *structural* deficiency of the unit, one naming the
capability it blocked. No adjectives about quality.
