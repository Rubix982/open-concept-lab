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

## Rationalism vs. Empiricism — The Philosophical Root of HCAI

The difference between standard AI and Human-Centered AI reflects a deeper
philosophical divide between two ways of knowing the world.

### The Rationalist Position — Aristotle, Descartes, Fisher

Rationalists believe in logical thinking, formal methods, and well-defined
categories. Rules can be perfected. Boundaries between categories are stable.
The world can be understood from first principles, in the comfort of the lab,
without necessarily going into the messy real world.

In AI, rationalism produces: elegant algorithms, statistical methods, the belief
that machine learning is sufficient to match human intelligence on well-defined
tasks, and the conclusion that correlations strong enough to guide decisions make
causal understanding unnecessary.

**The failure mode:** Ronald Fisher — one of the most important statisticians of
the 20th century — rejected early data on the risks of smoking because it did not
fit his rigid statistical framework. The framework was more trusted than the evidence.
The rigidity of the categories prevented seeing what the data was actually showing.

### The Empiricist Position — da Vinci, Galileo, Hume, Tukey

Empiricists believe that researchers are enriched by contradictions and ambiguities
that come with real-world experience. Beliefs must be continuously refined in response
to changing realities. Categories are provisional. Middle grounds matter.

Da Vinci developed fluid dynamics by watching water flow around obstacles — not by
deriving it from first principles. Galileo noticed a chandelier swaying in church
and followed the observation to the formula for pendulum swing. John Tukey insisted
on looking at data graphically because visual inspection reveals errors, anomalies,
and unexpected distributions that summary statistics hide.

**In HCAI, empiricism produces:** assessment of human performance in real contexts,
questioning of simple dichotomies, observation of how people actually interact with
systems rather than how they were designed to interact.

---

## Machines Have Data. Humans Have Curiosity.

This is the precise epistemological divide.

**Curiosity is not a personality trait. It is an epistemological stance.**

The curious person notices the gap between what they know and what is — and is
pulled toward it. The gap is not uncomfortable. It is interesting. Curiosity is
an active relationship to not-knowing that produces seeking.

**The machine has no relationship to not-knowing.**

It has a training distribution. When it encounters something outside that distribution
— the white truck against a white sky, the flu search pattern that shifted, the
candidate who does not fit the historical profile — it does not notice the gap.
It does not feel the pull toward investigation. It produces a confident output
from the nearest available pattern.

**The Tesla case:**

Tesla's self-driving car could not distinguish a white truck from a white sky
and drove into it. The algorithm produced certainty where there should have been
uncertainty. A human driver with impaired vision in those conditions would feel
uncertainty — would slow down, look again, ask for confirmation. The uncertainty
would produce caution.

The algorithm did not know it did not know. That is the precise failure.

**The Google Flu Trends case:**

The model predicted flu outbreaks by studying patterns of internet search queries.
It worked while the world stayed still. When search behaviour shifted and Google's
own algorithms changed, the model kept predicting based on a pattern that no longer
existed. It repeated the past in a present that had moved on.

A human epidemiologist watching predictions diverge from actual flu rates would
notice something is wrong, ask why, investigate whether underlying behaviour had
changed, and update or abandon the model.

The algorithm kept producing confident predictions until Google shut it down.

**Machines have data. Often limited data. With no pure or set amount of beliefs in them.**

The data reflects a specific slice of the world, observed from specific positions,
at specific times, through specific instruments. The limitation is not random.
It is structured by who had access to produce data, who had incentive to collect it,
and what categories were used to organise it.

The model does not know the limits of its own knowledge. It cannot ask what it is
not seeing. It cannot notice that the data is thin at the edges of its training
distribution. It produces confident outputs even there — sometimes especially there,
because the nearest pattern is pulled from a slightly different context and applied
as if appropriate.

---

## Closed World vs. Open World — The Deeper Divide

**Closed world assumption:** the world contains only what the training data contains.
Categories are fixed. The past predicts the future. Novel cases are handled by
finding the nearest known case.

**Open world assumption:** the world contains things not yet observed. Categories
are provisional. The future may differ from the past in ways that matter.
Novel cases are an invitation to learn.

Current ML is almost entirely closed world. It learns from what it was shown.
It cannot imagine what it was not shown. It cannot ask whether the categories
it learned are the right ones. It cannot notice that the world has changed
in ways its categories do not capture.

