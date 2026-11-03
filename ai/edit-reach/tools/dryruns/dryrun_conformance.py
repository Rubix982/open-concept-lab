"""Dry-run wrapper for `tools/ndif_conformance.py`, so it joins the standing set.

The suite carries its own `--dry-run`; this exists so that one command still
runs every dry-run in the project and so a regression in the suite is caught by
the same ritual as a regression anywhere else. Zero remote calls.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import ndif_conformance as C  # noqa: E402


def main() -> int:
    assert C.main(["--dry-run"]) == 0, "conformance dry-run returned non-zero"

    # The suite's value is that a check CAN differ. A check whose reference it
    # can satisfy by construction reports a match that means nothing, so the
    # shape of the registry is asserted here as well as inside the suite.
    assert C.CHECKS, "no checks registered"
    for name, (fn, ref, _) in C.CHECKS.items():
        assert callable(fn), f"{name} is not callable"
        if ref is not None:
            assert ref.tol > 0, f"{name}: a zero tolerance can never match"
            if ref.value:
                assert ref.tol < abs(ref.value), (
                    f"{name}: tolerance {ref.tol:g} reaches zero from "
                    f"{ref.value:g}, so an absent effect would read as a match")

    # `matmul_site` must not be read on the anchors: an anchor ratio is
    # analytically 1.000 under both arithmetics, so the check would read
    # 0.000e+00 whatever the instrument did. It did, once. Named here so the
    # fault cannot come back silently.
    src = (ROOT / "tools" / "ndif_conformance.py").read_text()
    body = src[src.index("def check_matmul_site"):src.index("def check_session_partition")]
    assert "FILLER" in body, "matmul_site must use non-anchor pairs"

    # The suite must IMPORT nothing from this project, or it cannot be copied
    # out and run by anyone else. Matched on import statements, not on the word:
    # the first version of this check grepped for "editreach" and tripped over
    # the suite's own docstring saying it deliberately does not import it. A
    # check that can be satisfied or broken by prose is checking prose.
    imports = re.findall(r"^\s*(?:from|import)\s+([\w.]+)", src, re.M)
    local = [m for m in imports if m.split(".")[0] == "editreach"]
    assert not local, f"the suite must stay standalone; it imports {local}"

    # Every model-specific reference must name a check that exists, or a typo
    # silently restores the 8B number for a model it does not describe.
    for model, refs in C.PER_MODEL.items():
        for check in refs:
            assert check in C.CHECKS, f"{model} references unknown check {check!r}"

    # `session_partition` must not claim a clean partition when there is only
    # one reading or one device. Asserted on the source because the condition
    # only arises against a live deployment that happens to be single-device.
    part = src[src.index("def check_session_partition"):src.index("def check_trace_source")]
    assert "len(devices) < 2" in part, (
        "session_partition must refuse to call a single-device run a partition")

    print(f"dryrun_conformance ok -- {len(C.CHECKS)} checks, registry sane, standalone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
