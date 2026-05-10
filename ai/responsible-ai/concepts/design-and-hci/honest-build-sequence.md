# The Honest Build Sequence — Plan, Validate, Evaluate, Then Build

*Personal study notes — applies to the Bau Lab knowledge infrastructure and
any AI product that affects people who did not ask to be affected.*

---

## The Sequence Almost Nobody Follows

Almost no startup follows the sequence that would actually produce a system that
serves people rather than extracts from them. The dominant model is:

**Build → Ship → Iterate → Apologise**

The iteration loop assumes you can learn your way to the right product through
user feedback after deployment. Sometimes true. For systems that collect sensitive
data, make claims about people's work, or shape how knowledge is discovered — iteration
after the fact is too late. The consent violation already happened. The wrong
connection was already drawn. The researcher's work was already misrepresented.

The correct sequence is the opposite:

**Plan → Validate → Evaluate → Build**

This is not over-caution. It is the only way to build a system that is honest by
design rather than honest in retrospect.

---

## Phase 1 — Write the Plan in Detail

Not a pitch deck. Not a one-pager. A genuine document that answers:

- **What problem?** Specific, named, with evidence that it exists
- **For whom?** Not "researchers" generically — which researchers, at what stage,
  with what existing tools and workflows
- **Under what conditions?** What does a typical use session look like? What are
  the edge cases? What happens when the system is wrong?
- **With what data?** What sources, under what licences, acquired how, stored how,
  retained for how long
- **With whose consent?** Who knows their work is in the system? Who agreed?
  Who can remove themselves?
- **Governed how?** Who makes decisions about what goes in? Who reviews disputes?
  Who is accountable when something is wrong?
- **Failing how?** What are the failure modes? Who bears the cost when they occur?
- **Corrected how?** What is the mechanism for identifying and fixing errors?

The document should be detailed enough that a second person could execute it
independently without asking clarifying questions. The ticket discipline principle
applied to product design: if it is not detailed enough to hand to someone else,
it is not detailed enough to build from.

**Why this phase takes months:**

Because the answers to these questions require conversations with the people who
will use the system, not assumptions about them. The plan is not finished when the
author has written it — it is finished when the first round of users has read it
and confirmed that it describes their actual problem and their actual needs.

---

## Phase 2 — Validate with Diagrams and Interfaces

Build the interface before building the system. Wizard of Oz prototyping — Xu's
method. Show researchers what the output might look like before any ML runs.

**What to show:**
- Mock knowledge graph connections — manually curated, not model-generated
- Sample claim attributions — what a connection looks like, how it is explained
- The researcher profile page — how their work appears in the graph
- The correction mechanism — how they would flag or fix something wrong

**What to watch:**
- Where does comprehension break? What needs explanation?
- What do they trust? What do they question?
- What do they wish it did differently?
- What would make them comfortable having their work in the graph?
- What would make them uncomfortable?

**Why this phase is simultaneous with consent:**

The researcher outreach designed for this project — showing researchers how their
work appears, asking if it accurately represents their contribution, giving opt-out
— is Wizard of Oz UX testing and ethical consent simultaneously. You are:

1. Testing whether the output is comprehensible (UX)
2. Testing whether the connection is accurate (quality)
3. Getting permission to keep it (consent)
4. Building a relationship (community)

All four happen in one honest conversation. This is not overhead. This is the product.

**The Microsoft G9 connection:**
Making correction easy — before the system even exists — is how you build a system
where correction is easy by design rather than retrofitted as an afterthought.

---

## Phase 3 — Evaluate Against Frameworks

Before writing code, evaluate the planned system against the frameworks the course
has covered. Not to produce a compliance document. To ask honest questions that
change the design before it is expensive to change.

### Canca's PiE Model — Core vs. Instrumental

What are the core values this system is trying to serve?
- **Autonomy** — researchers retain control over how their work is represented
- **Beneficence** — the graph surfaces connections that genuinely help understanding
- **Justice** — non-Western, non-English, non-elite institution work is not systematically underweighted

What instruments serve those values?
- Consent mechanism → serves autonomy
- Accuracy validation with researchers → serves beneficence and autonomy
- Dataset geography awareness → serves justice

Are we confusing instrumental principles with core ones? Is "comprehensiveness"
being treated as a core value when it is only instrumental to the core values?

### The Venn Diagram — Whose Interests Overlap?

Draw the stakeholders: researchers whose work is indexed, researchers who use the
graph to find connections, funders, the Bau Lab, the broader research community.

Where do their interests overlap? That is the safe design space.
Where do they not? That is where explicit choices must be made and stated.

