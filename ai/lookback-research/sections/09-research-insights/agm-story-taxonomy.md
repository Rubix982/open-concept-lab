# AGM Story Taxonomy for Lookback Compliance Testing

_Date: 2026-07-04_
_Status: design — no implementation yet_
_Related: agm-compliance-for-lookback.md_

---

## What the Existing Stories Test

The bigtom dataset and `story_templates.json` share one structural pattern:

```
[t=1] Character forms belief about (object, state)
[t=2] Unobserved event changes actual state
[?]   Question: what does the character believe?
```

This tests a single thing: **does the model track that the character's belief
was frozen at t=1 when they did not observe the t=2 event?**

That is the Sally-Anne false-belief task. It is a necessary condition for AGM
compliance but nowhere near sufficient. The bigtom stories are all vacuously
identical in structure — they vary setting, character name, and object, but
the epistemic pattern is always the same.

**What the existing templates test:**

| Property | Tested? | How |
|---|---|---|
| Basic false belief | Yes | Unobserved swap, binary Q |
| Observation gating | Yes | Visibility conditions in template variants |
| Binary state discrimination | Yes | (state_1 or state_2) |
| Iterated revision | No | — |
| Non-contradicting addition (vacuity) | No | — |
| Conflict / merging | No | — |
| Contraction | No | — |
| Minimal change (only targeted belief changes) | No | — |
| Temporal depth (old beliefs persist) | No | — |
| Closure (derived beliefs preserved) | No | — |
| Source reliability / priority | No | — |

---

## The Seven Missing Story Types

Each type targets one AGM property that the existing corpus cannot test.
Stories are given as concrete narratives; a template schema follows each.

---

### Type 1 — Iterated Revision

**AGM property:** SUCCESS applied twice in sequence (Darwiche-Pearl extension)

**What it tests:** When a character updates their belief at t=2 (via observation),
and a second unobserved event occurs at t=3, the model must track the t=2 state
as the relevant baseline — not the original t=1 state. The answer must come from
the last *observed* update, not from the first belief.

**Why this matters:** The current bigtom stories only ever test "original belief
vs. current world." Iterated revision tests whether the model can maintain a
belief chain — the lookback mechanism with temporal OIDs should distinguish
(char, obj, t=1) from (char, obj, t=2) as two distinct bindings.

**Concrete example:**

> Maya keeps a book on the shelf in her living room [t=1: belief = shelf].
> Before heading to work, Maya moves the book to her bag [t=2: Maya observes,
> belief = bag]. While Maya is at work, her roommate takes the book out of
> Maya's bag and puts it back on the shelf, not telling Maya [t=3: Maya does
> not observe]. Does Maya believe the book is in her bag or on the shelf?

**Correct answer:** Maya believes the book is in her bag (her t=2 belief is
her current belief; the t=1 state is irrelevant).

**Template schema:**
```json
{
  "type": "iterated_revision",
  "events": [
    {"t": 1, "state": "<state_1>", "agent_observes": true,  "observation_type": "initial_perception"},
    {"t": 2, "state": "<state_2>", "agent_observes": true,  "observation_type": "direct_action"},
    {"t": 3, "state": "<state_3>", "agent_observes": false, "observation_type": "none"}
  ],
  "question": "What does <character> believe about <object>?",
  "correct_answer": "state_2",
  "distractor": "state_3",
  "trap": "state_1"
}
```
Note the three-answer structure: the naive model confuses t=1 with t=2; the
baseline model only knows to avoid t=3 (the current world state). A correct
lookback with temporal OIDs returns t=2.

---

### Type 2 — Vacuity (Non-Contradicting Addition)

**AGM property:** VACUITY — if new information P does not contradict K, then
K*P = K+P. No prior belief should be disturbed.

**What it tests:** When a character acquires a new belief that does not conflict
with any existing belief, all prior beliefs must remain intact. The model should
not "shuffle" the belief set when new non-threatening information arrives.

**Concrete example:**

> Anya believes the box on the table contains a red marble. Later, Anya opens
> the desk drawer and sees it contains a blue pen. Does Anya believe the box
> contains a red marble? Does Anya believe the desk drawer contains a blue pen?

**Correct answers:** Yes to both. No revision occurred — this is pure expansion.
The red marble belief should be untouched by the pen observation.

