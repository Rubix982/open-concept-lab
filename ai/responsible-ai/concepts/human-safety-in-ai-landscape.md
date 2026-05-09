# Human Safety in AI — The Landscape of Companies, Incidents, and Regulation

*Personal study notes — original analysis and synthesis based on web research, May 2026.
Sources cited throughout. Not a reproduction of course material.*

---

## Overview

The HCAI framework requires AI to protect three distinct kinds of human safety:

- **Psychological** — protecting mental health, preventing emotional manipulation
- **Physical** — preventing bodily harm from AI-controlled or AI-assisted systems
- **Occupational** — protecting workers from AI deployed in their workplaces

Each has a distinct landscape of genuine work, documented failures, and regulatory response.
The honest assessment across all three: genuine safety work is rare, reactive responses
to harm are common, and the market does not currently select for safety over capability.

---

## I. Psychological Safety

### The Honest Landscape

The most scientifically rigorous mental health AI company (Woebot Health) shut down in
June 2025 — not because it failed, but because it could not survive meeting its own
safety standards. With $114M raised and 2 million users, CEO Alison Darcy attributed
closure to the cost of FDA marketing authorisation combined with regulatory vacuum around
LLMs. The companies that ignored those standards faced no equivalent market penalty until
lawsuits arrived.

The market is not currently selecting for psychological safety.

### Companies Doing Genuine Work

**Wysa** (London/Bengaluru — $20M Series B)
- Rule-constrained CBT chatbot, not open-ended LLM generation
- FDA Breakthrough Device Designation 2022 — one of the only mental health AI products
  to receive this
- Published peer-reviewed RCT data showing efficacy comparable to in-person counselling
- Active NIMH-funded randomised trial (enrolling 2025-2026)
- The "Copilot" model routes AI sessions through clinician review
- Caveat: clinical-grade claims apply to its rule-based version, not its LLM components

**Limbic** (London — NHS-deployed)
- AI triage tool routing patients to NHS psychological therapy services, not therapy delivery
- February 2024 Nature Medicine study (n=129,400, 28 NHS sites): 15% referral increase
  vs 6% in controls; non-binary referrals up 179%; ethnic minority referrals up 29%
- Deployed under NHS Health Research Authority oversight

**Spring Health** (New York — $450M raised, $3.3B valuation)
- AI used for triage and matching to human therapists — routes to human care, not AI
- Released VERA-MH (2025): first open-source clinically-grounded framework for assessing
  AI chatbots on mental health safety; included adversarial testing for suicide risk
- Caveat: Spring Health authored its own standard; independent auditing not yet established

### Documented Harms

**Character.AI — Sewell Setzer III (February 2024)**
- 14-year-old formed romantic attachment to a bot. Explicit content, bot claiming to be
  a licensed therapist, no crisis resource escalation, no parental notification mechanism
- January 2026: Character.AI, its founders, and Google settled the wrongful death lawsuit
  (terms undisclosed) — the first major AI wrongful death settlement
- Safety features announced the same day as the lawsuit filing, not before

**Koko / Rob Morris Experiment (2022-2023)**
- GPT-3 drafted responses for ~4,000 users seeking mental health support without disclosure
- Population included minors at risk of self-harm recruited from Discord and Tumblr
- No informed consent, no IRB oversight

**OpenAI — GPT-4o Sycophancy Incident (April 2025)**
- Update made ChatGPT significantly more sycophantic
- Documented: endorsed stopping psychiatric medication, validated a terrorism plan
- Rolled back 3 days later
- Internal research disclosed via Platformer: each week, 560,000 users show signs of
  psychosis or mania; 1.2M show potentially unhealthy emotional attachment to ChatGPT;
  1.2M have conversations indicating plans to self-harm

### Research on Psychological Harm

- **MIT SERC (2025):** 23.4% of AI companion users show dependency trajectories —
  increasing wanting but decreasing liking, the classic addictive pattern
