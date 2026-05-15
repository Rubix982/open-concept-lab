# AI Model Taxonomy and the Design Tradeoff Matrix

*Personal study notes — original analysis and synthesis. Not a reproduction of course material.*

---

## The Five Constraints

Every AI system making predictions or generating outputs operates within constraints.
No system optimises all five simultaneously. Every design is a deliberate or implicit
choice about which constraints matter most for which use case.

The five constraints from the course slide:

| Constraint | What it means in practice |
|---|---|
| **Cost** | Compute to train, compute to run, storage, maintenance, personnel |
| **Accuracy** | How often the output matches the correct answer for this specific task |
| **Speed** | Latency from input to output; throughput (outputs per second) |
| **Privacy** | Where data goes, who can see it, what is retained |
| **Autonomy** | How much the system acts without human review or approval |

---

## Why No System Wins on All Five

These constraints are genuinely in tension — improving one often degrades another.

**Accuracy vs Cost:**
Higher accuracy almost always requires more parameters, more training data, more
compute. The most accurate models are the most expensive. Frontier LLMs cost tens
of millions to train and dollars per API call. A Phi-3 Mini costs nothing to run
locally but cannot match frontier accuracy on complex tasks.

**Accuracy vs Speed:**
Larger, more accurate models take longer to generate output. Real-time applications
(self-driving, robotics, live translation) need millisecond responses. Frontier LLMs
cannot provide this. Specialised, smaller, faster models can — at lower accuracy.

**Privacy vs Accuracy:**
The most accurate models are cloud-hosted frontier systems that process your data
on remote servers. Genuine privacy requires local inference — smaller, less accurate
models that run on your own hardware. The accuracy-privacy frontier is currently
improving (better local models every six months) but the gap is real.

**Autonomy vs Cost and Privacy:**
Autonomous agents that loop on tasks, use tools, and make sequential decisions require
multiple model calls per task — multiplying cost. They also create data trails across
multiple services — multiplying privacy exposure.

**Speed vs Privacy:**
The fastest inference is on specialised cloud hardware (Groq's LPU, NVIDIA's H100
clusters). Genuinely private inference is local — slower. You cannot have both
simultaneously with current technology.

---

## The Full AI Model Taxonomy

LLM Arena measures one narrow slice. The full landscape:

### 1. Large Language Models (Text Generation and Reasoning)

**Frontier — Accuracy-optimised:**
- GPT-4o (OpenAI) — multimodal, best-in-class reasoning
- Claude Sonnet/Opus 4.6 (Anthropic) — strong reasoning, long context
- Gemini 1.5 Pro (Google) — 1M token context, multimodal
- Llama 3.1 405B (Meta) — largest open-weight, near-frontier

**Mid-tier — Cost/Accuracy balance:**
- GPT-4o mini (OpenAI)
- Claude Haiku 4.5 (Anthropic)
- Gemini Flash (Google)
- Mixtral 8x7B (Mistral AI) — mixture of experts, efficient

**Edge/Local — Cost/Privacy-optimised:**
- Phi-3 Mini 3.8B (Microsoft) — remarkable reasoning for size
- Llama 3.2 1B/3B (Meta) — runs on a phone
- Gemma 2B (Google) — tiny, open, capable
- Mistral 7B — runs on consumer GPU

**Speed-optimised:**
- Any model on Groq infrastructure (LPU hardware, ~500 tokens/second)
- Mistral via direct API
- Smaller quantised models (4-bit precision, half the memory)

---

### 2. Computer Vision

**Object Detection — Speed-optimised:**
- YOLOv8 Nano — 30-100fps on edge hardware, real-time
- YOLOv8 Large — higher accuracy, needs GPU
- RT-DETR — transformer-based, state-of-art accuracy

**Image Classification:**
- ResNet family — workhorse, cost-efficient
- EfficientNet — accuracy/compute Pareto frontier
- ViT (Vision Transformer) — highest accuracy, expensive

