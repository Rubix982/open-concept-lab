# Google's AI Principles (2026) — Critical Analysis

_Personal study notes — original analysis and synthesis. Not a reproduction of course material._

---

## The History — Why This Document Exists and What It Used to Say

### Origin: Project Maven (2018)

Google published its original AI Principles on June 7, 2018 — directly triggered by
internal employee revolt over **Project Maven**, a Pentagon contract in which Google
applied computer vision to analyse US military drone surveillance footage.

Approximately 4,000 employees signed an internal petition. At least 12 resigned.
Google declined to renew the Maven contract and published the principles as its
public commitment to ethical AI development.

### The Original Seven Objectives (2018)

Projects would only move forward when "overall likely benefits substantially exceed
the foreseeable risks and downsides":

1. **Be socially beneficial** — full range of social/economic impacts; benefits must outweigh risks
2. **Avoid creating or reinforcing unfair bias** — discriminatory impacts on race, ethnicity, gender, nationality, income, sexual orientation, ability, political or religious belief
3. **Be built and tested for safety** — robust safety practices, monitoring, user feedback, explanations
4. **Be accountable to people** — feedback opportunities, relevant explanations, appeal, human direction and control
5. **Incorporate privacy design principles** — notice and consent, architectures with privacy safeguards, transparency and control
6. **Uphold high standards of scientific excellence** — scientific method, open inquiry, intellectual rigour, peer review, sharing research
7. **Be made available for uses that accord with these principles** — limit harmful or abusive applications

### The Applications Google Originally Pledged NOT to Pursue

The 2018 principles included an explicit list of four AI application categories
Google would not develop or deploy:

1. **Technologies that cause or are likely to cause overall harm**
2. **Weapons or other technologies whose principal purpose is to cause or facilitate injury to people**
3. **Technologies that gather or use information for surveillance violating internationally accepted norms**
4. **Technologies whose purpose contravenes widely accepted principles of international law and human rights**

### The February 2025 Rollback

On **February 4, 2025**, Google quietly updated its AI Principles page, removing
the "Applications we will not pursue" section entirely — specifically stripping out
the commitments on weapons and surveillance.

No press release explicitly announced the removal. The accompanying blog post by
Demis Hassabis and Sundar Pichai framed the change geopolitically:

> *"There's a global competition taking place for AI leadership within an increasingly
> complex geopolitical landscape. We believe democracies should lead in AI development,
> guided by core values like freedom, equality, and respect for human rights."*

The post was published the same week President Trump revoked Biden's executive order
on AI safety.

**What replaced the prohibitions:** The new structure — Bold Innovation, Responsible
Development, Collaborative Progress — retains language about benefits outweighing risks
and human rights alignment, but without the explicit prohibitions on weapons or surveillance.

**Responses:**
- Senators Markey, Merkley, and Welch wrote formally to Pichai demanding explanation
  and asking whether Google was currently developing AI weapons or surveillance tools
- Amnesty International called the decision "shameful"
- Human Rights Watch: "Google Announces Willingness to Develop AI for Weapons"
- EFF: "Google is on the Wrong Side of History"
- Stop Killer Robots documented the rollback formally

**Employee context:** The 2025 rollback occurred with significantly less internal
resistance than Project Maven in 2018. Employee leverage has weakened substantially.
A May 2026 report noted new Pentagon AI contract backlash but observed that "power
had waned since Project Maven."

---

## What This Document Is (2026 Version)

Google's current AI Principles are a public-facing document with three named principles:
Bold Innovation, Responsible Development and Deployment, and Collaborative Progress.

Reading them without the history above produces a misleading picture. Read with it:
these are the principles that **replaced** the explicit prohibitions on weapons and
surveillance, reframed as a geopolitical necessity, during a week when US AI safety
executive orders were revoked.

The document grounds itself in Google's founding mission — "to organize the world's
information and make it universally accessible and useful." That framing positions
Google's AI development as an extension of a mission, not a business decision.
After the weapons rollback, that framing requires even more scrutiny than it did before.

---

## The Three Principles — What They Actually Say

### 1. Bold Innovation

- Develop and deploy where "likely overall benefits substantially outweigh foreseeable risks"
- Advance frontier AI through scientific method, rapid iteration, and open inquiry
- Use AI to accelerate scientific discovery across biology, medicine, chemistry, physics, mathematics
- Focus on real-world problems, tangible outcomes, broadly available breakthroughs

