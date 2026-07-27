"""
03 — Ablation: which layers actually matter for this fact?

So far we only READ. Now we WRITE. Ablation = deliberately damage part of the
computation and measure how much the answer suffers.

LESSON FROM v1 (the "zero the whole layer" version): zeroing
model.transformer.h[L].output[0][:] wipes the ENTIRE cumulative residual stream
at layer L — not layer L's marginal contribution. That is catastrophic at EVERY
layer (P(Paris) → 0 everywhere) and localizes nothing. `.output` is the running
sum of everything so far, so destroying it is equally fatal at any depth.

To actually LOCALIZE, we ablate ONE TOKEN POSITION at a time (not the whole
stream). Other positions survive, so downstream layers can partially rebuild —
and the effect now varies by layer, revealing which layers matter for this fact.

We compare two positions:
  (a) SUBJECT token ("Tower") — where ROME says the fact is stored
  (b) LAST token ("of")       — where the answer is read out

DEVICE NOTE (remote gotcha): with remote=True the activations live on the NDIF
GPU (cuda:0). A locally-built mask tensor lives on CPU, so `h * mask` throws a
device-mismatch error. We avoid it entirely by zeroing the row with a direct
indexed assignment — no separate tensor, no device to mismatch.
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
last_pos = len(token_ids) - 1
print(f"Subject token : idx {subj_pos} = {tokens[subj_pos]!r}")
print(f"Last token    : idx {last_pos} = {tokens[last_pos]!r}\n")

# ── baseline: no ablation ──────────────────────────────────────────────────
with model.trace(prompt, remote=True):
    base_logits = model.lm_head.output.save()
base_prob = float(base_logits[0, -1].softmax(dim=-1)[answer_id])
print(f"Baseline P('Paris') = {base_prob:.4f}\n")


def ablate_position(pos: int) -> list[float]:
    """Zero the residual at `pos` at each layer in turn; return P(Paris) per layer."""
    probs = []
    for L in range(n_layers):
        with model.trace(prompt, remote=True):
            # direct indexed zeroing — [batch=0, position=pos, all 4096 dims]
            model.transformer.h[L].output[0][0, pos, :] = 0
            logits = model.lm_head.output.save()
        probs.append(float(logits[0, -1].softmax(dim=-1)[answer_id]))
    return probs

# ── (a) ablate the SUBJECT position across layers ──────────────────────────
print("Ablate SUBJECT position ('Tower') at each layer:")
print(f"{'layer':>5}  {'P(Paris)':>10}  {'drop':>8}")
print("─" * 28)
subj_probs = ablate_position(subj_pos)
for L, p in enumerate(subj_probs):
    print(f"{L:>5}  {p:>10.4f}  {base_prob - p:>+8.4f}")

# ── (b) ablate the LAST position across layers ─────────────────────────────
print("\nAblate LAST position ('of') at each layer:")
print(f"{'layer':>5}  {'P(Paris)':>10}  {'drop':>8}")
print("─" * 28)
last_probs = ablate_position(last_pos)
for L, p in enumerate(last_probs):
    print(f"{L:>5}  {p:>10.4f}  {base_prob - p:>+8.4f}")

print("\nCompare the two: big drops at the SUBJECT position in early-mid layers")
print("= the fact is stored there (where ROME edits). Big drops at the LAST")
print("position in later layers = that's where the answer is read out.")
