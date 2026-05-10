# Frameworks and Guidelines

Academic and industry HCAI frameworks — what they say, what they commit to,
and where they fall short. Read together, these notes reveal a consistent pattern:
the frameworks are increasingly sophisticated at sounding committed while remaining
minimally accountable.

---

## [Cansu Canca and the PiE Model](cansu-canca-and-pie-model.md)
The most rigorous practitioner framework in the field. Canca's key insight: most AI
ethics principle sets improperly conflate **core principles** (autonomy, beneficence,
justice — intrinsic values) with **instrumental principles** (transparency, accountability,
fairness — mechanisms). You cannot implement "justice" directly; you implement transparency
as a mechanism that serves justice in a specific context. The Box: a practical checklist
that distinguishes hard ethical dilemmas (core principles conflict) from manageable ones
(instrumental principles can be substituted). CACM 2020 paper fully documented.

## [Microsoft 18 Guidelines for Human-AI Interaction](microsoft-18-guidelines-hcai.md)
The most empirically validated HCAI framework. 18 guidelines distilled from 150+
recommendations, tested against 20 AI products by 49 HCI practitioners. Key findings:
G11 (explain why) is the most violated despite the most research; G5/G6 (social norms,
social biases) are invisible to evaluators who don't experience the norms being violated.
The meta-irony: the guidelines most requiring diverse evaluators were tested by the
least diverse pool. Includes full application table mapping all 18 to the knowledge base.

## [Google PAIR Guidebook](google-pair-guidebook.md)
The bridge document between UX and ML teams. Six chapters covering user needs, mental
models, explainability, feedback/control, errors, and data collection. Distinctive for
treating the reward function as a design artifact — not an ML implementation detail.
Confirmed by two peer-reviewed academic analyses (CHI 2023, HCII 2021). Strongest on
data practices and reward function; weakest on accountability and structural fairness.
The participatory aspiration is genuine; the participatory mechanism is thin.

## [Google AI Principles](google-ai-principles.md)
The full history matters: published June 2018 under employee pressure after Project Maven
(4,000 signatures, 12 resignations). Original 7 objectives included explicit prohibitions
on weapons and surveillance. In February 2025, Google quietly removed those prohibitions
and replaced them with the current three-principle structure — same week Trump revoked
Biden's AI safety EO. Senators Markey, Merkley, and Welch formally demanded explanation.
Critical analysis: what the principles actually commit Google to vs. what real accountability
would require. The principles were never more binding than the pressure that produced them.

## [IBM AI Design Fundamentals](ibm-ai-design-fundamentals.md)
The most operationalised framework. Three layers: Design Ethics (5 focal areas),
Trustworthy AI Pillars (5 technical pillars), Team Essentials (5 practice activities).
IBM's distinguishing contribution: Carbon for AI — explainability as a mandatory UI
component standard that ships in product code, not just documentation. Open source
toolkits AIF360 and AIX360 are genuine, well-maintained, and predate most competitors
(AIF360 released 2018). Honest gap: operationalisation without binding enforcement.

## [Stanford HAI and CHAI Berkeley](stanford-hai-and-chai-berkeley.md)
Two founding institutes with fundamentally different approaches. Stanford HAI (2019):
convening institution, AI Index as flagship output, normative and broad definition —
augment not replace, present time horizon. CHAI Berkeley (2016, Stuart Russell): technical
alignment problem, "provably beneficial by construction," value uncertainty built into
the objective function, long-term and existential time horizon. Key distinction: HAI
asks what AI should do for humanity; CHAI asks how to build AI that cannot diverge from
human values. CHAI's alumni network runs the major AI safety organisations.

## [Xu's HCAI Framework and Application](xu-hcai-framework-and-application.md)
Wei Xu (Intel, 2019). Three-wave AI history showing first two waves failed not from
technology immaturity but from ignoring human needs. Extended HAI framework: ethically
aligned design + technology enhancement + human factors design. Critical distinctions:
explainability vs comprehensibility (XAI built for data scientists is useless to users),
AI-first UCD (design the human-machine task allocation before the interface), Wizard of Oz
prototyping. Includes honest critique: the human override requirement is nearly impossible
in real-time contexts (automation complacency). Application to knowledge base: full
mapping of methodology to the Bau Lab project.