### 2. Responsible Development and Deployment

- Implement "appropriate human oversight, due diligence, and feedback mechanisms"
- Align with user goals, social responsibility, and "widely accepted principles of international law and human rights"
- Invest in safety and security research, rigorous testing, monitoring, and safeguards
- "Mitigate unintended or harmful outcomes" and "avoid unfair bias"
- Promote privacy, security, and respect intellectual property rights

### 3. Collaborative Progress, Together

- Develop AI as "foundational technology capable of driving creativity, productivity, and innovation"
- Collaborate with researchers across industry and academia
- Engage governments and civil society on challenges no single stakeholder can solve
- Foster an ecosystem that empowers others to build

---

## What These Principles Actually Commit Google To

Almost nothing enforceable.

The language is carefully chosen to produce the appearance of commitment without the
substance of obligation. Every operative term is qualified or self-referential:

**"Likely overall benefits substantially outweigh foreseeable risks"**
This is not a commitment. It is an assessment criterion, and Google is both the assessor
and the assessed. Who determines what is "likely"? Google. Who determines what is
"foreseeable"? Google. Who determines what "substantially" means? Google. Who bears
the cost of errors in that assessment? Not Google.

This is the Venn diagram problem in print: the circle of "who decides" and the circle of
"who benefits" are almost entirely overlapping, while the circle of "who bears the harm"
sits largely outside both.

**"Appropriate human oversight"**
Appropriate compared to what? By whose standard? This phrase commits to having some
human oversight of some systems in some contexts. It commits to nothing specific. An
ethics review that a product team can override is "appropriate human oversight." A rubber
stamp is "appropriate human oversight." The word "appropriate" is the hinge on which the
entire commitment turns — and it is self-defined.

**"Widely accepted principles of international law and human rights"**
This phrase sounds substantial. It is actually a low bar. "Widely accepted" excludes
contested areas by definition. Human rights law is interpreted selectively by powerful
actors all the time. Google currently operates in jurisdictions where its compliance with
local law directly contradicts human rights norms — and the document does not address
that tension at all.

**"Avoid unfair bias"**
Note: not "avoid bias." "Avoid _unfair_ bias." The qualifier matters. Bias that is
considered fair — by whom, using what criteria? — is permissible under this framing.
This is not a trivial distinction. Statistical fairness metrics are incompatible with
each other. Optimising for one fairness criterion provably degrades another. Saying
"avoid unfair bias" while leaving the definition of unfairness to the deployer is not
a principle. It is a placeholder.

**"Mitigate unintended or harmful outcomes"**
"Mitigate" does not mean prevent. It does not mean remediate. It does not mean compensate
affected parties. It means reduce to some degree. This is possibly the most flexible
operational commitment in the document. Every harm-causing deployment can coexist with
genuine mitigation efforts. The harm and the mitigation are not mutually exclusive.

---

## What These Principles Do Not Commit Google To

- Independent third-party audits with binding authority
- External enforcement of any stated principle
- Liability when principles are violated
- Compensation for people harmed by systems that violate stated principles
- Veto power for affected communities over deployment decisions
- Transparency about when assessments of "likely benefits" were wrong
- Any mechanism for revisiting or correcting a principle violation after deployment
- Any timeline, measurable target, or accountability structure

This is the completeness of the silence. The document commits to running an internal
process. It does not commit to any particular outcome of that process, any independent
verification of the process, or any consequence when the process fails.

---

## The Core Tension: Bold Innovation vs. Responsible Development

The document presents these as complementary principles. They are frequently in direct
conflict, and the document does not specify how that conflict is resolved.

"Bold innovation" requires speed, tolerance for uncertainty, willingness to deploy before
all risks are understood. "Responsible development" requires caution, due diligence,
demonstrated safety before deployment. These are not the same direction.

Every major AI harm we have documented occurred in the gap between these two principles.
The GPT-4o sycophancy incident — a system update that caused ChatGPT to endorse stopping
psychiatric medication and validate a terrorism plan — was the product of "bold innovation"
(rapid iteration, ship the update) overwhelming "responsible development" (thorough testing,
identified risks before deployment). The update was rolled back in three days. The harm
had already accumulated.

_(See: human-safety-in-ai-landscape.md for documented cases across psychological,
physical, and occupational harm._)