Da Vinci watching water flow around obstacles was doing open world reasoning.
He did not assume he already knew what water does. He watched. He noticed.
He revised. The watching was the method because reality was the source of truth,
not the prior model.

The empiricist correction to AI is the reintroduction of the open world assumption —
keeping the human in a position where they can notice when the map does not match
the territory, and act on that noticing.

---

## What Human-in-the-Loop Actually Requires

Human-centered AI, in the empiricist tradition, is an attempt to reintroduce the
open world assumption. The human — with curiosity, with the capacity to notice gaps,
with the ability to ask "why is this wrong?" — must be in a position to correct
the machine's closed world confidence with open world observation.

**The machine maps patterns.**
**The human notices when the map does not match the territory.**

The human's job is not to rubber-stamp the machine's output. It is to be the
curiosity that the machine lacks — the active not-knowing that pulls toward
investigation when the output feels wrong.

This only works if:

- The human has **genuine authority to override** — not the appearance of oversight
  while the algorithm's output is the default
- The human has **genuine time to notice** — not 300 decisions per hour where
  noticing is structurally impossible
- The human has **genuine freedom from pressure** to accept the machine's confident
  output as faster and easier than their own uncertain judgment
- The human is **the right human** — someone who could be on the receiving end
  of the decision, not just someone at the comfortable end of the system

A human reviewer who lacks any of these is not in the loop in the meaningful sense.
They are providing the appearance of human oversight while the machine's closed world
assumption governs every consequential decision.

---

## HCAI as Civilisational Project — Flipping the Objective Function

At first glance the reading's dishwasher example looks like a product design argument.
It is not. It is a values argument dressed as a design argument.

### The Dishwasher Example — Design Encoding Values

**The robot that clears the table:**
Efficient. Removes inconvenience. Delivers service to a passive recipient.
Encodes the value: the elderly person's problem is inefficiency, and the goal
is to remove it. The person becomes a problem to be solved.

**The small dishwasher built into the table:**
Less efficient. Preserves the person's ability to do something themselves,
for themselves, in their own space. Encodes the value: self-efficacy matters
more than optimised service delivery. The person remains an agent.

The design choice is not about dishwashers. It is about what the person's
dignity requires and what kind of society produces that design instinctively.

**The rationalist AI objective function:**
Maximise efficiency of service delivery to passive recipients.

**The HCAI objective function:**
Maximise human agency, dignity, and social connectedness for everyone involved
— including the people delivering the service, not just receiving it.

These are not the same objective. They produce radically different designs.
Choosing between them is not a technical decision. It is a political and moral
decision about what society is for.

### The Meals on Wheels Example — The Relationship Is the Product

The delivery person who brings food, checks on the recipient, clears the table,
has a conversation — is not delivering a service. They are sustaining a social
relationship. The food is the occasion. The relationship is the value.

An automated delivery drone that drops a meal at the door is more efficient.
It completely misses the point.

**If you optimise for efficiency in caregiving, you destroy caregiving.**

Caregiving is not fundamentally an efficiency problem. It is a human relationship
problem. The relationship is the product. Automating the delivery automates away
the thing that made it valuable.

The HCAI algorithm that matches deliverer and recipient personalities, builds
long-term commitments, enables recipients to publicly praise caregivers — this
is not a scheduling tool. It is a community infrastructure tool. It is trying to
rebuild the social fabric that industrial modernity eroded by treating human care
as a cost to be minimised rather than a value to be cultivated.

### The Accountability Framework — Flight Data Recorders for AI

The reading proposes: every consequential AI system should have the equivalent
of a flight data recorder. Logging activity. Audit trails. Retrospective review
of failures and near misses. Transparent accountability.

Civil aviation's commitment to continual improvement after every incident —
regardless of whose fault, regardless of liability — produced the safest
mass transportation system in history. Not through blame. Through systematic
learning from failure.

The same approach applied to AI systems with significant consequences —
hospital decisions, battlefield systems, criminal justice tools, hiring algorithms
— would require:

- Every consequential decision logged with the inputs that produced it
- Retrospective review when outcomes are poor
- Aggregate pattern analysis that identifies systematic failures
- Public accountability for what the analysis reveals
- Design improvement required as a condition of continued operation

