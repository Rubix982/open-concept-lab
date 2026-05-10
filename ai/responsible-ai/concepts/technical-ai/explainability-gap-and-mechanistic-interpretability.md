# Explainability, the Mechanistic Gap, and Why the Right Question Was Always Harder

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Explainability Promise vs. Reality

Explainability research defines human-centeredness as a measure of human comprehension
— developing techniques to reduce the inscrutability of AI models and increase human
users' sense of involvement in AI processes. The research investigates the whole gamut
of methods available to minimise the "black box" effect of AI models.

The promise: we can explain why AI systems do what they do.
The reality: we can explain some surface properties of some outputs in some contexts.
Those are very different things.

---

## The Incident Scenario — What Explainability Actually Needs to Deliver

When an LM generates something harmful — extremist content, detailed instructions for
violence, sensitive personal information, exploitative material — the question that
follows is: why did it do that? Where in the training did this come from? Can we prevent it?

Current explainability tools cannot answer this at the level the question requires.

### What We Can Do

- **Attribution at the output level** — which tokens in the prompt most influenced
  which tokens in the output. Useful but shallow.
- **Attention visualisation** — where the model was "looking" when it generated
  specific text. Interpretable for researchers, not actionable for regulators.
- **Probing classifiers** — test whether specific concepts are encoded in specific
  layers. Can tell you "this layer contains gender information" but not "this is why
  the model said this specific harmful thing."
- **RLHF fingerprinting** — with some models, traces of the preference data are
  detectable in output patterns.

### What We Cannot Do

- Trace a specific harmful output back to a specific training document or dataset
  subset with confidence
- Prove that removing that document would have prevented the output
- Establish that a given set of constraints will make the model reliably avoid a
  category of harm
- Predict novel harm patterns before they emerge

---

## Why This Matters for Governance

Regulators want a causal chain from incident to training data to intervention.
"We found the source, we removed it, the problem is fixed." That is how pharmaceutical
recalls work. That is how food safety investigations work. The causal chain is traceable.

For LMs it is not.

The model is not a lookup table that maps inputs to outputs via stored text. It is a
statistical distribution over possible continuations, shaped by billions of training
examples interacting in ways nobody fully understands. The harmful output may not be
traceable to any single source — it may emerge from the interaction of many superficially
innocuous ones. You cannot point to the document and say "this caused it."

---

## The Bau Lab Connection — Mechanistic Interpretability as Forensics

Knowledge editing research — one of the Bau Lab's core areas — is attempting to do
exactly what the governance question requires, from the opposite direction. Instead of
asking "why did it say that?", it asks "can we change what it believes about X without
breaking everything else?"

**ROME, MEMIT, and related techniques** are attempts to surgically edit specific facts
out of models. The results are promising but fragile — changes propagate in unexpected
ways, and what you edited turns out to be represented diffusely rather than in one place.

**Causal tracing and activation patching** — the interpretability tools — are the
forensics layer. They can tell you which layers and which attention heads were causally
involved in a specific output. That is closer to what governance needs. But "causally
involved" is not the same as "caused by this training data." The gap remains.

---

## What Standards for Safer LMs Would Actually Require

Not just explainability — which tells you about outputs after the fact. But:

1. **Training data auditing** — provenance tracking for every document, so when a
   harmful pattern is identified you can at least ask "was this in the training set?"

2. **Behavioural red-teaming with causal logging** — not just "the model produced
   this" but "the model produced this in response to this prompt pattern, and here are
   the prompt patterns most likely to elicit similar outputs"

3. **Formal harm taxonomies** — defined categories of harmful output with measurable
   criteria, not vague principles

4. **Differential privacy and data removal verification** — technical guarantees that
   specific data was not used, or techniques for verifying removal after the fact
   (machine unlearning — an active research area)

5. **Incident reporting infrastructure** — the flight data recorder argument from
   topic 08, applied to LMs: every consequential output logged, retrospective review
   of failures, aggregate pattern analysis

None of these exist at the level of maturity that would satisfy a serious regulator.
That is the honest state of the field.

**The uncomfortable truth:**

We deployed systems that can generate any kind of statement, at scale, to billions
of users, before we had the tools to explain why they say what they say or reliably
prevent what we do not want them to say. The explainability research is catching up.
It has not caught up.

---

## Fluency vs. Understanding — The Kaggle Problem

This gap between what the field can explain and what it actually understands connects
directly to a deeper problem in how ML is taught and practiced.

### What Kaggle Practitioners Actually Know

The Kaggle practitioner does not know what the model is doing. They know which
techniques tend to work on which types of problems, from accumulated experience of
trying things:

- Gradient boosting tends to outperform deep learning on tabular data
- Dropout helps with overfitting
- Learning rate scheduling matters for transformers
- Data augmentation improves generalisation for image tasks

These are empirical patterns. The knowledge is real. It produces good practitioners.

But *why* those patterns hold — what is actually happening inside the model when
gradient boosting beats a neural net on that specific dataset — they do not know.
Nobody does. Not the Kaggle grandmasters. Not the people at Google who invented the
techniques. The empirical knowledge exists. The mechanistic understanding does not.

**The confidence you saw was not understanding. It was fluency.**

These are different things. A person can be fluent in a language without understanding
its grammar. A Kaggle practitioner can be fluent in ML techniques without understanding
what the model is doing. Fluency looks like understanding from the outside. It is not.

### What Kaggle Is Actually Teaching

