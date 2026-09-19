"""E-017 · Is the displacement keyed on the SUBJECT, or on the prompt's FORM?

[E-016] found ROME's `u·k*` normalisation pins the update coefficient to exactly 1 at the
subject's last token, and that any probe sharing the edit prompt's prefix has an identical
key there. Our probes share it by construction. This tests a probe where the subject
appears later, so nothing is pinned.

The trap this controls for: changing phrasing changes expressibility ([E-011]), so a late
form that simply does not work would look identical to "no leakage". Baseline possession on
both forms is measured first and the comparison is restricted to chains where both hold.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, retrying, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
LATE_TMPL = "The city where {} was born is"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--stall-wait", type=float, default=600)
    ap.add_argument("--max-stalls", type=int, default=12)
    args = ap.parse_args()

    e14 = json.loads((ROOT / "results" /
                      f"E-014-destination-{MODEL.replace('/', '_')}.json").read_text())
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    geo = json.loads((ROOT / "probes" / "geo.json").read_text())
    pt = json.loads((ROOT / "probes" / "place_types.json").read_text())
    pool = e14["pool"]
    cc = {c: k for c, k in geo["city_country"].items()
          if c not in set(pt["not_settlement"])}
    for ctry, cap in geo["capital"].items():
        cc[cap] = ctry

    deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{args.seed}.pt")
    kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{args.seed}.pt")
    rows = [r for r in e14["results"] if f"{r['case_id']}|real" in deltas]

    log = setup("run_e017", config={
        "ticket": "E-017", "model": MODEL, "layer": LAYER, "late_template": LATE_TMPL,
        "n_chains": len(rows), "pool": len(pool),
        "note": "same cached v* and k* as E-014; only the probe FORM varies"})
    log.info("%d chains; early vs late subject position, same edits", len(rows))

    m = connect(MODEL)
    cache_path = ROOT / "results" / "cache" / f"E017_L{LAYER}_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    def rank_top(prompt, edit=None):
        for attempt in range(args.max_stalls):
            try:
                sc = score_pairs(m, [(prompt, c) for c in pool], edit=edit)
                return pool[max(range(len(pool)), key=lambda j: sc[j])]
            except Exception as exc:  # noqa: BLE001
                if attempt == args.max_stalls - 1:
                    raise
                log.warning("scoring failed (%s); parking %.0f min",
                            type(exc).__name__, args.stall_wait / 60)
                time.sleep(args.stall_wait)

    for n, r in enumerate(rows, 1):
        cid = r["case_id"]
        if cid in done:
            continue
        c = chains[cid]
        subj, truth = c["inner_1"]["subject"], c["inner_1"]["answer"]
        early, late = c["inner_1"]["prompt"], LATE_TMPL.format(subj)
        ed = (LAYER, kstars[f"{cid}|real"], deltas[f"{cid}|real"])
        rec = {"case_id": cid, "subject": subj, "truth": truth,
               "target": r["target_country"], "late_prompt": late,
               "base_early": rank_top(early), "base_late": rank_top(late),
               "post_early": rank_top(early, ed), "post_late": rank_top(late, ed)}
        rec["holds_early"] = rec["base_early"] == truth
        rec["holds_late"] = rec["base_late"] == truth
        rec["hit_early"] = cc.get(rec["post_early"]) == r["target_country"]
        rec["hit_late"] = cc.get(rec["post_late"]) == r["target_country"]
        done[cid] = rec
        cache_path.write_text(json.dumps(done))
        if n % 8 == 0 or n == len(rows):
            log.info("  %d/%d", n, len(rows))

    rs = list(done.values())
    both = [r for r in rs if r["holds_early"] and r["holds_late"]]
    log.info("")
    log.info("BASELINE possession (the E-011 control):")
    log.info("   early form holds the true city : %d/%d", sum(r["holds_early"] for r in rs), len(rs))
    log.info("   late  form holds the true city : %d/%d", sum(r["holds_late"] for r in rs), len(rs))
    log.info("   BOTH hold (the comparable set) : %d/%d", len(both), len(rs))

    if len(both) < 10:
        log.error("only %d chains hold on both forms — NULL branch, experiment is unrun, "
                  "not negative", len(both))
    else:
        e = sum(r["hit_early"] for r in both)
        l = sum(r["hit_late"] for r in both)
        eo = sum(1 for r in both if r["hit_early"] and not r["hit_late"])
        lo = sum(1 for r in both if r["hit_late"] and not r["hit_early"])
        log.info("")
        log.info("RELOCATION into the target country, on the %d comparable chains:", len(both))
        log.info("   early subject (prefix shared, coefficient pinned) : %2d/%d = %3.0f%%",
                 e, len(both), 100 * e / len(both))
        log.info("   late  subject (no shared prefix, not pinned)      : %2d/%d = %3.0f%%",
                 l, len(both), 100 * l / len(both))
        log.info("   paired gap : %+.1f pp   (early-only %d, late-only %d)",
                 100 * (e - l) / len(both), eo, lo)

    # is anything actually pinned on the late form?
    log.info("")
    log.info("COEFFICIENT at each form's subject-last token (1.0 = pinned):")
    tok = m.tokenizer
    for r in rs[:4]:
        c = chains[r["case_id"]]
        ks = kstars[f"{r['case_id']}|real"].float()
        for label, prompt in (("early", c["inner_1"]["prompt"]), ("late", r["late_prompt"])):
            idx = subject_last_index(tok, prompt, r["subject"])

            def once():
                with m.trace(prompt, remote=True):
                    k = m.model.layers[LAYER].mlp.down_proj.input[0, idx].half().save()
                return k

            k = retrying(once, what="probe key").float()
            log.info("   %-6s %-5s coeff %.4f   %r", r["case_id"], label,
                     float((k @ ks) / (ks @ ks)), prompt)

    out = ROOT / "results" / f"E-017-form-{MODEL.replace('/', '_')}.json"
    out.write_text(json.dumps({"ticket": "E-017", "late_template": LATE_TMPL,
                               "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