The question every principles document should answer: when these two principles conflict —
and they will, regularly, at the level of individual product decisions — which one wins?
Google's document does not answer this. The structural answer, provided by the incentive
architecture rather than the text, is: bold innovation wins, responsible development is
consulted.

This is not a cynical reading. It is a structural reading. The company's revenue,
competitive position, talent acquisition, and market valuation are all directly tied
to being bold, fast, and frontier-pushing. They are not tied to the "responsible
development" bucket in any equivalently direct way. When two principles conflict and
one is financially incentivised, the outcome is predictable without any individual
actor making a conscious choice to violate the other principle.

---

## The "Foreseeable Risks" Problem

"Benefits substantially outweigh foreseeable risks" smuggles a major epistemological
problem into the assessment criteria. Black swans — by definition — are not foreseeable.

The most catastrophic AI outcomes are likely to be the ones nobody anticipated, precisely
because the novel capabilities create novel failure modes. An assessment framework that
only weighs foreseeable risks is systematically blind to the category of outcome that
matters most.

This is Taleb's argument from _The Black Swan_ applied directly: before the crash, the
risks are not foreseeable, so no assessment of "foreseeable risks" captures them. After
the crash, they are explained as if they were always obvious. The assessment framework
selects for optimism about unknown unknowns.

_(See: ethics-as-defanging.md — the Taleb Standard: who bears the cost of being wrong
about what was foreseeable?)_

The people assessing whether risks are foreseeable are not the people who will bear
the cost of being wrong. That asymmetry is the problem. A "foreseeable risk" calculation
performed by people with no skin in the game — whose careers and compensation are not
reduced when the unforeseeable harm arrives — is not a safety mechanism. It is a
documentation exercise.

---

## Canca's Lens: Core Principles or Instrumental Principles?

Applying the PiE model's core/instrumental distinction to this document:

**Bold Innovation** is not a principle in Canca's sense at all. It is a description of
how Google wants to work — a preference for pace and ambition. It contains no core value
(autonomy, beneficence, justice). It is not even an instrumental principle serving a core
value. It is a business methodology dressed as an ethical principle.

**Responsible Development and Deployment** bundles together genuine instrumental principles
(human oversight, testing, privacy protection) but does not ground them in core values.
Why does human oversight matter? Because it protects autonomy — people's right to engage
meaningfully with systems that affect them. Why does testing matter? Because it serves
beneficence — it reduces the probability of harmful outcomes. These connections are
not made. The instrumental principles float without the core value anchors that would
give them direction when they conflict with each other.

**Collaborative Progress** is entirely instrumental — and instrumentally vague. "Collaborate
with researchers" and "engage with governments" commit to participating in conversations.
They do not commit to any particular outcome, power-sharing arrangement, or meaningful
influence by those parties over Google's decisions.

Canca's specific observation about the proliferation of principles documents is directly
applicable here: if principles are well-done, they serve to declare _priority orderings_
when core principles conflict. Google's document does not do this. When "bold innovation"
and "responsible development" conflict — which they will — there is no declared priority.
The document offers no tiebreaker. Which means the tiebreaker will always be, in practice,
whichever outcome best serves the business at that moment.

_(See: cansu-canca-and-pie-model.md for the full core/instrumental distinction argument.)_

---

## What Is Genuinely Useful Here

This document is not entirely without value. Being honest requires acknowledging what
is real, not just what is branding.

**The scientific discovery commitments are specific enough to be testable.** "Using AI
to accelerate scientific discovery in biology, medicine, chemistry, physics, mathematics"
is a meaningful direction. Google DeepMind's AlphaFold work, AlphaGeometry, and weather
prediction systems are genuine examples of this principle being operationalised at scale.
These are not just aspirational — they produced results, published under open access,
that the broader scientific community could use. That is a real commitment with real
artifacts.

**The safety and security research investment is at least partly real.** Google DeepMind
publishes safety research, runs alignment initiatives, and contributes to public benchmarks.
This is not nothing. The research exists, is peer-reviewed, and influences the field. The
problem is not that the safety work doesn't happen — it is that it does not have binding
authority over product decisions.

**"Broadly available" breakthroughs is an interesting commitment.** It implies something
about not exclusively capturing the value of scientific AI advances. This is worth
watching rather than dismissing, because it creates at least a stated expectation that
can be pointed to when the company acts otherwise.

