# Healthcare AI — Strategic Decision-Making Case Study

*Based on: "The future of AI in medicine" — Conor Judge, TEDxGalway*
*Personal study notes — analysis and synthesis.*

---

## The Framing Problem

Judge opens with a structural diagnosis before he introduces a single AI system:
doctors spend 70% of their time collecting information and 30% making decisions
and communicating with patients. Technology made this worse, not better — electronic
health records were designed for billing, so they optimised for administrative
capture rather than clinical efficiency. The face-to-face time that patients want
and doctors were trained to provide got crowded out by data entry.

This is the right starting frame for any healthcare AI discussion. The problem is
not "doctors are inefficient." The problem is that a system designed around a
different incentive (billing) produces a different behaviour (documentation burden)
than the one the clinical relationship requires (diagnosis and care). AI enters
an already-misaligned system.

The honest question before introducing AI: does this tool fix the underlying
misalignment, or does it add another layer on top of it?

---

## Prediction Machines — Applied to Healthcare

The Prediction Machines framework (Agrawal, Gans, Goldfarb) argues that AI makes
**prediction cheap**. This reframes every AI application as a question about
what prediction enables and what complementary inputs it still requires.

Judge's three examples each reveal a different position in this framework:

### 1. ChestLink (Oxipit) — Chest X-ray Triage
- **What AI predicts:** normal vs abnormal across 75 pathologies
- **Prediction value:** high — most X-rays worldwide are normal; routing the
  normals autonomously frees radiologists for the abnormals
- **Human complement retained:** full radiologist involvement once any abnormality
  detected; final diagnosis and communication with patient
- **Structure:** AI as triage filter. The AI's prediction narrows the decision
  set for humans. This is a clear AI→human handoff model.

### 2. Retinal Scan → Parkinson's Prediction
- **What AI predicts:** retinal biomarkers correlated with Parkinson's, years
  before clinical symptoms
- **Prediction value:** extremely high in the cases where early intervention
  changes outcomes — cannot be done by human examination at all
- **Human complement:** compassionate diagnosis, treatment conversation,
  follow-up care. Judge is explicit: "it will never diagnose Parkinson's disease
  or provide compassionate care."
- **Structure:** AI extends the prediction frontier beyond what human senses
  can access. The complement is entirely human — not because humans are better
  at prediction here, but because prediction is not the whole job.

### 3. Med-PaLM / Medical LLM — Question Answering
- **What AI predicts:** answers to medical licensing exam questions; pattern
  matching across medical knowledge
- **Prediction value:** passing the licensing exam (67% → 86% in three months)
  is impressive as a benchmark, but the benchmark is a proxy for clinical
  judgment, not clinical judgment itself
- **Human complement:** the full clinical interaction — examination, context,
  relationship, uncertainty handling that exams don't test

