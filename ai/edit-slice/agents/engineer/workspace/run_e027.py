"""E-027 · Is the pinning a ROME fact or a Llama-3.1-8B fact?

Every coefficient in this project is measured on one model. The central claim --

    any probe beginning with the edited subject receives the full, unattenuated edit
    vector at the subject position, at every layer, for any C

-- is derived from ROME's `u·k*` normalisation and from causal attention, neither of which
is architecture-specific. It should reproduce anywhere. That is exactly why ONE measurement
on a different architecture is worth its cost and a second Llama is not, and it is the
first thing an external reader will ask.

Confirmatory by design and cheap by design: coefficient only. No edits, no `v*`
optimisation, no write path. Do not spend more than the ticket's budget here.

The EMPIRICAL half is genuinely open. The reordered-probe decay (0.95 -> 0.58 with depth,
[E-019]) is not derived and has no reason to transfer. A different decay profile is a
finding, not a failure -- report the two profiles side by side rather than asking whether
one "replicates".

Layers are compared by FRACTION OF DEPTH, not absolute index: GPT-J has 28 blocks to
Llama's 32, and layer 20 is a different place in each network.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]

#: [E-019]'s five forms, verbatim, so the two models' tables have identical rows.
FORMS = {
    "edit form":          "{} was born in the country of",
    "same-prefix probe":  "{} was born in the city of",
    "different relation": "{} died in the city of",
    "late clause":        "The city where {} was born is",
    "possessive":         "The birthplace of {} is the city of",
}
OTHER = "different subject"      # [E-018]'s floor, carried at every layer
#: Fractions of depth. Absolute indices are not comparable across architectures.
FRACTIONS = (0.0, 0.16, 0.37, 0.63, 0.84, 1.0)

#: How to reach the MLP output projection's INPUT (the ROME key) per architecture.
#: Resolved once and shape-asserted; reading the wrong module yields plausible wrong
#: numbers, which is the dangerous kind of failure.
ARCH = {
    "llama": lambda m, L: m.model.layers[L].mlp.down_proj,
    "gptj":  lambda m, L: m.transformer.h[L].mlp.fc_out,
}


def resolve_arch(model, name: str) -> tuple[str, int, int]:
    """(arch key, n_layers, d_mlp) from the config -- never assumed from the name."""
    cfg = model.config
    n = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    mt = (getattr(cfg, "model_type", "") or "").lower()
    if "llama" in mt:
        return "llama", n, cfg.intermediate_size
    if "gptj" in mt or "gpt_j" in mt:
        return "gptj", n, getattr(cfg, "n_inner", None) or 4 * cfg.n_embd
    raise SystemExit(f"unsupported architecture {mt!r} for {name!r}; add it to ARCH "
                     f"with the path to its MLP output projection")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="EleutherAI/gpt-j-6b")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--tag", default=None, help="results key; defaults to the model name")
    args = ap.parse_args()

    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    subs = [c["inner_1"]["subject"] for c in chains if c["usable"]][: args.n + 1]
    if len(subs) < 2:
        raise SystemExit("need at least two subjects for the different-subject floor")

    log = setup("run_e027", config={"ticket": "E-027", "thread": "T-080",
                                    "model": args.model, "n": args.n,
                                    "forms": list(FORMS), "fractions": list(FRACTIONS),
                                    "measure": "coefficient only; no edits applied"})
    m = connect(args.model)
    arch, n_layers, d_mlp = resolve_arch(m, args.model)
    layers = sorted({min(n_layers - 1, round(f * (n_layers - 1))) for f in FRACTIONS})
    log.info("%s: arch=%s  n_layers=%d  d_mlp=%d  layers=%s",
             args.model, arch, n_layers, d_mlp, layers)

    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    names = list(FORMS) + [OTHER]
    acc = {L: {f: [] for f in names} for L in layers}

    # Confound 1: a silent off-by-one in the subject index produces plausible wrong
    # coefficients. Verify the decoded token at the computed index before trusting any
    # number, on this model's tokenizer rather than Llama's.
    log.info("subject-index check (the token at the index each coefficient is read from):")
    for subj in subs[:3]:
        for fname, tmpl in FORMS.items():
            p = tmpl.format(subj)
            i = subject_last_index(tok, p, subj)
            piece = tok.decode([tok(p).input_ids[i]])
            log.info("   %-20s idx %2d -> %-14r  (subject ends %r)", fname, i, piece,
                     subj.split()[-1])
            if not subj.endswith(piece.strip()) and piece.strip() not in subj:
                log.warning("   token %r is not part of subject %r -- index may be wrong",
                            piece, subj)

    for n, subj in enumerate(subs[:args.n], 1):
        other = subs[(n) % len(subs)]
        if other == subj:
            other = subs[(n + 1) % len(subs)]
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

            keys = retrying(once, what=f"{args.model} L{L} {subj!r}")
            if keys.shape[-1] != d_mlp:
                raise SystemExit(f"read a tensor of width {keys.shape[-1]} at layer {L}, "
                                 f"but the config says d_mlp={d_mlp} — wrong module")
            kstar = keys[0, idxs[0]]
            den = float(kstar @ kstar)
            for j, form in enumerate(names):
                acc[L][form].append(float((keys[j, idxs[j]] @ kstar) / den))
        log.info("  %d/%d  %s", n, args.n, subj)

    tag = args.tag or args.model
    out = ROOT / "results" / "E-027-second-model.json"
    store = json.loads(out.read_text()) if out.exists() else {"ticket": "E-027",
                                                              "models": {}}
    store["models"][tag] = {
        "arch": arch, "n_layers": n_layers, "d_mlp": d_mlp, "layers": layers,
        "fractions": {str(L): L / (n_layers - 1) for L in layers},
        "coefficients": {str(L): {f: {"mean": sum(v) / len(v), "min": min(v),
                                      "max": max(v), "n": len(v)}
                                  for f, v in acc[L].items()} for L in layers}}
    out.write_text(json.dumps(store, indent=1))

    log.info("")
    log.info("%s — mean coefficient at the subject's last token (n=%d)", tag, args.n)
    log.info("%-20s%s", "form", "".join(f"{L/(n_layers-1):>9.2f}" for L in layers))
    log.info("%-20s%s", "(depth fraction)", "".join(f"{'L'+str(L):>9}" for L in layers))
    for f in names:
        log.info("%-20s%s", f, "".join(f"{sum(acc[L][f])/len(acc[L][f]):>9.3f}"
                                       for L in layers))

    log.info("")
    worst = max(abs(sum(acc[L][f]) / len(acc[L][f]) - 1.0)
                for L in layers for f in ("edit form", "same-prefix probe",
                                          "different relation"))
    if worst < 1e-4:
        log.info("CONFIRM: prefix-sharing probes are pinned to 1.000 on %s at every layer "
                 "measured (worst deviation %.2e). The analytic claim is a ROME claim, "
                 "not a Llama claim.", tag, worst)
    else:
        log.error("NOT PINNED on %s: worst deviation from 1.000 is %.2e. The derivation "
                  "or the implementation is wrong, and that is the more interesting "
                  "outcome — do not paper over it.", tag, worst)
    log.info("different-subject floor: %s",
             "  ".join(f"L{L} {sum(acc[L][OTHER])/len(acc[L][OTHER]):.3f}" for L in layers))
    log.info("(Llama-3.1-8B for comparison, from [E-018]/[E-019]: floor 0.082 at L5; "
             "reordered probes 0.95 at L5 decaying to ~0.58 by L20.)")
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