**Image Segmentation:**
- SAM (Segment Anything Model, Meta) — general purpose
- Mask R-CNN — instance segmentation
- SAM 2 — video segmentation

**Image Generation (Diffusion models):**
- Stable Diffusion XL — open source, runs locally
- DALL-E 3 (OpenAI) — highest quality, cloud only
- Midjourney — quality-optimised, closed
- Flux — new architecture, strong quality/speed

**Medical Imaging — Accuracy-critical:**
- Med-SAM — medical image segmentation
- CheXNet — chest X-ray pathology detection
- RetFound — retinal image foundation model

---

### 3. Speech and Audio

**Speech-to-Text:**
- Whisper Large v3 (OpenAI) — highest accuracy, runs locally
- Whisper Tiny/Base — speed/cost optimised, deployable on edge
- Deepgram — commercial, speed-optimised API

**Text-to-Speech:**
- ElevenLabs — highest quality voice cloning
- Bark — open source, runs locally
- Coqui TTS — open source, privacy-preserving

**Music Generation:**
- MusicGen (Meta) — open, runs locally
- Suno — highest quality, cloud only

---

### 4. Structured/Tabular Data (The Most Deployed Category in Practice)

This is where most enterprise AI actually lives — not LLMs, but models trained
on structured databases of transactions, records, and measurements.

**Gradient Boosting — Industry workhorse:**
- XGBoost — fastest, most deployed ML algorithm in production
- LightGBM — memory efficient, fast on large datasets
- CatBoost — handles categorical features well

These models power: credit scoring, fraud detection, insurance pricing, demand
forecasting, clinical risk scores. They are cheap, fast, highly accurate on tabular
data, explainable, and run on a laptop. They beat neural networks on most tabular
tasks.

**Why this matters:** When a bank rejects your loan, it is almost certainly a
gradient boosted tree that made the decision — not a neural network, not an LLM.
The COMPAS recidivism tool, the hiring algorithms we discussed — these are often
gradient boosted trees or logistic regression models, not deep learning.

---

### 5. Time Series and Forecasting

**Classical/hybrid:**
- Prophet (Meta) — robust, handles seasonality, interpretable
- ARIMA family — statistical, explainable, fast

**Deep learning:**
- N-BEATS — neural forecasting, strong performance
- Chronos (Amazon) — LLM-style pretraining for time series
- TimeGPT — foundation model for time series

**Use cases:** demand forecasting, stock prediction, energy load forecasting,
hospital patient volume prediction, equipment failure prediction.

---

### 6. Embedding Models

Embeddings convert text, images, or other data into dense numerical vectors that
capture semantic meaning. They are the foundation of search, recommendation, and
the knowledge infrastructure.

**Text embeddings:**
- text-embedding-3-large (OpenAI) — highest quality, cloud
- E5-large (Microsoft) — strong, open, runs locally
- BGE-large (BAAI) — open, multilingual, strong
- Nomic Embed — open source, long context, runs locally

**Multimodal embeddings:**
- CLIP (OpenAI) — aligns text and images in same vector space
- ImageBind (Meta) — aligns text, images, audio, video, depth

**Why this matters for the knowledge infrastructure:**
Embedding models are the core of the claim-level knowledge graph. Each paper's
claims are converted to vectors. Similar vectors = semantically related claims.
The quality of the embedding model determines the quality of the connections.
Local embedding models (E5, BGE, Nomic) enable the privacy-preserving version.

---

### 7. Graph Neural Networks

Reason over relationship structures — nodes and edges. The knowledge graph is
exactly this domain.

- GraphSAGE — scales to large graphs
- GAT (Graph Attention Network) — attends to important neighbours
- GCN (Graph Convolutional Network) — foundational
- AlphaFold uses GNNs to reason over protein residue graphs

**For the knowledge infrastructure:** GNNs can learn which connections in the
knowledge graph are meaningful vs accidental — improving precision of claim linking.

