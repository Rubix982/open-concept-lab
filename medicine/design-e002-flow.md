# Design — E-002 · The Board (department flow)

_Derived 2026-09-27 under R-001. Companion to `plan.md`._

---

## 0 · Premise dry-run (run before designing)

**The flat framing.** "A glossary of flow terms: ESI, door-to-doc, boarding,
LWBS, diversion, dispo." Correct, inert, and the reader leaves knowing eight
definitions and no argument. Stuck-and-flat, not stuck-and-hard — the
corrective was not missing information, it was a one-sided frame.

**Move 1 — find the structure under the intuition.** The recurring intuition
is that the ED "feels like it is failing while nobody is doing anything
wrong." That is not sentiment, it is a structural property: the ED is a
queueing system whose *output* is controlled by somebody else. Every symptom
people name — waits, LWBS, hallway medicine, diversion, moral injury — is
downstream of one upstream fact: admitted patients cannot leave.

**Move 2 — rename into an existing formalism.** This is Little's Law and the
input–throughput–output model of ED crowding (Asplin et al., 2003). Occupancy
= arrival rate × length of stay. Once length of stay is dominated by boarding
time, which the ED does not control, working faster cannot reduce occupancy.
Importing the formalism converts a complaint into an arithmetic claim that
can be checked.

**Move 3 — invert the difficulty.** The intuitive lever is throughput: see
patients faster. Inverting it: the easy-sounding lever barely moves the
number, and the leverage sits in a place that sounds unrelated to emergency
medicine entirely — when inpatient floors discharge, and whether boarded
patients are distributed to inpatient hallways instead of concentrated in the
ED. The difficulty judgement was a property of the frame.

**The spine, therefore:** *one constraint, and every word downstream of it.*
The bay piece is ordered by how fast things kill. The board piece is ordered
by where the queue is blocked. Those are different logics and the difference
is the content, not an inconvenience.

**Move 8 — what the reframe breaks.** It invalidates the obvious section
order. "Triage → waiting → seen → admitted → gone" is chronological and hides
the causality, because the blockage is at the *end* and the visible damage is
at the *beginning*. The piece must state the constraint early and then read
the vocabulary off it, which is close to the reverse of narrative order.

---

## 1 · Significance (WHY gate)

**Confirmed reading:** a viewer who finishes the piece can watch a crowded-ED
scene and correctly locate the cause outside the room — and can tell which of
the show's conflicts are about clinical judgement and which are about a bed
that does not exist. That is a genuine shift; the default viewer reading is
that the department is understaffed or someone is slow.

**Denied reading:** if the causal spine does not hold up — if crowding really
is mostly an input or throughput problem — the piece collapses back into a
glossary, and should be built as one, shorter.

The WHY gate passes, but note the honest limit: this is an *explainer*, not
research. Its contribution is representation, not discovery. What keeps it
from being a Wikipedia summary is the causal ordering and the tie to what a
viewer actually sees on screen.

## 2 · Prior art

Established and uncontroversial: the input–throughput–output model; Little's
Law; the Emergency Severity Index algorithm; EMTALA's screening and
stabilisation duty; the standard time-to-treatment targets. None of this is
mine and the piece should not imply otherwise.

---

## 3 · Sections

### A · The door — why the ED absorbs everything

**EMTALA.** A Medicare-participating hospital with an emergency department
must provide a medical screening exam and stabilise an emergency condition
regardless of ability to pay. One legal sentence, and it is the reason the ED
is the variance sink of the entire hospital: it is the only department that
cannot say no, cannot schedule, and cannot cap its intake.

Terms: EMTALA · medical screening exam · walk-in vs. EMS arrival · triage ·
ambulance patient offload.

### B · ESI — the triage tree  ★ animated panel

The correction most viewers need. ESI is *not* a pure severity scale.

- **ESI 1** — needs a life-saving intervention right now.
- **ESI 2** — high risk, or confused/lethargic/disoriented, or severe pain or
  distress. Should not wait.
- **ESI 3 / 4 / 5** — decided by **how many resources** the patient will
  consume: two or more → 3, one → 4, none → 5.
- A danger-zone vital sign can pull a 3 up to a 2.

So "ESI 3" does not mean *medium sick*. It means *two or more resources*. A
young patient with a sprained ankle needing an x-ray and nothing else is a 4
regardless of how loudly they are in pain, and the algorithm is explicitly
built so that triage does not require a diagnosis.

Panel: a patient descending four decision points and landing in a level.

> **Version caution:** ESI wording has changed across editions (the handbook
> moved stewardship to ENA and was revised in the 2020s). Keep to the stable
> core; do not quote edition-specific phrasing as if fixed.

### C · The board — where the time actually goes  ★ animated panel

