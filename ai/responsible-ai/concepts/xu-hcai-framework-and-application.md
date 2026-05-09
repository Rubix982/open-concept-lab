# Wei Xu's HCAI Framework — Detailed Notes and Application

*Personal study notes — synthesis of Wei Xu, "Toward Human-Centered AI: A Perspective
from Human-Computer Interaction," ACM Interactions, July-August 2019.*

---

## Context and Author

**Wei Xu** — Researcher at Intel Corporation, Chair of the Intel IT Cross-Domain HCI/UX
Technical Working Group. PhD in psychology (HCI-focused), MS in computer science, Miami
University. Research interests: HCI, cognitive engineering, aviation human factors.

Written in 2019 at the moment the third wave of AI was cresting — right as deep learning
had proven itself at scale but before serious questions about HCAI had become mainstream.
The article is a call to the HCI community to proactively enter AI R&D rather than waiting
to be invited.

---

## The Three Waves of AI — A Historical Framework

Xu provides a comparative table of the three waves of AI development. The pattern matters:
the first two waves failed not just because the technology was immature, but because they
never asked what humans actually needed from it.

| Wave | Period | Technology | Human Needs | Focus | Characteristics |
|---|---|---|---|---|---|
| **First** | 1950s–1970s | Early symbolism, connectionism, expert systems, knowledge inference | Not satisfied | Technological solutions | Academia driven |
| **Second** | 1980s–1990s | Statistical models, neural networks for pattern recognition, expert systems, speech recognition | Not satisfied | Technological solutions | Academia driven |
| **Third** | 2006– | Breakthroughs in deep learning, speech recognition, pattern recognition, big data, high-performance computing | Starting to provide useful and real problem-solving solutions | Integrated solutions: ethical design + technological enhancement + human factors design | Technological enhancement and application + a human-centred approach |

**The key insight:** The first two waves failed not only because they lacked mature
technologies but also because they left human needs unsatisfied. The third wave is
the first one where the question of human need is being asked at all — which is why
HCAI only becomes urgent now, even though AI has existed for 70 years.

> "The third wave of AI can be characterized by technological enhancement and
> application + a human-centered approach."

---

## The PC Parallel — History Repeating

Xu draws a precise historical analogy. When PCs emerged in the 1980s, they were designed
by programmers for programmers. The interface was command-line. The mental model was
technical. The assumption was that users would adapt to the machine.

It took the entire HCI field a decade to correct this. User-Centred Design (UCD) emerged
as the discipline that forced the field to reckon with actual human use, comprehension,
and need. The result was the visual interfaces everyone takes for granted today.

**His argument:** AI is at the same stage PCs were in 1983. Designed by ML engineers for
ML engineers. "Much current AI research focuses only on technical aspects, and therefore
AI solutions are facing similar problems." The HCI community's job is to do for AI what
it did for PCs — force the discipline to reckon with actual human use and need.

> "A new version of UCD practice, HAI, has again fallen on the shoulders of
> HCI professionals, promising many great opportunities for the HCI community."

---

## The Extended HAI Framework — Three Components

