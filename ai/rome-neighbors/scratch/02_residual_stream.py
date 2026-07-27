"""
02 — The Residual Stream: how the subject's hidden state evolves with depth.

In script 01 we projected the residual stream to vocabulary. Here we look at
the stream itself, as raw geometry.

Two things worth seeing:
  (a) The L2 NORM of the hidden state at each layer. It typically grows with
      depth — each layer adds its contribution. A sudden jump can mark a layer
      doing heavy lifting.
  (b) How much each layer CHANGES the state — the norm of the delta between
      consecutive layers. Big deltas = layers that write a lot at this position.

We look at the residual stream at the last SUBJECT token ("Tower"), because
that is where ROME says factual associations are stored and read.

Residual stream after layer L : model.transformer.h[L].output[0]   # [1, seq, 4096]
"""

import os
import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = 28

# find the last subject token position ("Tower")
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
subj_pos = max(i for i, t in enumerate(tokens) if "Tower" in t)
print(f"Tokens        : {tokens}")
print(f"Subject token : idx {subj_pos} = {tokens[subj_pos]!r}\n")

# collect the hidden VECTOR at the subject position for every layer, remotely,
# and save just its norm (a scalar) to keep the download tiny.
norms = []
vecs = []
with model.trace(prompt, remote=True):
    for L in range(n_layers):
        h = model.transformer.h[L].output[0][0, subj_pos]   # [4096]
        norms.append(h.norm().save())
        vecs.append(h.save())   # also grab the full vector for delta computation

# ── norms and layer-to-layer change ────────────────────────────────────────
print(f"{'layer':>5}  {'||h||':>10}  {'||Δ from prev||':>16}")
print("─" * 36)
prev = None
for L in range(n_layers):
    h = vecs[L]                      # [4096] real tensor now
    n = float(norms[L])
    if prev is None:
        delta = 0.0
    else:
        delta = float((h - prev).norm())
    print(f"{L:>5}  {n:>10.2f}  {delta:>16.2f}")
    prev = h

print("\nLarge Δ layers are where the subject representation is being rewritten —")
print("compare these to the layers where 'Paris' appeared in the logit lens (01).")
