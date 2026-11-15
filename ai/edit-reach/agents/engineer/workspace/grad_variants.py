"""Four ways to ask for the gradient, to find out whose bug the empty one is.

[E-043] stopped on `out.grad` being `None`. `_grad_step` reads `out =
dp.output`, replaces the output with `dp.output = patched`, calls
`total.backward()`, and then asks `out`. If the replacement is what puts
`patched` in the backward path, the gradient is on `patched` and `out.grad` is
`None` for a reason we wrote.

One model, one layer, one step each. No edit is applied and nothing is written.
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))

from editreach.arch import key_site      # noqa: E402
from editreach.remote import connect     # noqa: E402

MODEL = "meta-llama/Llama-3.1-8B"
LAYER = 5
PROMPT = "Henry Mackenzie was born in the city of"


def shape(x) -> str:
    if x is None:
        return "None"
    try:
        return f"tensor{tuple(x.shape)}  |g| = {float(x.float().norm()):.4g}"
    except Exception as e:                                   # noqa: BLE001
        return f"unreadable ({type(e).__name__})"


def main() -> int:
    model = connect(MODEL)
    dp = key_site(model, LAYER)
    ids = model.tokenizer(PROMPT, return_tensors="pt")["input_ids"]

    # 1 — as [E-043] wrote it
    try:
        with model.trace(ids, remote=True):
            out = dp.output
            out.requires_grad_(True)
            out.retain_grad()
            patched = out.clone()
            dp.output = patched
            loss = model.lm_head.output.float().sum()
            loss.backward()
            g = out.grad.float().save()
        print(f"1  out.grad after backward            {shape(g)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"1  out.grad after backward            FAIL {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1][:70]}")

    # 2 — the node the replacement actually put in the path
    try:
        with model.trace(ids, remote=True):
            out = dp.output
            patched = out.clone()
            patched.requires_grad_(True)
            patched.retain_grad()
            dp.output = patched
            loss = model.lm_head.output.float().sum()
            loss.backward()
            g = patched.grad.float().save()
        print(f"2  patched.grad                       {shape(g)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"2  patched.grad                       FAIL {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1][:70]}")

    # 3 — ask for the gradient before the backward rather than after
    try:
        with model.trace(ids, remote=True):
            out = dp.output
            out.requires_grad_(True)
            out.retain_grad()
            g = out.grad.save()
            patched = out.clone()
            dp.output = patched
            loss = model.lm_head.output.float().sum()
            loss.backward()
        print(f"3  grad proxy taken before backward   {shape(g)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"3  grad proxy taken before backward   FAIL {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1][:70]}")

    # 4 — never replace the output at all
    try:
        with model.trace(ids, remote=True):
            out = dp.output
            out.requires_grad_(True)
            out.retain_grad()
            loss = model.lm_head.output.float().sum()
            loss.backward()
            g = out.grad.float().save()
        print(f"4  no replacement, grad on the output {shape(g)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"4  no replacement, grad on the output FAIL {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