This is not surveillance of the AI. It is the empiricist approach applied to
AI governance — learn from what actually happens, update based on what you find,
never assume the system is working correctly just because it is running.

### Military and Autonomous Systems — No Full Autonomy

The reading is explicit: even when the case for autonomy in defensive systems
is strong, no weapons systems should be fully autonomous.

This is the accountability argument applied to its hardest case. A fully autonomous
weapons system that makes kill decisions without human involvement has no
accountability chain. There is no human who can be asked: why did you decide this?
There is no moment at which human judgment was exercised and can be reviewed.

The flight data recorder cannot help if there was no human in the chain to be
accountable. Accountability requires an agent. Algorithms are not agents.
The human must remain in the loop precisely where the consequences are most severe
— because that is where accountability matters most, and where the temptation to
remove it in the name of speed and efficiency is strongest.

### The Society the HCAI Vision Implies

The reading is not proposing a product. It is proposing a different civilisational
direction — one where technology's role is to enrich human agency and social
connectedness rather than to replace human participation.

**What this requires at the values level:**

The rationalist AI treats elderly people, people with disabilities, and caregivers
as passive targets of automation — problems to be solved efficiently. The HCAI
approach treats them as people with dignity, agency, and social needs — people
whose lives can be enriched through technology that serves rather than replaces
their humanity.

That distinction is not a design principle. It is a character principle. It reflects
what you believe about the value of human beings — whether their value is in their
productivity and self-sufficiency, or in their inherent dignity as persons who
deserve agency, relationship, and community regardless of their productive capacity.

**The Tarbiyat connection:**

The society that designs the robot to clear the table has decided efficiency is
the value. The society that designs the table with the dishwasher built in has
decided dignity is the value. The society that funds and celebrates Meals on Wheels
delivery as community care has decided relationship is the value.

These decisions are not made in product meetings. They are made in the formation
of character — individual and collective — about what matters and why. Technology
encodes those decisions at scale and makes them structural. Which is why the
technology conversation is ultimately a values conversation, and why responsible
AI is ultimately a civilisational project, not a product design problem.

**The objective function is the question:**

Not "how do we make this system more accurate?"
But "what is this system for, and for whom, and what kind of society does it produce?"

That question requires exactly the normative clarity the course has been building
toward — names values, names whose values, names the tradeoffs, names who bears
the cost of the choice made.

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

## The Software Engineering Talent Pyramid — What HCAI Actually Requires

The reading calls for: testing software to check AI algorithms, visual tools to
reveal anomalies, testing databases to enhance fairness, flight data recording
for retrospective forensic analysis, explainable AI, visual control panels.

Every one of these requires someone who is actively looking for what is wrong
before it becomes a problem. Someone with empiricist instincts applied to
engineering. That person is rare. The talent pyramid explains why.

### The Four Levels

```
Level 4 — Identifies problems before starting and articulates them clearly
           ↑ rarest, most valuable, least measured by any hiring process
Level 3 — Can lead other people doing Levels 1 and 2
           ↑ requires technical depth + human understanding simultaneously
Level 2 — Actually gets work done
           ↑ completely different skill from Level 1, rarely taught
Level 1 — Can write code that works
           ↑ what hiring algorithms select for
```

Each level is roughly an order of magnitude rarer than the previous one.

### The Gap Between Level 1 and Level 2

Writing code that works in isolation is a tractable skill. LeetCode measures
a version of it. University teaches a version of it. It can be learned.

Getting work done means:
- Understanding what is actually being asked, not just the literal specification
- Identifying when the specification is ambiguous or wrong before building the wrong thing
- Managing your own time and attention without external structure
- Knowing when you are stuck and need help vs. when to push through
- Delivering something that solves the actual problem, not the stated problem
- Communicating clearly about progress and blockers without being asked

None of these are taught. None appear on a resume. None are measured by any
hiring algorithm. They emerge from the 3.1 GPA student working part time —
who had to manage competing demands and limited resources and still deliver —
not from the gold medalist who optimised for a single metric in ideal conditions.

### Level 3 — Leading People

Requires everything from Level 2, plus:
- Understanding that other people think differently
- Explaining not just what to do but why
- Knowing when to direct and when to ask
- Holding people accountable without demoralising them
- Absorbing organisational pressure without transmitting it downward as anxiety
- Building an environment where Level 4 thinking is possible

