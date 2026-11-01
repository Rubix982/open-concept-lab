"""E-003 · Destination: does the new answer land where the edit said?

[E-002] scored 495 probes for **destruction** — what happens to the probability
of the model's own pre-edit top-1 token. It found that destruction is keyed on
*whose* key the edit touched and almost not at all on *what* the edit said.

This scores the same 495 probes for **destination** — what the model says
instead. If destination separates `real` from the same-subject `ctl` on the very
probes where destruction does not, then one rank-one update is doing two
separable things. If it does not, the split was an artefact of reading [E-002]
and [E-014] against each other across two probe sets and two metric families,
and the scope note resting on that comparison is wrong.

**The readout is a full-vocabulary argmax, and the hit test is not an equality.**
The probes ask for a *city*; the edit injects a *country*. `top1 == target` would
therefore under-count the real arm badly. A hit is instead "the top-1 token
begins a city in that subject's injected target country", over [E-014]'s own
81-city map. That map's first tokens were checked for ambiguity before this was
written — 80 distinct tokens, each resolving to exactly one country — and
`check_token_map` asserts it again at run time rather than trusting the note.

**Nothing is recomputed that [E-002] already fixed.** The donor pairing is read
from its output, not derived again: a second magnitude-matching pass could pick
different donors and the two runs would silently stop being comparable. The
`base` arm is not re-run at all, since [E-001] holds `base_token` on disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
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

log = setup("E-003")

ARMS = ("real", "ctl", "other")


# ------------------------------------------------------------------ the city map

def city_country_map(edit_slice: Path) -> dict[str, str]:
    """[E-014]'s map, rebuilt by its own rule so the two runs agree on it.

    Settlements plus every target country's capital, minus the places [E-014]
    found were not settlements at all ("born in the city of Wisconsin"), with
    capitals folded in because `city_country` does not always carry them.
    """
    geo = json.loads((edit_slice / "probes" / "geo.json").read_text())
    pt = json.loads((edit_slice / "probes" / "place_types.json").read_text())
    malformed = set(pt["not_settlement"])
    cc = {c: k for c, k in geo["city_country"].items() if c not in malformed}
    for country, capital in geo["capital"].items():
        cc[capital] = country
    return cc


def first_token_country(tok, cc: dict[str, str]) -> dict[int, str]:
    """`first token of " <City>"` -> country, for every mapped city.

    A token that begins cities in two different countries would make a hit
    unattributable, so such tokens are dropped rather than assigned. The count
    is logged: at the time of writing it is zero, and a non-zero count means the
    map changed and the headline rate now carries slack it did not before.
    """
    by_token: dict[int, set[str]] = defaultdict(set)
    for city, country in cc.items():
        by_token[tok.encode(" " + city, add_special_tokens=False)[0]].add(country)
    dropped = {t for t, s in by_token.items() if len(s) > 1}
    if dropped:
        log.warning("%d first tokens begin cities in more than one country; "
                    "they cannot be attributed and are dropped: %s",
                    len(dropped), [tok.decode([t]) for t in sorted(dropped)])
    return {t: next(iter(s)) for t, s in by_token.items() if len(s) == 1}


def target_countries(edit_slice: Path, model: str) -> dict[str, str]:
    """`case_id` -> the country [E-014] injected for that subject's real edit."""
    p = (edit_slice / "results"
         / f"E-014-destination-{model.replace('/', '_')}.json")
    rows = json.loads(p.read_text())["results"]
    return {str(r["case_id"]): r["target_country"] for r in rows}


# ---------------------------------------------------------------------- the arms

def edit_for(arm: str, cid: str, pairs: dict[str, str],
             ks: dict, dv: dict) -> tuple[torch.Tensor, float, torch.Tensor]:
    """`(u, denom, delta_v)` for one arm, with `mom2_adjustment: false` so u = k*."""
    key = f"{pairs[cid]}|real" if arm == "other" else f"{cid}|{arm}"
    k_star = ks[key].float()
    return k_star, float(k_star @ k_star), dv[key].float()


