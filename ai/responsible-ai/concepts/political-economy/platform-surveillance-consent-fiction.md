# Platform Surveillance and the Consent Fiction

*Personal study notes — original analysis and synthesis covering:
bundled consent, cross-site tracking, screenshot surveillance,
the Off-Facebook Activity tool as ethics-as-defanging.*

---

## Why Granular Terms and Conditions Don't Exist

Because granular terms and conditions would reduce the amount of data collected,
and data collection is the business model.

That is the complete answer. Everything else is elaboration.

**The honest structural explanation:**

The all-or-nothing terms are not a design oversight or a legal convenience.
They are a deliberate architecture that serves the platform's interests by
preventing users from making the choices they would actually make if given
real options.

If Facebook offered genuine granular consent:
- Allow friends to see my posts: **yes**
- Allow Facebook to use my posts to train AI models: **no**
- Allow advertisers to target me based on my browsing history: **no**
- Allow Facebook to infer my political views from my behaviour: **no**
- Allow Facebook to share my data with third-party data brokers: **absolutely not**

Most users, given genuine options, would select approximately this pattern.
The result: Facebook's ad targeting would collapse, its data brokerage revenue
would collapse, its AI training pipeline would collapse. The entire business
model depends on collecting data the user would not consent to if actually asked.

This is why granular consent is not offered: it would reveal, in the most direct
possible way, that the business model depends on doing things users would refuse
if asked.

---

## The GDPR Experiment — What Happens When Real Choice Is Offered

The EU's General Data Protection Regulation requires something closer to granular
consent. Cookie banners must offer a genuine "reject all" option alongside "accept
all." The result: when users are given a real choice, a large majority reject
non-essential tracking cookies.

Platforms responded in two ways:

1. **Dark patterns** — making the "reject" option more difficult to find than
   the "accept" option: smaller text, more clicks required, buried in menus
2. **Privacy as a paid luxury** — Meta's 2023 approach: making "reject all"
   require a paid subscription (€9.99/month on mobile) — turning privacy into
   something only people who can afford it can access

Both responses reveal the same thing: genuine granular consent is incompatible
with the business model, so the platforms work to undermine it while technically
complying with the law.

---

## The Legal Fiction of Consent

Contract law has a concept called **unconscionability** — a contract can be voided
if the terms are so one-sided, and the power asymmetry so extreme, that no
reasonable person would have agreed if they fully understood the terms.

Terms of service agreements meet this standard:

- They are thousands of words long
- Written in legal language designed to obscure rather than clarify
- Change unilaterally after agreement without meaningful notice
- Are presented on a take-it-or-leave-it basis with no negotiation
- Are agreed to under social pressure (everyone uses this platform) that removes
  meaningful choice
- Permit practices the user has no knowledge of and would not consent to if explained

Courts have largely not voided these agreements — partly because doing so would
destabilise enormous commercial relationships, and partly because the legal framework
for evaluating digital consent has not kept pace with the reality of what consent
means in a digital context.

**The consent framework is the industry's preferred alternative to direct regulation.**
It allows companies to claim they have user permission for practices that users would
refuse if properly understood. Genuine granular consent would collapse the consent
fiction. Direct regulation would make the fiction irrelevant.

**The two honest alternatives:**

1. **Change the business model** so it does not depend on data users would refuse
   to provide. Financially costly. Companies resist it.

2. **Regulate the data practices directly** — rather than relying on consent,
   prohibit specific uses of data regardless of what users "agreed to." Véliz's
   proposal: ban data brokers entirely, ban personalised advertising, impose data
   minimisation requirements. This approach does not rely on consent at all.
   It simply prohibits the harmful practice.

---

## What Granular Consent Would Actually Require

It is not technically difficult. A well-designed consent interface could present:

- What data is collected (location, contacts, browsing, messages — categorised simply)
- What it is used for (advertising, AI training, data sales, product improvement)
- Who receives it (the company, advertisers, data brokers, governments on request)
- Toggles for each category with clear descriptions
- Plain-language explanation of what each toggle controls

This is achievable. **Apple's App Tracking Transparency (ATT) framework** does a
version of it for cross-app tracking. The result: a majority of users opted out.
App developers lost revenue. **Meta lost approximately $10 billion in annual revenue
in the first year following the iOS 14.5 update** that introduced ATT.

That $10 billion figure tells you everything about why granular consent is not
offered voluntarily. It is not technically hard. It is financially catastrophic
for the current business model.

---

## Bundled Consent — GDPR Article 7(4)

The grouping of unrelated data practices into a single "I agree" button has a name
in privacy law: **tying** or **bundled consent**, and it is explicitly prohibited
under GDPR Article 7(4).

**The principle:**

> Consent is not freely given if it is bundled — if agreeing to one service
> requires agreeing to data practices unrelated to that service.

**Applied to Facebook messaging:**

If I want to use Facebook's messaging feature, that is one service with one data
requirement — the content of my messages to the people I message. It does not
require access to my browsing history, my location data, my contacts, my political
inferences, or my data being sold to third parties. Those are separate business
lines with separate data requirements. Bundling them into a single "yes" or "no"
eliminates meaningful consent.

**GDPR Article 7(4):**

> "When assessing whether consent is freely given, utmost account shall be taken
> of whether, inter alia, the performance of a contract, including the provision
> of a service, is conditional on consent to the processing of personal data that
> is not necessary for the performance of that contract."

Translation: you cannot make access to a service conditional on consent to data
processing not necessary for that service.

**The unbundling table:**

| Data | Service it enables | Necessary? | Consent required separately? |
|---|---|---|---|
| Message content | Delivering messages | Yes | No — inherent to the service |
| Contact list | Finding friends | Debatable | Yes, opt-in reasonable |
| Location | Location sharing features | Only when used | Yes, per-use |
| Browsing history | Nothing for the user | No | Yes, refusable without service loss |
| Political inference | Nothing for the user | No | Yes, should be refusable |
| Third-party data sale | Nothing for the user | No | Yes, should default to refused |

The last three rows are pure platform revenue extraction. They provide nothing to
the user. The user would refuse them if they could refuse without losing access
to the service. Bundling them into the same consent as the first row is the
mechanism through which the platform extracts data the user would not provide
voluntarily.

**The three violations bundled consent produces simultaneously:**

- **Contextual integrity violation** — data shared for one purpose (communicating
  with friends) flows under a different transmission principle (commercial exploitation)
  than the sharing context established
- **Free consent violation** — consent obtained by conditioning an unrelated service
  on it is not freely given
- **Autonomy violation** — the user's capacity to make genuine choices about their
  own data is structurally eliminated by the bundling

**The regulatory response that follows:**

- Every distinct data use requires its own consent
- Consent to one use cannot be conditioned on consent to another unrelated use
- Refusing non-essential data uses cannot result in loss of access to the core service
- The default for non-essential data collection is **no**, not yes

---

## LinkedIn Screenshot Detection — Device Sovereignty

LinkedIn detects screenshots through browser APIs and mobile OS features. On mobile,
some operating systems provide screenshot detection events that apps can listen to.
On desktop, certain browser-based mechanisms detect screen capture.

**Why this is a privacy violation — five angles:**

**1. Covert surveillance of your own device activity.**
You are using your own device. LinkedIn is a service running on that device. The act
of taking a screenshot is an action on your device, not on LinkedIn's servers.
LinkedIn has no legitimate claim over what you do on your own device. Monitoring your
device activity and transmitting that back to LinkedIn's servers is surveillance of
your local computing environment.

Analogy: a shop detecting that you have a notebook and notifying the shop manager
every time you write something down. The notebook is yours. Writing in it is your
activity. The shop has no legitimate interest in that activity.

