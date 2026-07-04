"""
Quick connectivity test — GPT-2 via NDIF remote.
Confirms API key works and request lifecycle completes.
"""

import os
from nnsight import LanguageModel, CONFIG

api_key: str = os.environ.get("NNSIGHT_API_KEY", "")
if not api_key:
    raise EnvironmentError("NNSIGHT_API_KEY not set. Run: source ~/.zshrc")
CONFIG.set_default_api_key(api_key)

text: str = (
    "Sally puts the marble in the basket. "
    "Anne moves the marble to the box. "
    "Where does Sally think the marble is?"
)

print("Loading GPT-J-6B skeleton...")
model: LanguageModel = LanguageModel("EleutherAI/gpt-j-6b")
print("Sending trace to NDIF (remote=True)...\n")

with model.trace(text, remote=True):  # type: ignore[union-attr]
    hs  = model.transformer.h[14].output[0].save()  # type: ignore[index]  mid-layer of 28
    out = model.lm_head.output.save()               # type: ignore[union-attr]

print(f"Hidden state shape : {hs.shape}")
print(f"Logits shape       : {out.shape}")

tok_id: int = model.tokenizer.encode(" basket")[0]  # type: ignore[union-attr]
last = out[-1] if out.ndim == 2 else out[0, -1]
logit: float = float(last[tok_id])
print(f"logit('basket')    : {logit:.4f}")

# top-5 predictions
import torch
last = out[-1] if out.ndim == 2 else out[0, -1]
probs = torch.softmax(last.float(), dim=-1)
top_ids = probs.topk(5).indices
print("\nTop-5 predictions at answer token:")
for rank, tid in enumerate(top_ids):
    tok = model.tokenizer.decode([int(tid)])  # type: ignore[union-attr]
    marker = " ◀" if int(tid) == tok_id else ""
    print(f"  {rank+1}. {tok!r:20s}  p={float(probs[tid]):.4f}{marker}")

print("\n✓ NDIF connection confirmed — GPT-J-6B running.")
