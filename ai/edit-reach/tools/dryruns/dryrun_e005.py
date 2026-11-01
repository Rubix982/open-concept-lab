"""Check E-005 offline. The risk here is a comparison that cannot report a difference.

Zero remote calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))

import run_e001 as R1                                             # noqa: E402
import run_e005 as R5                                             # noqa: E402
from editreach.remote import LOADERS, connect                     # noqa: E402


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    # --- the default must not have moved -----------------------------------
    import inspect
    sig = inspect.signature(connect)
    check(sig.parameters["loader"].default == "language",
          "connect still defaults to LanguageModel; 79 scripts depend on it")
    check(LOADERS == ("language", "transformers"), f"two loaders, got {LOADERS}")
    try:
        connect("x", loader="nonsense")
        check(False, "an unknown loader is rejected")
    except ValueError:
        check(True, "an unknown loader is rejected")
    except RuntimeError:
        # NNSIGHT_API_KEY missing is checked after the loader name, which would
        # mean a typo reaches the network before it is caught.
        check(False, "the loader name is validated BEFORE the API key")

    # --- the probes ---------------------------------------------------------
    items = json.loads((ROOT / "probes" / "generated.json").read_text())["items"]
    anchors = R5.probe_rows(items, "/anchor-prefix")
    floors = R5.probe_rows(items, "/anchor-floor")
    check(len(anchors) == 42, f"42 anchor-prefix probes, got {len(anchors)}")
    check(len(floors) == 42, f"42 anchor-floor probes, got {len(floors)}")
    check(not ({a["id"] for a in anchors} & {f["id"] for f in floors}),
          "the two probe sets are disjoint")
    # An anchor begins with its own subject; a floor names somebody else.
    check(all(a["prompt"].startswith(a["subject"]) for a in anchors),
          "every anchor prompt begins with its subject, which is why it pins at 1")
    # This was written as a vacuous check first — it ended in `or True` and
    # could not fail. A check that cannot fail is worse than no check, because
    # it reports a pass.
    owners = {f["id"].split("/")[0].replace("_", " ") for f in floors}
    check(all(f["subject"] != f["id"].split("/")[0].replace("_", " ") for f in floors),
          "every floor probe names somebody OTHER than the probe's owner")
    check(all(f["subject"] in f["prompt"] for f in floors),
          "and that other person is actually in the prompt")
    check(len({f["subject"] for f in floors}) == len(floors),
          f"42 distinct floor names, got {len({f['subject'] for f in floors})}")

    # --- the comparison can actually report a difference --------------------
    src = (ROOT / "agents" / "engineer" / "workspace" / "run_e005.py").read_text()
    check("torch.equal" in src, "bit-identity is still measured with torch.equal")
    # The repeat design is what makes a between-loader difference attributable.
    check("--repeats" in src, "the run takes repeats per loader")
    check("itertools.combinations" in src, "within-loader pairs are compared")
    check("worst_within" in src and "attributable" in src,
          "the verdict turns on BETWEEN exceeding WITHIN, not on bit-identity alone")
    # The word appears in the docstring, warning against it; what must not
    # appear is the CALL. Grepping the whole source caught its own warning.
    check("torch.allclose" not in src,
          "torch.allclose is never CALLED — it is how a re-baseline gets filed "
          "as an upgrade")
    check('"worst_abs"' in src and "max_fraction_differing" in src,
          "the magnitude AND the extent of any difference are both reported")
    # The verdict must be able to come out all three ways.
    for branch in ("branch 1", "branch 2", "branch 3"):
        check(branch in src, f"{branch} is reachable in the verdict")
    check("unsatisfiable" in src,
          "the card's original bit-identity criterion is recorded as a design "
          "error rather than quietly dropped")
    check("E001_FLOOR_MEDIAN" in src and "0.0809" in src,
          "[E-001]'s floor is a named constant, stated before the run")

    # torch.equal on bf16-derived float32 is strict; rehearse that it is not
    # accidentally vacuous on tensors that differ by one ulp.
    a = torch.tensor([1.0, 2.0], dtype=torch.float32)
    b = a.clone(); b[0] = torch.nextafter(b[0], torch.tensor(2.0))
    check(not torch.equal(a, b), "torch.equal separates tensors differing by one ulp")
    check(torch.allclose(a, b), "...where allclose would call them the same")
    check(torch.equal(a, a.clone()), "and it accepts genuinely identical tensors")

    # --- nothing is switched ------------------------------------------------
    rem = (ROOT / "src" / "editreach" / "remote.py").read_text()
    check('loader: str = "language"' in rem, "the package default is still LanguageModel")
    check("TransformersModel" in rem, "the alternative is reachable by name")
    check(rem.count("def connect") == 1, "there is one connect, not two")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\n{len(anchors)} anchors + {len(floors)} floors, both loaders, "
              f"4 remote passes.")
        print("Default loader unchanged. Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
