# IBM AI Design Fundamentals

*Research notes compiled from web search, IBM documentation, and published sources.
Primary source: https://www.ibm.com/design/ai/fundamentals*

---

## Framework Overview

IBM's AI design work is not a single document but a layered system published under
the **IBM Design for AI** umbrella. Three distinct layers:

**Layer 1 — Design Ethics**
Five focal areas forming the ethical foundation:
- Accountability
- Value Alignment
- Explainability
- Fairness
- User Data Rights (Privacy)

**Layer 2 — Trustworthy AI Pillars**
Five technical/operational pillars:
- Explainability
- Fairness
- Robustness
- Transparency
- Privacy

**Layer 3 — Team Practice Framework**
Five activities for teams building AI products:
- **Intent** — align on business and user intent
- **Data** — document the data used
- **Understanding** — determine what to teach the AI
- **Reasoning** — ground ideas in feasibility
- **Knowledge** — map direct and indirect effects

The practitioner-facing document is *Everyday Ethics for Artificial Intelligence*
(authored by Adam Cutler, Milena Pribić, and Lawrence Humphrey), published via
IBM Watson and catalogued by OECD.AI.

---

## IBM's Definition of Human-Centered AI

IBM Research formally defines human-centered AI as designing and investigating new
forms of human-AI interactions that enhance and extend human capabilities for the
good of products, clients, and society. The operative word is **augment**.

IBM's stated philosophy, reinforced across Watson design materials and corporate
policy: AI should augment, not replace, human intelligence. IBM has at various
points reframed "AI" as "Augmented Intelligence" to signal this.

> "The purpose of AI and cognitive systems developed and applied by IBM is to
> augment, not replace, human intelligence."

---

## Watson Design Principles

1. The user and Watson are partners working toward mutual goals
2. Watson never makes a decision for a person — it finds, augments, and educates
3. Users must be able to peek into the black box — showing what Watson knows builds
   confidence and enables correction
4. Designers must assume and design for fail states
5. Solving the user's need is central; enabling human-computer cooperation is the method

---

## Six Principles for Generative AI UX (IBM Research, CHI 2024)

Published as: *Design Principles for Generative AI Applications* (arXiv:2301.05578)

Each principle is coupled with four specific design strategies and real-world examples:

1. **Design Responsibly** — address real user needs without causing harm; resolve
   value conflicts among stakeholders
2. **Design for Mental Models** — help users understand how the AI works so they
   can use it effectively
3. **Design for Appropriate Trust and Reliance** — educate users about quality,
   accuracy, bias, and representation limitations
4. **Design for Generative Variability** — manage diverse outputs from the same
   input; encourage exploration
5. **Design for New Forms of Interaction** — intent-driven, prompt-based interaction
   is a new interaction paradigm requiring new design patterns
6. **Design for Imperfection** — acknowledge that models produce imperfect responses;
   support users in evaluating and improving outputs

---

## How IBM Operationalises Key Concepts

### Transparency

- Companies must be clear about who trains their AI, what data was used, and what
  drives recommendations
- Any AI making consequential determinations should explain how it arrived at conclusions
- IBM's Responsible Use Guide for the Granite LLM was recognised by Stanford
  University (2024) as one of the most transparent LLM documentation packages available
  — one of the more credible external validations in the IBM framework corpus

### Explainability

Design rules (confirmed from official IBM documentation):
- A user should be able to ask why an AI is doing what it's doing on an ongoing basis,
  clearly and up front in the UI at all times
- **Imperceptible AI is not ethical AI** — good design does not sacrifice transparency
  to create a seamless experience

Tooling: **AI Explainability 360 (AIX360)** — open source Python library covering
multiple explanation algorithms across the AI lifecycle; transferred to LF AI
Foundation July 2020.

### Fairness

Design rules:
- Design and develop without intentional biases
- Schedule regular team reviews to check for unintentional bias

Tooling: **AI Fairness 360 (AIF360)** — open source toolkit with 70+ fairness metrics
and 10+ bias mitigation algorithms (optimised preprocessing, reweighing, adversarial
de-biasing, reject option classification, equalized odds post-processing);
available in Python and R; transferred to LF AI Foundation July 2020.

Case example: IBM worked with the US Open to apply fairness tools to tournament data,
improving court decision fairness from 71% to 82%.

### Accountability

Design rules:
- Keep detailed records of design processes and decision-making

Governance: IBM operates a **Responsible Technology Board** — a cross-business body
providing centralised review and decision-making for AI ethics policies.

Enterprise product: **watsonx.governance** uses "factsheets" — described as
nutritional labels for AI models — that automatically log model facts, performance
data, and risk indicators throughout the model lifecycle.

### Privacy / User Data Rights

Design rule: Protect user data and preserve user power over access and use.
Framed as preserving "the feeling of human control" as a prerequisite for
emotional trust in AI systems.

---

## Carbon for AI — Design System Implementation

