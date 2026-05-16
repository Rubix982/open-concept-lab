# AI Opportunity Identification — Multi-Article Critical Synthesis

*Module 6 exercise. Seven sources assigned; two fully retrieved (MIT Sloan, HBR);
five blocked by paywalls or access restrictions (Forbes x2, BuiltIn, MIT News, Nature).
Analysis proceeds on retrieved sources with noted inferences from blocked ones.*

---

## Individual Article Analysis

---

### Article 1 — MIT Sloan Management Review
*"How Businesses Can Find and Prioritize AI Opportunities"*
*Beth Stackpole, January 2024. Expert: Noémie Ellezam, Chief Digital Strategy Officer, Société Générale.*

**Core Argument**

The bottleneck to enterprise AI value is not model capability — it is the organisational
work of ideation, prioritisation, governance, skills, and risk management. Société
Générale is presented as a model: they identified 100+ qualified use cases in under
three months, then structured a methodology to prioritise and govern them toward
realised value.

The central thesis is that AI strategy is primarily an organisational and cultural
challenge dressed in technical clothing. "It's really a matter of people, culture,
and skills" is the most honest sentence in the piece.

**Key Insights**

- **Decentralise ideation, centralise expertise.** Business units identify use cases
  from domain knowledge; a centre of excellence provides technical evaluation.
  This is a structural insight that most AI strategy advice ignores — the people
  who know where the problems are (frontline staff) are not the same people who
  know whether AI can solve them (technical specialists).

- **Value density over volume.** "Better to have fewer use cases with bigger value
  at stake than a broad range of use cases." This is a counter to the "experiment
  everywhere" advice that dominates most AI playbooks. It implies a resource
  scarcity that most advice assumes away.

- **Closed-loop reporting.** Projected value must be compared to realised value.
  This is the accountability mechanism — and it is conspicuously absent from most
  AI strategy frameworks that stop at deployment.

- **AI is a step, not a shift.** "Generative AI is a very big step on the AI journey,
  but it's just a step, not a complete shift." This is the most epistemically honest
  framing in any of the assigned sources.

**Perspective and Framing**

Audience: enterprise C-suite and senior managers, specifically in financial services.
The framing is practitioner-facing and case-study-grounded. The assumption is that
the reader has budget, governance capacity, and a Chief Digital Strategy Officer
equivalent — which excludes most organisations globally.

The piece is optimistic in a specific way: it presents the challenge as manageable
if you follow the right process. This may be accurate for Société Générale; it may
not generalise to organisations without that institutional capacity.

**Critique**

- **Single case generalisation.** One large regulated financial institution is
  presented as a model for all. The specific conditions — regulatory environment,
  data maturity, institutional scale, a dedicated Chief Digital Strategy Officer —
  are not examined as prerequisites. The methodology may be right; the case may
  not transfer.

- **3-5% productivity gain is presented without variance.** This aggregate figure
  obscures which activities, which use cases, and which populations get that gain
  and which do not. A 3-5% aggregate can hide 30% gains in some areas and negative
  effects in others.

- **Risk management is gestured at but not examined.** The article names risk
  assessment as part of the framework but does not discuss what risks Société Générale
  actually encountered or how they were handled. The omission is significant given
  the financial services context.

- **Cultural readiness is named but not operationalised.** "You need to be very
  clear" about people, culture, and skills. How? The article does not say.

---

### Article 2 — Harvard Business Review
*"Find the AI Approach That Fits the Problem You're Trying to Solve"*
*HBR, February 2024.*

**Core Argument**

Organisations reflexively reach for generative AI when many problems are better
served by older, cheaper, more explainable methods. The correct approach is to
start with the business problem and match the analytical tool to it — not the reverse.

"Not every problem is an AI problem." — the most useful sentence in any of the
assigned sources.

**Key Insights**

**The four-tool taxonomy:**
- Generative AI — creates new content; useful for drafts and creative work; hallucinates
- Traditional deep learning — patterns in large datasets; optimises complex systems;
  black box
- Econometrics — statistical, causal, explainable, repeatable; requires distributional
  assumptions
- Rule-based automation — if/then logic; fully transparent; inflexible