The technical people who develop this are extremely valuable. Most organisations
do not know how to identify them in hiring or retain them once found.

### Level 4 — Finding Issues Before Starting

This is the da Vinci instinct applied to engineering. The person who reads the
specification, sits with it, and then says:

*"Before we start, I want to flag three things that are unclear, two assumptions
that might be wrong, and one dependency we haven't accounted for."*

That conversation, had before any code is written, saves weeks of rework.
It requires:

- Enough experience to know what goes wrong and when
- Enough confidence to raise concerns without knowing if they will be welcomed
- Enough intellectual honesty to say "I don't know" rather than assume
- Enough systems thinking to see the work in its broader context
- The Tarbiyat to prioritise truth over the appearance of readiness

**This is exactly what the HCAI framework requires.** Fairness testing, anomaly
detection, database auditing for bias, retrospective forensic analysis — all of
these are Level 4 activities. They require someone who is actively looking for
what is wrong before it becomes a problem. Who treats systems with empiricist
skepticism rather than rationalist confidence.

Level 4 engineers are the da Vincis of software. They are rare.

### Why the Hiring Process Systematically Fails to Find Them

- **Algorithms** filter for Level 1 — keywords, credentials, LeetCode scores
- **Level 2** is invisible on a resume — it shows up in output over time
- **Level 3** is demonstrated in how teams function — not in an interview
- **Level 4** emerges in conversation about problems — not in a coding challenge

The organisation that most needs Level 4 thinking — one building consequential
AI systems with real fairness, accountability, and transparency requirements —
is using a hiring process that selects against the people who can provide it.

### What Actually Finds Level 4

- Referrals from people who have worked alongside them — judgment becomes
  visible through shared work over time
- Conversations designed to reveal how someone thinks about problems, not whether
  they can solve predefined ones
- Work samples with ambiguous specifications — the response to ambiguity reveals
  more than the solution to a defined problem
- The Bau Lab model — where you work alongside people and their thinking becomes
  visible through the work itself

The algorithm cannot find this. The credential cannot signal it.
The interview can reveal it — but only if the interview is designed to.
Most interviews are not.

---

## Level 5 — The Engineer Who Makes Safety Culture Real

The reading lists the mechanisms of safety culture: incident reporting, suggestion
boxes, voluntary standards, adverse event systems. All assume the person who sees
the problem will report it. None address the structural question:

**Is it actually safe to report?**

### The Psychological Safety Gap

Every organisation that has had a catastrophic safety failure had, in retrospect,
people who knew something was wrong before the failure happened.

- **Challenger (1986):** Engineers at Morton Thiokol explicitly recommended against
  launch in cold temperatures. They were overridden by management under schedule
  pressure. Seven lives. Program delayed years. Congressional investigations.
- **Columbia (2003):** Engineers raised concerns about foam strike damage.
  Concerns were minimised. Seven more lives.
- **Boeing 737 MAX (2018-2019):** Engineers raised concerns about the MCAS system.
  Overridden. Two crashes. 346 deaths. $20+ billion in costs. Reputational damage
  that persists years later.
- **Deepwater Horizon (2010):** Multiple warning signs raised and overridden.
  Eleven deaths. Largest marine oil spill in history.

In every case: someone knew. In every case: the cost of listening would have been
a delay. In every case: the cost of not listening was catastrophic.

The suggestion box is a trap without immunity. It identifies you as the person
who sees problems — which in many organisations means you are the person who
causes delays, raises uncomfortable questions, and makes leadership look bad.
The rational calculation becomes: reporting costs me something, silence costs me
nothing until the failure happens.

### Level 5 — Institutional Courage as Engineering Skill

```
Level 5 — Creates the conditions where Levels 1-4 can function honestly
           Speaks up when safety is compromised
           Points out issues before they become failures
           Produces proactive reports and evidence
           Makes it structurally safe for others to do the same
           ↑ requires everything below plus institutional courage
```

Level 5 requires:

- **Institutional courage** — raising concerns knowing they may not be welcomed,
  may slow things down, may make you unpopular with people who control your career
- **Evidentiary discipline** — not just "I think something is wrong" but "here is
  the data, here is what I predict will happen, here is what I recommend"
