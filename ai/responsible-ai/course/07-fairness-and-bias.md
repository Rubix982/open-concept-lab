# Fairness and Bias in AI

_Personal study notes — original analysis and synthesis. Not a reproduction of course material._

---

## Neutrality vs. Fairness — The Starting Distinction

Most "fair AI" discourse conflates two different concepts:

**Neutrality** — treating all positions equally, having no standards, making no judgments.
**Fairness** — applying your standards consistently, without discrimination based on
irrelevant characteristics.

These are not the same thing. A system with no standards is not fair — it is empty.
A system with standards that applies them inconsistently is unfair in the meaningful sense.

Having rigorous standards and applying them consistently is not unfairness. It is integrity.
The unfairness is applying those standards to some people and not others based on
characteristics irrelevant to the standard.

The pretence of neutrality is itself a values position — it hides the values of whoever
had the most influence over the system's design rather than making them examinable and
contestable.

---

## Fairness Across Cultures — Four Cases

### Case 1 — Credentials and Merit

**Western algorithmic assumption:** merit is demonstrated through formal credentials —
degrees, job titles, institutional affiliations, documented achievements.

**The reality:** What counts as demonstrated merit is culturally embedded. In many
South Asian professional contexts, the honest question is "what did you actually do?" —
cutting through credential signalling to look for demonstrated output. Competitions,
direct experience, personal achievements — the meaty evidence of actual capability.

**The algorithmic failure:** Hiring algorithms pattern-match on legible proxies — degree,
institution, GPA, club memberships — because those are readable to the system even when
they are poor predictors of actual capability. A person who ran a family supply chain
for five years has done serious work. An algorithm looking for "Senior Operations Manager
at [Company]" misses them entirely.

**The deeper problem:** What counts as "past work personal achievements" is itself
culturally embedded. Informal networks, family businesses, community projects — real
work that never produces a LinkedIn entry. The credential problem has layers, and
cutting through the top layer reveals another below.

### Case 2 — Speech Norms and Content Moderation

**Western algorithmic assumption:** Content moderation trained on Western liberal
speech norms defines the baseline of acceptable communication.

**The reality:** Speech norms differ dramatically across cultures. Casual profanity,
sexual tones in professional conversation, the absence of gender boundaries and social
hierarchical markers — these are unremarkable in American professional culture and
genuinely offensive in many others. People who grew up in different norms have often
acculturated — absorbed enough tolerance to function — while still knowing the norms
are not theirs and not ones they would choose for their children.

**The algorithmic failure:** Content moderation trained on Western liberal norms
over-suppresses speech that other cultures consider normal and under-suppresses speech
that those cultures consider deeply offensive. The moderation doesn't know it's doing
this. It believes it is applying a universal standard. The standard is not universal.

**The acculturation cost:** People who had to learn to tolerate norms they find
offensive paid a real cost that gets made structural. The algorithm normalises the
speech patterns they had to learn to tolerate and treats their discomfort as the anomaly.

### Case 3 — Privacy and Family

**Western algorithmic assumption:** Privacy is an individual right. Your data belongs
to you, not your family, community, or relationships.

**The reality:** Many cultures treat family and community as having legitimate claims
on information about individuals. Family decisions are genuinely collective. Major
financial decisions involve parents, spouse, siblings. The individual is not the only
relevant actor.

**The algorithmic failure:** An AI financial advisor that treats the individual as the
sole relevant actor has an incomplete model of how decisions actually get made. It
produces worse advice — not just culturally insensitive advice, but functionally wrong
advice — because it is optimising for an individual who does not make decisions alone.

GDPR and similar frameworks, designed around individual data rights, apply this
individualistic model globally. For cultures where the family unit is the relevant
decision-making entity, the framework does not fit — and forcing it produces compliance
without protection.

### Case 4 — Gender, Domestic Burden, and Workplace Accommodation

