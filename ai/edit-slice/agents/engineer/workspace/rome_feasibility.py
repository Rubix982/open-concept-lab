"""E-006 unknown 1: can NDIF host the two operations ROME requires?

ROME needs (a) to APPLY a rank-one weight delta — expressible as an additive
intervention on the MLP output projection at the target layer — and (b) to
OPTIMISE the target vector v* by gradient descent through the frozen model.

If (a) fails the edit cannot be applied to a shared remote model at all.
If (b) fails v* must be computed elsewhere, which needs local weights.
"""
import os, torch
from nnsight import CONFIG, LanguageModel
CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

MODEL = "meta-llama/Llama-3.1-8B"
m = LanguageModel(MODEL)
prompt = "The Eiffel Tower is in the city of"
L = 5

# --- baseline
with m.trace(prompt, remote=True):
    base = m.lm_head.output[0, -1].argmax(-1).save()
print("baseline next token:", repr(m.tokenizer.decode(base)))

# --- (a) additive intervention on the MLP down_proj output
with m.trace(prompt, remote=True):
    h = m.model.layers[L].mlp.down_proj.output
    m.model.layers[L].mlp.down_proj.output = h + 40.0 * torch.randn_like(h)
    pert = m.lm_head.output[0, -1].argmax(-1).save()
tok_pert = m.tokenizer.decode(pert)
print("perturbed next token:", repr(tok_pert))
print(f"(a) INTERVENTION: {'OK — output moved' if tok_pert != m.tokenizer.decode(base) else 'applied, output unchanged'}")

# --- (b) gradient through the frozen model
try:
    with m.trace(prompt, remote=True):
        acts = m.model.layers[L].mlp.down_proj.output
        acts.requires_grad_(True)
        acts.retain_grad()
        logits = m.lm_head.output[0, -1]
        loss = -torch.log_softmax(logits.float(), -1)[m.tokenizer(" Rome").input_ids[-1]]
        loss.backward()
        g = acts.grad.norm().save()
    print(f"(b) GRADIENT: OK — grad norm {float(g):.4f}")
except Exception as exc:
    print(f"(b) GRADIENT: FAILED — {type(exc).__name__}: {str(exc)[:200]}")