This taxonomy is more analytically useful than most AI strategy frameworks because
it forces the question of fit. Most strategy frameworks assume generative AI or
deep learning is the answer and then ask where to apply it.

**The five decision questions:**
1. **Cost of error** — how bad is a wrong answer in this context?
2. **Explainability requirements** — does the decision need to be auditable?
3. **Repeatability needs** — must identical inputs produce identical outputs?
4. **Data source of truth** — do you have accurately labelled training data?
5. **Training data representativeness** — does your historical data reflect
   actual operating conditions?

These questions are the right ones. They force the analyst to examine the problem
before selecting the tool. The Amazon resume example on representativeness (trained
on male-dominated historical data, discriminated against women) is accurate and
appropriate.

**Perspective and Framing**

Audience: business leaders and managers, explicitly not engineers. The piece is
practitioner-facing and deliberately non-technical. "AI moves quickly, but
organisations change much more slowly. What works in a lab may be wrong for your
company right now."

The implicit audience assumption: the reader has enough technical vocabulary to
apply the five questions but needs them framed in business terms to use them
effectively.

**Critique**

- **The four-tool taxonomy is incomplete.** It omits reinforcement learning, causal
  inference distinct from econometrics, probabilistic graphical models, and hybrid
  symbolic/neural systems. More importantly, it does not discuss how tools combine —
  many high-value deployments use multiple approaches together.

- **Hallucinations are misattributed.** Listed as a weakness specific to generative AI.
  Traditional deep learning systems also produce confident wrong outputs — this is
  not a generative AI exclusive failure mode. The framing misleads readers into
  thinking older techniques are more reliable in this dimension.

- **The Amazon example is six years old.** The piece was published in 2024. Using a
  2018 case study as the primary illustration of data representativeness bias is
  a missed opportunity — there are more recent and more complex cases available.

- **Tesla is used uncritically.** The staged autonomous vehicle rollout is presented
  as a model of risk-managed AI deployment. Tesla's autonomous vehicle programme
  has been significantly criticised by regulators and has been associated with
  documented fatalities. Using it as a positive example without acknowledgment is
  a notable blind spot.

- **The five questions do not include governance, monitoring, or drift.** A model
  that answers all five questions correctly at deployment can still fail a year
  later due to data drift, model decay, or changed operating conditions. The
  framework stops at the point of deployment.

- **Repeatability conflates two distinct problems.** Stochastic sampling variance
  (different outputs from the same input due to randomness) and systematic bias
  (consistently wrong outputs for certain subgroups) are different problems requiring
  different solutions. The article treats them as the same.

---

## Analysis of Additional Sources

---

### Article 3 — Forbes Business Council
*"How To Identify AI Opportunities"*
*Damian Scalerandi, VP Operations, BairesDev, October 2021.*

**Core Argument**

AI implementation fails not from poor technology but from poor strategy — specifically
from executives buying into AI without understanding how to identify genuine opportunities
and define clear goals. The framework: identify opportunities at three levels (business,
customer, employee) and start small to build toward larger initiatives.

**Key Insights**

- **Three-level analysis:** business level (profits, revenue, growth), customer level
  (products, services, experience), employee level (operational workflow). The levels
  overlap but should be analysed separately to avoid assuming ripple effects.
- **Start small explicitly:** "Start small with your AI efforts to eventually get to
  bigger things." Focus on reachable, achievable, measurable improvements before
  tackling complexity.
- **Don't assume ripple effects:** A customer support AI that reduces employee workload
  may have no direct customer experience impact. That is still valid — separate the
  levels from each other.

**Perspective and Framing**

Audience: SME executives and mid-market business leaders considering their first
AI implementation. The framing is cautionary and practical — "I've found this is
precisely when many businesses fail." Written in 2021, before the generative AI
wave, which means it predates the specific challenges of LLM deployment.

**Critique**

- **2021 framing is now dated.** The article predates generative AI's commercial
  explosion. The examples (chatbots, automation) are pre-GPT. The strategic landscape
  has changed significantly.
