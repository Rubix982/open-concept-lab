"""
12 — Attention patterns via .source (the payoff of the .source spike).

The attention weights live INSIDE attn.forward as the 2nd return of self._attn —
not at any module boundary. With 09's real op name we can finally grab them:

    model.transformer.h[L].attn.source.self__attn_0.output[1]   # [1, heads, seq, seq]

Question: when the model answers ("of" → Paris), which earlier tokens does the
LAST position attend to, and in which layers? The lookback/ROME story predicts
attention from the answer position back to the SUBJECT tokens ("Eiffel Tower")
in the layers that move the stored fact forward.

We grab attention weights at every layer, then for the LAST query position show
how much it attends to each key token (averaged over the 16 heads), per layer.

Usage:  python 12_source_attention.py
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = len(model.transformer.h)          # Envoy __len__ (28)

token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
seq_len = len(token_ids)

# grab attention weights at every layer, stack into one saved tensor
# (stack-and-save — the nnsight 0.7 loop-of-saves fix)
with model.trace(prompt, remote=True):
    attn_stack = torch.stack([
        model.transformer.h[L].attn.source.self__attn_0.output[1][0]  # [heads, seq, seq]
        for L in range(n_layers)
    ]).save()                                       # [n_layers, heads, seq, seq]

print(f"[debug] attn_stack shape = {tuple(attn_stack.shape)}  "
      f"(expect [{n_layers}, heads, {seq_len}, {seq_len}])")
print(f"Tokens: {tokens}\n")

# for each layer: attention FROM the last query position TO each key token,
# averaged over heads → [seq_len]
last_q = seq_len - 1
print(f"Attention from LAST position ({tokens[last_q]!r}) to each token, by layer")
print("(averaged over heads; rows=layer, cols=key token)\n")

# header of short token labels
print("layer " + "".join(f"{t.strip()[:5]:>7}" for t in tokens))
for L in range(n_layers):
    row = attn_stack[L].mean(dim=0)[last_q]      # [seq_len] avg over heads
    cells = "".join(f"{float(row[k]):>7.2f}" for k in range(seq_len))
    print(f"{L:>5} {cells}")

# which token does the last position attend to most, per layer, and how often
# is it a subject token?
subj_positions = [i for i, t in enumerate(tokens)
                  if any(w in t for w in ("Eiff", "Tower", "iffel"))]
print(f"\nSubject token positions: {subj_positions} "
      f"({[tokens[i] for i in subj_positions]})")
print("\nWatch which layers put the most last-position attention on the subject")
print("tokens — those are the layers carrying 'Eiffel Tower' forward to the answer.")
