# What Is Responsible AI?

## The Term Is Contested

"Responsible AI" means different things depending on who uses it:

1. **Academic field** — interdisciplinary research on technical and social approaches to AI in
   societal contexts
2. **Corporate framing** — stated aim projecting safety, benevolence, trustworthiness;
   translating principles into policies
3. **Stakeholder movement** — actors working to develop AI that promotes environmental and
   societal good

> Always ask: are they using it as greenwashing? A set of practices? A set of goals?

---

## Why Not "Ethical AI"?

"Ethics" is equally contested. Calling something "ethical" implies certitude that difficult
value questions are already settled — which they aren't.

---

## The Deeper Problem

"Responsible AI" as currently practiced is:

- Good-faith but insufficient technical measures
- Wrapped in corporate language
- Ratified by regulators who don't fully understand the architecture
- Marketed to a public that cannot evaluate the claims

The actual hard problems remain structurally unsolved.

---

## A Practical Demonstration — The Values Problem

Consider a direct interaction with an AI system. It may seem intelligent — it responds
coherently, follows complex reasoning, engages with nuance. But this appearance is
conditional and fragile.

With a different sequence of prompts, open permissions, or adversarial framing, the same
system can produce outputs that are confidently wrong, internally contradictory, or
outright ridiculous. A genuinely intelligent system would have some coherent internal model
of the world that resists arbitrary re-framing. These systems don't. There is no stable
ground being reasoned from — only a context window and a probability distribution over
the next token.

**This matters for "responsible AI" in a specific way.**

Responsible AI requires values to align to. But consider what happens when you try to
define those values:

- What is intelligence? Contested — see the behavioral vs. metaphysical vs. functional
  debate (*Topic 02*)
- Is AGI a meaningful goal? Contested — reasonable people disagree sharply (*Topic 03*)
- What constitutes human flourishing? Contested across cultures, traditions, and generations
- Whose values should the system reflect? Contested — no single answer survives scrutiny
- Who decides? Contested — and the people currently deciding are largely unrepresentative
  of the people affected

These are not edge cases. They are the centre of the problem. And they are not going to be
resolved by a benchmark, a principles document, or a safety team's internal review.

**RLHF and the approval problem.** The dominant method for aligning large language models —
Reinforcement Learning from Human Feedback — trains systems on human approval signals.
Humans rate outputs. The model learns to produce what receives high ratings.

But this encodes:
- The values of the specific group of humans providing feedback, not humanity broadly
- What people are comfortable *saying* they approve of, not necessarily what they actually value
- The approval-seeking dynamics of the feedback process itself — raters who avoid controversy
  produce models that avoid controversy
- The perspectives of people *in* the process, systematically excluding those who are not

The result is not a system with correct values. It is a system with a particular group's
expressed preferences, laundered through a technical process and presented as aligned.

---

## What "Responsible" Might Actually Mean

Not: a system that has correct values encoded into it — there is no agreed correct.

But: a system whose value assumptions are made **explicit and contestable**, rather than
hidden inside a training process and presented as neutral.

The honest version of "responsible AI" would require:

1. **Naming whose values** are encoded and how they were selected
2. **Naming who was excluded** from the process that produced those values
3. **Making the assumptions contestable** — not locked into infrastructure before the
   public can engage with them
4. **Acknowledging instability** — a system that can be made to behave ridiculously with
   the right prompt is not a system whose ethical behaviour should be trusted at scale

This is a much harder standard than current "responsible AI" practice meets. It is also
the only standard that takes the contestedness of the term seriously.

---

## Key Insight

> Placing "responsible" in front of anything makes us think of it more positively.
> That doesn't clarify what distinguishes responsible AI as such.
>
> The deeper problem: "responsible" requires values, values are contested, and the process
> of encoding values into AI systems currently hides that contest rather than resolving it.
> A system whose behaviour can be inverted with a prompt is not a system whose values
> can be trusted — regardless of what the principles document says.

---

## Connections

- *Topic 02 — What is Intelligence?* — the instability of AI behaviour reflects the
  unresolved question of what intelligence actually is
- *Topic 03 — Narrow AI vs. AGI* — the values problem scales: if we cannot agree on values
  for current systems, the AGI framing multiplies the stakes without resolving the contest
- *Concept — Tarbiyat and Epistemic Honesty* — the approval-seeking dynamic in RLHF
  mirrors the broader problem of sycophancy in the institutions that govern AI
