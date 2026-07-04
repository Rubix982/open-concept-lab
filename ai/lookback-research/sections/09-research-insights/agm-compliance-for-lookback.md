# Research Insight: AGM Compliance for the Lookback Mechanism

_Emerged from: connecting belief-revision theory to the lookback OID architecture_
_Date: 2026-07-04_
_Status: speculative — theoretical extension, not yet tested experimentally_
_Related: belief-revision-and-uncertainty.md, sections/00-abstract/notes.md_

---

## The Core Question

The lookback mechanism (as described in the paper) is a **read-only retrieval system**.
It maintains (Character, Object, State) bindings via co-located Ordering IDs in the
residual stream, and at answer time, attention looks back to retrieve the state matching
a queried (character, object) pair.

The question: what would the mechanism need to become **AGM-compliant** — capable of
rational belief revision in the formal sense?

AGM (Alchourrón, Gärdenfors, Makinson, 1985) defines **eight postulates** a rational
agent must satisfy when revising beliefs. K is the current belief set; P is the new
information being incorporated; K*P is the revised belief set.

---

### The Eight Postulates — Plain English

**1. Closure** — K*P is a belief set (deductively closed).
After revision, your beliefs still hang together. If you believe "it is raining" and
"if it rains the ground is wet", you implicitly believe "the ground is wet." Revision
doesn't break that — consequences are preserved.

**2. Success** — P ∈ K*P.
The new information actually makes it in. If P is "the marble is in the box", the
revised belief set must contain that. Revision that ignores the new information isn't
revision.

**3. Inclusion** — K*P ⊆ K+P.
Revision doesn't add more than necessary. Revising by P yields a subset of simply
adding P naively. You don't gain extra beliefs from revision that you wouldn't get
from straight addition. Revision is conservative.

**4. Vacuity** — If ¬P ∉ K, then K*P = K+P.
If P doesn't contradict anything you already believe, revision is just addition.
No conflict, no drama — you add P and nothing else changes. Revision only does real
work when there is a contradiction to resolve.

**5. Consistency** — K*P is inconsistent only if P is inconsistent.
After revision, your beliefs are consistent — unless P itself is self-contradictory.
If P is a coherent claim, the revised belief set must be contradiction-free.

**6. Extensionality** — If P and Q are logically equivalent, then K*P = K*Q.
Equivalent information produces the same revision. "It is not the case that it is not
raining" and "it is raining" mean the same thing; revising by either gives identical
results. The form of the new information doesn't matter, only its meaning.

**7. Superexpansion** — K*(P∧Q) ⊆ (K*P)+Q.
If you revise by "P and Q together", the result is contained within "first revise by
P, then just add Q." Revising by a conjunction is at most as strong as doing it in
two steps.

**8. Subexpansion** — If ¬Q ∉ K*P, then (K*P)+Q ⊆ K*(P∧Q).
The flip side. If Q doesn't contradict your P-revised beliefs, then revising by
"P and Q together" is at least as strong as revising by P then adding Q.

Postulates 7 and 8 together: revising by "P and Q" is equivalent to revising by P
then adding Q — *as long as Q doesn't conflict with the P-revised beliefs*. When Q
does conflict, the conjunction must be treated as its own revision problem.