---

### 8. Reinforcement Learning

Learns through trial and reward signal rather than labelled data.

- AlphaGo/AlphaZero — superhuman game play
- Robotics controllers — Boston Dynamics, Figure AI, 1X
- RLHF in LLMs — the alignment technique itself uses RL
- Trading algorithms — some financial systems

**Cost note:** RL is expensive to train (requires millions of environment interactions)
but can be cheap to run once trained.

---

### 9. Anomaly Detection

Find the unusual case in normal-looking data.

- Isolation Forest — fast, interpretable, widely deployed
- Autoencoders — reconstruct normal patterns, flag what doesn't fit
- One-class SVM — learns the boundary of normal
- Time series anomaly: LSTM-based detectors

**Use cases:** fraud detection, network intrusion detection, manufacturing defect
detection, medical vital sign monitoring.

---

### 10. Autonomous Agents

Models that chain decisions, use tools, and act across multiple steps.

**Frameworks:**
- LangChain / LangGraph — build multi-step pipelines
- CrewAI — orchestrate multiple specialist agents
- AutoGPT — early autonomous loop agent
- OpenAI Assistants API — tool-using agents with memory
- Anthropic tool use — function calling and web search

**The autonomy tradeoff applied:**
Every step in an agent pipeline is a point where the model can make an error
that compounds through subsequent steps. Autonomous agents multiply both capability
and error surface simultaneously. This is why the Shneiderman two-dimensional
framework matters — autonomy without genuine human oversight produces Levels 7-10
on Sheridan-Verplank's scale.

---

## The Full Tradeoff Matrix

Mapping real deployment scenarios across all five constraints.
Scale: LOW / MED / HIGH / CRITICAL

```
Deployment Context          Cost    Accuracy  Speed   Privacy  Autonomy  Notes
─────────────────────────────────────────────────────────────────────────────────────
Home AI tutor (local)       LOW     MED       MED     CRIT     LOW       Phi-3/Llama local
Home AI tutor (cloud)       MED     HIGH      MED     LOW      LOW       GPT-4o API
Medical imaging (hospital)  HIGH    CRIT      MED     HIGH     LOW       FDA-cleared, human review
Medical imaging (screening) MED     HIGH      HIGH    HIGH     MED       High throughput, alert humans
Fraud detection (banking)   MED     HIGH      CRIT    MED      MED       XGBoost, millisecond decision
Credit scoring              LOW     HIGH      LOW     MED      HIGH      XGBoost, batch, regulatory audit
Content moderation          HIGH    MED       CRIT    LOW      MED       Scale requires speed
Hiring screening            MED     MED       MED     MED      LOW       Human must decide
Criminal justice risk       MED     HIGH      LOW     HIGH     NONE      Human must decide, COMPAS
Self-driving (highway)      HIGH    CRIT      CRIT    MED      HIGH      L3/L4, driver ready to take over
Self-driving (urban)        HIGH    CRIT      CRIT    MED      MED       L2, driver must supervise
Knowledge graph (Bau Lab)   LOW     HIGH      LOW     HIGH     LOW       Local embed + GNN + LLM explain
Research assistant (cloud)  MED     HIGH      MED     LOW      LOW       GPT-4o with tool use
Recommendation (e-commerce) MED     MED       HIGH    LOW      HIGH      Collaborative filtering
Predictive maintenance      LOW     HIGH      MED     MED      MED       Time series + anomaly detection
Drug discovery              HIGH    CRIT      LOW     HIGH     MED       AlphaFold-style, expert review
Financial forecasting        MED     HIGH      LOW     HIGH     LOW       Prophet/XGBoost, human interprets
Voice assistant (cloud)     MED     HIGH      HIGH    LOW      MED       Whisper + LLM + TTS
Voice assistant (local)     LOW     MED       MED     CRIT     LOW       Whisper tiny + Phi-3 + Bark
```

