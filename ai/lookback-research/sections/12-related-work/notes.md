# Related Work and Conclusion — Notes

Paper sections 7 and 8, plus ethics and reproducibility statements.

---

## Section 7 — Related Work

The paper positions itself at the intersection of three research clusters.

---

### Cluster 1: Theory of Mind Benchmarks

**Prior state:** A large body of work evaluated ToM *behaviorally* — does
the model answer correctly? Key papers: Le et al. (2019), Shapira et al.
(2023), Wu et al. (2023), Kim et al. (2023), Xu et al. (2024), Jin et al.
(2024), Chan et al. (2024), Strachan et al. (2024).

**The gap:** All these benchmarks test behavior. None have the counterfactual
structure needed for causal mediation. You can't run IIA experiments on them
because they weren't designed with paired examples that isolate specific
variables.

**What this paper adds:** Built CausalToM specifically for causal analysis.
Every story has a counterfactual pair designed to isolate character OI,
object OI, state OI, and visibility independently.

**Papers attempting to improve ToM:** Sclar et al. (2023), Moghaddam &
Honey (2023), Zhou et al. (2023), Wilf et al. (2024), Hou et al. (2024).
The paper explicitly separates itself from this direction — it does not
try to make models better at ToM. It tries to understand what they already do.

**Relevance to Research Knowledge Infrastructure:** The behavioral papers
give us the "what" — which models succeed. The mechanistic paper gives
the "how." For the knowledge infrastructure, the "how" is what matters:
you can only intervene on beliefs you can locate.

---

### Cluster 2: Entity Tracking and Variable Binding

This is the most directly related cluster — prior work on how LMs track
entities and bind variables.

**Li et al. (2021):** LMs form internal representations encoding the
dynamic states of entities. These can be identified and manipulated with
linear probes. *This is the earliest mechanistic evidence that LMs track
entities internally, not just statistically.*

**Belinkov (2022):** Survey of probing classifiers — what they reveal and
their limitations. *Probing finds correlations but not causation. This
paper goes beyond probing to causal intervention.*

**Davies et al. (2023), Prakash et al. (2024), Yang et al. (2025):** Modern
LMs rely on a small set of attention heads that track an entity's positional
information to retrieve its attributes. *This is the direct predecessor to
the lookback mechanism — the "small set of attention heads" finding.*

**Feng & Steinhardt (2023):** LMs encode relational information as "Binding
IDs" in hidden representations. *The OID concept in this paper is an
extension of Binding IDs — more specific about the ordinal structure.*

**Dai et al. (2024):** LMs learn "Ordering IDs" — more symbolic
representations capturing positional information in low-rank subspaces of
residual streams. *This is the direct prior work for OIDs. The paper
builds directly on this finding and extends it to the belief-tracking task.*

**Wu et al. (2025):** Variable binding in Transformers trained on symbolic
programs emerges over three training phases — from shallow heuristics to
systematic mechanism. *This supports the paper's claim that the lookback
mechanism is learned, not programmed. It emerged through training.*

**What this paper adds:** Prior work found individual components (attention
heads, Binding IDs, OIDs). This paper is the first to map the **end-to-end
mechanism** — how all components work together in sequence to solve a
cognitive task (ToM).

**Relevance to Research Knowledge Infrastructure:** The OID/Binding ID
literature is the foundation for the L0 decoder concept. The progression
from correlation (probing) → causation (IIA) → end-to-end mechanism
(this paper) is the methodological template for building the L0 layer.

---

### Cluster 3: Mechanistic Interpretability of ToM

The most recent and directly relevant cluster.

**Zhu et al. (2024):** Belief states of different agents can be linearly
decoded using probes. Intervening on these representations changes ToM
performance. *This is the closest prior work — but it uses probing, not
causal mediation. It shows beliefs are encoded but doesn't identify the
mechanism that uses them.*

**Herrmann & Levinstein (2024):** How prompt variation and fine-tuning
affect stability and structure of belief representations. *More focused
on robustness than mechanism.*

**Bortoletto et al. (2024):** Proposes adequacy criteria for when an
internal representation "counts as belief-like" — accuracy, coherence,
uniformity, use. *This is directly relevant to the L0 decoder: what
makes an internal state a genuine belief vs. a correlate?*

**The gap all three share:** They identify that belief information is
encoded, but not how the model actually *uses* it to produce answers.
The mechanism — the lookback pipeline — is what this paper adds.

**Key quote from the paper (Section 7):**
> "While these works provide valuable insight into how belief information is
> encoded, they do not illuminate the mechanisms by which LMs actually solve
> ToM tasks, limiting our ability to understand, predict, and control model
> behavior."

This is the precise gap the paper fills. And it's the gap the extended
L0 decoder would fill at a higher level — not just "is it encoded" but
"how is it processed and with what confidence."

---

## Section 8 — Conclusion

**The paper's own summary of its contribution:**

> "We are surprised by the pervasive appearance of a single recurring
> computational pattern: the lookback, which resembles a pointer
> dereference inside a transformer."

The authors themselves describe it as a surprise — they found one pattern
doing most of the work, not a diffuse collection of mechanisms. This
supports the hypothesis that gradient descent converges on elegant,
reusable computational primitives.

> "Our improved understanding of these fundamental computations gives us
> optimism that it may be possible to fully reveal the algorithms underlying
> not only the theory of mind, but also other capabilities in LMs."

The paper is explicitly framed as a proof of concept for mechanistic
interpretability of cognitive capabilities. ToM is one capability;
the methodology generalizes.

---

## Ethics Statement — Key Points

**Separation from capability improvement:**
The paper deliberately avoids amplifying ToM capabilities. It characterizes
existing behavior, not enhances it. This is an important distinction for
dual-use concerns.

**Deception detection framing:**
> "Because deception and persuasion are, by definition, difficult or
> impossible to identify from a model's outputs alone, it is crucial to
> understand their neural signatures."

The paper frames mechanistic interpretability as a *safety tool* — if models
can deceive, you need to detect it internally, not just from outputs. This
is the exact argument for the L0 decoder: surface outputs can hide internal
belief states. Internal activation reading cannot be deceived.

**Explicit disclaimer on consciousness:**
> "Our findings describe internal computational mechanisms, not conscious
> reasoning, and should not be taken as evidence of sentience or moral
> agency in LMs."

This is responsible but also worth noting: the disclaimer applies equally
to our speculative ideas about the "mushy feeling." The RetrievalProfile
concept describes computational properties, not experiences.

---

## Reproducibility

- Two A100 80GB GPUs for 70B and Qwen experiments (local)
- NDIF for 405B experiments (remote)
- All models on HuggingFace
- CausalToM dataset, code, and results released at belief.baulab.info
- LLMs used only for grammar correction — no AI-generated research content

---

## Papers Most Relevant to Research Knowledge Infrastructure

In priority order:

1. **Dai et al. (2024)** — Ordering IDs in low-rank subspaces. Direct
   foundation for the OID concept and by extension the L0 decoder.

2. **Zhu et al. (2024)** — Linear decoding of belief states. Proof of
   concept that beliefs are readable from activations. Predecessor to L0.

3. **Bortoletto et al. (2024)** — Adequacy criteria for belief-like
   representations. Framework for evaluating whether the L0 decoder is
   reading genuine beliefs vs. correlates.

4. **Li et al. (2021)** — Dynamic entity state representations.
   Foundation for the broader claim that LMs maintain internal world models.

5. **Wu et al. (2025)** — Variable binding emerges through training phases.
   Evidence that the lookback mechanism was learned, supporting the claim
   that similar mechanisms exist for other capabilities.