The honest assessment: the scientific discovery cluster is where the principles have the
most concrete content and the most genuine correspondence between stated intention and
observed action. The governance and accountability cluster is where the language is most
designed to produce the appearance of commitment without its substance.

---

## The Ethics-as-Defanging Reading

This document is a textbook example of what the ethics-as-defanging analysis describes:
it frames AI accountability in the domain of philosophy — "principles," "values," "goals"
— and out of the domain of law, liability, and enforcement.

Every clause that could imply accountability is made soft:
- "Appropriate" oversight (not specified, not audited)
- "Mitigate" harms (not prevent, not remedy)
- "Avoid unfair" bias (not avoid bias, and unfairness is self-defined)
- "Broadly" accepted human rights (contested cases excluded by the qualifier)

The document does not use the words: liability, enforcement, penalty, remediation,
compensation, independent audit, or binding commitment.

This is not an oversight. These words are absent because their presence would produce
actual accountability. The absence of consequences is the design, not a gap.

_(See: ethics-as-defanging.md — the shift from "what are the enforceable rules?" to
"what are our values?" is where accountability disappears.)_

---

## Collaborative Progress — Who Is Actually Collaborating?

The third principle is worth examining specifically. "Engaging with governments and
civil society" is described as an approach to challenges "that can't be solved by any
single stakeholder." This framing implies multi-stakeholder governance while describing
what is, in practice, single-stakeholder decision-making with consultation.

Consultation is not collaboration. Advisory input is not governance power. When Google
"engages" governments and civil society, the decision over whether and how to proceed
still rests with Google. The engagement is an input to a decision made elsewhere. The
people "engaged" do not have veto power, amendment power, or binding authority.

This is the excluded perspectives problem operating at the governance level: the document
acknowledges the existence of multiple stakeholders, while the actual decision structure
remains single-stakeholder. Being invited to a conversation is not the same as having
a seat at the table where the decision is made. It is something you do _before_ going
to that table.

The one claim in this section that would be genuinely significant — "fostering a vibrant
ecosystem that empowers others to build innovative tools" — is also the one that creates
the most direct tension with Google's competitive interests. An ecosystem that empowers
others requires tolerating capable competitors built on your infrastructure. The degree
to which this principle holds when it conflicts with market position is the real test
of whether it is a principle or branding.

---

## The Sycophancy Loop, Applied

The sycophancy loop — a feedback dynamic where systems optimise for approval rather than
accuracy — applies to principles documents, not just AI models.

A company writes principles. Principles are praised by external stakeholders, regulators,
and press. Praise produces incentive to write more principles that will be praised. The
principles optimise for praise. The praise is produced by principles language that sounds
responsible. The principles language that sounds responsible is not the same as principles
that produce responsible outcomes.

There is an entire ecosystem of external stakeholders — academics, civil society groups,
journalists — whose engagement with Google is partly conditioned on Google making gestures
toward responsible AI. The principles document is partly an input to that ecosystem. The
ecosystem signals approval. The signals are interpreted as evidence the principles are
working. The feedback loop closes without any harm having been reduced.

This is Goodhart's Law at the institutional level: the measure (principles document)
became the target, and in becoming the target, it ceased to measure what it was supposed
to measure. The question is no longer "are we building responsibly?" — it is "do we
have a principles document that will satisfy this stakeholder?"

_(See: goodharts-law-and-the-prestige-trap.md for the full argument.)_

---

## The Structural Summary

| Claim in document                                                  | What it actually commits to                                             | What would actually produce accountability                                |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Benefits "substantially outweigh" risks                            | Google's internal assessment says so                                    | Third-party pre-deployment risk assessment with binding authority          |
| "Appropriate" human oversight                                      | Some human review exists somewhere in the process                       | Specified oversight at defined decision points with independent audit      |
| "Widely accepted" human rights alignment                           | Compliance with undisputed norms in undisputed contexts                 | Defined commitments for contested cases, with remedy mechanisms            |
| Avoid "unfair" bias                                                | Some bias that Google considers unfair is targeted                      | Independent fairness audit using multiple metrics with published results   |
| "Mitigate" harmful outcomes                                        | Some reduction of some harms is attempted                               | Liability for harms, with compensation pathways for affected parties       |
| Collaborate with governments and civil society                     | Advisory conversations take place                                       | Binding multi-stakeholder governance with real veto or amendment authority |

