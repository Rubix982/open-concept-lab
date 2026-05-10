# Value Sensitive Design — Embedding Values in AI Development

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Implementation Gap

HCAI frameworks offer principles — dignity, trust, accountability, fairness — that should
guide AI development. The problem: these values are often abstract enough that creating
robust, concrete methods for implementing them in actual development workflows is very
difficult. This gap between principle and practice is the **implementation gap**.

This is not a new observation. It is what Canca's PiE model is trying to close with
The Box. It is what the Microsoft 18 guidelines are trying to close with specific,
testable design rules. It is what the PAIR Guidebook is trying to close with chapter-by-
chapter design patterns. The implementation gap is the central problem in applied AI ethics.

Value Sensitive Design (VSD) is a framework specifically designed for this gap — it
provides methodologies for taking values expressed in the abstract and grounding them
concretely in technology, systems, and the lives of real people.

---

## What VSD Is

VSD is a theoretical and practical framework that provides methodologies for identifying
and embedding human values in design practice.

**Definition of human values (VSD):** "What is important to people in their lives,
with a focus on ethics and morality" — values as embedded in how people encounter the
world in daily life.

**The key insight:** People are often not consciously aware of what they value until
they have an interaction with something that conflicts with those values and they notice
the misalignment. Values become visible through conflict, not in the abstract.

This is especially true with technology. Privacy, security, trust — these values become
suddenly visible to more people when a new technology violates them. Not because people
suddenly start caring about them, but because technology makes people *notice* when those
values are not being upheld.

**VSD's foundational assumption:** People, technology, and values are co-constituted —
they shape one another in their interaction. This is the starting point from which design
practice should extend. Latent values are not visible until people bump into their values
being unmet, which makes them a critical place of intervention.

---

## The Tripartite Methodology

VSD's core methodology consists of three types of investigation, each approaching
the values-in-design question from a different angle.

---

### Part 1 — Conceptual Investigation

**What it is:** A theoretical or analytical approach that explores the overarching
ethical issues or concerns that arise in the design process.

**The questions it asks:**
- Who are the stakeholders?
- What values are those stakeholders committed to?
- What other values are implicated by those commitments?
- What harms or risks might arise from those implications?
- Who and what is involved in the design process?

**What it produces:** A human-centered map of the people whose lives might be touched
by the technology, and how those people relate to it from a values perspective — before
any empirical work begins.

**Connection to what we have built:**

This is what the Venn diagram exercise does — identifying whose interests are in the
overlap and whose are not. It is what the excluded perspectives analysis does — asking
who is not in the room and whose values are therefore absent from the design. It is
what the Canca PiE core/instrumental distinction does — clarifying which values are
foundational before deciding which mechanisms serve them.

For the knowledge infrastructure specifically: the conceptual investigation would ask
who the stakeholders are (researchers whose work is indexed, researchers who use the
graph, funders, the broader scholarly community, communities whose knowledge is
underrepresented in the literature) and what values each group holds. This has to happen
before the system is designed, not discovered through complaints after deployment.

---

### Part 2 — Empirical Investigation

**What it is:** An applied approach, drawing on quantitative and qualitative methods,
that looks at what actually happens when a technology is placed in a human context.

**The questions it asks:**
- What value tensions come up when someone interacts with this technology?
- Do some people feel their values are respected? Do others feel their values are ignored?
- When value tensions arise or stakeholders have competing values, how do you manage
  and prioritise those competing values so everyone feels heard?

**What it produces:** Real evidence about which values are actually implicated in practice,
as opposed to which values designers assumed would matter. Some value tensions are only
visible in actual interaction — not in the conceptual phase.

**Connection to what we have built:**

This is the Wizard of Oz testing phase from Xu's framework and the honest build sequence.
It is the researcher outreach — showing researchers how their work appears in the graph
and watching what they flag, question, or appreciate. It is what the Microsoft 18
guidelines validation study did: 49 practitioners interacting with real products to find
where the guidelines applied and were violated.

The empirical investigation does not replace the conceptual one — it extends it by finding
value tensions that were invisible in the abstract. The researcher who seemed fine with
the consent framing in the conceptual phase might, in actual interaction with the graph,
discover that their work is connected to something they find uncomfortable. That is an
empirical finding about values in practice that no amount of conceptual analysis would
have produced.

---

### Part 3 — Technical Investigation

**What it is:** An examination of the technology itself — how it is designed, what values
are embedded in that design, what values are made possible or foreclosed by specific
technical choices.

**The questions it asks:**
- Based on how this technology is designed, what values are visible? What values are
  invisible?
- Is the technology designed in a way that privileges one set of values while hindering
  another?
- What interactions does the design enable, and what interactions does it foreclose?
- What values are made feasible by the technical architecture? What values are minimised?

**What it produces:** A direct connection between technical decisions and values outcomes —
showing that the way a technology is built is not neutral, but encodes specific value
priorities that may or may not align with what was intended.

**Connection to what we have built:**

