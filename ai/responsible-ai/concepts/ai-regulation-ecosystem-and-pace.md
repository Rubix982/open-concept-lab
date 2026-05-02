# AI Regulation — The Ecosystem Framework and the Question of Pace

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Ecosystem Framework — What Is Actually Being Regulated?

"AI regulation" is too broad to be useful as a framing. The systems under discussion —
computer vision, predictive systems, semi-autonomous military systems, generative models,
therapeutic chatbots, facial recognition, autonomous vehicles — have overlapping but
distinct harms, benefits, and technical characteristics.

Regulation requires specificity. And that specificity extends beyond the systems themselves
to the entire ecosystem that produces and sustains them. Five layers, each with distinct
regulatory questions:

---

### Layer 1 — Compute

The computational resources, microprocessors, and hardware that AI systems run on.

- Who has the capacity to manufacture and provide compute?
- Where do the raw materials come from — and under what labour and environmental conditions?
- Should sales and development of compute be restricted?
- When does this become a national security or geopolitical matter?

**Already being regulated** — through export controls on advanced semiconductors (CHIPS Act,
US export restrictions on NVIDIA chips to China). This is the least contested layer because
governments already understand it in national security terms. The governance conversation
is happening, just not in public.

---

### Layer 2 — Data Centres

The large facilities containing the hardware AI runs on. Currently require enormous amounts
of land, electricity, and water.

- How should their location and construction be governed?
- How should power grid usage be managed — especially as AI energy demand grows?
- How should environmental effects — water use, heat generation, carbon footprint — be regulated?

**Straightforward regulatory territory.** Environmental impact assessment, land use planning,
water rights, grid access — these are existing regulatory frameworks that apply directly.
No new conceptual apparatus needed. Just political will to apply existing tools to a new
context.

---

### Layer 3 — Data

The material used to train and test machine learning systems.

- From what sources can training data be acquired?
- How should it be acknowledged and compensated — especially creative work, journalism,
  personal data?
- How should the people who clean and filter data be acknowledged and compensated?
  (Largely workers in the Global South, paid fractional wages for traumatising work)
- Should model builders be required to reveal their data sources and processing methods?

**Where the most immediate and tractable harm lives.** The data layer is where consent
was bypassed at scale, where labour was extracted without compensation, where surveillance
infrastructure was quietly built. This is also where existing law — copyright, privacy,
labour — has the most direct applicability. Start here.

---

### Layer 4 — Models

The software that produces outputs based on training.

- Should small models face different scrutiny than large ones?
- Should models be open or closed — and what does "open" actually mean?
- Should outputs be accurate, explainable, and minimally biased — and what do those terms mean?
- Since developers cannot fully control who uses their models, how is accountability
  for downstream use apportioned?

**The hardest layer conceptually.** The accountability question — developer vs. deployer vs.
user — does not have a clean answer. The pharmaceutical analogy breaks down here: drug
manufacturers can track who prescribes and how. Model developers cannot. New frameworks
are genuinely needed, not just applications of existing law.

---

### Layer 5 — Agents

AI-based software that uses other AI systems to accomplish tasks on a user's behalf.
The most urgent frontier.

- What restrictions should be placed on the kinds of actions agents can undertake?
- Who is liable when an agent causes harm acting on a user's behalf?

**The least governed and fastest moving layer.** Agents can send emails, make purchases,
execute code, interact with other systems — all on behalf of a user who may not fully
understand what they authorised. Liability frameworks for autonomous action on behalf
of another person do not currently exist in a form adequate to this.

---

## You Don't Have to Regulate All Five at Once

The "regulate AI" or "don't regulate AI" binary misses the point. Different layers are
at different stages of harm visibility, regulatory readiness, and technical clarity.

**Start where harm is clearest and tools most available:**
- Data — now. Consent, compensation, transparency. Existing law, requires extension.
- Agents — now. Liability frameworks before deployment scales further.

**Apply existing frameworks where they fit:**
- Data centres — environmental and land use law, applied directly.
- Compute — export controls and national security frameworks, already in use.

**Develop new frameworks for:**
- Model accountability — genuinely novel problem requiring genuinely new approaches.

This is not slowing down AI. It is governing the layers where governance is most needed
and most tractable, while leaving space for development to continue where it can.

---

## The Question of Pace — Is the World Going to Die Without AI?

No.

And the fact that this question sounds almost absurd when stated plainly is itself
revealing. The urgency narrative — move fast, falling behind is catastrophic, delay is
dangerous — is produced and funded by the people who benefit from moving fast.

The majority of humanity is managing food, water, shelter, family, and community largely
without frontier AI, and largely fine. The urgency is real for:
- Companies racing for market position
- Investors with time-horizoned bets
- Governments concerned about strategic advantage

