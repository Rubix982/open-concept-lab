# Prediction Machines — The Simple Economics of AI

*Research notes on: Agrawal, Gans, and Goldfarb, "Prediction Machines: The Simple
Economics of Artificial Intelligence" (HBR Press, 2018) and "Power and Prediction:
The Disruptive Economics of Artificial Intelligence" (HBR Press, 2022).*

*Presented at the Big Ideas Speaker Series, Rotman School of Management, April 2018.*

---

## The Authors

**Ajay Agrawal** — Peter Munk Professor of Entrepreneurship, founder of the Creative
Destruction Lab (CDL), Rotman School of Management, University of Toronto. CDL
is one of the world's leading startup accelerators focused on science-based companies.

**Joshua Gans** — Jeffrey S. Skoll Chair of Technical Innovation and Entrepreneurship,
Chief Economist of CDL, Rotman. Research focus: innovation economics, platform
competition, technology strategy.

**Avi Goldfarb** — Ellison Professor of Marketing, Chief Data Scientist of CDL,
Rotman. Research focus: the economics of AI, digital advertising, data and privacy.

All three are economists by training — which is the key to understanding their
framework. They are not asking "what can AI do technically?" They are asking
"what changes economically when a specific input becomes dramatically cheaper?"

---

## The Core Thesis — AI as Cheap Prediction

**The simplest version of the argument:**

> Artificial Intelligence is a technology that dramatically reduces the cost of prediction.

That is it. Everything else follows from that.

**Why "prediction" is the right word:**

In economics, prediction is not just forecasting the future. It is filling in
missing information using available data. When an image classifier identifies a
cat, it is "predicting" what the image contains based on patterns in training data.
When a recommendation system suggests a product, it is "predicting" what you will
like based on your history. When a credit scoring model assesses risk, it is
"predicting" the probability of default. All of these are prediction in the
economic sense.

**The economic logic:**

When a previously expensive input becomes cheap, three things happen:

1. **It is used more** — applications that were not viable when prediction was
   expensive become viable when it is cheap
2. **It substitutes for other things** — what was previously done without prediction
   now gets prediction added to it
3. **It changes what is valuable** — the things that *complement* the now-cheap
   input become more valuable; the things that substitute for it become less valuable

This is the same logic that applies to any input cost reduction. When electricity
became cheap, it was not just used for lighting — it transformed manufacturing,
communication, and domestic life in ways nobody anticipated. When computing became
cheap, the same transformation happened again. AI reducing the cost of prediction
is that same story in the current chapter.

---

## The Prediction vs. Judgment Distinction

This is the most important concept in the book for strategic decision making.

**Prediction:** Filling in missing information from available data. What AI does.

**Judgment:** Deciding what to do based on predictions, values, and stakes.
What humans do — or should do.

**The relationship:** Prediction and judgment are complements, not substitutes.
Better prediction raises the value of good judgment. An AI that can predict
with 95% accuracy what a customer will do next is only valuable if someone with
good judgment decides what to do with that information.

**The implication for strategy:**

As AI gets better at prediction, the scarce and valuable resource shifts from
prediction to judgment. The strategic question becomes: who in your organisation
has genuine judgment, and are they spending their time on judgment or on producing
predictions that AI could produce more cheaply?

A doctor who spends 70% of their time doing pattern recognition on symptoms —
a prediction task — and 30% of their time explaining options, weighing values,
and deciding with patients — a judgment task — is using their most valuable hours
on the cheaper task. AI flips this: the pattern recognition becomes cheap, and the
doctor's genuine value is in the judgment that AI cannot provide.

**The warning:**

Not all judgment complements AI. In some complex environments, AI prediction
becomes good enough that judgment itself can be automated — reducing the need for
human judgment entirely. The strategic challenge is knowing which domain you are in.

---

## The Three Trade-offs

The authors identify three fundamental trade-offs when deploying AI prediction:

**1. More data = less privacy**
Better predictions require more data. More data means more surveillance of behaviour.
This is not a technical problem to be engineered away — it is a structural trade-off
built into the economics of prediction.

**2. More speed = less accuracy**
Faster predictions are cheaper to produce but less accurate. Slower predictions
with more deliberation are more accurate but more expensive. Every deployment choice
involves this trade-off, usually implicitly.

**3. More autonomy = less control**
More autonomous AI systems make more decisions without human review. More human
control means more human review, which is slower and more expensive. The Shneiderman
two-dimensional framework (high automation, high human control) is the aspiration —
but the economic trade-off runs against it.

**Why these trade-offs matter for responsible AI:**

These are exactly the trade-offs that the responsible AI discourse either ignores
or pretends to resolve. You cannot have perfect privacy AND perfect prediction.
You cannot have maximum speed AND maximum accuracy. You cannot have maximum autonomy
AND maximum human control. Every framework that promises all of them is not being
honest about the economics.

The right response is not to pretend the trade-offs do not exist. It is to make
explicit which side of each trade-off you are accepting and why — and to be clear
about who bears the cost of each choice.

---

## Substitutes and Complements

**What becomes less valuable when prediction is cheap:**

- Human prediction — if a doctor's value is pattern recognition, AI substitutes
  for that
- Data that was valuable primarily for making predictions that AI can now make
  more cheaply
- Processes designed to manage prediction uncertainty (because there is less uncertainty)

**What becomes more valuable when prediction is cheap:**

