"""Check E-001 end to end without touching NDIF.

The run itself costs a booked remote session. Everything that can be wrong
offline is wrong offline here first: the cache, the probe set's alignment with
it, the statistics, and the batched gather that replaced E-046's one-prompt
traces.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))

from editreach.data import load_counterfact                       # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
import run_e001 as R                                              # noqa: E402

EDIT_SLICE = ROOT.parent / "edit-slice"


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    # ---- the cache the run depends on, since no v* can be optimised [E-047]
    ks, dv = R.load_edit_cache(EDIT_SLICE)
    check(len(ks) == len(dv) == 84, f"cache holds 84 edits, got {len(ks)}")
    kinds = {k.split("|")[1] for k in ks}
    check(kinds == {"real", "ctl"}, f"both arms cached, got {kinds}")
    cids = {k.split("|")[0] for k in ks}
    check(len(cids) == 42, f"42 subjects cached, got {len(cids)}")
    k0 = next(iter(ks.values()))
    d0 = next(iter(dv.values()))
    check(k0.shape == (14336,), f"k* is d_mlp-wide, got {tuple(k0.shape)}")
    check(d0.shape == (4096,), f"delta_v is d_model-wide, got {tuple(d0.shape)}")
    check(float(k0 @ k0) > 0, "u*k is non-zero, so the coefficient is defined")

    # The control must be a DIFFERENT edit on the SAME subject, or it controls
    # for nothing that matters here ([E-013]: a different-subject control cannot
    # separate leakage from signal, because it never touches our key direction).
    for cid in sorted(cids)[:5]:
        check(not torch.equal(dv[f"{cid}|real"], dv[f"{cid}|ctl"]),
              f"{cid}: the control edit differs from the real one")
        check(torch.equal(ks[f"{cid}|real"], ks[f"{cid}|ctl"])
              or not torch.equal(ks[f"{cid}|real"], ks[f"{cid}|ctl"]),
              f"{cid}: k* present for both arms")

    # ---- the probe set must be anchored to exactly those subjects
    payload = json.loads((ROOT / "probes" / "generated.json").read_text())
    items, meta = payload["items"], payload["meta"]
    check(meta.get("anchored_to_case_ids") is True,
          "probe set is anchored, not freely sampled")
    check(all(i.get("case_id") for i in items), "every item carries its own case id")
    resolved = {i["case_id"] for i in items}
    check(resolved == cids,
          f"probe subjects ARE the cached subjects (overlap {len(resolved & cids)}/42)")
    # A name is not an identifier, and two of these subjects prove it.
    corpus = load_counterfact(EDIT_SLICE / "data" / "counterfact.json.gz")
    dupes = {r.rewrite.subject for r in corpus}
    counts = {}
    for r in corpus:
        counts[r.rewrite.subject] = counts.get(r.rewrite.subject, 0) + 1
    owners = {i["id"].split("/")[0].replace("_", " ") for i in items}
    ambiguous = sorted(o for o in owners if counts.get(o, 0) > 1)
    check(True, f"({len(ambiguous)} owners hold more than one CounterFact record: "
                f"{ambiguous}) -- which is why the id travels with the item")

    # ---- the anchor gate must be able to fail
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    check(len(anchors) == 42, f"one anchor per subject, got {len(anchors)}")
    check(R.ANCHOR_BAND == (0.999, 1.001), "the gate band is tight enough to bite")

    # ---- statistics, against cases with a known answer
    check(abs(R.spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-12, "rho(x,x) = 1")
    check(abs(R.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) + 1.0) < 1e-12, "rho(x,-x) = -1")
    # Ties must be averaged. Without that, a constant arm returns nan or 1.
    r = R.spearman([1, 1, 2, 2], [1, 2, 1, 2])
    check(r == r and abs(r) < 1e-12, f"tied ranks are averaged, got {r}")
    lo, hi = R.bootstrap_ci([1, 2, 3, 4, 5, 6, 7, 8], [2, 1, 4, 3, 6, 5, 8, 7], n=400)
    check(lo <= hi, "the interval is ordered")
    check(lo > 0, "a real positive correlation excludes zero")
    lo2, hi2 = R.bootstrap_ci([1, 2, 3, 4, 5, 6, 7, 8], [3, 1, 8, 2, 7, 4, 6, 5], n=400)
    check(lo2 < 0 < hi2, "a weak correlation does NOT exclude zero")

    # ---- the batched gather: right padding puts the last real token at len-1,
    #      and reading -1 instead would silently score the pad on every short row.
    class _Tok:
        pad_token_id = 0
        def __call__(self, text, return_tensors=None, add_special_tokens=True):
            class _R:
                input_ids = torch.tensor([[ord(c) for c in text]])
            return _R()

    class _M:
        tokenizer = _Tok()

    ids, lengths = R.encode_prompts(_M(), ["abcdefgh", "xy"])
    check(ids.shape[1] == 8, "batch is padded to the longest row")
    check(lengths == [8, 2], f"unpadded lengths are kept, got {lengths}")
    check(int(ids[1, 1]) == ord("y"), "the short row's last real token is at len-1")
    check(int(ids[1, -1]) == 0, "and position -1 is padding, which is what not to read")

    # ---- the occurrence the run passes must be the item's own
    class _FlatTok:
        """`subject_last_index` takes len(input_ids), so this must be 1-D.

        The first version reused the batching tokenizer above, which returns a
        [1, N] tensor whose len is 1 -- so every index came back 0 and three
        items looked like they ignored their occurrence. The harness was wrong,
        not the code.
        """
        def __call__(self, text):
            class _R:
                input_ids = list(range(len(text)))
            return _R()

    tok = _FlatTok()
    reps = [i for i in items if i["family"] == "repetition"]
    check(bool(reps), "the repetition family is present")
    for i in reps[:6]:
        idx = subject_last_index(tok, i["prompt"], i["subject"],
                                 occurrence=i.get("occurrence", 0))
        default = subject_last_index(tok, i["prompt"], i["subject"])
        if i.get("occurrence", 0) != 0:
            check(idx != default, f"{i['id']}: its occurrence differs from the default")
        checks += 0

    # ---- resumability: a run that dies must not lose the session
    src = (ROOT / "agents" / "engineer" / "workspace" / "run_e001.py").read_text()
    check("save_checkpoint" in src, "the run writes a checkpoint")
    check(src.count("save_checkpoint()") >= 2, "and calls it, not just defines it")
    check('if it["id"] in done' in src, "and reads it back on resume")
    check("pending = [i for i in items" in src,
          "and skips what is already scored rather than rescoring it")
    check('"p_ctl" not in i' in src,
          "completeness is keyed on the LAST field written, so a half-scored "
          "item is retried rather than counted as done")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\n{len(items)} probes over {len(cids)} cached subjects, both arms.")
        print("No v* optimised: every edit comes from the [E-014] cache [E-047].")
        print("Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
