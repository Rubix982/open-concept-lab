# Data Intimacy, Incentive Misalignment, and the Limits of Embedded Ethics

Notes drawn from Canca's TEDx talk, the CACM paper, and course discussion.

---

## The Intimacy of Data

The data that AI systems collect and train on is not abstract. It is intimate in the
fullest sense — it reveals things people do not share with their closest relationships:

- What you search for at 2am
- What content makes you stop scrolling, and for how long
- What you type and delete before sending
- Where you go for healthcare, for worship, for things you do not announce publicly
- The pattern of your anxiety, your loneliness, your financial stress, your desire
- Political leanings you haven't stated, health conditions you haven't disclosed,
  relationship states you haven't processed

This data is more intimate than most human relationships. It reveals things people
don't consciously know about themselves. And it is collected continuously, at scale,
by systems whose business models depend on extracting value from exactly this intimacy.

---

## The Incentive Misalignment

The more intimate the data, the more precise the ta^rgeting. The more precise the
targeting, the more valuable the platform. The incentive structure does not merely fail
to reward ethical data handling — it actively rewards the opposite.

Ethics frameworks that ask companies to collect less, retain less, or be more transparent
about use are asking them to voluntarily reduce the value of their core asset. This does
not work without external enforcement. It is structurally equivalent to asking a factory
to voluntarily clean up its own pollution.

Facebook's own internal researchers documented that Instagram caused measurable harm
to teenage girls' mental health and self-image. The research existed internally. Nothing
material changed. The product continued as designed — because the product _is_ the
mechanism that produced the harm. Changing it would be changing the product.

> "They don't care about us" is not a moral judgment about individuals.
> It is a description of an incentive architecture.

The people working inside these companies are, in the main, ordinary people trying to
build careers and support families — the same observation we made about governance.
The structure does not require malice. It requires only that financial incentives
consistently outweigh ethical ones, which they do, because that is how the system is built.

---

## Incidental Harm vs. Structural Harm

This distinction matters for understanding where ethics frameworks can and cannot reach.

**Incidental harm** — the goal is legitimate, the harm is a side effect. Examples:

- A diagnostic AI that needs to balance data privacy against accuracy
- A hiring tool that produces biased outcomes because of biased training data
- A recommendation system that surfaces misinformation as a byproduct of engagement

For incidental harms, embedded ethics frameworks — like Canca's PiE model and The Box —
are genuinely useful. The developer wants to do good and needs structured help navigating
trade-offs between core and instrumental values. The puzzle-solving model applies.

**Structural harm** — the harm is not a side effect. It is the mechanism. Examples:

- A platform whose recommendation algorithm is designed to maximise time-on-platform,
  and does so by systematically surfacing outrage, anxiety, and compulsion — because
  those emotional states produce the most activity
- A surveillance system whose core function is tracking and control
- A data broker whose product is intimate personal information sold without meaningful consent

For structural harms, embedded ethics cannot reach the problem. You cannot embed ethics
into a system whose design goal _is_ the harm. The right question is not "how do we make
this more responsible" — it is "should this exist in this form at all?" That question is
almost entirely absent from responsible AI discourse, because asking it would require
confronting the business model directly.

> Embedded ethics assumes the developer wants to do good and needs help navigating
> trade-offs. It does not address the case where the developer has already decided
> that harm is acceptable, or where the product _is_ the harm.

---

## The Biomedical Comparison — What Canca Argues

Canca explicitly compares the trajectory of AI ethics to biomedical ethics — and argues
against following the same path.

**The biomedical model:** Institutional Review Boards (IRBs) must approve research before
it happens. Nothing moves without clearing the ethics gate. This model emerged in direct
response to documented atrocities — the Tuskegee syphilis study, Nazi experimentation,
thalidomide — where the absence of ethical oversight caused catastrophic harm.

**Her argument against applying this to tech:** Development cannot stop. The speed and
scale are incomparable. A drug trial affects hundreds of people over years. A platform
update affects a billion people overnight. A gatekeeping model that slows approvals at
biomedical research pace would effectively halt all AI development — and the development
would happen anyway, somewhere with even less ethical consideration.

**Therefore: embedded ethics.** Ethics integrated at every stage of development, not
applied as an approval gate at the start. Collaborative, dynamic, ongoing — the PiE model.

---

## Where the Biomedical Comparison Turns

The tension Canca is navigating is real, but it cuts both ways.

The biomedical gatekeeping model exists because the field produced catastrophic harm
without it. The gates were built _in response to_ documented atrocities. Her embedded
ethics model implicitly assumes tech has not crossed an equivalent threshold — or that
crossing it wouldn't be prevented by gates anyway.

But consider what tech has produced without meaningful ethical governance:

- Documented harm to teenage mental health at scale (internal Facebook research,
  suppressed from publication)
- Algorithmic discrimination in housing, lending, hiring, and criminal justice
- Mass manipulation of political opinion through micro-targeted misinformation
- Surveillance infrastructure that has been used against journalists, activists,
  and minority populations
- Erosion of informed consent at a scale no individual can meaningfully navigate

One could argue the threshold has already been crossed. And if it has, then "we can't
stop development" starts to sound less like pragmatism and more like the factory saying
"we can't stop production" while the river downstream turns brown.

**The honest version of the tension:**

|                | Biomedical gatekeeping model                 | Embedded ethics model                             |
| -------------- | -------------------------------------------- | ------------------------------------------------- |
| **Strength**   | Hard stop on catastrophic harm               | Responsive, doesn't halt development              |
| **Weakness**   | Slows beneficial work, bureaucratic          | Cannot reach structural harm, requires good faith |
| **Assumes**    | The harm is in specific research acts        | The developer wants to do good                    |
| **Fails when** | Bureaucracy blocks genuinely beneficial work | The product _is_ the harm                         |

Neither model alone is sufficient. The biomedical model assumes you can identify and
gate specific harmful acts. The embedded model assumes the actor is operating in good
faith. The social media case fails both assumptions: the harm is systemic, continuous,
and built into the product design — and the actor has explicitly chosen to continue it.

---

## What This Means

**Embedded ethics is necessary but not sufficient.**

It is the right approach for the vast majority of AI development where:

- The goal is legitimate
- The harms are incidental or emergent
- The developers have genuine incentive to reduce harm

It is inadequate for cases where:

- The business model depends on the harmful mechanism
- External enforcement is the only viable constraint
- The question is whether the product should exist, not how to make it better

**The question responsible AI discourse largely avoids:**

> For which AI systems is the right ethical question not "how do we make this responsible"
> but "should this exist in this form at all?" — and who has the standing and power to
> answer that question?

Currently, almost no one with power is asking it.

---

## Key Insight

> Ethics frameworks are tools. Tools work when the person holding them wants the outcome
> the tool is designed for. A hammer does not help you if you want the nail to stay out.
> Embedded ethics, however well-designed, cannot substitute for the structural question
> of whether a product's existence is justified — and that question requires political
> power, not just ethical methodology.
