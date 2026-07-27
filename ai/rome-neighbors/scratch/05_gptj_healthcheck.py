"""
Token / NDIF health check — GPT-J-6B (known-good model).
If this completes, the account and token are fine and the Llama 'idx'
error is a server-side bug specific to Llama-3.1-8B on NDIF.
"""

import os
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

# Use the env var you already have set — never hardcode the key
CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")

# ── The forward pass pipeline ──────────────────────────────────────────────
# tokens → embeddings → [28 transformer layers] → final layernorm → lm_head → logits
#                                                                    ▲
#                                                    this is what we grab below

logits = None
with model.trace("The Eiffel Tower is in the city of", remote=True):
    # DEFERRED EXECUTION: inside this block nothing has actually run. We are
    # describing a computation graph, not fetching values. Every expression
    # here returns a PROXY — a placeholder for "the value once the graph runs".
    #
    # model.lm_head        → the language modeling head: a linear layer of shape
    #                        [d_model, vocab_size] = [4096, 50400] for GPT-J. It
    #                        projects each token's 4096-dim hidden state into
    #                        50,400 vocabulary scores (logits). Higher = more
    #                        likely to be the next token.
    # .output              → what lm_head produces this forward pass. Shape
    #                        [batch, seq_len, vocab_size] = [1, 8, 50400]. Still
    #                        a proxy at this point — not a real tensor yet.
    # .save()              → PIN this value so it survives after the block exits.
    #                        Anything not saved is discarded. For remote=True it
    #                        also marks what gets sent back over the network from
    #                        NDIF — everything unsaved stays on their server.
    logits = model.lm_head.output.save()

# ── block exits here → the graph actually executes on NDIF, logits is now real ──

# logits[0, -1] → batch 0, LAST token position. We want the prediction for the
#                 token that comes AFTER the whole prompt, so we take position -1.
#                 Result shape: [50400] (one score per vocab token).
last = logits[0, -1]

# argmax over the 50,400 scores → index of the single most likely next token.
top1 = int(last.argmax(dim=-1))

print(f"\nTop-1 token id : {top1}")

# decode() turns that vocab index back into the actual word/subword string.
print(f"Top-1 token    : {model.tokenizer.decode([top1])!r}")
print("\n✓ Token healthy — NDIF job completed successfully.")
