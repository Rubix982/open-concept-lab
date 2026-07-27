"""
03 — Ablation: which layers actually matter for this fact?

So far we only READ. Now we WRITE. Ablation = deliberately damage part of the
computation and measure how much the answer suffers. If zeroing layer L tanks
the probability of "Paris", layer L was doing something important for this fact.

We sweep two kinds of ablation:
  (a) zero the ENTIRE residual stream output of layer L (all positions)
  (b) zero only the SUBJECT position at layer L ("Tower")

The subject-position ablation is the more surgical, ROME-relevant one: it asks
"how much does this fact depend on the subject token's representation at layer L?"

We track the logit (and probability) of the correct answer token "Paris".
"""

import os
import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = 28

answer_id = model.tokenizer.encode(" Paris")[0]
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
subj_pos = max(i for i, t in enumerate(tokens) if "Tower" in t)

# ── baseline: no ablation ──────────────────────────────────────────────────
with model.trace(prompt, remote=True):
    base_logits = model.lm_head.output.save()
base_prob = float(base_logits[0, -1].softmax(dim=-1)[answer_id])
print(f"Baseline P('Paris') = {base_prob:.4f}\n")

# ── (a) full-layer ablation sweep ──────────────────────────────────────────
# NOTE on the NNSight pattern: in-place multi-index assignment on a proxy can
# fail, so for the subject-only ablation (b) we use the clone→mask→assign
# pattern. For (a) we zero the whole tensor, which is safe with [:] = 0.
print("Full-layer ablation (zero all positions at layer L):")
print(f"{'layer':>5}  {'P(Paris)':>10}  {'drop':>8}")
print("─" * 28)
full_probs = []
for L in range(n_layers):
    with model.trace(prompt, remote=True):
        model.transformer.h[L].output[0][:] = 0
        logits = model.lm_head.output.save()
    p = float(logits[0, -1].softmax(dim=-1)[answer_id])
    full_probs.append(p)
    print(f"{L:>5}  {p:>10.4f}  {base_prob - p:>+8.4f}")

# ── (b) subject-position-only ablation sweep ───────────────────────────────
# build a mask [seq_len, 4096] that is 1 at the subject position, 0 elsewhere,
# then zero only that row via clone → (1-mask) multiply → assign.
seq_len = len(token_ids)
mask = torch.zeros(seq_len, 4096)
mask[subj_pos, :] = 1.0

print("\nSubject-position-only ablation (zero just the 'Tower' row at layer L):")
print(f"{'layer':>5}  {'P(Paris)':>10}  {'drop':>8}")
print("─" * 28)
for L in range(n_layers):
    with model.trace(prompt, remote=True):
        h = model.transformer.h[L].output[0].clone()
        model.transformer.h[L].output[0] = h * (1.0 - mask)
        logits = model.lm_head.output.save()
    p = float(logits[0, -1].softmax(dim=-1)[answer_id])
    print(f"{L:>5}  {p:>10.4f}  {base_prob - p:>+8.4f}")

print("\nThe layers with the biggest drop are the ones this fact depends on.")
print("Subject-position ablation localizes it to WHERE ROME would edit.")
