# Dr. Agata Lapedriza — Research Profile

*Research notes compiled from web search, DBLP, arXiv, and institutional sources.*

---

## Who She Is

**Agata Lapedriza Garcia** — Associate Research Professor at Northeastern University's
Institute for Experiential AI (EAI) + Khoury College of Computer Science, and Professor
at Universitat Oberta de Catalunya (UOC, Barcelona). MIT CSAIL affiliated researcher.

**Career trajectory:**
- PhD, Universitat Autònoma de Barcelona — Extraordinary PhD Thesis Award 2009
- 2012–2015: Visiting Professor, MIT CSAIL (Torralba lab — where the Places work happened)
- 2017–2020: Visiting Professor, MIT Media Lab, Affective Computing Group (Picard lab)
- 2020–2021: Visiting Faculty, Google
- 2022–2023: Contractor, Apple Machine Learning Research
- Current: Northeastern EAI + UOC

**The through-line:** Computer vision → scene understanding → what neural networks
actually learn → emotion and social signal recognition from visual data → AI for wellbeing.

---

## Research Focus

Building AI systems capable of analyzing and interpreting emotions, social signals,
experiences, behaviours, and context from visual data, language, and wearable sensors.
She collaborates with clinical psychologists, cognitive scientists, neuroscientists,
and medical professionals.

**Core domains:**
- Affective computing — emotion recognition from face, body, scene context, video
- Computer vision — scene understanding, object detection, image classification
- Deep learning interpretability / explainable AI — network dissection
- Social robotics — robots for wellbeing coaching
- NLP — cultural representations of emotion in LLMs
- Humanitarian AI — disaster/incident detection from social media images

---

## Key Publications — What She Actually Found

### Foundational Scene Understanding (MIT CSAIL, Torralba lab)

**Places: An Image Database for Deep Scene Understanding** (2016)
10 million scene photographs with semantic category labels. One of the most widely
cited scene understanding datasets. She is a core co-author.

**Object Detectors Emerge in Deep Scene CNNs** (ICLR 2015)
Networks trained purely for scene classification spontaneously develop internal
object detectors — no object supervision needed. A foundational finding about
what neural networks learn without being told to learn it.

**Learning Deep Features for Discriminative Localization** (2015)
Global average pooling enables CNNs to localise the discriminative regions in images
without location-labelled training data. Foundational for weakly-supervised detection.

**Are all training examples equally valuable?** (2013)
Proposed ranking training examples by value. Classifiers improve when trained on
ranked subsets rather than whole datasets. Directly relevant to the dataset quality
argument — not more data, better data.

---

### Interpretability and Network Dissection

**Understanding the Role of Individual Units in a Deep Neural Network**
*Proceedings of the National Academy of Sciences, 2020*
Co-authored with David Bau, Torralba, and others. Presented the "network dissection"
framework: systematically identifies what semantics individual hidden units encode
in classification and GAN models. Applied to adversarial attack analysis and semantic
image editing.

**Bau Lab connection:** David Bau is a co-author on this paper. This is the mechanistic
interpretability lineage — understanding what individual units in a network actually
represent. The Bau Lab's current work on knowledge editing and causal tracing is
downstream of this foundational interpretability approach.

**Automated Detection of Visual Attribute Reliance with a Self-Reflective Agent**
*(NeurIPS 2025)*
Introduced a self-reflective agent that iteratively generates and tests hypotheses
about which visual attributes a model relies on. Validated on CLIP and YOLOv8 across
130 models. This is the automated version of the human-in-the-loop evaluation we
need for fairness auditing.

---

### Emotion Recognition

**Context Based Emotion Recognition using EMOTIC Dataset**
*IEEE Transactions on Pattern Analysis and Machine Intelligence*
Created the EMOTIC dataset: people in natural settings annotated with 26 discrete
emotion categories plus valence/arousal/dominance. Key finding: scene context
meaningfully improves emotion recognition beyond faces alone.

This matters: AI that reads only the face misses most of what is actually happening.
Context — where you are, what is around you — is doing most of the work.

---

### LLMs and Cultural Emotion — Critical Evaluation

**Analyzing Cultural Representations of Emotions in LLMs through Mixed Emotion Survey**
*(ACII 2024 — Best Paper Award)*
Administered mixed-emotion surveys to five LLMs. Found models show "limited alignment
with evidence in the literature" and that written language influences responses more
than speaker origin.

**Expressing Social Emotions: Misalignment Between LLMs and Human Cultural Emotion Norms**
*(arXiv 2026, under review)*
Extended cross-cultural study — European American vs. Latin American participants vs.
LLM outputs. All models over-express engaging emotions.

**What this means:** LLMs do not represent human emotional experience — they represent
the statistical texture of how English-language internet text discusses emotion. This
is the understanding problem from topic 11 applied to affective computing: the model
does not feel, it produces text that statistically resembles descriptions of feeling.
The cultural alignment failure is the dataset geography problem applied to emotion.

---

### Humanitarian and Social Impact

**Detecting natural disasters, damage, and incidents in the wild** *(ECCV 2020)*
**Incidents1M** *(IEEE TPAMI 2023)*
~977,000 images covering 43 incident types + 49 place categories. Disaster detection
from social media imagery — a genuine use case where AI provides value to communities
with limited resources.

**A Robotic Positive Psychology Coach to Improve College Students' Wellbeing**
*(RO-MAN 2020 — Best Paper Award)*
Deployed social robot in dorms. Statistically significant improvements in psychological
wellbeing, mood, and readiness to change. The robot-as-wellbeing-coach use case —
adjacent to the My AI concern but in the context of a research intervention with
IRB oversight and measured outcomes, not an engagement-maximising product.

---

## Notable Collaborations

- **Antonio Torralba** (MIT CSAIL) — most frequent collaborator, 2013–2025
- **David Bau** (formerly MIT, now UW) — network dissection PNAS paper
- **Rosalind Picard** (MIT Media Lab Affective Computing) — driver stress, robotic wellbeing
- **Bolei Zhou** — Places database, object detection papers
- **Aude Oliva** (MIT CSAIL) — Places and localization

---

## What This Research Means for the Course

**Generative vs. Predictive AI:**
Lapedriza's work is primarily on predictive/discriminative AI — emotion recognition,
scene classification, interpretability of classifiers and GANs. Her recent LLM work
(2024–2026) is evaluative and critical: examining where LLMs fail to match human
behavioural patterns, not building them.

Her perspective on generative AI is likely grounded in this: she has spent a career
understanding what discriminative models actually learn, and she can read the cultural
alignment failures of LLMs as exactly the dataset geography and understanding problems
we have documented throughout this course.

**The network dissection connection to the Bau Lab:**
The PNAS 2020 paper — understanding what individual units encode — is the foundational
interpretability work that the Bau Lab's mechanistic interpretability research builds
on. Lapedriza is in the lineage of the research that the knowledge infrastructure
project is grounded in. The Bau Lab connection is direct.

**The training data quality finding:**
"Are all training examples equally valuable?" (2013) — the answer is no. This is
the empirical grounding for the cultural dataset argument: more data from a biased
distribution does not fix the problem. Better, more representative, consented data
does.

---

## Key Insight

> Lapedriza's career is a through-line from "what do neural networks actually learn?"
> to "what do they fail to learn about human emotion and cultural experience?"
>
> The network dissection work showed that networks learn more than they are told to.
> The LLM cultural alignment work shows that they learn less than they appear to.
> Both findings point at the same gap: the statistical texture of the training data
> is not the same as the human experience the data describes.
>
> The understanding problem from topic 11, stated as a research programme.
