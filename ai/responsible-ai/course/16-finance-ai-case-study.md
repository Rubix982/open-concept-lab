# Generative AI in Finance — Strategic Decision-Making Case Study

*Based on: "What's Possible? Generative AI and Finance" (industry briefing)*
*Personal study notes — analysis and synthesis.*

---

## The Opening Tension — and Why It Is Poorly Framed

The briefing states the problem cleanly: GenAI is a new paradigm, but banking
interactions "typically need 100 percent accuracy." This is the right tension to
name. But the framing is slightly off, and getting it wrong leads to the wrong
conclusions.

**The accurate framing:**
Banks do not need AI to be 100% accurate. Banks need their *decisions* to be
defensible, fair, and within regulatory tolerance. Those are different requirements.

A credit decision can incorporate an AI model that is 85% accurate if:
- A human relationship manager reviews the output before acting
- The reasoning is explainable and auditable
- The error rate is distributed fairly across demographic groups
- The decision can be appealed and corrected

The 100% accuracy standard is really a proxy for three separate requirements:
**auditability** (can you explain the decision?), **fairness** (does the error
rate fall equally?), and **accountability** (when it goes wrong, who is
responsible?). Naming these separately matters because they have different
solutions.

The text's conclusion — that the current GenAI opportunity is more internal
than consumer-facing — is correct. But the reasoning should be about
auditability and accountability, not accuracy.

---

## Prediction Machines — Applied to Finance

Finance is among the oldest and most mathematically sophisticated prediction
industries. Banks have been building prediction models for credit risk, fraud
detection, and market movement for decades. The Prediction Machines framework
(Agrawal, Gans, Goldfarb) asks: what does cheap prediction change?

In finance, the answer is more nuanced than in healthcare:

### Where cheap prediction creates genuine new value

**Credit decision synthesis:** The briefing mentions synthesizing "structured
and unstructured data from a range of sources" for loan decisions. Traditional
credit scoring is heavily structured (income, payment history, debt ratios).
GenAI can incorporate unstructured signals — call transcripts, customer service
notes, market context — that structured models cannot process. This is a real
expansion of the prediction frontier, not just making existing prediction cheaper.

**Personalized financial advice at scale:** Relationship managers at banks
serve wealthy clients partly because the economics of personalization don't
work for smaller accounts. Cheap prediction changes the economics — it becomes
possible to generate personalized content and advice for segments that previously
received only generic products.

**Fraud detection and anomaly flagging:** Pattern recognition in transaction
data is a prediction task that AI has done well for years. GenAI extends this
to more complex fraud patterns involving narrative reasoning (e.g., identifying
coordinated fraud networks from unstructured communication).

### Where cheap prediction changes incentives rather than capability

**Marketing content generation:** AI generating "personalized and targeted
content at scale to drive more efficient marketing campaigns" is not a prediction
problem in the meaningful sense — it is automation of content production. The
briefing frames this as a GenAI win; it is worth noting separately that it is
also an amplifier for persuasion at scale. Banks directing AI-generated
personalized marketing at financially vulnerable customers is a documented risk
that the briefing does not name.

---

## The Use Case Taxonomy — Reorganized by Stakes

The briefing lists use cases without distinguishing their risk profiles. A more
useful organizing principle is stakes: what goes wrong if the AI is wrong?

| Use Case | Stakes if AI Fails | Human Oversight Required |
|---|---|---|
| Call center agent assist | Low — agent can correct in real time | Minimal |
| Software co-pilot for coders | Low-medium — code review catches errors | Code review |
| Customer onboarding automation | Medium — compliance risk, customer friction | Compliance check |
| Personalized marketing | Medium-high — regulatory risk (targeting rules) | Legal/compliance review |
| Credit decisions | High — material harm to customers, regulatory exposure | Required, documented |
| Relationship manager insights | High — fiduciary duty, fraud risk | RM judgment |

The internal/back-office-first recommendation makes sense not because consumer-facing
AI is impossible, but because the low-stakes use cases (call center assist, software
co-pilot) have the most forgiving error tolerance. Starting there builds internal
competence and error-pattern understanding before moving into higher-stakes
applications.

This is the HCAI principle applied: automation should increase in proportion to
the demonstrated reliability of the system and the severity of consequence for
failure. Start where failure is cheap to correct.

---

## Credit Decisions — The Fairness Problem the Briefing Doesn't Name

The credit decision use case is the highest-stakes application described and
receives the least scrutiny.

"GenAI can synthesize all kinds of data — structured and unstructured — from a
range of sources, preparing loan decisions with greater accuracy."

This is technically possible. It is also where algorithmic harm has been most
thoroughly documented.

**Why unstructured data is not automatically better:**
Unstructured data includes things like neighborhood descriptions, writing style,
communication patterns, and social connections. These features correlate with
protected class membership. A model trained to maximize accuracy on historical
loan data will learn these correlations. Greater accuracy on historical data
does not mean greater fairness — it may mean more sophisticated encoding of
historical discrimination.

