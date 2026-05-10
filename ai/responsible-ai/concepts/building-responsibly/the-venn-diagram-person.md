# The Venn Diagram Person — Who AI Products Actually Need

*Personal study notes — original analysis and synthesis.*

---

## The Profile

Building a responsible AI product requires a person who sits at the intersection
of three capabilities that existing training pipelines almost never combine:

```
    Technical depth              People depth
    (can read the                (can hold space
    mechanistic                  for competing
    interpretability             values, hear
    paper and know               what is not
    what it means)               being said)
              \                 /
               \               /
                \             /
                 \           /
                  [  This   ]
                  [ person  ]
                 /           \
                /             \
               /               \
    Knows that before           Can translate
    implementation,             between the
    conversations must          technical and
    have happened               the human
```

**Technical depth:** Can engage seriously with the architecture. Knows that the
similarity function encodes a theory of relevance. Knows that removing the explanation
layer forecloses a value. Can read the mechanistic interpretability paper and know
what it claims and what it does not. Can evaluate whether a training data decision
is sound, not just whether it produces a good benchmark score.

**People depth:** Can hold space for competing values without forcing premature
resolution. Can hear what is not being said — the researcher who says "this looks
fine" but whose hesitation suggests something else. Can map stakeholders and their
values without projecting the designer's own values onto them. Knows that genuine
listening is a skill that takes as long to develop as technical expertise.

**Knows conversations must happen first:** Has internalised that the sequence
matters — that design decisions made before any conversation with affected communities
are bets made without information, and that the cost of getting them wrong is paid
by people who were not in the room. Is not impatient with the planning phase. Sees
the planning phase as the work, not the overhead.

---

## Why Current Training Doesn't Produce This Person

Each of the three capabilities is produced by a different training pipeline.
None of those pipelines produces the other two.

**ML engineering training** optimises for technical depth and speed. Move fast,
ship, iterate. The "people skills" required are mostly about managing stakeholders
to get the project shipped — not genuine value elicitation, not listening for what
is not being said. The metric is the measure. Understanding why the metric improved
is secondary.

**UX research training** optimises for people depth and empirical methods. But it
rarely includes the technical depth to read an architecture and know that a specific
design choice encodes a specific value priority. The technical system is often a
black box that UX researchers are not expected to open.

**Ethics training** produces people who can do conceptual investigation — map
stakeholders, identify value tensions, ask whose interests are missing. But rarely
with the technical depth to engage with the architecture, or the empirical methods
to run the research that would reveal whether the conceptual analysis was right.

The person who can do all three has to assemble themselves from multiple training
paths simultaneously — or be assembled by a life that didn't respect disciplinary
boundaries.

---

## What Actually Forms This Person

Not a degree program, in most cases. The combination tends to emerge from:

**Technical training that produced discomfort with the absence of understanding.**
Not just learning which techniques work, but being troubled by not knowing why.
Asking "what is the model actually doing?" when the field was asking "which model
performs best?" Feeling that "the metric improved" is not a sufficient answer.

**Genuine exposure to people and contexts different from your own.**
Not diversity as a performance — actual sustained exposure to people whose lives
look different, whose values were formed differently, whose problems your technical
training was not designed to address. This is where the people depth comes from.
It cannot be acquired from a workshop.

**Intellectual restlessness that doesn't respect disciplinary walls.**
Following threads wherever they lead — from a technical question to a philosophical
one to a historical one to a political one and back. Discomfort with the idea that
the question you are asking belongs to someone else's field and you should stay in yours.

**Some form of values formation that takes honesty seriously.**
Tarbiyat. Ethical upbringing. Exposure to traditions where truth-telling is a virtue
and flattering is a failure. The discipline that makes the people dimension feel as
important as the technical one — not because it is instrumentally useful but because
it is right.

This combination is not taught. It is formed. Which is why it is rare.

---

## What Happens When This Person Is Absent

**Technical without people:** Products built fast, shipped to users who were not
consulted, discovering value violations through complaint and litigation rather than
through design. The "move fast and fix problems later" model. The cost falls on users.

**People without technical:** Products that sound ethical, that have the right
language, that consulted the right stakeholders — but whose architecture encodes
value priorities that contradict everything the consultation produced. The ethics
is in the documentation. The values are in the code. They do not match.

**Neither, with both claimed:** The principles document that commits to nothing.
The ethics team with no power to stop a launch. The "responsible AI" label on a
product whose mechanism of profit is the harm it claims to prevent.

---

## The Implication for Team Building

You cannot hire this person off a job board under a single title. The Venn diagram
person exists but does not have a name that hiring processes recognise. You find them
by:

- Looking for technical people who ask the wrong questions — who want to know why,
  not just what works
- Looking for people-oriented researchers who are not satisfied with the interface
  and want to understand the system underneath it
- Looking for people whose intellectual biography crosses multiple fields, whose
  curiosity did not stop at the boundary of their training
- Paying attention to who makes you uncomfortable by asking questions you had not
  thought to ask — that discomfort is often the signal

And when you find them: do not optimise them away. The incentive structures of most
organisations — speed, output, measurable deliverables — gradually erode the qualities
that made this person valuable. The planning phase that they know must happen looks
like inefficiency to someone who only measures shipping velocity. Protect the conditions
that let them do the slow work.

---

## Connection to the Knowledge Infrastructure

The Bau Lab knowledge infrastructure project needs this person at every stage — not
just at design time but continuously. The three VSD investigations (conceptual, empirical,
technical) are not a one-time exercise. They are an ongoing practice.

**At design:** Who are the stakeholders? What do they value? What does the architecture
encode? Have the right conversations happened?

**During deployment:** What are researchers actually experiencing? What value tensions
are emerging that the conceptual investigation missed?

**Over time:** As the dataset grows, as new communities are asked to contribute, as
the graph is used in ways nobody anticipated — the same three questions, asked again.

The knowledge infrastructure does not need this person once. It needs this orientation
permanently embedded in how decisions get made.

---

## Key Insight

> The Venn diagram person is rare not because the capability is innately rare,
> but because the training pipelines that produce AI specialists are optimised
> for exactly one of the three dimensions and actively discourage the others.
>
> Technical training rewards speed and metric improvement over understanding.
> People training rarely extends to the architecture.
> Ethics training rarely extends to the empirical or technical.
>
> The person who has all three assembled them through curiosity that didn't
> respect boundaries, exposure that didn't stay comfortable, and values formation
> that made honesty feel as important as efficiency.
>
> When you find this person, the right response is to build the conditions
> that let that combination compound — not the conditions that optimise
> away the parts that look like slowness to people measuring velocity.