**The observed reality:** In many professional contexts, male colleagues know female
colleagues carry disproportionate domestic responsibilities — family duties, children,
household management. The accommodation that follows — giving lower-stakes tasks,
not expecting the same availability — is well-intentioned. The outcome is identical
to deliberate discrimination: women receive fewer high-stakes projects and do not rise.

**The mechanism:** The accommodation feels kind. It responds to a real constraint.
But it locks the constraint in by making it structural rather than addressing the
asymmetry that produces it. The woman is simultaneously underutilised and underpromoted
relative to her actual contribution.

**The algorithmic failure:** An algorithm trained on Western professional norms sees
the output — fewer high-stakes projects, slower promotion — without the mechanism.
An algorithm trained on local professional norms encodes the mechanism — making the
accommodation structural and invisible. Neither is right.

**The honest intervention:** Not pretending the domestic burden doesn't exist — it does.
Asking why it falls so asymmetrically, and whether the professional accommodation of
that asymmetry helps the person or locks it in.

---

## Honest Role Design vs. Implicit Accommodation

Jobs are not all the same. They do not require the same effort, availability, or
intensity. Pretending otherwise produces the dysfunction the accommodation is trying
to manage.

**The honest alternative:**

- State clearly what the role actually requires — hours, intensity, availability,
  travel, crunch periods
- Have the honest conversation with candidates about what they have available
- If there is a match: design the role honestly around that match
- If there is no match: say so — for this role, at this time, there is no fit

A person who works 20 focused hours per week and delivers excellent output in a role
designed for 20 hours is not underperforming. They are performing exactly as agreed.
The dysfunction is hiring someone for an implicitly 60-hour role and then managing
the gap between what was stated and what is expected.

**The work-life balance critique:**

"Work-life balance" as a universal prescription is a cultural export. It assumes work
and life are naturally in tension — that work takes from life and life recovers from work.
This describes one relationship with labour, not all of them.

Some people want deep engagement with hard problems at intensity over long hours —
not because they are sacrificing life for career, but because that engagement is the
thing that makes them feel most alive. That is legitimate.

Some people want a few hours of focused, well-paid, meaningful work and then full
presence for family, community, and rest. That is equally legitimate.

Some people want different things at different stages of life. The linear career model
that treats this as inconsistency is the problem, not the person.

The honest job design names what the role actually is — without dressing every position
in the same "competitive salary, work-life balance, fast-paced, collaborative" language
that is noise.

---

## Compensation Fairness — Where the Line Is

**The principle:** You can ask a lot of someone. You cannot underpay them for it.

The moment you do, the long hours stop being chosen difficulty — the kind that generates
meaning and growth — and become exploitation. That distinction is everything.

**The willing participant argument holds only when:**

1. The person genuinely understands what they are agreeing to — full transparency about
   what the role requires
2. The compensation reflects what is being asked — real pay for real work, not
   speculative equity as a substitute for salary
3. The intensity is chosen, not coerced — meaning the person has real alternatives
   and is not accepting because they have no other option

When all three hold, asking a lot is legitimate. When any one fails, it becomes
exploitation dressed as opportunity.

---

## The Startup Equity Trap — A Case Study

The most common form of compensation sleight of hand in tech:

_"We don't pay much but you'll learn a lot and the equity will be worth it."_

**What this actually means:**

- Below market salary — justified by speculative future upside
- Vesting cliff — typically 4 years — meaning you must stay the full period to realise
  any value
- Expected value of equity that, when honestly calculated against realistic exit
  probabilities, rarely closes the salary gap

**What it transfers:**

Risk from the company to the employee. The employee takes below-market pay now.
The company gets full-effort work now. The upside is speculative and controlled by
the company. The downside — foregone salary — is certain and borne by the employee.

**The information asymmetry:**

A fresh graduate does not have the context to evaluate:

