# Categorical Data Exclusion — Addiction-Based Products

## The Core Argument

Society has already made a judgment about certain product categories: their harm is
sufficiently documented and their addiction mechanisms sufficiently clear that normal
market freedom does not apply. These categories receive special regulatory treatment
as a result.

The logical extension of that existing judgment — one that has not yet been made — is:

> **Products in harm-recognized categories should only collect the minimum data
> necessary for the minimum necessary purpose — with criminal enforcement,
> not guidelines and fines.**

The principle already exists in privacy law. It is called **data minimisation**.
Currently it is treated as a best practice with weak enforcement. For harm-recognized
categories it should be an absolute:

- **Collect only what the specific, declared purpose requires**
- **No opt-in pathway to broader collection** — consent cannot override this
- **Any collection beyond the minimum is a criminal offence, not a regulatory violation**

The current system inverts the burden: collect everything, then justify what you use.
The honest system reverses it: justify what you need before you collect anything.

---

## Minimum Necessary Data — What That Looks Like in Practice

The argument is not that these products cannot exist. It is that they can only collect
what their legitimate, narrow function requires. Nothing more is permissible, regardless
of consent.

| Product                                    | Legitimate purpose                  | Permissible data                                                                | Everything else                                                                                                                  |
| ------------------------------------------ | ----------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Tobacco / vape retail**                  | Sell an age-restricted product      | Age verification at point of sale                                               | Purchase history, brand switching data, price sensitivity, loyalty profiles — **prohibited**                                     |
| **Casinos / betting**                      | Operate a licensed gambling service | Age verification, self-exclusion check, transaction record for legal compliance | Behavioral profiling, session analysis, emotional state targeting, loss-chasing pattern detection for retention — **prohibited** |
| **Social media with addiction mechanisms** | Connect users                       | Account existence, content posted                                               | Engagement pattern analysis, emotional state inference, vulnerability profiling, behavioral targeting — **prohibited**           |

**Age verification does not require identity.** A cryptographic proof that a credential
issued by a trusted authority confirms an age threshold is sufficient. The platform
does not need to know who you are — only that you meet the threshold. Technologies
for this exist. They are not deployed because identity data is more valuable than
age compliance.

---

## On Consent — Why It Cannot Unlock Broader Collection

Current frameworks allow platforms to present a consent wall — a long document and a
button — and treat the click as meaningful agreement. Courts have largely accepted this.
For harm-recognized categories, this should not be sufficient, for two reasons:

**First:** You cannot meaningfully consent to a system specifically designed to exploit
your psychology against your own interests. The consent is structurally compromised
from the start — you do not fully understand what you are agreeing to, and the system
is designed to ensure you do not. We recognise this for children universally.
The argument is that the same logic applies to adults when the mechanism is
sufficiently predatory.

**Second:** The value of minimum necessary data as a protection comes precisely from
its absoluteness. An opt-in pathway for broader collection destroys the protection —
the platform will make the opt-in the path of least resistance, and most users will
follow it. The rule only works if it has no exceptions.

---

## The Categories Society Has Already Recognized

Each of the following already receives special regulatory treatment in most jurisdictions,
precisely because the harm is acknowledged:

| Category                      | Existing interventions                                                                             |
| ----------------------------- | -------------------------------------------------------------------------------------------------- |
| **Cigarettes / tobacco**      | Advertising bans, health warnings, age restrictions, plain packaging, taxation as deterrent        |
| **Vapes / e-cigarettes**      | Increasingly identical to tobacco as evidence accumulates                                          |
| **Casinos / gambling**        | Age verification, self-exclusion lists, spending limits, location restrictions, operator licensing |
| **Online betting**            | Same as above, extending to app-based platforms                                                    |
| **Social media (emerging)**   | Age restrictions, some advertising limits — recognition growing, intervention lagging              |
| **Addictive pharmaceuticals** | Prescription controls, scheduling, dispensing limits                                               |

The regulatory judgment is already made. The product is harmful. The market cannot
self-correct. External constraint is required.

The intervention that follows logically — categorical data exclusion — has not been made.

---

## Why Data Collection Amplifies the Harm

Data collection by addiction-based products does not merely record behavior.
It enables the precision engineering of addiction in ways that were not previously possible.

**Pre-data era:** A casino knew you came back on Fridays. A cigarette company knew
which demographics smoked most. The harm was real but the targeting was blunt.

**Current era:** A platform knows:

- Which emotional states correlate with your highest engagement or spending
- Which sounds, images, or content sequences keep you in the session longest
- What time of night you are most vulnerable to compulsive behavior
- Which specific notification, sent at which interval, produces the strongest response
- How your behavior changes when you are stressed, lonely, or sleep-deprived

The data does not just observe the addiction. It enables precision-engineered addiction
targeted at individual psychological profiles at scale. The surveillance and the
harm mechanism are the same product.

**AI makes this categorically worse.** AI-powered recommendation and optimization
systems can identify and exploit individual vulnerabilities with a precision and speed
that pre-AI systems could not approach. The combination of intimate data collection
and AI-powered optimization creates addiction mechanisms that are qualitatively
different from anything that existed when existing regulations were designed.

---

## The Upstream Intervention

Most regulatory discourse about harmful products focuses downstream:

- How is the data stored?
- Who has access to it?
- What are the consent requirements?
- What deletion rights exist?

These are the wrong questions for addiction-based products. They accept data collection
as a given and try to regulate what happens to the data afterward.

The upstream intervention cuts at the right point:

> If the mechanism producing the data is itself the harm, regulate the mechanism.
> Do not build a careful framework for how a gambling platform stores your
> vulnerability data. Remove the right to collect it in the first place.

This follows the logic of existing pharmaceutical regulation: you cannot bring a drug
to market and then figure out the safety profile afterward. The precondition for
operating is demonstrated harm mitigation, not demonstrated data security.

---

## Higher Entry Barriers

Currently, the cost of starting a social media platform, a gambling app, or a vaping
brand is relatively low. Low barriers produce proliferation of harm-maximizing products
because the incentive structure rewards whoever optimizes the addiction fastest.

Higher entry barriers for harm-recognized categories would:

1. **Require demonstrated harm mitigation before operating** — not a compliance checkbox,
   but genuine evidence that the product does not rely on addiction mechanisms
2. **Impose substantial compliance costs** — making it expensive to enter the category,
   which favors actors who have genuinely thought about what they are building
3. **Slow proliferation** — fewer harm-maximizing products reach scale before their
   mechanisms are understood

This is the pharmaceutical model applied to digital products. Clinical trials are slow
and expensive by design, because the cost of getting it wrong falls on people who had
no say in the decision. The same logic applies when the product's mechanism of profit
is demonstrably harmful to the user.

---

## The Honest Complications

**Definition problem.** "Addiction mechanism" needs a regulatory definition precise
enough to survive legal challenge from companies with unlimited litigation budgets.
Variable reward schedules, infinite scroll, notification engineering, autoplay —
these are documented in the psychology and behavioral economics literature.
The science exists. The regulatory definition has not been constructed with sufficient
precision, partly because the industry has resisted it at every stage.

**International coordination.** A single-jurisdiction ban does not eliminate the product —
it moves the corporate domicile. TikTok illustrates this clearly: the ownership and
data access question has been politically contested for years across multiple
jurisdictions without clean resolution. Effective categorical exclusion requires
coordinated international action, which is slow and subject to the same captured
governance problems that produced the current situation.

**Uneven application.** The cut is not clean across the digital industry:

- Social media platforms with infinite scroll: clearly in scope
- Search engines: largely not
- Messaging applications: ambiguous — utility with some addictive features
- Streaming with autoplay: partially in scope
- Email: not in scope

These distinctions require regulatory precision that does not currently exist.

**None of these complications refute the principle.** They are implementation
challenges for a logically sound intervention. The fact that definition is hard does
not mean definition is impossible. The fact that international coordination is slow
does not mean the intervention is wrong.

---

## Connection to Responsible AI

The responsible AI discourse almost entirely avoids this question. It asks:

- How do we make recommendation systems fairer?
- How do we reduce bias in engagement algorithms?
- How do we give users more transparency about how their data is used?

These are the wrong questions if the product's core function is addictive by design.

The honest responsible AI question for this category is:

> Should AI be permitted to be applied to optimize addiction mechanisms at all?

Not "how do we make it more responsible" — but "should this use of AI exist?"

That question does not appear in most principles documents, ethics frameworks,
or governance guidelines, because the institutions producing those documents have
financial relationships with the companies whose products the question would abolish.

---

## Key Insight

> The regulatory judgment that these products are harmful enough to require special
> treatment has already been made. Society said so when it banned cigarette advertising
> and required casino self-exclusion lists.
>
> The intervention that follows from that judgment — categorical exclusion from the
> data economy — has not been made. The gap between the judgment and the intervention
> is not philosophical. It is political.
