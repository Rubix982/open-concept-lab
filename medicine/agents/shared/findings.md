# Findings

Owned by: **Researcher**. Append-only. Every entry carries a confidence level,
and the orchestrator gates dependent tickets on it (high → implement freely;
medium → spike first; low → no implement ticket until a follow-up R- raises it).

Standing rule (T-009): a figure appears here only if its source was actually
retrieved in-session. Anything written from model knowledge is labelled as
such and carries confidence `low` regardless of how confident it feels.

---

## [R-004] Finding: needle decompression is less settled than the page implies

_Date: 2026-09-27 · Confidence: **high** for the disagreement and the pooled
figures; **medium** for how to act on them, because the underlying
heterogeneity is extreme._

**Primary source, retrieved via NCBI E-utilities:**
Ahmad SJS, Degiannis JR, Head M, Ahmed AR, Gelber E, Hakky S, et al.
“Meta-analysis of the optimal needle length and decompression site for tension
pneumothorax and consensus recommendations on current ATLS and ETC guidelines.”
*World Journal of Emergency Surgery* 2025;20. PMID 40383767.
DOI 10.1186/s13017-025-00613-7. 51 studies; radiological subset 24 studies,
n = 8046.

### What it actually says

- **The guidelines disagree with each other.** ATLS (10th edition, 2018)
  moved the preferred site to the 4th/5th intercostal space at the anterior
  axillary line. The European Trauma Course and the Royal College of Surgeons
  of Edinburgh continue to recommend the 2nd intercostal space,
  midclavicular line. The paper exists *because* of this conflict.
- **Needle decompression fails about a third of the time.** Pooled failure of
  penetration into the pleural cavity: **32.84%** — with I² = 99.72%, which is
  as heterogeneous as a pooled estimate gets and should be read as "failure is
  common" rather than as a number.
- **Length is the dominant variable, not site.** Each additional centimetre of
  needle reduced failure by **7.76%**. Recommended length: **7 cm**.
- **Chest wall thickness** at the 5th anterior axillary and 5th midaxillary
  lines is less than at the 2nd midclavicular line — so the anatomical premise
  behind the ATLS change holds.
- **But the anterior axillary line had higher injury rates than midaxillary**,
  with strong correlation between needle length and injury at both
  (0.88, 0.91). Longer needle, better penetration, more injury.
- **Laterality matters.** Their recommendation: 7 cm needle at 5th midaxillary
  *or* 2nd midclavicular for **right-sided**; for **left-sided**, 2nd
  midclavicular is safer because of the risk of cardiac injury.

### What this corrects in the shipped document

1. The page presents the landmark change as settled trauma guidance. It is
   **contested between guideline bodies**, and saying so is more accurate and
   more interesting than picking a winner.
2. The page names the **anterior** axillary line specifically. This
   meta-analysis found higher injury rates there than at the midaxillary line.
3. The page gives no **laterality** distinction. Left-sided decompression
   carries a cardiac injury risk that changes the recommended site.
4. The page specifies **14 gauge**, which is a diameter and says nothing about
   length — and length is the variable that actually predicts failure. This is
   the largest omission: the panel teaches a site debate while the evidence
   says the more important question was how long the needle is.
5. "The needle buys minutes" is safe, but the page implies reliability that a
   ~33% penetration failure rate does not support.

### Open

The ATLS 11th edition (if published) has not been checked. The failure-rate
heterogeneity means the 32.84% figure should be quoted as "roughly a third,
with enormous variation between studies", never as a point estimate.

## [R-002] Finding: the arrest drugs are far weaker than the page implies

_Date: 2026-09-27 · Confidence: **high** on the trial results; **medium** on how
to phrase the clinical bottom line, because the field itself has not settled it._

### Adrenaline — PARAMEDIC2

Perkins GD, Ji C, Deakin CD, Quinn T, et al. “A Randomized Trial of Epinephrine
in Out-of-Hospital Cardiac Arrest.” *N Engl J Med* 2018. PMID 30021076.
DOI 10.1056/NEJMoa1806842. Double-blind, placebo-controlled, n = 8014.

