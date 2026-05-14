# Eight GDPR Questions When Adopting Generative AI

*Research notes on: Avi Gesser, Robert Maddox, Friedrich Popp, and Martha Hirst
(Debevoise & Plimpton LLP). NYU Compliance & Enforcement Blog, October 11, 2023.*
*Source: https://wp.nyu.edu/compliance_enforcement/2023/10/11/eight-gdpr-questions-when-adopting-generative-ai/*

---

## Overview

Written by privacy lawyers at a major international firm, this article provides
a compliance checklist for organisations adopting generative AI under GDPR.

The overarching conclusion:

> "If privacy is dealt with as an afterthought, it may be difficult to retrofit
> controls that are sufficient to mitigate privacy-related risk and ensure compliance."

This is the legal profession's version of the honest build sequence argument:
the privacy questions must be asked before deployment, not after. The difference
from the VSD and HCAI frameworks is that lawyers are saying it because of liability,
not just because it is right — which makes it a stronger practical incentive.

---

## The Eight Questions

### Q1 — Does GDPR Apply?

GDPR governs personal data processing by EEA/UK-established businesses, or by
foreign businesses offering goods or services to individuals in those regions,
or monitoring their behaviour. Foreign businesses operating under Standard
Contractual Clauses or the EU-US Data Protection Framework must also comply.

**Recommended action:** Assess whether personal data used for AI training or
testing is GDPR-covered. Consider anonymising data before use to avoid triggering
requirements.

**The extrapolated insight:**

"Does GDPR apply?" is the wrong first question. The right first question is:
"does this involve personal data?" — because if yes, some form of data protection
law likely applies somewhere. GDPR's extraterritorial reach is broad: if your
AI system is accessible in Europe, or if you train on data from European individuals,
you are likely within scope regardless of where your company is incorporated.

For the knowledge infrastructure: if the research papers being indexed include
work by European researchers, or if the system is accessible in Europe, GDPR
applies to how those researchers' data is processed.

---

### Q2 — Do You Have a Lawful Basis to Use Personal Data?

Organisations need a lawful basis for processing — consent, legitimate interest,
or contractual necessity. Critically:

> "If you have a lawful basis to process personal data for one purpose, it does
> not necessarily mean that you also have a lawful basis to use the same personal
> data for a different purpose."

**Recommended action:** Document the lawful basis before use. Update Records of
Processing Activities. Implement controls restricting special category data.

**The extrapolated insight:**

This is Nissenbaum's contextual integrity argument translated into GDPR compliance
language. The lawful basis is context-specific and purpose-specific. Data collected
under a legitimate interest for one purpose (publishing a research paper) does not
automatically carry a lawful basis for a different purpose (training an AI model).

This is the precise legal problem with scraping public web content for AI training.
The data was made public for one purpose. Training an AI model is a different purpose.
The lawful basis for the original publication does not extend to the training use.
This is why the NYT v. OpenAI litigation is legally meaningful — it is not just
about copyright, it is about whether the training use falls within any lawful basis.

For the knowledge infrastructure: the consent mechanism designed for the project —
contacting researchers, explaining the purpose, getting explicit agreement — is
exactly the lawful basis documentation this question requires. The consent is the
lawful basis. The purpose specificity is built in.

---

### Q3 — How Will You Ensure Transparent Data Handling?

Transparency is described as:

> "A core principle of GDPR, and has been a primary regulatory concern in the
> context of Generative AI."

Privacy notices must disclose purposes and lawful bases for processing.

**Recommended action:** Review and update privacy notices for AI tool usage.
Flag employee monitoring applications prominently.

**The extrapolated insight:**

Transparency in the GDPR sense is not "we disclosed it in the terms." It is
disclosure in a form that the data subject can actually understand and act on.
This is Xu's comprehensible AI distinction translated into compliance language:
the disclosure must be comprehensible to the target audience, not just technically
present in a document.

Generative AI creates a specific transparency problem: the model's outputs are
generated from patterns learned across millions of training examples, and the
model itself cannot explain precisely which training data contributed to a specific
output. You cannot be fully transparent about a process you do not fully understand.
This is the explainability gap problem (from the Bau Lab note) surfacing as a
GDPR compliance issue.

---

### Q4 — How Will You Handle Individual Rights Requests?

Once trained, models may struggle to "unlearn" information, limiting the ability
to satisfy deletion and correction requests. Organisations should:

> "Consider risks associated with individuals exercising data subject rights at
> an early stage of Generative AI development."

**Recommended action:** Develop response strategies early. Maintain detailed
training and operating data inventories.

**The extrapolated insight:**

This is the machine unlearning problem from the explainability gap note — stated
as a GDPR compliance obligation. GDPR gives individuals the right to erasure
(Article 17) and the right to rectification (Article 16). If a person's data was
used to train a model and they request deletion, what does "deletion" mean for a
model whose weights were shaped by that data?

Current technical answer: we do not have a reliable way to selectively remove the
influence of specific training examples from a trained model. Machine unlearning
is an active research area but is not solved. This means every AI system trained
on personal data has a latent GDPR compliance problem that the legal profession
is noting but that the technical infrastructure cannot yet resolve.

This is one of the strongest arguments for the knowledge infrastructure's consent
mechanism: if researchers can request removal of their work at any time, the
system must be designed from the start to accommodate this — which means the
knowledge graph, not the model weights, must be the primary store, and the graph
must support genuine deletion.

---

### Q5 — Will the Tool Make Automated Decisions?

GDPR Article 22 protects individuals from:

> "A decision based solely on automated processing producing legal or significant
> effects."

**Recommended action:** Identify automated decision-making risks, including
discrimination risks. Determine mitigation measures. Document human involvement
requirements.

**The extrapolated insight:**

This is the Shneiderman two-dimensional framework stated as a legal obligation.
The law requires human involvement in decisions with significant effects — not as
a nice-to-have, but as a right. The person subject to an automated decision has
the right to human review, to contest the decision, and to explanation.

Most current AI deployment violates Article 22 in spirit, if not always in letter,
because the "human involvement" is often nominal — a rubber-stamping of algorithmic
outputs at volumes that make genuine review impossible. The Microsoft G11 guideline
(make clear why the system did what it did) is the design-level implementation
of the Article 22 obligation.

Hiring algorithms, credit scoring, content moderation decisions — all of these
involve significant effects. All of them require either genuine human oversight
or an explicit exemption under Article 22. Most current implementations provide
neither.

---

### Q6 — Will the Tool Create New Personal Data?

Generative AI may produce inferred data — summarising CVs, inferring race from
other attributes, generating personal profiles — creating new personal data:

> "Personal data may give rise to privacy concerns if this generated data is not
> dealt with in accordance with GDPR, even if the created personal data is not accurate."

**Recommended action:** Assess circumstances under which personal data may be
generated. Document lawful bases for newly created data. Account for generated
data in rights requests.

**The extrapolated insight:**

This is the inference problem — the gap between data collected and data derived.
When a model summarises your CV, it has created a new document containing personal
information about you. When it infers your political views from your browsing
patterns, it has created a new data point about you. These derived data points are
personal data under GDPR even if they are inferences, even if they are wrong.

The specific note that inaccurate generated data still constitutes personal data
is important: if an AI generates false information about you, you still have rights
over that false information as personal data. The wrongness of the data does not
make it not personal data.

This applies directly to AI-generated content: if a model hallucinates that you
said something you did not say, you have GDPR rights over that hallucination as
personal data about you. The legal framework is starting to close around AI
hallucinations as a privacy violation, not just a factual error.

---

### Q7 — Does This Constitute Employee Monitoring?

Tools integrating with email, conferencing, or other workplace software may trigger
employee monitoring obligations:

> "Employee monitoring is a key focus for European privacy and labour regulators."

German Works Council (Betriebsrat) approval requirements are specifically noted.

**Recommended action:** Evaluate tools for employee monitoring implications.
Consider employment law requirements. Implement collection and use controls.

**The extrapolated insight:**

This question connects to the employer monitoring note directly. What the GDPR
and European employment law framework recognises is that AI tools integrated
into workplace software — Copilot in Microsoft 365, AI features in Slack, AI
meeting transcription — are employee monitoring tools. They observe, record,
and analyse employee behaviour. That is monitoring. It requires legal basis,
transparency, and in some jurisdictions employee representative approval.

The German Works Council requirement is the most concrete: in Germany, an
employer cannot deploy monitoring technology in the workplace without agreement
from the works council representing employees. This is exactly the structural
accountability mechanism we identified as missing in the US context — mandatory
employee representation in decisions about AI monitoring tools.

---