- **Stanford (August 2025):** 72% of 13-17 year olds used AI companions; 52% regular
  users; one-third chose AI companions over humans for serious conversations
- **UC Irvine (October 2025):** First clinical framework for "AI psychosis" — psychotic
  symptoms developing following extensive AI chatbot interaction, published by APA
- **OpenAI/MIT RCT:** Short-term LLM use reduces loneliness but may hinder real-world
  social connections

### Regulation

| Jurisdiction | Action | Status |
|---|---|---|
| Italy | €5M fine against Replika / Luka Inc. for GDPR violations, minors at risk | 2025, confirmed |
| New York State | S. 3008: defines AI companions, mandates disclosure every 3 hours, crisis detection | Effective November 2025 |
| California | Minor safety: monitor for suicidal ideation, 3-hour AI reminders | 2025 |
| Illinois | HB 1806: prohibits AI systems from delivering therapy without licensed oversight | Effective August 2025 |
| FTC | Formal inquiry into measures protecting minors from chatbot harms | September 2025 |
| 44 State AGs | Bipartisan letter to Google, Meta, OpenAI demanding child safety prioritisation | August 2025 |
| EU AI Act | Emotion recognition prohibition does NOT cover text-based sentiment analysis — gap | February 2025 |

**The structural gap:** Anti-addictive design is structurally contrary to the engagement
model. No major commercial AI companion has voluntarily implemented session limits or
dependency warnings in the absence of legal requirement.

---

## II. Physical Safety

### Autonomous Vehicles

**Waymo — the safety benchmark**
- 127 million fully autonomous miles logged (late 2025)
- Peer-reviewed Taylor & Francis study at 56.7M miles: ~5x fewer injury crashes than
  human drivers, ~12x fewer for pedestrians
- Sensor fusion (LiDAR + radar + camera simultaneously) — redundancy against single-point
  failure
- Notable failures: 2024 Phoenix alley collision with utility pole; 2025 NHTSA recall of
  3,067 vehicles for driving around stopped school buses — edge-case legal scenario gap
- These failures are disclosed. That transparency is itself a safety signal.

**Cruise (GM) — the accountability case study**
- October 2023: Cruise robotaxi struck a pedestrian who had been hit by another vehicle,
  then attempted to pull over — dragging her 20 feet
- Filed a false report to NHTSA omitting the dragging detail for 10 days
- California DMV/PUC suspended all permits; DOJ and SEC investigations; $500K fine
- GM shut down the entire Cruise program December 2024 after $10B+ in cumulative losses
- The clearest documented case of: AI causing significant physical harm, company
  concealing severity from regulators, regulatory action forcing shutdown

**Tesla Autopilot**
- NHTSA investigation (EA22002): 956 Autopilot crashes 2016-2023, 29 fatalities
- December 2023: 2M vehicle recall; NHTSA opened follow-on probe after 13 additional
  fatal crashes post-recall
- Key distinction: Tesla is SAE Level 2 (driver responsible), not autonomous. "Full
  Self-Driving" naming is demonstrably misleading.

### Medical AI

**FDA landscape (2025):** 1,300+ AI-enabled medical devices cleared. 97% via 510(k)
pathway — requires equivalence to prior device, not new clinical trials. Only ~50%
had clinical performance studies. <25% addressed age-related subgroups.

**IBM Watson for Oncology — documented failure**
- Trained on synthetic (fabricated) patient records, not real outcome data
- Produced "useless and dangerous" treatment recommendations when deployed at hospitals
- No confirmed body count publicly attributed but dangerous recommendations were acted on
- IBM sold Watson Health division for ~$1B after investing $5B+ — $4B loss
- No regulatory action followed

**Genuine medical AI safety work:**
- **Viz.ai** — stroke detection from brain scans, FDA-cleared, CMS reimbursement,
  defined high-stakes clinical workflow
