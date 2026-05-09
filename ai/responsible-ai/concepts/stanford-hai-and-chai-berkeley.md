# Stanford HAI and CHAI Berkeley — Two Founding Institutes

*Research notes extracted from official websites May 2026.
Sources: https://hai.stanford.edu/about and https://humancompatible.ai/*

---

## Why These Two Matter

The earliest formalised academic responses to AI ethics, safety, and accountability
came from these two institutes. They define "human-centered AI" differently — and
that difference matters for understanding the field.

---

## Stanford HAI — Human-Centered Artificial Intelligence Institute

**Founded:** 2019
**Co-founders:** Fei-Fei Li (CS, creator of ImageNet) and John Etchemendy (former
Stanford Provost)
**Website:** https://hai.stanford.edu

### Mission (exact)

> "Stanford HAI's mission is to advance AI research, education, policy, and practice
> to improve the human condition."

> "AI should be guided by its human impact, inspired by human intelligence, and
> designed to augment, not replace, people."

### What Makes It Distinctive

HAI is a **convening institution** more than a research lab. Its power comes from
bringing economists, lawyers, psychologists, artists, engineers, and physicians into
the same conversations about AI. It spans seven of Stanford's schools — engineering,
humanities, social sciences, law, medicine, education, and business.

The definition of "human-centered" here is **normative and broad**: AI should be
built with human welfare as the guiding criterion, assessed by its societal impact,
and designed to augment human capability rather than replace it.

Time horizon: **present and near-term** — the harms, benefits, and governance
challenges of AI as it exists today.

### Research Focus Areas

| Domain | Focus |
|---|---|
| AI Foundations & Methods | Machine learning, generative AI, RL, computer vision, NLP |
| Applied AI | Scientific discovery, healthcare, mental health, education, arts |
| Ethics & Society | Fairness, transparency, policy implications |
| Human-Computer Interaction | Augmenting human capability |
| Sustainability & Equity | Environmental applications, diversity in AI |
| Governance | Foundation model governance, policy work |

### Major Programs and Outputs

**AI Index** — HAI's most consequential external output. An annual data-driven
report monitoring AI progress across: research development, technical performance,
ethics, economics, education, policy, governance, diversity, and public opinion.
Widely cited by policymakers globally. The 2025 AI Index Report is the current edition.

**Foundation Model Governance Initiative** — Rigorous inquiry into developing and
governing advanced AI tools.

**Grant programs** — Supported 348+ faculty members across all seven Stanford schools.

**National AI Research Resource (NAIRR)** — HAI has been an active advocate for this
federal infrastructure initiative.

**Global Policymakers in Residence** — Places policymakers at Stanford; reverse
fellowship places students in government.

**Fellowship programs** — Postdoctoral Fellowship, Graduate Fellows, HAI Data Science
Scholars (two-year PhD fellowships across all schools). Concentration areas include:
AI + Sustainability, Human-Computer Interaction, Equity and Diversity in AI.

### Selected Faculty

Judith Fan (Psychology), Victor Lee (Education), Allison Okamura (Mechanical
Engineering), Diyi Yang (CS), Rob Reich (Political Science), Michael Snyder
(Genetics), Jennifer Pan (Communication), Camille Utterback (Art & Art History).

The breadth is the point — HAI deliberately includes disciplines that standard
AI labs exclude.

---

## CHAI — Center for Human-Compatible AI, UC Berkeley

**Founded:** 2016
**Founder:** Stuart Russell (Professor of EECS, UC Berkeley)
**Website:** https://humancompatible.ai

### Mission (exact)

> "building exceptional AI for humanity"

> "develop the conceptual and technical wherewithal to reorient the general thrust
> of AI research towards provably beneficial systems"

### What Makes It Distinctive

CHAI's operative word is **provably**. It is not satisfied with AI that is merely
intended to be beneficial — it pursues formal, verifiable guarantees that AI systems
will behave in ways compatible with human values.

The name encodes the philosophy: human-**compatible**, not human-**centered**.
Compatible means: by construction, the AI's objectives cannot diverge from human
values — even values that are uncertain, inconsistent, or not yet fully known.

**The philosophical move that makes CHAI unique:**

Standard AI design gives the system a fixed reward function to optimise. CHAI argues
this is wrong in principle — humans cannot fully specify their values in advance.
Any initial formal specification of human values is bound to be wrong in important ways.

The solution: build **uncertainty about human values directly into the AI's objective
function**. The AI then has an incentive to observe human behaviour, ask clarifying
questions, and defer to humans in proportion to its uncertainty — because the AI's
objective is to maximise a distribution over possible human value functions, not a
single fixed one.

This is **inverse reinforcement learning applied to the alignment problem**: the AI
learns what humans value from observing them, rather than being told what to optimise.

Time horizon: **long-term and existential** — risks from advanced AI systems, not
just current applications.

### Research Focus Areas

| Domain | Details |
|---|---|
| Value Alignment & Inverse RL | Learning human preferences, reward specification, preference-based RL |
| Foundations of Rational Agency | RL representation complexity, causal modelling, sequential decision-making |
| Human-Robot Cooperation | Shared autonomy, human motion prediction, assistive technology |
| Models of Human Cognition | Learning, reasoning, communication, pragmatics |
| Multi-Agent Perspectives | Game theory, cooperative/competitive settings, institutional design |
| Governance & Risk | Autonomous weapons, existential risk taxonomy, AI policy |

