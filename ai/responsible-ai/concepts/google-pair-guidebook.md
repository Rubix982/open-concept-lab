# Google PAIR Guidebook — People + AI Research (2019)

*Research notes compiled from web search, academic analyses, and official sources.
Primary source: https://pair.withgoogle.com/guidebook/
Academic sources: CHI 2023 (Liao et al., arXiv:2301.12243), HCII 2021 (McAran, Springer LNCS vol. 12783)*

---

## What PAIR Is and Why It Exists

Google's People + AI Research team (PAIR) sees its object of study as advancing
machine learning for public good. The stated mission: "for machine learning to
achieve its positive potential, it needs to be participatory, involving the
communities it affects and guided by a diverse set of citizens, policy-makers,
activists, artists and more."

The guidebook originated in 2018 as an internal exercise — approximately 100
Googlers across product and research teams co-wrote the initial guidance, led by
PAIR co-founder Jess Holbrook and UX researcher Kristie Fisher. It launched
publicly in May 2019.

**Audience:** UX designers and product managers — explicitly written to bring
human-centered thinking into AI product teams where ML engineers dominate.

**Format:** Five components per chapter: (1) design considerations text, (2) design
patterns with sensitizing examples, (3) case studies, (4) workshop kit with
facilitator guide, (5) glossary. Worksheets downloadable as PDFs.

**Best understood as:** A bridge artifact — translating ML practitioner concerns
(reward functions, training data, precision/recall) into UX language, and UX
concerns (mental models, trust, control) into terms ML engineers can act on.

---

## The Six Chapters

| # | Chapter | Core Focus |
|---|---|---|
| 1 | User Needs + Defining Success | Is AI the right solution? What does success mean for people? |
| 2 | Mental Models | How users understand and form expectations of AI systems |
| 3 | Explainability + Trust | How to calibrate user confidence in AI outputs |
| 4 | Feedback + Control | How users guide and correct AI behaviour |
| 5 | Errors + Graceful Failure | How to handle system limitations and failures |
| 6 | Data Collection + Evaluation | How to translate user needs into training data and model evaluation |

The guidebook splits into two clusters:
- **UX/trust cluster (1–3):** value, clarity, and understanding
- **Technical/AI-practitioner cluster (4–6):** training data, feedback loops, failure modes

---

## Core Framework — Four Constants

PAIR's framework is not a numbered list but a product-design philosophy grounded
in four constants that outlast any technology cycle:

**Value** — AI must add demonstrable user value. The first act of human-centered
AI design is asking whether AI is the right solution at all.

**Clarity** — Users must understand what the system can do, what it cannot do,
how it may change, and how they can improve it.

**Trust** — AI systems produce probabilistic outputs; users need enough explanation
to know when to trust. Neither over-trust nor under-trust is the goal.

**Control** — Users must be able to guide, correct, and override AI behaviour.
Automation and control are not opposites — both can be high simultaneously.

---

## Chapter-by-Chapter Detail

### Chapter 1 — User Needs + Defining Success

- Start by identifying real problems people have — observed through user research,
  data, and behavioural observation — not by finding use cases for AI technology
- **The reward function is a design artifact.** Any AI model is guided by a mathematical
  reward function (also called objective or loss function). PAIR treats this as a design
  decision that must be made cross-functionally — not delegated to ML engineers
- Optimising a proxy metric can diverge from true user benefit. Design the reward
  function for long-term user benefit, not short-term measurable proxies
- Identify how you'd define success for users (long-term benefit) vs. the system
  (model performance metrics) — these often conflict
- Share the reward function with users when possible; transparency about optimisation
  goals builds trust

**Automation vs. augmentation as deliberate choice:**
- Automate tasks that are unpleasant, repeatable, and where experts agree on correct answers
- Augment tasks that carry social or creative value and that users enjoy

### Chapter 2 — Mental Models

- Mismatched mental models lead to unmet expectations, frustration, misuse, and abandonment
- When introducing an AI product, communicate four things explicitly:
  1. What it can do
  2. What it cannot do
  3. How it may change over time
  4. How users can improve it
- Build on familiar mental models where possible; use analogies to existing experiences
- Be upfront about limitations; offering examples of known failure modes calibrates
  expectations before they are violated

