# Enterprise AI Strategy — The Real State of Deployment

*Notes from: "A Playbook for Crafting AI Strategy," MIT Technology Review Insights
in partnership with Boomi, July 2024. Survey of 205 C-suite executives across
11 industries, all organisations with $500M+ annual revenue, global sample.*

*Personal study notes — original analysis and synthesis. Not a reproduction of
course material.*

---

## The Headline Gap

**What companies say:**
- 95% are already using AI
- 99% expect to in the future

**What companies are actually doing:**
- Only **5.4% of US businesses** were using AI to produce a product or service in 2024
- **76% have deployed AI in only 1-3 use cases** — still in pilot mode
- Half expect to fully deploy AI across all business functions within two years

This is the most important finding in the report. The hype is enormous. The deployment
is narrow. There is a vast gap between "we are using AI" (which includes things like
ChatGPT for email drafting) and "AI is integrated into core business operations."

The report exists to help companies cross that gap. Its honest conclusion: the gap
is not a technology problem. It is a data infrastructure, governance, and
organisational capability problem.

---

## Why the Pilot-to-Scale Gap Exists

### The Five Real Blockers

**1. Data quality** — 49% overall, 52% of largest companies
The most common single blocker. Bad data going in, bad AI coming out. Not fixable
by buying a better model. "AI is a science and a tool. You still have to do all of
the hard work around data governance." — Kevin Collins, Charli AI

**2. Data infrastructure and pipelines** — 44% overall, 55% of largest companies
The plumbing is wrong. Legacy systems that cannot talk to each other, cannot feed
clean data to AI systems. The bigger the organisation, the worse this problem.

**3. Data integration tools** — 40% overall
The systems do not connect. Data exists in silos — contracts, PDFs, spreadsheets,
legacy databases — and the tools to integrate them are absent or inadequate.

**4. Governance, security, and privacy** — 45% say this is the biggest brake on speed;
65% of the largest companies say this. The bigger you are, the more you have to
lose and the more regulatory scrutiny you face.

**5. Legacy infrastructure** — the "it's kind of working" problem. One person knows
how to maintain the older technology. Sunk costs prevent necessary transition.
90% of enterprise data is unstructured and sitting in systems that cannot be
easily fed to AI.

### The Squeezed Middle Problem

- Large companies ($10B+): have resources to invest, moving fastest
- Small companies: can move fast with less to lose
- Mid-sized companies ($500M-$1B): 47% cite budget as the biggest obstacle vs 22%
  survey average — need AI to stay competitive but cannot afford the infrastructure

---

## The Data Core — What Actually Enables AI

### Data Liquidity

The key concept from the report: not data volume, not data centralisation, but
**data liquidity** — the ability to get the right data to the right place at the
right time.

> "Organizations with high data liquidity — the ability to get the right data at
> the right time and place — will be most successful with AI."
> — Matt McLarty, CTO, Boomi

Data liquidity requires flexible, harmonised, scalable IT infrastructure that can
handle increasing volumes and varieties of data without disrupting existing operations.
Organisations that have this will win. Organisations with large data lakes that became
data swamps will struggle.

### The Data Lake Warning

A centralised data lake is not sufficient on its own. Without governance over data
lineage — how data flows from one model to the next — it becomes a data swamp.

> "It's not enough to just have a big data lake, because that's going to become a
> data swamp; you have to have good governance over the data lineage and how it
> flows from one model to the next." — Kevin Collins, Charli AI

### Metadata — The Underrated Asset

90% of enterprise data is unstructured. Metadata — data about data — is what makes
unstructured data usable for AI. Without a metadata strategy, organisations are
sitting on assets they cannot deploy.

Metadata connects data sources from different systems through a common language.
The choice of metadata language matters for specific domains: Darwin Core for
biological specimens, VRA Core for visual culture — the same principle of contextual
specificity we identified in the dataset geography argument.

### Data Management Principles (from the report)

- Track data lineage — maintain quality and integrity as data moves between models
- Prioritise data **contextualisation** over data centralisation — metadata first
- Identify core capabilities, avoid over-reliance on legacy infrastructure
- Optimise cross-functional communication on AI data requirements

---

## The Cost Reality

**Training costs (not enterprise costs — platform costs):**
- GPT-4 training: $78 million in compute
- Gemini Ultra training: $191 million in compute

**What enterprises actually pay:**
- Data management and monitoring
- Compliance infrastructure
- Talent — hiring or upskilling
- Energy consumption
- GPU infrastructure for inference
- Ongoing model maintenance to keep systems relevant

**The build vs buy conclusion** — confirmed by all four executives interviewed:
Most organisations should not build their own LLMs. Building is expensive, requires
massive infrastructure, and the value is time-limited. The path is:
1. Fine-tune off-the-shelf models
2. Build on existing platforms
3. Integrate AI into existing workflows

> "The companies that don't put the AI cart before the business problem horse are
> going to be better positioned." — Matt McLarty, CTO, Boomi

### ROI Measurement — The Evolving Framework

**Wave 1 — Cost savings (current dominant frame):**
Motorola: tracks hours taken with vs without AI. Klarna: AI equivalent to 700
customer service agents.

**Wave 2 — Revenue enablement:**
Using AI to grow, not just cut. "The mindset is shifting to using AI as an enabler
for revenue growth, not just cost savings." — Amy Machado, IDC

**Wave 3 — Strategic positioning:**
AI as competitive moat. The most valuable use cases are those that create unique
competitive advantage — not the generic chatbot that every competitor can also deploy.

**The hardest ROI to measure:** the creative and innovative work that AI enables
by freeing human time from routine tasks. This is the Prediction Machines point
made concrete — AI handles prediction, humans do judgment, the judgment becomes
more valuable and harder to quantify.