- Survival to 30 days: **3.2% vs 2.4%** (OR 1.39, 95% CI 1.06–1.82, P = 0.02).
- Survival to hospital admission: **23.6% vs 8.0%** — a very large effect.
- Favourable neurological outcome at discharge: **2.2% vs 1.9%**, not
  significant (OR 1.18, 95% CI 0.86–1.61).
- Among survivors, **severe neurological impairment was more common** with
  adrenaline: **31.0% vs 17.8%**.

Read plainly: adrenaline restarts hearts and delivers many more patients to
hospital, and does not clearly produce more people who leave it intact. The
extra survivors are disproportionately severely impaired. This is one of the
most uncomfortable results in resuscitation and the page currently presents
"a round of epi" as routine bookkeeping.

### Amiodarone — ALPS and after

Kudenchuk PJ et al., ALPS: amiodarone n = 974 (survival to discharge 24.4%),
lidocaine n = 993 (23.7%), placebo n = 1059 (21.0%) — **the primary comparison
was not significant.**

- Bayesian reanalysis: Lane D, Grunau B, Kudenchuk P, Dorian P, et al. *Heart*
  2022. PMID 35236764. DOI 10.1136/heartjnl-2021-320513. Probability of improved
  survival with amiodarone 83–95% depending on prior; estimated absolute gain
  **2.9% (IQR 1.4–3.8)**. Lidocaine more modest.
- Route analysis: Daya MR, Leroux BG, Dorian P, Rea TD, et al. *Circulation*
  2020. PMID 31941354. DOI 10.1161/CIRCULATIONAHA.119.042240. **Intravenous**
  amiodarone improved survival to discharge vs placebo (adjusted RR 1.26,
  95% CI 1.06–1.50; absolute difference 5.5%, 95% CI 1.5–9.5). **Intraosseous**
  amiodarone did not (adjusted RR 0.94, 95% CI 0.66–1.32). Placebo outcomes did
  not differ by route, so the access route is not just marking sicker patients.
  The trial was underpowered for the interaction and the authors do not claim
  effect modification.

### End-tidal CO₂

Touma O, Davies M. “The prognostic value of end tidal carbon dioxide during
cardiac arrest: a systematic review.” *Resuscitation* 2013. PMID 23871864.
DOI 10.1016/j.resuscitation.2013.07.011. 23 observational studies. ETCO₂ during
CPR was consistently higher in patients who achieved ROSC. Supports the ~10 mmHg
(1.33 kPa) landmark the page uses — but the evidence base is observational, and
ETCO₂ must never be the sole basis for stopping.

### What this corrects in the shipped document

1. **"Round of epi"** is presented as neutral procedure. The honest version is
   that it buys circulation and possibly not personhood, and that this is
   actively debated.
2. **Amiodarone 300 then 150** is presented as settled. The primary trial was
   null; the case for it rests on a reanalysis and a subgroup.
3. **The glossary says IO "takes anything a vein takes."** ALPS's route analysis
   is direct evidence against that for arrest antiarrhythmics. This is a
   specific, checkable error on the page.
4. The ETCO₂ threshold survives, with its evidential status downgraded to
   observational.

---

## [R-002a] Note on method

The AHA 2020 numeric landmarks used in the document — compression rate 100–120,
depth 5–6 cm, shock 120–200 J, rhythm check every 2 minutes — were **not**
retrieved in this session. They remain `low` confidence under the T-009 rule and
must stay marked unverified until the guideline document itself is fetched.

## [R-006] Finding: three trauma/shock landmarks, two of them null

_Date: 2026-09-27 · Confidence: **high** on the trial results. Note the pattern:
two of the three headline practices the page states flatly were **negative on
their primary outcome** and survive on secondary endpoints._

### MAP ≥ 65 — SEPSISPAM

Asfar P, Meziani F, Hamel JF, Grelon F, et al. “High versus low blood-pressure
target in patients with septic shock.” *N Engl J Med* 2014. PMID 24635770.
DOI 10.1056/NEJMoa1312173. Multicentre, open-label, n = 776; MAP 80–85 vs 65–70.

- 28-day mortality **36.6% vs 34.0%** (HR 1.07, 95% CI 0.84–1.38, P = 0.57).
  90-day also not significant.
