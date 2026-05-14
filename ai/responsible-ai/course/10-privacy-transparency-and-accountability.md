# Privacy, Transparency, and the Accountability Asymmetry

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Basic Distinction

**Privacy** is the claim that certain information about you belongs to you — that you
have the right to control who knows it, when, and in what context.

**Transparency** is the claim that certain information should be accessible to others
— that hiding it causes harm, enables abuse, or undermines accountability.

These are not simple opposites. They are both claims about who has the right to
information. Which claim wins depends on who is asking, about whom, in what context,
and why.

---

## The Accountability Asymmetry

Your intuition — the higher people go, the more transparency is required — has a
precise name in political philosophy: the **accountability asymmetry**.

> The more power you hold over others, the less privacy you are entitled to
> in the exercise of that power.

A private citizen's medical records are private. A politician's financial
relationships with pharmaceutical companies are not — because those relationships
affect public decisions that affect everyone.

The politician does not lose all privacy. They lose privacy specifically in the domain
where they exercise power over others. The shrinking of the privacy interest tracks
exactly the growing of the power interest.

**Why this asymmetry exists:**

Unchecked power exercised in secret is the structural condition for corruption, abuse,
and the accumulation of advantage at everyone else's expense. Democratic accountability
requires that the exercise of power be visible to those over whom it is exercised.
Without that visibility, the governed cannot evaluate whether power is being used for
their benefit or against them.

**Where this accountability asymmetry appears in law and practice:**

- Politicians must disclose financial interests
- Judges must recuse themselves from cases involving their own interests
- Executives of public companies must disclose material information to shareholders
- Police officers' use-of-force records are subject to public disclosure
- Lobbyists must register and disclose who they represent
- Corporations must publish environmental impact data in some jurisdictions

In each case: the privacy interest shrinks where the power interest grows. Not because
powerful people are less human. Because the people affected by that power have a right
to evaluate whether it is being used honestly.

---

## Contextual Integrity — The More Precise Framework

Helen Nissenbaum's framework, developed in *Privacy in Context* (2010), makes the
privacy/transparency distinction more precise than a simple binary.

**The core argument:** Privacy is not about secrecy vs. disclosure. It is about
whether information flows appropriately within its context.

> Information flows appropriately when they match the norms of the context
> in which the information was originally shared.

**Examples:**

Medical information shared with your doctor flows appropriately to other treating
physicians — that is within the context of healthcare. It does not flow appropriately
to your employer — that violates the contextual norms under which you shared it.

A politician's voting record flows appropriately to constituents — that is within
the context of democratic accountability. It does not flow appropriately to foreign
intelligence services mapping influence networks — different context, different norms.

Your location data shared with a navigation app to get directions flows appropriately
to the navigation function. It does not flow appropriately to advertisers, data brokers,
or law enforcement without warrant — different context, different norms.

**Why contextual integrity is more useful than privacy/transparency binary:**

It captures why some disclosures feel right and others feel like violations — even
when the same information is involved. The question is not "is this private?" but
"does this information flow match the norms of the context in which it was originally
shared?"

This matters for AI systems because they routinely violate contextual integrity:
- Data shared for one purpose (navigation) is used for another (targeted advertising)
- Information disclosed in one relationship (doctor-patient) flows to another (employer)
- Behaviour observed in one context (browsing) is used to make decisions in another (credit)

The violation is not that the data was collected. It is that the flow broke the
contextual norms under which collection was agreed to.

---

## The Surveillance Inversion

The accountability asymmetry says: powerful actors → more transparency required.
This is the direction democratic accountability runs.

What surveillance technology has produced is the precise inversion:

**Maximum transparency about ordinary citizens. Maximum opacity about the institutions
surveilling them.**

The person walking down the street:
- Captured by facial recognition cameras
- Matched against a database they cannot access
- Assessed by an algorithm whose error rate they cannot know
- Stored in a record they cannot see or contest

The institution doing this:
- The algorithm is a trade secret
- The training data is proprietary
- The error rate is not disclosed
- The database is not subject to public records requests in most jurisdictions
- The decision to deploy is not democratically accountable

The person has minimum power. Maximum transparency is imposed on them.
The institution has maximum power. Maximum opacity protects it.

This is the exact inversion of what the accountability asymmetry requires.

**How it happened:**

The technology to surveil at scale became available before the accountability frameworks
caught up. Companies deployed it. Governments used it. The legal frameworks designed
for an era of expensive, targeted surveillance did not scale to mass, cheap, automated
surveillance. The result: the structural condition for accountability — that the exercise
of power is visible to those over whom it is exercised — has been undermined precisely
as the power to surveil has grown.

---

## The AI-Specific Version

When an AI system makes a decision about you:

**What the system knows about you:** Your history, patterns, associations, behaviour
across contexts, proxies for protected characteristics you did not disclose.

**What you know about the system:** Usually nothing. Possibly: that a decision was
made. Rarely: why.

| | You | The AI System |
|---|---|---|
| Access to your data | Limited | Extensive |
| Access to decision reasoning | None | Not disclosed |
| Error rate for people like you | Unknown | Not published |
| Ability to contest | Unclear | Procedurally difficult |
| Who bears the cost of errors | You | The deploying institution, indirectly if at all |

This is a power asymmetry. The system has power over you. By the accountability
asymmetry, it should be more transparent, not less. Current practice is the reverse.

**Why this matters for governance:**

