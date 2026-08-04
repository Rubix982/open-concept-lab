# Research Threads — rome-neighbors

_Open questions from research discussion, tracked as a tree so none is lost._
_See global CLAUDE.md → "Research Thread Tracking" for the protocol._

---

### T-001 · Does editing a fact ripple to its logical neighbours?

**Status:** active (the project's root question)
**Parent:** — (root)
**Opened:** 2026-07-22
**Question:** After a ROME edit (Eiffel Tower → Rome), do entailed neighbours
(country → Italy, language → Italian, reverse lookups) also update? This is the
portability/ripple problem the whole project studies.
**Answer:** — (E-002/E-003/E-004 will measure it)

---

### T-002 · What are the conditions for an IIA interchange to flip the answer?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-08-04
**Question:** When does patching SOURCE's activation into BASE flip Paris→Rome?
**Answer:** Two conditions, BOTH required: (1) the site `(L,p)` must encode the
variable in SOURCE, and (2) the same site must be READ by BASE downstream. See
`readings/metrics/notes.md` and the 2026-08-04 discussion. Off-peak `(L,p)` →
IIA collapses; that collapse is what gives the sweep its resolution.

---

### T-003 · Why do mismatched-layer patches collapse IIA?

**Status:** answered
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** If the patch layer isn't where the fact lives (or differs between
runs), what happens?
**Answer:** IIA falls toward 0. Two distinct failure signatures: INERT (BASE
still says Paris → wrong site, no signal transplanted) vs. DESTRUCTIVE (garbage
output → off-distribution injection, e.g. cross-layer patch). Layer and position
are coupled: "early" is fatal at the readout position but correct at the subject
position. Same-index interchange works because both prompts share the circuit.

---

### T-004 · How do we determine the "Rome-ness" of an activation?

**Status:** open
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** IIA condition 1 assumes we can tell whether an activation at `(L,p)`
carries the location variable. By what measure do we establish that? Candidate
methods: linear probe for the location, Direct Logit Attribution toward the city
token, logit-lens projection, or DAS to find the subspace. Which is right, and
do they agree?
**Answer:** —

---

### T-005 · How do we verify what BASE downstream actually consumes?

**Status:** open
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** IIA condition 2 requires that a site is READ by downstream layers.
How do we check consumption directly rather than inferring it from the flip?
Candidate methods: path patching, attention knockout on the edges out of `(L,p)`,
or ablating the site and watching which downstream components change.
**Answer:** —

---

### T-006 · Is "downstream consumption" itself a kind of neighbour?

**Status:** open
**Parent:** T-005
**Opened:** 2026-08-04
**Question:** A downstream component that READS from the edited site is
structurally the same relationship as a neighbour fact that depends on the
edited fact. If so, the ripple problem (T-001) and the consumption question
(T-005) are the same question at two levels — representational and logical.
Does the mechanistic "who reads this site" map onto the logical "which facts
entail this one"? If they line up, the causal graph over activations IS the
entailment graph over facts — which would be the deep result of the project.
**Answer:** —

---

## Thread tree

```
T-001 ripple/portability (root)
└─ T-002 IIA flip conditions ...................... answered
   ├─ T-003 mismatched-layer collapse ............. answered
   ├─ T-004 determining "Rome-ness" ............... OPEN
   └─ T-005 verifying downstream consumption ...... OPEN
      └─ T-006 consumption-as-neighbour ........... OPEN  ← the deep one
```
