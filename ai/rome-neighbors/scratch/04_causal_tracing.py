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
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"

# Envoy-derived — no hardcoded architecture constants, so this script is
# model-agnostic (works on any stack, not just GPT-J's 28 layers).
# len(model.transformer.h) uses the Envoy's __len__ over the layer list.
n_layers = len(model.transformer.h)     # 28 for GPT-J
d_model = model.config.n_embd           # 4096 for GPT-J (hidden size, from config)

NOISE = 0.3   # embedding noise std; tune if corruption is too weak/strong
SEED = 0      # fixes the corruption noise so it is IDENTICAL across all runs

answer_id = model.tokenizer.encode(" Paris")[0]
token_ids = model.tokenizer.encode(prompt)
tokens = [model.tokenizer.decode([t]) for t in token_ids]
seq_len = len(token_ids)

# subject token span = the tokens making up "Eiffel Tower"
subj_positions = [i for i, t in enumerate(tokens)
                  if any(w in t for w in ("Eiff", "Tower", "iffel"))]
print(f"Tokens          : {tokens}")
print(f"Subject positions: {subj_positions}\n")


def answer_probability(logits) -> float:
    """How much probability the model puts on the answer token (" Paris").

    `logits` has shape [batch, seq_len, vocab] = [1, 8, 50400] here.
    The compact form is `float(logits[0, -1].softmax(-1)[answer_id])`;
    below is the same thing, unrolled so no index is magical.
    """
    BATCH_INDEX = 0     # we only sent ONE prompt, so batch dim is just 0
    LAST_TOKEN = -1     # the last position predicts the NEXT token — i.e. the
                        # model's answer to "...the city of ___". Earlier
                        # positions predict earlier continuations; we want the end.

    # 1. take the logit vector at (our prompt, its last token) → shape [50400],
    #    one raw score per vocabulary token
    logit_vector = logits[BATCH_INDEX, LAST_TOKEN]

    # 2. softmax turns those 50,400 raw scores into probabilities summing to 1
    probabilities = logit_vector.softmax(dim=-1)

    # 3. answer_id is " Paris"'s vocab index; read off just its probability
    answer_prob = probabilities[answer_id]

    # 4. pull the single value out of the tensor into a plain Python float
    return float(answer_prob)


def corrupt_subject() -> None:
    """Add fixed Gaussian noise to the subject-token embeddings, IN-TRACE.
    Generated on-device via randn_like (avoids the CPU/GPU device-mismatch that
    a locally-built noise tensor causes under remote=True). torch.manual_seed
    makes the noise reproducible so RUN 2 and every RUN 3 restore share the
    exact same corruption — otherwise 'recovery' would compare against a moving
    baseline. [VERIFY on first run: that manual_seed is honoured per remote job.]
    """
    torch.manual_seed(SEED)
    for sp in subj_positions:
        e = model.transformer.wte.output[0, sp, :]                 # type: ignore[index]
        model.transformer.wte.output[0, sp, :] = e + NOISE * torch.randn_like(e)  # type: ignore[index]


# ── RUN 1: CLEAN — stack all hidden states into ONE saved tensor ───────────
# FIX: appending 28 individual .save() proxies returns empty on nnsight 0.7
# (same bug as 01/02). Stack into one [n_layers, seq, d_model] tensor instead.
# We ITERATE the Envoy (model.transformer.h) rather than range(n_layers) — same
# result, but no hardcoded count and portable to any model.
with model.trace(prompt, remote=True):
    clean_stack = torch.stack(
        [layer.output[0][0] for layer in model.transformer.h]      # iterate the Envoy
    ).save()                                                       # [n_layers, seq, d]
    clean_logits = model.lm_head.output.save()
clean_prob = answer_probability(clean_logits)
print(f"[debug] clean_stack shape = {tuple(clean_stack.shape)}  (expect ({n_layers},{seq_len},{d_model}))")

# ── RUN 2: CORRUPTED — noise the subject embeddings, measure the damage ────
with model.trace(prompt, remote=True):
    corrupt_subject()
    corr_logits = model.lm_head.output.save()
corr_prob = answer_probability(corr_logits)

print(f"P('Paris')  clean     = {clean_prob:.4f}")
print(f"P('Paris')  corrupted = {corr_prob:.4f}   (should be much lower)\n")

# ── RUN 3: RESTORED — corrupted + patch one clean (layer, position) ────────
# For each (L, p): re-corrupt, then overwrite the residual at (L, p) with the
# CLEAN vector. recovery = (restored - corrupted) / (clean - corrupted):
#   0 = restoring did nothing ; 1 = fully recovered the fact.
#
# FIX: the clean vector is a direct INDEXED ASSIGNMENT (like 03), not a
# mask-multiply — setitem uses copy_, which handles CPU→GPU transfer on the
# server, so no device mismatch. We sweep every position × every 4th layer.

print("Causal trace — recovery when restoring (layer L, position p):")
print("(rows = position, cols = layer; recovery fraction)\n")

denom = (clean_prob - corr_prob) or 1e-6
sweep_layers = list(range(0, n_layers, 4))
print("pos\\L " + "".join(f"{L:>6}" for L in sweep_layers))

for p in range(seq_len):
    row = f"{tokens[p][:5]:>5} "
    for L in sweep_layers:
        clean_vec = clean_stack[L][p]      # [d_model] — clean residual at (L, p)
        with model.trace(prompt, remote=True):
            corrupt_subject()                                       # same noise as RUN 2
            # restore the clean vector at (L, p) via indexed assignment
            model.transformer.h[L].output[0][0, p, :] = clean_vec   # type: ignore[index]
            r_logits = model.lm_head.output.save()
        r_prob = answer_probability(r_logits)
        recovery = (r_prob - corr_prob) / denom
        row += f"{recovery:>6.2f}"
    print(row)

print("\nThe cell with the highest recovery is where this fact is stored.")
print("For GPT-J it usually peaks at the SUBJECT position, mid layers (~15-20).")
print("That (layer, position) is the site ROME writes its rank-1 update to.")
