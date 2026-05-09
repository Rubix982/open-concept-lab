# Human-Centered AI and Broken Systems

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The UK Grading Algorithm — AI as Mirror, Not Cause

In 2020, the UK's Ofqual algorithm attempted to grade A-level students during
COVID-19 when exams could not be held. The algorithm:

- Looked at the school's historical grade distribution
- Used prior attainment data mapped across England
- Predicted current students' grades based on their school's historical performance
- Ranked students and assigned grades accordingly

**The outcome:**
- Over 40% of students received lower grades than their teachers predicted
- Only 2% received higher grades
- The majority of downgraded students were from poor, non-white communities
- Private schools were systematically favoured
- The government reversed course two days before final release under public backlash

**What the algorithm actually did:**

It took the school's resource poverty and encoded it as the individual student's
academic ceiling. A student at an underfunded school, who achieved the same raw
performance as a student at a well-funded school, was pulled down toward their
school's historical average — an average produced by historical underfunding,
not by the capabilities of the current student.

**The self-fulfilling prophecy mechanism:**

```
Underfunded school → lower historical grades
        ↓
Algorithm predicts lower grades for current students
        ↓
Lower grades assigned → students denied university places
        ↓
School's graduates have worse outcomes
        ↓
Next year's algorithm sees confirmed low historical performance
        ↓
Ceiling is lowered further
        ↓
Repeat
```

The algorithm did not create educational inequality in Britain. It operationalised
it — encoded it mechanically, applied it at scale, and made it feel like a natural
fact rather than a political choice.

---

## Applied to Pakistan — The Cost Gap

In Pakistan, the cost of secondary education varies enormously:

- Government / basic private intermediate school: ~5,000 PKR per month
- Private O/A-levels school: 35,000-40,000 PKR per month — sometimes more

This is not primarily a difference in student capability. It is a difference in:

- Teaching quality — better paid, better trained, better resourced teachers
- Infrastructure — functional labs, libraries, reliable electricity
- Exam preparation — dedicated coaching, past papers, structured revision
- Peer environment — students from more stable home conditions
- Social capital — networks, connections, references

**The signal the cost gap actually carries:**

A student at the 5,000 PKR school who achieves the same grade as a student at
the 40,000 PKR school has demonstrated something categorically different. They
produced equal output with a fraction of the input. That is a signal of
exceptional capability — not equal capability.

An Ofqual-style algorithm would invert this. It would see the 5,000 PKR school's
lower historical average and pull the high-achieving student's grade down toward
it. The school's resource poverty becomes the student's personal ceiling.
The student who overcame the constraint is penalised for the constraint.

**The connection to hiring:**

The 3.1 GPA student working part time while studying — identified as the stronger
hire — is the same profile. Equal or better output under unequal conditions.
The algorithm sees equal output and assigns the lower-resourced student a lower
predicted grade because the school's history pulls them down.

The correct instinct — finding the part-time working student more impressive —
is the right correction. The algorithm does the opposite at scale and calls it objectivity.

---

## The GRE as Barrier of Entry

The GRE costs $220. TOEFL costs $220. Each university application costs $150+.
Score reports cost additional fees. Preparation materials cost hundreds more.

Before a single person reads your application, you have spent $2,000-3,000 minimum
— just to be considered. From Karachi, that sum represents months of middle-class
income. From Connecticut, it is a minor inconvenience.

**The price is not set by cost.**

ETS's actual cost to deliver a computer-based test is a fraction of $220. The price
is set by what the market can bear from people who have no alternative — because
universities require it, because ETS has a near-monopoly, because the applicant
has no leverage. The high price is not a side effect of operational costs. It is
a filter. It filters by family wealth before the test begins.

**The compounding barrier:**

- $220 GRE + $220 TOEFL
- $150+ per university application × 8-12 schools
- $200-400 for score reports
- Coaching and preparation materials: $500-1,000+
- Travel and accommodation if test centre is not local

Total: $2,000-4,000 before consideration begins.

**The self-selection filter before the filter:**

Many capable students from Pakistan, Nigeria, Bangladesh, Indonesia — who would
succeed in US graduate programs — never apply. Not because they are incapable.
Because the application cost is too high to attempt. The most capable students
who cannot afford the barrier self-select out before any algorithm ever sees
their application.

The algorithm's dataset is already filtered by wealth before it runs.
It learns from a population that already passed the financial filter.
It encodes that filter as capability.

**What the GRE actually measures:**

- Academic preparation, yes
- Analytical reasoning developed over years, yes
- But also:
  - Access to test preparation resources
  - Freedom from financial stress on test day
  - Ability to retake when underperforming — another $220
  - Cultural familiarity with standardised American testing format
  - Whether preparation coaching — which inflates scores 10-15 percentile points
    — was affordable

None of those are capability. All correlate with wealth. The score bundles them
together and presents the bundle as a single neutral measure.

**The natural experiment:**

COVID forced many universities to suspend GRE requirements 2020-2022. The result:
- Applicant pools became more diverse
- Admitted students performed as well or better
- GRE turned out to be a weaker predictor of graduate success than GPA and letters
- Several universities permanently dropped the requirement

The test was presented as a necessary measure of capability. The experiment showed
it was partly a financial filter that produced the appearance of academic selection.

---

## AI as Entry Point — The Precise Framing

AI did not create these systems. It revealed them — mechanically, at scale,
visibly enough that they became undeniable.

