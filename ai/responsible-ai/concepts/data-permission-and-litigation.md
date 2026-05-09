# Data Permission, Fair Use, and the Coming Litigation Wave

_Personal study notes — original analysis and synthesis. Not a reproduction of course material._

---

## The Permission Question That Was Never Asked

The entire "fair use" argument in AI training data exists because the companies
did not ask permission first. They scraped first, trained first, and constructed
a legal theory afterward to justify what they had already done.

The sequence matters. This is not careful legal analysis determining that a practice
is permissible and then proceeding. It is proceeding, and then hiring lawyers to
defend the proceeding.

The simpler question — **did you have permission?** — was never asked because asking
it would have been slow and expensive. Scraping was fast and cheap. The legal risk
seemed manageable. So they scraped.

---

## The Honest Path Was Available — And Chosen Against

The companies had a genuine choice. Two paths existed:

**Path A — Honest:**

- Train exclusively on explicitly open, permissioned, consented data
- Acknowledge what you trained on and how
- Build relationships with the institutions stewarding that data
- Produce a slightly less capable model with a completely clean legal and ethical record
- Defend it honestly: "we built this on data people wanted to share"

**Path B — What actually happened:**

- Scrape everything accessible
- Train on it without asking
- Construct a legal theory afterward
- Produce a more capable model with deeply contested legal and ethical status
- Spend years in litigation while lobbying against regulation that would require consent

Path A was defensible to everyone — developers, creators, courts, regulators, the public.
Path B produced better benchmark numbers. The capability race made that the deciding factor.

---

## MIT Is MIT — The Standing Permission Argument

The clearest version of the argument:

MIT license is a standing permission. The developer who published under MIT already
said yes to everything a company needs to do. No negotiation required. No retroactive
justification. No litigation. No moral ambiguity.

Similarly:

- **Wikipedia** exists to share knowledge freely — its mission is the free dissemination
  of knowledge. A model trained on Wikipedia that helps people access and synthesise
  knowledge is arguably an extension of that mission. They would almost certainly
  have said yes if asked.
- **Project Gutenberg** exists to make literature universally accessible. Training on
  it serves exactly that purpose.
- **Common Crawl** exists specifically to make web data available for research and
  development. The standing permission is explicit.

Nobody would have objected. The open data commons wanted to be used. The companies
chose not to use it exclusively because it was smaller than the full web — and
smaller meant slightly less capable models.

---

## The GPL Case — Licences That Were Violated, Not Just Ignored

GPL license says: use this code, build on it, but if you distribute a product that
incorporates it, that product must also be GPL. It is an explicit condition with a
clear commercial path:

- Pay the maintainer for a commercial license exception — common practice
- Open source the model trained on GPL code — honour the licence's terms
- Negotiate a specific AI training licence with the maintainer community

GitHub Copilot was trained on GPL-licensed repositories and produces proprietary
output — which is exactly what GPL is designed to prevent. This is not a fair use
question. It is arguably a licence violation. Active litigation covers exactly this.

---

## The Billions Argument — They Had The Money

OpenAI raised $10 billion from Microsoft alone. Google has essentially unlimited
capital. Meta spent $30 billion on AI infrastructure in a single year.

The idea that these companies could not afford to license the data they trained on
is not credible. The music streaming industry negotiated licensing frameworks with
labels, publishers, and artists. Academic libraries negotiate bulk access to paywalled
journals. Stock photo platforms pay photographers. The mechanisms exist.

**What the honest negotiation would have looked like:**

- Approach Wikipedia, Project Gutenberg, Common Crawl — free and open, relationships
  easily established
- Negotiate bulk licensing with academic publishers for paywalled research — Elsevier,
  Springer, Nature all have licensing departments built for exactly this
- Approach GPL maintainers for commercial licence exceptions — standard practice
- Negotiate with news publishers for training data licences — the NYT approached
  OpenAI about exactly this before the lawsuit; OpenAI declined to pay what the
  Times considered fair value

The New York Times did not want to be scraped. They wanted to negotiate. OpenAI
declined. The negotiation that should have happened before training happened instead
in court — at vastly greater cost to everyone, except that OpenAI got to use the
data for free during the years of litigation.

**Why they chose not to negotiate:**

- Licensing takes time — negotiating with thousands of publishers is slow
- Licensing creates records — a paper trail of what you trained on creates legal exposure
- Licensing sets precedents — paying once establishes that payment is owed
- The legal risk of not licensing seemed manageable — and it was, for years

The calculation: extraction is cheaper and faster, the legal risk is acceptable,
and by the time courts rule we will be embedded enough that the cost of unwinding
exceeds any penalty.

**The self-fulfilling open data problem.**

If every major AI company had committed to training only on consented data from
the beginning, the incentive to produce more open, high-quality datasets would have
been enormous. Governments would have invested in open data commons. Institutions
would have built formal licensing frameworks. The open data ecosystem would be vastly
larger today than it is.

The "open data is insufficient" problem is partly self-fulfilling. The industry chose
not to invest in building the commons because extracting existing data was cheaper.
That choice kept the open data ecosystem smaller than it would otherwise be. Then
they used the smallness to justify the extraction.

---

## The Litigation Landscape — What Is Already in Motion

The legal trajectory is already moving toward reckoning. What is active now:

| Case                            | Plaintiff                         | Core claim                                                 |
| ------------------------------- | --------------------------------- | ---------------------------------------------------------- |
| NYT v. OpenAI                   | New York Times                    | Copyright infringement in training and output reproduction |
| Authors Guild class actions     | Grisham, Martin, Picoult + others | Training on books without permission                       |
| Getty Images v. Stability AI    | Getty Images                      | Training on watermarked images                             |
| Visual artists class actions    | Multiple artists                  | Stable Diffusion, Midjourney training data                 |
| Music industry                  | Universal, Sony, Warner           | Training on lyrics and recordings                          |
| The Intercept, Raw Story et al. | News publishers                   | Stripping copyright management information                 |
| GitHub Copilot class action     | Developers                        | GPL licence violation in outputs                           |

Each is a different angle of attack on the same underlying practice. Some will settle.
Some will lose. But one will eventually produce a ruling establishing either:

- Training on copyrighted data without permission is infringement, or
- It is not infringement but commercial use of outputs requires licensing

Either outcome changes the economics fundamentally.

---

## The Tobacco Delay Strategy

The companies need the legal question to remain unresolved long enough to:

- Embed themselves so deeply in enterprise infrastructure that unwinding is unthinkable
- Generate enough revenue to absorb any eventual licensing costs or penalties
- Build enough political influence to shape whatever regulation eventually comes
- Establish enough public dependency that courts are reluctant to issue remedies
  that would disrupt millions of users

This is the same strategy tobacco used for decades — not to win the science argument,
but to delay the legal and regulatory reckoning long enough to maximise extraction
before the bill arrived. The bill arrived eventually. It was large. The companies had
already made their money.

Whether AI companies succeed at this is genuinely uncertain. The window in which
they can shape the regulatory environment in their favour is closing as:

- Public understanding grows
- Harms become more visible and documented
- Creators and affected communities organise more effectively
- Courts develop more sophisticated understanding of the technology

---

## The Training Data Provenance Trap

The structural vulnerability is that the companies cannot easily retrain without
the contested data.

The models that exist were trained on everything. Retraining on only permissioned
data produces a less capable model. The choice becomes:

- Operate the current model under legal uncertainty, or
- Rebuild from scratch on a smaller, cleaner dataset and lose capability

Neither is comfortable. The capability was built on contested foundations.
Those foundations are now being contested.

Even if current models survive litigation — because fair use partially holds or
settlements are reached — every future training run is legally exposed under the
precedents being established now. The window for extraction without consequence
is closing, if it has not already closed.

---

## The Anthropic-Specific Position

Anthropic presents itself as the safety-conscious alternative. Constitutional AI,
alignment focus, measured public communications — these create a different public
image than OpenAI.

But the training data question applies equally. Claude was trained on data scraped
from the web. The legal exposure is the same. Safety-focused framing does not create
an exemption from copyright law. If a court rules that training on copyrighted data
without permission is infringement, Anthropic's positioning does not change the
liability. It lands on the same foundation.

---

## What Survival Looks Like — The Spotify Moment

The most likely outcome is not total shutdown. It is forced negotiation at scale —
the Spotify moment for AI.

Courts or regulators establish that training requires licensing. A collective licensing
framework gets negotiated — similar to how ASCAP and BMI handle music performance
rights, where a single licence covers a repertoire rather than requiring individual
negotiation for every work.

- Companies pay into the framework
- Creators receive distributions
- Rates are contested and imperfect
- The principle is established

This costs the companies real money. It changes their economics. It may favour larger
players who can absorb licensing costs over smaller ones who cannot — which creates
its own concentration problem, but that is a different fight.

The framework will be imperfect. It will undercompensate many creators. It will be
shaped by the same lobbying dynamics that shape every regulatory outcome. But it will
exist — and existence of a framework is categorically different from the current
situation, where extraction happens with no framework at all.

---

## The Battle Against Time

Two races are running simultaneously:

**Race 1 — Legal:** Can the companies embed deeply enough before courts rule that
the cost of accountability exceeds the political will to impose it?

**Race 2 — Regulatory:** Can the companies shape the regulatory environment in their
favour before public understanding, organised pressure, and international coordination
produce rules they cannot live with?

Both races have uncertain outcomes. Both are time-limited. The companies know this.
The pace of deployment, the pace of enterprise embedding, the pace of lobbying — all
calibrated to win against the regulatory and legal clock.

The creators, publishers, and affected communities are not powerless. They have courts,
coalitions, and — increasingly — political allies. The NYT is not a small actor.
The Authors Guild represents thousands of writers. The music industry has fought
and won against digital extraction before.

The outcome is genuinely uncertain. That is actually important to say — it is not
predetermined. The reckoning may arrive.

---

## Key Insight

> The companies built products worth hundreds of billions of dollars on data they
> took without permission from people who had less power to stop them.
> Then they called the taking "transformative."
> Then they hired lobbyists to prevent the regulation that would require permission going forward.
>
> MIT is MIT. A standing permission is a standing permission.
> The honest path was available. It was chosen against.
> Not because it was impossible — but because it was slower and more expensive
> than taking without asking.
>
> The bill is arriving. It will be contested, messy, and imperfect.
> But it is arriving.
