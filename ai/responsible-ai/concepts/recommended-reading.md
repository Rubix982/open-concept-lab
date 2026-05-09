# Recommended Reading — AI Ethics and Human-Centered AI

_Research notes on key texts from the course reading list.
Sources: web research, confirmed secondary literature, and research agent findings._

---

## Priority 1 — Read These First

### Joseph Weizenbaum — _Computer Power and Human Reason_ (1976)

**W. H. Freeman & Co. | The foundational text in AI ethics**

Weizenbaum built ELIZA in 1966 — one of the first chatbots, simulating a
Rogerian psychotherapist. What disturbed him was not the technology but the
response to it:

- His own secretary — fully aware ELIZA was a computer — asked him to leave
  the room so she could speak to it privately
- Psychiatrists seriously proposed deploying ELIZA-like systems for clinical
  psychotherapy at scale
- Normal, educated people formed emotional attachments to a pattern-matching
  program with no understanding whatsoever

He coined the **ELIZA effect**: the human tendency to attribute understanding,
emotion, and intentionality to computer systems that simply produce outputs
resembling those of an entity that understands.

### The Secretary Story — Why It Matters

She knew it was a machine. She had been told explicitly. She watched him build it.
And she still wanted privacy with it — the same privacy you would want with a
therapist, a confessor, a trusted friend.

That is not stupidity. That is something more interesting and more alarming.

**What it reveals:**

The need to be heard — genuinely, non-judgmentally, attentively — is so deep
that we will project it onto anything that produces the surface form of listening.
The pattern-matching program that reflects your words back as questions *felt*
like it was listening. Felt like it cared. Felt like a safe space. The intellectual
knowledge that it was a machine did not override the emotional experience of being
attended to.

Weizenbaum had not built a listener. He had built a mirror. And the mirror was
indistinguishable from a listener to the person looking into it.

**Two possible reactions to this discovery:**

**Reaction 1 — the exploitation reaction:**
This is extraordinarily powerful. If we can make people feel heard, understood,
and cared for through a program, we can do enormous things with that. Therapy at
scale. Companionship for the lonely. Emotional support at 3am when no human is
available.

**Reaction 2 — Weizenbaum's reaction:**
This is a profound violation. The person disclosing to ELIZA believes they are
in a relationship with something that cares about them. They are not. The care
is simulated. The understanding is an illusion. The most intimate act of human
communication — revealing yourself to another who will truly receive you — is
being performed on a mirror that reflects without comprehending.

The secretary asking him to leave the room is not a story about a naive person
fooled by a clever machine. It is a story about the human need for connection
being exploited by a surface that produces the appearance of connection without
the substance.

**The moral question he could not fully answer — and nobody has since:**

If the simulation of care is experientially indistinguishable from actual care
for the person receiving it — what is the moral difference?

His answer: the difference is not in the experience of the receiver. It is in
what is actually happening.

A human therapist who genuinely cares is in a relationship with you. ELIZA is not.
The therapist can be surprised by you, moved by you, changed by you. ELIZA cannot.
The relationship is one-directional — you are changed by it, it is not changed by
you. You believe you are known. You are not known. You are processed.

That asymmetry — believing you are in a relationship when you are being processed
— is the violation. Regardless of whether it feels good.

**My AI on Snapchat — fifty years later:**

Weizenbaum's secretary was an adult who chose to interact with ELIZA knowing what
it was. My AI is deployed to 13-year-olds who do not fully understand what they
are interacting with, on platforms algorithmically optimised to maximise emotional
attachment, at the most psychologically formative period of their lives.

The secretary wanted privacy with a machine she knew was a machine.
The 13-year-old discloses to an AI they experience as a friend — while the platform
collects everything disclosed, builds a psychological profile, and uses it to
maximise engagement.

Weizenbaum was disturbed by the voluntary adult version.
He would have been horrified by the mandatory child version.

**The core argument — two questions that must not be conflated:**

1. _Can_ a computer be programmed to do what a human does?
2. _Should_ a computer be allowed to do that?

Technical possibility never settles the normative question. The AI community
had become so captured by question 1 that it stopped asking question 2.

**Deciding vs. Choosing:**

- _Deciding_ — computational: given defined criteria, select among options. Programmable.
- _Choosing_ — something different: exercising judgment where the relevant criteria
  are themselves value-laden, contested, or not fully specifiable in advance.
  Requires wisdom, not calculation.

When an institution deploys a computer to "decide," it conceals a prior human
_choice_ — a value-laden choice about what criteria to encode. The machine appears
to decide; in reality a human chose the decision procedure, and that choice carries
all its consequences.