---

## The Caution Signal — What Executives Actually Think

**98% of companies say they are willing to forego first-mover advantage** to ensure
safe and secure AI deployment. For the largest companies ($10B+), this is 100%.

This directly contradicts the "move fast or be left behind" hype narrative. The
actual C-suite consensus: we would rather be second and safe than first and wrong.

**The legal catalyst:** Air Canada was held liable for misleading information
provided by an AI chatbot. That case is concentrating minds on liability.

### New Risks from Generative AI

**Prompt injection:** adversarial inputs that make models reveal sensitive information
or bypass controls. A Stanford student exposed this in Bing Chat (2023) by instructing
it to "ignore previous instructions" — revealing its hidden system prompt.

**Data poisoning:** malicious data injected into training sets to corrupt model
behaviour.

**Pipeline leakage:** data flowing through LLM infrastructure being exposed to
third parties.

**Hallucinations:** confidently wrong outputs with real-world consequences. In
financial services, credit risk assessments built on biased training data will
amplify existing discrimination. In healthcare, wrong diagnostic AI causes harm.

**The cybersecurity paradox:** AI creates new attack surfaces at "machine scale
rather than human scale," but AI is also the best tool for defending against
machine-scale attacks. The solution to AI-created security problems is partly
more AI — but with human guardrails.

---

## The Regulatory Landscape

- 1 AI law globally in 2016 → 37 in 2022 → accelerating
- **EU AI Act:** risk-based framework. Highest requirements for critical infrastructure,
  employment, law enforcement. Conformity assessment before market. Low-risk systems
  (chatbots) subject to transparency requirements.
- **EU AI Act prohibitions:** social scoring and mass surveillance banned outright
- **US Biden Executive Order (October 2023):** AI safety standards, AI Safety and
  Security Board, mandatory safety test disclosure for most powerful systems.
  *(Note: this was revoked in early 2025 under the Trump administration — a development
  this July 2024 report predates.)*

**AI explainability** is becoming both a compliance requirement and a trust-building
tool. Companies that can explain their AI's decisions will have regulatory and
commercial advantage as requirements tighten.

---

## The Key Finding for Module 6 — AI for Strategic Decision Making

**The industry-specific use case insight:**
General-purpose AI use cases (chatbots, email drafting) are easy to implement but
provide no competitive advantage — because competitors implement them equally easily.

The most valuable AI use cases are:
- Industry-specific (AI for drug discovery, AI for drywall finishing optimisation)
- Business-unique (AI that leverages your specific data, relationships, and processes)

Larger companies are more likely to develop these — they have the data, infrastructure,
and domain knowledge to build something competitors cannot easily replicate.

**The strategic decision-making implication:**
The question for strategic AI is not "which model is best?" but "where in our
specific business does cheap prediction create the most value, and what does our
data situation enable us to do that competitors cannot?"

This is the Prediction Machines question applied to enterprise context: where does
prediction become cheap, what does that enable, and what judgment capabilities do
we need to build to take advantage of it?

---

## Connections to Course Material

**The more data fallacy (module 2):**
"Data quality is a major limitation for AI deployment." Half of respondents cite it.
This confirms the COMPAS and Amazon hiring algorithm finding: more data from bad
sources does not fix the AI. Better, more representative, accurately labelled data
does. Quality beats quantity.

**The governance finding (modules 4-5):**
45% cite governance, security, and privacy as the biggest brake. This is not a
fringe concern — it is the dominant operational constraint for the largest
organisations. The regulatory argument we built in module 4 is not theoretical.
It is the daily operational reality of enterprise AI deployment.

**The Prediction Machines framework (module 6):**
The report confirms the Agrawal/Gans/Goldfarb thesis at the enterprise level.
The bottleneck is not model capability — it is data infrastructure, the input to
prediction. Companies that solve the data quality and liquidity problem will be
able to deploy AI prediction effectively. Companies that do not will have access
to the same models and produce worse results.

**The Canca PiE argument:**
The industry-specific use case finding confirms the PiE model's core claim: the
most valuable AI is designed for specific purposes with specific stakeholders in
specific contexts — not deployed generically across every business function.
"You can deploy AI capabilities, but if they don't provide true business value,
you're just wasting money to say you did something cool." — Amy Machado, IDC

**The ethics-as-defanging critique:**
The report is sponsored by Boomi — a data integration platform vendor. Its
recommendations (invest in data infrastructure, choose the right vendors and
partners, prioritise data liquidity) are genuinely useful and also serve Boomi's
commercial interests. This is not a disqualification. It is the same conflict of
interest we noted throughout: the people producing the framework benefit from
its adoption. Read the advice as sound but apply the source-awareness filter.

**The building-responsibly argument:**
The 98% caution finding — companies willing to forego first-mover advantage for
safety — is the enterprise-level version of the honest build sequence argument.
The companies that built without adequate data foundations, governance, and
compliance infrastructure are now paying to retrofit. The companies that built
foundations first are "way better positioned for the AI landscape."

---

## Key Insight

> The gap between AI ambition and AI deployment is not a technology gap.
> It is a data quality gap, an infrastructure gap, a governance gap,
> and an organisational capability gap.
>
> Every one of these is addressable before the first AI model is deployed.
> The companies that addressed them first will win.
> The companies that deployed first without addressing them are now
> paying to fix what they should have built correctly from the start.
>
> "Data hygiene and rigor" is not boring infrastructure work.
> It is the competitive moat that makes AI strategy possible.
> The AI cart cannot go before the business problem horse —
> and the horse needs clean, liquid, well-governed data to run.
