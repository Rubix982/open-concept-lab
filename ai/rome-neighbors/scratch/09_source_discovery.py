"""
09 — .source discovery: what operations does NNSight expose INSIDE each module?

Everything so far worked at MODULE BOUNDARIES: model.transformer.h[L].output /
.input. `.source` goes one level finer — it reads the module's forward() source
code and exposes each operation / function-call inside it as its own hook point
(readable and patchable), so you can reach intermediates that are not themselves
submodules (e.g. the attention softmax weights).

Operation names are MODEL-SPECIFIC — they come from GPT-J's actual forward code,
so we must discover them, not guess. This script prints the .source view for the
key modules so we can read off the real names, then build capture/attention/
intervention experiments (10–13) on top of them.

Runs LOCALLY — source introspection reads the module classes' forward() code;
no weights, no NDIF, no remote call. (API key is read only if nnsight wants it.)

Usage:
    python 09_source_discovery.py
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

# set the key if present, but we do NOT make a remote call here
_key = os.environ.get("NNSIGHT_API_KEY")
if _key:
    CONFIG.set_default_api_key(_key)

model = LanguageModel("EleutherAI/gpt-j-6b")

# the modules whose internal operations we most want to reach
targets = {
    "block  transformer.h[0]":        model.transformer.h[0],
    "attn   transformer.h[0].attn":   model.transformer.h[0].attn,
    "mlp    transformer.h[0].mlp":    model.transformer.h[0].mlp,
    "norm   transformer.ln_f":        model.transformer.ln_f,
    "head   lm_head":                 model.lm_head,
}

for label, module in targets.items():
    print("=" * 74)
    print(f"MODULE: {label}")
    print("=" * 74)

    # 1. the .source view — per the docs, printing it lists the operation
    #    (call-site) accessors available inside this module's forward()
    try:
        src = module.source
        print("--- module.source ---")
        print(src)
    except Exception as e:
        print(f"  (.source unavailable: {type(e).__name__}: {e})")
        print()
        continue

    # 2. best-effort enumeration of the operation accessors on the SourceEnvoy,
    #    so we have a plain list of names to reference in scripts 10–13
    try:
        op_names = [a for a in dir(src) if not a.startswith("_")]
        print("\n--- candidate operation accessors (dir) ---")
        for n in op_names:
            print(f"    .source.{n}")
    except Exception as e:
        print(f"  (could not enumerate accessors: {type(e).__name__}: {e})")

    print()

print("=" * 74)
print("Next: read off the real op names above (esp. the attention module's),")
print("then 10–13 capture / verify / plot-attention / intervene on them.")