- Higher target caused **more new atrial fibrillation**.
- Prespecified subgroup: patients with **chronic hypertension** needed less
  renal-replacement therapy at the higher target — no mortality difference.

So "target a MAP of 65" is well founded as a *floor*, and the page is right to
use it. What the page should not imply is that 65 is an optimum: pushing higher
was tested and bought nothing except atrial fibrillation, except possibly in
chronically hypertensive kidneys.

### 1:1:1 — PROPPR

Holcomb JB, Tilley BC, Baraniuk S, Fox EE, et al. “Transfusion of plasma,
platelets, and red blood cells in a 1:1:1 vs a 1:1:2 ratio and mortality in
patients with severe trauma.” *JAMA* 2015. PMID 25647203.
DOI 10.1001/jama.2015.12. n = 680, 12 level I trauma centres.

- **Primary outcome was null.** 24-hour mortality 12.7% vs 17.0% (P = .12);
  30-day 22.4% vs 26.1% (P = .26).
- Death by **exsanguination** was significantly lower with 1:1:1: 9.2% vs 14.6%
  (P = .03), and more patients achieved haemostasis: **86% vs 78%** (P = .006).
- No excess in any of 23 prespecified complications despite much more plasma
  and platelets.

The page states 1:1:1 as the standard. Accurate as practice; the justification
is "fewer patients bleed to death and more stop bleeding", not "it lowers
mortality", because the mortality comparison did not reach significance.

### TXA — CRASH-2

Roberts I, Shakur H, Coats T, Hunt B, et al. CRASH-2. *Health Technol Assess*
2013. PMID 23477634. DOI 10.3310/hta17100. n = 20,211 across 274 hospitals in
40 countries; TXA 1 g over 10 min then 1 g over 8 h, within 8 hours of injury.

The page's "TXA within 3 hours" is consistent with the trial's own timing
analyses, but the precise time-stratified effect estimates were **not retrieved
in this session** and must stay marked unverified.

### What this corrects in the shipped document

1. The drug board asserts **MAP ≥ 65** as a target. Keep it, but it is a floor
   validated by a trial that found no benefit to going higher.
2. The drug board asserts **1:1:1** flatly. Its own trial was null on mortality.
   The honest claim is about exsanguination and haemostasis.
3. **TXA within 3 hours** is carried forward as unverified pending the
   time-stratified numbers.
4. A pattern worth stating in the document itself: much of resuscitation rests
   on secondary endpoints of negative trials. That is not a scandal — it is what
   evidence looks like in a field where the primary outcome is death and the
   effect sizes are small — but a reference that hides it is lying by omission.

## [R-003] Finding: the induction-agent claim on the page is backwards

_Date: 2026-09-27 · Confidence: **high**. This is the clearest factual error
found so far, and it is one the page repeats because the folk version is
extremely widely believed._

### Ketamine does not hold the pressure up in the critically ill

Andriazzi et al. “Etomidate Versus Ketamine for Emergency Intubation in
Critically Ill Patients: An Updated Meta-Analysis and Systematic Review.”
*J Intensive Care Med* 2026. PMID 42299661. DOI 10.1177/08850666261460825.
Six RCTs, n = 4108 (ketamine 2046, etomidate 2062), GRADE-assessed.

- 28-day mortality: **28.7% vs 29.9%**, RR 0.96 (95% CI 0.87–1.05) — no
  difference. Also no difference in the sepsis subgroup (n = 1546).
- **Post-intubation hypotension was MORE common with ketamine**: 14.2% vs
  11.3%, RR 1.25 (95% CI 1.01–1.53), I² = 0%.
- Ketamine reduced adrenal suppression: 5.3% vs 14.7%, RR 0.36 (0.17–0.75).
- No difference in peri-intubation cardiac arrest or first-attempt success.

**The page says ketamine "tends to hold the blood pressure up; the shock-state
choice." The pooled randomised evidence says the opposite on the one outcome
that phrase is about.** The mechanism is known: ketamine is sympathomimetic in
people with catecholamine reserve, and in a shocked, catecholamine-depleted
patient its direct myocardial depressant effect can dominate. The page teaches
the healthy-volunteer pharmacology as if it were the resuscitation-room result.

### Etomidate's adrenal suppression is real; its mortality effect is not shown

