"""
Exploring the FULL lm_head output.

model.lm_head.output is a [batch, seq_len, vocab_size] tensor — for this prompt
that's [1, 8, 50400]. The healthcheck only looked at [0, -1] (last position,
top-1). Here we look at everything:
  1. the full shape
  2. top-5 candidates at the final position (what else did it consider?)
  3. top-1 prediction at EVERY position (the model's running next-token guess
     as it reads the sentence left to right)
"""

import os
import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "Do you know where the Eiffel Tower is located? It's in the city of"

logits = None
with model.trace(prompt, remote=True):
    # save the ENTIRE logits tensor — all positions, all vocab
    logits = model.lm_head.output.save()

# ── 1. The full shape ──────────────────────────────────────────────────────
print(f"Full logits shape : {tuple(logits.shape)}   [batch, seq_len, vocab]")

# recover the tokens so we can label each position
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]

# ── 2. Top-5 at the FINAL position ─────────────────────────────────────────
print(f"\nTop-5 predictions for the token after '{prompt}':")
last = logits[0, -1]                          # [50400]
probs = torch.softmax(last.float(), dim=-1)   # logits → probabilities
top5 = probs.topk(5)
for rank, (p, idx) in enumerate(zip(top5.values, top5.indices), 1):
    print(f"  {rank}. {model.tokenizer.decode([int(idx)])!r:15s}  p={float(p):.4f}")

# ── 3. Top-1 prediction at EVERY position ──────────────────────────────────
# At position i, the model has read tokens[0..i] and predicts what comes next.
# This is the model "reading" the sentence and guessing the continuation at
# each step. Position -1's guess is the real answer; the rest are diagnostic.
print("\nRunning next-token guess at each position:")
print(f"  {'pos':>3}  {'read so far':30s}  {'predicts next':15s}")
for i in range(logits.shape[1]):
    pred_id = int(logits[0, i].argmax(dim=-1))
    read_so_far = "".join(tokens[: i + 1])
    pred_tok = model.tokenizer.decode([pred_id])
    print(f"  {i:>3}  {read_so_far[-30:]:30s}  → {pred_tok!r}")
