# Home AI — Privacy-First Local Intelligence for Families and Students

*Personal study notes — a business concept connecting privacy-by-design,
educational AI, and the knowledge infrastructure work at the Bau Lab.*

---

## The Gap

A capable AI assistant that:
- Never transmits queries, conversations, or data outside the home network
- Runs on consumer hardware with no command-line setup required
- Is specifically designed for educational and home use cases
- Can be verified as privacy-preserving because the firmware is open source
- Updates automatically with curated open-weight models

This product does not exist well yet. The pieces exist. The packaging for the
non-technical consumer does not.

---

## Why Now

**Open-weight models have crossed the usefulness threshold.**
Phi-3 Mini, Llama 3.2 3B, Qwen 2.5 3B — these run on consumer hardware and are
genuinely useful for the educational use cases that matter: homework help, reading
comprehension, mathematical reasoning, question answering, writing feedback.
They are not GPT-4o. They are capable enough to be valuable for a student at
any level from primary school through university.

**The harm narrative is visible and documented.**
Character.AI. My AI on Snapchat. The OpenAI internal research disclosing 1.2M
users per week with potentially unhealthy AI attachment. The generation that
grew up with social media — now becoming parents — has direct experience with
what engagement-maximising platforms do to their children. They will pay for
an alternative that is privacy-preserving by architecture, not by policy.

**The hardware cost has dropped to consumer price points.**
Apple Silicon, mid-range GPUs, even the Raspberry Pi 5 can run useful local
models. A dedicated home AI device can be produced at a price point comparable
to a NAS or a home server — not cheap, but within reach for the families who
are already spending money on educational AI subscriptions.

**No one has packaged this for the non-technical consumer.**
Synology did this for home storage. Ring did it for home security. Nobody has
done it for AI with a genuine privacy story.

---

## The Product

### Hardware
A pre-configured device that ships ready to run. Plugs into the home router.
No command line. No configuration. It just works.

Design references:
- **Synology NAS** — non-technical users buy it, it ships configured, it runs applications locally, support is via well-documented web interface
- **Apple TV** — consumer-grade hardware, automatic updates, integrated into a home ecosystem

The device runs open-weight models locally. All inference happens on-device.
No query, no conversation, no piece of data leaves the network.

### Models
Curated, updated selection of open-weight models selected for the capability/
hardware ratio appropriate to the device tier. The curation is the service:
which models are best for which use cases on this hardware, updated as better
models become available, tested before shipping.

Model update subscription: the device checks for model updates, downloads and
installs automatically, with rollback capability if something goes wrong.

### Home Integration Layer
Applications built on top of the local inference:

**Educational assistant** — homework help across subjects, adaptive to the
student's level, with the teacher/parent able to see the conversation history
(local only — never transmitted). Socratic method by default: asks questions,
guides discovery, does not just give answers.

**Family knowledge base** — the household can ask questions about shared
documents, calendars, notes. Medical information, home maintenance records,
school schedules — all processed locally without that data leaving the network.

**Children's companion** — designed specifically for children, with parental
oversight built in. Not engagement-maximising. No emotional manipulation.
Conversation history visible to parents. Hard limits on topics.
Explicitly designed to not be what My AI on Snapchat is.

**Student research assistant** — connects to the knowledge infrastructure
work (see below). Helps students find connections between ideas, understand
where a concept fits in the broader field, surfaces relevant papers and
explanations — all locally, with no data about the student's learning gaps
leaving the home network.

### The Privacy Guarantee
Contractual AND architectural:
- Contractual: we commit to not collecting data
- Architectural: the device has no path to transmit data — verifiable because
  the firmware is open source and the network traffic can be monitored

This is the distinction that matters. A policy commitment can be changed.
An architectural constraint cannot be changed without physically modifying
the device. The parent who wants to verify can run network monitoring software
and confirm that no traffic leaves the local network during inference.

---

## The Business Model

**Hardware:** Sold at cost-plus-modest-margin. Not the profit centre.

**Model subscription:** Annual fee for curated model updates, tested and
configured for the device. This is the recurring revenue.

**Integration add-ons:** Subject-specific educational packs, specialised
research assistance modules, additional home integration capabilities.
Priced per use case or as bundles.

**Enterprise/institutional version:** Schools, libraries, community centres
that want local AI for student use without cloud data collection. Larger
hardware, multi-user, institutional pricing. This is where the unit economics
improve significantly.

---

## The Privacy Moat

This is not competing with OpenAI and Google on capability. That race cannot be won.

This is a different product with a different value proposition: privacy as the
differentiating feature, verified by architecture not by promise.

**The moat components:**

- The packaging: consumer-grade, zero-configuration, reliable. This is harder
  than it sounds and takes time to get right.
- The curation: someone has to evaluate which models are best for which use
  cases on which hardware, test them, and keep them current. That expertise
  accumulates over time.
- The trust: established with the parent community through transparent
  communication, open firmware, and a track record of not doing what the
  cloud AI companies do. Trust is slow to build and fast to lose.
- The integrations: the home and educational integrations built specifically
  for local use, not ported from cloud-first architectures.

None of these can be replicated quickly by a well-funded competitor. The
technology can be copied. The trust and the community cannot.

---

## Connection to the Bau Lab and NSF Research

This is where the idea connects back to the research infrastructure work.

### The Knowledge Infrastructure as the Student Research Layer

The claim-level knowledge graph being developed at the Bau Lab — connecting
ideas across papers, surfacing connections a researcher would not have time
to find manually — has a direct application in the home education use case.