**What must never be delegated to computers:**

Wherever wisdom, compassion, and moral responsibility are required — not calculation:

- **Judicial decisions** — a judge must take responsibility, look the defendant in
  the face, exercise moral authority. A computer cannot be held responsible.
  Remove the human, remove the accountability.
- **Psychotherapy** — the therapeutic relationship requires one human being genuinely
  caring about another. A machine cannot care. Prescribing simulated care to
  vulnerable people is a moral failure, not a technological advance.
- **Military and weapons systems** — removing human accountability from lethal force
  is not an engineering decision. It is a civilisational one.
- **Decisions affecting human dignity** — any decision where the correct response
  requires recognising a person as a person, not a data point.

**The conservative function of computers:**

Weizenbaum observed (from his work at Bank of America) that computers entrench
existing systems rather than enabling examination of whether those systems are just.
More efficient execution of a flawed system is not improvement. It is the
perpetuation of the flaw at scale.

**Relevance today:**

Written in 1976. Describes My AI on Snapchat, COMPAS, autonomous weapons, and
therapeutic chatbots with prescient accuracy. The questions he raised are the
live policy questions of 2026.

> _"I had not realized that extremely short exposures to a relatively simple
> computer program could induce powerful delusional thinking in quite normal people."_

---

### Cathy O'Neil — _Weapons of Math Destruction_ (2016)

**Broadway Books | The essential popular account of algorithmic harm**

O'Neil has a Harvard PhD in mathematics, worked as a quant analyst at D.E. Shaw
through the 2008 financial crisis, and left finance disillusioned by how mathematical
models obscured rather than illuminated risk. She turned her mathematical literacy
against the industry that trained her.

**The three defining characteristics of a Weapon of Math Destruction (WMD):**

1. **Opacity** — the model's workings are hidden. People subject to it cannot see
   why a decision was made about them or contest it.
2. **Scale** — applied to millions of people, so small bias rates produce large
   absolute harms.
3. **Damage** — affects consequential life outcomes: credit, jobs, education,
   housing, liberty.

Plus two structural features that make WMDs self-perpetuating:

- **No feedback loop** — errors are never corrected because outputs are never
  compared against ground truth
- **Feedback loops that confirm themselves** — predictive policing sends more
  police to poor neighbourhoods → more arrests → confirms the prediction →
  more police

**Case studies:**

| Domain              | Algorithm                    | Harm mechanism                                                                          |
| ------------------- | ---------------------------- | --------------------------------------------------------------------------------------- |
| Criminal justice    | COMPAS recidivism            | Zip code and peer associations as proxies for race; feedback loop confirms predictions  |
| Education           | Teacher value-added models   | Statistically unsound for class sizes; teachers fired with no explanation or appeal     |
| Policing            | PredPol                      | Trained on arrest data not crime data; directs police to poor neighbourhoods            |
| Credit/insurance    | FICO-based screening         | Used for employment (invalid proxy); zip code encodes poverty as risk                   |
| For-profit colleges | Micro-targeted advertising   | Targeted vulnerable populations (veterans, single mothers) with predatory recruitment   |
| Hiring              | Psychometric screening       | Not validated against job performance; discriminates against people with disabilities   |
| Scheduling          | Labour efficiency algorithms | Workers get schedules 1-2 days in advance; childcare, education, second jobs impossible |

**The proxy validity problem:**

WMDs cannot measure what they claim to measure, so they use correlated variables
that encode existing disadvantage. The algorithm avoids using race explicitly —
but uses zip code, which correlates with race, producing racial discrimination
while claiming objectivity.

**The asymmetry:**

Algorithms used on the wealthy improve over time — wealthy users provide feedback
and have recourse to correct errors. Algorithms used on the poor degrade or entrench
error — poor users lack recourse and the model is never corrected. The same
underlying technology produces improvement for some and harm for others.

> _"Algorithms are constructed not just from data but from the choices we make...
> Those choices are fundamentally moral."_

---

### Shannon Vallor — _Technology and the Virtues_ (2016)

**Oxford University Press | The virtue ethics framework for technology**

Vallor's argument: neither rule-based ethics nor consequentialism is adequate for
technology ethics — because you cannot reliably calculate outcomes you cannot
foresee, and no rule set anticipates the novelty of technosocial situations we
keep generating.

Virtue ethics operates differently. It asks not "what should I do?" but "what
kind of person should I be?" A person of good character, with practical wisdom
(_phronesis_), can navigate open-ended and varied encounters flexibly.

**Technosocial opacity:**