The Microsoft G11 guideline — make clear why the system did what it did — is the
design-level response to this asymmetry. It tries to restore some transparency to
the person affected. But G11 is violated more than almost any other guideline in
the study.

The Rawlsian veil of ignorance test applied here: would you design this system if
you did not know whether you would be the institution deploying it or the person
subject to its decisions? Most systems as currently designed would not survive this test.

---

## Facial Recognition — The Clearest Case

Facial recognition is the sharpest example of the surveillance inversion because
the asymmetry is most visible:

**What facial recognition does:** Identifies individuals from images or video,
matching them against databases, in public spaces, without their knowledge or consent.

**The accountability asymmetry applied:**

- A private individual walking in public: high privacy expectation in their movements
- A police officer exercising power in public: lower privacy expectation in their
  use of that power
- A facial recognition system deploying state power against citizens: maximum
  accountability requirement

**What the accountability asymmetry would require:**

- Public disclosure of where systems are deployed
- Independent audit of error rates, especially across demographic groups
- Community consent before deployment in public spaces
- Accessible appeals mechanism for incorrect matches
- Prohibition on use for protected characteristics inference

**What current practice looks like:**

- Deployment often undisclosed
- Error rates for dark-skinned faces documented to be dramatically higher —
  NIST studies showing error rates 10-100x higher for Black and Asian faces
  than white faces in some systems
- No standard community consent process
- Appeals mechanisms often absent or opaque
- Use for immigration enforcement, protestor identification, and other high-stakes
  contexts with minimal oversight

The surveillance inversion is most visible here: the people most likely to be
misidentified (Black women documented at highest error rates) are also the people
with least power to contest or appeal the misidentification.

---

## Consent and Its Limits in Big Data

The standard model of privacy protection: **notice and consent**. Tell people what
you will collect. Get their agreement. Then proceed.

This model is broken for big data AI systems in three specific ways:

**1. Consent is not meaningful at scale.**
Nobody reads terms of service. The legal fiction that a click on "I agree" constitutes
meaningful informed consent for complex data processing that will affect you in ways you
cannot anticipate is not defensible. It satisfies a legal requirement. It does not
satisfy the ethical standard of genuine consent.

**2. The inferences are not disclosed.**
Consent can be given for the collection of explicit data. It cannot be given for
inferences from that data that were not described at collection time. You consented
to location data for navigation. You did not consent to the inference that your
regular presence near an addiction treatment clinic makes you a credit risk.

**3. Contextual integrity violations are not captured.**
Consent frameworks do not capture whether data flows appropriately across contexts.
You consented to sharing your health data with your doctor. You did not consent to
that data flowing to an employer via a data broker aggregating health system records.
The consent was genuine. The contextual integrity violation is still real.

**What this means for AI governance:**

Consent is necessary but not sufficient. Additional requirements:
- **Data minimisation** — only collect what is needed for the declared purpose
- **Purpose limitation** — data cannot be used for purposes beyond what was disclosed
- **Contextual integrity** — data flows must respect the norms of the context in which
  data was shared, not just the explicit consent terms
- **Inference disclosure** — the inferences being made from data should be disclosed,
  not just the data being collected

---

## The Generative AI Information Access Problem

The question "how is generative AI changing the way we access information?" is a
privacy question disguised as an information access question.

When you search Google, you receive links to sources. You can evaluate the source,
check the date, read the context, decide how much to trust it.

When you query a generative AI, you receive a synthesised answer. The sources are
often not cited. The training data is not disclosed. The model's confidence is often
presented without calibration. The information flow has broken contextual integrity
in multiple directions:

- Training data was collected without clear consent for use in generating outputs
- The model's synthesis may combine information from contexts that should not flow together
- The user cannot evaluate the source, date, or context of the information
- The model may confidently generate false information (hallucination) without signalling uncertainty

From a privacy standpoint: generative AI creates new forms of contextual integrity
violation by aggregating and synthesising information across contexts that the people
who originally shared that information never intended to be combined.

From an accountability standpoint: the opacity of the model — what was it trained on,
whose information did it synthesise, how confident is it — is precisely the inverse
of what the accountability asymmetry requires for systems that hold this much information
and exercise this much influence.

---

## Key Insight

> Privacy and transparency are not opposites.
> They are both claims about who has the right to information.
> Which claim wins depends on who holds power and over whom.
>
> The accountability asymmetry says: the more power you hold over others,
> the less privacy you are entitled to in the exercise of that power.
>
> Surveillance technology has inverted this: the least powerful are most transparent,
> the most powerful institutions are most opaque.
>
> Restoring the accountability asymmetry — not eliminating surveillance,
> but directing transparency toward power rather than away from it —
> is the structural fix that no principles document has yet produced.

---

## Connections

- *Topic 05 — Why Regulation* — regulatory capture is what happens when the institutions
  that should be transparent use their power to remain opaque
- *Concept — Categorical Data Exclusion* — minimum necessary data as the upstream
  intervention before contextual integrity violations can occur
- *Concept — Data Intimacy and Ethics Limits* — the intimate data that platforms collect
  is the clearest case of contextual integrity violation at scale
- *Concept — Human Safety in AI Landscape* — facial recognition section documents the
  error rate asymmetry across demographic groups
- *Microsoft G11* — make clear why the system did what it did — is the design-level
  response to the AI accountability asymmetry
- *Rawls veil of ignorance* — would you design this surveillance system if you didn't
  know whether you'd be the institution or the subject?