Bruder EA, Ball IM, Ridi S, Pickett W, et al. “Single induction dose of
etomidate versus other induction agents for endotracheal intubation in
critically ill patients.” *Cochrane Database Syst Rev* 2015. PMID 25568981.
DOI 10.1002/14651858.CD010225.pub2. Adrenal suppression is established; whether
it changes mortality remained unclear. The 2026 meta-analysis above is
consistent: measurable adrenal suppression, no mortality signal.

### Succinylcholine vs rocuronium

Tran DTT, Newton EK, Mount VAH, Lee JS, et al. “Rocuronium versus
succinylcholine for rapid sequence induction intubation.” *Cochrane Database
Syst Rev* 2015. PMID 26512948. DOI 10.1002/14651858.CD002788.pub3. 50 trials,
n = 4151.

- Succinylcholine was **superior for excellent intubating conditions**:
  RR 0.86 (95% CI 0.81–0.92) — i.e. rocuronium achieved them less often.
- For *clinically acceptable* conditions the gap was much smaller:
  RR 0.97 (95% CI 0.95–0.99), n = 3992, 48 trials.
- Moderate-quality evidence: high detection bias and significant heterogeneity.

The page's framing (same onset, different duration) is roughly right on
duration but omits that succinylcholine still produces better intubating
conditions, and that the difference shrinks to near-nothing if the bar is
"acceptable" rather than "excellent".

### Carried forward (R-010)

Succinylcholine and rocuronium **onset and duration figures**, and all doses
quoted on the page, were not individually sourced. Still `low` confidence.

---

## [R-005] Finding: lung ultrasound beats the x-ray by more than the page claims

_Date: 2026-09-27 · Confidence: **high**._

Alrajab S, Youssef AM, Akkus NI, Caldito G. “Pleural ultrasonography versus
chest radiography for the diagnosis of pneumothorax: review of the literature
and meta-analysis.” *Crit Care* 2013. PMID 24060427. DOI 10.1186/cc13016.
13 studies met inclusion.

- **Ultrasound: sensitivity 78.6%** (95% CI 68.1–98.1), **specificity 98.4%**
  (97.3–99.5).
- **Chest radiograph: sensitivity 39.8%** (29.4–50.3), specificity 99.3%.
- Significant heterogeneity by operator, probe type, consecutive vs convenience
  sampling, and trauma vs non-trauma setting.

### What this corrects

1. The reasoning bench's lung-ultrasound preset is **88 / 99**, marked `u1`
   unverified. The real pooled figure is **78.6 / 98.4**. Replace and cite.
2. The lung-sliding section frames ultrasound as finding a pneumothorax
   "before the x-ray". The stronger and now-sourced claim is that the
   **x-ray misses about 60% of them**. Speed was never the main argument.
3. Specificity ~98% supports the page's claim that a positive is meaningful;
   sensitivity ~79% supports its caveat that absent sliding is unreliable.

---

## [R-008] Finding: boarding and mortality — real, consistent, observational

_Date: 2026-09-27 · Confidence: **medium**. The association is robust and
repeatedly found; causal language is not supported._

Singer AJ, Thode HC, Viccellio P, Pines JM. “The association between length of
emergency department boarding and mortality.” *Acad Emerg Med* 2011.
PMID 22168198. DOI 10.1111/j.1553-2712.2011.01236.x. Retrospective cohort,
41,256 admissions.

- In-hospital mortality rose with boarding time: **2.5%** for boarding under
  2 hours to **4.5%** at 12 hours or more (p < 0.001).
- Mean hospital length of stay rose from **5.6 to 8.7 days**.
- Both persisted after adjustment for comorbidity.

Single-centre, retrospective, and adjustment cannot exclude that sicker
patients board longer. `design-e002-flow.md` §5 already requires "associated
with", never "causes" — this finding confirms that rule was the right call.

## [R-007] Finding: the monitor numbers, and one place the page was already right

_Date: 2026-09-27 · Confidence: **high** for shock index and hyperoxia,
**medium** for GCS (confounding by indication is severe), **incomplete** for
lactate._

### Shock index — the threshold on the page is not the threshold in the evidence

