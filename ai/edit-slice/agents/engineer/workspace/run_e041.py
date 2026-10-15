"""E-041 · Attention or MLP? Decomposing what reorients the subject key. [T-078]

[T-077] established the subject key reorients by DIRECTION — cosine 0.984 -> 0.471 across
depth, norm ratio flat — and refused the next step: "a falling cosine is consistent with
attention mixing, with MLP writes at the subject position, and with anything else that
reorients the residual stream."

**This does not run the test [T-078] proposed, and that is deliberate.** Comparing
attention PATTERNS between the edit form and a reformulated one largely confirms itself:
`"{} was born in the city of"` puts the subject at the start with nothing before it,
`"The city where {} was born is"` puts three tokens before it. Their patterns must differ
because one position has context available and the other does not.

What this measures instead is the accumulation itself. The residual stream at the subject's
last token is a sum,

    h(L) = embed + SUM_{l<L} [ attn_out(l) + mlp_out(l) ]

so the divergence between two forms' keys accumulates term by term and every term is
readable:

    D_attn(L) = || SUM_{l<L} ( attn_out_form(l) - attn_out_edit(l) ) ||
    D_mlp(L)  = || SUM_{l<L} ( mlp_out_form(l)  - mlp_out_edit(l)  ) ||

DIRECT WRITES, NOT CAUSATION. The MLP's input depends on attention, so attention can drive
D_mlp indirectly. The causal version is an ablation and is deferred — confound 1.

DELIVERY, NOT EFFECT. [E-028d], 2.96x.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
N_LAYERS = 32
PROBE = [0, 3, 5, 8, 12, 16, 24, 31]
EDIT_FORM = "{} was born in the city of"
#: ONLY THE PREFIX MATTERS, and the first version of this list did not respect that.
#: Under causal attention the representation at the subject's LAST TOKEN depends on the
#: tokens up to and including the subject and on nothing after — which is the property
#: this whole project rests on. So the first run's five forms collapsed to three distinct
#: prefixes: `"{} died in the city of"` is bit-identical to the edit form (it produced
#: exact zeros at every layer), and `"The city where " + EDIT_FORM` is bit-identical to
#: the late clause. Confound 2's control never ran, and the verdict was computed over a
#: duplicate plus an infinity. Forms are now keyed by prefix and asserted distinct.
#:
#: Confound 2, properly: `matched filler` carries a prefix of the SAME TOKEN COUNT as the
#: late clause's (5 including BOS) and unrelated content. If it tracks the late clause the
#: effect is about POSITION; if it tracks the edit form it is about CONTENT.
FORMS = {
    "edit form":      EDIT_FORM,
    "late clause":    "The city where {} was born is",
    "possessive":     "The birthplace of {} is the city of",
    "matched filler": "Among other things {} was born in the city of",
}
NAMES = list(FORMS)
RATIO = 2.0

#: [E-020]'s cosine at each probed layer, so the accumulation can be read against the
#: quantity it is meant to explain. Copied from that run's table, not recomputed.
E020_COSINE = {0: 0.984, 3: 0.962, 5: 0.951, 8: 0.898, 12: 0.812,
                16: 0.733, 24: 0.598, 31: 0.471}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=16)
    a = ap.parse_args()

    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    ks = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
    # The cache is read only for its SUBJECT LIST, not its values — but a partial cache
    # would still silently yield fewer subjects than asked for, and [E-033] is the record
    # of what that costs. Named and refused rather than absorbed.
    real = [k.split("|")[0] for k in ks if k.endswith("|real")]
    cids = [c for c in real[: a.n] if c in chains]
    want = set(real[: a.n])
    missing = want - set(chains)
    if len(cids) < a.n:
        raise SystemExit(
            f"asked for {a.n} subjects, the cache and chain file yield {len(cids)} "
            f"({len(real)} cached keys, {len(missing)} without a chain record). "
            f"Refusing rather than running a smaller study than the ticket scoped.")

    log = setup("run_e041", config={
        "ticket": "E-041", "thread": "T-078", "model": MODEL, "n_subjects": len(cids),
        "forms": NAMES, "probe_layers": PROBE, "layers_read": N_LAYERS,
        "measure": "cumulative ||sum of per-layer deltas|| at the subject's last token",
        "limit": "DIRECT WRITES, not causation — the MLP's input depends on attention"})
    log.info("%d subjects, %d forms, every layer read for the cumulative sum",
             len(cids), len(NAMES))

    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    # acc[form][layer] -> list over subjects of (D_attn, D_mlp)
    acc = {f: {L: [] for L in PROBE} for f in NAMES}

    for n, cid in enumerate(cids, 1):
        subj = chains[cid]["inner_1"]["subject"]
        prompts = [t.format(subj) for t in FORMS.values()]
        # Assert the forms differ where it matters. Two of the first version's five did
        # not, and the run reported numbers for both anyway.
        pres = {p[: p.index(subj) + len(subj)] for p in prompts}
        if len(pres) != len(prompts):
            raise SystemExit(
                f"{len(prompts)} forms share only {len(pres)} distinct prefixes up to the "
                f"subject's last token. Under causal attention those are the same probe: "
                f"{sorted(pres)}")
        ids = [tok(p).input_ids for p in prompts]
        try:
            idxs = [subject_last_index(tok, p, subj) for p in prompts]
        except ValueError:
            log.debug("%s: subject not locatable in one of its forms; skipped", subj)
            continue
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)

        def once(bt=batch):
            # UNROLLED. [O-008]: a loop inside a trace body raises nothing and returns
            # zero saves. These 64 lines are generated, not typed, and N_LAYERS is
            # asserted against them so the two cannot drift apart.
            assert N_LAYERS == 32, "unrolled saves must match N_LAYERS"
            with _quiet_stdout(), m.trace(bt, remote=True):
                a0 = m.model.layers[0].self_attn.output[0].half().save()
                p0 = m.model.layers[0].mlp.output.half().save()
                a1 = m.model.layers[1].self_attn.output[0].half().save()
                p1 = m.model.layers[1].mlp.output.half().save()
                a2 = m.model.layers[2].self_attn.output[0].half().save()
                p2 = m.model.layers[2].mlp.output.half().save()
                a3 = m.model.layers[3].self_attn.output[0].half().save()
                p3 = m.model.layers[3].mlp.output.half().save()
                a4 = m.model.layers[4].self_attn.output[0].half().save()
                p4 = m.model.layers[4].mlp.output.half().save()
                a5 = m.model.layers[5].self_attn.output[0].half().save()
                p5 = m.model.layers[5].mlp.output.half().save()
                a6 = m.model.layers[6].self_attn.output[0].half().save()
                p6 = m.model.layers[6].mlp.output.half().save()
                a7 = m.model.layers[7].self_attn.output[0].half().save()
                p7 = m.model.layers[7].mlp.output.half().save()
                a8 = m.model.layers[8].self_attn.output[0].half().save()
                p8 = m.model.layers[8].mlp.output.half().save()
                a9 = m.model.layers[9].self_attn.output[0].half().save()
                p9 = m.model.layers[9].mlp.output.half().save()
                a10 = m.model.layers[10].self_attn.output[0].half().save()
                p10 = m.model.layers[10].mlp.output.half().save()
                a11 = m.model.layers[11].self_attn.output[0].half().save()
                p11 = m.model.layers[11].mlp.output.half().save()
                a12 = m.model.layers[12].self_attn.output[0].half().save()
                p12 = m.model.layers[12].mlp.output.half().save()
                a13 = m.model.layers[13].self_attn.output[0].half().save()
                p13 = m.model.layers[13].mlp.output.half().save()
                a14 = m.model.layers[14].self_attn.output[0].half().save()
                p14 = m.model.layers[14].mlp.output.half().save()
                a15 = m.model.layers[15].self_attn.output[0].half().save()
                p15 = m.model.layers[15].mlp.output.half().save()
                a16 = m.model.layers[16].self_attn.output[0].half().save()
                p16 = m.model.layers[16].mlp.output.half().save()
                a17 = m.model.layers[17].self_attn.output[0].half().save()
                p17 = m.model.layers[17].mlp.output.half().save()
                a18 = m.model.layers[18].self_attn.output[0].half().save()
                p18 = m.model.layers[18].mlp.output.half().save()
                a19 = m.model.layers[19].self_attn.output[0].half().save()
                p19 = m.model.layers[19].mlp.output.half().save()
                a20 = m.model.layers[20].self_attn.output[0].half().save()
                p20 = m.model.layers[20].mlp.output.half().save()
                a21 = m.model.layers[21].self_attn.output[0].half().save()
                p21 = m.model.layers[21].mlp.output.half().save()
                a22 = m.model.layers[22].self_attn.output[0].half().save()
                p22 = m.model.layers[22].mlp.output.half().save()
                a23 = m.model.layers[23].self_attn.output[0].half().save()
                p23 = m.model.layers[23].mlp.output.half().save()
                a24 = m.model.layers[24].self_attn.output[0].half().save()
                p24 = m.model.layers[24].mlp.output.half().save()
                a25 = m.model.layers[25].self_attn.output[0].half().save()
                p25 = m.model.layers[25].mlp.output.half().save()
                a26 = m.model.layers[26].self_attn.output[0].half().save()
                p26 = m.model.layers[26].mlp.output.half().save()
                a27 = m.model.layers[27].self_attn.output[0].half().save()
                p27 = m.model.layers[27].mlp.output.half().save()
                a28 = m.model.layers[28].self_attn.output[0].half().save()
                p28 = m.model.layers[28].mlp.output.half().save()
                a29 = m.model.layers[29].self_attn.output[0].half().save()
                p29 = m.model.layers[29].mlp.output.half().save()
                a30 = m.model.layers[30].self_attn.output[0].half().save()
                p30 = m.model.layers[30].mlp.output.half().save()
                a31 = m.model.layers[31].self_attn.output[0].half().save()
                p31 = m.model.layers[31].mlp.output.half().save()
            saved = {
                "a0": a0, "p0": p0,
                "a1": a1, "p1": p1,
                "a2": a2, "p2": p2,
                "a3": a3, "p3": p3,
                "a4": a4, "p4": p4,
                "a5": a5, "p5": p5,
                "a6": a6, "p6": p6,
                "a7": a7, "p7": p7,
                "a8": a8, "p8": p8,
                "a9": a9, "p9": p9,
                "a10": a10, "p10": p10,
                "a11": a11, "p11": p11,
                "a12": a12, "p12": p12,
                "a13": a13, "p13": p13,
                "a14": a14, "p14": p14,
                "a15": a15, "p15": p15,
                "a16": a16, "p16": p16,
                "a17": a17, "p17": p17,
                "a18": a18, "p18": p18,
                "a19": a19, "p19": p19,
                "a20": a20, "p20": p20,
                "a21": a21, "p21": p21,
                "a22": a22, "p22": p22,
                "a23": a23, "p23": p23,
                "a24": a24, "p24": p24,
                "a25": a25, "p25": p25,
                "a26": a26, "p26": p26,
                "a27": a27, "p27": p27,
                "a28": a28, "p28": p28,
                "a29": a29, "p29": p29,
                "a30": a30, "p30": p30,
                "a31": a31, "p31": p31
            }
            with _quiet_stdout():
                return {k: v.float() for k, v in saved.items()}

        got = retrying(once, what=f"{subj!r}")
        # Per-layer contribution at each form's own subject index.
        attn = {j: [got[f"a{lay}"][j, idxs[j]] for lay in range(N_LAYERS)]
                for j in range(len(NAMES))}
        mlp = {j: [got[f"p{lay}"][j, idxs[j]] for lay in range(N_LAYERS)]
               for j in range(len(NAMES))}
        for j, name in enumerate(NAMES):
            if name == "edit form":
                continue
            da = torch.zeros_like(attn[0][0])
            dm = torch.zeros_like(mlp[0][0])
            for lay in range(N_LAYERS):
                da = da + (attn[j][lay] - attn[0][lay])
                dm = dm + (mlp[j][lay] - mlp[0][lay])
                if lay in acc[name]:
                    acc[name][lay].append((float(da.norm()), float(dm.norm())))
        if n % 4 == 0 or n == len(cids):
            log.info("  %d/%d subjects", n, len(cids))

    report(acc, log)


def report(acc, log) -> None:
    log.info("")
    log.info("E-041 — what writes the divergence at the subject's last token")
    log.info("cumulative ||sum of per-layer deltas|| against the edit form. "
             "DIRECT WRITES, not causation.")
    verdicts = {}
    for name in NAMES:
        if name == "edit form":
            continue
        log.info("")
        log.info("%s", name.upper())
        log.info("%-8s%12s%12s%10s%12s", "layer", "D_attn", "D_mlp", "ratio",
                 "E-020 cos")
        rats = []
        for L in PROBE:
            v = acc[name][L]
            if not v:
                continue
            da, dm = st.median([x[0] for x in v]), st.median([x[1] for x in v])
            r = da / dm if dm else float("inf")
            rats.append(r)
            log.info("%-8d%12.2f%12.2f%10.2f%12.3f", L, da, dm, r,
                     E020_COSINE.get(L, float("nan")))
        if rats:
            deep = st.median(rats[len(rats) // 2:])
            verdicts[name] = deep

    log.info("")
    if not verdicts:
        log.error("no form produced a comparison — nothing to report")
        return
    med = st.median(list(verdicts.values()))
    if med >= RATIO:
        log.info("VERDICT: ATTENTION WRITES IT — D_attn exceeds D_mlp by %.1fx in the "
                 "deeper half, median across forms. Context mixing is the mechanism and "
                 "[T-077]'s leading candidate is confirmed. DIRECT writes only: the "
                 "ablation in confound 1 is what would make this causal.", med)
    elif med <= 1 / RATIO:
        log.warning("VERDICT: MLP WRITES IT — D_mlp exceeds D_attn by %.1fx in the deeper "
                    "half. The reorientation is written by the MLP at that position and "
                    "the attention account named in [E-020] is WRONG. Nothing in the "
                    "record predicted this.", 1 / med)
    else:
        log.info("VERDICT: BOTH — the ratio sits at %.2f, inside [%.2f, %.2f]. The "
                 "decomposition does not separate them, and confound 1's ablation becomes "
                 "necessary rather than optional.", med, 1 / RATIO, RATIO)

    out = ROOT / "results" / "E-041-reorientation.json"
    out.write_text(json.dumps({"ticket": "E-041", "thread": "T-078", "probe": PROBE,
                               "forms": NAMES, "deep_ratio": verdicts,
                               "per_layer": {f: {str(L): acc[f][L] for L in PROBE}
                                             for f in NAMES if f != "edit form"}},
                              indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
