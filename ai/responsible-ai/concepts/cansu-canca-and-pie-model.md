# Cansu Canca and the PiE Model

Research notes on the primary architect of the EAI Responsible AI framework.
Sources gathered via web research — to be expanded as papers and talks are read.

---

## Who She Is

Cansu Canca is a philosopher specialising in applied ethics, and the person most
responsible for the practical framework underpinning this course.

- **Director of Responsible AI Practice**, Institute for Experiential AI (EAI), Northeastern
- **Research Associate Professor**, Department of Philosophy and Religion, Northeastern
- **Founder and Director**, AI Ethics Lab (founded ~2016, Cambridge MA) — one of the first
  initiatives focused exclusively on advising practitioners on AI ethics
- **Founding Editor**, *AI & Ethics* journal (Springer Nature)
- **PhD**, Applied Ethics, National University of Singapore

Prior: University of Hong Kong Medical School (faculty), Harvard Law School, Harvard School
of Public Health, Harvard Medical School, WHO, Osaka University — all in population-level bioethics.

**Key external roles:**
- UN Centre for AI & Robotics — AI Ethics and Governance Expert
- INTERPOL — AI Ethics and Governance Expert (law enforcement applications)
- World Economic Forum AI Governance Alliance — working group member
- IEEE AI Experts Network Criteria Committee — chair
- Fortune 500 companies — ethics advisor
- EU- and NIH-funded research projects — ethics expert

**Links:**
- AI Ethics Lab: https://aiethicslab.com
- Personal site: https://cansucanca.com
- EAI profile: https://ai.northeastern.edu/our-people/cansu-canca
- Wikipedia: https://en.wikipedia.org/wiki/Cansu_Canca

---

## Background Worth Understanding

Her decade in **population-level bioethics** before AI is significant. Bioethics has
developed mature frameworks for exactly the questions AI ethics is still working out:

- How do you make decisions that affect populations, not just individuals?
- How do you handle uncertainty about harm in novel technologies?
- How do you govern research that outpaces regulation?
- What does informed consent look like at scale?

Bioethics is further along than tech ethics on most of these. Her AI ethics methodology
is almost certainly shaped by that lineage — worth keeping in mind when reading her frameworks.

---

## TEDxCambridge Talk — "How to Solve AI's Ethical Puzzles"

- **Event:** TEDxCambridgeSalon, November 2019
- **Published:** February 2020, ~18 minutes
- **TED.com:** https://www.ted.com/talks/cansu_canca_how_to_solve_ai_s_ethical_puzzles
- **YouTube:** https://www.youtube.com/watch?v=cplucNW70II
- **AI Ethics Lab page:** https://aiethicslab.com/tedx/

### Key Ideas (from description — not yet watched in full)

1. **Problem vs. puzzle reframe** — ethical challenges in AI are puzzles, not problems.
   Problems imply something broken needing a fix. Puzzles imply configurations requiring
   navigation. No single correct answer, but rigorous methods for finding principled ones.

2. **Concrete harms as entry points** — filter bubbles distorting political and health
   decisions; algorithmic bias in hiring discriminating against women; biased risk-assessment
   tools targeting minority populations in criminal justice.

3. **Applied philosophy as a practical toolkit** — not ethics as moral policing, but
   philosophy giving practitioners structured methods for evaluating trade-offs.

4. **Ethics integration, not ethics bolted on** — ethics should be woven into the innovation
   process from the start, not applied as an approval gate at the end.

*To expand: watch the talk and add specific arguments, examples, and structure.*

---

## The PiE Model — Puzzle-solving in Ethics

**Primary source:** https://aiethicslab.com/pie-model/
**Published description:** "Operationalizing AI Ethics Principles", *Communications of the ACM*,
Vol. 63 No. 12, pp. 18-21, 2020.
- ACM: https://cacm.acm.org/opinion/operationalizing-ai-ethics-principles/
- Preprint PDF: https://aiethicslab.com/wp-content/uploads/2020/08/Canca_AI-Principles_ACM.pdf
- YouTube lecture on PiE: https://www.youtube.com/watch?v=29pzpwlsWV4