The briefing's claim that GenAI improves credit decision "accuracy" is accurate
only if accuracy is measured against a benchmark that is itself fair. If the
training data reflects decades of discriminatory lending, "more accurate
prediction of default" can mean "more accurate prediction of which historically
excluded groups will default on loans they were historically denied."

**What responsible credit AI actually requires:**
- Disparate impact testing across protected classes
- Adverse action explanations that satisfy regulatory requirements (Equal Credit
  Opportunity Act in the US; similar frameworks elsewhere)
- Regular audits that test for proxy discrimination (neighborhood as proxy for
  race, etc.)
- Clear human override mechanisms and appeal processes

None of these are technically hard. All of them require organizational commitment
that the briefing's framing — "greater accuracy" as the sole success criterion —
does not demand.

---

## Regulation as a Forcing Function

The briefing notes that finance is "subject to strict regulation and scrutiny for
standards of accuracy, security, and privacy." This is framed as a constraint.
It is also a forcing function for responsible deployment.

Banks cannot operate the way social media companies operated in their early years
— moving fast, breaking things, and treating regulatory response as a later
problem. The existing regulatory architecture (banking licenses, capital requirements,
consumer protection law, anti-discrimination enforcement) creates liability for
getting AI wrong. This is a structural incentive toward caution and oversight
that does not exist in less regulated sectors.

The implication for responsible AI: finance may be one of the sectors where the
market incentive and the responsible AI requirement are better aligned than
usual — not because banks are virtuous, but because the consequences of failure
are internally costly, not just externally borne by customers.

This is the same logic as fiduciary duty in medicine: physicians who harm patients
face professional and legal consequences. The accountability structure does not
eliminate harm, but it creates incentives that pure market competition does not.

---

## Privacy — The Gap in the Briefing

The briefing mentions privacy once: "especially in personal finance, where very
sensitive information is involved, banks will have to assess the quality of the
GenAI, the sources, and the reasons for its use."

This is the minimum necessary statement. It understates the privacy stakes
significantly.

Financial data is among the most sensitive categories of personal information.
It reveals health status (pharmacy transactions), political affiliation (donation
records), religious practice (tithing patterns), relationship structure (joint
accounts, beneficiaries), and behavioral patterns across every domain of life.
A comprehensive bank transaction record is, in practice, a behavioral biography.

GenAI models trained on or given access to this data face:
- **Training data leakage:** models that memorize specific customer transactions
  rather than learning general patterns
- **Inference attacks:** the ability to reconstruct sensitive information from
  model outputs even without direct access to training data
- **Third-party exposure:** GenAI providers who receive financial data for model
  improvement create data flows that existing privacy frameworks may not adequately
  govern

Nissenbaum's contextual integrity framework applies directly: financial information
flows appropriately between customer and bank for the purposes of the banking
relationship. It does not flow appropriately to GenAI training pipelines, model
providers, or marketing systems without explicit consent — even if the bank's
privacy policy technically permits it.

---

## What the Briefing Gets Right

The sequencing recommendation is correct: internal/back-office first, where
errors are cheaper and the feedback loop is faster. This is how organizational
AI competence should be built — not because consumer-facing AI is impossible,
but because the skills (evaluating model outputs, building oversight workflows,
understanding failure modes) are developed at lower stakes before being applied
at higher ones.

The framing of GenAI as a synthesis and augmentation layer — processing existing
information to support human decision-makers — is also correct. The relationship
manager still makes the call; the loan officer still reviews the recommendation.
AI is most valuable in finance when it reduces the cost of information preparation,
not when it removes the human from the decision.

---

## Key Takeaways

1. **"100% accuracy" is the wrong standard.** The real requirements are
   auditability, fairness, and accountability. Name them separately because
   they have different solutions.

2. **Use cases should be organized by stakes, not by capability.** Start where
   errors are cheap to correct. Build organizational competence before moving
   to high-stakes applications.

3. **Credit decisions are the highest-risk application described.** "Greater
   accuracy" on historically biased data is not the same as fairness. The
   briefing's framing omits the fairness requirement entirely.

4. **Finance regulation is a forcing function, not just a constraint.** The
   existing accountability structure creates internal incentives toward caution
   that do not exist in less regulated sectors. This is structurally better
   alignment between responsible AI and business interest than most sectors provide.

5. **Financial data privacy is undernamed.** Transaction records are behavioral
   biographies. GenAI access to this data creates training leakage, inference
   attack, and third-party exposure risks that deserve more than a single
   sentence of caution.

6. **The marketing use case deserves more scrutiny than it receives.** Personalized
   AI-generated persuasion at scale directed at financially vulnerable customers
   is a known harm pathway. Efficiency in marketing is not a neutral good when
   the product being marketed is financial risk.