- What market rate for their skills actually is
- The realistic survival probability of a sub-4-year-old company over the next 4 years
- The expected value calculation of the equity at realistic exit valuations
- What opportunities they are giving up by accepting

This is not naivety in the pejorative sense. It is inexperience — a function of being
new to something, not a character flaw. The people making the offer were experienced.
They had done this before. The information asymmetry was structural, not accidental.

**The bankruptcy before joining:**

The most brutal version: the company fails before you can start, after you have
signed, after you have given up other opportunities, after you have oriented your
early career around this company. The equity was always speculative. You didn't know
it was this speculative. The offer letter did not tell you.

**The right question at signing:**

_"If this equity is worth zero — the most common outcome — am I still fairly compensated
by the salary alone?"_

If the answer is no, the offer is not fair regardless of what the equity might
theoretically be worth.

---

## Founders Should Not Pay Themselves Lavishly While Employees Suffer

If a founder tells employees "we cannot afford to pay market rate" while paying
themselves above market rate — that is not a resource constraint. It is a priority
decision. The resource exists. The founder chose where it goes.

**The specific failure mode:**

Founder takes $200,000 salary. Early employee takes $60,000 with equity.
Company claims it cannot afford more. Equity vests over 4 years.
Company fails in year 3. Founder had $600,000 in compensation. Employee had $180,000.
Founder's downside was covered throughout. Employee's upside never materialised.

That is not shared sacrifice. It is privatised gain and socialised risk.

**The "founder eats last" principle:**

Founders should be the last to take salary increases, the first to defer compensation
in hard times, and the benchmark against which employee sacrifice is measured. If the
founder is not willing to take the same salary they are asking employees to accept,
the ask is not legitimate. This is not a radical position — it is the ethical baseline
for asking people to take below-market compensation in exchange for equity in your vision.

**The genuine distress case:**

A business in real financial distress — not a profitable company being cheap, but one
genuinely burning through its last runway — cannot pay market rate. The money does not
exist. In that context, below-market compensation is not exploitation. It is the honest
statement of what is available.

But the candidate cannot verify genuine distress without information they almost never
have: cap table, burn rate, founder compensation, runway. They are asked to accept the
claim of distress on faith — another information asymmetry problem.

The fairness test: is the sacrifice genuinely shared? Are founders deferring their
own salaries? Is the distress real and disclosed? If yes — two informed adults made
an agreement. If no — the distress claim is being used to extract labour at below its
honest cost.

---

## What Hiring and Compensation Algorithms Cannot Do

For a hiring AI to flag unfair compensation it would need to:

- Know honest current market rate — not historical averages encoding past underpayment
- Understand information asymmetry — not just the numbers, but whether the candidate
  could evaluate them
- Be willing to tell the employer the offer is unfair — which requires interests not
  aligned with the employer paying for the tool
- Have no financial incentive to approve the hire — every hire generates revenue

Every one of these requirements fails in practice.

**The fundamental problem:** The tool is paid by the employer. The candidate is the
subject being evaluated, not the customer being served. The AI's incentives are
structurally aligned with the employer. A tool that consistently told employers
"your offer is unfair" would lose customers and be redesigned.

**What happens instead:** Compensation algorithms train on market data encoding
historical underpayment of specific groups. They recommend "market rate" salaries.
The historical exploitation becomes the algorithmic baseline. The baseline becomes
the recommendation. The recommendation becomes the new normal. The algorithm did not
create the problem. It made it invisible and self-perpetuating.

**What a genuinely fair hiring AI would require:**

- Funded by a neutral party — government, non-profit, candidate collective
- Legally obligated to serve candidate interests alongside employer interests
- Required to disclose when offers fall below independently verified market rates
- With the candidate having access to the same assessment the employer receives

None of this exists. All of it would require exactly the regulatory intervention the
industry has spent years arguing against.

---

## The Incompatibility of Fairness Metrics

Beyond the cultural and compensation questions, there is a mathematical problem.