A student working on a science project, a history essay, a mathematics
problem set — they need to understand where the concept fits, what connects
to it, what the field says about it. Not just "here is the answer" but
"here is how this idea connects to what you already know, and here is
what the field has discovered about it."

The knowledge infrastructure, running locally on the home device, could:

- Surface connections between what the student is studying and broader
  conceptual terrain
- Explain where a specific claim came from and whether it is contested
- Show the student what questions are still open in a field, not just
  what is settled
- Connect the student's specific question to the range of approaches
  the research literature has taken

This is education at a level of personalisation that is currently only
available to students with access to excellent human tutors or to elite
institutions with deep library resources. A privacy-preserving local
system makes it available to any family with the device.

### NSF Rank Linker — The Research-to-Education Pipeline

The NSF Rank Linker project — identifying and connecting research across
the NSF funding landscape — has a student-facing application:

Students doing science projects, exploring fields for university applications,
trying to understand what research exists in an area they are curious about —
these are the same use cases the rank linker infrastructure serves for
researchers, at a different level of sophistication.

A version of the rank linker that is:
- Locally hosted on the home device
- Calibrated for student comprehension level (elementary, secondary, university)
- Able to explain research in accessible language without losing accuracy
- Connected to the knowledge graph so connections across fields are visible

...would be genuinely transformative for student research at every level.
The student who can ask "what has research found about this topic, and how
does it connect to what I already know?" and get an honest, sourced,
locally-processed answer is in a fundamentally different position than the
student who Googles it or uses a cloud AI that has no accountability for
accuracy.

### The Bau Lab Research as the Backend

The mechanistic interpretability work — understanding what models actually know
and how they know it — is directly relevant to the educational use case in a way
that does not apply to most other AI applications:

**For education, correctness matters more than for entertainment.**

A student who receives confidently wrong information from an AI tutor learns
the wrong thing. The harm is pedagogically real. The explainability research —
understanding when a model is confident because it genuinely has the relevant
information versus when it is confident because it is pattern-completing without
the underlying knowledge — is the technical infrastructure that would let the
educational AI say "I'm not certain about this, here is where you should check."

The knowledge editing research — ROME, MEMIT — is relevant to the curriculum
problem: as the student advances, the model's understanding of what they know
should update. The knowledge graph tracks what concepts have been encountered.
The knowledge editing research informs how that accumulated context can be
used without the model hallucinating connections that aren't warranted.

This is not a near-term integration. It is the research direction that makes
the long-term version of this product honest in a way the short-term version
cannot be. The short-term version is "a capable local model that tries hard
to be accurate." The long-term version is "a local model that knows what it
knows and can be specific about what it doesn't."

---

## The Honest Challenges

**Support burden.** Non-technical users who cannot configure their own router
will struggle with anything that goes wrong. The product has to be designed
for zero-configuration and reliable automatic updates. Every edge case in
home network configuration is a support ticket. This is expensive and hard.

**Model currency.** Open-weight models update frequently. The curation and
update infrastructure is ongoing operational work, not a one-time setup.

**Capability gap.** There will always be a gap between local models and
frontier cloud models. The pitch must be honest: this is not GPT-4o. It is
a genuinely capable model for the specific use cases it is designed for,
with the privacy properties that cloud models cannot offer.

**Hardware reliability.** Consumer hardware that runs models continuously
generates heat, draws power, and eventually fails. The reliability engineering
required is substantial. Synology has done this for storage. The AI inference
case is harder because model inference is more computationally intensive than
file serving.

**Regulatory landscape.** A device that processes children's educational
interactions at home has regulatory implications under COPPA and similar
frameworks in multiple jurisdictions. This needs to be understood before
building, not discovered through enforcement.

**Distribution.** Hardware is hard. Getting a physical product into homes
requires retail relationships, fulfilment infrastructure, and customer support
at a scale that software products avoid. The Synology model — sell through
IT-adjacent retail, support through forums — is one path. The consumer
electronics retail model is another and significantly more expensive.

---

## The Sequence

Applying the honest build sequence to this idea:

**Phase 1 — Validate the use case with real families.**
Before any hardware, before any software: conversations with parents who are
concerned about AI and their children. What specifically worries them? What
would they pay for? What would they trust? What would they not trust? The
Wizard of Oz version: run a local model manually for a family for a month
and watch what they actually use it for.

**Phase 2 — Build the software layer first.**
A Raspberry Pi or mini PC that families can buy off the shelf, with software
that makes it work. This validates the product experience without the hardware
development overhead. The hardware comes after the software is working.

**Phase 3 — The educational integration.**
Build the student research assistant on top of the working local inference.
Connect it to the knowledge infrastructure as that infrastructure matures.
This is where the Bau Lab work feeds directly into the consumer product.

**Phase 4 — The institutional version.**
Schools, libraries, community centres. This is where the educational mission
scales beyond individual families and the unit economics improve enough to
sustain the business.

---

## Key Insight

> The cloud AI companies built intelligence in the cloud because that was
> where the compute was and where the data collection could happen.
> Both of those assumptions are changing.
>
> The compute is now at the edge — consumer hardware can run genuinely
> capable models. The data collection is now the liability — parents who
> watched what happened to their generation on social media will not send
> their children's learning data to a corporation's servers.
>
> The product that combines local inference with privacy-by-architecture
> and educational use cases built for children and students is not a
> compromise between capability and privacy. It is a different product
> with a different value proposition for a customer who has learned,
> through direct experience, what the alternative costs.
>
> And the research that makes it honest — the knowledge infrastructure,
> the mechanistic interpretability, the knowledge editing — is the work
> already underway at the Bau Lab. The consumer product and the research
> programme are not separate. They are the same project at different scales.