**2. The contextual integrity violation.**
Once content is rendered on your screen, it exists in your device's context — your
local computing environment, under your control. The transmission principle governing
content on your device is your own use and discretion. LinkedIn monitoring what you do
with content after it has been delivered to your device extends LinkedIn's reach into
a space that is yours.

**3. You were never meaningfully asked.**
If LinkedIn updated its terms to include screenshot detection, that update was:
- Unilateral — LinkedIn changed terms without your negotiation
- All-or-nothing — accept or lose access to your professional network
- Not separately consented to — bundled into the same agreement as professional networking

You never specifically agreed to "LinkedIn may monitor my device's screen capture
activity." Under GDPR Article 7(4), this is not freely given consent. Screenshot
monitoring and professional networking are unrelated. Tying them is the violation.

**4. What LinkedIn can actually restrict — the legal tension.**
A terms of service clause cannot override your legal rights under copyright fair
use/fair dealing. A terms of service clause cannot extend into controlling your local
device's operations. A terms of service clause changed without meaningful notice may
not bind you to the new restriction.

LinkedIn monitoring your screenshot activity and transmitting it back to its servers
is doing something different from simply prohibiting screenshots — it is actively
surveilling your device to enforce a contractual term, which is a more invasive act
than the term itself.

**5. The notification is the harm.**
When LinkedIn logs that you took a screenshot, it creates a record of:
- What content you found worth capturing
- When you captured it
- Information that could be used against you — if you screenshotted a competitor
  job posting and your employer is LinkedIn's enterprise customer

This is not neutral technical telemetry. It is behavioural surveillance with
consequences you cannot anticipate.

**The broader principle:**

A service granted access to your device for one purpose — professional networking —
has no legitimate claim to monitor other device activities beyond what is necessary
for that function. Screenshot detection is not necessary for LinkedIn to function.
It is surveillance serving LinkedIn's interest in controlling how its content is used,
at the cost of surveilling your device.

---

## Facebook's Cross-Site Tracking — The Full Picture

Facebook does not just collect data when you visit Facebook. It tracks you across
the entire web — even when you are not on Facebook and not logged in — through
several mechanisms simultaneously.

**The Facebook Pixel:**
Millions of websites embed Facebook's JavaScript code. When you visit any of those
sites, the Pixel fires and sends a signal to Facebook's servers: this device, at this
time, visited this page. Facebook matches the visit to your profile using your IP
address, browser fingerprint, and other identifiers — even if you are not logged in,
even if you have cleared your cookies.

You did not visit Facebook. You did not interact with Facebook. But Facebook knows
you visited that website.

**Browser fingerprinting:**
Cookies can be deleted. Browser fingerprints cannot. Your browser has a unique
combination of: screen resolution, installed fonts, browser version, operating system,
timezone, language settings, graphics hardware, and dozens of other attributes.
Combined, these produce a fingerprint that is unique or near-unique to your device.
Facebook uses this to re-identify you after you clear cookies, switch browsers, or
use private browsing mode.

**The login button:**
Every "Login with Facebook" button tells Facebook you visited that site — even if
you do not click it. The button loads JavaScript from Facebook's servers, which
executes on your device and reports the visit.

**The "like" and "share" buttons:**
Same mechanism. Every social button on a third-party site is Facebook code executing
on your device and reporting back that you were on that page.

**What this profile contains:**
- What news you read and for how long
- What products you browsed and on which sites
- What health information you searched for
- What legal or financial services you looked at
- What political content you engaged with
- What you bought, on which platforms, at what times

**The contextual integrity violations:**
Each website you visited had its own context. Reading a health article happened in
a health information context — the transmission principle did not include Facebook.
Browsing a legal services site happened in a legal inquiry context — the transmission
principle did not include Facebook. Shopping happened in a commercial context — the
transmission principle did not include Facebook.

Facebook inserted itself into all of those contexts, invisibly, collecting data under
transmission principles none of those contexts established.

