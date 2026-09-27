"""E-032 · Does the pinning hold at frontier scale? 8B -> 70B -> 405B. [T-080]

Coefficient measurement needs NO gradients — one forward pass, save the MLP input at the
subject's last token. That is `basic_trace`, which every hosted model supports, so the
scale question costs ~40 traces instead of the days an EDIT at 405B would.

Three claims, and only the first is derived:

    ANALYTIC   prefix-sharing probes sit at exactly 1.000. Follows from causal attention
               and ROME's u·k* division; neither cares about parameter count. Anything
               else means the derivation or this code is wrong, which is the more
               interesting outcome.
    DECAY      reordered probes fall with depth. NOT derived. No reason it must survive a
               16x parameter increase.
    FLOOR      different-subject separation. NOT derived. [E-030] established it is
               architectural rather than a familiarity artifact; whether it is also
               scale-dependent is open.

**Two caveats that are not symmetric between the models.**

Llama-3.1-70B is a BASE model, so it is the clean scale comparison against 8B — same
family, same training recipe, same tokenizer, 2.5x the layers.

Llama-3.1-405B-Instruct is the only 405B hosted, and it is INSTRUCTION-TUNED. So its arm
varies scale AND post-training together. A difference there cannot be attributed to scale
alone, and this file must not let a table imply otherwise. Instruction tuning is exactly
the kind of thing that could move subject representations, which is the quantity measured
here.
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
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402
from run_e027 import FORMS, OTHER  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FRACTIONS = (0.00, 0.06, 0.10, 0.16, 0.23, 0.32, 0.55, 1.00)
M70 = ("meta-llama/Llama-3.1-70B", [0, 5, 8, 13, 18, 25, 43, 79], "base")
M405 = ("meta-llama/Llama-3.1-405B-Instruct", [0, 8, 13, 20, 29, 40, 69, 125], "instruct")
#: Llama-3.1-8B at the same fractions, from [E-031], as the reference profile.
REF_8B = {0.00: 0.992, 0.06: 0.960, 0.10: 0.930, 0.16: 0.951,
          0.23: 0.900, 0.32: 0.858, 0.55: 0.700, 1.00: 0.598}
INVARIANT_BAND = 0.15
EXACT = 1e-4


def keys_70(m, batch, layers):
    assert layers == [0, 5, 8, 13, 18, 25, 43, 79], "unrolled saves must match layers"

    def once():
        with _quiet_stdout(), m.trace(batch, remote=True):
            a0 = m.model.layers[0].mlp.down_proj.input.half().save()
            a5 = m.model.layers[5].mlp.down_proj.input.half().save()
            a8 = m.model.layers[8].mlp.down_proj.input.half().save()
            a13 = m.model.layers[13].mlp.down_proj.input.half().save()
            a18 = m.model.layers[18].mlp.down_proj.input.half().save()
            a25 = m.model.layers[25].mlp.down_proj.input.half().save()
            a43 = m.model.layers[43].mlp.down_proj.input.half().save()
            a79 = m.model.layers[79].mlp.down_proj.input.half().save()
        saved = {0: a0, 5: a5, 8: a8, 13: a13, 18: a18, 25: a25, 43: a43, 79: a79}
        with _quiet_stdout():
            return {L: v.float() for L, v in saved.items()}
    return once


def keys_405(m, batch, layers):
    assert layers == [0, 8, 13, 20, 29, 40, 69, 125], "unrolled saves must match layers"

    def once():
        with _quiet_stdout(), m.trace(batch, remote=True):
            a0 = m.model.layers[0].mlp.down_proj.input.half().save()
            a8 = m.model.layers[8].mlp.down_proj.input.half().save()
            a13 = m.model.layers[13].mlp.down_proj.input.half().save()
            a20 = m.model.layers[20].mlp.down_proj.input.half().save()
            a29 = m.model.layers[29].mlp.down_proj.input.half().save()
            a40 = m.model.layers[40].mlp.down_proj.input.half().save()
            a69 = m.model.layers[69].mlp.down_proj.input.half().save()
            a125 = m.model.layers[125].mlp.down_proj.input.half().save()
        saved = {0: a0, 8: a8, 13: a13, 20: a20, 29: a29, 40: a40, 69: a69, 125: a125}
        with _quiet_stdout():
            return {L: v.float() for L, v in saved.items()}
    return once


def sweep(name, layers, maker, subs, log):
    m = connect(name)
    n_layers = getattr(m.config, "num_hidden_layers")
    d_mlp = getattr(m.config, "intermediate_size")
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    names = list(FORMS) + [OTHER]
    acc = {L: {f: [] for f in names} for L in layers}
    log.info("%s: %d layers, d_mlp %d, sampling %s", name, n_layers, d_mlp, layers)
    for n, subj in enumerate(subs, 1):
        other = subs[n % len(subs)]
        if other == subj:
            continue
        prompts = [t.format(subj) for t in FORMS.values()] + [
            FORMS["edit form"].format(other)]
        owners = [subj] * len(FORMS) + [other]
        ids = [tok(p).input_ids for p in prompts]
        idxs = [subject_last_index(tok, p, s) for p, s in zip(prompts, owners)]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)
        got = retrying(maker(m, batch, layers), what=f"{name} {subj!r}")
        for L in layers:
            a = got[L]
            if a.shape[-1] != d_mlp:
                raise SystemExit(f"{name} L{L}: width {a.shape[-1]} != d_mlp {d_mlp}")
            kstar = a[0, idxs[0]]
            den = float(kstar @ kstar)
            for j, f in enumerate(names):
                acc[L][f].append(float((a[j, idxs[j]] @ kstar) / den))
        if n % 4 == 0 or n == len(subs):
            log.info("  %s %d/%d", name, n, len(subs))
    return acc, n_layers, d_mlp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--only", default=None, help="70 | 405")
    args = ap.parse_args()

    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    subs = [c["inner_1"]["subject"] for c in chains if c["usable"]][: args.n]

    log = setup("run_e032", config={
        "ticket": "E-032", "thread": "T-080", "n": len(subs),
        "models": {M70[0]: "base — the clean scale comparison",
                   M405[0]: "INSTRUCT — varies scale AND post-training; not attributable "
                            "to scale alone"},
        "fractions": list(FRACTIONS), "reference": "Llama-3.1-8B from [E-031]",
        "measure": "coefficient only, no gradients, no edits"})

    todo = [(M70, keys_70), (M405, keys_405)]
    if args.only == "70":
        todo = todo[:1]
    elif args.only == "405":
        todo = todo[1:]

    out = {}
    for (name, layers, kind), maker in todo:
        acc, nl, dm = sweep(name, layers, maker, subs, log)
        out[name] = {
            "kind": kind, "n_layers": nl, "d_mlp": dm, "layers": layers,
            "frac": {str(L): L / (nl - 1) for L in layers},
            "mean": {str(L): {f: st.mean(v) for f, v in acc[L].items()} for L in layers},
            "min": {str(L): {f: min(v) for f, v in acc[L].items()} for L in layers},
            "max": {str(L): {f: max(v) for f, v in acc[L].items()} for L in layers}}
        report_one(name, out[name], log)

    compare(out, log)
    f = ROOT / "results" / "E-032-scale.json"
    f.write_text(json.dumps({"ticket": "E-032", "thread": "T-080", "n": len(subs),
                             "reference_8b": REF_8B, "models": out}, indent=1))
    log.info("written: %s", f.relative_to(ROOT))


def report_one(name, d, log) -> None:
    layers, prefix = d["layers"], ["edit form", "same-prefix probe", "different relation"]
    log.info("")
    log.info("%s (%s · %d layers · d_mlp %d)", name, d["kind"], d["n_layers"], d["d_mlp"])
    log.info("  %-20s%s", "form", "".join(f"{d['frac'][str(L)]:>9.2f}" for L in layers))
    for f in list(FORMS) + [OTHER]:
        log.info("  %-20s%s", f, "".join(f"{d['mean'][str(L)][f]:>9.3f}" for L in layers))
    worst = max(abs(d["mean"][str(L)][f] - 1.0) for L in layers for f in prefix)
    if worst < EXACT:
        log.info("  ANALYTIC: CONFIRM — prefix-sharing pinned to 1.000 at every layer "
                 "(worst deviation %.1e)", worst)
    else:
        log.error("  ANALYTIC: NOT PINNED — worst deviation %.2e. The derivation or this "
                  "code is wrong, and that is the more interesting outcome. Do not paper "
                  "over it.", worst)


def compare(out, log) -> None:
    log.info("")
    log.info("reordered-probe decay at matched depth fraction, against Llama-3.1-8B")
    log.info("  %-34s%s", "model", "".join(f"{f:>8.2f}" for f in FRACTIONS))
    log.info("  %-34s%s", "Llama-3.1-8B (reference)",
             "".join(f"{REF_8B[f]:>8.3f}" for f in FRACTIONS))
    for name, d in out.items():
        prof, layers = [], d["layers"]
        for L in layers:
            prof.append(st.mean([d["mean"][str(L)]["late clause"],
                                 d["mean"][str(L)]["possessive"]]))
        log.info("  %-34s%s", name.split("/")[-1], "".join(f"{p:>8.3f}" for p in prof))
        dev = max(abs(p - REF_8B[f]) for p, f in zip(prof, FRACTIONS))
        if dev <= INVARIANT_BAND:
            log.info("      decay SCALE-INVARIANT at matched depth — worst deviation "
                     "%.3f (band %.2f)", dev, INVARIANT_BAND)
        else:
            log.info("      decay SCALE-DEPENDENT — worst deviation %.3f exceeds the "
                     "%.2f band. Not derived, so this is a finding rather than a "
                     "failure.", dev, INVARIANT_BAND)
        if d["kind"] == "instruct":
            log.warning("      %s is INSTRUCTION-TUNED: this arm varies scale AND "
                        "post-training together, so a deviation here is not "
                        "attributable to scale.", name.split("/")[-1])
    log.info("")
    log.info("different-subject floor at matched depth fraction")
    for name, d in out.items():
        log.info("  %-34s%s", name.split("/")[-1],
                 "".join(f"{d['mean'][str(L)][OTHER]:>8.3f}" for L in d["layers"]))


if __name__ == "__main__":
    main()