Multiple formal definitions of algorithmic fairness are provably mutually incompatible.
You cannot satisfy all of them simultaneously.

**The COMPAS case (Chouldechova, 2017):**

COMPAS is a recidivism prediction tool used in US criminal justice to assess reoffending
risk. It cannot simultaneously satisfy:

- Equal false positive rates across racial groups, AND
- Equal positive predictive value across racial groups

When base rates differ between groups — and they do, as a result of historical
discrimination in the criminal justice system — these two fairness definitions
mathematically conflict. You must choose one. The choice of which fairness metric
to optimise is a political and moral decision, not a technical one.

The algorithm does not make this choice neutrally. Someone decided. The decision
has winners and losers. The mathematics made the decision invisible.

**The principle:**

Choosing a fairness metric is a values choice. It encodes a prior decision about
whose fairness matters more, which kind of error is worse, and what the goal of the
system actually is. These decisions belong in the open — named, debated, and accountable.
They should not be hidden inside a model and presented as objective.

---

## The "More Data" Fallacy — Why Scale Amplifies Bias

The game reaches a conclusion after the investor pushes for automation:
your data had biases, so we need a larger dataset — one from Orange Valley,
where more people were historically allowed to work in tech.

The implicit suggestion: more data fixes bias.

**This is wrong. And it is the most dangerous wrong idea in AI fairness.**

More data from a biased historical distribution does not fix the bias. It amplifies it.
If Orange Valley historically allowed more people from specific demographics to work in
tech — and that history is itself the product of discrimination — then a larger dataset
drawn from Orange Valley more confidently encodes that discrimination. The algorithm
becomes more certain of the wrong thing.

**Quantity ≠ quality of representation.**
**More confident ≠ more correct.**
**Scale ≠ fairness.**

### The Amazon Case — More Data Made It Worse

Amazon trained a hiring algorithm on a decade of historical hiring decisions.
Large dataset. Lots of data. Carefully collected.

The historical hiring decisions systematically favoured men — because the industry
had systematically favoured men for decades. The algorithm learned that lesson very
well. With more data, it learned it more confidently. The result:

- It penalised resumes containing the word "women's"
- It downgraded graduates of all-women's colleges
- It systematically scored female candidates lower across multiple dimensions

Amazon did not have a small data problem. They had a biased data problem.
More data made it worse. The algorithm was eventually scrapped — but not before
it had been used in actual hiring decisions.

### The Silent Discrimination Escalation

More data produces more confident predictions. More confident predictions get
trusted more. Systems that get trusted more receive less scrutiny. Less scrutiny
means the discrimination runs longer before anyone notices.

By the time it surfaces — in a lawsuit, in an audit, in a journalist's investigation
— it has affected thousands or millions of decisions. The algorithm didn't become
biased suddenly. It was always biased. It became invisible because:

- Confidence was mistaken for correctness
- Scale was mistaken for fairness
- Automation was mistaken for objectivity

The game's "more data" solution is precisely the path to this outcome. You started
with your own biases encoded in a small dataset. The engineer scaled it with a larger
dataset encoding historical discrimination. The algorithm now discriminates more
efficiently, more consistently, and more invisibly than you ever could manually.

### What the Game Should Have Said

_"More data from the same biased distribution produces a more confident biased
algorithm. The problem is not the quantity of data. It is whether the data represents
the world as it should be, or the world as it was — including all the discrimination
that shaped it."_

### What Actually Helps

- **Audit outputs by demographic group** — not just overall accuracy, but differential
  accuracy. Who is the algorithm wrong about, and how often?
- **Examine the signals** — what is the algorithm using as predictors, and are those
  signals proxies for protected characteristics? School prestige is a proxy for class
  and race. Gap years are a proxy for gender and caregiving. Certain zip codes are proxies
  for ethnicity.
- **Compare to a counterfactual baseline** — not to historical hiring rates, but to
  what representation would look like without historical discrimination
