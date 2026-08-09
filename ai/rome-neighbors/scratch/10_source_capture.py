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

# NOTE (lesson from the first run): do NOT hook the same operation both via
# .source AND via its module boundary in ONE trace — the interleaver provides
# one and the other raises MissedProviderError ("called out of order"). Read
# them in SEPARATE traces and compare locally. Also grab the _attn tuple ONCE,
# then index, rather than hooking .output twice.

# Trace 1 — capture non-boundary intermediates via .source (homogeneous)
with model.trace(prompt, remote=True):
    q = attn0.source.self_q_proj_0.output.save()          # query projection
    attn_ret = attn0.source.self__attn_0.output           # (attn_out, attn_weights)
    attn_out = attn_ret[0].save()                          # attention output
    attn_w = attn_ret[1].save()                            # ATTENTION WEIGHTS
    src_outproj = attn0.source.self_out_proj_0.output.save()

# Trace 2 — the SAME source-op again (determinism baseline): two separate
# remote jobs of the same forward differ slightly in fp16 (nondeterministic GPU
# reductions). This measures that run-to-run noise floor.
with model.trace(prompt, remote=True):
    src_outproj_2 = attn0.source.self_out_proj_0.output.save()

# Trace 3 — the SAME op via its module boundary, in a separate trace
with model.trace(prompt, remote=True):
    mod_outproj = attn0.out_proj.output.save()

print("── captured intermediate shapes (layer 0 attention) ──")
print(f"  q_proj output      : {tuple(q.shape)}        (expect [1, seq, 4096])")
print(f"  _attn output[0]    : {tuple(attn_out.shape)} (attention output)")
print(f"  _attn output[1]    : {tuple(attn_w.shape)}   (ATTN WEIGHTS [1,heads,seq,seq])")

print("\n── sanity: source-op == module-boundary? ──")
# noise floor: SAME source-op, two separate remote jobs (fp16 nondeterminism)
noise_floor = float((src_outproj - src_outproj_2).abs().max())
# the comparison of interest: source-op vs the module boundary
src_vs_mod = float((src_outproj - mod_outproj).abs().max())

print(f"  noise floor (same op, 2 runs)          : {noise_floor:.2e}")
print(f"  source-op vs module-boundary           : {src_vs_mod:.2e}")

# trustworthy if the source-vs-boundary diff is within ~the noise floor,
# i.e. they only differ because of cross-run fp16 nondeterminism
trustworthy = src_vs_mod <= max(noise_floor * 3, 1e-2)
print(f"  → {'TRUSTWORTHY ✓' if trustworthy else 'REAL MISMATCH ✗'} "
      f"({'within' if trustworthy else 'exceeds'} the noise floor)")

print("\nIf TRUSTWORTHY, .source matches the module boundary up to hardware noise")
print("— operation-level access is reliable. Ready for 12 (attention) & 13.")