It is not real for the person in Lagos, Karachi, Manila, or rural Mississippi whose life
will be shaped by these systems but who had no say in their development.

---

## Slowing Down Is Not a Cost — It Is a Values Choice

The "speed is necessary" argument assumes:
1. Benefits of AI deployment accrue broadly
2. Costs of delay are shared equally

Neither is true.

Benefits accrue primarily to the companies deploying, the investors funding, and early
adopters with resources. Costs of harmful deployment — algorithmic discrimination, job
displacement, surveillance, manipulation — fall disproportionately on people with less
power to resist or recover.

**Slowing down to get it right costs the people racing.**
**Getting it wrong costs everyone else.**

The world does not need to move at Silicon Valley's pace. Silicon Valley's pace serves
Silicon Valley's interests. The rest of the world is allowed to say: we will take what
is useful, reject what is harmful, and set our own timeline.

---

## The Growth Rate Question — Does the Economy Need 20% Growth to Survive?

No. And this is one of the most important questions to ask clearly.

The obsession with growth rate as the measure of economic health is a normative choice —
made in a specific historical context, treated as neutral ever since. GDP growth does
not measure:

- Whether people have enough time
- Whether communities are intact
- Whether people feel secure
- Whether the environment is stable
- Whether gains are distributed
- Whether people are healthy
- Whether work is meaningful

**A society growing at 2%** where everyone has healthcare, housing, time for family,
and meaningful work is objectively better than **a society growing at 20%** where half
the population is precarious, anxious, and one medical bill from catastrophe.

The number does not capture the reality. The number was never designed to capture the
reality. It was designed to measure market activity — which is one component of a good
life, not its definition.

**The evidence from slower-growth, higher-wellbeing societies:**

| Country | GDP growth (avg) | Healthcare | Housing security | Life satisfaction |
|---|---|---|---|---|
| Denmark | ~1-2% | Universal | High | Top 5 globally |
| Japan | ~0.5-1% | Universal | High | High |
| Germany | ~1-2% | Universal | Moderate-high | High |
| USA | ~2-3% | Partial | Low-moderate | Declining |

The US grows faster and delivers less security to more of its population. The growth
is real. The distribution is the problem. And AI, deployed into this context without
accountability, accelerates every existing dynamic — more productivity, more displacement,
more concentration, worse distribution.

**Is anyone dying of starvation if the economy grows at 2% vs 20%?**

No. People are dying of starvation — and homelessness, and untreated illness, and
despair — in economies growing at 3% right now. The growth rate is not the variable.
The distribution is the variable. And that is a political choice, not a technical one.

---

## The Security Carve-Out — An Honest Position

Governments are pursuing more sophisticated AI systems than are publicly available.
This is not conspiracy — it is standard state behaviour in any domain with strategic
implications. Military and intelligence AI programmes operate outside public governance
frameworks in every major power.

This is understandable. States have security obligations that require capabilities
their adversaries cannot anticipate. Transparency about those capabilities would
undermine the security they are designed to provide.

But this is precisely the argument for strong civilian regulation — not to slow down
state programmes, which will proceed regardless, but to ensure that civilian AI
deployment happens with accountability. The gap between what states can do and what
civilians can demand accountability for should not become permanent and unbridgeable.

Strong civilian governance does not constrain military AI development. It creates a
legitimate public framework within which the benefits of AI can be deployed responsibly
and the harms can be identified and addressed. The two tracks — state security and
civilian accountability — can coexist. They already do in nuclear, pharmaceutical,
and aviation domains.

---

## The Neoliberal Context — Why This Matters Now

In a different economic context — one where productivity gains were shared, where
displaced workers were genuinely supported, where the state had meaningful redistributive
capacity — the "move fast and fix problems later" argument would be more defensible.

In the actual context of the last 40-50 years, where every previous wave of automation
produced concentrated gains and diffuse costs, trusting the same system to handle AI
differently requires ignoring the entire track record.

The world does not need to accept the pace, the priorities, or the governance framework
of the actors currently driving AI development. It is absolutely fine — desirable, even —
to slow down, to ask the hard questions, to build the safeguards before scaling the
systems. The cost of that slowdown falls on the people racing. The cost of not doing it
falls on everyone else.

> The question is not "can we afford to slow down?"
> The question is "who pays when we don't?"

---

## Key Insight

> The urgency of AI deployment is real for specific actors with specific interests.
> It is not a fact about the world.
>
> A society that reaches advanced AI with proper safeguards, fair distribution,
> and genuine accountability will be better than one that arrived faster without them.
> The destination matters more than the speed.
> The people being asked to bear the cost of speed are not the people setting the pace.