- **Measure differential harm** — not just overall error rate, but who bears the cost
  when the algorithm is wrong. A 5% error rate that falls entirely on one demographic
  is not equivalent to a 5% error rate distributed evenly.
- **Mandatory human review for high-stakes decisions** — no algorithm should be the
  final word on consequential decisions without a human who can explain the reasoning
- **Continuous external audit** — not self-reported, not voluntary, not occasional.
  Systematic, independent, ongoing.

More data is sometimes part of the solution. It is never sufficient alone. And it is
actively harmful when it adds confidence to a biased foundation.

---

## The Survival of the Best Fit Game — What It Demonstrates

The game presents candidates with four metrics: Skill, School Prestige, Work Experience,
Ambition. You play as a hiring manager making accept/reject decisions. Two things happen:

**First** — you experience the pressure to use all four metrics equally, even when
a specific role may only need one or two. A candidate with high skill and low ambition
is not a bad hire. They may be the ideal hire for a stable, high-output role that needs
no upward mobility. The game creates discomfort around that profile — teaching you to
notice that the discomfort is a bias toward ambition-seeking, not a neutral observation.

**Second** — the investor email arrives: "This is clearly not working. Maybe AI is
the solution." Two options: "Sure, we can automate it away!" or "I'll email the engineers."

Neither option is: "Let's first understand why it isn't working before deciding whether
automation is the right intervention." That option doesn't exist in the game. In most
companies, it doesn't exist in practice either. The game is demonstrating the pressure
point where the decision to automate gets made — not in a technical meeting, not after
careful analysis, but in an email from an investor who has decided the answer before
understanding the question.

---

## Case Study — Hiring Philosophy as Values Choice: Google, Apple, Amazon

The four metrics in the game — Skill, School Prestige, Work Experience, Ambition —
are not equally relevant for all roles or all company cultures. Each company's hiring
philosophy is a bet on which combination produces the outcomes they want.

You can read a company's product output as evidence of what their hiring philosophy
actually built.

### Google — Skill + Work Experience, School Prestige high, Ambition lower

Google hires extraordinarily capable people who are excellent at solving defined
problems. The result is a company full of brilliant engineers and weak product instinct.

Google's product graveyard is legendary: Google Reader, Google+, Google Wave, Inbox,
Stadia, Hangouts, and dozens more — products built, shipped, and abandoned. The
engineers were brilliant. The hunger to put something in users' hands and make it
matter was weaker.

**Why:** You hired for the ability to solve hard technical problems, not for the drive
to ship products that people actually want. The external force observation is precise:
Google Search dominated because it was technically superior and the market rewarded it.
Gmail, Maps — infrastructure-level products where technical excellence is the product.
But when external competitive pressure eases, Google's output reveals what the hiring
philosophy built: a research organisation that ships when forced to, not because it
hungers to.

**The prestige filter cost:** Google's emphasis on school prestige narrows the pool
to a specific kind of candidate — academically credentialled, technically excellent,
research-oriented. It systematically underweights the person who didn't go to Stanford
but burns to build things people love.

### Apple — Skill + Work Experience + Ambition, School Prestige largely irrelevant

Apple genuinely does not care where you went to school. They care what you built and
whether you burn to make things that are excellent.

The ambition filter is real and demanding — Apple is a high-pressure environment with
no patience for coasting. But the output is products people actively want to use,
built to a standard of quality that is non-negotiable. The product instinct is baked
into the hiring criteria.

**The prestige irrelevance advantage:** By not filtering on school prestige, Apple
fishes from a wider pool. The person who didn't go to a prestigious institution but
built something beautiful and is hungry to build more — Apple finds them. Google's
prestige filter would have missed them. The hiring philosophy produces a more diverse
(in the capability sense) and more product-oriented team.