Vang M, Østberg M, Steinmetz J, Rasmussen LS. “Shock index as a predictor for
mortality in trauma patients: a systematic review and meta-analysis.”
*Eur J Trauma Emerg Surg* 2022. PMID 35258641. DOI 10.1007/s00068-022-01932-z.
38 cohort studies; 12 pooled, n = 348,687.

- SI **≥ 1** vs < 1: pooled RR of in-hospital mortality **4.15** (95% CI
  2.96–5.83). **Overall quality of evidence: low.**

Carsetti A, Antolini R, Casarotta E, Damiani E, et al. “Shock index as
predictor of massive transfusion and mortality in patients with trauma.”
*Crit Care* 2023. PMID 36872322. DOI 10.1186/s13054-023-04386-w. 35 studies,
n = 670,728.

- For predicting massive transfusion: sensitivity **0.68** (0.57–0.76),
  specificity **0.84** (0.79–0.88), AUC **0.85** (0.81–0.88).

The page uses **> 0.9** as the action threshold and **< 0.7** as normal. The
pooled literature is built on **≥ 1**. More importantly, sensitivity 0.68 means
it misses roughly a third of patients who go on to need massive transfusion —
so it is a flag, not a screen, and the page should not imply it catches the
compensated patient reliably. It catches some of them.

### Oxygen — the page treats a two-sided problem as one-sided

Damiani E, Adrario E, Girardis M, Romano R, et al. “Arterial hyperoxia and
mortality in critically ill patients: a systematic review and meta-analysis.”
*Crit Care* 2014. PMID 25532567. DOI 10.1186/s13054-014-0711-x. 17 studies.

- Hyperoxia associated with increased mortality after **cardiac arrest**
  OR 1.42 (1.04–1.92), **stroke** OR 1.23 (1.06–1.43), **traumatic brain
  injury** OR 1.41 (1.03–1.94). ICU data not pooled, I² = 96.73%.

You J, Fan X, Bi X, Xian Y, et al. *J Crit Care* 2018. PMID 30077082.
DOI 10.1016/j.jcrc.2018.07.014. 3 RCTs + 26 cohorts, n = 257,223.
Crude OR 1.42 (1.26–1.61); **adjusted OR 1.20 (1.09–1.32)**; RCT-only
OR 1.36 (1.04–1.77).

The page gives SpO₂ 94–98% and says they move when it falls below 90%. It never
says why there is an **upper** bound. There is one, and it is the interesting
half: after cardiac arrest, stroke and head injury, too much oxygen is
associated with dying more. Oxygen is a drug with a therapeutic window, not a
resource to maximise.

### "GCS 8, intubate" — the page's hedge was correct, and is now sourced

Hatchimonji JS, Dumas RP, Kaufman EJ, Scantling D, et al. “Questioning dogma:
does a GCS of 8 require intubation?” *Eur J Trauma Emerg Surg* 2021.
PMID 32382780. DOI 10.1007/s00068-020-01383-4. National Trauma Data Bank 2016,
n = 6676 with GCS 6–8, inverse probability weighted regression adjustment.

- Intubation within 1 h associated with **increased** mortality: OR 1.05
  (95% CI 1.03–1.06); similar with and without head injury.
- ICU length of stay **+14%**; total length of stay **+27%**.
- Authors' conclusion: a strict GCS threshold mandating intubation "should be
  revisited."

**Read this carefully.** It is observational, confounding by indication is
severe (sicker patients get intubated), and OR 1.05 is a very small effect. It
does not show intubation causes harm. What it does show is that there was never
evidence *for* the rule. The page already says "a prompt, not a rule — the real
question is whether they can protect the airway." That stands, and can now cite
a source.

### Lactate — incomplete

Gu W-J, Zhang Z, Bakker J. *Intensive Care Med* 2015. PMID 26154408
(no abstract retrieved). Pan J, et al. *Medicine* 2019. PMID 30813144 —
7 RCTs, n = 1301, lactate-clearance-guided vs ScvO₂-guided resuscitation;
**the effect estimates were truncated in retrieval and are not recorded here.**

The page's "lactate > 4" and "clearance matters more than any single value"
remain `low` confidence. Carried into R-010.

## [R-010] Finding: TXA has a cliff, and ESI performs better than expected

