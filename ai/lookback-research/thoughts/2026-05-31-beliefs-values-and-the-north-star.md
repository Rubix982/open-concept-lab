# Beliefs, Values, and the North Star

_2026-05-31_

---

## On what activations actually are

Started from a simple question in the abstract notes: what exactly are "internal
activations"? Landed somewhere precise.

An activation is just a vector of floats. For Llama 3 70B — 8192 of them. No
labels, no symbols. Just numbers. The embedding is the entry point — it converts
a token into a vector based on what the model learned that token tends to mean
across the corpus. Then every layer adds to that vector. Each attention head and
MLP contributes a small delta. The residual stream is that accumulation — the
token's running working memory.

A "belief" in an LLM is not stored as a retrievable fact. It's a direction in
that float space. A region that, when the activation points into it, causes the
model to produce a certain output when queried. You can encode a belief (write
into the residual stream), remove it (ROME's rank-one weight edit), or redirect
it (causal patching — swap the floats at one layer, everything downstream
reorients).

---

## On why current "values" in LLMs are a cover-up

Values in current LLMs aren't structural. They're injected as tokens in the
system prompt, or baked into weights through RLHF — which is essentially
statistical pressure to produce outputs that look like a values-aligned person
wrote them.

In humans, values don't work that way. They're in the machinery, not the
memory. You don't recall "honesty is good" before deciding to tell the truth.
The preference is structural — it persists under fatigue, distraction, emotion,
because it's not dependent on a retrieval succeeding.

RLHF is the closest thing we have to structural value encoding. But it's still
surface-level. The model can't *evaluate* an action against a value — it can
only predict tokens that a values-aligned entity would produce in this context.
Which means it's gameable, brittle, and doesn't generalise the way human values
do.

What we're doing with safety now is throwing tokens at the problem and hoping
the statistical pressure holds. It often does. But it holds for the reasons a
well-trained actor holds character on stage — not for the reasons a person with
genuine values holds them under pressure.

---

## LMs as the subconscious

The most accurate analogy for what a forward pass is: the subconscious. It
doesn't deliberate — it pattern-matches, surfaces associations, generates
impulses. Fast, parallel, not governed by explicit rules. The output isn't a
decision, it's a proposal.

The conscious mind evaluates, filters, acts or doesn't. In current systems that
second layer barely exists — we ship the proposal directly.

The architectural gap: we don't know how to build the discriminator process into
the architecture. We know how to make outputs look aligned. We don't know how to
make the model *be* aligned in the structural sense — where values operate as
foreground machinery rather than retrieved content.

---

## The restructuring idea

What if instead of injecting values as tokens at inference time, we designed
models that restructure themselves based on initial fed-in values? Architecture
that reorganises based on what it receives — the way a baby's brain wires itself
through early experience.

The baby analogy is right. Innate priors aren't rules — they're tendencies with
enough flexibility to be shaped by experience. A baby doesn't know "don't lie."
It knows something more primitive: maintain trust relationships. Honesty emerges
from that contextually.

For an LM-augmented system: start with architectural priors that strongly resist
certain structural patterns. Not "don't say X" but "when your outputs would
produce this class of downstream effect, your own update signal treats that as
negative." The value is in the feedback loop, not the content filter.

To encode a reasoning process rather than conclusions, the system needs to
observe you *thinking*, not just the outputs of your thinking. It needs to learn
the discriminator, not the discriminated. Training signal not "was this output
correct" but "was this reasoning process sound."

---

## The default mode insight

The human brain at rest does its most creative work — loose associative
connections across distant memories, counterfactuals, narrative coherence across
unrelated experiences. The default mode network. That's where novel ideas come
from. Not focused retrieval, but undirected traversal of a densely connected
graph of concepts with taste guiding which threads to follow.

This maps onto a specific architectural proposal: a system that, when not being
invoked, notices what it couldn't answer well, what connections it made that felt
weak, what gaps it exposed but couldn't fill — and uses that incompleteness
signal to restructure. Traversing its own graph, pulling new papers, identifying
where its representation is thin. Returning to the next interaction more complete
than before.

Not retrieval. Not standard learning. Epistemic hygiene — the system maintaining
and improving its own model of what it knows and doesn't know.

The incompleteness signals:
- Retrieval confidence gaps
- Contradictions surfaced but not resolved
- Connection attempts that failed
- Questions the researcher stopped pursuing not because answered but because
  the system couldn't go deeper

Each of these is a wound in the knowledge graph. The background process heals
wounds.

---

## The three-layer architecture

```
Researcher ←→ Interface        (subconscious — fast, associative, LM)
                   ↓
             Evaluator          (conscious — what do I not know well enough?)
                   ↓
             Background cultivator  (default mode — wanders, reads, reorganises)
                   ↓
             Knowledge substrate    (the graph itself)
```

The cultivator is the piece nobody has built seriously yet. It runs when nobody
is watching. It makes the difference between a tool useful on day one and a tool
more useful on day 100 — because it has been thinking in between.

---

## The north star

Goal from the beginning: helping purpose-filled people arrive at better science
faster. Humanity gets stuck in periods of knowledge stagnation. Progress stalls
not because humans get less intelligent but because:

- Knowledge becomes too dense to navigate alone
- Disciplines silo — the insight that unlocks medicine is in a materials science
  paper nobody in medicine ever read
- The compounding problem — novel ideas require standing on prior ideas; if you
  can't find the right prior work you unknowingly repeat it or build on weaker
  foundations
- Gatekeeping of access — talent is globally distributed, opportunity is not

The tool is an equaliser and an accelerant simultaneously. Equaliser: a
researcher at a small institution gets the same traversal of the knowledge graph
as someone at MIT with 40 years of accumulated reading. Accelerant: the
bottleneck in science isn't intelligence, it's orientation. Most researchers
spend enormous time figuring out where they are in the landscape. The tool
compresses that orientation phase.

The hardest constraint: genuinely novel ideas are outside the distribution of
what's already known. A system trained on existing knowledge has gravitational
pull toward the known. It needs to support the researcher who suspects the
consensus is wrong — pointing not at the centre of the known, but at its ragged,
unresolved edges. The anomalous data nobody has explained yet.

---

## On the business

The market isn't the question. Research institutions, pharmaceutical companies,
biotech, materials science, government labs — they already pay for an inferior
version of this. The question is whether it has enough depth to be genuinely
irreplaceable. Researchers will know immediately if it's real. One genuine
insight they couldn't have found themselves — one connection across two papers
they never would have read together — and you have a user for life who tells ten
colleagues.

Build it right, build it deep. The survival question answers itself.