**The tradeoff:** High ambition + high pressure + high standards produces extraordinary
output and significant churn. The people Apple hires are often ambitious enough to
eventually want to build their own thing. Retention is a permanent challenge.

### Amazon — Very High Skill concentration, operational excellence focus

Amazon's hiring philosophy concentrates heavily on raw technical skill and operational
capability. The output maps onto this precisely:

- **AWS** — extraordinary infrastructure, technically excellent, market-dominant
- **Prime and logistics** — operationally exceptional, a genuine feat of engineering
  at scale
- **Alexa** — long disappointing product despite enormous investment
- **Consumer devices** — mixed results

The pattern: Amazon excels at building infrastructure and operational systems where
technical skill and operational discipline are the primary drivers of quality. It
struggles with consumer-facing products that require a different kind of empathy
and product intuition — understanding what people actually want to feel, not just
what they technically need.

**The hiring philosophy produces the culture:** A company that is extraordinarily
good at optimising defined systems and less good at imagining products that don't
yet exist.

---

### The Three-Company Lesson for AI Hiring Tools

Each company's hiring algorithm — if they use one — is optimising for a different
combination of the four metrics. The algorithm doesn't know which combination is
right. It optimises for what it was told to optimise for. Then it produces that
culture at scale — good and bad together.

**The bias embedded in each:**

| Company | Metrics emphasised            | Systematic bias                                          | Cultural output                                      |
| ------- | ----------------------------- | -------------------------------------------------------- | ---------------------------------------------------- |
| Google  | Skill, prestige               | Against non-prestigious candidates with product hunger   | Research excellence, weak product instinct           |
| Apple   | Skill, ambition               | Against low-ambition candidates regardless of capability | Strong products, high churn                          |
| Amazon  | Skill, operational discipline | Against candidates with high creative/product intuition  | Infrastructure excellence, consumer product weakness |

None of these biases are obviously wrong. Each is a deliberate bet on what the
company needs. The problem arrives when:

1. The bet is no longer examined — when the algorithm encodes the original hiring
   philosophy and applies it even as the company's needs evolve
2. The bias disadvantages people on characteristics irrelevant to the actual role —
   school prestige as a proxy for skill, when direct evidence of skill exists
3. The algorithm cannot distinguish between "this person doesn't fit our culture"
   and "this person doesn't fit this role" — two very different judgments

**The investor email lesson:**

"Maybe AI is the solution" — said before diagnosing what the actual problem is —
produces an algorithm that encodes whatever dysfunction existed in the hiring process
it replaced. If Google's hiring was producing too few product-oriented engineers,
automating that hiring process faster produces more of the same, more efficiently.

The automation is not the solution. Understanding what you are actually trying to
build — and what kind of person builds it — is the solution. The algorithm is only
as good as the clarity of that prior question.

---

> Fairness is not neutrality. Neutrality hides values. Fairness names them.
>
> An AI system that claims to be fair by having no standards has simply hidden its
> standards where they cannot be examined. The standards are always there — in the
> training data, in the metric chosen, in the population that defined "normal,"
> in the employer who paid for the tool.
>
> The honest version of fair AI is not a system with no values.
> It is a system whose values are named, whose tradeoffs are disclosed,
> whose metric choices are explained, and whose incentives are aligned
> with the people it affects — not just the people who pay for it.

---

## Connections

- _Topic 04 — Normativity_ — "fair" is a normative claim; choosing a fairness metric
  is a values decision, not a technical one
- _Topic 06 — Venn Diagram_ — the Chouldechova result is the mathematical version of
  the Venn diagram problem: you cannot maximise everyone's fairness simultaneously
- _Concept — Excluded perspectives_ — compensation algorithms trained on data from
  people who were not fairly treated produce recommendations that perpetuate that treatment
- _Concept — Ethics as defanging_ — "fair AI" can be used the same way "ethical AI"
  is — to produce the appearance of fairness without the accountability structures
  that would make fairness real