### Q8 — Do You Need a Data Protection Impact Assessment?

GDPR Article 35 requires DPIAs for high-risk processing. The ICO states directly:

> "In the vast majority of cases, the use of AI will involve a type of processing
> likely to result in a high risk to individuals' rights and freedoms, and will
> therefore trigger the legal requirement for you to undertake a DPIA."

**Recommended action:** Conduct DPIAs before using personal data in AI systems.
Reference CNIL and ICO guidance on AI-specific considerations. Integrate DPIA
processes into governance frameworks.

**The extrapolated insight:**

The ICO's position — that the vast majority of AI uses require a DPIA — is
essentially saying: AI is presumptively high-risk until you can demonstrate
otherwise. This reverses the burden of proof from "prove it caused harm" to
"demonstrate it is safe before deploying."

A DPIA is not a box-ticking exercise. Done properly, it is exactly the VSD
conceptual and technical investigation: identify who is affected, what values
are at stake, what the technical architecture encodes, what the failure modes
are, and what mitigations are in place. The GDPR formalised VSD's methodology
as a legal requirement for high-risk processing.

For the knowledge infrastructure: a DPIA should be conducted before the system
goes live. Given that the system processes researchers' personal data (their work,
their affiliations, their intellectual contributions) and makes inferences about
that data (connections, claims, relationships), it almost certainly qualifies
as high-risk processing. The DPIA is not optional.

---

## What the Eight Questions Actually Map To

Reframed through everything else in this repository:

| GDPR Question | What it is really asking |
|---|---|
| Q1: Does GDPR apply? | Have you identified who is affected and by what law? |
| Q2: Lawful basis? | Did you get genuine consent for the actual use, not a bundled click? |
| Q3: Transparency? | Is your disclosure comprehensible to the people it affects? |
| Q4: Rights requests? | Can you actually delete data or is it baked into model weights? |
| Q5: Automated decisions? | Is the human oversight genuine or nominal? |
| Q6: New personal data? | Do you know what you are generating, not just what you collected? |
| Q7: Employee monitoring? | Did employees have any say in being surveilled by this tool? |
| Q8: DPIA? | Did you assess the risks before deploying, not after harm occurred? |

Every question is the honest build sequence from a legal obligation angle.
Every question the answer to which is "we didn't think about that yet" is a
violation waiting to materialise.

---

## The Practical Implication for AI Development

The article's core message for practitioners: privacy cannot be retrofitted.

This is the GDPR equivalent of the Woebot lesson — the company that built the
most safety-conscious mental health AI failed partly because it could not retrofit
safety into an LLM architecture that had not been designed for it from the start.

The same dynamic applies to GDPR compliance. An AI system trained on personal
data without a documented lawful basis, without transparency to the data subjects,
without DPIA, and without a mechanism for rights requests cannot be made compliant
after the fact by adding a privacy policy page. The violations are architectural.
The remedies are architectural. And the architects are needed before the first
line of code.

---

## Connections

- *Honest build sequence* — Q8 DPIA maps to Phase 3 evaluate; Q2 lawful basis
  maps to Phase 1 consent mechanism; Q3 transparency maps to Phase 2 WOZ testing
- *VSD tripartite methodology* — a DPIA is a legal formalisation of the conceptual
  and technical investigations VSD requires
- *Data permission and litigation* — Q2 lawful basis is the legal version of the
  MIT standing permission argument
- *Explainability gap and mechanistic interpretability* — Q4 rights requests and
  the machine unlearning problem; Q3 transparency and the model opacity problem
- *Platform surveillance and consent fiction* — Q2 is the legal version of why
  bundled consent is not genuine consent
- *Employer monitoring note* — Q7 is the legal requirement for what the employer
  monitoring note argues ethically

---

## Key Insight

> The eight GDPR questions are not bureaucratic checkboxes.
> They are the legal formalisation of the ethical questions that should
> have been asked before any AI system touching personal data was designed.
>
> Q2 (lawful basis) is the consent question.
> Q3 (transparency) is the comprehensibility question.
> Q4 (rights requests) is the machine unlearning question.
> Q5 (automated decisions) is the human oversight question.
> Q8 (DPIA) is the honest risk assessment question.
>
> Every one of them is answered badly or not at all by most current AI deployments.
> Every one of them was answerable before deployment — but only if privacy
> was treated as a design constraint, not a compliance afterthought.
