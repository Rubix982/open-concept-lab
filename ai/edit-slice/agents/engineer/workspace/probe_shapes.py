"""E-013 gate: confirm the module paths and shapes ROME needs, on the real model.

nnsight's tracer reads the calling frame's source, so this must live in a file —
a heredoc raises OSError('could not get source code').
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
L = 5
prompt = "Maurice de Vlaminck was born in the country of"

with m.trace(prompt, remote=True):
    k_all = m.model.layers[L].mlp.down_proj.input.save()
    o_all = m.model.layers[L].mlp.down_proj.output.save()
    top = m.lm_head.output[0, -1].argmax(-1).save()

print("down_proj.input  (keys,   d_mlp):", tuple(k_all.shape), k_all.dtype)
print("down_proj.output (values, d_model):", tuple(o_all.shape), o_all.dtype)
print("top token:", repr(m.tokenizer.decode(top)))

ids = m.tokenizer(prompt).input_ids
print("n tokens:", len(ids))
print("tokens:", [m.tokenizer.decode([i]) for i in ids])

# ROME's fact_token is "subject_last": the last token OF THE SUBJECT, not of the
# prompt. Locate it explicitly rather than assuming a position.
subject = "Maurice de Vlaminck"
pre = m.tokenizer(prompt[: prompt.index(subject) + len(subject)]).input_ids
print(f"subject {subject!r} ends at token index {len(pre) - 1} "
      f"= {m.tokenizer.decode([pre[-1]])!r}")
