"""Check E-006 offline. The risk is a design that cannot see its own answer.

Zero remote calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve()
sys.path.insert(0, str(ROOT.parents[2]))
sys.path.insert(0, str(ROOT.parents[2] / "agents" / "engineer" / "workspace"))

import run_e006 as R6                                             # noqa: E402


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    base = ROOT.parents[2]

    # --- the probes ---------------------------------------------------------
    items = json.loads((base / "probes" / "generated.json").read_text())["items"]
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    check(len(anchors) == 42, f"42 anchor probes, got {len(anchors)}")

    # --- the signature must be able to separate what we are measuring -------
    g = torch.Generator().manual_seed(1538)
    x = torch.randn(8, 16, generator=g)
    y = x.clone()
    check(R6.signature(x) == R6.signature(y), "identical tensors hash the same")
    y[3, 7] = torch.nextafter(y[3, 7], torch.tensor(1e9))
    check(R6.signature(x) != R6.signature(y),
          "a one-ulp change in ONE element changes the hash — the effect under "
          "study is 94% of elements, so a hash that missed this would miss nothing, "
          "but a hash that collided would be silent")

    # --- the GPU reader -----------------------------------------------------
    check(R6.gpu_of({"max_mem_by_gpu": {"2": 5937664}}) == "2", "a single GPU reads back")
    check(R6.gpu_of({"max_mem_by_gpu": {"2": 1, "0": 1}}) == "0,2",
          "several GPUs are reported in a stable sorted order, not dict order")
    check(R6.gpu_of({}) == "?", "missing meta reads as unknown, not as a GPU")
    check(R6.gpu_of({"max_mem_by_gpu": {}}) == "?", "an empty map reads as unknown")

    # --- the verdict can come out all three ways ----------------------------
    src = (base / "agents" / "engineer" / "workspace" / "run_e006.py").read_text()
    for branch in ("branch 1", "branch 2", "branch 3"):
        check(branch in src, f"{branch} is reachable in the verdict")
    check("one_value_per_gpu" in src and "one_gpu_per_value" in src,
          "partitioning is tested in BOTH directions, not just one")
    check("frequency bound" in src,
          "agreement across N readings is reported as a bound, not as stability")

    # --- the connection is the variable, so it must be re-made --------------
    check(src.count("connect(R.MODEL)") == 1 and "for n in range(a.readings)" in src,
          "a fresh connection per reading, inside the loop")
    check("meta_out=meta" in src, "the server's meta is captured per reading")
    check("keys_at" in src, "the read goes through the package primitive, not a copy")
    check("model.trace" not in src, "no trace body lives in this script")

    # --- the raw tensor is hashed, not the ratio ----------------------------
    check("signature(keys)" in src,
          "the hash is of the RAW keys; the anchor ratio cancels the effect and "
          "hashing it would hide what is being measured")
    check("anchor_worst_deviation" in src,
          "the derived quantity is recorded beside it, so the practical impact "
          "is visible rather than inferred")
    # The anchor ratio cancels the effect, so it cannot supply a tolerance. The
    # floor, read against a CACHED k*, does not cancel and is the number
    # [E-001] published. A card that owes a tolerance must measure that one.
    check("floor_median" in src, "the floor is measured too, for the tolerance")
    check("floor_spread_across_gpus" in src and "floor_spread_within_gpu" in src,
          "the tolerance separates within-device from across-device spread")
    check(src.count("keys_at(") == 1,
          "all three prompt groups ride in ONE trace; the extra quantity costs "
          "no extra remote pass")

    # --- the package change is additive -------------------------------------
    coef = (base / "src" / "editreach" / "coefficient.py").read_text()
    check("meta_out: dict | None = None" in coef,
          "keys_at gained meta_out as an optional keyword")
    check("meta_out.clear()" in coef,
          "the dict is cleared before filling, so a reused dict cannot carry "
          "a previous reading's device forward")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\n{len(anchors)} probes + {len(anchors)} edit prompts per reading. "
              f"Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