Xu proposes a framework with three main components. He argues that human factors design
is not fully considered in today's HCAI research agenda — the conversation is dominated
by ethics and technology, with the human factors dimension underrepresented.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│            ETHICALLY ALIGNED DESIGN                │
│    Avoids discrimination, maintains fairness        │
│    and justice, does not replace humans             │
│                                                     │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│  TECHNOLOGY          │   HUMAN FACTORS DESIGN       │
│  ENHANCEMENT         │                              │
│                      │   Explainable AI             │
│  Fully reflects      │   Comprehensible AI          │
│  human intelligence  │   Useful AI                  │
│                      │   Usable AI                  │
│                      │                              │
└──────────────────────┴──────────────────────────────┘
```

The three components are synergistic. For example: ethical AI design emphasises human
capability enhancement rather than replacement, which requires HCI design to ensure
that human operators can quickly and effectively take over control of an intelligent
system in an emergency — so that fatal accidents like autonomous vehicle crashes can
be avoided.

### Component 1 — Ethically Aligned Design

- Creates AI solutions that avoid discrimination
- Maintains fairness and justice
- Does not replace humans

AI engineers typically lack formal training in applying ethics to design in their
engineering courses and tend to view ethical decision-making as another form of
technical problem-solving. The HCI community can leverage their interdisciplinary
skills to assess ethics-related issues — not just as a philosophical exercise but
from a broader sociotechnical systems perspective.

### Component 2 — Technology Enhancement

- Reflects the depth characterised by human intelligence
- Makes AI more like human intelligence in the fullness of its reasoning

HCI can contribute here by following a human-centred ML approach: defining UX criteria,
testing and optimising ML training data and algorithms iteratively, and avoiding extreme
algorithmic bias by keeping humans involved in the training pipeline.

### Component 3 — Human Factors Design

This is the most neglected component and the one Xu focuses on most. It has four
sub-requirements:

**Explainable AI (XAI)**
**Comprehensible AI**
**Useful AI**
**Usable AI**

---

## The Black Box Problem

ML and its learning processes are opaque. Neural networks for pattern recognition in
deep learning are especially so. This "black-box phenomenon" causes users to question
decisions:

- Why did you do this?
- Why is this the result?
- When did you succeed or fail?
- When can I trust you?

This reflexive skepticism directly affects users' trust and decision-making efficiency,
thus affecting adoption. The black-box effect makes AI solutions not explainable and
not comprehensible to users — across financial decisions, legal decisions, medical
diagnoses, industrial monitoring, security screening, employment recruitment, legal
judgment, university admissions, smart homes, autonomous vehicles.

---

## Explainable AI vs. Comprehensible AI — A Critical Distinction

Xu draws a distinction that most XAI research misses entirely.

**Explainable AI (XAI):**
Enables users to understand the algorithm and parameters used. The DARPA XAI five-year
program organised 13 universities and research institutes primarily to develop new or
improved explainable ML algorithms. It also investigates explanation UIs with advanced
HCI techniques (UI visualisation, conversational UI) and evaluates psychological
explanation theories.

**The problem with current XAI approaches:**
- Previous research used primarily two methods: visualisation of ML processes and
  explainable ML algorithms
- These approaches may be biased in explaining how ML algorithms work
- They rely mainly on abstract visualisation methods or statistical algorithms
- This may further increase complexity rather than reduce it
- Most importantly: **the XAI version created for data scientists is incomprehensible
  to most non-expert users**

**Comprehensible AI:**
Goes further than explainability. According to UCD principles, a design must provide
comprehensible AI based on **target users' needs and capabilities** — specifically their
knowledge level and mental models.

> "The ultimate goal of XAI should be to ensure that target users can understand the
> outputs, thus helping them improve their decision-making efficiency."

**The critical insight:** There is no guarantee that the target users of an XAI system
will be able to understand it just because it produces explanations. The explanation
must fit the user's existing mental model — which varies by expertise, domain, context,
and task. This is fundamentally a cognitive science and HCI problem, not an ML problem.

**What HCI professionals can contribute to XAI/comprehensible AI:**
1. Effective HCI design for explanation UIs — visualisation models, adaptive UI,
   natural UI dialogue technologies
2. Application of psychological theories of explanation — these exist in the literature
   but have not been incorporated into XAI research driven by AI professionals
3. Rigorous user-involved behavioural experimental methods to validate proposed
   explanations — this was overlooked in most previous AI-driven research

---

## Useful AI

Xu defines useful AI specifically:

> "Useful AI is defined as an AI solution that can provide the functions required to
> satisfy target users' needs in the valid usage scenarios of their work and life."

One of the main reasons third-wave AI is penetrating people's work and life is that it
can now solve practical problems with the right usage scenarios and UX — something not
achieved in past waves. Some AI applications were very expensive and failed due to a
lack of use value.

**What HCI professionals can contribute:**
- Identifying usage scenarios based on HCI methods — ethnographic studies and
  contextual inquiries
- Mining user needs, behavioural patterns, and usage scenarios
- Using AI and big data to model real-time user behaviours
- Building digital user personas to identify potential user needs and real-world
  usage scenarios

---

## Usable AI

Xu defines usable AI as:

> "An AI solution that is easy to learn and use via optimal UX created by effective
> HCI design."

### Challenge 1 — Moving Beyond Mere Interaction

With the addition of learning capabilities in AI-based machine intelligence, the
human-machine relationship has shifted:

```
Human-Computer Interaction
        ↓