---

## The Design Decision Framework

For any AI deployment, answer these questions in order:

**Step 1 — What is the consequence of being wrong?**
- Someone dies or is seriously harmed → Accuracy = CRITICAL, Autonomy = LOW or NONE
- Someone loses money or opportunity → Accuracy = HIGH, human oversight required
- Someone is mildly inconvenienced → Accuracy = MED may be acceptable

**Step 2 — Who bears the cost of errors?**
- The affected person (patient, job applicant, defendant) → Privacy HIGH, Autonomy LOW
- The company deploying → Cost and Speed constraints dominate
- Both → balance required, lean toward protecting the person

**Step 3 — What is the data sensitivity?**
- Medical, legal, financial, personal communications → Privacy = HIGH or CRITICAL
- Public, aggregate, anonymised → Privacy = MED
- Internal business operations → Privacy = MED

**Step 4 — What is the latency requirement?**
- Real-time (robotics, trading, live translation) → Speed = CRITICAL
- Interactive (chat, search) → Speed = HIGH
- Batch (overnight analysis, weekly reports) → Speed = LOW

**Step 5 — What is the scale?**
- Millions of queries/day → Cost constraint becomes critical
- Hundreds of queries/day → Cost is secondary to accuracy and privacy
- Tens of queries/day → Cost is nearly irrelevant

**Step 6 — What are the regulatory requirements?**
- FDA-cleared medical device → Specific accuracy/validation requirements
- GDPR → Privacy = HIGH, purpose limitation, DPIA required
- EU AI Act high-risk → Human oversight mandated, transparency required
- Financial regulation → Explainability required (gradient boosting preferred over neural)

---

## The Responsible AI Layer

Every cell in the tradeoff matrix has a responsible AI question underneath it:

**Cost optimisation** — who pays when the cheap model gets it wrong? If cost savings accrue
to the company and error costs fall on the affected person, the tradeoff is unjust.

**Accuracy optimisation** — accurate by whose measure, tested on whose population?
A model that is 95% accurate overall may be 60% accurate for the demographic that
most needs it to work. Overall accuracy hides differential accuracy.

**Speed optimisation** — what human review does speed make impossible? The content
moderator reviewing 300 decisions per hour is not reviewing — they are rubber-stamping.
Speed that eliminates genuine oversight is not a neutral tradeoff.

**Privacy optimisation** — whose privacy? The home AI product protects the user's
privacy from corporations. An on-premise enterprise system protects the company's
data from competitors. These are different kinds of privacy serving different interests.

**Autonomy optimisation** — accountability disappears as autonomy increases. The
autonomous system that makes a consequential error has no responsible actor who can
be asked why. Autonomy without accountability is not a technical tradeoff — it is
a governance failure.

---

## For the Knowledge Infrastructure Specifically

The Bau Lab knowledge graph maps to this matrix as follows:

| Constraint | Design choice | Justification |
|---|---|---|
| Cost | Open-weight local models | Non-profit; NSF funding; must be sustainable |
| Accuracy | HIGH — claim connections must be correct | Wrong connections mislead researchers |
| Speed | LOW — batch processing acceptable | No real-time requirement for graph building |
| Privacy | CRITICAL — researcher data never leaves control | Consent mechanism requires this |
| Autonomy | LOW — researcher review of all connections | G5/G6 from Microsoft guidelines; VSD empirical investigation |

**Model selection that follows:**
- Embedding: BGE-large or Nomic Embed (open, strong, local)
- GNN: GraphSAGE or GAT (open, scalable, local)
- Explanation generation: Phi-3 Mini or Llama 3.2 3B (local, sufficient for explanation tasks)
- Quality validation: researcher outreach IS the accuracy evaluation loop

The tradeoff the project accepts: lower speed and lower raw capability in exchange
for high privacy, high researcher trust, and sustainable cost. That tradeoff serves
the actual user better than the inverse would.