- **Political sophistication** — raising concerns in a way that can actually be
  heard, not just technically correct but practically effective
- **Tolerance for being wrong** — sometimes the concern turns out to be unfounded;
  you must be willing to have been wrong publicly without it destroying your
  willingness to raise the next concern

**This is the Tarbiyat dimension applied to engineering.**

The engineer who raises the safety concern knows that the correct answer may delay
the launch, cost money, make leadership uncomfortable, and put them in conflict
with the people who control their career.

The person raised to please will not raise the concern. Or will raise it so softly
it can be ignored. Or will raise it once, be pressured, and withdraw.

The person with Tarbiyat raises the concern clearly, documents it, and does not
withdraw it when pressured — not to cause problems, but because their silence
is a choice with consequences that others will bear.

### The Business Case — The Asymmetry Is Extreme

**What a Level 5 engineer costs:**
- Delays when concerns are raised and investigated
- Uncomfortable conversations with leadership
- Occasionally being wrong — concern raised, turned out to be unfounded
- Time spent documenting, reporting, building the evidentiary case

**What a Level 5 engineer saves:**

The asymmetry is extreme and historically documented:

| Case | Cost of listening | Cost of not listening |
|---|---|---|
| Boeing 737 MAX | Schedule delay, MCAS redesign | 346 deaths, $20B+ costs, years of reputational damage |
| Challenger | Launch delay | 7 deaths, years of program delay, congressional investigation |
| Equifax breach | Patching known vulnerabilities | 147M people's data, $700M settlement |
| Amazon hiring algorithm | Delay to audit and correct | Discriminatory decisions at scale, public embarrassment |

**The delay is visible. The catastrophe is invisible until it isn't.**

The Level 5 engineer who raises the concern that stops the bad product costs the
organisation a sprint delay. That delay is present-tense, attributable, and
uncomfortable. The catastrophe is future, probabilistic, and by the time it
arrives nobody remembers who said what in which meeting.

This asymmetry is why organisations systematically undervalue Level 5. The cost
of their contribution is legible. The value is invisible — until it becomes
visible as a disaster that did not happen.

**The Level 5 engineer is the cheapest possible insurance against the most
expensive possible failures.**

Organisations that understand this build safer products, ship with more confidence,
have lower legal and regulatory exposure, and retain the people who make all of
that possible. Organisations that punish Level 5 behaviour get silence — until
the silence becomes a catastrophe that costs more to fix than the concern would
ever have cost to investigate.

### The Flight Data Recorder Applied to Engineers

Civil aviation solved a version of this. The FAA's Aviation Safety Reporting System
offers **immunity** — if you report a safety concern through the system, the report
cannot be used against you in enforcement action.

The result: pilots report. Near misses are captured. Patterns are identified before
they become crashes. The system learns from what almost happened rather than only
from what did.

The equivalent for engineering organisations:

- A protected channel for raising safety concerns — independent of the management
  chain that might suppress them
- Immunity for concerns raised in good faith — even if wrong
- Visible celebration when an early concern prevented a disaster
- "Concerns raised and acted on" tracked as a positive metric in performance reviews
- Leadership that visibly, specifically names: this person found something we needed
  to know, and we are grateful, even though it was uncomfortable

### The Reward Structure That Makes Level 5 Sustainable

People watch what leadership **celebrates**, not what leadership **says** it celebrates.

If the person who raised the concern that delayed the launch is quietly passed over
for promotion while the person who shipped on time is celebrated — the signal is
clear. Regardless of what the safety culture document says.

**What actually works:**

- Specific, named, public recognition when a concern prevented a bad outcome
- Performance reviews that explicitly track early problem identification as a
  positive — not as "slowing down delivery"
- Leadership that models the behaviour — raising their own uncertainties, naming
  their own mistakes, creating the permission structure from the top
- Retaliation for speaking up treated as a firing offence, not a management style

**The additional burden is real.**

Level 5 is not just doing more work. It is doing harder work in a system often
structured against it — and doing it anyway, while also doing all the work of
Levels 1-4. This is why Level 5 engineers are extraordinarily rare, extraordinarily
valuable, almost never identified by hiring processes, rarely rewarded by performance
management systems, and frequently lost to organisations that punish what they do.

The organisations that keep them are the ones that built the structure that makes
it worth staying.

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
