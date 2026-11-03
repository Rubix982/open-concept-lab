"""Check E-004 offline. The donor exclusion is where this one can go quietly wrong.

Zero remote calls. The tokenizer comes from the local HuggingFace cache: whether
a hop-2 question names its edited subject is a fact about the benchmark, and the
whole card rests on it.
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

# This dry-run exercises code paths in run_e004 that LOG, so unlike its
# siblings it would leave a file in the project's log directory on every pass.
# A dry-run is not a run and its output is not part of the record, so it writes
# somewhere else. Set before importing anything from the package, because
# `setup()` resolves the directory when it is called.
os.environ.setdefault("EDITREACH_LOGS", tempfile.mkdtemp(prefix="dryrun-e004-"))

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))
sys.argv = ["dryrun_e004"]

import run_e004 as R                                              # noqa: E402

EDIT_SLICE = ROOT.parent / "edit-slice"


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    # --- the selection, which is [E-039]'s and must stay [E-039]'s ----------
    picked = R.select(EDIT_SLICE / "data" / "mquake" / "MQuAKE-CF-3k.json", 2, 600)
    hops = Counter(u["hop"] for u in picked)
    check(len(picked) == 513, f"[E-039]'s 513 instances, got {len(picked)}")
    check(hops[1] == 213, f"213 hop-1, got {hops[1]}")
    check(hops[2] == 300, f"300 hop-2, got {hops[2]}")
    check(all(u["chain_len"] == 2 for u in picked), "two-hop chains only")
    check(len({u["case_id"] for u in picked}) == len(picked), "case ids are unique")

    # --- the property the entire card rests on ------------------------------
    # MQuAKE names the edited subject iff the edit is on hop 1. If that is not
    # true of this selection, there is no near field and no far field in it.
    h1 = [u for u in picked if u["hop"] == 1]
    h2 = [u for u in picked if u["hop"] != 1]
    named_h1 = sum(1 for u in h1 for q in u["questions"] if u["subject"] in q)
    named_h2 = sum(1 for u in h2 for q in u["questions"] if u["subject"] in q)
    check(named_h1 / (3 * len(h1)) > 0.9,
          f"hop-1 questions name their subject: {named_h1} of {3 * len(h1)}")
    check(named_h2 == 0,
          f"hop-2 questions never name their subject: {named_h2} of {3 * len(h2)} do")

    # --- positions ----------------------------------------------------------
    from transformers import AutoTokenizer
    from editreach.rome import subject_last_index
    tok = AutoTokenizer.from_pretrained(R.MODEL)
    bad_star = 0
    for u in picked:
        try:
            p = subject_last_index(tok, u["edit"], u["subject"])
        except ValueError:
            bad_star += 1
            continue
        check(0 <= p < len(tok(u["edit"]).input_ids),
              f"{u['case_id']}: k* position is inside its own edit prompt")
        if checks > 2000:
            break
    check(bad_star == 0, f"every subject is locatable in its own edit prompt "
                         f"({bad_star} are not)")

    # --- the arithmetic -----------------------------------------------------
    g = torch.Generator().manual_seed(1538)
    k = torch.randn(4, 16, generator=g)
    check(torch.allclose(R.coefficients(k[:1], k[0]), torch.ones(1), atol=1e-5),
          "a key against itself scores exactly 1")
    # Each donor is normalised by its OWN denominator. The coefficient is
    # (k.k*)/(k*.k*), so scaling a donor's k* by c scales its coefficient by 1/c
    # — it is the fraction of THAT donor's delta_v which arrives, and a longer
    # k* delivers proportionally less of it. Asserted because using the
    # subject's denominator with a donor's numerator would break exactly here
    # and would look like a floor.
    d = k[1] * 7.0
    check(torch.allclose(R.coefficients(k[:1], d),
                         R.coefficients(k[:1], k[1]) / 7.0, atol=1e-5),
          "a donor's coefficient scales as 1/|k*|, by its own denominator")

    # --- the donor exclusion, rehearsed on a grid with known answers --------
    # Three instances, two questions each on the first two. The mask must remove
    # exactly the question's own instance and nothing else.
    stars = torch.randn(3, 16, generator=g)
    denoms = (stars * stars).sum(-1)
    per = [2, 2, 0]
    owner = torch.tensor([i for i in range(3) for _ in range(per[i])])
    qk = torch.randn(len(owner), 16, generator=g)
    grid = (qk @ stars.T) / denoms
    mask = torch.ones_like(grid, dtype=torch.bool)
    mask[torch.arange(len(owner)), owner] = False
    check(mask.sum().item() == len(owner) * 3 - len(owner),
          "exactly one donor is removed per question")
    for row, own in enumerate(owner.tolist()):
        check(not mask[row, own], f"row {row} excludes its own instance {own}")
        check(all(mask[row, j] for j in range(3) if j != own),
              f"row {row} keeps every other instance")
    floors = torch.where(mask, grid, torch.nan)
    check(torch.isnan(floors[torch.arange(len(owner)), owner]).all(),
          "the excluded cells are nan, not zero — a zero would drag the median down")
    check(not torch.isnan(torch.nanmedian(floors, dim=1).values).any(),
          "every question still has a floor after the exclusion")

    # --- the gate is stated in advance --------------------------------------
    src = (ROOT / "agents" / "engineer" / "workspace" / "run_e004.py").read_text()
    check("E039_HOP1_NATURAL" in src and "E039_HOP2_FINAL" in src,
          "[E-039]'s published medians are named constants, not read from a file")
    check("TOLERANCE" in src and "0.02" in src,
          "the reproduction tolerance is stated before the run")
    check("from run_e039 import usable" in src,
          "the selection is imported from [E-039], not reimplemented")
    check("model.trace" not in src,
          "no trace body lives here; the remote work goes through keys_at")
    check("weights_only=False" in src, "the key cache is resumable")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\n{len(picked)} instances: {hops[1]} hop-1, {hops[2]} hop-2, "
              f"3 questions each.")
        print(f"hop-1 questions naming their subject: {named_h1}/{3 * len(h1)}; "
              f"hop-2: {named_h2}/{3 * len(h2)}.")
        print("Reproduces [E-039]'s selection. Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