The tracking display itself: rows, acuity colour, elapsed timers, and the
states a patient passes through — arrival → triage → room → provider →
workup → disposition decision → departure.

The useful reveal is proportion. For a discharged patient the workup
dominates; for an admitted patient the time *after* the decision — waiting
for a bed — can exceed everything before it combined. Same department, same
staff, wildly different shapes.

Terms: the board · charge nurse · flow coordinator · provider-in-triage ·
pull-till-full / immediate bedding · fast track · vertical care · hallway bed.

### D · Boarding — the constraint  ★ the panel the piece exists for

Boarding: a patient who has been admitted but is still physically in the ED
because no inpatient bed is available.

Panel: arrivals continue at a steady rate while the output valve narrows.
Nobody on screen slows down. The waiting room fills anyway, LWBS climbs, and
the department is full — arithmetic, not effort. Little's Law stated plainly:
occupancy = arrival rate × length of stay.

The causal direction is the whole point, and it runs *outward*: the bed is
blocked upstairs, so the ED fills, so the waiting room fills, so people
leave without being seen.

### E · What the constraint produces

Each of these presented as a **consequence**, never as its own category:

- **LWBS / LWOT** — left without being seen. Rises with wait time; a queue
  metric wearing the costume of a patient choice.
- **Hallway medicine** — care delivered in a corridor because the room is a
  fiction.
- **Diversion** — telling EMS to go elsewhere. It does not create capacity;
  it relocates the queue, and it delays time-critical care. Several
  jurisdictions have restricted or banned it for exactly that reason.
- **Handoff / signout** — shift change as a known danger point, made worse by
  a department holding patients it has already decided about.

### F · Dispo — every patient terminates somewhere

Discharge · admit · **observation** · transfer · OR · AMA · LWBS · death.

Two that deserve real explanation because they confuse people:

- **Observation status** is a billing and bed category, not a clinical one.
  The patient is in a hospital bed and has not been admitted. Under Medicare
  this interacts with the two-midnight rule and with skilled-nursing
  coverage, so it has consequences the patient cannot see from the bed.
- **AMA** — leaving against medical advice. The widespread belief that
  insurance will refuse to pay is largely unsupported; it circulates anyway,
  including among staff, which makes it a coercive myth rather than a
  neutral one.

### G · The clocks — time-to-treatment targets

Table, in the style of the monitor-numbers section:

| Clock | Target | What it is measuring |
|---|---|---|
| Door-to-doc | local | Time to provider contact |
| Door-to-balloon | ≤ 90 min | Arrival to primary PCI in STEMI |
| Door-to-needle | ≤ 60 min | Arrival to IV thrombolysis in stroke |
| Sepsis bundle | 3 h | Lactate, cultures, antibiotics, fluids |
| ED length of stay | by dispo | The number boarding destroys |
| LWBS rate | low single % | The queue, measured |

### H · Glossary — the board-side acronym wall

---

## 4 · Takeaways (the argument, stated)

1. Crowding is an **output** problem. It is created upstairs and paid for
   downstairs.
2. **ESI 3 is not "medium sick."** It is "two or more resources." The
   algorithm deliberately avoids requiring a diagnosis.
3. **Diversion does not make capacity.** It moves the queue and costs
   time-critical patients minutes they cannot spare.
4. **The waiting room is a symptom.** Treating it as the disease is how a
   department spends years optimising the part that was never the constraint.

---

## 5 · Claims to hedge (move 8 · the adversary lens)

An infographic's confident register will overclaim these unless the wording
is controlled. Flagged now so the copy is written correctly the first time:

- **Boarding and harm.** Association with increased mortality and longer
  inpatient stay is repeatedly found and biologically plausible, but the
  evidence is observational. Write "associated with", never "causes".
- **Discharge-before-noon.** Intuitive and widely promoted; the actual
  evidence for its effect on ED boarding is mixed and modest. Do not present
  it as a solved lever.
- **Full-capacity protocols** (distributing boarded patients to inpatient
  hallways) have better support than most interventions, but "better
  supported" is not "proven". Say so.
- **ESI edition drift** — see §B.
- **Numbers vary enormously** by country, system and hospital. Any figure
  quoted as if universal will be wrong somewhere; prefer directions and
  thresholds over point estimates.

---

## 6 · Deliverable

The one figure that carries the claim is the **boarding panel** (§D): steady
arrivals, a narrowing output, a filling department, nobody slowing down. If
that single panel lands, the rest of the vocabulary reads itself off it. Every
other section should be checked against whether it serves that panel.

---

## 7 · Open — the merge

Deliberately unresolved here; see `threads.md` T-003. The two pieces have
different organising logics (physiology vs. queueing), which is either the
strongest reason to join them or the strongest reason not to.