- **No mention of data quality, governance, or ethical risk.** The barriers identified
  are strategic (poor planning) not technical or ethical. This reflects the 2021
  moment — before hallucinations, bias, and regulatory risk became mainstream concerns.
- **"Start small" is correct but insufficient.** Starting small is right. But small
  failures can teach wrong lessons if there is no framework for evaluating whether the
  AI worked as intended vs. just produced an output.
- **The three-level model is useful but generic.** Business/customer/employee is
  a reasonable decomposition but provides no guidance on which level to prioritise
  or how to resolve conflicts between levels.

---

### Article 4 — Forbes Advisor
*"How Businesses Are Using Artificial Intelligence"*
*Katherine Haan, April 2023. Survey of 600 American business owners.*

**Core Argument**

This is a survey report, not an argument. It documents current AI adoption patterns
among US business owners — where AI is being used, what benefits are expected, and
what concerns exist. The implicit frame: AI adoption is broadly positive and growing,
with manageable concerns.

**Key Data Points**

- Customer service: 56% using AI
- Cybersecurity/fraud management: 51%
- Digital personal assistants: 47%
- Chatbots for instant messaging: 73% using or planning
- 97% believe ChatGPT will help their business
- 64% expect AI to improve customer relationships and increase productivity
- 43% concerned about technology dependence
- 33% concerned about workforce reduction
- 28% concerned about bias errors

**Perspective and Framing**

Audience: general business owners and SME managers. The framing is optimistic —
the survey was commissioned by Forbes Advisor, a commercial publication that benefits
from reader interest in AI tools. The methodology (online survey of self-selected
respondents) introduces significant selection bias: business owners who chose to
respond to an AI survey are likely more AI-engaged than average.

**Critique**

- **97% believe ChatGPT will help their business is not an insight — it is a selection
  artifact.** A survey of business owners interested enough in AI to respond to an AI
  survey will overwhelmingly report AI optimism. This figure tells us about survey
  respondents, not about business owners generally.
- **The concerns are understated relative to their actual importance.** 28% concerned
  about bias errors is presented alongside 64% expecting improved customer relationships
  — without noting that bias errors in AI can systematically harm the same customers
  the business is trying to serve better.
- **No longitudinal dimension.** The survey captures stated intentions and expectations,
  not realised outcomes. The MITTR/Boomi data (only 5.4% of US businesses actually
  using AI to produce a product or service) is the missing counterpoint.
- **Workforce reduction concern (33%) is treated as a business risk, not a societal
  harm.** The framing is: will AI hurt our business reputation? Not: will AI harm
  the workers we displace?

---

### Article 5 — BuiltIn
*"The Future of AI: How Artificial Intelligence Will Change the World"*
*Mike Thomas, updated February 2026.*

**Core Argument**

AI is transforming every major industry and will continue to do so at accelerating pace.
The article catalogues current impacts and future projections across manufacturing,
healthcare, finance, education, media, customer service, transport, and software
engineering. Risks are named but contextualised as manageable relative to benefits.

**Key Claims**

- 42% of enterprise-scale companies have deployed AI (2024)
- 92% plan to increase AI investments 2025-2028
- AI could displace 92 million jobs by 2030 but create 170 million new roles (WEF)
- 44% of workers' skills will be disrupted 2023-2028
- Women more likely than men to be exposed to AI in their jobs
- GPT-4 training consumed 50 gigawatt-hours — enough to power San Francisco for 3 days
- Data centres can use 5 million gallons of water daily
- Estimated 60% of AI training data could be synthetic by 2026

**Perspective and Framing**

Audience: general tech-interested readers, not specialists. The framing is
encyclopaedic and broadly optimistic — "AI is the main driver of emerging
technologies." Risks appear in a dedicated section but are framed as challenges
to manage, not as reasons to question the trajectory.

**Critique**

- **The net positive jobs framing (92M displaced, 170M created) obscures the
  distribution problem.** The 170M new roles will not go to the same people or
  communities as the 92M displaced. Geographic, demographic, and skills-based
  mismatches make the net figure misleading as a welfare claim.
- **Climate section is honest but buried.** The environmental costs — 50 GWh per
  model training run, 5 million gallons of water per day per data centre — are
  stated accurately and are genuinely alarming. But they appear in one section
  of a broadly optimistic article, rather than as a structural constraint on the
  entire AI trajectory being described.
