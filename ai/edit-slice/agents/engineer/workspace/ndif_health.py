"""NDIF connectivity check — run this first when a sweep misbehaves.

Distinguishes "NDIF is down or the key is wrong" from "my code is wrong", which
cost time during E-005 when three separate defects (transport-error
classification, log_softmax allocation, per-deployment memory budgets) all
presented as a run dying partway.

    NNSIGHT_API_KEY=... python agents/engineer/workspace/ndif_health.py [model]
"""

from __future__ import annotations

import os
import sys
import time

from nnsight import CONFIG, LanguageModel

DEFAULT = "meta-llama/Llama-3.1-8B"


def main() -> None:
    key = os.environ.get("NNSIGHT_API_KEY")
    if not key:
        raise SystemExit("NNSIGHT_API_KEY not set — get one from login.ndif.us")
    CONFIG.set_default_api_key(key)

    name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    prompt = "The Eiffel Tower is in the city of"
    t0 = time.time()
    model = LanguageModel(name)
    with model.trace(prompt, remote=True):
        out = model.lm_head.output[0, -1].argmax(-1).save()
    print(f"model:   {name}")
    print(f"prompt:  {prompt!r}")
    print(f"answer:  {model.tokenizer.decode(out)!r}")
    print(f"elapsed: {time.time() - t0:.1f}s  (mostly queue and transfer; compute is sub-second)")


if __name__ == "__main__":
    main()