Human-Machine Integration
        ↓
Human-Machine Teaming
```

Humans and machines are teammates and collaborative partners now. The dynamic
cooperation between two cognitive agents — with enhanced capability on the machine
side as it learns over time — brings added complexity to HCI design.

Questions requiring systematic HCI research:
- Dynamic functional allocation and task assignments between human and machine
- Dynamic goal setting
- Allocation of decision-making power between the two over time

### Challenge 2 — HCI Methods Were Built for Non-Intelligent Systems

Current HCI methods were originally created for non-intelligent solutions. They assume
the system has no learning ability to change its behaviour — the system is predictable.
Intelligent systems behave differently: their behaviour develops over time.

**The AI-First Design Approach (Xu's proposal):**

During UI prototyping, instead of rushing to focus on visual and interactive design
as usual, HCI designers should:

1. **Consider the AI-first approach first** — carry out dynamic functional allocation
   between human and machine
2. **Prioritise machine intelligence functions** — smart search, real-time user
   behaviour, contextual information, voice input — to reduce repetitive human activities
3. **Design more intuitive UIs** that leverage what the AI does well rather than
   designing around human tasks and bolting AI on afterward

### Challenge 3 — Verification and Validation

Traditional software verification assumes the system has no learning ability and its
behaviour is predictable. AI behaviour develops over time.

Verification evaluation of AI solutions requires collaboration between AI software
engineers and HCI professionals — a combination of:
- Software validation methods
- User-involved UX validation methods

**Wizard of Oz (WOZ) prototyping:**
Early UX evaluation of low-fidelity intelligent design prototypes requires alternatives
like WOZ design prototypes — where a human simulates the AI's intelligent behaviour —
to validate the learning and intelligent behaviours of AI before they are built. This
allows UX testing of AI behaviour without the ML system being operational yet.

### Challenge 4 — No HCI Design Standards for AI

Current AI-related standards focus primarily on ethical design issues (e.g., IEEE
guidelines). There are currently **no specific HCI design standards** for guiding
AI solutions. The HCI community needs to develop these.

---

## The Human-Machine Teaming Model

The shift from interaction to teaming is not just terminological. In the teaming model:

- **Tasks shift dynamically** — between human and machine depending on who is better
  positioned at that moment in the task
- **Decision-making authority is not fixed** — it moves based on context, expertise,
  and system confidence
- **The machine learns over time** — so the relationship itself evolves; what was
  appropriate to delegate at t=0 may not be appropriate at t=100
- **Trust is calibrated, not binary** — not "do I trust this system?" but "in what
  conditions, for what decisions, to what degree do I trust this system?"

This requires HCI research on:
- When and how to transfer control between human and machine
- How to communicate machine confidence levels in ways humans can interpret
- How to maintain appropriate human oversight as systems become more capable
- How to avoid both over-reliance (human defers when they should not) and
  under-reliance (human overrides when they should not)

---

## Application to a Persistent Knowledge Base with AI

Xu's framework applied to the specific challenge of building a researcher-facing
AI knowledge infrastructure:

### Step 1 — Define the User Before Building Anything

Not "researchers" generically. Specific users with specific contexts:

- A PhD student at the end of a literature review who has 200 papers open and
  cannot see the connections
- A professor building a new course who needs to know what the field has said
  about a specific claim
- A non-expert who read one paper and wants to understand what challenges it
- An early career researcher trying to find where their own work fits in the landscape

Each has a different mental model, a different definition of "useful," and a different
bar for what counts as a comprehensible explanation.

### Step 2 — Dynamic Functional Allocation

What should the AI do versus what should the human do?

**The human brings:**
- Judgment about relevance and significance
- Domain expertise to recognise when something is wrong or missing
- The ability to evaluate whether a claimed connection is meaningful
- Context about what question they are actually trying to answer

**The AI brings:**
- Breadth across thousands of papers no human has time to read
- Pattern recognition across claims at scale
- Surfacing connections the human would not have had time to find
- Consistency — applying the same criteria to all papers rather than privileging
  familiar ones

Neither should do the other's job. The interface design should make the allocation
visible — the user should always know what the AI produced and what was left to them.

### Step 3 — Wizard of Oz Before Building

Before the knowledge graph exists:

- Create a mock interface
- Show actual researchers what the output might look like
- Simulate AI-produced connections manually
- Watch where comprehension breaks down
- Watch what they trust and what they question
- Note what they wish it did differently

This is faster and cheaper than building the system and discovering the UX is wrong.
The researcher outreach and consent mechanism already designed — showing researchers
how their work appears in the graph and asking for corrections — is simultaneously:
- Ethical consent
- Wizard of Oz UX testing
- Quality validation

This is the right design. It was arrived at independently of Xu's framework but maps
precisely onto it.

### Step 4 — Comprehensible Explanations for the Right Audience

The system can find a real connection between two papers. But if the explanation of
why those papers are connected is not comprehensible to the person looking at it,
the accuracy is useless.

For a PhD student: "These two papers both address the same causal mechanism from
different experimental contexts — Paper A establishes it in vitro, Paper B challenges
it in vivo."

For a non-expert: "These papers disagree about whether X causes Y. Here is what each
one says and why they reach different conclusions."

The same connection. Entirely different explanations. Both need to be correct and
both need to fit the mental model of the person receiving them.

### Step 5 — Iterative UX Criteria Before Training

Following the AI-first approach:

1. Define the UX criteria with actual users — what does a useful output look like?
   What makes an explanation trustworthy? What makes a connection feel spurious?
2. Use those criteria to guide training data selection and annotation
3. Test and optimise iteratively — not once at the end
4. Validate with behavioural experiments — watch people use it, measure comprehension,
   not just accuracy
5. Update both the model and the interface based on what you observe

### Step 6 — The Teaming Model for Knowledge Work

The knowledge infrastructure should be designed as a **collaborative partner**, not
a search engine and not an oracle:

- The researcher brings the question and the judgment
- The system brings the breadth and the pattern recognition
- The interface makes the collaboration visible — showing what the system found,
  why it thinks it is relevant, how confident it is, and what it might have missed
- The researcher can override, correct, and teach — and the system should be designed
  to learn from those corrections

Trust is built incrementally through repeated interactions where the system is right,
is honest when it is uncertain, and accepts correction gracefully. That is not a
technical specification. It is a relationship design specification.

---

## Summary — What Xu Adds to the Framework

| Xu's contribution | Application to knowledge base |
|---|---|
| Three-wave historical frame | The knowledge base is part of the third wave — it must address human needs, not just technical capability |
| Black box problem | Every connection the system surfaces needs an explanation the target user can understand |
| XAI vs comprehensible AI | Accuracy alone is insufficient — comprehensibility must be designed for the specific user |
| AI-first UCD | Define UX criteria and allocate human/machine tasks before building the ML system |
| Wizard of Oz prototyping | Simulate outputs with real researchers before building; researcher outreach IS the WOZ test |
| Human-machine teaming | The researcher and the system are partners; the interface should make the partnership visible |
| Iterative UX validation | Consent mechanism + output review is the ongoing validation loop |
| No standards yet | The knowledge infrastructure can contribute to developing what those standards look like |

---

## Key Insight

> The first two waves of AI failed not only because the technology wasn't ready,
> but because they never asked what humans needed.
>
> The third wave asks — but the asking is dominated by ML engineers asking on behalf
> of users rather than with them. Comprehensibility is not the same as explainability.
> Usefulness is not the same as accuracy. Usability requires knowing who is using it.
>
> The right knowledge infrastructure is not built and then tested for UX.
> It is built from the UX criteria outward — with the users who will actually
> use it, at every stage, as partners rather than as validators at the end.
