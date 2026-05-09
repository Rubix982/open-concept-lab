# Goodhart's Law, the Prestige Trap, and the FANG Arc

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## Goodhart's Law

> *"When a measure becomes a target, it ceases to be a good measure."*

Originally stated by British economist Charles Goodhart about monetary policy:
when central banks target a specific monetary indicator, actors optimise for
that indicator rather than the underlying economic health it was supposed to
measure. The indicator loses its predictive value the moment it becomes the goal.

Applies universally — to education, hiring, research metrics, corporate KPIs,
and AI benchmarks.

**The mechanism:**

1. A measure is identified that correlates with a desirable outcome
2. The measure becomes the target
3. People optimise for the measure rather than the outcome
4. The correlation between measure and outcome breaks down
5. The measure no longer measures what it was designed to measure
6. But it persists — because the infrastructure built around it has its own momentum

---

## Campbell's Law — The Social Science Version

> *"The more any quantitative social indicator is used for social decision-making,
> the more subject it will be to corruption pressures and the more apt it will be
> to distort and corrupt the social processes it is intended to monitor."*

— Donald Campbell, 1979

Where Goodhart describes the mechanism, Campbell describes the corruption.
The indicator does not just become less useful — it actively distorts the
behaviour it was meant to measure. People do not just optimise for the measure;
they game it, and the gaming damages the underlying process.

**Applied to CS hiring:**

- CS degree: designed to measure technical competence → became a prestige signal
  → universities expanded enrollment for tuition revenue → degree now represents
  a heterogeneous population and provides weak signal about individual capability
- LeetCode score: designed to measure algorithmic thinking → became the hiring
  target → an entire industry of LeetCode coaching emerged → now measures
  LeetCode preparation, not software engineering capability
- Interview round count: designed to reduce false positives → became a status
  signal → companies added rounds to signal rigour → now measures interview
  endurance, not job performance

---

## The Prestige Trap

When something becomes prestigious, it attracts people motivated by the
prestige rather than the thing itself. Those people change what the thing is.

**The sequence:**

1. A field or institution does genuinely excellent, novel work
2. The outcomes become visible — high compensation, interesting problems, status
3. Prestige-motivated people enter to capture those outcomes
4. The volume of prestige-motivated entrants grows
5. The field adapts its filtering to handle the volume
6. The filters select for filter-passing ability, not the original capability
7. The original people leave or get drowned out
8. The prestige hollows out the substance
9. The prestige signal follows the substance downward — but with a lag

**Historical examples:**

- Investment banking — 1980s-90s: genuine financial innovation; 2000s: prestige
  capture; 2008: hollowed out, prestige intact until it wasn't
- Management consulting — 1990s-2000s: genuine strategic value; 2010s: prestige
  capture; now: expensive PowerPoint production with diminishing returns
- Academic philosophy — genuine intellectual inquiry → prestige signal for
  elite education → professionalization → now largely self-referential publishing
- AI research — 2012-2018: genuine frontier work; 2019-present: prestige capture
  accelerating; benchmark optimisation replacing genuine understanding

---

## The FANG Arc — A Precise Case Study

### Early 2010s FANG — What It Actually Was

Google 2008, Facebook 2010, Amazon 2012: companies solving genuinely novel
problems at scales nobody had solved before.

- Distributed systems at unprecedented scale — no textbook existed
- Search infrastructure that had never been built
- Real-time social graph computation for hundreds of millions of users
- Engineers were hired because the problems were hard and the people who
  could solve them were rare

The measure (FANG engineer) and the target (solving novel hard problems)
were aligned. Compensation was high because genuine scarcity commanded it.
The batch size was 30-40 — small enough for relationship-based hiring,
individual vouching, direct placement.

### Mid-2010s — The Prestige Trap Closing

- Compensation became public knowledge
- Status became visible and aspirational
- CS enrollment expanded massively — 30-40 to 445 in 27 years
- LeetCode founded 2015 — exactly when the prestige trap was closing
- Interview process industrialised — the filter needed to handle the volume

### Current FANG — What It Actually Is

- Large, stable, process-driven engineering organisations
- Most work: maintaining and incrementally improving existing systems
- Significant bureaucracy, slower decision-making, internal political complexity
- Interview process optimised to filter volume, not identify exceptional people
- Compensation still high but gap with well-funded startups has narrowed
- Prestige signal now self-referential — impressive to people who don't know
  the inside; known as a credential more than an experience

**The signal that "FANG engineer" sent in 2010 had collapsed by 2020.**
The population it represents changed too much. The degree is the same.
The credential is not.

---

## The CS Credential Bubble — 30-40 to 445

