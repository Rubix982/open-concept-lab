# ROME — Causal Tracing Notes

_Scholar ticket: S-002_
_Source: Section 2 of the paper + `experiments/causal_trace.py`_

---

## The Knowledge Tuple

ROME represents every fact as a triple:

```
t = (s, r, o)
    subject, relation, object

Examples:
  (Space Needle, located in, Seattle)
  (Marie Curie, born in, Warsaw)
  (Eiffel Tower, located in, Paris)
```

To test the model's knowledge: provide (s, r) as a prompt, check if
the model predicts o.

---

## The Three Runs

Causal tracing requires exactly three forward passes per fact:

### Run 1 — Clean
```
Input:  "The Space Needle is located in the city of"
Output: "Seattle" (correct, with high probability)
Save:   ALL hidden states at every (token, layer) position
```

### Run 2 — Corrupted
```
Input:  same prompt, BUT add Gaussian noise to subject token embeddings
        noise_level = 3× std of all embeddings (calibrated per model)
Output: something wrong — "the", random token, etc.
        The subject information is destroyed at the input level.
Save:   all corrupted hidden states
```

The corruption happens at the EMBEDDING level (layer 0), before any
attention or MLP processing. It's like scrambling the subject's
representation before the model even starts thinking.

### Run 3 — Corrupted with Restoration
```
Start:  corrupted run (noisy subject embeddings)
But at ONE specific (token T, layer L):
        replace the corrupted hidden state with the CLEAN state from Run 1
Continue: let the rest of the model run normally

Measure: did the model recover "Seattle"?
         If yes → that (T, L) position is causally decisive
```

This is the **indirect effect** — the causal contribution of a single
state to the correct prediction, while everything else stays corrupted.

---

## The Indirect Effect (IE)

```
IE(token T, layer L) =
    P[Seattle | corrupted + clean state at (T,L)]
  - P[Seattle | fully corrupted]

High IE → restoring this state rescues the prediction
          → this position carries the fact
Low IE  → this state doesn't matter for this fact
```

Run across all (token, layer) pairs and averaged over 1000 facts →
the Average Indirect Effect (AIE) heatmap (Figure 2 in the paper).

---

## What the Heatmap Shows (Figure 2)

Two hot regions emerge:

```
"Early site":
  Token: last token of the subject ("le" in "Space Need|le|")
  Layer: middle layers (~15 in GPT-2 XL)
  Component: MLP dominates (AIE=6.6%), attention minimal (AIE=1.6%)

"Late site":
  Token: last token of the full prompt
  Layer: final layers
  Component: attention dominates
```

**The early site is the discovery.** Everyone expected the late site
(of course the last token before the answer matters). But finding that
the middle-layer MLP at the SUBJECT's last token is decisive — that's new.

Why the last token of the subject specifically?

In auto-regressive models, each token can only attend to prior tokens.
So by the time GPT processes the last subject token ("le" in "Needle"),
it has seen the full subject but not yet the relation or object. The MLP
at this position must be encoding "given everything up to this subject,
what do I know about it?" — it's the point where subject knowledge
gets consolidated into the residual stream.

---

## MLP vs Attention: Path-Specific Effects (Figure 3)

To confirm MLPs are the decisive component, they run a cleverer experiment:

```
Normal restoration:  restore clean state at (T, L)
                     → MLP and attention both benefit

Modified graph:      restore clean state at (T, L)
                     BUT sever the MLP at that position
                     (freeze it at its corrupted baseline value)
                     → only attention benefits from the restoration
```

Result: when MLP is severed, the early site effect disappears completely.
When attention is severed similarly, the early site effect is unchanged.

**Conclusion: the early site effect flows specifically through MLP modules.**
Attention carries information at the late site. MLPs carry it at the early site.

---

## The Localized Factual Association Hypothesis

Based on causal tracing, ROME proposes:

```
Each mid-layer MLP module:
  1. Accepts inputs that encode a subject (at the last subject token)
  2. Produces outputs that recall memorized properties of that subject

The outputs accumulate across middle layers
Then attention at high layers copies the information to the last token
Then the last token predicts the object
```

Three dimensions of localization:
1. **Where:** MLP modules (not attention)
2. **When (layer):** middle layers
3. **When (token):** last token of the subject

This is the hypothesis that ROME then tests by editing — if you can
change the MLP at layer 17, subject's last token, and the model now
believes a different fact, the hypothesis is confirmed.

---

## Connection to the Lookback Paper

| | ROME causal tracing | Lookback causal mediation |
|---|---|---|
| Method name | Indirect Effect (IE) | IIA (Interchange Intervention Accuracy) |
| How corrupted | Gaussian noise on subject embeddings | Counterfactual story (swap characters) |
| What's restored | Single (token, layer) hidden state | Single (token, layer) hidden state |
| Metric | Probability recovery | Output prediction match |
| Finding | MLPs at middle layers, last subject token | Attention heads, OIDs in residual stream |

Same method. Different tasks. Different findings.

**Key difference:** ROME corrupts at the embedding level (adds noise to subject).
Lookback corrupts at the story level (swaps which character is first).
Both then restore one state at a time and measure the effect.

**The open question for S-007:** ROME finds facts in MLPs. Lookback finds
belief retrieval in attention heads. Are these two separate mechanisms that
work in sequence? Does the MLP store "Space Needle → Seattle" and then
the attention-based lookback mechanism *retrieves* it to answer the question?
If so, ROME edits the storage and Lookback describes the retrieval.
That would make them complementary halves of one system.

---

## The Code: `trace_with_patch`

The key function in `experiments/causal_trace.py`:

```python
def trace_with_patch(
    model,
    inp,              # batch: [clean_run, corrupted_run_1, ...]
    states_to_patch,  # list of (token_index, layer_name) to restore
    tokens_to_mix,    # range of subject tokens to corrupt
    noise=0.1,        # noise level
):
```

Convention:
- `inp[0]` = clean run
- `inp[1:]` = corrupted runs

At each forward pass, `patch_rep` is called at every layer:
- At embedding layer: add noise to subject tokens (for runs 1+)
- At specified layers: replace corrupted state with clean state (from run 0)

Uses `nethook.TraceDict` to hook into the model mid-forward-pass —
same pattern as NNsight in the Lookback paper.

The three `kind` values run the experiment three ways:
- `None` = full hidden state (residual stream)
- `"mlp"` = only MLP contribution
- `"attn"` = only attention contribution
→ This is how Figure 1(e,f,g) in the paper are produced.
