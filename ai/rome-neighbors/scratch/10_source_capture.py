"""
10 — .source capture + sanity check (grounded in 09's real GPT-J op names).

Two things:
  (a) CAPTURE intermediates that are NOT module boundaries — prove we can reach
      inside the attention forward (q_proj, the _attn tuple, its attn_weights).
  (b) SANITY: a source-op that IS a submodule call must equal that submodule's
      own .output. We check self_out_proj_0 (source op) == attn.out_proj.output
      (module boundary). If they match, .source is trustworthy.

Real names from 09:
  attn.source.self_q_proj_0.output    → query projection      [1, seq, 4096]
  attn.source.self__attn_0.output     → (attn_output, attn_weights) tuple
  attn.source.self__attn_0.output[1]  → attention weights      [1, heads, seq, seq]
  attn.source.self_out_proj_0.output  → == attn.out_proj.output (sanity)

Usage:  python 10_source_capture.py
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

model = LanguageModel("EleutherAI/gpt-j-6b")
prompt = "The Eiffel Tower is in the city of"
attn0 = model.transformer.h[0].attn

with model.trace(prompt, remote=True):
    # (a) capture non-boundary intermediates inside attn.forward
    q = attn0.source.self_q_proj_0.output.save()          # query projection
    attn_out = attn0.source.self__attn_0.output[0].save()  # attention output
    attn_w = attn0.source.self__attn_0.output[1].save()    # ATTENTION WEIGHTS

    # (b) sanity: source-op output vs the same submodule's boundary output
    src_outproj = attn0.source.self_out_proj_0.output.save()
    mod_outproj = attn0.out_proj.output.save()

print("── captured intermediate shapes (layer 0 attention) ──")
print(f"  q_proj output      : {tuple(q.shape)}        (expect [1, seq, 4096])")
print(f"  _attn output[0]    : {tuple(attn_out.shape)} (attention output)")
print(f"  _attn output[1]    : {tuple(attn_w.shape)}   (ATTN WEIGHTS [1,heads,seq,seq])")

print("\n── sanity: source-op == module-boundary? ──")
same = torch.allclose(src_outproj, mod_outproj)
print(f"  self_out_proj_0.output  vs  attn.out_proj.output : "
      f"{'MATCH ✓' if same else 'MISMATCH ✗'}")
print(f"  max abs diff = {float((src_outproj - mod_outproj).abs().max()):.2e}")

print("\nIf the shapes are sane and the sanity check MATCHES, .source is giving")
print("us trustworthy operation-level access — ready for 12 (attention) & 13.")
