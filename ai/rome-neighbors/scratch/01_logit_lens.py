"""
01 — The Logit Lens: how the prediction forms across depth.

Big idea: the residual stream is the model's "working memory". Every layer
reads it, does some computation, and writes an update back. So the residual
stream after layer L is a partial, in-progress version of the final answer.

The logit lens trick: take the residual stream at layer L, push it through the
SAME final layernorm + unembedding (lm_head) that the model uses at the end,
and read off what the model "would predict" if it stopped thinking at layer L.

Watch the prediction crystallize: early layers guess garbage or generic words,
then somewhere in the middle the fact ("Paris") snaps into place.

GPT-J-6B: 28 layers, d_model=4096, vocab=50400.
Residual stream after layer L : model.transformer.h[L].output[0]   # [1, seq, 4096]
Final layernorm               : model.transformer.ln_f
Unembedding                   : model.lm_head
"""

import os
# silence the "process got forked" tokenizer warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = 28

# KEY FIX vs. the first version:
# The first version appended 28 separate .save() proxies to a list — on
# nnsight 0.7 those came back empty (the table printed zero rows). Instead we
# collect the per-layer proxies, torch.stack them into ONE tensor inside the
# graph, and save that single tensor. Stacking forces every element to
# materialise, and we download just two small [28] tensors.
ids_list = []
ps_list = []

with model.trace(prompt, remote=True):
    for L in range(n_layers):
        # residual stream after layer L, at the LAST token position
        resid = model.transformer.h[L].output[0][0, -1]        # [4096]

        # push it through the model's OWN final norm + unembedding (logit lens)
        normed = model.transformer.ln_f(resid)                  # [4096]
        lens_logits = model.lm_head(normed)                     # [50400]

        ids_list.append(lens_logits.argmax(dim=-1))             # scalar proxy
        ps_list.append(lens_logits.softmax(dim=-1).max())       # scalar proxy

    # stack into single tensors and save THOSE (not the individual scalars)
    top_ids = torch.stack(ids_list).save()                      # [28]
    top_ps = torch.stack(ps_list).save()                        # [28]

# ── diagnostic: confirm what actually came back ────────────────────────────
print(f"Prompt: {prompt!r}")
print(f"[debug] top_ids shape = {tuple(top_ids.shape)}  (expect (28,))")

# ── decode and print the crystallization ───────────────────────────────────
print(f"\n{'layer':>5}  {'lens prediction':18s}  {'p':>6}")
print("─" * 36)
for L in range(n_layers):
    tok = model.tokenizer.decode([int(top_ids[L])])
    print(f"{L:>5}  {tok!r:18s}  {float(top_ps[L]):.4f}")

print("\nWatch where 'Paris' first appears and how its probability climbs —")
print("that's the layer range where this fact is assembled.")