**Why this is legal in the United States:**
No comprehensive federal privacy law. The sectoral approach — HIPAA for healthcare,
COPPA for children, GLBA for finance — does not cover general web tracking. In the
absence of a federal law prohibiting it, and with consent captured through broadly
worded terms of service, the practice is legal.

In the EU it is substantially more restricted under GDPR. Enforcement has been
inconsistent and fines, while large, are small relative to the revenue the tracking
generates.

**The honest summary:**
You are not the customer. You are the product — and the product is a comprehensive
behavioural profile built by surveilling you everywhere you go on the internet,
assembled without meaningful disclosure, sold to advertisers to influence your behaviour.

---

## The Off-Facebook Activity Tool — A Confession Dressed as a Product Launch

The image shows Facebook's Off-Facebook Activity tool announcement:

**"You see it."** — View a summary of information Facebook receives about your
activity on other apps and websites.

*Translation: we have been collecting this for years without telling you. Here is
a list of what we took.*

**"You control it."** — If you'd like, you can disconnect that information from
your account, and it will not be associated with you personally.

*Translation: we will stop associating it with your named account. We will not
stop collecting it. The data still flows to Facebook's servers. It is just stored
"anonymously" — which Facebook can re-identify through fingerprinting anyway.*

**Why the tool exists:**

The tool was announced in 2018 and rolled out in 2019 — directly following the
Cambridge Analytica scandal, congressional hearings, and enormous regulatory pressure.
It was not a proactive privacy commitment. It was the minimum disclosure required
to survive the political moment.

**What the tool does not do:**

- Does not stop the Facebook Pixel from collecting data
- Does not stop websites from sending your activity to Facebook
- Does not delete the data already collected
- "Disconnecting" means data is stored without your name — Facebook still has it
- Future visits to the same sites still send data — you can clear history, collection continues
- The tool has to be found, understood, and actively used — the default is collection

**The "you control it" language is doing specific work:**

It shifts responsibility from Facebook to you. If you do not manage it, that is your
choice. The collection is positioned as the default you opt out of — when the honest
framing is that collection without consent is the violation and opt-in should be the
default.

**The Java House and Downtown Stylists:**

The businesses listed in the screenshot — a coffee shop, a hair salon — sent your
activity to Facebook. They embedded the Facebook Pixel on their websites, probably
because a marketing consultant told them it would help with advertising, without
understanding or disclosing to their customers that a visit to their website would
report to Facebook.

These businesses are also victims. They became data collectors for Facebook's
advertising infrastructure without meaningfully choosing to do so, without
understanding the implications, and without disclosing it to their customers.
Facebook recruited them as surveillance nodes and presented this to them as a
marketing tool.

**The shame that the framing obscures:**

The product being announced is: we have been surveilling you everywhere you go on
the internet, including at your local coffee shop and hair salon, without your
knowledge. Here is a list of everywhere we followed you. You can clear the list,
though we will keep following you.

That is not a privacy feature. It is a confession dressed as a product launch.

This is the ethics-as-defanging pattern in its most visible form: the surveillance
continues. The announcement produces the appearance of accountability. The regulatory
pressure eases. The data keeps flowing. Meta calls it innovation.

---

## Did Regulators Not See This? — The Enforcement Gap

Yes. They saw it.

The FTC saw it. The EU Data Protection Authorities saw it. The UK ICO saw it.
Congressional investigators saw it. Internal Meta communications — through the
Cambridge Analytica fallout, through legal proceedings, through Frances Haugen's
2021 whistleblower disclosures — revealed employees treating privacy features as
exactly what they are: regulatory theatre designed to reduce pressure, not genuine
protection.

The problem is not that regulators lacked knowledge. It is that the enforcement
tools available are not commensurate with the harm being caused or the revenue
being generated.

### The FTC Consent Decree — Violation Priced as a Cost of Business