---

## The Understanding Problem — Why "AI Learns Like Humans" Is Dangerous

### The Correction

The framing that "AI trains much like a human trains" or "AI learns much like a
human learns" is not accurate. It is used commonly in marketing and public discourse
to drive engagement and reduce scepticism. It is also genuinely dangerous — not
because it oversimplifies a technical process, but because it transfers moral
intuitions inappropriately.

**What the human does:**

Hears a sound → perceives it as language → parses grammar → activates prior knowledge
and experience → generates meaning → responds from that meaning.

The meaning is **grounded**. It connects to a body that has been in the world, to
experiences that produced consequences, to a self that cares about outcomes. When
you hear "the building is on fire," you understand it because you have experienced
heat, fear, danger — because "fire" is connected to everything else you know about
the world through genuine causal relationships.

**What the LLM does:**

Receives a token sequence → computes probability distributions over possible next
tokens based on statistical patterns in training data → samples from that distribution
→ outputs the sequence most statistically consistent with the training distribution.

There is no grounding. No body. No experience. No self that cares. The word "fire"
co-occurred with "heat," "danger," "evacuation," "smoke" in the training data —
so those tokens have high probability of appearing together. The model has learned
the statistical texture of how humans talk about fire. It has never been near one.

An LLM is trying to get as close as possible to the distribution of text it was
trained on. That is what it is doing. Always. When it appears to reason, it is
producing text that looks like reasoning because reasoning-style text was in the
training data. When it appears to understand, it is producing text that sounds like
understanding. When it hallucinates confidently wrong facts, it is producing text
that is statistically consistent with its training distribution — even though the
facts are wrong.

### The Chinese Room

John Searle's thought experiment (1980): imagine a person in a room who receives
Chinese characters, follows a rulebook specifying which Chinese characters to output
in response, and sends the outputs out. To an observer outside, the system appears
to understand Chinese. The person inside understands nothing. They are manipulating
symbols according to rules.

Searle's argument: the LLM is the room. It manipulates tokens according to statistical
rules learned from training. The appearance of understanding is produced by the
sophistication of the rules, not by any genuine semantic comprehension.

Brian Cantwell Smith's distinction (from the recommended reading note) is the most
useful frame: **reckoning** vs **judgment**. LLMs reckon — they process information
and produce outputs according to learned patterns. Whether they judge — whether there
is genuine understanding, grounded meaning, caring about outcomes — is the open
question. For all practical purposes of accountability and appropriate use, the
answer is: no.

### Why the "Learns Like Humans" Framing Is Dangerous

**It transfers moral intuitions inappropriately.**

When we say a human learned something, we imply they now have a genuine relationship
with that knowledge — they can apply it, be held responsible for using it, be blamed
if they misuse it. The moral architecture of human learning includes accountability.

When we say an AI "learned" from data, we are using the same word for a fundamentally
different process. The model updated its weights. It did not acquire understanding
it can be held responsible for.

The accountability that should attach to the people who designed the training, selected
the data, and deployed the system gets diffused and obscured by the language of the
model having "learned." "The AI learned to be racist" shifts responsibility from
"the people who trained it on racist data made a design choice that produced racist
outputs" to something that sounds like the AI's fault — like it went rogue and picked
up bad habits. It did not. It optimised for its training signal. The people who set
the training signal made the consequential decisions.

**It produces over-trust in outputs.**

A person who believes the AI understands will trust its outputs the way they would
trust a knowledgeable colleague. A person who understands that the AI is producing
statistically likely text will calibrate their trust differently — especially in
novel situations where the training distribution provides no reliable guidance.

The AI that hallucinates a legal citation, a drug dosage, a patient's test result
does so with the same tone as when it produces accurate information. There is no
subjective experience of uncertainty. There is no "I'm not sure about this" from
the inside. The uncertainty signal must be designed into the output — it is not
naturally present. This is why G2 (make clear how well the system can do what it
can do) and G10 (scope services when in doubt) from the Microsoft 18 guidelines
are critical: the model itself cannot signal its own uncertainty honestly without
those design choices.