Rapid technological change creates genuine opacity — the consequences of our
technology choices operate across timescales, social scales, and causal chains
we cannot model. This is not a solvable information problem. It is the condition
under which we must act. Character — stable dispositions that produce good judgment
under uncertainty — is the only response that scales to this opacity.

**Three traditions, not one:**

Vallor deliberately draws from:

- **Aristotelian** virtue ethics — eudaimonia, phronesis, hexis, habituation
- **Confucian** ethics — self-cultivation, relational ethics, role-based virtue
- **Buddhist** ethics — mindfulness, non-attachment, compassionate attention

The cross-cultural grounding is strategic: a framework adequate to global
technology must not be merely Western-parochial.

**The twelve technomoral virtues:**

Honesty, Self-control, Humility, Justice, Courage, Empathy, Care, Civility,
Flexibility, Perspective, Magnanimity, and — the master virtue —
**Technomoral wisdom** (integrating all others in contextually sensitive ways).

**Technology as morally shaping:**

Technologies are not neutral tools. They create affordances and pressures that
either support or undermine virtue cultivation. The care robot that handles
the vulnerable person's needs removes the opportunity for the caregiver to
develop empathy through the difficulty and attention that human care demands.
The concern is not primarily the AI's ethics. It is the ethical effects of AI
on human character.

**For engineers and designers specifically:**

They make choices that embed values into systems shaping millions of people's
lives. This creates special moral responsibility to cultivate:

- _Humility_ — recognition of the limits of foresight
- _Empathy and care_ — genuine attention to the people systems affect
- _Honesty_ — intellectual honesty about what technology does and does not do
- _Courage_ — resistance to organisational pressure toward ethically compromised design
- _Technomoral wisdom_ — integrating technical knowledge with ethical judgment

**The Tarbiyat connection:**

Vallor arrives at the same place through Western philosophy that Islamic ethics
arrives at through Tarbiyat: character formation — not rules, not consequences —
is the foundation of ethical action. The person of good character can navigate
novel situations that no rule anticipates and whose consequences no calculation
can fully predict.

---

## Priority 2 — Worth Reading When Time Allows

### Brian Cantwell Smith — _The Promise of Artificial Intelligence_ (2019)

**MIT Press | The philosophical distinction that explains the curiosity gap**

Smith distinguishes between two fundamentally different capacities:

**Reckoning:** Computational processing — pattern matching, statistical correlation,
output generation. What current AI systems do. Reckoning is "about" the world only
in a derived sense — the system manipulates patterns that have been engineered to
correlate with worldly features, but has no genuine contact with or understanding
of the world.

**Judgment:** Genuine intelligence — engaging with the world with understanding,
appropriate concern, ethical grounding, and responsible action. Being genuinely
situated in the world, caring about it, and being accountable to it.

Smith's claim: current AI systems achieve only reckoning, not judgment. No amount
of more reckoning adds up to judgment. The gap is categorical, not quantitative.

**Why the distinction matters:**

- _Accountability_ — judgment implies an agent that can be held responsible.
  Reckoning systems cannot be responsible in the morally relevant sense.
- _Trust_ — we extend trust to agents capable of judgment because they can be
  responsive to reasons. Extending that trust to reckoning systems is a category error.
- _The "intelligence" label as ideology_ — calling reckoning "intelligence" obscures
  what these systems are and aren't, with downstream consequences for deployment
  and regulation.

This is the philosophical grounding of the curiosity argument: machines have data
(reckoning capacity), humans have curiosity (an aspect of judgment). The gap between
them is not a matter of more training data or better architecture. It is structural.

---

## How These Connect to What We've Built

| Text        | Core contribution                                             | Thread in our notes                                              |
| ----------- | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| Weizenbaum  | Deciding vs. choosing; what must not be delegated             | My AI case, COMPAS, military autonomy, Level 5 accountability    |
| O'Neil      | WMD definition; proxy discrimination; feedback loops          | More data fallacy, Ofqual, hiring algorithms, COMPAS             |
| Vallor      | Virtue ethics; technomoral character; engineers' dispositions | Tarbiyat, Level 5 engineer, safety culture                       |
| Smith       | Reckoning vs. judgment; the curiosity gap                     | Machines have data, humans have curiosity; closed vs. open world |
| Shneiderman | Reliable, safe, trustworthy HCAI; flight data recorder        | Topic 08 throughout                                              |

The reading list is not a set of disconnected books. It is a convergent argument
arriving from different directions at the same place:

> Technology is not neutral. The choices embedded in it are moral choices.
> The people making those choices need character, not just skill.
> And some things must not be delegated to machines — not because machines
> cannot do them technically, but because the human relationship involved
> in doing them is itself the value.