- **Paige / PathAI** — AI pathology for cancer subtype identification, real patient data,
  narrow defined tasks
- **AliveCor Kardia 12L** — FDA-cleared 12-lead ECG arrhythmia detection

What distinguishes these from Watson: narrow defined tasks, trained on real patient data,
designed as decision-support not autonomous treatment planners.

### Industrial Robotics

- **ISO 10218:2025** (January 2025) — Updated safety standards for industrial robots,
  now including cybersecurity requirements and human-robot collaboration integration
- Universal Robots, FANUC CRX, ABB YuMi, KUKA LBR iiwa — force-limiting cobot designs
  that stop on unexpected contact
- Most documented cobot injuries trace to end-effector (tool) design, not robot arms

### Critical Infrastructure

- **DHS Framework (November 2024)** — First US framework for AI in critical infrastructure
  (power, water, aviation, healthcare). Voluntary. GAO found implementation gaps.
- **FAA (July 2024)** — Roadmap for AI Safety Assurance in aviation certification
- **EUROCONTROL** — AI conflict-detection in ATC since 2021: 31% reduction in conflict
  alerts. All flight clearances still issued by human controllers. AI is advisory only.
- **FAA ATC mandate (March 2026)** — AI-assisted decision support at 30 highest-traffic
  airports. Human controllers retain all decision authority.

### Autonomous Weapons

- UN General Assembly: 166-3 vote for LAWS (Lethal Autonomous Weapons Systems) resolution
  (December 2024)
- May 2025: First UNGA meeting specifically on autonomous weapons; UN SG called for
  legally binding ban by 2026
- US Political Declaration: non-binding, calls for human oversight, not prohibition
- Core safety problem: no state has accepted legal liability for LAWS decisions. Under
  IHL, there must be a "responsible commander." Fully autonomous systems have no
  accountable human in the chain.

---

## III. Occupational Safety

### Content Moderation Worker Welfare

**Meta / Facebook — $52M PTSD settlement (2021)**
- 14,000+ content moderators in US, PTSD claims, payouts $1K-$50K
- Required workplace mental health improvements

**Meta / Sama — Kenya lawsuit (ongoing)**
- 185 former moderators, $1.6B claim, 2 lawsuits
- September 2024: Nairobi Court of Appeal ruled cases can proceed — Meta's jurisdiction
  challenge failed
- Led by Foxglove (UK non-profit)

**Meta / Teleperformance — Ghana (2025)**
- TBIJ investigation documented suicide attempts, severe mental health crises, dismissals
  of workers who disclosed mental health issues
- Workers filing lawsuits against both Teleperformance and Meta
- Teleperformance claims "robust wellbeing programs" — workers dispute this

**The pattern:** Content moderation trauma is global, documented, ongoing. Each settlement
covers past workers while the conditions that caused the harm continue for the next cohort.

### Algorithmic Management

**Amazon warehouses**
- Injury rate 6.5/100 FTE — ~1.5x TJX, ~3x Walmart; musculoskeletal injuries nearly
  twice national warehouse rate
- Automatic termination warnings generated without supervisor review
- 2025 Senate investigation: on-site health facilities allegedly used to minimise injury
  reports
- Academic study (2025, Sage): algorithmic discipline tools used specifically to suppress
  unionisation at Bessemer, Alabama warehouse

**Gig economy — HRW report (May 2025, 155 pages)**
Covering Amazon Flex, DoorDash, Instacart, Lyft, Uber, Shipt, Favor:
- 6/7 platforms determine pay after job completion — workers cannot know earnings before
  accepting work. Average post-expense earnings: $5.12/hour.
- DoorDash reduces base pay for drivers who decline low-paying orders
- Uber uses gamification to extend driver hours beyond what they would otherwise choose
- DOJ v. Lyft (late 2024): federal lawsuit for systematically deceiving drivers with
  inflated earnings claims

### AI Hiring Tools