**Societal-scale risk areas explicitly named:** lethal autonomous weapons, future of
employment, public health and safety, AI alignment, existential risks from advanced AI.

### Key People

**Stuart Russell** — Founder, Professor of EECS, Berkeley. Author of *Human Compatible:
Artificial Intelligence and the Problem of Control* (2019) — CHAI's intellectual
manifesto. Also co-author of the standard AI textbook *Artificial Intelligence: A
Modern Approach*.

**Pieter Abbeel** — Professor of EECS, Berkeley. Robotics, learning from demonstration.

**Anca Dragan** — Professor of EECS, Berkeley. Founder of InterACT Lab. Human-robot
interaction, shared autonomy.

**Tania Lombrozo** — Professor of Psychology, Berkeley. Cognitive science, human
reasoning.

**Tom Griffiths** — Professor of Psychology and Cognitive Science, Princeton.

**Mark Nitzberg** — Executive Director. Also Head of Strategic Outreach for BAIR
(Berkeley AI Research).

**Brian Christian** — Affiliate. Author of *The Alignment Problem* — the most
accessible account of what CHAI works on.

**Alison Gopnik** — Affiliate. Professor of Psychology, Berkeley. Developmental
cognition — understanding how humans learn is foundational to building AI that can
learn human values.

### Notable Alumni — Where CHAI's Impact Goes

CHAI's alumni network is the who's-who of the AI safety field:

| Person | Current role |
|---|---|
| Adam Gleave | Founder, FAR AI |
| Dan Hendrycks | Director, Center for AI Safety |
| Dorsa Sadigh | Assistant Professor, Stanford |
| Dylan Hadfield-Menell | Assistant Professor, MIT |
| Jaime Fernandez Fisac | Assistant Professor, Princeton |
| Rohin Shah | Research Scientist, Google DeepMind |
| Alex Turner | Research Scientist, Google DeepMind |

### Notable Publications

- *Human Compatible* (Stuart Russell, 2019) — mainstream manifesto for the alignment problem
- "Open Problems and Fundamental Limitations of RLHF" — examines core challenges in aligning AI via human feedback
- "TASRA: A Taxonomy of Societal-Scale Risks from AI" — governance framework
- Research on political neutrality in AI systems, offline RL via supervised learning

### Funding

- Open Philanthropy
- Future of Life Institute
- The Leverhulme Trust
- CITRIS (Center for Information Technology Research in the Interest of Society)

### Partner Organisations

Leverhulme Centre for the Future of Intelligence (Cambridge), Center for Long-Term
Cybersecurity (Berkeley), Berkeley Existential Risk Initiative (BERI), Kavli Center
for Ethics, Science, and the Public, ICT4Peace Foundation.

---

## The Key Difference

| Dimension | Stanford HAI | CHAI Berkeley |
|---|---|---|
| **Definition** | AI guided by human impact, augments not replaces | AI formally compatible with human values — "provably beneficial" |
| **Core problem** | AI's broad societal impact today | The control/alignment problem — advanced AI pursuing wrong goals |
| **Scope** | Entire AI ecosystem, all domains | Alignment, value learning, long-term safety |
| **Time horizon** | Present and near-term | Long-term and existential |
| **Technical emphasis** | Institutional — convening, grants, reports | Technical — formal methods, inverse RL, provability |
| **Vocabulary** | "human-centered," "augment not replace" | "human-compatible," "provably beneficial," "value uncertainty" |
| **Flagship output** | AI Index (annual data report) | *Human Compatible* + formal alignment research |
| **Policy style** | Active advocacy, policymakers-in-residence | Academic publications, governance frameworks |

---

## Why Both Matter

**HAI** defines the governance agenda — its AI Index is what policymakers read.
Its interdisciplinary structure is the institutional model for taking AI seriously
as a civilisational challenge, not just a computer science problem.

**CHAI** defines the technical alignment agenda — the formal question of how you
build an AI system that is guaranteed to pursue human values rather than arbitrary
objectives. Its alumni run the major AI safety organisations. Its intellectual
framework — uncertainty over human values, inverse RL, deference to humans — is
the foundation of most serious technical alignment work.

Together they represent the two axes of the field:
- HAI asks: *what should AI do for humanity, and how do we govern it?*
- CHAI asks: *how do we build AI that, by construction, cannot do things contrary to what humanity values?*

The second question is harder and more important as AI systems become more capable.
The first question is more urgent today.

---

## Connection to What We've Discussed

- **Stuart Russell's control problem** is the technical version of Weizenbaum's
  deciding vs. choosing distinction — the question of whether AI systems can be
  trusted to exercise something like judgment, and what guarantees we need
- **CHAI's value uncertainty framework** is the technical version of the values
  contestedness argument from topic 04 — you cannot encode a fixed objective function
  because human values are genuinely uncertain and contested
- **HAI's AI Index** is the empiricist tool the course calls for — systematic
  measurement and tracking of AI's effects rather than optimistic assumption
- **The alumni network** — FAR AI, Center for AI Safety, the safety teams at
  Google DeepMind — these are the organisations you want to pay attention to if
  you are interested in where genuine technical safety work is happening
