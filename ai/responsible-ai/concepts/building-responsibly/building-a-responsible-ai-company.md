# Building a Responsible AI Company — A Framework

_Personal study notes — original analysis and synthesis drawn from the full body
of responsible AI learning in this repository. Not a prescription — a framework
for honest thinking._

---

## The Problem with Most AI Company Building Advice

Most advice for building AI companies is optimised for one thing: speed to market.
Move fast. Ship early. Iterate on user feedback. Get to product-market fit before
you run out of runway.

This advice is not wrong for every company. It is wrong for AI companies whose
products make consequential decisions about people's lives, collect intimate data,
or affect communities that were not consulted during design.

For those companies — which is most serious AI companies — the advice optimises for
the wrong objective. Moving fast before the values questions are answered does not
avoid those questions. It defers them, with compound interest, until they arrive as
lawsuits, regulatory actions, or harms to people who had no say.

This document is a framework for building differently — not slower for its own sake,
but slower in the right places and faster in the right places.

---

## Before You Write a Line of Code

### 1. Name the Problem Honestly

Not "we are building an AI product." The actual problem. Who has it? How do you know
they have it? What have you observed, not assumed?

The PAIR Guidebook's first question: does this need AI at all? The answer might be no.
A product built on the honest answer to this question — even if that answer is "not yet"
or "not this way" — will be more defensible than a product built on the assumption that
AI is the right tool because AI is interesting.

### 2. Map the Stakeholders — All of Them

Not just users. Affected communities who are not users. People whose data trains the
system. Workers who will be displaced or changed. Communities near the infrastructure.
Future generations who inherit the ecological and social effects.

VSD's conceptual investigation: who are the stakeholders, what do they value, what other
values are implicated by those commitments, what harms might arise?

The Venn diagram test: whose interests overlap? Legislate inside that overlap. Name
what is outside it and why.

### 3. Name the Values — Core and Instrumental

Using Canca's distinction: what are the core values this product should serve?
Autonomy? Beneficence? Justice? Name them explicitly.

What are the instrumental principles — transparency, accountability, fairness, privacy?
Each of these is a mechanism serving core values in specific contexts. Name which core
value each instrument serves. When instruments conflict, the core value is the tiebreaker.

If you cannot name the core values, you cannot make principled design decisions when
tradeoffs arise. And tradeoffs will arise.

### 4. Plan the Consent Mechanism Before Planning the Product

Who will you ask before indexing, training on, or making decisions about people's data
or work? How will you ask? What will you show them? What will opt-out look like?

The consent mechanism is not a legal formality. It is the foundation of the community
that will sustain the product. MIT is MIT — a standing permission. Everything else
requires asking first, not defending afterward.

The data permission hierarchy:

- **Build on freely given first** — MIT-licensed, Creative Commons, explicitly open
- **Negotiate for what requires negotiation** — contact rights holders, explain the
  project, get explicit consent before use
- **Exclude what cannot be obtained honestly** — do not scrape, do not use, do not
  assume fair use covers it

---

## The Build Sequence

### Phase 1 — Plan (Months, Not Weeks)

Write the plan in enough detail that a second person could execute it independently
without asking clarifying questions. Answer:

- What problem, for whom, under what conditions?
- With what data, acquired how, stored how, retained how long?
- With whose consent, under what terms?
- Governed how — who makes decisions about what goes in, who reviews disputes?
- Failing how — what are the failure modes, who bears the cost?
- Corrected how — what is the mechanism for identifying and fixing errors?

Apply the tripartite VSD methodology:

- **Conceptual:** stakeholder map, values map, harm identification
- **Technical:** what values does the planned architecture encode?
- **Empirical:** planned — what will you observe when people use this?

Run through the pre-flight checklist: Microsoft 18 guidelines, Shneiderman's
top-right quadrant, Xu's AI-first UCD, Canca's PiE model.

### Phase 2 — Validate Before Building

Wizard of Oz prototyping. Show the interface before the system exists. Mock the outputs.
Watch what people do.

For the knowledge infrastructure specifically: show researchers how their work might
appear in the graph before the graph exists. Watch what they flag. Watch what they
trust. Watch what they wish were different.

This phase is simultaneously:

- UX testing (do people understand it?)
- Quality validation (are the connections accurate?)
- Consent (do they want to be included?)
- Community building (do they want to be involved?)

Four things. One conversation. This is not overhead. This is the product.

### Phase 3 — Evaluate Against Frameworks

Before writing production code, evaluate the designed system:

| Framework      | What to check                                                                            |
| -------------- | ---------------------------------------------------------------------------------------- |
| Canca PiE      | Are core values named? Is the Box applied? Are complex cases escalated?                  |
| Microsoft 18   | Which guidelines does the planned design violate by default?                             |
| Shneiderman    | Top-right quadrant: is automation high AND human control genuinely high?                 |
| VSD tripartite | Are all three investigations complete?                                                   |
| Rawls veil     | Would you design this system if you didn't know which side of its decisions you'd be on? |
| Taleb skin     | Do the people making decisions bear the cost if those decisions are wrong?               |

Fix violations before building. This is cheap. Fixing them after deployment is expensive.

