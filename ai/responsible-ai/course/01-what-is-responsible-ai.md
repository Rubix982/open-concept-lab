# What Is Responsible AI?

_Personal study notes — original analysis and synthesis based on course themes,
independent research, and discussion. Not a reproduction of course material._

---

## The Term Is Contested

"Responsible AI" means different things depending on who uses it:

1. **Academic field** — interdisciplinary research on technical and social approaches to AI in
   societal contexts
2. **Corporate framing** — stated aim projecting safety, benevolence, trustworthiness;
   translating principles into policies
3. **Stakeholder movement** — actors working to develop AI that promotes environmental and
   societal good

Always worth asking: is someone using it as greenwashing? As a set of practices?
As a set of goals? The answer changes everything about how seriously to take the claim.

---

## Unpacking the Adjacent Terms

### "Trustworthy AI"

The problem with "trustworthy AI" is that it humanises a system and implies a level of
dependability that does not exist. A useful analogy: if someone a century ago advertised
"trustworthy aviation," you would not be reassured — you would be worried. Things that
work reliably do not need the label. The label signals anxiety, not competence.

> "That is the difference between engineering and alchemy." — Ricardo Baeza-Yates

A second problem: framing trust as the goal redirects attention from the system to the
user's feeling about the system. It circumvents the hard work of building ethically sound
systems by placing the burden — and the blame, if something goes wrong — on the user.
Trust is the outcome of doing the work correctly. It is not the goal that substitutes for
doing the work.

### "Ethical AI"

"Ethical AI" implies moral agency — the capacity to intend ethical outcomes and reorient
behaviour toward values. Humans have this. AI systems do not.

An AI system can produce ethical or unethical _outcomes_. It can incorporate value
judgments embedded by its designers. But it is not a moral agent. It has no intent.
Ethics, in the full sense, remains strictly a human domain.

The danger of the term is that it shifts perceived responsibility from the people who
built and deployed the system — where it belongs — onto the system itself, which cannot
bear it. When an "ethical AI" produces harmful outcomes, the framing obscures who is
actually accountable.

### "Responsible AI" — Why It Is Preferred (and Still Imperfect)

Responsibility, unlike ethics, has been legally and institutionally extended beyond
individuals to organisations and structures. That extension makes "responsible AI" more
precise: it is shorthand for _responsible development and deployment of AI_ — the
responsibility always lying with the humans and institutions involved, never with the
system.

AI Ethics is a _subdomain_ of Responsible AI — not a synonym. Within responsible AI
we ask "what is the right thing to do?" Ethics sits at that core. Around it is the
broader interdisciplinary space: design, engineering, policy, law, philosophy, and
the governance structures that hold all of it together.

The term is still imperfect — it can still be read as implying the AI itself carries
responsibility, which is not the intent. But it is the least misleading of the three.

---

## Why Not "Ethical AI"?

"Ethics" is equally contested. Calling something "ethical" implies certitude that difficult
value questions are already settled — which they aren't. And as above, it misplaces moral
agency onto a system that cannot hold it.

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
  debate (_Topic 02_)
- Is AGI a meaningful goal? Contested — reasonable people disagree sharply (_Topic 03_)
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
- What people are comfortable _saying_ they approve of, not necessarily what they actually value
- The approval-seeking dynamics of the feedback process itself — raters who avoid controversy
  produce models that avoid controversy
- The perspectives of people _in_ the process, systematically excluding those who are not

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

## Sources

- Cansu Canca and Ricardo Baeza-Yates — _"What is the Difference Between AI Ethics,
  Responsible AI, and Trustworthy AI?"_ Institute for Experiential AI, December 2022.
  Interviews with the co-chairs of the AI Ethics Advisory Board.

---

## Connections

- _Topic 02 — What is Intelligence?_ — the instability of AI behaviour reflects the
  unresolved question of what intelligence actually is
- _Topic 03 — Narrow AI vs. AGI_ — the values problem scales: if we cannot agree on values
  for current systems, the AGI framing multiplies the stakes without resolving the contest
- _Concept — Tarbiyat and Epistemic Honesty_ — the approval-seeking dynamic in RLHF
  mirrors the broader problem of sycophancy in the institutions that govern AI