### Chapter 3 — Explainability + Trust

- Focus explanations on decision-support information, not technical completeness.
  The question is "what does the user need to act?" not "how does the model work?"
- Explain what the system optimises for and what data it was trained on
  (e.g., a plant classifier trained 75% North American, 25% South American plants —
  tell users this so they can calibrate by geography)
- Place detailed technical explanations **outside** the active user flow — not inline.
  Marketing materials, onboarding screens, help documentation are the right places
- In high-stakes or onboarding situations, give users more manual control to compensate
  for lower trust
- Test confidence displays early — many user populations find numeric probabilities
  confusing; visual indicators often work better

### Chapter 4 — Feedback + Control

- Provide explicit opportunities for users to give feedback on predictions
- Communicate **time to impact** — how long before feedback affects the system?
  This is often unknown but worth surfacing when possible
- Balance automation and control: let users control the aspects of the experience
  they care about most
- In high-stakes or novel product contexts, err toward more user control over automation
- Make opting out of feedback easy — forcing feedback training degrades trust

### Chapter 5 — Errors + Graceful Failure

Classify errors by type before designing responses:

| Error type | Description | Design response |
|---|---|---|
| **User error** | Mismatched input or expectations | Guide to correct input; explain constraints |
| **System error** | Model failure or incorrect weighting | Explain how system matched input to output; give correction mechanism |
| **Context error** | System working as intended but misaligned with real-life context | Irrelevance is most common; allow user to signal context |

- Trust is most fragile during onboarding and high-stakes moments; errors at these
  points cause disproportionate trust collapse
- System errors require explanation of the match process, not just an apology

### Chapter 6 — Data Collection + Evaluation

- Gather training data that is realistic and includes real-world "noise" —
  perfectly curated datasets create brittle models
- Identify data sources collaboratively with users when appropriate
- **Fairness requires proactive effort:** conduct iterative user testing with diverse
  participants throughout development, not only at launch
- Privacy: give users explicit notice and consent for data use; communicate which
  data is shared and which is not
- Evaluate models against diverse user populations, not only aggregate metrics
- The precision/recall tradeoff is a design decision, not a purely technical default —
  expose it to the product team cross-functionally

---

## Key Design Patterns

- **Partial explanations** — surface the most decision-relevant information, not
  a complete account of model internals
- **Progressive disclosure** — reveal AI reasoning in layers: summary first, detail on demand
- **Model confidence displays** — communicate certainty; test early as users often
  misinterpret numeric probabilities
- **Precision/recall tradeoffs as design decisions** — treat as a product choice,
  not an engineering default
- **User feedback loops** — make the feedback mechanism visible; communicate
  time-to-impact
- **Graceful degradation by error type** — distinct responses for user, system,
  and context errors

---

## 13 Confirmed Actionable Guidelines

1. Ask "does this need AI?" before designing — be willing to answer no
2. Automate repeatable tasks where experts agree; augment creative and social tasks
3. Design the reward function as a product decision, not an ML implementation detail
4. Never let AI make a high-stakes decision without surfacing that it is probabilistic
5. Always tell users what the product cannot do, not only what it can
6. Put detailed explanations outside the active flow — not as inline interruptions
7. Test confidence displays early with real users
8. Tell users how feedback helps them, not only that it helps the system
9. Classify errors by type before designing error responses
10. Use realistic, noisy training data — do not over-curate
11. Give explicit notice and consent for all data collection
12. Conduct iterative usability testing with diverse participants throughout development
13. Design for diverse users from the start — do not add inclusion retroactively

---

## Comparison with Microsoft's 18 HAX Guidelines

Both emerged at CHI 2019 and represent the two dominant industry human-AI
interaction frameworks.

| Domain | PAIR Guidebook | Microsoft HAX |
|---|---|---|
| User control | Strong (Chapter 4) | Strong (G12–G18) |
| Explainability | Strong (Chapter 3) | Moderate |
| Mental models | Strong (Chapter 2) | Partial |
| Error handling | Strong (Chapter 5) | Strong |
| Data practices | Strong (Chapter 6) | Not addressed |
| Reward function design | Strong (Chapter 1) | Not addressed |
| Privacy and data governance | Moderate | Weaker |
| Diversity and fairness | Moderate | Weaker |
| Accountability | Weak | Weak |
| Environmental and social well-being | Absent | Absent |