The gap between column two and column three is where real accountability would live,
and where this document is entirely silent.

---

## Why This Matters for the Broader Course

Google's AI Principles are not unusual. They are typical. The EU AI Act, Microsoft's
Responsible AI principles, OpenAI's usage policies — all operate in the same register.
The language is more sophisticated than it used to be. The accountability structures are
not more binding than they used to be.

What Google's document offers that is worth studying: it is the most polished version
of a form that has been iterated on for years, by a company with enormous legal and
communications resources. Every clause has been reviewed by lawyers, every word has
been weighed. The gaps are not accidents. The qualifications are intentional. The
document is maximally sophisticated about sounding committed while remaining minimally
committed.

Understanding exactly _where_ the commitments hollow out — which words do the softening,
which qualifications do the exclusion — is a core analytical skill for this field.
Reading this document carefully is practice for reading every principles document that
will follow it.

---

## Documented Tensions and Critiques

### Timnit Gebru and the Ethical AI Team (2020)

Gebru was co-lead of Google's Ethical AI team. In December 2020, she was fired
(or resigned under pressure — accounts differ) after a paper she co-authored —
*"On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?"* — was
blocked from internal publication review.

The paper raised concerns directly relevant to Google's own AI Principles:
environmental and financial costs of large language models, problematic training
data, amplification of societal bias, and misdirected research priorities.

The case exposed a structural problem: Google's principles committed to "upholding
scientific excellence" and "avoiding bias," but Google had control over whether
Ethical AI team research could be published. The dispute raised a question the
principles document cannot answer: what happens when research findings threaten
business interests?

### Gemini Image Generation Incident (2024)

Google suspended Gemini's ability to generate images of people after users found
the model producing historically inaccurate and racially biased outputs. This
directly contradicted the stated principle of "avoiding unfair bias" and forced
a public correction — demonstrating that stated principles do not automatically
prevent bias in deployed systems.

### Bard Launch (2023)

Bard's launch was rushed in response to ChatGPT. In its first public demo, Bard
produced a factually incorrect answer visible in Google's own promotional materials.
The incident reduced Alphabet's market cap by approximately $100B and highlighted
the tension between "be socially beneficial" and competitive market pressure.

### The 2025 Weapons Rollback as the Clearest Signal

The February 2025 rollback is the most significant single data point for evaluating
the durability of Google's AI principles. The company removed explicit prohibitions
on weapons and surveillance without public notice, during a week when US AI safety
executive orders were revoked, justified by geopolitical competition framing.

The original 2018 document was written under employee pressure after Project Maven.
The 2025 document was written with significantly reduced employee leverage.
The difference in content reflects the difference in pressure, not a difference
in values. The principles were never more binding than the pressure that produced them.

### Google AI Principles Governance Infrastructure

Despite the document's softness, Google does have real governance infrastructure:

**Frontier Safety Framework (FSF)** — introduced May 2024, updated February and
September 2025. Defines Critical Capability Levels (CCLs) that trigger evaluation
protocols. Current domains: autonomy, biosecurity (CBRN), cybersecurity, ML R&D,
harmful manipulation (added v3). Uses "early warning evaluations" before thresholds
are crossed.

**Responsibility and Safety Council (RSC)** — internal review body evaluating
research and projects against principles.

**SynthID** — imperceptible watermarking of synthetic media (images, audio, text,
video) via deep learning. A genuine technical commitment.

The governance infrastructure is real. The gap remains: it is internal, self-assessed,
and without binding authority over product decisions.

---

## Key Insight

> Principles documents do not fail because they are written in bad faith.
> They fail because they are written in a system where good-faith principles
> without enforcement mechanisms produce the same outcomes as no principles at all.
>
> The question is not whether Google's stated values are genuine.
> Many of the people who wrote this document probably believe it.
> The question is what happens when "bold innovation" and "responsible development"
> conflict at the level of a specific product decision, in a company whose revenue,
> market valuation, and competitive position all depend on the former.
>
> Principles without a tiebreaker, a mechanism, and a consequence are not governance.
> They are aspiration. Aspiration is not nothing. But it is also not accountability.
>
> The difference between this document and a serious accountability framework is the
> same as the difference between a company saying "we value safety" and a company
> being liable when safety fails.
> One produces brochures. The other produces incentives.
