"""
13 — Operation-level intervention: MLP vs attention, per layer.

GPT-J runs attention and MLP IN PARALLEL (block forward, line 23):
    hidden_states = attn_outputs + feed_forward_hidden_states + residual
Both read the same ln_1 output; their outputs are summed with the residual.

.source lets us zero ONE of those two contributions at a given layer, without
touching the other — a cleaner ablation than zeroing the whole block. Real op
names (from 09, at the BLOCK level transformer.h[L]):
    self_attn_0.output[0]  → the attention contribution (attn_outputs)
    self_mlp_0.output      → the MLP contribution (feed_forward_hidden_states)

Question (the ROME thesis): is the "Eiffel Tower → Paris" fact carried by the
MLP or by attention, and in which layers? ROME says factual associations live
in the MLP. So zeroing the MLP contribution in the storage-band layers should
hurt P('Paris') more than zeroing the attention contribution there.

Usage:  python 13_source_intervene.py
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = len(model.transformer.h)
answer_id = model.tokenizer.encode(" Paris")[0]


def answer_prob(logits) -> float:
    return float(logits[0, -1].softmax(dim=-1)[answer_id])


# baseline
with model.trace(prompt, remote=True):
    base_logits = model.lm_head.output.save()
base = answer_prob(base_logits)
print(f"Baseline P('Paris') = {base:.4f}\n")

sweep = list(range(0, n_layers, 2))
print("Zero ONE contribution at layer L, measure P('Paris') drop:")
print(f"{'layer':>5}  {'zero MLP':>18}  {'zero ATTN':>18}")
print(f"{'':>5}  {'P(Paris)  drop':>18}  {'P(Paris)  drop':>18}")
print("─" * 46)

for L in sweep:
    # zero the MLP contribution at block L
    with model.trace(prompt, remote=True):
        model.transformer.h[L].source.self_mlp_0.output[:] = 0     # type: ignore[index]
        mlp_logits = model.lm_head.output.save()
    p_mlp = answer_prob(mlp_logits)

    # zero the attention contribution at block L
    with model.trace(prompt, remote=True):
        model.transformer.h[L].source.self_attn_0.output[0][:] = 0  # type: ignore[index]
        attn_logits = model.lm_head.output.save()
    p_attn = answer_prob(attn_logits)

    print(f"{L:>5}  {p_mlp:>9.4f} {base - p_mlp:>+8.4f}  "
          f"{p_attn:>9.4f} {base - p_attn:>+8.4f}")

print("\nBigger MLP drops than ATTN drops in the storage-band layers would")
print("support the ROME thesis: the fact lives in the MLP, not attention.")
print("(Compare the storage band ~layers 2–12 we found in the ablation spike.)")