In 2012, the FTC required Meta to stop misrepresenting its privacy practices and
get user consent before sharing data beyond stated privacy settings. Meta signed
the consent decree.

In 2019 — seven years later — the FTC fined Meta $5 billion for violating that
consent decree. At the time, the largest privacy fine in history.

**What $5 billion means to Meta:**

Meta's revenue in 2018 was approximately $55 billion. The $5 billion fine was
roughly 9% of annual revenue — paid once, for seven years of ongoing violation.

The business case calculation: the surveillance revenue generated over seven years
substantially exceeded the eventual fine. Violation was more profitable than
compliance. The fine did not deter — it priced the violation.

This is not an accident. When regulators set fines smaller than the revenue the
violation generates, they are effectively licensing the violation. The consent decree
became a speed bump, not a stop sign.

### The Internal Communications Pattern

Through whistleblower disclosures and legal proceedings, substantial internal Meta
communications have become public. The consistent pattern:

- Internal research documents harm that is not disclosed externally
- Privacy features are designed to satisfy regulatory optics, not genuinely limit
  collection
- The business impact of genuine privacy protection is modelled internally and rejected
- Regulatory compliance is treated as a constraint to be minimised, not a standard
  to be met
- Privacy announcements are timed to regulatory pressure, not to genuine improvement

The dynamic you describe — employees treating privacy features as a ruse — is
exactly what the internal communications reveal. The public announcement says "you
control it." The internal engineering reality is designed to ensure that control
is as limited as possible while satisfying the legal minimum.

### Why Regulators Saw It and Could Not Stop It

**Enforcement tools are inadequate.**
Fines smaller than the revenue generated by the violation do not deter. They price
the violation. The $5 billion FTC fine was insufficient relative to Meta's revenue
and the revenue the violation generated. The remedy needs to be: personal liability
for executives, structural separation of the surveillance business from the social
network, or outright prohibition of the harmful practices.

**Regulatory bodies are under-resourced.**
The FTC has a fraction of the staff and budget of Meta's legal team. EU data
protection authorities, which have stronger legal tools under GDPR, are chronically
underfunded relative to the complexity of the cases they pursue. A company with
thousands of engineers and hundreds of lawyers faces regulatory bodies with dozens
of investigators.

**The regulatory capture dynamic.**
The revolving door between tech companies and regulatory bodies means the people
writing and enforcing regulations often previously worked at or will later work at
the companies being regulated. The same dynamic as the FEC — the regulated parties
shape the regulatory environment. Former Meta employees at the FTC. Former FTC
staff at Meta's compliance team. The institutional knowledge flows both directions,
and the financial incentive flows toward the company.

**The legal process is slow.**
By the time a violation is identified, investigated, litigated, and resolved, years
have passed. The violation continued during those years. New violations began.
The regulatory timeline cannot keep pace with the deployment timeline. Meta
launches features faster than the FTC can investigate them.

**Meta spent hundreds of millions on lobbying.**
When regulators propose stronger enforcement tools — the ability to break up the
company, meaningful data minimisation requirements, personal liability for executives
— that lobbying shapes the legislative response. The tools that would make enforcement
effective are the tools that never get passed.

### The Haugen Disclosures — What Internal Knowledge Looked Like

Frances Haugen's 2021 disclosures provided the clearest public window into what
Meta's internal knowledge looked like versus its public statements:

- Internal research documented that Instagram caused measurable harm to teenage
  girls' mental health — findings not disclosed publicly
- Internal research documented that the platform's algorithms amplified divisive
  content because engagement metrics rewarded outrage
- Internal discussions acknowledged problems that were not being acted on because
  the fixes would reduce engagement metrics

The disclosures confirmed what the privacy tool pattern already suggested: Meta's
internal knowledge of its own harms was significantly greater than what it disclosed
to regulators or the public. The gap between internal knowledge and public statement
is not ignorance. It is the deliberate management of information to regulators — the
same pattern as every regulatory capture case in this repository.