| AI system | What it revealed | What actually needs to change |
|---|---|---|
| Ofqual grading algorithm | School funding inequality encoded as individual destiny | School funding policy, resource allocation, structural inequality |
| COMPAS recidivism tool | Racial disparity in criminal justice encoded as risk score | Criminal justice system, policing policy, sentencing structures |
| Amazon hiring algorithm | Gender discrimination in tech encoded as hiring preference | Industry culture, pipeline access, pay equity enforcement |
| Image generation models | Western cultural dominance in knowledge representation | Dataset construction, cultural partnership, representation infrastructure |
| GRE score cutoffs | Financial barrier encoded as academic merit | Test cost regulation, monopoly breakup, alternative admission pathways |

In every case: the algorithm is downstream of the social system. Fixing the
algorithm without fixing the social system produces a cleaner-looking algorithm
that still encodes the same underlying structure.

**But the algorithm made the conversation possible.**

Before Ofqual, the inequality was diffuse, invisible, distributed across millions
of individual decisions. After Ofqual, it was concentrated, visible, in a single
technical system that people could point at and say: this is wrong, and here is why.

The algorithm is an entry point to the conversation the system needed to have
with itself. The algorithm loses. The conversation should continue — toward the system.

---

## The Two Incomplete Positions

**Position 1 — "AI is racist/sexist/biased" as the complete critique:**

Correct that the algorithm is wrong. Incomplete because it stops at the entry point
and does not follow the thread to where the wrong actually lives — in the political
choices, resource allocation decisions, and historical patterns the algorithm learned.

Fixing the algorithm without fixing the system produces a cleaner-looking algorithm
that encodes the same underlying inequality more invisibly.

**Position 2 — "AI just reflects society, don't blame the tool":**

Correct that the algorithm did not create the problem. Wrong to use that as a reason
not to fix the algorithm — because the algorithm is now part of the system, and the
system includes the algorithm.

Also wrong because "just reflecting society" understates what the algorithm does.
It does not passively reflect. It actively encodes, scales, automates, and
legitimises — converting a political choice into what feels like a natural fact.

**The complete position:**

The algorithm is wrong and should be fixed. Fixing the algorithm is not sufficient.
The conversation the algorithm started should be directed at the system that produced it.

AI is the entry point. The system is the conversation. The system is what needs to change.

---

## The Self-Fulfilling Prophecy — Why Algorithms Make It Worse

A human evaluator who gives a student a lower grade because of their school's
history is making a biased judgment that can be challenged, overridden, appealed.

An algorithm that does the same thing is making an "objective" determination that
feels like a fact. The bias is harder to see, harder to challenge, and harder to
appeal. The legitimacy of the technical process obscures the political choice embedded in it.

Worse: the algorithm's outputs become the next generation's training data.
The suppressed grades confirm the historical pattern. The historical pattern
justifies the next suppression. The ceiling lowers with every iteration —
all while the system reports increasing accuracy.

This is the self-fulfilling prophecy mechanism at scale. Not a bug. A structural
feature of systems that learn from outcomes they themselves produced.

---

## Human-Centered AI — What It Actually Requires

The module's concept of human-centered AI — keeping humans in the loop —
is necessary but not sufficient in broken systems.

A human reviewing Ofqual's algorithmic grades is still reviewing grades shaped
by a funding system the human did not design and cannot override. The human in
the loop inherits the system's constraints.

Truly human-centered AI in broken systems requires:

- **Transparency** about what the algorithm is actually measuring vs. what it
  claims to measure
- **Disaggregated evaluation** — who is the algorithm right about, and who is it
  wrong about, and does that pattern correlate with historical inequality
- **Override mechanisms with real authority** — not rubber-stamping, genuine power
  to correct
- **Upstream accountability** — the algorithm's designers accountable for the
  social effects of their design choices, not just the technical accuracy
- **System-level questioning** — when the algorithm reveals a pattern, following
  it to its source rather than fixing the symptom

Most importantly: **centering the humans who are harmed, not just the humans who
are using the tool.**

The Ofqual algorithm was human-centered in that teachers were consulted, officials
reviewed the design, and the government approved it. None of those humans were the
students in underfunded schools whose futures were being determined. Human-centered
AI that does not centre the affected humans is just stakeholder management with
better branding.

---

## Key Insight

> AI did not create the gap between the 5,000 PKR school and the 40,000 PKR school.
> AI did not create the $220 GRE barrier that filters by wealth before measuring capability.
> AI did not create the inequality that Ofqual's algorithm encoded as destiny.
>
> AI made these things visible, mechanical, and undeniable.
> That visibility is an opportunity — if we follow it to the right place.
>
> The right place is not the algorithm.
> The right place is the system that produced the data the algorithm learned from,
> the political choices that created the inequality the algorithm reflected,
> and the people with the power to change those choices who have not yet been
> made sufficiently uncomfortable to do so.
>
> AI is the entry point. The system is the conversation.

---

## Connections

- *Topic 07 — Fairness and Bias* — the more data fallacy: adding more data from
  a biased distribution amplifies the problem; the Ofqual case is the live example
- *Concept — Rawls and Distributive Justice* — the veil of ignorance test: would
  you design the Ofqual algorithm if you did not know which school you would be in?
- *Concept — Goodhart's Law* — GRE scores became a target; they ceased to measure
  what they were supposed to measure
- *Concept — Environmental cost of AI* — the same sequential build argument applies:
  deploy incrementally, measure effects, do not scale before you understand what you
  are scaling
- *Concept — Ethics as defanging* — "human-centered AI" can be used the same way
  "ethical AI" is: to produce the appearance of human consideration without the
  structural accountability that would make it real