**Key difference:** PAIR includes ML-practitioner concerns (reward functions, training
data, precision/recall) that Microsoft HAX does not. PAIR is a bridge document between
UX and ML teams. Microsoft HAX is more purely interaction-focused and better suited
to evaluating specific UI decisions against a checklist.

**Key similarity:** Both emphasise user control, graceful error handling, and
calibrated trust as core responsibilities of AI product teams.

---

## What Academic Analysis Found

**CHI 2023 (Liao et al.) — How Practitioners Actually Use the Guidebook:**

31 interviews with designers and product managers found practitioners use the
guidebook for four purposes beyond its intended design guidance:

1. **Education** — building AI/ML literacy among team members
2. **Developing internal resources** — adapting guidebook content into company-specific playbooks
3. **Cross-functional alignment** — bridging UX, PM, and engineering
4. **Gaining credibility** — advocating for user-centered approaches with leadership

The guidebook's technical content (precision-recall tradeoffs, confusion matrices)
distinguishes it from other industry guidelines and makes it uniquely valuable as
a literacy-building tool. Practitioners found it stronger on "how to design" than
on "whether and how to scope" AI features.

**HCII 2021 (McAran) — Privacy, Ethics, and Trust Analysis:**

Five UX design components identified as novel to AI products (not in standard UX guidance):
1. Deciding whether AI adds unique value
2. Automation vs. augmentation assessment
3. Reward function design and evaluation
4. Precision/recall tradeoffs as design decisions
5. Monitoring negative downstream impacts

Confirmed gaps: privacy primarily addressed through consent and transparency, not
structural privacy-by-design. Trust addressed through calibration rather than
accountability or redress. Accountability and environmental/social well-being
absent from both PAIR and HAX.

---

## The Participatory Gap

PAIR's stated philosophy: ML "needs to be participatory and guided by diverse
citizens, policy-makers, and activists."

What the 2019 guidebook actually operationalises:
- Iterative usability testing with diverse user populations
- Including underrepresented groups in research participants
- Giving users notice and consent before data collection
- Sharing the reward function with users when possible

What is absent (confirmed by both academic analyses):
- No formal community governance or co-design processes with affected communities
- No structured mechanisms for ongoing community input post-launch
- No accountability framework for when community needs are not met

The gap between the participatory aspiration and the participatory practice is the
same gap we identified in the ethics-as-defanging analysis: the language of inclusion
without the structure of inclusion.

Post-2019: PAIR collaborated with the Equitable AI Research Roundtable and Google
for Startups to address unfair bias and sociotechnical harms — indicating the gap
is recognised internally, if not yet closed.

---

## Connections to Other Notes

- *Xu's HCAI framework* — PAIR and Xu arrive at similar conclusions from different
  directions; both treat the reward function as a design artifact
- *Microsoft 18 guidelines* — complementary frameworks; use both: HAX for UI
  evaluation, PAIR for cross-functional product design and ML literacy
- *Canca's PiE model* — PAIR's Chapter 1 question ("does this need AI?") maps to
  Canca's check for whether we face a core values problem or an instrumental one
- *Shneiderman two-dimensional framework* — PAIR's Chapter 4 (Feedback + Control)
  is the design implementation of the top-right quadrant
- *Honest build sequence* — PAIR's six-chapter structure is the content that fills
  each phase of Plan → Validate → Evaluate → Build
- *Excluded perspectives* — both academic analyses confirm PAIR's weakest coverage
  is accountability and structural fairness — the same gaps identified in the
  broader AI governance critique

---

## Key Insight

> The PAIR Guidebook is the most practically useful HCAI framework for product teams
> precisely because it speaks two languages simultaneously — UX and ML.
> Its strength is the bridge. Its gap is governance: it tells teams how to design
> responsibly but does not tell them how to be accountable when they do not.
>
> The participatory aspiration is genuine. The participatory mechanism is thin.
> Iterative user testing is not community governance.
> Diverse research participants are not structural representation.
> The gap between the two is where the most important work remains undone.