This is the Shneiderman two-dimensional framework applied at the technical level — asking
whether the architecture maintains genuine human control or just nominal control. It is
Xu's point that imperceptible AI is not ethical AI — a technical choice to make AI
invisible is a values choice, not just a design choice.

For the knowledge infrastructure: the technical investigation would examine the embedding
model, the similarity function, the thresholding decisions. Each of these encodes values.
A similarity function that prioritises citation overlap over semantic similarity encodes
a specific theory of what makes papers "related." A threshold that returns the top 5
connections encodes a theory of how many connections a researcher can usefully process.
These are not neutral engineering decisions — they are values embedded in technical choices.

The Microsoft G11 gap (most products do not explain why the system did what it did) is
a technical investigation finding: the architecture does not include an explanation layer,
which forecloses the value of user understanding by design.

---

## The Three Investigations Together

VSD does not prescribe running these in sequence. They are complementary lenses, often
running in parallel or cycling between them:

- **Conceptual** identifies which values are at stake and for whom — *before* building
- **Empirical** discovers which value tensions actually emerge in practice — *during and after*
- **Technical** examines what values the architecture encodes — *throughout*

The interaction between them is where the real work happens. A technical investigation
might reveal that the architecture forecloses a value the conceptual investigation identified
as important — which triggers a design revision. An empirical investigation might surface
a value tension the conceptual investigation missed — which requires revisiting both the
technical design and the stakeholder map.

---

## VSD and the Implementation Gap — Why It Helps

The implementation gap exists because values stated at the principle level ("respect
privacy," "ensure fairness") are too abstract to translate directly into design decisions.
VSD narrows this gap by providing structured methods for:

1. Making latent values visible before they become conflict (conceptual)
2. Discovering what values actually emerge in practice (empirical)
3. Tracing how technical choices encode specific value priorities (technical)

Together, these give designers a vocabulary and methodology for moving between the
abstract and the concrete — not solving the implementation gap entirely, but providing
the scaffolding that makes principled design tractable.

---

## What VSD Adds That Other Frameworks Miss

- **Canca's PiE model** tells you which values are core and which are instrumental —
  but it does not tell you which values are implicated for which stakeholders in which contexts.
  VSD's conceptual investigation does that.

- **The Microsoft 18 guidelines** tell you what properties the interface should have —
  but they do not tell you how to discover whether those properties align with the values
  users actually hold in practice. VSD's empirical investigation does that.

- **Xu's framework** tells you to do AI-first UCD and Wizard of Oz testing — but it does
  not tell you how to examine the technology itself for embedded values. VSD's technical
  investigation does that.

VSD is not a replacement for any of these. It is a layer underneath them — the
philosophical and methodological foundation that makes the specific frameworks legible
as attempts to embed values in design.

---

## Connection to the Knowledge Infrastructure

The three investigations applied to the Bau Lab project:

**Conceptual:** Who are the stakeholders and what do they value?
- Researchers whose work is indexed: accuracy, attribution, opt-out, being understood correctly
- Researchers who use the graph: breadth, precision, trustworthy connections, explainability
- Funders: sustainability, demonstrated impact, non-commercial mission
- Underrepresented scholarly communities: inclusion, not being erased by dataset geography

**Empirical:** What actually happens when researchers interact with the graph?
- The researcher outreach IS the empirical investigation — watching what they flag,
  correct, appreciate, or find confusing
- The Wizard of Oz testing phase produces empirical evidence about value tensions before
  the system is built

**Technical:** What values does the architecture encode?
- The similarity function: what counts as "related"?
- The confidence threshold: how certain before a connection is shown?
- The explanation layer: does it exist, and is it comprehensible to the target user?
- The correction mechanism: is it easy (G9 from Microsoft) or requires contacting the team?

---

## Key Insight

> VSD's foundational observation — that people are not consciously aware of their values
> until technology violates them — is precisely why the planning phase matters so much.
>
> By the time users discover their values are not being met, the system is deployed
> and correction is expensive. The three investigations are attempts to surface those
> values before they become visible through conflict.
>
> The conceptual investigation asks: whose values, and what are they?
> The empirical investigation asks: what actually happens when people use this?
> The technical investigation asks: what values did we encode without realising it?
>
> Together they are the methodology for honest building —
> not eliminating the implementation gap, but traversing it with intention.

---

## Connections

- *Honest build sequence* — VSD's tripartite methodology maps directly onto the
  Plan → Validate → Evaluate phases: conceptual = plan, empirical = validate, technical = evaluate
- *Microsoft 18 guidelines* — G5/G6 (social norms, social biases) are the guidelines
  most requiring empirical investigation with diverse participants to identify
- *Canca's PiE model* — the conceptual investigation is where core/instrumental
  distinction is applied before technical decisions are made
- *Xu's HCAI framework* — Wizard of Oz prototyping is the empirical investigation tool;
  AI-first UCD is the technical investigation approach
- *Excluded perspectives* — the conceptual investigation is where you ask whose values
  are absent from the stakeholder map — not after deployment
