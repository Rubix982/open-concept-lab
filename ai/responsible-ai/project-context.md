# Project Context

This directory contains notes, animations, and research from a course on the
foundations of responsible AI, taken Fall 2026. The notes go significantly
beyond the course material — following threads wherever they lead rather than
stopping at the assigned reading.

---

## Who This Is For

Primarily personal notes for the author. Secondarily, anyone interested in
responsible AI who wants a perspective that includes political economy, Islamic
ethics, lived experience from Pakistan and South Asia, and genuine engagement
with the structural causes of AI governance failures — not just the technical ones.

---

## Three Ongoing Projects That Inform These Notes

### 1. Bau Lab Knowledge Infrastructure

Building a claim-level knowledge graph of AI research with Natalie and the
Bau Lab (David Bau's lab at MIT — interpretability, knowledge editing,
mechanistic understanding).

**The core design principles:**
- Non-profit structure with donor funding — removes investor pressure, makes
  researcher consent honest, qualifies for foundation funding
- Three-tier data strategy: build on fully open sources first (arXiv, OpenAlex,
  MIT-licensed), navigate paywalls through direct researcher contact, exclude
  anything that cannot be obtained with genuine consent
- Consent mechanism before indexing — contact researchers, show them how their
  work appears, ask for corrections, give opt-out. This is simultaneously ethical
  consent and Wizard of Oz UX testing
- The differentiator: "we built this honestly, on consent, for the research
  community, not for profit"

**Why this matters for responsible AI:**
The knowledge infrastructure is the honest version of what AI companies should
have built — data acquired with consent, researchers treated as stakeholders not
sources, non-profit mission aligned with public good. The litigation wave hitting
AI companies for scraped training data makes this model increasingly necessary
and increasingly valuable.

### 2. Cultural Dataset Business

A related business idea: building consented, culturally diverse datasets for
AI training — solving the dataset geography problem that produces the Ibn Rushd
failure (Western-centric training data that erases non-Western intellectual traditions).

**The moat:** Relationships, not data. Any company can scrape. No company can
replicate years of trust-based partnerships with Al-Azhar, Banaras Hindu University,
African cultural archives, and Indigenous community organisations at speed.
The race logic that dominates AI development is the enemy of the trust this requires —
which means the race cannot build what this project can build.

**The structure:** Four-layer model — dataset licensing, audit/certification,
custom construction for specific deployments, non-profit arm for sensitive
communities where commercialisation is inappropriate.

**The Bau Lab connection:** The knowledge infrastructure is the proof of concept
and the pilot. Same consent mechanism, same relationship-first approach, same
non-profit structure. Expand from research papers to cultural heritage using
what the pilot teaches.

### 3. The Course Itself

The course — Foundation of Responsible AI — provided vocabulary and entry points.
The discussions extended those into: neoliberalism as the operating system of AI
governance failures, Tarbiyat and epistemic honesty, the anthropological argument
against AGI, the KSA case study on productive struggle, Goodhart's Law and the
prestige trap in hiring, the 18 Microsoft guidelines applied to the knowledge
infrastructure, and the cultural dataset geography problem.

The course is a starting point. The notes are where the actual learning happened.

---

## Structure

```
responsible-ai/
├── course/          ← Per-topic notes (01-08 and growing)
├── concepts/        ← Standalone deep dives on specific ideas
├── animations/      ← Manim animations for key concepts
│   ├── shared/      ← Reusable lecture primitives
│   ├── 02_intelligence/
│   ├── 03_agi/
│   ├── 05_regulation/
│   └── 08_hcai/
├── requirements.txt
├── pyproject.toml
└── .flake8
```

## Key Threads Running Through Everything

- **The values problem** — AI governance requires values, values are contested,
  and the process of encoding values into AI systems currently hides that contest
  rather than resolving it
- **Excluded perspectives** — the people making decisions about AI are not the
  people who will live with the consequences. The room is too small.
- **No skin in the game** — Taleb's principle applied: those who cannot be harmed
  by their recommendations cannot be trusted to make them honestly
- **AI as entry point** — AI did not create inequality, it reveals it. The
  conversation AI starts should be directed at the systems that produced the
  data it learned from
- **The honest path was available** — in data collection, in governance, in product
  design. It was slower. It was chosen against. The costs are now arriving.
