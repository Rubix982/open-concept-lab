"""
04 — Causal Tracing: WHERE is the fact stored? (the ROME method)

This is the capstone. Everything before was warm-up for this.

The question: the model knows "Eiffel Tower → Paris". That knowledge lives in
the weights somewhere. WHERE? Which (layer, token position) actually carries it?

Causal tracing answers this with three runs:

  1. CLEAN     : normal forward pass. Save the hidden state at every
                 (layer, position). Record P('Paris'). This is high.

  2. CORRUPTED : add noise to the SUBJECT token embeddings ("Eiffel Tower").
                 Now the model is confused about the subject. P('Paris') drops.

  3. RESTORED  : run corrupted AGAIN, but at ONE (layer L, position p) copy the
                 CLEAN hidden state back in. If restoring that single site
                 recovers P('Paris'), then that site was carrying the fact.

Sweep L and p. The site with the biggest recovery = where the fact lives.
That is exactly the site ROME edits.

This is more involved than 01–03. If it needs a tweak when you run it, work
through it — understanding this IS the point of the whole project.
"""

import os
import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
n_layers = 28
d_model = 4096
NOISE = 0.3   # embedding noise std; tune if corruption is too weak/strong

answer_id = model.tokenizer.encode(" Paris")[0]
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
seq_len = len(token_ids)

# subject token span = the tokens making up "Eiffel Tower"
subj_positions = [i for i, t in enumerate(tokens)
                  if any(w in t for w in ("Eiff", "Tower", "iffel"))]
print(f"Tokens          : {tokens}")
print(f"Subject positions: {subj_positions}\n")

# ── RUN 1: CLEAN — save all hidden states + baseline probability ───────────
clean_states = {}   # (L) -> tensor [seq_len, d_model]
with model.trace(prompt, remote=True):
    for L in range(n_layers):
        clean_states[L] = model.transformer.h[L].output[0][0].save()  # [seq, d]
    clean_logits = model.lm_head.output.save()
clean_prob = float(clean_logits[0, -1].softmax(dim=-1)[answer_id])

# ── RUN 2: CORRUPTED — noise the subject embeddings, measure the damage ────
# embedding layer output: model.transformer.wte.output  -> [1, seq, d_model]
# build an additive-noise tensor that is nonzero only at subject positions.
noise = torch.zeros(seq_len, d_model)
for p in subj_positions:
    noise[p, :] = NOISE * torch.randn(d_model)

with model.trace(prompt, remote=True):
    emb = model.transformer.wte.output.clone()
    model.transformer.wte.output = emb + noise
    corr_logits = model.lm_head.output.save()
corr_prob = float(corr_logits[0, -1].softmax(dim=-1)[answer_id])

print(f"P('Paris')  clean     = {clean_prob:.4f}")
print(f"P('Paris')  corrupted = {corr_prob:.4f}   (should be much lower)\n")

# ── RUN 3: RESTORED — corrupted + patch one clean (layer, position) ────────
# For each (L, p): rerun corrupted, but overwrite the residual stream at
# layer L, position p with the CLEAN vector we saved. Measure recovery.
#
# recovery = (restored_prob - corrupted_prob) / (clean_prob - corrupted_prob)
#   0.0 = restoring this site did nothing
#   1.0 = restoring this site fully recovered the fact
#
# We sweep every position, all layers. This is O(seq_len × n_layers) remote
# calls — fine for exploration on one prompt.

print("Causal trace — recovery when restoring (layer L, position p):")
print(f"(rows = position, cols = layer; showing recovery fraction)\n")

denom = (clean_prob - corr_prob) or 1e-6
header = "pos\\L " + "".join(f"{L:>5}" for L in range(0, n_layers, 4))
print(header)

for p in range(seq_len):
    row = f"{tokens[p][:5]:>5} "
    for L in range(0, n_layers, 4):   # every 4th layer to keep output readable
        clean_vec = clean_states[L][p]      # [d_model], real tensor
        mask = torch.zeros(seq_len, d_model)
        mask[p, :] = 1.0
        with model.trace(prompt, remote=True):
            emb = model.transformer.wte.output.clone()
            model.transformer.wte.output = emb + noise      # corrupt again
            h = model.transformer.h[L].output[0].clone()
            # patch clean vector into position p at layer L
            h = h * (1.0 - mask) + clean_vec.unsqueeze(0) * mask
            model.transformer.h[L].output[0] = h
            r_logits = model.lm_head.output.save()
        r_prob = float(r_logits[0, -1].softmax(dim=-1)[answer_id])
        recovery = (r_prob - corr_prob) / denom
        row += f"{recovery:>5.2f}"
    print(row)

print("\nThe cell with the highest recovery is where this fact is stored.")
print("For GPT-J it usually peaks at the SUBJECT position, mid layers (~15-20).")
print("That (layer, position) is the site ROME writes its rank-1 update to.")
