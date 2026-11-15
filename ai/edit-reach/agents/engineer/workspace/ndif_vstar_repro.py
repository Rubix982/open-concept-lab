"""Two reasons ROME's `v*` optimisation does not run on NDIF today.

[E-043] set out to build the Llama-3.1-70B edit cache so the spine could leave
one model. It never reached a second chunk. The run's own handler reported
`chunk failed (RemoteError)` and nothing else, because it logs the exception's
*type* and not its message — so the first thing to say is that the failure was
not diagnosable from the log it wrote.

Run this to see both faults. It is two optimisation steps, no edit is applied,
and it writes nothing.

    .venv/bin/python agents/engineer/workspace/ndif_vstar_repro.py

**Fault 1 — the gradient comes back empty.** On Llama-3.1-70B *and* on
Llama-3.1-8B, `rome.py`'s `_grad_step` reaches

    g_all = out.grad.float().save()

with `out.grad` as `None`, and raises `AttributeError: 'NoneType' object has no
attribute 'float'` inside the remote interleaver. It is not a capacity problem
and it is not specific to the larger model: forward passes on both models
succeed the same afternoon ([E-040] read twelve of them). The 8B cache this
project depends on was built on 16 September, so whatever changed is between
then and nnsight 0.8.1 as deployed now.

**Fault 2 — `rome.py` is Llama-only.** On GPT-J it does not get as far as a
gradient: `AttributeError: 'LanguageModel' object (nor its module) has attribute
'model'`. `rome.py` writes `model.model.layers[layer].mlp.down_proj` in five
places. `editreach.arch.key_site` exists to resolve exactly that path per
architecture — its docstring says *"other script hard-coded Llama's path"* — and
`rome.py` never adopted it. So even with fault 1 fixed, the cache could be built
for two Llamas and not for the third model in the paper.

Neither fault is in this project's control for fault 1, and both are in it for
fault 2.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SLICE = HERE.parents[4] / "edit-slice"
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(SLICE / "src"))

import nnsight                                      # noqa: E402
from editreach.remote import connect                # noqa: E402
from editreach.rome import EditSpec, compute_v_batch  # noqa: E402

MODELS = ("meta-llama/Llama-3.1-70B", "meta-llama/Llama-3.1-8B",
          "EleutherAI/gpt-j-6b")
SPEC = EditSpec("repro|real", "Henry Mackenzie was born in the city of",
                "Henry Mackenzie", "Rome", "real")


def main() -> int:
    print(f"nnsight {nnsight.__version__}\n")
    bad = 0
    for name in MODELS:
        try:
            out = compute_v_batch(connect(name), [SPEC])
            print(f"  {name:<28} OK   "
                  f"{ {k: tuple(v.shape) for k, v in out.items()} }")
        except Exception as e:
            bad += 1
            tail = str(e).strip().splitlines()[-1][:90]
            print(f"  {name:<28} FAIL {type(e).__name__}: {tail}")
    print(f"\n{bad} of {len(MODELS)} models cannot optimise v* through NDIF today.")
    # Zero when the blocker clears, which is the signal E-043 is waiting for.
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