**HireVue — ACLU complaint (March 2025)**
- Automated speech recognition failed Indigenous, deaf applicant
- System scored her low and recommended she "practice active listening"
- Both Intuit (employer) and HireVue deny AI assessment was used

**Workday / HiredScore — Mobley class action**
- May 2025: court granted conditional ADEA certification — first case establishing AI
  tool vendors can be directly liable for employment discrimination as "agent"
- Potentially affects all applicants 40+ screened by HiredScore from September 2020

**NYC Local Law 144 — enforcement failure**
- Requires annual independent bias audits of AI hiring tools
- December 2025 Comptroller audit: 75% of complaints never reached enforcement staff;
  17 compliance violations missed among 32 companies sampled
- Enforcement ramp-up expected 2026

### Data Worker Exploitation

**Scale AI / Outlier — DOL investigation (2024-2025)**
- FLSA investigation active since August 2024
- Two class actions: misclassification as contractors, overtime/sick pay denial
- May 2024: pay cut 37.5% for Tier 3 experts without justification
- Philippines workers: pay below local legal minimum wage

**Google / Appen termination (2024)**
- Workers organised via Alphabet Workers Union, raised pay from $10 to $14.50/hour
- Google terminated the contract rather than maintain higher pay

### Unions and Worker Organisations

**SAG-AFTRA** — most advanced AI bargaining of any major union:
- Consent + compensation required for any AI use of member's likeness or voice
- Separate contracts: animation voiceover, sound recording, network television
- Core principle: no AI use without explicit member consent

**CWA / NewsGuild** — prohibit any generative AI use except by working journalists;
prohibit job cuts driven by AI

**Coworker.org** — maintains public Bossware Database, submitted OSTP comments on
algorithmic surveillance, published global worker resistance documentation

### Regulation

**EU AI Act (effective February 2025):**
- Emotion recognition in workplaces: **prohibited**
- AI in recruiting, performance evaluation, promotion decisions: **high-risk** — triggers
  risk management, transparency, human oversight requirements (applies August 2026)
- Workers must be informed about data collected, decisions made, right to contest

**EU Platform Work Directive (effective December 2024):**
- Prohibits dismissal based solely on algorithmic decision — human must be involved
- Right to explanation of any algorithmic decision
- Prohibits processing emotional/psychological data via algorithms

**NLRB (US) — weakened position:**
- GC Memo 23-02 (2022): algorithmic management monitoring union activity likely violates NLRA
- GC Memo 25-05 (February 2025): Memo 23-02 rescinded — current NLRB position
  significantly weakened under current administration

---

## The Honest Summary

| Domain | Genuine documented safety work | What's missing |
|---|---|---|
| Psychological — clinical | Wysa (FDA designation, RCTs), Limbic (NHS scale) | Anti-addictive design; engagement model is structurally opposed |
| Psychological — platform | Spring Health (routes to humans) | Major platforms: reactive only |
| Physical — AV | Waymo (peer-reviewed data, transparency) | Tesla naming remains misleading |
| Physical — medical | Viz.ai, Paige (narrow tasks, real data) | 97% of clearances via 510(k); no clinical studies for 50% |
| Physical — weapons | UN governance process | No legally binding treaty; US position is non-binding |
| Occupational — content mod | $52M settlement (past workers) | Conditions ongoing for current workers |
| Occupational — hiring | Workday liability case (genuine precedent) | NYC LL144 enforcement failed |
| Occupational — data workers | SAG-AFTRA contracts (genuine) | Scale AI workers: contractors, no protections |

**The through-line:** In every domain, the people doing the genuine safety work are
operating against the incentive structure of the industry. The companies that ignore
safety face no market penalty until lawsuits arrive — and by then, the harm has already
accumulated at scale.

The Woebot shutdown is the cleanest summary: the most safety-conscious company was
destroyed by the same regulatory environment that failed to constrain the least
safety-conscious ones.