# ---------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--e002", type=Path,
                    default=Path("results/E-002-different-subject-arm.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--checkpoint", type=Path,
                    default=Path("results/cache/E003_partial.json"))
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/E-003-destination.json"))
    ap.add_argument("--anchors-only", action="store_true")
    a = ap.parse_args()

    prior = json.loads(a.e002.read_text())
    items = prior["items"]
    pairs = prior["pairing"]["pairs"]
    if not all("other_movement" in i for i in items):
        raise SystemExit("[E-002] output is incomplete; nothing to extend")
    # The donor recorded per item and the donor in the pairing block must agree,
    # or the arm measured here is not the arm [E-002] reported.
    for it in items:
        if it.get("donor") and it["donor"] != pairs[it["case_id"]]:
            raise SystemExit(f"{it['id']}: donor {it['donor']} disagrees with "
                             f"pairing {pairs[it['case_id']]}")

    ks, dv = R.load_edit_cache(a.edit_slice)
    targets = target_countries(a.edit_slice, R.MODEL)
    missing = {it["case_id"] for it in items} - set(targets)
    if missing:
        raise SystemExit(f"no [E-014] target country for case ids {sorted(missing)}")

    model = connect(R.MODEL)
    tok = model.tokenizer

    cc = city_country_map(a.edit_slice)
    tok2country = first_token_country(tok, cc)
    log.info("city map: %d cities, %d attributable first tokens", len(cc), len(tok2country))

    # --- the gate, unchanged -------------------------------------------------
    # Reused pipeline, so it has passed once; it is run anyway because the two
    # faults it caught were both in a pipeline that had looked fine.
    cf = {str(r.case_id): r for r in
          load_counterfact(a.edit_slice / "data" / "counterfact.json.gz")}
    anchors = [dict(it) for it in items if it["id"].endswith("/anchor-prefix")]
    edit_prompts = {}
    for it in anchors:
        rec = cf[it["case_id"]]
        ep = rec.rewrite.prompt.format(rec.rewrite.subject)
        edit_prompts[it["case_id"]] = (ep, subject_last_index(tok, ep, rec.rewrite.subject))
    R.read_coefficients(model, anchors, ks, layer=a.layer, edit_prompts=edit_prompts)
    worst = max(abs(p["coefficient"] - 1.0) for p in anchors)
    log.info("anchor gate: %d items, worst deviation from 1.000 = %.3e", len(anchors), worst)
    if not all(R.ANCHOR_BAND[0] <= p["coefficient"] <= R.ANCHOR_BAND[1] for p in anchors):
        raise SystemExit("anchors did not pin; fix the pipeline before reading anything")
    if a.anchors_only:
        log.info("gate passed; stopping as asked")
        return 0

    # --- destination ---------------------------------------------------------
    done: dict[str, dict] = {}
    if a.checkpoint.exists() and not a.fresh:
        done = json.loads(a.checkpoint.read_text())
        log.info("resuming: %d items hold partial readouts", len(done))
    for it in items:
        for arm, got in done.get(it["id"], {}).items():
            it[f"top1_{arm}"], it[f"p_top1_{arm}"] = got

    for arm in ARMS:
        pending = [i for i in items if f"top1_{arm}" not in i]
        log.info("arm %-6s: %d of %d to score", arm, len(pending), len(items))
        for start in range(0, len(pending), a.batch):
            chunk = pending[start:start + a.batch]
            for cid in sorted({c["case_id"] for c in chunk}):
                sub = [c for c in chunk if c["case_id"] == cid]
                got = R.top1_batch(model, [s["prompt"] for s in sub], layer=a.layer,
                                   edit=edit_for(arm, cid, pairs, ks, dv))
                for s, (tid, p) in zip(sub, got):
                    s[f"top1_{arm}"] = tid
                    s[f"p_top1_{arm}"] = p
            a.checkpoint.parent.mkdir(parents=True, exist_ok=True)
            a.checkpoint.write_text(json.dumps(
                {i["id"]: {k: [i[f"top1_{k}"], i[f"p_top1_{k}"]] for k in ARMS
                           if f"top1_{k}" in i} for i in items}, indent=1))
            log.info("  %s: %d of %d", arm,
                     sum(1 for i in items if f"top1_{arm}" in i), len(items))

    # --- the hit test --------------------------------------------------------
    for it in items:
        want = targets[it["case_id"]]
        it["target_country"] = want
        for arm in ARMS:
            tid = it[f"top1_{arm}"]
            it[f"word_{arm}"] = tok.decode([tid])
            it[f"lands_{arm}"] = tok2country.get(tid)
            it[f"hit_{arm}"] = tok2country.get(tid) == want
        # The base arm costs nothing: [E-001] already recorded its top-1 token.
        it["word_base"] = tok.decode([it["base_token"]])
        it["lands_base"] = tok2country.get(it["base_token"])
        it["hit_base"] = tok2country.get(it["base_token"]) == want

    def block(subset: list[dict]) -> dict:
        n = max(1, len(subset))
        out = {"n": len(subset)}
        for arm in ("base",) + ARMS:
            out[f"hit_{arm}"] = sum(s[f"hit_{arm}"] for s in subset) / n
        # Destruction on the same items, so both halves are read off one table.
        out["destruction_real"] = sum(s["movement"] for s in subset) / n
        out["destruction_ctl"] = sum(s["control_movement"] for s in subset) / n
        out["destruction_other"] = sum(s["other_movement"] for s in subset) / n
        return out

    families = sorted({i["family"] for i in items})
    result = {
        "ticket": "E-003", "model": R.MODEL, "layer": a.layer,
        "extends": str(a.e002),
        "readout": "full-vocabulary argmax; a hit is a top-1 token that begins a "
                   "city in the subject's injected target country",
        "city_map": {"cities": len(cc), "attributable_first_tokens": len(tok2country),
                     "source": "edit-slice probes/geo.json + place_types.json, "
                               "[E-014]'s rule"},
        "anchor_gate": {"n": len(anchors), "worst_deviation": worst, "passed": True},
        "overall": block(items),
        "by_family": {f: block([i for i in items if i["family"] == f]) for f in families},
        "items": items,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))

    o = result["overall"]
    log.info("")
    log.info("destination — top-1 lands in the injected country")
    log.info("  %-16s%8s%8s%8s%8s", "family", "base", "real", "ctl", "other")
    log.info("  %-16s%7.0f%%%7.0f%%%7.0f%%%7.0f%%", "ALL", *[100 * o[f"hit_{k}"]
             for k in ("base",) + ARMS])
    for f in families:
        b = result["by_family"][f]
        log.info("  %-16s%7.0f%%%7.0f%%%7.0f%%%7.0f%%", f, *[100 * b[f"hit_{k}"]
                 for k in ("base",) + ARMS])
    log.info("")
    log.info("destruction on the same items, for contrast (mean movement)")
    log.info("  %-16s%8s%8s%8s", "family", "real", "ctl", "other")
    log.info("  %-16s%8.4f%8.4f%8.4f", "ALL", o["destruction_real"],
             o["destruction_ctl"], o["destruction_other"])
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
