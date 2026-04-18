# Theory of Mind — Full Landscape

A map of the full ToM space. The lookback paper covers a narrow slice.
Everything else is open territory for mechanistic research.

---

## Where This Paper Sits

```
Full ToM Space
│
├── Beliefs ← this paper
│   ├── First-order ← this paper
│   ├── False beliefs ← this paper
│   └── Visibility / perspective ← this paper (partially)
│
├── Desires                    ← largely unstudied mechanistically in LLMs
├── Intentions                 ← largely unstudied mechanistically in LLMs
├── Higher-order beliefs       ← some behavioral work, little mechanistic
├── Epistemic states           ← almost no mechanistic work
├── Deception                  ← almost no mechanistic work
└── Collective intentionality  ← nearly untouched
```

---

## 1. First-Order vs. Higher-Order Beliefs

**First-order:** what a character believes about the world.
> "Bob believes the bottle contains beer."

**Higher-order:** what a character believes about another character's beliefs.
```
2nd order: "Carla believes that Bob believes the bottle has beer."
3rd order: "Alice believes that Carla believes that Bob believes..."
```

Humans handle ~4-5 levels before breaking down. LLMs are inconsistent
above 2nd order. Whether higher-order beliefs have distinct internal
mechanisms — separate OID-like structures for each level — is unknown.

**Research gap:** Does the model build separate binding structures per
belief level, or does it collapse them? Causal mediation could test this.

---

## 2. False Beliefs vs. True Beliefs

**True belief:** character believes X, X is true. Trivial — no divergence
between belief and reality.

**False belief:** character believes X, reality is Y. The hard case.
This is the Sally-Anne test. The model must track two separate states
simultaneously: the world state and the character's belief state.

The lookback paper specifically targets false beliefs — the interesting
science is always in the divergence. A model that only handles true
beliefs isn't doing ToM, it's doing retrieval.

**Key question for LLMs:** when the model fails false-belief tasks, is it
because the belief-tracking mechanism breaks down, or because something
downstream (answer generation) ignores the correctly-tracked belief?
Causal mediation can separate these failure modes.

---

## 3. Desires and Intentions

ToM classically covers more than beliefs:

| Mental State | Definition | Example |
|---|---|---|
| Belief | what someone thinks is true | "Bob thinks the bottle has beer" |
| Desire | what someone wants | "Bob wants the bottle to have water" |
| Intention | what someone plans to do | "Bob intends to pour out the beer" |
| Emotion | what someone feels | "Bob is surprised the bottle has coffee" |

The paper is narrowly scoped to beliefs. Desire and intention tracking
are much less studied mechanistically. Yet they are essential for full
ToM — predicting behavior requires modeling desires, not just beliefs.

**The belief-desire-intention (BDI) model** (Bratman, 1987) is the
classical framework: agents act based on what they believe is true AND
what they desire to achieve AND what they intend to do. All three are
required to predict another agent's next action.

**Research gap:** Do LLMs have separate internal mechanisms for desire
and intention tracking? Or do they conflate them with beliefs?

---

## 4. Epistemic States — Knowledge vs. Belief

Knowledge and belief are not the same:

```
Belief:    Bob thinks the bottle has beer  (may be wrong)
Knowledge: Bob knows the bottle has beer   (true + justified)
Ignorance: Bob has no information about the bottle
```

In classical epistemology: knowledge = justified true belief.
A character can believe something false (Sally and the marble).
A character can know something true but not believe it (cognitive
dissonance). A character can be deliberately kept ignorant.

**Why this matters for LLMs:** the distinction between "the model knows X"
and "the model believes X" maps directly onto the L0/L3 gap in the
research knowledge infrastructure. The model may output X confidently
while its internal belief node holds something different. That divergence
is the ungrounded epistemic class.

---

## 5. Perspective-Taking

Not just "what does Bob believe" but "how does the world look from
Bob's position?" Three dimensions:

**Visual perspective:** what can Bob physically see?
The visibility condition in the lookback paper is a narrow form of this.
Full visual perspective-taking requires spatial reasoning about occlusion,
viewpoint, and line of sight.

**Informational perspective:** what information has Bob been exposed to?
This is what the paper primarily models — tracking which events each
character witnessed. But real informational perspective is richer:
prior knowledge, background beliefs, inference capacity all differ
between characters.

**Emotional/evaluative perspective:** how would Bob feel, given what he
knows and wants? This requires combining belief tracking with desire
tracking and an emotion model.

**Research gap:** LLMs tested on visual perspective-taking tasks
(e.g., "what can the character see from their position?") fail in ways
that mirror pre-ToM children — they default to their own (the reader's)
perspective rather than the character's.

---

## 6. Deception and Strategic Reasoning

A character may deliberately manipulate another character's beliefs.
This requires the deceiver to:

1. Model the target's current beliefs (first-order ToM)
2. Identify what false belief would be useful to plant
3. Choose actions that will cause the target to form that false belief
4. Predict whether the deception will succeed

This is ToM + game theory. It requires recursive modeling:
"I know what you believe, so I act to make you believe what I want
you to believe, while knowing that you may be modeling me."

Poker bluffing, negotiation, and social manipulation all require this.
Almost no mechanistic work exists on whether LLMs implement anything
systematic here, or whether they're pattern-matching on surface cues
in deception-heavy training text.

---

## 7. Collective and Shared Intentionality

What a *group* believes vs. what individuals believe:

```
Individual: "Bob believes the strategy will work."
Collective: "The team believes the strategy will work."
```

These are not equivalent. Collective belief involves:
- Shared knowledge (everyone knows X)
- Common knowledge (everyone knows everyone knows X)
- Joint intention (we intend to act together toward a goal)

Common knowledge is recursive: "I know X, and I know you know X,
and I know you know I know X..." — infinite regress that humans
resolve with pragmatic shortcuts.

LLMs handling of collective intentionality is almost completely
unstudied. Most ToM benchmarks are dyadic (two characters). Multi-agent
scenarios with group beliefs are rare.

---

## 8. Developmental Trajectory — Failure Modes

In humans, ToM develops in stages:

| Age | Capability |
|-----|-----------|
| ~18m | Joint attention — following gaze, pointing |
| ~2y  | Pretend play — distinguishing appearance from reality |
| ~4y  | First-order false belief — Sally-Anne test |
| ~6y  | Second-order false beliefs |
| ~9y+ | Higher-order, deception, social strategy |

Before ~4, children fail false-belief tasks in a specific way: they
answer from their own (the observer's) perspective, not the character's.
They don't yet distinguish "what I know" from "what Sally knows."

**LLMs exhibit analogous failure modes.** When they fail ToM tasks,
they tend to default to ground truth (the reader's perspective) rather
than tracking the character's divergent belief. The failure looks like
a pre-ToM child — not random error, but systematic perspective collapse.

Whether this means LLMs are "developmentally" stuck, or whether it's
a different kind of mechanism failure, is an open question.

---

## Connection to Research Knowledge Infrastructure

Every ToM branch above has a direct analog in the L0 belief decoder problem:

| ToM Concept | L0 Analog |
|---|---|
| False belief | Model outputs X while internal node holds Y |
| Higher-order | Nested belief nodes — "model believes user believes..." |
| Epistemic state | Difference between model's confident output and internal confidence |
| Perspective-taking | Whose belief is the model currently tracking? |
| Deception | Model that has learned to produce outputs inconsistent with internal state |
| Collective intentionality | Multi-agent reasoning across model instances |

The paper's methodology — causal mediation finding specific nodes —
is the flashlight. This landscape is the cave.
