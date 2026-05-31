# How an LM Actually Works — From Tokens to Output

_2026-05-31_

---

## The vocabulary table

The model knows a fixed set of tokens — roughly 32,000 for Llama 2, 128,000
for Llama 3. This is just a lookup table:

```
index 0      → "<unk>"     (unknown token, special)
index 1      → "<s>"       (beginning of sequence, special)
index 2      → "</s>"      (end of sequence, special)
...
index 29     → "▁the"      (the word "the" with a leading space marker)
index 304    → "▁in"
index 1176   → "▁transform"
index 2068   → "ers"        (a suffix, not a standalone word)
index 4821   → "▁juice"
...
index 31999  → some rare subword fragment
```

The `▁` symbol marks "this piece starts a new word" — SentencePiece's way of
encoding word boundaries since spaces are not tokens themselves.

The model never works with words directly. Everything is indices and vectors.

**What the vocabulary actually contains — not complete words**

This is a common misconception. The vocabulary is not a word dictionary like
Webster's (470,000 entries) or the OED. It is a *fragment dictionary* — a mix
of special tokens, single characters, common subword pieces, and some whole
common words. Most entries are subword fragments, not complete words.

Real English dictionaries have hundreds of thousands of complete word entries.
The model vocabulary has tens of thousands of fragments that can *compose* into
any word.

**Why subwords instead of whole words**

BPE (Byte Pair Encoding) builds the vocabulary by:
1. Starting with all individual bytes/characters as the base
2. Counting which pairs of tokens appear most frequently together in the corpus
3. Merging the most frequent pair into a new token
4. Repeating until the vocabulary size limit is reached

The ordering reflects the merge history — early indices tend to be single
characters and bytes, later indices tend to be common fragments and words that
got merged in. The index order is NOT sorted by frequency. Index 29 is not
the 29th most frequent word.

**The consequence: any word can be represented**

```
"unbelievable"  →  ["un", "believ", "able"]
"transformers"  →  ["transform", "ers"]
"مرحبا"         →  [3-5 Arabic subword pieces]
"saifulislam"   →  ["sa", "if", "ul", "islam"]
```

Any text — including words coined after training, typos, code, URLs, numbers,
any human language — can be represented as a sequence of subword tokens. The
model never hits an unknown word. It just uses more tokens to represent it.

**Token fertility — the multilingual problem**

How many tokens a language needs per word is called token fertility. A
vocabulary optimised for English will decompose Arabic, Tamil, or Swahili text
into many more pieces than equivalent English text:

```
"hello"   →  1-2 tokens     (English, well represented in vocabulary)
"مرحبا"   →  3-5 tokens     (Arabic, fewer merges allocated)
```

High fertility = that language is a second-class citizen in the model regardless
of training data volume. The model's effective context window shrinks, embeddings
for byte fragments carry almost no semantic content, and the residual stream must
do enormous reconstruction work just to understand a basic word.

This is why Llama 3 expanded from 32K to 128K tokens — more vocabulary slots
means more merges available for non-English scripts, reducing fertility and
making those languages computationally first-class.

**Vocabulary sizes across models**

| Model       | Vocabulary size |
|-------------|----------------|
| GPT-2       | 50,257         |
| Llama 2     | 32,000         |
| Llama 3     | 128,256        |
| GPT-4       | ~100,000       |
| Mistral 7B  | 32,000         |
| Qwen 2.5    | ~150,000       |

The real memory cost is the embedding matrix:
```
Llama 2:  32,000  × 4,096  ≈ 131M parameters  just for embeddings
Llama 3:  128,256 × 4,096  ≈ 525M parameters  just for embeddings
```

Beyond ~200,000 tokens the gains in text compression are small relative to the
memory and compute cost — which is why vocabularies don't grow indefinitely.

**Multilingual LLMs — data is necessary but not sufficient**

The claim "multilingual LLM" often means: good at 20-30 well-resourced
languages, passable at another 50, barely functional at the remaining 6,000+
languages humans speak. Better and more balanced training data helps, but
without vocabulary allocation for those languages the fertility problem remains.
This is not primarily a technical problem — it is a data sovereignty, incentive,
and resource allocation problem. Talent is globally distributed. Opportunity,
and language representation in training data, is not.