### The Honest Assessment

Regulators saw it. Regulators know. The structural problem is that:

- The violated rules produce fines smaller than the violation's revenue
- The enforcement bodies are outgunned by the companies they regulate
- The political process is captured by the companies' lobbying
- The legal timeline cannot match the product deployment timeline

This is why Véliz argues for direct prohibition rather than consent frameworks and
fine structures. The consent framework has been violated for decades with $5 billion
fines and continued violation. Direct prohibition of data brokerage, personalised
political advertising, and cross-context tracking would make the consent question
moot — the practices would simply be illegal regardless of what any terms of service
say.

The regulators are not ignorant. They are structurally outmatched by the entities
they regulate, operating with inadequate tools, in a political environment shaped
by the companies' lobbying. The shame belongs to the companies. The structural fix
belongs to the political process that has not yet produced enforcement commensurate
with the harm.

---

## The Responsibility Inversion — Notice and Consent as Recycling

The course material names this precisely:

> "Notice and consent is similar to trash recycling: it puts the onus on the
> wrong party. It does nothing to call into question the large practices of
> pervasive and ubiquitous data collection; it takes those practices as given."

**The recycling analogy:**

Recycling puts moral responsibility for industrial waste on the individual consumer.
Did you sort your recycling correctly? Did you rinse the containers? Did you check
which plastics your municipality accepts? If the plastic ends up in landfill anyway —
if the "recycling" stream is actually incinerated — that is somehow your failure,
not the manufacturer's failure for producing non-recyclable packaging at scale.

The manufacturer produced the waste. You are responsible for managing it correctly.
Individual compliance with recycling rules does not address the upstream production
problem. Only direct regulation of the manufacturer does.

Notice and consent is the same structure applied to data:

- The platform designed the surveillance architecture
- The platform embedded the Pixel across millions of websites
- The platform created the business model requiring mass data extraction
- The platform wrote terms in language designed to obscure rather than clarify
- The platform presented those terms on a take-it-or-leave-it basis under social pressure

And then: if your data is used in ways that harm you, the question asked is whether
you read the terms and clicked agree. Your fault for not reading the 50,000-word
document. Your fault for not finding the opt-out buried seven menus deep. Your fault
for not understanding that "we may share your data with partners" means "we sell
everything to anyone who pays."

**The structural inversion:**

Notice and consent places legal and moral responsibility on the party with:
- The least power
- The least information
- The least ability to change the underlying system

And removes legal and moral responsibility from the party with:
- The most power
- The most information
- The complete ability to change the underlying system

This is not a side effect of the framework. It is its function. The notice and
consent framework was developed in an era of consumer protection law where the
assumption was roughly equal bargaining power. Applied to platform surveillance,
where the power asymmetry is total, it produces the exact inversion the course
material names: the victim of the surveillance is responsible for managing it
correctly, and the perpetrator is responsible for nothing as long as it disclosed
in the terms.

**Why this is the industry's preferred framework:**

Because it is the framework under which the platforms bear the least responsibility.
Every alternative — data minimisation, purpose limitation, prohibition of certain
uses, fiduciary duty — places responsibility on the collector. Notice and consent
places it on the subject. The industry lobbied for notice and consent precisely
because it is the framework most compatible with their business model.

**The Véliz collective privacy argument applied here:**

The individual cannot opt out of a structural surveillance system by reading privacy
policies and adjusting settings. The Facebook Pixel fires when you visit a website
that embedded it. You had no relationship with Facebook, made no agreement with
Facebook, and have no ability to prevent Facebook collecting data about your visit.
Your individual consent or lack of it is irrelevant to the system's operation.

Making the individual responsible for managing a structural surveillance system
through individual choices is like making each person responsible for cleaning
the river that a factory is polluting upstream. The pollution is not your fault.
The factory produced it. Individual management of the water does not address the
factory. Direct regulation of the factory does.