The researchers whose work is indexed and the researchers who use the graph have
mostly overlapping interests — both want accurate, well-attributed connections.
The funder may want comprehensiveness. If comprehensiveness conflicts with consent —
a researcher who does not want their work indexed — the Venn diagram resolves it:
consent is inside the overlap, comprehensive coverage is not.

### The Microsoft 18 Guidelines — Pre-flight Check

Run through all 18 guidelines against the planned design:

- G1: Does the interface make clear what the system can and cannot find?
- G2: Does it communicate how often it is likely to be wrong?
- G9: Is correction easy and visible?
- G10: When the system is uncertain about a connection, does it show alternatives
  rather than picking one and presenting it as fact?
- G11: For every connection surfaced, is there a visible explanation of why?
- G15: Can researchers rate connections and see how their feedback shapes results?
- G17: Can researchers globally customise what appears about their work?

Any guideline violated by the planned design should be addressed before building —
not flagged as a known issue to fix later.

### Shneiderman's Two-Dimensional Check

Is the system designed for the top-right quadrant — high automation AND high human
control? Or is it sliding toward high automation and nominal human control?

For the knowledge graph, high automation means: the system finds connections across
thousands of papers no human could read. High human control means: the researcher
can understand every connection, evaluate it, correct it, or remove it.

If the automation is high but the explanation is opaque — if the researcher cannot
understand why two papers are connected — the system is in the wrong quadrant
regardless of how capable the underlying model is.

### The Xu AI-First UCD Check

- Have the UX criteria been defined with actual users before the ML is designed?
- Has the human-machine task allocation been made explicit?
- Is the WOZ validation complete before model training begins?
- Is the explanation designed for the specific audience, not for data scientists?

---

## Phase 4 — Then Build

With all of that clarity in hand. Not because it eliminates uncertainty — it does not.
But because the uncertainty that remains is the right kind:

**Right kind of uncertainty:** Technical questions with testable answers.
Does this embedding method produce better claim matching? Does this interface
layout make the explanation more comprehensible? Does this model architecture
handle the dataset size efficiently?

**Wrong kind of uncertainty:** Values questions that should have been answered
before building. Whose interests does this serve? What happens when it is wrong?
Who bears the cost? These questions, answered implicitly by whoever wrote the
first line of code, are the hardest to correct after the fact.

The months of planning are not cost. They are the product.

The researcher relationships built during validation become the community that
sustains the infrastructure. The consent mechanism designed during planning
becomes the differentiator that nobody else has. The framework evaluation done
before building becomes the honest answer to every funder's question about why
this is different.

---

## Why This Connects to PAIR's Definition of HCAI

Google's People + AI Research Team says machine learning needs to be participatory
— involving the communities it affects, guided by a diverse set of citizens,
policymakers, activists, artists.

The sequence above is participatory design in practice, not as a principle:

- **Planning phase:** the community defines the problem
- **Validation phase:** the community evaluates the solution before it exists
- **Evaluation phase:** the community's interests are explicitly mapped and protected
- **Build phase:** the community is already a stakeholder, not a user to be acquired

The difference between a tool built this way and a tool built the standard way —
build fast, iterate on feedback, apologise for harms — is not just ethical. It is
structural. The participatory tool has a community. The standard tool has users.
Communities sustain. Users churn.

---

## The Race Logic Argument — Why Nobody Does This

The race logic: move fast, ship early, iterate based on user feedback. First-mover
advantage. The market rewards speed.

This argument fails for the knowledge infrastructure on three specific grounds:

1. **The moat is relationships, not code.** First-mover advantage in the cultural
   dataset and knowledge graph space comes from the trust built with researchers
   and institutions — not from being first to ship a model. Trust takes years.
   Slow, honest building builds it. Fast, extractive building destroys it.

2. **The consent mechanism cannot be retrofitted.** You cannot ask for retroactive
   consent from researchers whose work you scraped without asking. The litigation
   wave hitting AI companies for exactly this reason demonstrates the cost. Building
   honestly from the start is not slow — it is the path that does not end in court.

3. **The wrong kind of speed is self-defeating.** A knowledge graph that researchers
   do not trust is not a knowledge graph. It is a dataset. The speed of building it
   does not matter if the result does not serve its purpose.

---

## Key Insight

> The months of planning are not the cost of building responsibly.
> They are what responsible building looks like.
>
> The correct sequence — plan, validate, evaluate, then build — is not over-caution.
> It is the only sequence that produces a system honest by design
> rather than honest in retrospect, after the harm has already accumulated.
>
> For a knowledge infrastructure built on consent and community,
> the planning phase is where the community is built.
> You cannot build it after the fact.
