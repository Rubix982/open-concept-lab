# Guidelines for Human-AI Interaction — Microsoft Research (2019)

_Detailed research notes on: Amershi et al., "Guidelines for Human-AI Interaction,"
CHI 2019, May 4–9, Glasgow, Scotland. Microsoft Research + University of Washington._

_Authors: Saleema Amershi, Dan Weld, Mihaela Vorvoreanu, Adam Fourney, Besmira Nushi,
Penny Collisson, Jina Suh, Shamsi Iqbal, Paul N. Bennett, Kori Inkpen, Jaime Teevan,
Ruth Kikin-Gil, and Eric Horvitz._

---

## Why This Paper Exists

AI-infused systems violate established usability guidelines of traditional UI design.
The most fundamental: **consistency**. Traditional UX principle — minimise unexpected
changes, maintain predictable behaviours. AI components are inherently inconsistent:

- They operate on probabilistic behaviours based on nuances of tasks and settings
- They change via learning over time
- They react differently depending on conditions not recognised as distinct by end users
  (lighting, noise, session history)
- They respond differently to the same input across time (autocompletion suggesting
  different words after language model updates)
- They behave differently from one user to the next (personalised search results)

Inconsistent and unpredictable behaviours confuse users, erode confidence, and lead to
abandonment. Errors are common, rendering error prevention nearly impossible.

**The problem the paper solves:** Over 20 years of HCI research had proposed guidelines
for AI-infused systems, but scattered across disciplines (AAAI, UbiComp, RecSys, SIGIR,
HRI, KDD) and rarely presented as explicit, reusable design guidelines. This paper
synthesises them into 18 concrete, validated, generally applicable guidelines.

---

## Methodology — Four Phases

This paper is unusually rigorous for a design guidelines paper. Understanding the
methodology matters because it validates the guidelines' credibility.

### Phase 1 — Consolidating Guidelines

Sources:

- Industry AI products and internal company guidelines (Microsoft + external)
- Recent public articles and editorials about AI design
- Relevant scholarly papers (20+ years of HCI literature)

Result: **168 potential AI design guidelines** collected.

Process: Three researchers conducted asynchronous affinity diagramming, clustering
guidelines into related concepts. Resulted in 35 concepts, filtered down to 20 by
removing:

- Too vague to design for directly (e.g., "build trust")
- Too specific to one AI scenario (e.g., "establish that the bot is not human")
- Not AI-specific (e.g., "display output effectively")

20 concepts organised into 4 categories by interaction phase.

### Phase 2 — Modified Heuristic Evaluation (Internal)

11 team members evaluated 13 AI-infused products against the initial 20 guidelines
over one hour each. Products included: email filtering, navigation, e-commerce
recommendations, photo organizers, design assistance, research assistance, social
network feeds, web search, image search.

Key outcomes:

- Identified confusing overlaps between guidelines (e.g., G9 and G17 confused)
- Removed guidelines that produced no identifiable applications (e.g., "explore vs.
  exploit in moderation" — important at modelling level, not observable at interface)
- Reformatted all guidelines to: start with a verb, 3-10 words, accompanied by a
  one-sentence clarification, no conjunctions (forcing splits where needed)
- Reduced to **18 guidelines**

### Phase 3 — User Study with 49 HCI Practitioners

**Scale:** 49 participants (29F, 18M, 2 preferred not to answer), ages 18-55.
19 researchers, 12 designers, 11 HCI/design interns from universities worldwide,
7 others. Experience: 1-4 years (23), 5-9 years (14), 10-14 years (9), 20+ (2).
4 countries, 3 continents.

**Products tested:** 20 products across 10 categories, 2-3 participants per product:

| Category              | Feature tested                    |
| --------------------- | --------------------------------- |
| E-commerce (Web)      | Recommendations                   |
| Navigation (Mobile)   | Route planning                    |
| Music Recommenders    | Recommendations                   |
| Activity Trackers     | Walking detection and step count  |
| Autocomplete (Mobile) | Autocomplete                      |
| Social Networks       | Feed filtering                    |
| Email (Web)           | Importance filtering              |
| Voice Assistants      | Creating a reminder with due date |
| Photo Organizers      | Album suggestions                 |
| Web Search            | Search                            |

**Process:** Each participant assessed one product for applications and violations of
all 18 guidelines. Rated each example on a 5-point scale from "clearly violated" to
"clearly applied." Also rated guideline clarity from "very confusing" to "very clear."

**Results:** 785 examples identified across 20 products:

- 313 applications
- 277 violations
- 89 neutral (midpoint)
- 106 "does not apply"

### Phase 4 — Expert Evaluation of Revisions

11 UX experts reviewed 9 revised guidelines from Phase 3, choosing between old and
new versions. Experts preferred revised versions for all but Guideline 15.

---

## The 18 Guidelines — Full Detailed Treatment

Organised by interaction phase. For each guideline: definition, why it matters,
documented violations in real products, and implications.

---

### INITIALLY — Before the User Starts

#### G1: Make Clear What the System Can Do

_Help the user understand what the AI system is capable of doing._

**Why it matters:** Users who do not know what a system can do cannot use it effectively
and cannot calibrate their expectations. Overestimation leads to frustrated abandonment
when the system fails at things it was never capable of. Underestimation means users
never discover capabilities that would serve them.

**Documented applications:**

- Activity Tracker: "Displays all the metrics that it tracks and explains how."
- Social Network: "[Product] communicates to users that it will evaluate and provide
  potential people to follow based on your interests."

**Documented violations:**

- Social Network: "I cannot even tell what this news feed can/will show."
- Photo Organizer: "We know the AI is able to detect and associate an image with a
  category, but the user does not know all the categories available."
- Voice Assistant: "When invoked verbally, I was not given any indication of what
  commands I could request."

**Key tension:** Full disclosure of capabilities can be overwhelming. The design
challenge is progressive disclosure — surface what is relevant to the current context
without burying the user in a capabilities list.

---

#### G2: Make Clear How Well the System Can Do What It Can Do

_Help the user understand how often the AI system may make mistakes._

**Why it matters:** This is the calibration guideline. Users cannot make good decisions
about when to trust, verify, or override an AI system if they do not understand its
error profile. A system that is 95% accurate on average may be 60% accurate in edge
cases that matter most. Users need to know when to be skeptical.

**Documented applications:**

- Music Recommender: "A little bit of hedging language: 'we think you'll like'."
- Email: Help page sets expectation that the system "will start working right away,
  but will get better with use, making it clear that mistakes will happen."

**Documented violations:**

- Navigation: "No indication of accuracy of time estimates or how conditions may be
  changing. No measure of how well AI predictions matched the result."
- Voice Assistant: "No expectation of quality is set."
- Social Network: "For some ads, there is a 'suggested post' indicator. For the rest
  of the posts, no clue about quality."

**Key insight from this study:** G1 and G2 were the most confused with each other
(13 misinterpreted instances). G1 is about _what_ the system can do. G2 is about
_how well_ it does it. G11 is about _why_ it did what it did. These are distinct
questions requiring distinct design responses.

**Connection to Xu's comprehensible AI:** G2 is the design-level implementation of
the comprehensibility requirement. Hedging language ("we think you'll like") is a
simple mechanism. More sophisticated implementations include: confidence bars,
accuracy disclosure in help text, adaptive uncertainty signals.

---

### DURING INTERACTION

#### G3: Time Services Based on Context

_Time when to act or interrupt based on the user's current task and environment._

**Why it matters:** Proactive AI that interrupts at the wrong moment is worse than
no AI at all. The automation complacency problem (from our critique of Xu) is partly
produced by poorly timed interruptions — users learn to dismiss them reflexively,
including the ones that matter. Appropriate timing requires the system to model the
user's current state, not just their historical patterns.

**Documented applications:**

- Navigation: "Provides timely route guidance because the map updates regularly with
  actual location."
- Autocomplete: "Suggestions are always present when you might need them — whenever
  the keyboard is up."

**Documented violations:**

- Activity Tracker: "Notifies when I approach my goal, hit my goal, or exceed it.
  The timing is not clear. Feels pretty arbitrary."
- Email: "Sending notifications for unimportant messages — something most people
  will not want as an interruption."

**Important finding:** G3 had one of the highest "does not apply" rates. Many products
only respond to explicit user requests — "pull" interactions where the user initiates.
G3 is most relevant for "push" interactions where the system proactively acts. This
guideline matters most for notification systems, ambient assistants, and proactive
recommendation engines.

---

#### G4: Show Contextually Relevant Information

_Display information relevant to the user's current task and environment._

**Why it matters:** AI systems that show information relevant to past behaviour
rather than present context are noise sources. The recommendation system that keeps
surfacing tennis balls after you've already bought them fails exactly this guideline.

**Documented applications:**

- E-commerce: "Assumes I'm about to buy a gaming console and shows accessories."
- Web Search: "Searching a movie title returns show times near my location for
  today's date."

**Documented violations:**

- E-commerce: "I start looking at paper towels, but get recommendations for tennis
  balls (recently viewed). Does not take into account what I am currently looking for."
- Email: "What goes into the tabs is the same all the time. Does not change based
  on context — for example, emails related to the meeting I'm attending."

**Distinction from G13 (learn from user behaviour):** G4 is about _current context_
(this task, this moment, this environment). G13 is about _historical preferences_
(what this user has liked over time). Both matter. They require different signals and
different mechanisms.

---

#### G5: Match Relevant Social Norms

_Ensure the experience is delivered in a way that users would expect, given their
social and cultural context._

**Why it matters:** AI systems embed cultural assumptions in their interaction patterns.
A voice assistant that uses a corporate formal register with a user expecting casual
conversation violates this guideline. A navigation app that sends "time to stand up"
reminders during a meeting violates this guideline. The social context is not just
aesthetic — it affects whether the system feels intrusive, appropriate, or respectful.

**Documented applications:**

- Photo Organizer: "Recognizes people's pets and uses the verbiage 'important cats
  and dogs', understanding that pets are important to users."
- Voice Assistant: "Uses a semi-formal voice — spells out 'okay' and asks further
  questions."

**Documented violations:**

- Activity Tracker: "Provides a reminder to stand up without understanding my social
  context (in a meeting, having lunch). Just says 'time to stand!' no matter what."
- Email: "Does not follow social norms of a workplace. A norm is to pay attention
  to your manager, but it isn't clear the system prioritises messages from direct
  managers."
- Voice Assistant: "Does not match expected conversation norms. Requires very specific
  command syntax rather than interpreting conversational language."

**Critical finding:** G5 had one of the highest "does not apply" rates AND the lowest
clarity ratings. Multiple participants said: "Hard for a designer to implement, because
it requires them to think outside of their own social context" and "Doesn't apply to me
but to potential other people." This is the excluded perspectives problem as a research
finding. The evaluators in this study could not identify violations of social norms they
did not themselves hold. Diverse evaluators are not optional for this guideline — they
are structurally necessary.

---

#### G6: Mitigate Social Biases

_Ensure the AI system's language and behaviours do not reinforce undesirable and
unfair stereotypes and biases._

**Why it matters:** AI systems trained on historical data encode historical biases.
When surfaced in user-facing products, these biases are presented with the authority
of algorithmic objectivity — making them more insidious than explicit human bias,
which can at least be challenged directly.

**Documented applications:**

- E-commerce: "Does not unfairly assume gender biases. A search for tools or diapers
  provides specific recommendations without gender-biased associations."
- Autocomplete: "Clearly suggests both genders [him, her] without bias."

**Documented violations:**

- Voice Assistant default female voice: "Reinforces stereotypical gender roles that
  presume a secretary or receptionist is female."
- Autocomplete: "Suggests names correctly for Western-sounding names but falls short
  for ethnic-sounding names."
- Navigation: "No way to set average walking speed. Assumes users to be healthy."
- Photo Organizer: "I typed in 'black' in the search bar and it returned me and my
  niece. It saw a black face and used that as its frame of reference — returned all
  pictures of me and my family, not images of other black spaces in an environment."

**Critical finding:** G6, like G5, had both the highest "does not apply" rates and
the lowest clarity ratings. Participants said: "Hard to measure. Who defines what is
undesirable and unfair?" Some participants firmly believed guidelines did not apply
to products where other participants found clear violations in the same products.

**The paper's conclusion:** "A diverse set of evaluators may be necessary to effectively
recognise or apply these guidelines in practice. Alternatively, designers may need
specific training or tools to recognise social norms and biases."

This is the excluded perspectives problem made empirically visible. The bias that
was invisible to evaluators in this study was invisible because they were not the
people it affected. This is not an HCI problem that better tools solve alone. It is
a representation problem — who is in the room when the evaluation happens.

---

### WHEN WRONG — Error Recovery

#### G7: Support Efficient Invocation

_Make it easy to invoke or request the AI system's services when needed._

**Why it matters:** AI services that cannot be reliably invoked at the moment they
are needed are worthless at that moment. The value of an AI capability is partly
a function of its accessibility when relevant.

**Documented violations:**

- Navigation: "Remembers where you parked your car. But if it fails, there is no
  way to invoke the capability manually."
- E-commerce: "Many products I searched for did not show the 'Customers also
  considered' AI feature. No way to invoke it manually."

---

#### G8: Support Efficient Dismissal

_Make it easy to dismiss or ignore undesired AI system services._

**Why it matters:** The corollary to G7. A system that cannot be easily dismissed
when its output is wrong or unwanted trains users to ignore all its output — including
when it is correct. Efficient dismissal preserves the signal-to-noise ratio that makes
the system worth using.

**Documented violations:**

- Autocomplete: "No dismiss button. Can only dismiss by dismissing the whole keyboard."
- Navigation: "Suggested locations based on calendar entries cannot be removed from
  suggestions."

---

#### G9: Support Efficient Correction

_Make it easy to edit, refine, or recover when the AI system is wrong._

**Why it matters:** AI systems make mistakes. The cost of those mistakes to users
depends partly on how hard it is to recover from them. A system that makes
recoverable mistakes gracefully is far more usable than one that makes the same
mistakes but with high recovery cost.

**Documented applications:**

- Navigation: "If wrong about where I parked, provides easy way to edit by dragging
  on the map."
- Web Search: "Automatically corrects spelling errors but gives option to return to
  original query."
- Voice Assistant: "Once reminder processed, ability to edit visible with 'Tap to Edit'."

**Documented violations:**

- E-commerce: "Already bought the items in my recommendation list. No option to
  remove them."
- Activity Tracker: "No way for the user to edit the number of steps. Can delete
  the data point altogether but cannot manually input or change it."
- Web Search: "Edits to AI interpretation of query (SEA to 'Sea of') not possible."

---

#### G10: Scope Services When in Doubt

_Engage in disambiguation or gracefully degrade the AI system's services when
uncertain about a user's goals._

**Why it matters:** An AI system that is uncertain should surface that uncertainty
to the user rather than picking an answer and presenting it with false confidence.
The system that shows 3-4 suggestions rather than auto-completing directly is
applying this guideline. The system that says "I had trouble hearing you" rather
than silently failing is applying this guideline.

**Documented applications:**

- Autocomplete: "Usually provides 3-4 suggestions instead of directly autocompleting."
- Voice Assistant: "If I didn't respond or spoke quietly, let me know they had trouble
  hearing me."

**Documented violations:**

- Navigation: "When restaurant not found, fails to recognise the broader user goal
  of finding food and does not suggest alternatives."
- Email: "No indication if the system is unsure. Does not ask for assistance. Not
  clear how it decides what to do with unclear messages."

**Important finding:** G10 had zero instances reported for the two social networks
tested. Some participants noted it was difficult to assess without knowledge of the
underlying AI algorithms or without extended use. This guideline is harder to observe
in a single evaluation session — which is a design and evaluation challenge.

---

#### G11: Make Clear Why the System Did What It Did

_Enable the user to access an explanation of why the AI system behaved as it did._

**Why it matters:** This is the explainability guideline — the design-level
implementation of the XAI requirement. Without explanation, users cannot:

- Determine whether to trust a specific output
- Understand when the system is likely to be wrong
- Provide meaningful correction
- Build an accurate mental model of how the system works

**Documented applications:**

- E-commerce: "Clicking 'Why recommended' explains why they recommended that item."
- Navigation: "The route chosen was based on the Fastest Route, shown in subtext."

**Documented violations:**

- Music Recommender: "No information about why the recommended songs/artists are chosen."
- Email: "No indication of why a message is classified as it is. Could be content,
  sender, or any other reason. No details available."
- E-commerce: "I have no idea why this is being shown to me. Is it trying to sell
  me stuff I do not need?"

**Critical finding:** G11 had one of the **highest numbers of violations** despite
the large volume of active research in AI explanations and interpretability. Also had
one of the fewest "does not apply" responses — participants could _imagine_ opportunities
for explanations but were often unable to obtain them.

This is the most important gap in the study. The HCI and ML research communities have
invested enormously in XAI. Products are not implementing it. The research is not
reaching practice. And when explanation is provided, it is often inadequate:

- "This does list out things which affect it, but they don't explain it in a clear manner.
  Do each of these affect it equally?"
- "It always says the suggested route is the 'best route' but it doesn't give criteria
  for why that route is best."

**Connection to Xu's comprehensible AI distinction:** This validates Xu's point
precisely. XAI research produces explanations. Products fail to implement them.
When they do implement them, the explanations are not comprehensible to the target
user. All three failure modes are visible in the violations above.

**One documented reason products do not implement G11:** Financial and business reasons.
"Adversarial (gaming) behaviour by Web page authors would be exacerbated if search
engines explained their ranking." Explainability can enable people to game the system.
This is a genuine design tension, not just negligence.

---

### OVER TIME — Long-term Interaction

#### G12: Remember Recent Interactions

_Maintain short term memory and allow the user to make efficient references
to that memory._

**Why it matters:** Context in conversation and task-completion accumulates. A system
that forgets what was just said or done forces the user to constantly re-establish
context — adding cognitive load and making the system feel unintelligent.

**Documented applications:**

- Navigation: "Opening the app shows a list of recent destinations."
- Web Search: "Remembers the context of certain queries. After a search surfacing
  Benjamin Bratt, understands 'who is he married to'."

**Documented violations:**

- Social Network: "No indication of 'what you have read'."
- Voice Assistant: "Set the same reminder twice to drink water at 4:15 and it had
  no idea."

**Distinction from G13:** G12 is _short-term memory_ — recent interactions in the
current session or very recent past. G13 is _long-term learning_ — behavioural
patterns that develop over weeks and months. Both matter. They require different
technical architectures and different design affordances.

---

#### G13: Learn from User Behaviour

_Personalise the user's experience by learning from their actions over time._

**Why it matters:** A system that does not learn from the user's demonstrated
preferences is not intelligent in any meaningful sense. It applies the same model
to everyone regardless of what it has observed about this specific person.

**Documented violations:**

- Web Search: "I search for recipes all the time and only ever click on 4 sources.
  But rarely surfaces recipes from those sites."
- Activity Tracker: "Notifies/nudges users to achieve goals but no change in behaviour
  even though my patterns have changed."
- Navigation: "If you don't take the suggested route because you don't want stop-and-go
  traffic, it never learns."

**Important observation:** Learning from user behaviour (G13) can conflict with
updating and adapting cautiously (G14). The system that learns quickly is the system
that changes its behaviour quickly — which can be disruptive. This is a documented
tension in the paper.

---

#### G14: Update and Adapt Cautiously

_Limit disruptive changes when updating and adapting the AI system's behaviours._

**Why it matters:** A system that learns too aggressively changes its behaviour in
ways that are jarring and confusing. The user builds a mental model of how the system
works. Rapid behaviour changes invalidate that mental model without notice.

**Documented applications:**

- Music Recommender: "Once we select a song they update the immediate song list below
  but keep the above one constant."
- Web Search: "After clicking and returning from a result, the order of search results
  didn't change."

**Documented violations:**

- E-commerce: "When I accidentally browse one item, my entire recommendation list
  changes to things relevant to that item. The change is really jarring, especially
  when the browsing is a result of a curious moment or an accident."
- Social Network: "Pulling down can sometimes be triggered unintentionally, causing
  posts to disappear."

---

#### G15: Encourage Granular Feedback

_Enable the user to provide feedback indicating their preferences during regular
interaction with the AI system._

**Why it matters:** AI systems that learn only from implicit signals (what the user
clicked, how long they read, what they bought) are learning from proxies for preference.
Direct feedback — like/dislike, mark as important, flag as spam — provides a richer
and more reliable signal. Making this feedback easy and contextually available improves
the model faster and gives the user appropriate agency.

**Documented applications:**

- Social Network: "Allows user to 'Hide an Ad,' then solicits feedback to improve
  relevancy of future ads."
- Music Recommender: "Love/dislike buttons are prominent and easily accessible."
- Email: "The user can directly mark something as important, when the AI hadn't."

**Documented violations:**

- Voice Assistant: "Once the task was performed, no additional ability to customise
  or give feedback on satisfaction."
- Navigation: "Does not let the user tweak routes based on prior behaviour."

---

#### G16: Convey the Consequences of User Actions

_Immediately update or convey how user actions will impact future behaviours
of the AI system._

**Why it matters:** Users need to understand what they are teaching the system when
they take actions. Clicking "not interested" on a recommendation, hiding an ad,
marking an email as important — each of these has consequences for the system's
future behaviour. If users cannot see those consequences, they cannot make informed
decisions about how to interact with the system.

**Documented applications:**

- Music Recommender: "Tapping like/dislike results in immediate popups informing
  that the user will receive more/fewer recommendations like it."
- Social Network: "Communicates that hiding an Ad will adjust the relevancy of
  future ads."

**Documented violations:**

- Social Network: "You can unfollow or like or interact but how that affects you
  isn't clear. It just sorta happens."
- Photo Organizer: "No messages to confirm that the system will learn from my dismiss
  or save action."

---

#### G17: Provide Global Controls

_Allow the user to globally customise what the AI system monitors and
how it behaves._

**Why it matters:** Instance-level feedback (G15) lets users correct individual
decisions. Global controls let users set standing preferences that govern the system's
overall behaviour. Without global controls, users are trapped correcting the same
type of error repeatedly.

**Documented applications:**

- Photo Organizer: "Allows users to turn on location history so the AI can group
  photos by where you have been."
- Navigation: "Options to adjust preferences for how I want to get directions."

**Documented violations:**

- Email: "The only option is to turn the system on or off. It otherwise applies to
  all messages at all times. Not clear what data it monitors."
- Music Recommender: "Does not provide a mechanism to turn off tracking of listening
  data."

**Important finding:** G17 had a high number of violations. Combined with G15, this
suggests that most AI products give users very limited ability to shape what the system
learns and how it behaves. This is the data sovereignty problem — users generate the
data that trains the system, and have minimal control over how that data is used
or what the system learns from it.

---

#### G18: Notify Users About Changes

_Inform the user when the AI system adds or updates its capabilities._

**Why it matters:** AI systems change over time — model updates, new capabilities,
changed behaviours. Users who built a mental model of how the system works have that
model invalidated by silent updates. This creates confusion and erodes trust.

**Documented violations:**

- Music Recommender: "The algorithm feels like it constantly updates, with a slightly
  different feel to my recommendations every week. No explanation of what has changed."
- Social Network: "It's always a mystery when the product updates the ranking algorithm."
- Web Search: "No notifications when the search algorithm changes or new capabilities
  are added. Updates are only noticeable with use."

---

## Summary — What Is Most Violated and Why It Matters

### Most violated guidelines (by violation count relative to applications):

**G11 — Make clear why the system did what it did**
Most violated despite most research investment. Products either do not explain or
explain inadequately. This is the XAI-to-practice gap made visible.

**G2 — Make clear how well the system can do what it can do**
Products routinely omit uncertainty signals. Users cannot calibrate trust without
error profile information.

**G17 — Provide global controls**
Users cannot meaningfully customise AI behaviour at a system level. Data they
generate trains models they cannot control.

### Most "does not apply" (lowest universal relevance):

**G5 and G6 — Social norms and social biases**
Not irrelevant — but invisible to evaluators who do not experience the norms being
violated or the biases being encoded. This is the excluded perspectives finding.

### The Critical Research Finding

G5 and G6 had the lowest clarity ratings AND participants disagreed about whether
violations existed in the same products. This is not a problem of unclear guidelines.
It is a problem of who is doing the evaluation.

**The paper's own conclusion:**

> "A diverse set of evaluators may be necessary to effectively recognise or apply
> these guidelines in practice."

But the study itself recruited participants via "HCI and design distribution lists at
a large software company" — a narrow population. The finding about diversity is
produced by a study that lacked it. This is the meta-irony of the paper: the guideline
most requiring diverse evaluators was tested by the least diverse evaluator pool.

---

## The Tensions the Paper Documents

The guidelines are not always compatible. The paper identifies several documented
tensions:

**G13 (learn from user behaviour) vs. G14 (update and adapt cautiously)**
Learning quickly means changing quickly. Changing quickly is disruptive.
Design must find the right rate of adaptation for each context.

**G11 (explain why) vs. business interests**
Explaining ranking algorithms enables gaming. There are legitimate reasons
not to explain, which the paper acknowledges. This tension cannot be resolved
by design alone — it requires policy decisions about when explanation is
mandatory regardless of business consequences.

**G16 (convey consequences of user actions) vs. G13 (learn from user behaviour)**
If the system uses a complex deep model to achieve high performance, conveying
the exact consequences of user actions may be technically impossible. High
performance and transparent consequence may be in conflict at the model level.

---

## Application to the Knowledge Infrastructure

These 18 guidelines are a design specification for the researcher-facing knowledge base.
Applied directly:

| Guideline                                   | Application                                                                                                                                      |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| G1 — Make clear what system can do          | Explicitly state what the graph can find and what it cannot — it finds textual co-occurrence and claim connections, not truth                    |
| G2 — Make clear how well                    | Show confidence levels on every connection. Never present a connection as a fact — it is an inference with a confidence score                    |
| G3 — Time services based on context         | Surface connections that are relevant to what the researcher is currently reading, not just historically interesting                             |
| G4 — Show contextually relevant information | When a researcher is reading Paper A, surface the papers that speak to the same claim, not all connected papers                                  |
| G5 — Match social norms                     | Academic communication norms differ from consumer norms. The interface should feel like a scholarly tool, not a recommendation engine            |
| G6 — Mitigate social biases                 | The dataset geography problem is G6. Papers from non-Western institutions should not be systematically underweighted                             |
| G7 — Support efficient invocation           | Any connection or claim should be discoverable by explicit search, not only by browsing                                                          |
| G8 — Support efficient dismissal            | Researchers must be able to flag connections as spurious and suppress them from their view                                                       |
| G9 — Support efficient correction           | The researcher outreach mechanism IS G9 — making correction easy and relational                                                                  |
| G10 — Scope services when in doubt          | When the system is uncertain about a connection, show alternatives rather than picking one. Show "possibly related" vs "strongly related"        |
| G11 — Make clear why                        | For every connection surfaced: which text, which claim, which co-occurrence produced it. The explanation must be accessible on demand            |
| G12 — Remember recent interactions          | Within a research session, remember what the researcher has looked at and weight subsequent suggestions accordingly                              |
| G13 — Learn from user behaviour             | Over time, learn which types of connections this researcher finds valuable and which they dismiss                                                |
| G14 — Update and adapt cautiously           | When the graph updates (new papers added, claims revised), notify researchers whose work is affected rather than silently changing what they see |
| G15 — Encourage granular feedback           | Every connection should have a rating mechanism. Every claim attribution should be correctable                                                   |
| G16 — Convey consequences                   | When a researcher rates a connection, show them how that rating will affect what they see and what others see                                    |
| G17 — Provide global controls               | Researchers should be able to set standing preferences: which fields, which time periods, which connection types to emphasise                    |
| G18 — Notify users about changes            | When new papers are added that connect to a researcher's work, or when their work is newly connected to others', notify them                     |

---

## Key Insight

> These 18 guidelines are the design specification for building AI systems that
> treat users as agents rather than subjects.
>
> The most violated guideline (G11 — explain why) is the one that requires the
> most technical work. The most problematic guidelines (G5, G6 — social norms and
> biases) are the ones that require the most human diversity in evaluation.
>
> Both gaps point at the same structural problem: AI products are built by small,
> homogeneous teams optimising for measurable outcomes, not for the full range of
> people who will use them. The guidelines name what is missing. Implementing them
> requires changing who is in the room — at design time, at evaluation time, and
> at deployment time.