---

## Step 1 — Embedding: index → vector

When a token enters the model, it looks up its index in the embedding matrix.

```
embedding matrix shape: (32000, 8192)
one row per token, each row is 8192 floats long
```

Token at index 4821 → pull out row 4821 → a vector of 8192 floats.

That vector is the token's starting position in residual stream space. It encodes
what the model learned that token tends to mean across the corpus — not a hand-
designed meaning, but a direction in float space that emerged from training.

This is a one-to-one mapping. One token → one vector. No ambiguity.

The reason it's 8192 numbers rather than one number: a single number can only
express magnitude. Meaning has many independent dimensions simultaneously —
"bank" is financial and also riverbank, "king" relates to "queen" in one
direction and "man" in another. A high-dimensional vector can hold all of those
relationships at once. Each dimension isn't labelled — the geometry emerged from
training.

---

## Step 2 — The residual stream: accumulating context

Each token starts with its embedding vector. As it passes through 80 layers,
each layer *adds* a delta to that vector:

```
residual[0]  = embedding(token)
residual[1]  = residual[0] + attn_0(residual[0]) + mlp_0(residual[0])
residual[2]  = residual[1] + attn_1(residual[1]) + mlp_1(residual[1])
...
residual[80] = final representation
```

The residual stream is that accumulation — the token's running working memory.

**What attention contributes:**
Each attention head looks at other tokens in the sequence and decides what
information to pull in. If head 7 in layer 23 decides the current token needs
to know about "juice" three positions back, it writes a delta in that direction.
The delta is small — a nudge — but 80 layers of nudges compound.

**What the MLP contributes:**
A nonlinear transformation — two linear layers with an activation function
between them. Where attention routes information *from other tokens*, the MLP
transforms the current token's representation in place. Thought of as storing
and retrieving factual associations from the weights.

**The key property:**
Nothing is overwritten. Everything is added. The original embedding is always
in there — every layer's contribution stacks on top. This is why it's called
a residual stream — information flows through and accumulates, it doesn't get
replaced.

---

## Step 3 — The LM head: vector → logits

At the final layer, the model only cares about the **last token's** residual
stream vector. That's the one that has been attending to everything before it —
it carries the accumulated context of the whole sequence.

That vector `(8192,)` is multiplied by the LM head matrix:

```
LM head shape: (32000, 8192)
32,000 rows — one per vocabulary token
each row is 8192 floats long

(32000 × 8192)  @  (8192,)  →  (32000,)  logits
```

**What is a row in the LM head?**
Each row is a "template" — the fingerprint of what that token's direction looks
like in residual stream space. Learned during training, not hand-designed.

**What is a dot product doing here?**
For each of the 32,000 rows, compute the dot product with the residual vector.
Dot product measures: how much does the current residual vector point in the
direction of this token's template?

```
high dot product → residual pointing toward this token's region → high logit
low dot product  → residual pointing away                       → low logit
```

The result is 32,000 raw scores — one per vocabulary token. These are logits.

**Where did the LM head values come from?**
Training. During pretraining the model was shown billions of tokens, made
predictions, measured error, and nudged every parameter including every value
in the LM head matrix in the direction that would have reduced the error. Done
billions of times, the matrix organises itself so each row genuinely captures
the fingerprint of its token in residual stream space. Nobody designed this —
it emerged.

**Weight tying:**
In many models (GPT-2, Llama), the LM head matrix is the same matrix as the
input embedding matrix, transposed. The embedding maps token index → residual
stream direction on the way in. The LM head maps residual stream direction →
token score on the way out. Same learned values, used in both directions.

This means the model learned one consistent geometry: a space where tokens have
addresses, and the residual stream accumulates toward the address of the most
likely next token.

---

## Step 4 — Softmax: logits → probabilities

```
logits  (32000,)  →  softmax  →  probabilities  (32000,)
```

Softmax converts raw scores into a probability distribution. All 32,000 values
now sum to 1.0:

```
token_0    ("the")   → 0.000823
token_1    ("a")     → 0.000241
...
token_4821 ("juice") → 0.412000
...
```

---

## Step 5 — Sampling: probabilities → next token

**Argmax:** always pick the index with the highest probability. Deterministic.
Same prompt always produces same output.

**Sampling:** pick probabilistically from the distribution. The same prompt can
produce different outputs each time. Controlled by:

- **Temperature** — scales logits before softmax. High = flatter distribution
  (more random). Low = sharper distribution (more deterministic).
- **Top-k** — restrict sampling to only the top k tokens.
- **Top-p (nucleus)** — restrict to the smallest set of tokens whose
  probabilities sum to p.

The winning index is looked up in the vocabulary table → that's the output word.

---

## The full chain

```
"juice"
  ↓
index 4821
  ↓
embedding lookup → (8192,) starting vector
  ↓
layer 1:  + attn_0 delta + mlp_0 delta
layer 2:  + attn_1 delta + mlp_1 delta
...
layer 80: + attn_79 delta + mlp_79 delta
  ↓
final residual vector (8192,)  ← carries accumulated context of whole sequence
  ↓
layer norm
  ↓
LM head (32000 × 8192) @ (8192,)  →  logits (32000,)
  ↓
softmax  →  probabilities (32000,)
  ↓
argmax or sample  →  winning index
  ↓
vocabulary lookup  →  next token
```

---

## The one-sentence summary

Transform the input token addresses through 80 layers of contextual
accumulation — each layer adding a small delta based on what other tokens say
and what the weights know — until the resulting vector is closest to the address
of the most likely next token.

---

## What this means for "beliefs"

A belief is not stored anywhere explicitly. It's a direction in residual stream
space that emerged from training and gets written into a token's vector through
attention. When you ask the model "what does Bob believe?" — the forward pass
accumulates deltas that push the final residual vector toward the region of
vocabulary space corresponding to Bob's believed state. The answer is geometry,
not retrieval.

Encoding a belief: attention writes a delta in a particular direction.
Removing a belief: ROME edits the weight matrix so that direction no longer
gets written (permanent).
Redirecting a belief: causal patching swaps the floats at one layer — everything
downstream reorients (transient, per forward pass).

---

## What we glossed over or stated with more confidence than warranted

**"The model only cares about the last token's residual stream"**
True for next-token prediction in a standard autoregressive decoder. Not
universally true — encoder models use every token's final representation, and
even in decoders all intermediate token representations shaped the last token
via attention.

**"Each row in the LM head is a template for that token"**
Useful intuition but oversimplified. The geometry is messier — superposition,
polysemanticity, interference between concepts mean the space is more tangled
than one direction per token.

**"Weight tying"**
True for many models but not all. Worth verifying for any specific model.

**"The MLP stores factual associations"**
The ROME hypothesis — compelling, supported by experiments, but not settled.
One interpretation of what MLPs do, not a documented fact.

**"Attention routes information from other tokens"**
True directionally. In practice heads do many things simultaneously, some heads
appear to do very little, the division of labour is messy and model-specific.

**"Beliefs as directions in float space"**
Supported by interpretability research but oversimplified. Concepts are often
represented in superposition — multiple concepts sharing overlapping directions,
disambiguated by context. A belief is a region, not a single clean direction,
and its boundaries are fuzzy and context-dependent.

**The neuroscience analogies**
Default mode network, subconscious, values as structural priors — these are
analogies, not established mappings. Useful thinking tools, not scientific claims.

**The meta-point**
Most of what is described here is the standard pedagogical account of
transformers — accurate enough to build intuition, simplified enough to be
communicable. The gap between the standard account and what is actually
happening in a trained model is where all the interesting research lives.

---

## The Arabic moment

Typed: مرحبا

The model processed it — tokenised it into probably 3-5 subword pieces, ran
each through the full forward pass, used attention to assemble them back into
a coherent greeting, responded in Arabic.

"hello" in English: almost certainly 1 token.
"مرحبا" in Arabic: 3-5 tokens.

Same meaning. Potentially 5x the computational work. The fertility problem made
concrete and live.