- **Data** — the input to prediction; more valuable as prediction becomes more useful
- **Judgment** — the complement to prediction; more valuable as predictions improve
- **Actions** — the things you do based on predictions; if prediction improves, you
  can act more precisely
- **Risk management** — knowing what will happen changes which risks are worth taking

**The strategic implication:**

If AI is reducing prediction costs in your industry, the question is not "will AI
take my job?" It is "what in my job is prediction and what is judgment?" The
prediction part will be automated. The judgment part will become more valuable —
if you invest in developing it.

---

## Power and Prediction (2022) — The Institutional Extension

The second book extends the framework from individual decisions to organisational
decision-making systems.

**The core new argument:**

AI does not just change individual decisions. It changes the architecture of decision
making itself. When prediction becomes cheap, the structure of who decides what,
when, and with what information can be completely rebuilt.

**Point decisions vs. system decisions:**

- **Point decisions** — individual choices made by a person or system at a specific
  moment. AI improves these by providing better prediction inputs.
- **System decisions** — the structure of rules, processes, and roles that govern
  how decisions are made across an organisation. AI can restructure these entirely.

The book argues that most organisations are trying to use AI to improve point
decisions while leaving the system unchanged. The real opportunity — and the real
disruption — is in redesigning the system. This is harder, slower, and more
politically complex, but it is where the transformative value lives.

**Why this matters for module 6 (AI for Strategic Decision Making):**

Strategic decisions are system decisions, not point decisions. Deciding which markets
to enter, which products to build, which acquisitions to pursue — these are not
improved by giving one executive a better prediction tool. They are improved by
redesigning how the organisation gathers information, processes it, and routes it
to the people with the judgment to act on it.

---

## Connections to What We Have Built

**The understanding problem (topic 11):**
The prediction/judgment distinction is the economic version of the reckoning/judgment
distinction from Brian Cantwell Smith. Machines reckon (predict). Humans judge.
The economic framework makes explicit what the philosophical framework names: the
two are complementary, and improving one raises the value of the other.

**The Shneiderman two-dimensional framework:**
High automation + high human control is the design aspiration. The Agrawal/Gans/Goldfarb
trade-off (more autonomy = less control) is the economic constraint. The gap between
the aspiration and the constraint is where responsible AI design happens.

**The exclusion problem:**
"Prediction" in the economic sense requires data. Data reflects who was observed,
when, and under what conditions. The dataset geography problem (Ibn Rushd, the
cultural dataset business) is the economic entry point: if AI is cheap prediction,
and prediction requires data, and data systematically underrepresents certain
populations, then cheap prediction is cheap prediction for some people and unavailable
or wrong prediction for others.

**The responsible AI accountability argument:**
The three trade-offs (data/privacy, speed/accuracy, autonomy/control) make explicit
something the ethics-as-defanging critique identified: the costs of these trade-offs
are not shared equally. The people who benefit from cheap, fast, autonomous prediction
are often not the people who bear the cost of the privacy loss, accuracy reduction,
or control erosion. This is the Rawlsian veil of ignorance test applied to the
economics of AI.

**The knowledge infrastructure:**
The Bau Lab knowledge graph is a prediction machine in exactly the sense Agrawal
et al. describe. It predicts: which papers make claims connected to which other
papers, which researchers work on adjacent problems, which concepts are related.
The judgment — which connections are actually meaningful, which should be acted on,
which papers should be in conversation with each other — remains with the researchers
who use it.

The design principle that follows: the graph should be excellent at prediction and
transparent about its uncertainty, so that the researchers bring good judgment to
the results rather than deferring to the prediction.

---

## For Module 6 — AI for Strategic Decision Making

Chan's module will almost certainly engage with this framework. The Prediction
Machines thesis is the foundational economic argument for why AI matters strategically
— not because AI is powerful, but because prediction has become cheap and the
implications of cheap prediction ripple through every industry and organisation.

**The strategic questions the framework generates:**

1. In your organisation, what decisions are primarily prediction and what are
   primarily judgment?
2. Where is prediction currently expensive and therefore limiting what you can do?
3. If prediction in your domain became 10x cheaper or more accurate, what decisions
   would you make differently?
4. Who in your organisation has genuine judgment, and are they spending their time
   on judgment or on producing predictions?
5. What data do you have that would become more valuable if prediction became cheaper?

**The responsible AI layer:**

Every one of these strategic questions has a shadow question:
1. Who does not have access to cheap prediction, and what does that mean for
   equity in your domain?
2. Whose data makes prediction cheap for you — and what did they receive for it?
3. If prediction in your domain became 10x cheaper, whose privacy would that cost?
4. The judgment you are concentrating — is it actually good judgment, or is it
   judgment by people with no accountability for errors?
5. The data you hold — was it obtained with genuine consent for this use?

The framework is analytically powerful and ethically incomplete on its own.
Combining it with the responsible AI critique we have built produces a more honest
account of what "AI for strategic decision making" actually requires.

---

## Key Insight

> The Prediction Machines framework is the most useful economic lens for thinking
> about AI strategy because it asks the right prior question: not "what can AI do?"
> but "what changes when prediction becomes cheap?"
>
> The answer to that question determines which industries are disrupted, which skills
> become more valuable, which decisions need to be redesigned, and which organisations
> will survive the transition.
>
> The responsible AI question it leaves open: cheap for whom, accurate for whom,
> and who bears the cost of the trade-offs that cheap prediction requires?
> That is where the economic framework needs the ethical one.