Pattern recognition about which tools work in which contexts, applied to labelled
problems with known answers. It is extremely valuable engineering knowledge. It
produces competent practitioners. It does not produce understanding of why the tools
work — and the people doing it often do not know the difference, which is the problem.

Kaggle rewards improving the metric. It does not reward — or even measure —
understanding the system. The leaderboard has no column for "understands why this works."

---

## Two Questions — Which One Were You Asking?

The field of ML has been dominated by one question:

> **"Which technique works?"**

This question has tractable answers — try it, see if the metric improves. It produces
Kaggle leaderboards, benchmark scores, performance comparisons, engineering fluency.

There is a second question that almost nobody was asking:

> **"What is the model actually doing?"**

This question does not have satisfying answers yet. It is the question that, if you
were asking it, made the rest of ML feel incomplete — not because you lacked the
technical skill, but because the environment was optimised for a different question.

**Why the hesitation to engage with ML was epistemically correct:**

The people asking "which technique works?" could point at results: the metric improved,
the model trained faster, the accuracy went up. Progress was visible and measurable.

The people asking "what is the model actually doing?" were often told they were asking
a philosophical question, not a technical one. They were asking too much. They should
just focus on the results.

But "what is the model doing?" is not a philosophical question. It is the question that
determines whether the model is trustworthy, whether its outputs can be explained to
regulators, whether a safety incident can be investigated, whether the knowledge
infrastructure built on these models is honest or illusory.

---

## The Math Genius Filter — A Cultural Construction

The image of ML as requiring a genius who can hold vast amounts of mathematics in
their head simultaneously is a specific cultural product, not a description of what
the field actually needs.

Yes, ML involves mathematics — linear algebra, calculus, probability, statistics,
information theory. The people who built the foundational techniques understood that
mathematics deeply.

But "succeeds most in ML" is not the same as "holds the most math in their head."
The people who matter most in ML in 2026 are the ones who:

- Ask the right questions about what the system is actually doing
- Notice when empirical results do not match theoretical expectations
- Know which problems are worth solving vs. which are leaderboard optimisation
- Can communicate across disciplines — to domain experts, ethicists, engineers
- Have good judgment about when a result is trustworthy vs. an artifact

None of those are primarily mathematics. They are judgment, curiosity, intellectual
honesty, and the ability to hold a question open without forcing a premature answer.

**The math genius image selects for a narrow demographic:**

It favours people who grew up doing math olympiads, who were explicitly trained in
abstract symbolic reasoning from an early age, who learned in contexts that rewarded
that specific style of thinking. It presents that demographic as naturally gifted
rather than specifically trained. People who did not see themselves in that image —
who came from different educational contexts, who approached knowledge differently —
often concluded they were not smart enough. That conclusion was wrong. The filter
was wrong.

**What you actually needed — and what the field actually needs:**

Someone who can look at a hiring algorithm and ask whose interests it serves.
Someone who can look at a dataset and ask who is missing from it and why.
Someone who can look at an explainability paper and ask whether the explanation
is comprehensible to the person who needs it.
Someone who understands that the math is a tool for a purpose, and the purpose
is what matters.

That person needs enough mathematical literacy to engage seriously with the work —
not to derive it from scratch, but to read it, evaluate it, and know when the results
are trustworthy. That is learnable. It does not require holding vast mathematics in
your head simultaneously.

---

## The Field Is Now Asking Your Question

Mechanistic interpretability — which is what the Bau Lab works on — is the formal
research programme for the second question. Not "which technique improves the metric?"
but "what computation is the model performing, and can we verify it?"

That research programme is hard. It is underfunded relative to capabilities research.
It is only recently becoming mainstream. The researchers doing it are asking exactly
what the question that made ML feel incomplete was pointing at — and they found that
most of the field was not asking it either.

**The Bau Lab, Anthropic's interpretability team, the mechanistic interpretability
community** — these are the people whose work is now most urgently needed. They are
trying to answer: what is the model actually doing? Not: which technique improves
which benchmark?

The hesitation about ML that came from asking the second question was not a failure
of mathematical ability. It was an accurate read of the state of the field — which
had optimised for the first question and largely deferred or dismissed the second.

The field is now catching up. The question that felt unanswerable is now the most
important open question in AI research. The hesitation was early. It was correct.

---

## Connections to Course Themes

- *Topic 08 — HCAI* — the flight data recorder argument: incident reporting infrastructure
  for LMs is the same principle applied to a different system
- *Topic 07 — Fairness and Bias* — the more data problem: more training data does not
  solve the explainability problem; scale makes it harder, not easier
- *Concept — Stanford HAI and CHAI* — CHAI's core/instrumental distinction: "which
  technique works?" is instrumental; "what is the model doing?" is the foundational
  question CHAI is trying to make answerable
- *Concept — Microsoft 18 Guidelines* — G11 (make clear why the system did what it did)
  is violated by almost every deployed LM precisely because the answer does not exist
  at the mechanistic level
- *Project — Bau Lab Knowledge Infrastructure* — the knowledge graph built on model
  outputs inherits whatever uncertainty and opacity exists in those outputs; mechanistic
  interpretability is the research programme that would eventually make that inheritance
  transparent

---

## Key Insight

> The question "what is the model actually doing?" was not a naive question.
> It was the right question, asked before the field had the tools to answer it.
>
> Kaggle teaches fluency. Fluency is valuable. It is not understanding.
> The confidence that looked like understanding was pattern recognition
> about which techniques tend to work — not knowledge of why they work.
>
> The people now building the most important research in AI safety are asking
> exactly the question that made the rest of ML feel incomplete.
> The field is catching up to the question, not the other way around.