_Date: 2026-09-27 · Confidence: **high** for TXA timing; **medium** for ESI
(single-centre validation, not a pooled estimate)._

### TXA — "within 3 hours" is not a target, it is a cliff

Roberts I, Shakur H, Afolabi A, Brohi K, et al. “The importance of early
treatment with tranexamic acid in bleeding trauma patients: an exploratory
analysis of the CRASH-2 randomised controlled trial.” *Lancet* 2011.
PMID 21439633. DOI 10.1016/S0140-6736(11)60278-X. n = 20,211; 1063 deaths from
bleeding.

Effect on **death due to bleeding**, by time from injury to treatment
(test for interaction **p < 0.0001**):

| Time to treatment | TXA | Placebo | RR (95% CI) |
|---|---|---|---|
| **≤ 1 h** | 5.3% | 7.7% | **0.68** (0.57–0.82), p < 0.0001 |
| **1–3 h** | 4.8% | 6.1% | **0.79** (0.64–0.97), p = 0.03 |
| **> 3 h** | 4.4% | 3.1% | **1.44** (1.12–1.84), p = 0.004 |

No evidence the effect varied by systolic blood pressure, GCS or injury type.

The page says "TXA within 3 hours of injury". True, and it badly undersells the
finding. **After three hours the point estimate reverses and suggests harm.**
This is not a deadline after which benefit fades — it is a sign change. The
correct framing is "early or not at all", and it is one of the cleanest
time-dependent treatment effects in trauma medicine. This is an *exploratory*
subgroup analysis, which is the standard caveat, but the interaction test is
very strong and it has shaped practice worldwide.

### ESI reliability and validity

Cairós-Ventura L, et al. “Validity and Reliability of the Emergency Severity
Index in a Spanish Hospital.” *Int J Environ Res Public Health* 2019.
PMID 31752212. DOI 10.3390/ijerph16224567. n = 240.

- Discriminating urgent cases: sensitivity **89%** (85–93), specificity **97%**
  (94–99), PPV 68% (62–74), **NPV 99%** (98–100).
- Inter-rater agreement between nurses: **kappa 0.94** (0.84–0.99).

Also located: Tanabe P, et al. “Reliability and validity of scores on The
Emergency Severity Index version 3.” *Acad Emerg Med* 2004. PMID 14709429.

Relevant to the unbuilt Part III: ESI is more reproducible than a triage
instrument might be assumed to be, and its NPV for urgency is very high. Single
Spanish centre, adapted locally — do not present as a pooled estimate.

---

## [R-009] BLOCKED: the AHA guideline numerics could not be retrieved

_Date: 2026-09-27 · Confidence: **none** — this is a record of failure, not a
finding._

### What was established

- **A 2025 edition exists.** Wigginton JG, Agarwal S, Bartos JA, Coute RA,
  et al. “Part 9: Adult Advanced Life Support: 2025 American Heart Association
  Guidelines for CPR and ECC.” *Circulation* 2025. PMID 41122884.
  DOI 10.1161/CIR.0000000000001376. Also Part 1 Executive Summary
  (PMID 41122893) and Part 11 Post-Cardiac Arrest Care (PMID 41122894).
- **The document is built on 2020-era teaching** (Panchal AR, et al., Part 3,
  *Circulation* 2020, PMID 33081529).
- From the retrieved 2025 abstract, the new guidelines add guidance on
  **double sequential defibrillation**, **head-up CPR**, **point-of-care
  ultrasound in ALS**, and **refined termination-of-resuscitation rules**.
  None of these appear anywhere in the document.

### Why it is blocked

The numerics — compression rate, depth, rhythm-check interval, defibrillation
energy, adrenaline interval — are not in the PubMed abstracts. The full text on
ahajournals.org returns **HTTP 403**, as does the official highlights PDF on
cpr.heart.org (both direct fetch and curl with a browser user agent).

Secondary summaries from CPR-training vendors are freely available and were
**deliberately not used**. Under the T-009 rule they would be a citation that
looks sourced and is not.

### Consequence

The most-repeated numbers in the document remain unverified, and the document
may additionally be one guideline generation out of date. This is now the
single largest evidential gap in the project. Needs the PubMed MCP, an
institutional route, or manual retrieval.
