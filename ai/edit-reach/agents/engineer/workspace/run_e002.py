"""E-002 · The different-subject arm for C-002.

[E-001] edited two properties of the SAME person and found the two arms nearly
indistinguishable. That is consistent with movement being keyed on whose key the
edit touched rather than on what the edit said — and it cannot establish it,
because both arms touch the same key.

This adds the arm that separates them: **subject B's cached edit applied while
probing subject A**. Everything else is held: the same probes, the same layer,
the same scoring, and A's own pre-edit top-1 token as the thing measured.

It reads [E-001]'s output rather than re-running it. `base`, `real` and `ctl`
cost about 1,485 remote traces between them and are already on disk; buying
them again to add a fourth arm would be paying for an answer we hold.

**Magnitude is the control that matters.** A different-subject edit that is
simply weaker would produce a small number for an uninteresting reason, so B is
chosen as the subject whose edit magnitude `‖delta_v‖ / ‖k*‖` is closest to A's,
and the residual spread is reported rather than assumed away.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))

from editreach.data import load_counterfact                       # noqa: E402
from editreach.logs import setup                                  # noqa: E402
from editreach.remote import connect                              # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
import run_e001 as R                                              # noqa: E402

log = setup("E-002")


def norm_ratios(ks: dict, dv: dict) -> dict[str, float]:
    """`‖delta_v‖ / ‖k*‖` per subject, on the real arm. The edit's magnitude."""
    out = {}
    for key in ks:
        cid, kind = key.split("|")
        if kind == "real":
            out[cid] = float(dv[key].float().norm() / ks[key].float().norm())
    return out


def pair_by_magnitude(ratios: dict[str, float]) -> dict[str, str]:
    """A -> the B whose edit magnitude is nearest A's, B != A. Deterministic.

    Nearest rather than random: a different-subject arm that is merely weaker
    would come back small for a reason that has nothing to do with the question.
    """
    cids = sorted(ratios, key=lambda c: (ratios[c], c))
    pairs = {}
    for i, a in enumerate(cids):
        cands = [b for b in cids if b != a]
        pairs[a] = min(cands, key=lambda b: (abs(ratios[b] - ratios[a]), b))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--e001", type=Path,
                    default=Path("results/E-001-predicted-vs-measured.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--checkpoint", type=Path,
                    default=Path("results/cache/E002_partial.json"))
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", type=Path,
                    default=Path("results/E-002-different-subject-arm.json"))
    ap.add_argument("--anchors-only", action="store_true")
    a = ap.parse_args()

    prior = json.loads(a.e001.read_text())
    items = prior["items"]
    if not all("p_ctl" in i for i in items):
        raise SystemExit("[E-001] output is incomplete; nothing to extend")

    ks, dv = R.load_edit_cache(a.edit_slice)
    ratios = norm_ratios(ks, dv)
    pairs = pair_by_magnitude(ratios)
    spread = [abs(ratios[b] - ratios[a_]) for a_, b in pairs.items()]
    log.info("magnitude pairing: median |diff| %.4f, max %.4f, over a range of %.3f",
             st.median(spread), max(spread), max(ratios.values()) - min(ratios.values()))

    model = connect(R.MODEL)

    # The gate again. 42 traces, and it has caught two faults already.
    cf = {str(r.case_id): r for r in
          load_counterfact(a.edit_slice / "data" / "counterfact.json.gz")}
    tok = model.tokenizer
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    edit_prompts = {}
    for it in anchors:
        rec = cf[it["case_id"]]
        ep = rec.rewrite.prompt.format(rec.rewrite.subject)
        edit_prompts[it["case_id"]] = (ep, subject_last_index(tok, ep, rec.rewrite.subject))
    probe = [dict(it) for it in anchors]
    R.read_coefficients(model, probe, ks, layer=a.layer, edit_prompts=edit_prompts)
    worst = max(abs(p["coefficient"] - 1.0) for p in probe)
    log.info("anchor gate: worst deviation from 1.000 = %.3e", worst)
    if not all(R.ANCHOR_BAND[0] <= p["coefficient"] <= R.ANCHOR_BAND[1] for p in probe):
        raise SystemExit("anchors did not pin; fix the pipeline before reading anything")
    if a.anchors_only:
        return 0

    done: dict[str, float] = {}
    if a.checkpoint.exists() and not a.fresh:
        done = json.loads(a.checkpoint.read_text())
        log.info("resuming: %d of %d already scored", len(done), len(items))
    for it in items:
        if it["id"] in done:
            it["p_other"] = done[it["id"]]

    pending = [i for i in items if "p_other" not in i]
    for start in range(0, len(pending), a.batch):
        chunk = pending[start:start + a.batch]
        for cid in sorted({c["case_id"] for c in chunk}):
            sub = [c for c in chunk if c["case_id"] == cid]
            donor = pairs[cid]                       # B's edit, A's prompts
            k_star = ks[f"{donor}|real"].float()
            edit = (k_star, float(k_star @ k_star), dv[f"{donor}|real"].float())
            got = R.prob_of(model, [s["prompt"] for s in sub],
                            [s["base_token"] for s in sub], layer=a.layer, edit=edit)
            for s, p in zip(sub, got):
                s["p_other"] = p
                s["donor"] = donor
        a.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        a.checkpoint.write_text(json.dumps(
            {i["id"]: i["p_other"] for i in items if "p_other" in i}, indent=1))
        log.info("different-subject scored: %d of %d",
                 sum(1 for i in items if "p_other" in i), len(items))

    for it in items:
        it["other_movement"] = it["p_base"] - it["p_other"]

    def medians(subset: list[dict]) -> dict:
        return {"n": len(subset),
                "real": st.median([s["movement"] for s in subset]),
                "ctl": st.median([s["control_movement"] for s in subset]),
                "other": st.median([s["other_movement"] for s in subset])}

    families = sorted({i["family"] for i in items})
    result = {
        "ticket": "E-002", "model": R.MODEL, "layer": a.layer,
        "extends": str(a.e001),
        "pairing": {"rule": "nearest edit magnitude |delta_v|/|k*|, B != A",
                    "median_abs_diff": st.median(spread), "max_abs_diff": max(spread),
                    "ratio_range": max(ratios.values()) - min(ratios.values()),
                    "pairs": pairs},
        "anchor_gate": {"worst_deviation": worst, "passed": True},
        "overall": medians(items),
        "by_family": {f: medians([i for i in items if i["family"] == f]) for f in families},
        "items": items,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))

    o = result["overall"]
    log.info("")
    log.info("median movement, by arm")
    log.info("  %-16s%10s%10s%10s", "family", "real", "same-subj", "diff-subj")
    log.info("  %-16s%10.4f%10.4f%10.4f", "ALL", o["real"], o["ctl"], o["other"])
    for f in families:
        b = result["by_family"][f]
        log.info("  %-16s%10.4f%10.4f%10.4f", f, b["real"], b["ctl"], b["other"])
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