IBM's Carbon Design System includes a **Carbon for AI** layer — the most concretely
operationalised aspect of the framework. It ships in product code, not just documentation:

- Every AI-powered component must carry an embedded **AI label**
- The AI label functions as both a visual indicator and the trigger for an
  **explainability popover**
- The explainability popover is defined as "the first layer of explainability" —
  providing in-context explanation for a specific AI result with the option to drill deeper
- Components switch to "AI visual style" when the AI label is on, maintaining
  identical functionality
- Base principle: mark where AI is present while providing explainability whenever available

This is the closest thing in any major framework to explainability as a mandatory
UI component standard rather than a documentation aspiration.

---

## Governance Infrastructure

- **Responsible Technology Board** — cross-business body for centralised AI ethics review
- **AI Seoul Summit Commitments (2024)** — IBM signed frontier safety commitments
- **EU AI Pact (2024)** — IBM signed voluntary pledge aligned with EU AI Act
- **AI Alliance** — co-founded with Meta, December 2023; 140+ member organisations
- **watsonx.governance** — enterprise commercial product embedding governance
  checkpoints at data ingestion, model development, validation, and production monitoring

---

## Comparison with Google PAIR and Microsoft HAX

| Dimension | IBM | Google PAIR | Microsoft HAX |
|---|---|---|---|
| Standout feature | AI/Human Context Model; ethics pillars; open source toolkits | Bridge document UX↔ML; reward function as design artifact | 18 evidence-based guidelines; temporal organisation |
| Transparency mechanism | Carbon for AI label + popover; factsheets | Explainability rubric (22 information types) | Social bias and user control guidelines |
| Open source tools | AIF360, AIX360, AR360 (genuine, well-maintained) | Not a primary focus | Not a primary focus |
| Enterprise governance | watsonx.governance (commercial product) | Not commercially productised | Azure AI/ML governance tooling |
| Data practices | Layer 3 team activities | Chapter 6 (strongest in field) | Not addressed |
| Reward function | Not explicitly addressed | Central (Chapter 1) | Not addressed |
| Accountability | Weakest area | Weakest area | Weakest area |

**IBM's distinguishing characteristics:**
1. Open source research toolkits that predate most competitors (AIF360 released 2018)
2. A commercial governance product (watsonx.governance) that embeds principles into
   enterprise workflows
3. Carbon for AI making explainability a UI component standard, not just documentation

---

## Honest Assessment — What IBM Commits To vs. Claims

**What is genuinely useful:**
- The open source toolkits (AIF360, AIX360) are real, well-maintained, and freely available
- Carbon for AI is concrete and ships in product code
- The Granite LLM Responsible Use Guide received independent Stanford validation
- The six generative AI design principles (CHI 2024) are specific and actionable

**What is weaker than it appears:**
- The ethics pillars and design principles carry no binding enforcement mechanism.
  The Responsible Technology Board reviews policies, not individual product decisions at scale.
- watsonx.governance is a paid enterprise product — governance as a revenue line creates
  different incentives than governance as a public commitment
- IBM's own data: 79% of executives say AI ethics is important, but less than 25% have
  operationalised ethics governance. IBM presents this as an industry problem it is solving
  while also selling into exactly this environment
- No published independent audits assessing whether IBM products comply with IBM's own
  stated design principles were found in this research

**The commercial incentive tension:**
IBM's positioning of trustworthy AI as a commercial offering (watsonx.governance)
creates an incentive structure where governance is a revenue line rather than a public
good. This differs from PAIR (free, open methodology) — though IBM's open source
toolkits partially offset this.

---

## Connections to Other Notes

- *PAIR Guidebook* — PAIR stronger on reward function and data practices; IBM stronger
  on enterprise governance tooling and explainability as a UI component standard
- *Microsoft 18 Guidelines* — all three frameworks weak on accountability and structural
  fairness; IBM unique in having open source toolkits that operationalise fairness metrics
- *Ethics as defanging* — IBM's principles documents have the same gap: stated commitments
  without binding enforcement, measured by IBM itself
- *Canca's PiE model* — IBM's ethics pillars (Accountability, Value Alignment, Explainability,
  Fairness, Privacy) are primarily instrumental principles without a declared core value
  framework or priority ordering when they conflict
- *Honest build sequence* — IBM's Layer 3 Team Essentials (Intent, Data, Understanding,
  Reasoning, Knowledge) maps directly onto the planning phase of the honest build sequence

---

## Key Insight

> IBM's framework is the most operationalised of the three major industry frameworks —
> Carbon for AI, AIF360, AIX360, and watsonx.governance all ship as real artifacts,
> not just documents.
>
> But operationalisation without enforcement is compliance theatre with better tooling.
> The tools exist. The binding requirement to use them does not.
> The Responsible Technology Board reviews policy. It does not audit products.
>
> IBM's distinguishing contribution: making explainability a UI component standard.
> The gap that remains: making compliance a product requirement, not a design choice.
