"""E-021 · Which positions does the relocation actually depend on?

[T-067]. Everything from [E-013] to [E-020] is behavioural — vary an input, read an
output. [E-016] showed the coefficient at the subject's last token is analytically 1, but
a coefficient of 1 at a position that contributes nothing would give the same numbers.

Four arms, identical except for which positions receive the edit vector:

    A  full    all positions            reproduces [E-014] — the gate
    B  only    the subject's last only  sufficiency
    C  except  every position but it    necessity
    D  none    baseline

Same cached v* and k*; only the mask varies. Reports the masked coefficient MASS per arm,
because the subject token carries the largest coefficient by construction — "removing it
kills the effect" is unsurprising if it also removes most of the magnitude.
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
from remote import _quiet_stdout, connect, retrying, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
#: Arm E is the one that makes C interpretable. The subject's last token carries ~67% of
#: the coefficient mass, so "except" removes position AND magnitude together, and E-016's
#: scale test showed 0.27x breaks relocation on its own. E restores the magnitude the mask
#: removed, leaving position as the only difference from A.
ARMS = [("A_full", "all"), ("B_only", "only"), ("C_except", "except"),
        ("E_except_rescaled", "except"), ("D_none", None)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--n", type=int, default=0, help="0 = all available")
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
    if args.n:
        rows = rows[: args.n]

    log = setup("run_e021", config={
        "ticket": "E-021", "thread": "T-067", "model": MODEL, "layer": LAYER,
        "arms": [a for a, _ in ARMS], "n_chains": len(rows),
        "note": "same cached v* and k* as E-014; only the position mask varies"})
    log.info("%d chains x 4 arms; gate is arm A reproducing E-014's 67%%", len(rows))

    m = connect(MODEL)
    tok = m.tokenizer
    cache_path = ROOT / "results" / "cache" / f"E021b_L{LAYER}_s{args.seed}.json"
    done: dict[str, dict] = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    for n, r in enumerate(rows, 1):
        cid = r["case_id"]
        if cid in done:
            continue
        c = chains[cid]
        p1, subj = c["inner_1"]["prompt"], c["inner_1"]["subject"]
        idx = subject_last_index(tok, p1, subj)
        kstar = kstars[f"{cid}|real"].float()
        dv = deltas[f"{cid}|real"]
        den = float(kstar @ kstar)

        # Coefficient mass by position, so a necessity result can be read against how
        # much magnitude each mask removed rather than assumed independent of it.
        def keys_once():
            with _quiet_stdout(), m.trace(p1, remote=True):
                a = m.model.layers[LAYER].mlp.down_proj.input[0].half().save()
            with _quiet_stdout():
                return a.float()

        keys = retrying(keys_once, what=f"keys {cid}")
        coeffs = (keys @ kstar) / den
        total = float(coeffs.abs().sum())
        at_subj = float(coeffs[idx].abs())

        rec = {"case_id": cid, "target": r["target_country"], "was": r["was"],
               "subject_index": idx, "mass_total": total, "mass_at_subject": at_subj,
               "mass_share_at_subject": at_subj / total if total else 0.0,
               "top1": {}, "in_target": {}}
        for arm, mode in ARMS:
            if mode is None:
                ed = None
            elif arm == "E_except_rescaled":
                share = at_subj / total if total else 0.0
                gain = 1.0 / (1.0 - share) if share < 0.999 else 1.0
                ed = (LAYER, kstar, den, dv, mode, idx, gain)
            else:
                ed = (LAYER, kstar, den, dv, mode, idx)
            for attempt in range(args.max_stalls):
                try:
                    sc = score_pairs(m, [(p1, city) for city in pool], edit=ed)
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == args.max_stalls - 1:
                        raise
                    log.warning("%s %s failed (%s); parking %.0f min", cid, arm,
                                type(exc).__name__, args.stall_wait / 60)
                    time.sleep(args.stall_wait)
            top = pool[max(range(len(pool)), key=lambda j: sc[j])]
            rec["top1"][arm] = top
            rec["in_target"][arm] = cc.get(top) == r["target_country"]
        done[cid] = rec
        cache_path.write_text(json.dumps(done))
        if n % 5 == 0 or n == len(rows):
            log.info("  %d/%d", n, len(rows))

    rs = list(done.values())
    nn = len(rs)
    log.info("")
    log.info("%-12s%-26s%10s", "arm", "positions receiving delta", "in target")
    labels = {"A_full": "all", "B_only": "subject's last token only",
              "C_except": "all but the subject's last",
              "E_except_rescaled": "all but it, mass restored",
              "D_none": "none (baseline)"}
    rates = {}
    for arm, _ in ARMS:
        hit = sum(r["in_target"][arm] for r in rs)
        rates[arm] = hit / nn
        log.info("%-12s%-26s%7d/%d = %.0f%%", arm, labels[arm], hit, nn, 100 * hit / nn)

    log.info("")
    log.info("coefficient mass at the subject's last token: mean %.1f%% of the prompt total",
             100 * sum(r["mass_share_at_subject"] for r in rs) / nn)
    log.info("  (so arm C removes ~%.0f%% of the magnitude as well as the position)",
             100 * sum(r["mass_share_at_subject"] for r in rs) / nn)

    log.info("")
    if rates["A_full"] < 0.55:
        log.error("GATE FAILED: arm A is %.0f%%, not E-014's 67%%. The masking changed the "
                  "full-edit result, so the other three arms are not interpretable.",
                  100 * rates["A_full"])
    else:
        log.info("gate passed: arm A %.0f%% against E-014's 67%%", 100 * rates["A_full"])
        suff = rates["B_only"] >= rates["A_full"] - 0.10
        nec_raw = rates["C_except"] <= rates["D_none"] + 0.10
        nec_fair = rates["E_except_rescaled"] <= rates["D_none"] + 0.10
        log.info("sufficiency  (B >= A - 10pp)          : %s", "YES" if suff else "NO")
        log.info("necessity    (C <= D + 10pp)          : %s  <- confounded with magnitude",
                 "YES" if nec_raw else "NO")
        log.info("necessity    (E <= D + 10pp, mass restored): %s  <- the real test",
                 "YES" if nec_fair else "NO")
        if nec_fair and not suff:
            log.warning("necessary but not sufficient — the single-position story is "
                        "incomplete")

    out = ROOT / "results" / f"E-021-positions-{MODEL.replace('/', '_')}.json"
    out.write_text(json.dumps({"ticket": "E-021", "model": MODEL, "layer": LAYER,
                               "rates": rates, "results": rs}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
