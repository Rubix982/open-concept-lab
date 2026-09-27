# Researcher tickets

Agenda derived 2026-09-27. Priority is driven by correctness debt first:
the document already asserts these things in public, unsourced.

| ID | Area | Why it is on the list | Priority |
|----|------|----------------------|----------|
| R-002 ✓ | ACLS / arrest | Compression rate and depth, adrenaline interval, defibrillation energy, amiodarone dosing, ETCO₂ thresholds and the ROSC signal. All currently shipped unsourced. | high |
| R-003 ✓ | RSI and airway | The seven P's, induction and paralytic doses, succinylcholine contraindications, rocuronium duration, waveform capnography as confirmation. | high |
| R-004 ✓ | Tension pneumothorax | The needle decompression landmark and the ATLS change, catheter length vs chest wall thickness, tube size, the triangle of safety. The page makes a specific causal claim about *why* the landmark moved. | high |
| R-005 ✓ | Ultrasound characteristics | E-FAST lung sliding sensitivity and specificity, the lung point, and the limits of a negative FAST. Partially done (R-001). | medium |
| R-006 ✓ | Shock and transfusion | MAP ≥65 (SEPSISPAM), 1:1:1 (PROPPR), TXA (CRASH-2/CRASH-3), permissive hypotension, calcium in massive transfusion. | high |
| R-007 ✓ | The monitor numbers | SpO₂ targets, ETCO₂ ranges, shock index threshold, "GCS 8, intubate" and its critique, lactate >4 and clearance. | medium |
| R-008 ✓ | Department flow | ESI edition and algorithm, EMTALA, boarding and patient outcomes, LWBS, diversion policy. Needed before E-006 builds Part III. | medium |

---

### R-004 · Tension pneumothorax: landmark, catheter, tube

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-27

**Description:**
The document currently states that trauma guidance moved the needle
decompression site from the second intercostal space midclavicular line to the
fifth intercostal space anterior axillary line, and gives a causal reason
(thinner chest wall laterally, frequent failure at the old site in adults).
That is a specific, checkable claim shipped without a source.

Establish: what the current guidance actually says, what the evidence for the
change was, what catheter length is needed, and whether the tube size question
is settled. Record disagreement where it exists rather than picking a side.

**Artifacts:**

- agents/shared/findings.md → "[R-004] Finding: needle decompression is less
  settled than the page implies"

**Closed:** 2026-09-27

### R-002 · ACLS / arrest

**Status:** closed (partial — see R-002a)
**Closed:** 2026-09-27

Trial-level evidence for adrenaline, amiodarone and ETCO₂ retrieved and written
up. The AHA guideline numerics were not retrieved and are carried forward as a
follow-up; they stay `low` confidence until then.

**Artifacts:** agents/shared/findings.md → [R-002], [R-002a]

### R-009 · AHA guideline numerics

**Status:** open
**Type:** research
**Priority:** high
**Created:** 2026-09-27

Retrieve the AHA 2020 Guidelines for CPR and ECC (and any later focused update)
and source the compression rate and depth, defibrillation energy, rhythm-check
interval and adrenaline interval directly. These are the most-repeated numbers
on the page and currently the least supported.

### R-006 · Shock and transfusion

**Status:** closed (partial)
**Closed:** 2026-09-27

SEPSISPAM, PROPPR and CRASH-2 retrieved. TXA time-stratified effect estimates
not retrieved — carried into R-010.

**Artifacts:** agents/shared/findings.md → [R-006]

### R-010 · TXA timing, and the remaining unverified numerics

**Status:** open
**Type:** research
**Priority:** medium
**Created:** 2026-09-27

CRASH-2/CRASH-3 time-stratified effects; succinylcholine and rocuronium onset
and duration (R-003); ESI algorithm (R-008). Grouped because each is a small
number of specific figures rather than a literature.

### R-003 / R-005 / R-008 · closed (partial)

**Closed:** 2026-09-27
**Artifacts:** agents/shared/findings.md → [R-003], [R-005], [R-008]

R-003 found the single clearest error on the page (ketamine and haemodynamics).
R-005 supplies the real lung-ultrasound figures, retiring unverified marker u1.
R-008 sources boarding/mortality; ESI algorithm and LWBS still unsourced and
carried into R-010.

R-007 (monitor numbers: shock index, oxygen targets, lactate clearance,
"GCS 8 intubate") was NOT run this session. It remains open at medium priority.

### R-007 · The monitor numbers

**Status:** closed (partial — lactate incomplete)
**Closed:** 2026-09-27
**Artifacts:** agents/shared/findings.md → [R-007]

Method note: free-text queries kept returning a single large conference-
proceedings record. Switching to PubMed field syntax ([ti], [pt], [sb]) fixed
it. Use field syntax for the remaining tickets.

### R-009 · AHA guideline numerics — BLOCKED

**Status:** blocked
**Updated:** 2026-09-27
**Blockers:** access. ahajournals.org and cpr.heart.org both return 403.

Established that a 2025 edition exists and the document reflects 2020 teaching.
Numerics not retrieved. Secondary vendor summaries deliberately refused.

### R-010 · closed (partial)

**Status:** closed
**Closed:** 2026-09-27
**Artifacts:** agents/shared/findings.md → [R-010]

TXA timing and ESI retrieved. Succinylcholine/rocuronium onset and duration,
and lactate clearance effect estimates, still not sourced — folded into R-011.

### R-011 · The remaining pharmacology numerics

**Status:** open
**Priority:** medium
Succinylcholine and rocuronium onset/duration; all induction and pressor doses
quoted on the page; lactate clearance effect estimates.
