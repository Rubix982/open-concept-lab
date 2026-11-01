"""Check E-003 offline. The hit test is where this one can go quietly wrong.

Zero remote calls. The tokenizer is loaded from the local HuggingFace cache
because the token->country map is the one part of this run that cannot be
checked by reading the code: whether two cities share a first token is a fact
about the tokenizer, not about us.
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))

import run_e001 as R1                                             # noqa: E402
import run_e003 as R3                                             # noqa: E402

EDIT_SLICE = ROOT.parent / "edit-slice"


def main() -> int:
    failures, checks = [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    # --- what it extends ----------------------------------------------------
    prior = ROOT / "results" / "E-002-different-subject-arm.json"
    check(prior.exists(), "[E-002] output is on disk to extend")
    payload = json.loads(prior.read_text())
    items, pairs = payload["items"], payload["pairing"]["pairs"]
    check(len(items) == 495, f"495 items, got {len(items)}")
    check(all("movement" in i and "control_movement" in i and "other_movement" in i
              for i in items), "every item already carries its three destruction numbers")
    check(all("base_token" in i for i in items),
          "and the base top-1 token, so the base arm is not re-bought")
    check(all(i["donor"] == pairs[i["case_id"]] for i in items if i.get("donor")),
          "the per-item donor agrees with the pairing block")
    check(len(pairs) == 42, f"42 donors, got {len(pairs)}")

    # --- the arms -----------------------------------------------------------
    ks, dv = R1.load_edit_cache(EDIT_SLICE)
    cids = sorted({i["case_id"] for i in items})
    for cid in cids[:10]:
        e_real = R3.edit_for("real", cid, pairs, ks, dv)
        e_ctl = R3.edit_for("ctl", cid, pairs, ks, dv)
        e_oth = R3.edit_for("other", cid, pairs, ks, dv)
        check(not e_real[2].equal(e_ctl[2]), f"{cid}: real and ctl are different edits")
        check(not e_real[2].equal(e_oth[2]), f"{cid}: real and donor are different edits")
        check(e_oth[2].equal(dv[f"{pairs[cid]}|real"]),
              f"{cid}: the donor arm uses the donor's REAL edit, not their control")
        check(all(torch.isfinite(t).all() for t in (e_real[0], e_real[2])),
              f"{cid}: the edit tensors are finite")

    # The control that makes a destination gap readable. These two were never
    # magnitude-matched, unlike the donor arm, so it is asserted rather than hoped.
    real_r = {c: float(dv[f"{c}|real"].float().norm() / ks[f"{c}|real"].float().norm())
              for c in cids}
    ctl_r = {c: float(dv[f"{c}|ctl"].float().norm() / ks[f"{c}|ctl"].float().norm())
             for c in cids}
    weaker = sum(1 for c in cids if ctl_r[c] < real_r[c])
    check(0.3 < weaker / len(cids) < 0.7,
          f"ctl is not systematically the weaker edit: weaker in {weaker} of {len(cids)}")

    # --- the city map, which is the part the code cannot check on its own ----
    cc = R3.city_country_map(EDIT_SLICE)
    check(len(cc) > 70, f"the city map is populated, got {len(cc)}")
    pt = json.loads((EDIT_SLICE / "probes" / "place_types.json").read_text())
    check(not (set(cc) & set(pt["not_settlement"])),
          "[E-014]'s malformed places are excluded: no 'born in the city of Wisconsin'")
    geo = json.loads((EDIT_SLICE / "probes" / "geo.json").read_text())
    check(all(cc.get(cap) == country for country, cap in geo["capital"].items()),
          "every capital resolves to its own country")

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(R1.MODEL)
    t2c = R3.first_token_country(tok, cc)
    by_token = defaultdict(set)
    for city, country in cc.items():
        by_token[tok.encode(" " + city, add_special_tokens=False)[0]].add(country)
    check(len(t2c) == len(by_token),
          f"no first token is shared across countries: {len(by_token) - len(t2c)} dropped")

    # The hit test is NOT an equality against the injected country. The probes
    # ask for a city; a run that tested `top1 == country` would score the real
    # arm near zero and look like a finding.
    targets = R3.target_countries(EDIT_SLICE, R1.MODEL)
    check(set(cids) <= set(targets), "every subject has an [E-014] target country")
    check(len(set(targets.values())) > 10,
          f"the targets are spread, not one country: {len(set(targets.values()))}")
    for country in sorted(set(targets.values()))[:40]:
        cap = geo["capital"].get(country)
        if not cap:
            continue
        cap_tok = tok.encode(" " + cap, add_special_tokens=False)[0]
        check(t2c.get(cap_tok) == country,
              f"a top-1 of '{tok.decode([cap_tok])}' counts as landing in {country}")

    # --- the source ---------------------------------------------------------
    src = (ROOT / "agents" / "engineer" / "workspace" / "run_e003.py").read_text()
    check("R.top1_batch" in src, "the readout reuses [E-001]'s primitive, not a copy")
    check("model.trace" not in src,
          "no trace body lives here, so the APPLY_IDIOM and the editreach "
          "import constraint stay confined to run_e001")
    check("edit=None" not in src, "the base arm is not re-run")
    check("anchors_only" in src, "the gate can be run alone")
    check("checkpoint" in src, "the run is resumable")
    check('pairing"]["pairs"' in src, "the donor pairing is read, never recomputed")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"\nCity map: {len(cc)} cities, {len(t2c)} attributable first tokens, "
              f"0 ambiguous.")
        print(f"Magnitudes: ctl weaker in {weaker} of {len(cids)}; "
              f"median |ctl-real| {st.median([abs(ctl_r[c] - real_r[c]) for c in cids]):.4f}.")
        print("Extends [E-002]; only the readout changes. Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
