"""Minimal reproducer: which gradients a remote backward trace will serve.

Written to be the single file handed to NDIF if we ask them, so it carries no
project code, no cache, and no helper of ours beyond the connection. Two arms,
one difference, and the documented 0.8.1 idiom throughout — `with loss.backward():`
with `.grad` read inside it, in reverse-forward order, off raw module-output
tensors (a tuple element such as `layers[i].output[0]` is a copy and an in-place
`requires_grad_` on it never reaches the real tensor).

    ARM 1   gradient of a tensor THE BLOCK built from the model's final output
    ARM 2   gradient of a MODULE's own output tensor, at layers 31, 20 and 5

Measured 2026-10-25 against NDIF, meta-llama/Llama-3.1-8B, client nnsight 0.8.1:
arm 1 is served; arm 2 is refused at every layer with

    OutOfOrderError: '<id>.grad.i0' was requested but the model already ran past it

Depth is not the variable — layer 31, the module immediately before the head,
fails identically to layer 5. Nor is the output swap: the same refusal occurs with
no swap in the trace at all. The boundary separates tensors whose whole forward
use is inside the block from tensors the model itself consumed.

Consequence for this project: `compute_v` needs d(loss)/d(activation) at layer 5,
which is arm 2. It cannot run remotely under 0.8.1 until this changes. Everything
already measured is unaffected — it reads deltas from the [E-014] cache.

    python agents/engineer/workspace/nnsight081_backward_repro.py

Run it as a FILE. nnsight compiles the source of the frame entering `trace`, so
piping on stdin raises WithBlockNotFoundError.
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import connect  # noqa: E402

MODEL = "meta-llama/Llama-3.1-8B"
PROMPT = "Maurice de Vlaminck was born in the country of Chile"
LAYERS = (31, 20, 5)


def main() -> None:
    model = connect(MODEL)
    batch = torch.tensor([model.tokenizer(PROMPT).input_ids])

    # ---- ARM 1 ---------------------------------------------------- expected: OK
    try:
        with model.trace(batch, remote=True):
            act = model.model.layers[5].mlp.down_proj.output
            act.requires_grad_(True)       # frozen model: without this, no graph
            head = model.lm_head.output.float()
            loss = head.sum()
            with loss.backward():
                g = head.grad.float().sum().save()
        print(f"ARM 1  block-built tensor      OK    grad sum = {float(g):.6g}")
    except Exception as exc:  # noqa: BLE001
        print(f"ARM 1  block-built tensor      FAIL  {str(exc).strip().splitlines()[-1]}")

    # ---- ARM 2 -------------------------------------------- expected: OutOfOrder
    for layer in LAYERS:
        try:
            with model.trace(batch, remote=True):
                act = model.model.layers[layer].mlp.down_proj.output
                act.requires_grad_(True)
                head = model.lm_head.output.float()
                loss = head.sum()
                with loss.backward():
                    # Requested for its ORDER, not its value: 0.8.1 requires gradients
                    # in reverse-forward order, and head comes before any layer.
                    gh = head.grad.float().sum().save()  # noqa: F841
                    ga = act.grad.float().norm().save()
            print(f"ARM 2  layer {layer:2d} module output  OK    grad norm = {float(ga):.6g}")
        except Exception as exc:  # noqa: BLE001
            print(f"ARM 2  layer {layer:2d} module output  FAIL  "
                  f"{str(exc).strip().splitlines()[-1]}")


if __name__ == "__main__":
    main()
