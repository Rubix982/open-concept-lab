"""E-030 · Is GPT-J's higher different-subject floor real, or unfamiliarity? [T-082]

[E-027] measured GPT-J's different-subject floor at 0.155 at the edit layer against Llama's
0.082, and §4.3 of the paper narrows [E-018] to a Llama statement on that basis. The
narrowing is flagged PLAUSIBLE because the subjects were possession-gated on *Llama* and
run on GPT-J unfiltered: if GPT-J does not know these people, their name tokens may share a
generic "unfamiliar person" direction and inflate the floor by construction.

This resolves it by SPLITTING rather than by measuring a rate: run the shipped possession
filter on GPT-J, partition into HELD and NOT-HELD, and compare the floor in each.

    ARCHITECTURAL  floors differ by < 0.05 at the edit layer -> the narrowing is confirmed
    FAMILIARITY    NOT-HELD exceeds HELD by >= 0.10 AND HELD sits near Llama's 0.082
                   -> the narrowing is withdrawn and comes out of the packet
    MIXED          anything between -> report both, claim neither

The pool confound is ASYMMETRIC and that is what makes this runnable: [E-023] showed a
candidate pool undercounts, which moves subjects from HELD into NOT-HELD. That DILUTES the
contrast rather than manufacturing one — so a FAMILIARITY verdict survives the objection
and an ARCHITECTURAL verdict is weakened by it.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from possession import Edit, FilterConfig, run  # noqa: E402
from remote import _quiet_stdout, connect, retrying, score_pairs  # noqa: E402
from run_e027 import ARCH, FORMS, OTHER, resolve_arch  # noqa: E402
from edit import subject_last_index  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "EleutherAI/gpt-j-6b"
FRACTIONS = (0.15, 0.63, 1.00)
LLAMA_FLOOR = 0.082              # [E-018], at the edit layer
ARCH_BAND, FAM_BAND, MIN_GROUP = 0.05, 0.10, 8


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=36)
    ap.add_argument("--seed", type=int, default=1538)
    args = ap.parse_args()

    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    picked = [c for c in chains if c["usable"]][: args.n]
    edits = [Edit(case_id=c["seed_case_id"], prompt=c["inner_1"]["prompt"],
                  subject=c["inner_1"]["subject"], true_answer=c["inner_1"]["answer"],
                  relation_id="P19") for c in picked]

    log = setup("run_e030", config={
        "ticket": "E-030", "thread": "T-082", "model": MODEL, "n": len(edits),
        "fractions": list(FRACTIONS), "llama_floor_reference": LLAMA_FLOOR,
        "bands": {"ARCHITECTURAL": f"<{ARCH_BAND}", "FAMILIARITY": f">={FAM_BAND}"},
        "note": "subjects were possession-gated on Llama; this re-gates them on GPT-J"})

    m = connect(MODEL)
    cfg = FilterConfig(model=MODEL, seed=args.seed)
    cache = ROOT / "results" / "cache" / f"E030_poss_{cfg.fingerprint.replace('|', '_')}.json"
    rep = run(edits, cfg, lambda pairs: score_pairs(m, pairs), cache_path=cache,
              reference=edits,
              progress=lambda i, n: log.info("  possession %d/%d", i, n) if i % 8 == 0
              else None)
    held = {r.case_id for r in rep.results if r.held(require_lift=True)}
    log.info("GPT-J possession: %d HELD / %d scored (%.0f%%)",
             len(held), len(rep.results), 100 * len(held) / max(1, len(rep.results)))

    arch, n_layers, d_mlp = resolve_arch(m, MODEL)
    layers = sorted({min(n_layers - 1, round(f * (n_layers - 1))) for f in FRACTIONS})
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    scored = [c for c in picked if any(r.case_id == c["seed_case_id"] for r in rep.results)]
    acc: dict[int, dict[str, list[float]]] = {
        L: {"held|floor": [], "held|same": [], "notheld|floor": [], "notheld|same": []}
        for L in layers}

    for n, c in enumerate(scored):
        subj = c["inner_1"]["subject"]
        other = scored[(n + 1) % len(scored)]["inner_1"]["subject"]
        if other == subj:
            continue
        grp = "held" if c["seed_case_id"] in held else "notheld"
        prompts = [t.format(subj) for t in FORMS.values()] + [
            FORMS["edit form"].format(other)]
        owners = [subj] * len(FORMS) + [other]
        ids = [tok(p).input_ids for p in prompts]
        idxs = [subject_last_index(tok, p, s) for p, s in zip(prompts, owners)]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)

        for L in layers:
            def once(L=L):
                with _quiet_stdout(), m.trace(batch, remote=True):
                    k = ARCH[arch](m, L).input.half().save()
                with _quiet_stdout():
                    return k.float()
            keys = retrying(once, what=f"L{L} {subj!r}")
            kstar = keys[0, idxs[0]]
            den = float(kstar @ kstar)
            names = list(FORMS) + [OTHER]
            vals = {f: float((keys[j, idxs[j]] @ kstar) / den)
                    for j, f in enumerate(names)}
            acc[L][f"{grp}|floor"].append(vals[OTHER])
            # same-subject reference: the reordered forms, which is what the floor is
            # compared AGAINST in [E-027]'s table
            acc[L][f"{grp}|same"].append(
                st.mean([vals["late clause"], vals["possessive"]]))
        if (n + 1) % 6 == 0:
            log.info("  coefficients %d/%d", n + 1, len(scored))

    report(acc, layers, n_layers, len(held), len(scored), log)


def report(acc, layers, n_layers, n_held, n_total, log) -> None:
    edit_layer = layers[0]
    nh = {g: len(acc[edit_layer][f"{g}|floor"]) for g in ("held", "notheld")}
    log.info("")
    log.info("E-030 — different-subject floor by GPT-J possession (HELD %d, NOT-HELD %d)",
             nh["held"], nh["notheld"])
    log.info("%-10s%-8s%12s%12s", "layer", "group", "floor", "same-subj")
    means = {}
    for L in layers:
        for g in ("held", "notheld"):
            f = acc[L][f"{g}|floor"]
            sm = acc[L][f"{g}|same"]
            if not f:
                continue
            means[(L, g)] = st.mean(f)
            log.info("%-10s%-8s%12.3f%12.3f", f"L{L} (f={L/(n_layers-1):.2f})",
                     g.upper(), st.mean(f), st.mean(sm))

    log.info("")
    if min(nh.values()) < MIN_GROUP:
        log.warning("UNDERPOWERED: smallest group has %d subjects (need %d). Report the "
                    "counts, not a difference — §4.3's flag stays as it is.",
                    min(nh.values()), MIN_GROUP)
    else:
        h, nhd = means[(edit_layer, "held")], means[(edit_layer, "notheld")]
        gap = nhd - h
        log.info("at the edit layer: HELD %.3f · NOT-HELD %.3f · gap %+.3f "
                 "(Llama reference %.3f)", h, nhd, gap, LLAMA_FLOOR)
        same_gap = abs(st.mean(acc[edit_layer]["held|same"])
                       - st.mean(acc[edit_layer]["notheld|same"]))
        if same_gap > 0.15:
            log.warning("CONFOUND 3 FIRES: the two groups also differ by %.3f in the "
                        "SAME-subject coefficient, so the split is picking up something "
                        "other than familiarity and neither verdict holds.", same_gap)
        elif abs(gap) < ARCH_BAND:
            log.info("VERDICT: ARCHITECTURAL — the floors differ by only %.3f, so "
                     "familiarity is not driving it. §4.3's narrowing of [E-018] to a "
                     "Llama fact is CONFIRMED and the flag is upgraded.", abs(gap))
            log.info("  caveat, and it belongs beside this verdict rather than under it: "
                     "the pool confound weakens THIS direction specifically — "
                     "undercounting moves subjects into NOT-HELD and dilutes the "
                     "contrast, so a small gap is the outcome a bad pool would also "
                     "produce.")
        elif gap >= FAM_BAND and h < LLAMA_FLOOR + ARCH_BAND:
            log.warning("VERDICT: FAMILIARITY — NOT-HELD exceeds HELD by %.3f and the "
                        "HELD floor (%.3f) sits near Llama's %.3f. The high floor was "
                        "unfamiliar names. §4.3's narrowing is WITHDRAWN and the sentence "
                        "comes out of the packet.", gap, h, LLAMA_FLOOR)
        else:
            log.info("VERDICT: MIXED — gap %+.3f with a HELD floor of %.3f. Report both "
                     "groups and claim neither; §4.3's flag stays.", gap, h)

    out = ROOT / "results" / "E-030-floor-by-possession.json"
    out.write_text(json.dumps(
        {"ticket": "E-030", "thread": "T-082", "model": MODEL,
         "n_held": n_held, "n_scored": n_total, "group_n": nh,
         "llama_floor": LLAMA_FLOOR,
         "means": {f"L{L}|{g}": v for (L, g), v in means.items()},
         "per_subject": {f"L{L}": acc[L] for L in layers}}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