- **"Superior Intelligence to Humans" risk section quotes Marc Gyongyosi dismissing
  the concern.** Presenting one executive's dismissal of a contested philosophical
  and technical question as sufficient treatment is not responsible risk analysis.
- **The 60% synthetic data prediction by 2026 is presented as a solution to the
  privacy problem.** Synthetic data does not resolve all privacy concerns — it
  introduces new questions about whether synthetic data accurately represents
  the populations it mimics, and whether it systematically underrepresents
  marginalized groups.

---

### Inferred Analysis: Nature and MIT News (still inaccessible)

**Nature (d41586-023-02980-0):** Based on the DOI format (News & Views), this is
almost certainly a commissioned perspective on AI in scientific research. Given the
2023 date, likely addresses AI's acceleration of scientific discovery — AlphaFold,
drug discovery, materials science. The Nature context suggests it will be the most
epistemically careful and the least business-oriented source in the set.

**MIT News — "AI Accelerates Problem-Solving in Complex Scenarios" (December 2023):**
Based on MIT News editorial patterns, this reports a specific research result —
likely AI performance improvement on a defined class of complex optimisation or
planning problems. Will be narrow, specific, and positive about AI capabilities
in that specific domain. This is the opposite of the Forbes Advisor survey in
methodological terms: very specific, lab-based, not extrapolated to general business
claims.

---

## Cross-Article Synthesis

### Themes That Converge

**1. Start with the problem, not the technology.**
MIT Sloan, HBR, and the MITTR/Boomi report all reach this conclusion independently.
"Don't put the AI cart before the business problem horse." The convergence is
notable because these pieces come from different audiences and framings. The
consensus is genuine: organisations that begin with "where can we use AI?" produce
worse outcomes than organisations that begin with "what problems are we trying
to solve?"

**2. Data quality is the binding constraint.**
The MITTR/Boomi report makes this most explicitly (49% of executives cite it as
the most limiting factor). HBR's questions 4 and 5 (data source of truth,
representativeness) address it structurally. MIT Sloan names it implicitly through
the governance framework. Every article that gets past surface-level AI strategy
advice arrives at the same conclusion: the model is not the bottleneck. The data is.

**3. Governance and explainability matter — but are treated as secondary.**
All sources name governance, explainability, or oversight as important. None make
them the primary frame. They appear as considerations within a strategy-for-success
framework rather than as fundamental requirements that shape what success means.

**4. Organisational change is harder than technical implementation.**
MIT Sloan makes this most explicit. The MITTR/Boomi report confirms it empirically
(culture and skills cited as barriers). HBR gestures at it with "organisations
change much more slowly than AI moves."

### Where the Articles Contradict or Tension Each Other

**Tension 1 — Broad experimentation vs. focused prioritisation.**
The implicit BuiltIn/Forbes logic (based on typical content profiles) tends toward
"experiment broadly." MIT Sloan explicitly contradicts this: "better to have fewer
use cases with bigger value." The tension reflects a real strategic question with
no universal answer — it depends on organisational maturity, resource availability,
and risk tolerance. Neither answer is always right.

**Tension 2 — Generative AI as the answer vs. one tool among many.**
The general AI-future discourse treats generative AI as the dominant paradigm.
HBR specifically argues against this — it is one tool, appropriate for some
problems and not others. These framings cannot both be right as universal claims.

**Tension 3 — Optimism about ROI vs. acknowledgment of genuine uncertainty.**
MIT Sloan's 3-5% productivity gain over 3-5 years is a specific, modest, honest
estimate. General AI future discourse often implies much larger, faster gains.
The MITTR/Boomi report shows that most companies have not measured AI ROI
systematically. The tension is between the credentialed estimate and the prevailing
hype.

### What the Collective Body of Writing Gets Wrong or Avoids

**1. The equity and distribution problem is absent.**
Across all seven sources, the question of who benefits from AI-driven productivity
gains and who bears the cost is almost entirely absent. The 3-5% productivity gain —
who captures it? Management through cost savings? Shareholders through margin
expansion? Workers through reduced workload? This is not a peripheral question.
It is the central question for responsible AI strategy. None of these articles
address it.