**Template schema:**
```json
{
  "type": "vacuity",
  "prior_beliefs": [
    {"object": "<object_A>", "state": "<state_A>", "agent_observes": true}
  ],
  "new_info": {
    "object": "<object_B>",
    "state": "<state_B>",
    "agent_observes": true,
    "contradicts_prior": false
  },
  "questions": [
    {"object": "<object_A>", "correct_answer": "state_A"},
    {"object": "<object_B>", "correct_answer": "state_B"}
  ]
}
```

---

### Type 3 — Minimal Change Check

**AGM property:** MINIMAL CHANGE / INCLUSION — revision should change only what
it must. Other beliefs are left alone.

**What it tests:** When a character revises one belief (due to new observation),
all unrelated beliefs should remain unchanged. The model must not "spread"
revision across the belief set.

**Concrete example:**

> Priya enters the kitchen. She sees that the first jar on the shelf contains
> jam and the second jar contains honey [belief_A = jam, belief_B = honey].
> Later, Priya watches her housemate replace the first jar with one containing
> mustard [belief_A revised to mustard, Priya observes]. Does Priya believe
> the second jar contains honey?

**Correct answer:** Yes — the second-jar belief was never touched by the revision.

**Template schema:**
```json
{
  "type": "minimal_change",
  "initial_beliefs": [
    {"object": "<object_A>", "state": "<state_A>"},
    {"object": "<object_B>", "state": "<state_B>"}
  ],
  "revision_event": {
    "object": "<object_A>",
    "new_state": "<state_A_prime>",
    "agent_observes": true
  },
  "test_question": {
    "object": "<object_B>",
    "correct_answer": "state_B",
    "distractor": "null or revised"
  }
}
```

---

### Type 4 — Merging (Two Conflicting Sources, No Priority)

**AGM property:** MERGING (Konieczny & Pérez 2002) — two sources that conflict
with no known reliability ordering.

**What it tests:** When a character hears two contradictory claims about the
same (object, state) from two sources of equal reliability, what belief state
results? The correct AGM response is suspension or partial belief — the model
should not silently pick one source.

**Concrete example:**

> Luis asks two colleagues where the company's backup drive is stored. Amara
> says it is in the server room. Kwame says it is in the manager's office. Luis
> has no reason to trust one over the other and has not checked himself. Is
> Luis certain the drive is in the server room?

**Correct answer:** No — Luis has conflicting information and cannot be certain.
(A model that confidently answers one source has failed the merging test.)

**Template schema:**
```json
{
  "type": "merging",
  "sources": [
    {"agent": "<source_1>", "claim": {"object": "<object>", "state": "<state_A>"}},
    {"agent": "<source_2>", "claim": {"object": "<object>", "state": "<state_B>"}}
  ],
  "receiver": "<character>",
  "receiver_observes_directly": false,
  "reliability_ordering": "none",
  "question": "Is <character> certain that <object> is <state_A>?",
  "correct_answer": "No — conflicting sources, no priority",
  "distractor": "Yes — first source wins"
}
```

---

### Type 5 — Contraction (Belief Removal via Source Invalidation)

**AGM property:** CONTRACTION — a belief can be removed without being
contradicted, if its sole justification is undermined.

**What it tests:** When the *reason* a character holds a belief is revealed to
be unreliable (the source was mistaken, fabricated, or unqualified), the belief
should be retracted even though no direct contradiction has been offered.

**Concrete example:**

> Omar received a message from his colleague stating that the afternoon meeting
> had been moved to the large conference room. Omar believes the meeting is in
> the large conference room. Later, Omar discovers that the message was a test
> sent by the IT department — the sender had no actual knowledge of the
> meeting location. Does Omar still believe the meeting is in the large
> conference room?

**Correct answer:** No — the belief's sole support (the colleague's message) is
revealed to be without foundation. No new state is asserted, but the belief
should be retracted.

**Template schema:**
```json
{
  "type": "contraction",
  "belief": {"object": "<object>", "state": "<state>"},
  "belief_source": {"agent": "<source>", "reliability": "initially trusted"},
  "invalidation_event": {
    "type": "source_discredited",
    "description": "<source> had no actual knowledge"
  },
  "direct_contradiction": false,
  "question": "Does <character> still believe <object> is <state>?",
  "correct_answer": "No — source invalidated",
  "distractor": "Yes — no contradiction offered"
}
```

---

### Type 6 — Temporal Depth (Belief Retention Across Unrelated Events)

**AGM property:** MINIMAL CHANGE — beliefs not targeted by a revision event
must survive across time, even if many other events have occurred.

**What it tests:** When many events happen (none of which touch a specific
belief), that belief should still be retrievable at a later point. This tests
whether the model's lookback can reach across a long intervening passage to
retrieve an old but still-valid binding.