**What 30-40 CS graduates in 1995 meant:**

- Genuine selection pressure — CS was difficult to enter, limited awareness,
  mathematical prerequisites filtered heavily
- People chose CS because they were drawn to computing, not primarily for salary
- Faculty-to-student ratio allowed relationship-based teaching and direct placement
- Industry could absorb the cohort with individual attention and relationship hiring
- The degree carried specific information: this person can do this specific thing

**What 445 CS graduates in 2022 means:**

- CS became the prestige degree — high salaries, visible success stories,
  strong parental encouragement — attracting people primarily motivated by outcome
- Universities expanded capacity because tuition revenue followed enrollment
- Faculty ratios deteriorated — instruction quality diluted at scale
- Industry cannot absorb the cohort without filtering mechanisms
- The degree carries weak information: this person completed a CS program

**The quality observation:**

Not that 445 individuals are less capable than 30. Some in the 445 are more
capable than anyone in the original cohort. The issue is:

- Average capability lower because selection pressure lower
- Variance higher — exceptional people and genuinely mismatched people in the
  same cohort, with the same credential
- Signalling value of the degree collapsed — too heterogeneous to carry
  specific information

**The structural injustice:**

Your brother's degree and your degree have the same name. They are not the
same credential. Not because of anything either of you did — because the
institution changed what it was selecting for and how many it was selecting,
driven by tuition revenue incentives with no accountability for what the
credential would mean at the receiving end.

The cost of this collapse is borne by the candidates — not by the universities
that expanded enrollment, not by the companies that built elaborate filtering
mechanisms in response, not by the policy makers who let it happen.

---

## The Shirky Principle

> *"Institutions will try to preserve the problem to which they are the solution."*

— Clay Shirky

FANG hiring processes preserve the filtering problem that justifies their
existence. If companies hired through relationships, demonstrated work, and
research output — they would not need the enormous recruiting machinery,
the LeetCode interview infrastructure, the multiple round systems.

The machinery justifies itself by existing. The problem it was built to solve
is now partly produced by the machinery itself.

Universities preserve the credential problem. The credential bubble justifies
expanded enrollment. Expanded enrollment produces more credential inflation.
More inflation justifies the credential as a signal. The signal loses value.
Universities expand to compensate. The loop continues.

---

## Where Goodhart's Law Meets AI Hiring

Every metric in the AI hiring pipeline is subject to Goodhart's Law:

- **Resume keywords** → candidates optimise for ATS keyword matching →
  keywords no longer measure fit, they measure keyword awareness
- **GitHub activity** → candidates generate commit activity → commits no longer
  measure genuine open source contribution
- **LeetCode rating** → candidates grind LeetCode → rating measures grinding
  capacity, not engineering judgment
- **Years of experience** → HR requires X years for entry level → years no longer
  measure experience, they measure time elapsed
- **School prestige** → school becomes the proxy → prestige no longer measures
  capability, it measures access to prestigious institutions

The algorithm learns from historical hiring data that optimised for all of these
measures. It encodes the Goodhart corruption. It scales it. It presents it with
a confidence score. The corruption becomes infrastructure.

---

## What Compounds Your Specific Kind of Thinking

The FANG filter is not looking for someone who:

- Thinks in frameworks across disciplines
- Follows threads beyond what was assigned
- Has strong opinions about what is worth building and why
- Connects technical capability to philosophical and social context
- Builds for reasons, not just for outputs

LeetCode does not measure this. Behavioural interview rubrics do not capture it.
Volume-handling filters cannot find it in a pool of 445.

The environments where this kind of thinking compounds:

- **Research environments** — Bau Lab, interpretability research, any lab where
  the question is genuinely open and the answer matters
- **Early-stage companies** — small enough that a founder or senior engineer
  reviews applications personally, where the filter is a conversation not a pipeline
- **Non-profits with genuine mission** — where the work is selected for what it
  is, not what it signals
- **Independent projects** — where the output speaks for itself before any filter
  gets involved

The filter is broken. The honest response is not to optimise for the filter.
It is to build the relationships and the record that make the filter irrelevant.

---

## Key Insight

> When a measure becomes a target, it ceases to be a good measure.
> The CS degree became a target. It ceased to measure CS capability.
> The LeetCode score became a target. It ceased to measure engineering judgment.
> The FANG credential became a target. It ceased to measure the thing
> that made early FANG worth joining.
>
> The prestige hollows out the substance.
> The substance leaves.
> The prestige follows — but slowly, and with a lag long enough
> for another generation to optimise for the hollow signal.
>
> Find the work before it becomes the signal.
> That is where the substance still lives.