The whole set says: revision should be **conservative** (change only what you must),
**consistent** (never produce contradictions from coherent input), and
**meaning-sensitive** (grammar of the new information doesn't distort the result).

---

### Simplified View Used in This Analysis

For the purposes of analyzing the lookback mechanism, the eight postulates reduce to
three properties that matter architecturally:

```
SUCCESS      — new belief must be incorporated        (postulates 2, 4)
CONSISTENCY  — resulting belief set must be consistent (postulates 1, 5, 6)
MINIMAL CHANGE — revise only what must be revised     (postulates 3, 7, 8)
```

The lookback mechanism satisfies none of these as currently described.
Below is what each requires.

---

## Axiom 1: SUCCESS — Requires a Write Operation

**What lookback does now:**
Bindings are written once during the forward pass from story text. The (character_OID,
object_OID) → state mapping is fixed in the residual stream and never updated.

**What SUCCESS requires:**
When new information about a (character, object) pair arrives, the mechanism must write
a new state to that binding. The OID indexing is already the right key structure — you
can address a specific (character, object) pair precisely. What is missing is any path
that takes new input and updates the state at that address.

**Concrete requirement:**
A write operation alongside the existing read:

```
READ:  (character_OID, object_OID) → current state         [exists]
WRITE: (character_OID, object_OID) × new_state → updated   [missing]
```

Without this, the mechanism cannot satisfy SUCCESS. It can retrieve beliefs but cannot
revise them.

---

## Axiom 2: CONSISTENCY — Requires Temporal OIDs

**What lookback does now:**
OIDs encode *positional* identity: first/second character, first/second object. They do
not encode *when* a belief was formed. If Sally believes (marble → basket) at t=1 and
receives information (marble → garden) at t=2, the mechanism has no way to represent
these as two states for the same (Sally, marble) pair — or to detect that they conflict.

**What CONSISTENCY requires:**
OIDs must extend to a temporal dimension:

```
CURRENT:  (character_OID, object_OID)          → state
EXTENDED: (character_OID, object_OID, belief_t) → state
```

With temporal OIDs, two entries for the same (character, object) pair but different
belief_t values constitute a detectable conflict. The consolidation step can then
resolve it:

```
REVISION: belief_t=2 wins (new information treated as more reliable)
MERGING:  negotiate (no priority assumed; both sources weighed)
```

**Concrete implementation path:**
The paper already notes that lookback uses RoPE for positional encoding. RoPE can be
extended to carry a belief-formation timestamp alongside token position. Lookback
attention would then naturally distinguish the most recent valid binding for a
(character, object) pair from earlier superseded ones.

---

## Axiom 3: MINIMAL CHANGE — Requires Non-Destructive Revision

**What lookback does now:**
If a write operation overwrites the state at a (character, object) key, the prior
belief is lost. This violates minimal change — you changed more than necessary because
you erased information that was not required to be erased.

**What MINIMAL CHANGE requires:**
Old bindings must be marked as superseded, not deleted. The belief store becomes a
chain:

```
(Sally, marble) → basket   [t=1, active=false, superseded_by=t=2]
(Sally, marble) → garden   [t=2, active=true,  source=Anne testimony]
```

Lookback retrieves the active (most recent) entry for current-belief queries. The full
chain is preserved for provenance queries ("what did Sally used to believe?").

This is structurally cheap given OIDs: you are only marking a flag on an existing entry
and adding a new one with a higher belief_t. No other bindings are touched — minimal
change is architecturally enforced by the OID address structure.

---

## The Structural Gap: Read-Only vs Read-Write

The three axioms together expose a single underlying gap:

```
CURRENT ARCHITECTURE         AGM-COMPLIANT EXTENSION
─────────────────────        ──────────────────────────────────────────
Belief store: residual       Belief store: external, writable, persistent
              stream only                  indexed by (char_OID, obj_OID, t)

Operations:   read only      Operations:   read + write + consistency check

Scope:        single         Scope:        across forward passes
              forward pass                 (beliefs persist between sessions)

Provenance:   none           Provenance:   full chain — active + superseded,
                                           with source and timestamp per entry
```

The lookback mechanism is the **read half** of a larger system. The paper demonstrates
that this read half exists and is mechanistically real in current LLMs — a significant
finding. The write half, the consistency check, and the non-destructive archive are
what must be designed to achieve AGM compliance.

---

## Does the Lookback Ordering Complement the AGM Requirements?

**Yes — as a foundation, not as a solution.**

The OID co-location structure gives you:
- Precise addressability: you can target a specific (character, object) pair
- Binding integrity: character and object OIDs are co-located in the state token,
  so they cannot be decoupled accidentally
- Retrieval mechanism: attention-based lookback already works as the read operation

What OIDs do not currently provide:
- Temporal indexing: no belief_t dimension
- Write semantics: no path to update a binding from new input
- Conflict detection: no check when a new state would collide with an existing one
- Chain preservation: no superseded-not-deleted semantics

The extension from positional OIDs to temporal OIDs is the single most load-bearing
change. With temporal OIDs, SUCCESS, CONSISTENCY, and MINIMAL CHANGE all become
architecturally expressible — they are no longer blocked by the structure itself.

---

## Connection to Existing Insights

From `belief-revision-and-uncertainty.md`:

> The first load is *replaced*, not *updated*. The model does not use the weak first
> load as a query to search for confirming or contradicting evidence. It drops it and
> waits for a stronger signal.

This is the same failure mode viewed from a different angle. That insight identified
the replacement-not-accumulation problem at the level of activation dynamics within a
forward pass. This insight identifies the same problem at the level of belief
representation across forward passes.

The RetrievalProfile (from the prior insight) tracks *how* a belief was retrieved.
The temporal OID extension tracks *when* a belief was formed and whether it was
subsequently superseded. Together they would give a system that knows both the quality
and the history of each belief it holds.

---

## Open Questions

1. **Can temporal OIDs be grounded in existing RoPE positions?**
   RoPE already encodes token position — can belief_t be derived from the token
   position of the state token that originally wrote the binding? If so, no new
   positional encoding scheme is required.

2. **Where does the external belief store live architecturally?**
   Options: external key-value memory (Neural Turing Machine style), an auxiliary
   embedding layer trained to track (char, obj, t) → state, or a structured database
   queried at attention time.

3. **Can consolidation be trained as an operation?**
   Rather than hard-coding revision vs. merging, could a model learn to perform the
   consolidation step from examples — given a conflict between two (char, obj) bindings,
   produce the correct resolution?

4. **What is the minimal architectural change?**
   Full AGM compliance may require external memory. But partial compliance — e.g.,
   SUCCESS + MINIMAL CHANGE without full consistency checking — might be achievable
   within the transformer architecture by extending RoPE and adding a write-head
   attention pattern.

---

## Questions to Bring to Authors

1. Are there any attention heads in the paper's analysis that appear to be doing
   something like a write operation — updating a prior binding rather than retrieving?

2. Does the lookback mechanism ever re-fire on a (character, object) pair that it
   has already bound — and if so, does it replace or accumulate?

3. Has anyone extended the OID framework to carry temporal information? Is this a
   direction the authors have considered?