### Phase 4 — Build With Right-Kind Uncertainty

The uncertainty that remains after Phases 1-3 should be:

- Technical — which implementation approach works best?
- Empirical — which design works better for which users?
- Iterative — what does testing reveal?

Not:

- Whose interests does this serve? (Should be answered in Phase 1)
- What happens when it fails? (Should be answered in Phase 1)
- Did we have permission to use this data? (Should be answered in Phase 1)

The wrong-kind uncertainty is the kind that produces lawsuits and harms. It should
be resolved before the first line of code, not discovered after the first million users.

---

## Structure and Governance

### The Non-Profit Question

For products that collect sensitive data, make decisions about people's lives, or
affect communities — the non-profit structure deserves serious consideration:

**What it changes:**

- Removes investor return pressure — the incentive to monetise in ways that compromise
  mission disappears
- Makes the consent conversation honest — researchers and communities contribute to a
  commons, not to a product that will sell their work
- Qualifies for foundation funding — Wikimedia, Internet Archive, Allen Institute models
  are proven precedents
- Creates the right relationship with partner institutions — universities and labs can
  contribute without commercial exploitation concern

**What it does not change:**

- The need for revenue — non-profits still need to operate, which means funding strategy
  matters as much as product strategy
- The need for capable people — the talent question does not go away

**The four-layer funding model for a responsible AI company:**

1. **Open core** — free tools, open source, MIT-licensed outputs build community and
   credibility
2. **Foundation grants** — NSF, Wikimedia, open science infrastructure funders
3. **Enterprise services** — organisations that need the capability pay for custom
   deployment, support, or data services
4. **Cloud credits** — AWS, Google, Microsoft all have non-profit research programmes

### Governance That Is Not Theatre

Real governance means:

- The people affected by the system have meaningful input before decisions are made,
  not just consultation after
- The people making decisions bear some consequence if those decisions are wrong
- There is a mechanism for correction that does not require the harmed party to mount
  a lawsuit
- The values commitments are reviewed against actual product decisions, not just
  principles documents

The Responsible Technology Board that only reviews policy, not individual product
decisions, is governance theatre. The ethics team with no power to stop a launch is
governance theatre. The principles document with no tiebreaker is governance theatre.

The test: when "bold innovation" and "responsible development" conflict in a specific
product decision, which one wins, and who decides?

If the answer is "whoever is most senior" or "whoever has the most financial stake,"
the governance structure has not been built.

---

## People and Culture

### Hire for the Venn Diagram

The AI specialist needed is not just technically excellent. They sit at the intersection
of:

- Technical depth (can engage with the architecture and know what it encodes)
- People depth (can hold space for competing values, hear what is not said)
- Process discipline (knows conversations must happen before implementation)

See: [The Venn Diagram Person](the-venn-diagram-person.md)

### Protect the Slow Work

The conditions that let the Venn diagram person function are:

- Time for the planning phase without velocity pressure
- Permission to say "we need more conversations before we build"
- Explicit recognition that the researcher outreach, the stakeholder mapping, and the
  values investigation are the work — not the overhead before the work
- Leadership that models intellectual honesty over confident wrongness

### The Sycophancy Problem

The biggest internal risk for a responsible AI company is the same as the biggest
external risk in AI governance: sycophancy. People who tell the product team what
they want to hear rather than what they need to hear.

The planning phase requires people who will say: "this connection the model makes is
wrong," "this researcher is uncomfortable with how their work is represented," "this
design choice forecloses the value of user control."

Those people need to be protected, celebrated when they are right, and not penalised
when they are wrong. The signal to watch: does the culture reward finding problems
early, or does it treat problem-finders as obstacles?

---

## The Honest Business Case

Building responsibly is slower in the planning phase and faster in every phase after it.

**What you avoid by building honestly:**

- Lawsuits from people whose data was used without consent (the NYT v. OpenAI model)
- Regulatory action from building harmful products (the My AI / Character.AI model)
- Community backlash that destroys the trust the product depends on
- Rebuilding from scratch when early design decisions encode values you didn't intend

**What you gain by building honestly:**

- The moat of genuine relationships — communities that trust you and contribute
- The defensibility of a clean provenance record
- The credibility to ask for consent from the next community
- The funder relationships that open when your mission is genuine

The race logic says: move fast, iterate, apologise later. The honest business case
for responsible building says: the apologising is more expensive than the planning.
And some things cannot be apologised out of — consent that was not obtained cannot
be retroactively granted. Community trust that was violated cannot be unconsumed.

---

## Key Insight

> Most AI companies are built around the assumption that the right time to think
> about values is after you have users. The responsible AI literature — all of it,
> from every framework in this repository — says the opposite: by the time you have
> users, the values are already encoded in the architecture, the training data, the
> consent (or lack of it), and the business model.
>
> Building responsibly is not a constraint on building well.
> It is the condition for building something that lasts.
>
> The planning phase is where the community is built.
> The consent mechanism is where the moat is built.
> The values investigation is where the accountability is built.
>
> None of these can be retrofitted after the first line of code.
> Which means they are not optional.
> They are the sequence.