### Core Philosophy

- Ethics in AI development is not a compliance exercise — it is collaborative puzzle-solving
- Steers away from **ethics policing** (checklists, approval gates) toward **ethics integration**
- Gives equal weight to **ethical risks** AND **ethical opportunities** — not just harm avoidance
- Grounded in applied ethics from moral and political philosophy, then layered with
  systems thinking and design methodology to make it actionable

### The Critical Distinction — Core vs. Instrumental Principles

This is the sharpest insight from her 2020 CACM paper:

Most AI ethics principle sets **improperly conflate** two different kinds of principles:

| Type | Examples | Nature |
|---|---|---|
| **Core principles** | Autonomy, Beneficence, Justice | The actual ethical values — what we are trying to achieve |
| **Instrumental principles** | Transparency, Accountability, Fairness | Mechanisms for achieving core values in specific contexts |

You cannot implement "justice" directly. You can implement transparency as a mechanism
that serves justice in a given context. Conflating these two levels is why most AI ethics
frameworks fail to operationalize — they treat instruments as if they were ends.

This also explains why "fairness" debates in AI go in circles: fairness is instrumental,
not foundational. Which core value is fairness serving? In this context? For whom?
Answer that first, then determine which fairness metric actually serves it.

### The Core vs. Instrumental Distinction — Full Argument (from CACM paper)

**The problem Canca identified:** Over 100 sets of AI ethics principles have been published.
None of them have proven helpful in guiding actual practice. The reason: they conflate two
fundamentally different kinds of principles without distinguishing them.

**Core principles** — encapsulate intrinsic values. Valuable for their own sake.
Drawn from moral and political philosophy:

- **Autonomy** — respect for persons as self-determining agents
- **Beneficence** — avoid harm, do good
- **Justice** — equal treatment, equal opportunity, protection of the worst off

These answer: *"Is this ethically problematic at all?"* Any action that disrespects autonomy,
inflicts harm, or discriminates is ethically problematic by definition.

Notably: across all published AI principles, globally and across industries, the distribution
is remarkably consistent — ~25-30% autonomy-focused, ~32-34% beneficence-focused,
~36-41% justice-focused. The content converges even when organisations don't coordinate.

**Instrumental principles** — valuable only because of what they achieve. Their value is
derived, not intrinsic:

- **Transparency** — valuable because it allows people to understand and audit systems,
  which upholds autonomy and justice. Not valuable in itself.
- **Accountability** — valuable because it assigns responsibility (justice) and deters harm
  (beneficence). Not valuable in itself.
- **Explainability** — valuable in some contexts (a bail risk-assessment tool — judges and
  defendants need to engage autonomously with the system) and unnecessary in others (an
  AI optimising fuel efficiency in cars — explainability should not be prioritised if it
  compromises accuracy and safety).
- **Fairness, Privacy, Consent** — all instrumental.

**The key operational implication:** Instrumental principles are **interchangeable**.
You can substitute one for another, or deprioritise one, if a different instrument better
serves the core value in context. There is no deep ethical dilemma when an instrumental
principle is not applicable.

But when **core principles conflict** — that is a genuine ethical dilemma. No checklist
resolves it. Ethics experts must be brought in to apply ethical theory.

Example from the paper: Developing an AI diagnostic system for a dangerous, rapidly
spreading disease. To minimise harm, you need large amounts of personal data quickly —
you cannot fully anonymise it, and seeking proper consent would delay the project and
cause more infections. But circumventing consent violates autonomy. Beneficence and
autonomy point in opposite directions. That is a real dilemma. Principles cannot resolve
it. Ethical theory and expert analysis must.

**The lineage:** This framework is explicitly drawn from bioethics — specifically the
*Belmont Report* (1978) and Beauchamp & Childress' *Principles of Biomedical Ethics* (1979),
which established autonomy, beneficence, non-maleficence, and justice as the canonical
core principles for human subjects research. Canca is importing a mature bioethics
framework into AI ethics, where it did not previously exist in this form.