**If you believed your data was wrongly used — are you to blame?**

No. Not ethically.

Consent obtained through:
- Terms you could not meaningfully understand
- A binary choice between full acceptance and losing your social network
- Social pressure that removed genuine choice
- Language designed to obscure what was actually being agreed to
- For practices you would have refused if clearly explained

...is not genuine consent. It is the legal shell of consent with none of the
moral substance.

The moral substance of consent requires:
- Genuine understanding of what is being agreed to
- Genuine alternatives — the ability to refuse without disproportionate cost
- Genuine freedom from coercion
- Specific consent to specific practices — not blanket acceptance of everything

Notice and consent as practised by platforms satisfies none of these for the
practices that most harm users.

The law, in most jurisdictions, still treats the click as consent. Ethics does
not have to follow the law's error. Better law — GDPR, the EU AI Act, the Platform
Work Directive — is starting to catch up: the click is not consent when the
conditions under which it was obtained were coercive, opaque, and asymmetric.

**The direct regulation argument that follows:**

If notice and consent cannot produce genuine consent — because the power asymmetry
makes genuine choice structurally impossible — then the framework should be abandoned
in favour of direct regulation that does not rely on consent at all.

Véliz: ban data brokers. Ban personalised advertising. Impose data minimisation.
These prohibitions do not ask whether users consented. They simply declare certain
practices off-limits regardless of what any terms of service say. The consent
question becomes moot because the harmful practice is prohibited.

This is what happened with food safety. The consumer does not consent to or refuse
individual food safety standards — they are simply required of any food sold. The
responsibility for safe food rests on the producer, not on the consumer's ability
to audit the supply chain and manage their own exposure. Privacy regulation should
work the same way.

---

## The Through-Line

All four cases — bundled consent, cross-site tracking, screenshot surveillance,
the Off-Facebook Activity tool — express the same structural logic:

> The platform's access to your device, your attention, and your data was granted
> for one purpose. It is used for a different purpose. The consent obtained for
> the first is used to justify the second. The second never received genuine consent
> — it received coerced consent, where the coercion is the threat of losing access
> to the first.

The remedy is not better privacy settings. Privacy settings are opt-out mechanisms
layered over opt-in surveillance architectures. They individualise responsibility
for a structural problem.

The remedy is:
1. Unbundled consent — each data use requires its own justification and its own consent
2. Data minimisation as a default — collect only what is necessary, not everything possible
3. Direct prohibition of the most harmful practices — data brokerage, personalised
   political advertising, cross-context tracking — regardless of what terms of service say
4. Opt-in as the default for non-essential collection, not opt-out

Until those structural changes exist, the consent the platforms claim is not consent.
It is the legal residue of a power asymmetry that made meaningful choice impossible.

---

## Connections

- *Privacy theory reference* — Véliz: ban data brokers, ban personalised advertising;
  Nissenbaum: contextual integrity violations across all four cases
- *Topic 10 — Privacy, Transparency, Accountability* — surveillance inversion; consent
  limits in big data; the three failures of the consent framework
- *Categorical data exclusion* — the upstream version: don't collect it at all
- *Ethics as defanging* — the Off-Facebook Activity tool as the clearest example of
  the ethics-as-defanging pattern applied to a specific product announcement
- *Political economy — neoliberalism* — the business model cannot change through
  voluntary compliance; direct regulation is the structural fix

---

## Key Insight

> The all-or-nothing terms exist because granular terms would reveal
> that the business model depends on doing things users would refuse if asked.
>
> The Off-Facebook Activity tool exists because regulators required disclosure,
> not because Facebook wanted to give you control.
>
> The $10 billion Meta lost when Apple gave users real tracking choice
> is the price of genuine consent — and the reason it will never be offered voluntarily.
>
> A confession dressed as a product launch is still a confession.
> The shame is real. The innovation claim is not.