The Prediction Machines insight: in healthcare, cheap prediction is most valuable
where prediction is currently impossible (retinal → Parkinson's), moderately
valuable where prediction is possible but slow (X-ray triage), and potentially
misleading where the benchmark proxy diverges from the real task (LLM exam
scores vs clinical practice).

---

## Shneiderman's HCAI Framework — Applied

Shneiderman's two-dimensional model asks: how much control does the AI have, and
how much human oversight is maintained? High reliability requires both automation
and oversight — not a trade-off between them.

Judge's examples map differently across this framework:

| System | Automation | Human Oversight | Assessment |
|--------|-----------|-----------------|------------|
| ChestLink (normal reports) | High — fully autonomous reporting | Minimal on normals, full on abnormals | Acceptable: stakes of a normal report are low; abnormals escalate |
| ChestLink (abnormals) | Low — passes to radiologist | Full | Correct position |
| Retinal prediction | High (pattern recognition) | High (required for diagnosis) | Good design — output is flagging, not diagnosis |
| Med-PaLM | Variable | Unclear in deployment | Risk zone if deployed without oversight protocols |

The ChestLink design is the most carefully constructed: it achieves full autonomy
only in the lowest-stakes scenario (confirming normal) and escalates every
uncertain case to human review. This is what "task sharing between AI and human
radiologists" means in practice — not splitting work randomly but splitting it
along stakes and certainty.

---

## The Trust Problem — Three Requirements

Judge names three conditions for responsible medical AI deployment:
**trust, explainability, and randomized clinical trials (RCTs).**

### Trust
The survey data is striking: over half of US respondents would feel anxious if
their healthcare worker relied on AI for treatment; 75% feared doctors would
move too fast. Trust in this context is not irrational resistance to technology.
It reflects a reasonable prior: healthcare decisions have irreversible consequences,
and patients have limited ability to audit the AI's reasoning.

Trust is not built by demonstrations that AI can pass medical exams. It is built
by transparent deployment with clear escalation protocols, patient communication
about what AI is and is not doing in their care, and accumulated evidence that
outcomes improve.

### Explainability
Judge raises confirmation bias explicitly: a doctor who sees an AI recommendation
may anchor to it without adequately weighing contradictory clinical evidence.
Explainable AI is not just a feature preference — it is a mechanism for
maintaining the independent clinical judgment that provides the check on AI error.

A black-box system that says "this is abnormal" is less useful than one that shows
which feature drove the classification, because the clinician can evaluate whether
the feature interpretation is plausible given the full clinical picture.

### Randomized Clinical Trials
This is the most structurally important point. Medical devices and pharmaceuticals
require RCTs before deployment — a control arm receiving standard care, a treatment
arm receiving the AI-augmented intervention, outcome comparison. Medical AI has
largely been deployed without equivalent evidence standards.

The licensing exam benchmark for Med-PaLM is not an RCT. It tests a specific
proxy. The actual question — does this system improve patient outcomes when
deployed in a real clinical setting with all the messiness that entails — requires
a different study design. The absence of RCTs for medical AI is the governance
gap that trust and explainability cannot substitute for.

---

## The Eyeball Test — What AI Cannot Replicate

Judge's observation that the "eyeball test" (direct patient observation) sometimes
outperforms sophisticated models is important for two reasons:

1. **Clinical context that data doesn't capture.** A patient who appears more
   distressed than their vital signs suggest; a family member's affect in the
   room; the way someone describes pain vs. the recorded pain score. These are
   inputs that current AI systems do not process and that experienced clinicians
   have learned to weight.

2. **The judgment call about what data to collect.** An experienced clinician
   decides in real time which information to pursue — which examination is
   warranted, which test is actually needed. AI systems are generally downstream
   of this decision; they process data already collected, not data the doctor
   decided to collect because something felt off.

This is not an argument against AI in healthcare. It is a constraint on where AI
adds the most value: processing structured data at scale, identifying patterns in
populations, extending prediction beyond what human senses can access. It does
not currently replicate the adaptive, multimodal, contextually sensitive judgment
that the clinical relationship requires.

---

## The Equity Argument — Honest Examination

Judge closes with an aspiration: multimodal AI could bring specialized care to
"remote corners of low and middle-income countries." This is a real possibility
worth examining honestly.

**What it would require:**
- Infrastructure for data collection and connectivity — not trivially available
  in the same settings that lack specialist care
- Regulatory frameworks in LMICs that can evaluate and approve AI medical devices
- Training for healthcare workers who will use the systems and interpret outputs
- Trust-building in populations who have often experienced extractive rather than
  beneficial technology transfer
- Business models that are not dependent on high-income-country reimbursement

**The risk:**
The equity aspiration is sometimes used to justify faster, less rigorous deployment
in LMICs than would be accepted in high-income settings. "It's better than nothing"
is not an evidence standard. The populations with least access to specialist care
are also the populations least able to detect and correct AI system failures.

The honest version of the equity argument: AI could reduce specialist care gaps
if deployed with the same evidence standards and oversight protocols applied in
high-income settings, at price points that health systems in LMICs can afford,
with infrastructure investment that precedes rather than follows deployment.

---

## Connection to the Knowledge Infrastructure

The 70/30 split problem has a direct analogue in research:

Researchers spend significant time reading, organizing, and contextualizing prior
work before making the actual judgment: is this claim credible? Is it connected
to this other finding? What does it imply for the design choice I am about to
make?

The claim-extraction classifier being built in this repository is an attempt to
shift the 70/30 ratio in the research reading task — not to automate the
judgment, but to make the information retrieval faster so more time is available
for the judgment. The parallel to ChestLink's triage function is exact:
route the clearly-categorizable inputs to a fast path, preserve human attention
for the cases that require it.

---

## Key Takeaways

1. **Frame the problem before introducing AI.** The 70/30 split is a systems
   design failure, not a human capability gap. AI that addresses the symptom
   without the structural cause may not improve the underlying situation.

2. **Task sharing, not task replacement.** The best healthcare AI designs split
   work along stakes and certainty, not randomly. Low-stakes, high-certainty
   decisions can be automated. High-stakes or uncertain decisions require
   human judgment.

3. **The benchmark is not the outcome.** Med-PaLM passing medical licensing exams
   is not evidence that it improves patient outcomes. The evidence standard for
   medical AI should match the evidence standard for medical intervention: RCTs.

4. **Explainability is a safeguard against confirmation bias, not a UX feature.**
   Doctors who see AI recommendations anchor to them. Showing the reasoning
   preserves independent clinical judgment.

5. **The equity argument requires the same evidence standards, not lower ones.**
   Populations with least access to specialist care are also those least able to
   detect and correct AI failures.

6. **The eyeball test is data too.** Not all clinical inputs are digitised. The
   AI-augmented future of medicine still depends on the clinician who decides
   what to observe and how to weight what they observe.
