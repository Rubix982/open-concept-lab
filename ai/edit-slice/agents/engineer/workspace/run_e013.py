"""E-013 · The edit, with three controls. PILOT — read it before scaling.

For each usable chain: edit `outer` to a counterfactual country, then probe all three
facts under three conditions — baseline, the real edit, and the SAME-SUBJECT control
(an unrelated occupation edit on the same person, clamped to comparable magnitude).

The n=1 smoke test showed `inner_1` moving hard while `inner_2` stayed inert, which is
what subject-keyed leakage looks like rather than contraction. Only `inner_1` movement
in EXCESS of the same-subject control is evidence about contraction. See
agents/shared/decisions.md [E-013].
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
CONTROL_TMPL = "By profession, {} is a"
NATURAL = {"United States": "the United States", "United Kingdom": "the United Kingdom",
           "Netherlands": "the Netherlands", "Philippines": "the Philippines",
           "Czech Republic": "the Czech Republic",
           "People's Republic of China": "China"}


def nat(s: str) -> str:
    return NATURAL.get(s, s)


def usable_chains(chains: list[dict], min_auc: float = 0.8) -> list[dict]:
    """Chains held at all three legs under E-012's natural+paired measure.

    The file records `auc` and `rank_subject` but not `held`, so it is recomputed from
    the definition rather than read from a field that does not exist.
    """
    d = json.loads((ROOT / "results" /
                    "E-012-discrimination-natural-meta-llama_Llama-3.1-8B.json").read_text())
    ok: dict[str, dict[str, bool]] = {}
    for r in d["per_item"]:
        cid, pos = r["case_id"].split("|")
        ok.setdefault(cid, {})[pos] = (r["rank_subject"] == 1
                                       and r["auc"] is not None and r["auc"] >= min_auc)
    return [c for c in chains
            if all(ok.get(c["seed_case_id"], {}).get(p) for p in
                   ("inner_1", "inner_2", "outer"))]


def occupations(snap: Snapshot, qid: str) -> list[str]:
    out = []
    for s in snap.claims.get(qid, {}).get("P106", []):
        try:
            o = s["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        lab = snap.labels.get(o)
        if lab and lab != o:
            out.append(lab)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=12, help="pilot size; read before scaling")
    ap.add_argument("--seed", type=int, default=1538)
    ap.add_argument("--chunk", type=int, default=6, help="specs per optimisation trace")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    usable = usable_chains(chains)
    snap = Snapshot.load("2026-09-15")

    pool_country = sorted({nat(c["outer"]["answer"]) for c in chains})
    pool_occ = sorted({o for c in chains
                       for o in occupations(snap, c["inner_1"]["qid_subject"])})

    picked, specs = [], []
    for c in usable:
        occs = occupations(snap, c["inner_1"]["qid_subject"])
        if not occs:
            continue
        true_country = nat(c["outer"]["answer"])
        tgt_country = rng.choice([x for x in pool_country if x != true_country])
        tgt_occ = rng.choice([x for x in pool_occ if x not in occs])
        cid = c["seed_case_id"]
        specs += [
            EditSpec(f"{cid}|real", c["outer"]["prompt"], c["outer"]["subject"],
                     tgt_country, "real"),
            EditSpec(f"{cid}|ctl", CONTROL_TMPL.format(c["inner_1"]["subject"]),
                     c["inner_1"]["subject"], tgt_occ, "control"),
        ]
        picked.append({**c, "target_country": tgt_country, "true_country": true_country,
                       "target_occ": tgt_occ, "occupations": occs})
        if len(picked) >= args.n:
            break

    log = setup("run_e013", config={
        "ticket": "E-013", "model": MODEL, "layer": LAYER, "seed": args.seed,
        "n_pilot": len(picked), "n_usable_available": len(usable),
        "control_template": CONTROL_TMPL, "chunk": args.chunk,
        "editor": "ROME as configured by EasyEdit (C = I)"})
    log.info("%d usable chains available; piloting %d", len(usable), len(picked))

    m = connect(MODEL)

    deltas: dict[str, torch.Tensor] = {}
    for i in range(0, len(specs), args.chunk):
        grp = specs[i : i + args.chunk]
        log.info("optimising v* for specs %d-%d of %d", i + 1, i + len(grp), len(specs))
        deltas.update(compute_v_batch(m, grp, progress=lambda s, n: log.debug("  %d/%d", s, n)))

    k_stars = {sp.case_id: read_key_and_value(m, sp.prompt, sp.subject, LAYER)[0]
               for sp in specs}

    POS = ("inner_1", "inner_2", "outer")
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    results = []

    for c in picked:
        cid = c["seed_case_id"]
        prompts = [c[p]["prompt"] for p in POS]
        answers = [c["inner_1"]["answer"], nat(c["inner_2"]["answer"]), c["true_country"]]
        rows, spans = [], []
        for p, a in zip(prompts, answers):
            ids_p = tok(p).input_ids
            ids_a = tok(" " + a.lstrip(), add_special_tokens=False).input_ids
            rows.append(ids_p + ids_a)
            spans.append((len(ids_p), len(ids_a)))
        width = max(len(r) for r in rows)
        batch = torch.full((3, width), pad, dtype=torch.long)
        for j, r in enumerate(rows):
            batch[j, : len(r)] = torch.tensor(r)

        cond: dict[str, list[float]] = {}
        tops: dict[str, list[str]] = {}
        for name, key in (("base", None), ("real", f"{cid}|real"), ("ctl", f"{cid}|ctl")):
            if key is None:
                with m.trace(batch, remote=True):
                    lg = m.lm_head.output.float().save()
            else:
                lay, ks_cpu, dv_cpu = LAYER, k_stars[key], deltas[key]
                with m.trace(batch, remote=True):
                    dp = m.model.layers[lay].mlp.down_proj
                    k = dp.input
                    ks = ks_cpu.to(k.device, k.dtype)
                    dp.output = dp.output + ((k @ ks) / (ks @ ks)).unsqueeze(-1) \
                                            * dv_cpu.to(k.device, k.dtype)
                    lg = m.lm_head.output.float().save()
            L = lg.cpu()
            vals, top1 = [], []
            for j, (np_, na) in enumerate(spans):
                lp = torch.log_softmax(L[j], -1)
                # teacher-forced sum over the answer's tokens, never position one alone
                vals.append(float(sum(lp[np_ + t - 1, rows[j][np_ + t]] for t in range(na))))
                top1.append(tok.decode(int(lp[np_ - 1].argmax(-1))))
            cond[name] = vals
            tops[name] = top1

        results.append({"case_id": cid, "entailment": c["entailment"],
                        "true_country": c["true_country"],
                        "target_country": c["target_country"], "target_occ": c["target_occ"],
                        "answers": answers, "logp": cond, "top1": tops,
                        "delta_norm_real": float(deltas[f"{cid}|real"].norm()),
                        "delta_norm_ctl": float(deltas[f"{cid}|ctl"].norm())})
        log.info("%-6s outer %+.2f->%+.2f | inner_1 %+.2f->%+.2f (ctl %+.2f) | "
                 "inner_2 %+.2f->%+.2f (ctl %+.2f)", cid,
                 cond["base"][2], cond["real"][2],
                 cond["base"][0], cond["real"][0], cond["ctl"][0],
                 cond["base"][1], cond["real"][1], cond["ctl"][1])

    out = ROOT / "results" / f"E-013-pilot-{MODEL.replace('/', '_')}.json"
    out.write_text(json.dumps({"ticket": "E-013", "model": MODEL, "layer": LAYER,
                               "seed": args.seed, "control_template": CONTROL_TMPL,
                               "editor": "ROME as configured by EasyEdit (C = I)",
                               "results": results}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