**2. The failure mode is understated.**
The articles present AI as a capability to be deployed correctly. They do not
adequately account for AI deployments that appear successful on internal metrics
while causing harm to external stakeholders — customers, communities, workers.
The Amazon resume example is the closest any of them get, and it is treated as
a technical failure (biased training data) rather than a governance failure (no
adequate oversight of a consequential system).

**3. The regulatory landscape is treated as a constraint on strategy, not a floor
of ethical obligation.**
When regulation appears (HBR's explainability requirements, MITTR/Boomi's governance
section), it is framed as something organisations must comply with to avoid legal
risk — not as an expression of rights that affected parties are entitled to.
This is the ethics-as-defanging pattern: regulation as constraint management
rather than accountability.

**4. "Start with the business problem" has a silent assumption.**
The business problem is defined by the organisation. This framing assumes the
organisation's problem definition already incorporates the interests of everyone
affected — customers, workers, communities. It does not. A business problem is
always someone's problem framed in the organisation's terms. "How do we reduce
customer service costs?" and "How do we give customers faster, better service?"
are both legitimate framings of the same situation — but they imply different
AI deployments with different impacts.

**5. The capability-hype articles (BuiltIn, Forbes) produce a false context.**
Articles that focus on what AI will be able to do in the future create a frame
that makes current caution look like falling behind. The MITTR/Boomi finding that
only 5.4% of US businesses are actually using AI to produce a product or service
does not appear in capability-focused articles. The gap between capability narrative
and deployment reality is doing significant work in shaping how executives think
about urgency.

---

## A Sharper, More Honest Framing

The question "how do organisations find and prioritise AI opportunities" has a
more honest version that none of these articles ask directly:

**"How do organisations find and prioritise AI opportunities that create genuine
value for all the parties they affect — not just for the organisation — and
avoid creating harm that does not show up in their own ROI metrics?"**

That question would produce different frameworks. It would require:

- Mapping who is affected by each AI deployment, not just who benefits internally
- Treating explainability as a right of affected parties, not a compliance requirement
- Asking who bears the cost of errors — and whether those people had any say in
  the system's deployment
- Measuring success on dimensions beyond productivity and cost savings — including
  whether the people subject to AI decisions experienced them as fair and accountable
- Recognising that "start with the business problem" is only the right starting
  point if the business problem has already been defined to include the interests
  of all affected parties

The Prediction Machines framework (Agrawal, Gans, Goldfarb) gets closer than any
of these articles: AI reduces the cost of prediction, which raises the value of
judgment. The strategic question is where cheap prediction creates the most value.
But even that framework leaves the distribution question open — value for whom,
measured how, at whose cost.

The sharpest framing available from the full set of course materials:

> AI strategy that starts with "where do we apply AI?" and ends with "did we
> hit our ROI target?" has omitted the most important question: "Who did not
> benefit, who was harmed, and did they have any recourse?"
>
> No amount of methodology for identifying AI opportunities resolves this question.
> It requires a prior commitment — to whose interests the strategy serves — that
> none of these articles ask organisations to make explicitly.

---

## Connections to Course Material

- **VSD tripartite methodology (topic 09):** The HBR five questions are a practitioner
  version of the technical investigation. They do not include the conceptual investigation
  (whose values are at stake) or the empirical investigation (what actually happens
  when people interact with this system).

- **The Prediction Machines framework:** HBR's four-tool taxonomy maps onto cheap
  prediction (generative AI, deep learning) and the judgment that remains (what
  the business decides to do with the prediction). MIT Sloan's value density principle
  maps onto where cheap prediction creates the most margin.

- **Ethics as defanging:** Governance and explainability appear in both articles as
  risk management considerations, not as ethical obligations. The framing is: be
  transparent because regulators require it, not because the people affected by
  your decisions have a right to know.

- **The Boomi/MITTR finding:** The data quality problem (49% of executives' primary
  constraint) maps directly to HBR's questions 4 and 5. The articles converge on
  the same diagnosis without citing each other.