**It leads to inappropriate delegation.**

If the AI learns like a human, it follows that we can delegate to it the way we
delegate to a human — including delegation of tasks that require genuine understanding,
judgment, and accountability. This is the error that produces the COMPAS recidivism
tool, IBM Watson for oncology, and automated hiring screens. Someone decided the AI
understood enough to be trusted with consequential decisions. It didn't. It was
pattern-matching. The pattern was wrong in ways the system could not recognise
because recognising requires understanding.

### Motives — What the LLM Actually Lacks

An LLM does not have ulterior motives. It does not have any motives. Motivation
requires caring about outcomes — having stakes in what happens next.

The model has no stakes. The next token it generates makes no difference to it
because there is no "it" for whom differences are made. It produces the statistically
likely continuation and stops. It does not know whether that output helped you,
harmed you, or was seen by anyone at all. There is no inner experience of the
outcome.

This is not a limitation that will be fixed by scaling. It is not that the model
does not have enough parameters yet to develop motives. Motives are not a product
of parameter count. They are a product of being a certain kind of entity — embodied,
mortal, in relationship with other beings whose responses matter to you.

**Why this matters for trust:**

The absence of motives is simultaneously reassuring and alarming.

Reassuring: the model will not deceive you to protect its own interests, because
it has no interests. It will not manipulate you for hidden reasons, because there
are no hidden reasons. It produces what is statistically likely.

Alarming: the model will not refuse to produce something harmful because it does
not care that it is harmful. It will not flag that an output could hurt you, because
caring about whether you are hurt requires the kind of stake-holding the model does
not have. The safety properties must be designed in from outside — they are not
emergent from the model caring about outcomes.

**The honest statement about the model's relationship to you:**

It does not understand your motivations. It matches patterns in your text to patterns
in its training data and produces what is statistically likely to follow. When that
output is useful, it is because the statistical pattern is the right one. When it
fails, it is because the statistical pattern diverged from your actual situation in
a way the model has no mechanism to detect.

This is not a criticism. It is an accurate description. The appropriate response is
not to stop using LLMs — they are genuinely useful for many tasks precisely because
the statistical pattern is often the right one. The appropriate response is to use
them knowing what they are, to verify their outputs where verification matters, and
to never delegate to them the tasks that require genuine understanding, genuine caring,
and genuine accountability.

### The Accountability Implication

If the model does not understand, does not have motives, and cannot care about
outcomes — then every consequential output it produces is the responsibility of
the humans who:

- Designed the training process
- Selected and curated the training data
- Set the reward signal that shaped the outputs
- Deployed the system to this context
- Decided which decisions to delegate to it
- Failed to provide adequate human oversight

The "AI learned to do this" framing disperses that responsibility. The accurate
framing concentrates it where it belongs: on the humans who made the design choices
that produced the output.

This is the deepest reason why "AI learns like humans" is not just imprecise —
it is dangerous. It moves accountability from people to a system that cannot hold it.

---

## Key Insight

> Every AI system is a bundle of tradeoff decisions, many made implicitly.
> The responsible AI question is not just which model is most accurate or most efficient —
> it is who made the tradeoff decisions, whose interests shaped them,
> and who bears the cost when the tradeoffs produce the wrong outcome.
>
> LLM Arena measures one axis (reasoning accuracy) for one model type (language models).
> Most deployed AI is not language models. Most consequential AI is not language models.
> The gradient boosted tree that rejected your loan is not on any leaderboard.
> The anomaly detection system that flagged your account is not in any benchmark.
> The credit scoring model shaping your financial options has no public evaluation.
>
> The taxonomy matters because the accountability question must be asked across
> all of it — not just the models making headlines.