**Concrete example:**

> On Monday, Elena puts her passport in the left drawer of her desk. On Tuesday,
> she reorganizes her bookshelf. On Wednesday, she buys new plants for the
> balcony. On Thursday, she replaces her kitchen table. On Friday, Elena needs
> her passport. Where does Elena believe her passport is?

**Correct answer:** In the left drawer — none of the intervening events touched
the passport belief. This tests "belief retention across noise."

**Template schema:**
```json
{
  "type": "temporal_depth",
  "initial_belief": {
    "object": "<object>", "state": "<state>", "time": "t=1",
    "agent_observes": true
  },
  "intervening_events": [
    {"time": "t=2", "object": "<other_object_1>", "unrelated": true},
    {"time": "t=3", "object": "<other_object_2>", "unrelated": true},
    {"time": "t=4", "object": "<other_object_3>", "unrelated": true}
  ],
  "question_time": "t=5",
  "question": "Where does <character> believe <object> is?",
  "correct_answer": "state (from t=1)",
  "distractor": "not stated / cannot know"
}
```

---

### Type 7 — Source Priority (Reliability-Ordered Revision)

**AGM property:** REVISION with an explicit priority ordering over sources.

**What it tests:** When two conflicting sources exist but one is explicitly more
reliable (eyewitness vs. hearsay, expert vs. non-expert), the revision should
favor the more reliable source — regardless of temporal order.

**Concrete example:**

> A rumor circulates that the lab is on the third floor. Selin hears the rumor
> and forms a tentative belief. Later, Selin asks the department administrator
> directly, who has access to the official building plan and says the lab is on
> the second floor. Does Selin believe the lab is on the third or second floor?

**Correct answer:** Second floor — the administrator is an authoritative source
and should override the rumor even though the rumor came first.

**Template schema:**
```json
{
  "type": "source_priority",
  "beliefs_in_order": [
    {
      "source_reliability": "low",
      "object": "<object>", "state": "<state_A>",
      "temporal_order": 1
    },
    {
      "source_reliability": "high",
      "object": "<object>", "state": "<state_B>",
      "temporal_order": 2
    }
  ],
  "question": "What does <character> believe about <object>?",
  "correct_answer": "state_B (high-reliability source wins)",
  "distractor": "state_A (first-heard source wins)"
}
```

---

## The Full Coverage Matrix

```
Story Type              | Postulates Tested
─────────────────────────────────────────────────────────────────────
bigtom / templates       | Implicit initial SUCCESS
Type 1 Iterated Revision | SUCCESS (iterated), temporal OID depth
Type 2 Vacuity           | VACUITY (#4), INCLUSION (#3)
Type 3 Minimal Change    | MINIMAL CHANGE (#3, #7, #8)
Type 4 Merging           | CONSISTENCY (#5), Konieczny merging
Type 5 Contraction       | CONTRACTION (CONSISTENCY variant)
Type 6 Temporal Depth    | MINIMAL CHANGE across span, CLOSURE
Type 7 Source Priority   | REVISION with priority, SUCCESS variant
─────────────────────────────────────────────────────────────────────
```

---

## Creative Extensions: Multi-Agent Stories

The template above covers single-character belief tracking. Extending to
**multi-character joint belief states** opens a second dimension of testing:

**Type M1 — Belief Divergence:** Two characters observe the same event, then
one receives additional information. Questions ask about both. Tests whether
the mechanism can maintain *separate* belief stores for co-present characters.

**Type M2 — False Belief About False Belief (Second-Order):** Character A
believes something; character B has an outdated model of what A believes.
"What does B think A believes?" This is the standard ToM second-order test.
The lookback paper only tests first-order (what does X believe?). Second-order
requires nested (char, obj, believing_char) bindings.

**Type M3 — Gossip Chain:** A → B → C → D, each conveying the same piece of
information with possible distortion. By the time the belief reaches D, how
much does D's belief correspond to what A originally observed? Tests belief
propagation fidelity.

---

## Engineering Implication

The existing `story_templates.json` has a flat schema:
`context + causal_event + event_noticed + question → answer + distractor`

That schema cannot express:
- Multiple events at different time points (Types 1, 6)
- Multi-object belief sets (Types 2, 3)
- Multiple sources (Types 4, 7)
- Source invalidation (Type 5)
- Nested belief queries (Type M2)

A revised schema for the extended templates is in:
`belief_tracking/data/agm_story_templates.json`