### "The Box" — Practical Tool for Developers

A simplified checklist for developers to use for basic ethics analysis:

1. **Identify the ethical concern** — which core principle is at stake?
   (autonomy / beneficence / justice)
2. **Weigh instrumental principles** — which instruments apply here?
   Which can be substituted or deprioritised without violating the core value?
3. **Detect core conflicts** — do core principles point in opposite directions?
   If yes: this is a complex case. Bring in ethics experts. Do not try to resolve with
   a checklist.

The Box does not resolve hard cases — it tells you whether you have a hard case or a
manageable one. That distinction alone is valuable: most developers treat every ethics
question as equally complex (paralysis) or equally simple (rubber-stamp). The Box
calibrates which is which.

*Note: The visual figure of The Box did not render in the preprint PDF. The published ACM
version (Vol. 63 No. 12) likely contains it. Worth finding.*

### On the Proliferation of Principles

Why do companies publish their own principles if the content is largely the same?

Canca's answer: if well done, organisational principles serve to declare **priority orderings**
when core principles conflict and no single argument emerges as strongest after full analysis.
When push comes to shove — does this organisation prioritise individual autonomy or
minimisation of harm? The organisation's principles should answer that. They are not a
substitute for ethics analysis. They are a tiebreaker that reflects the organisation's
stated values when genuine dilemmas have no clean resolution.

This is a useful reframe: principles documents are not ethics frameworks. They are
declarations of priority in hard cases. Most organisations publish them as if they were
frameworks. That is the mismatch.

### Four Services of the PiE Model

| Service | Purpose |
|---|---|
| **AI Ethics Roadmap** | Assess current ethical readiness; design an integration plan |
| **AI Ethics Strategy** | Establish governance structures for recurring ethical questions |
| **AI Ethics Analysis** | Identify specific ethical puzzles; develop targeted solutions |
| **AI Ethics Training** | Equip practitioners to navigate ethical questions independently |

---

## *AI & Ethics* Journal (Springer Nature)

- **Link:** https://link.springer.com/journal/43681
- **Canca's role:** Co-founding editor
- **Focus:** Ethical, regulatory, and policy implications of AI — practical orientation,
  not purely theoretical

Coverage areas:
- Fairness, accountability, transparency in AI systems
- Bias in face recognition, hiring, risk assessment
- Weaponisation risks and dual-use concerns
- Privacy, autonomy, dignity
- Regulatory and governance frameworks
- AI in healthcare, education, law enforcement, creative industries
- Interdisciplinary research combining technical and humanistic perspectives

Explicitly cross-audience: academics, practitioners, policymakers, public.

---

## Other Published Work

- "Operationalizing AI Ethics Principles" — *Communications of the ACM*, 2020 (primary)
- "AI and Governance in Defence Innovation: Implementing an AI Ethics Framework"
  in *The AI Wave in Defence Innovation* (Routledge, 2023)
- "Ethical and Legal Aspects of Data Science for Large Scale Human Mobility"
  in *Data Science for Migration and Mobility* (Oxford University Press, 2022)
- "Did You Find It on the Internet? Ethical Complexities of Search Engine Rankings"
  in *Perspectives on Digital Humanism* (Springer, 2021)
- Writing in Forbes, Harvard Law School's Bill of Health blog, Petrie-Flom Center

---

## Open Threads to Follow

- [x] Watch TEDx talk — key argument: embed ethics into development, not as a gate;
      biomedical IRB comparison; data intimacy; notes in data-intimacy-and-ethics-limits.md
- [x] Read CACM paper — full notes added above, The Box visual figure still to find
- [ ] Watch PiE model YouTube lecture — more detail on the four-service structure
- [ ] Explore AI Ethics Lab site — what tools and resources are public?
- [ ] Look at *AI & Ethics* journal — what recent issues cover topics relevant to this course?
- [ ] Follow the bioethics lineage — how do bioethics frameworks (principlism, etc.)
      translate to AI ethics? Where do they fit well and where do they break?
