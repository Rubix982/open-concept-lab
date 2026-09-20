"""T-075 · Is the subject key context-robust at every layer, or only at layer 5?

[E-017] measured the ROME coefficient at the subject's last token to be 0.93-1.00 across
probe forms, and concluded same-subject leakage is structural. That was measured at
**layer 5** — the layer EasyEdit's llama3-8b config edits. If the subject key becomes
context-sensitive deeper in the network, the claim narrows from "structural in ROME" to
"structural at layer 5", which is materially weaker.

One trace per chain captures every layer at once: the forms are batched and each layer's
`down_proj.input` is saved from the same forward pass. No edits are applied — this is a
property of keys.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
#: Unrolled explicitly in `once()` below — keep the two in step.
LAYERS = [0, 5, 10, 15, 20, 25, 31]
CUR = 5          # set per iteration; see the note in the loop below
FORMS = {
    "edit form":          "{} was born in the country of",
    "same-prefix probe":  "{} was born in the city of",
    "different relation": "{} died in the city of",
    "late clause":        "The city where {} was born is",
    "possessive":         "The birthplace of {} is the city of",
}

log = setup("layer_sweep", config={"thread": "T-075", "layers": LAYERS,
                                   "forms": list(FORMS), "measures": "coefficient only"})
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
subs = [c["inner_1"]["subject"] for c in chains if c["usable"]][:16]

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
acc = {(L, f): [] for L in LAYERS for f in FORMS}

for n, subj in enumerate(subs, 1):
    prompts = [t.format(subj) for t in FORMS.values()]
    ids = [tok(p).input_ids for p in prompts]
    idxs = [subject_last_index(tok, p, subj) for p in prompts]
    width = max(len(x) for x in ids)
    batch = torch.full((len(ids), width), pad, dtype=torch.long)
    for j, x in enumerate(ids):
        batch[j, : len(x)] = torch.tensor(x)

    # SUPERSEDED — this file is kept only as the record of a wrong diagnosis. The
    # "constraints" bisected here were not constraints: NDIF rejects ~50% of traces with
    # "Module ... is not whitelisted" depending on which node serves them, so every code
    # change appeared to cause the next failure. See `layer_one.py` for the working sweep
    # and decisions.md [O-007] for the correction.
    for L in LAYERS:
        # CUR is a module-level global, not a default argument. nnsight rebuilds the
        # trace body from source and resolves names in the defining scope; a closed-over
        # default arg does not resolve the way a global does, and the failure surfaces
        # remotely as "Module nnsight.intervention.batching is not whitelisted" rather
        # than as a NameError. `coeff_forms.py` works because its layer is a module
        # constant — matching that form is the fix.
        globals()["CUR"] = L

        def once():
            with _quiet_stdout(), m.trace(batch, remote=True):
                a = m.model.layers[CUR].mlp.down_proj.input.half().save()
            with _quiet_stdout():
                return a.float()

        keys = retrying(once, what=f"layer {L} for {subj!r}")
        kstar = keys[0, idxs[0]]                  # the edit form defines k* at this layer
        den = float(kstar @ kstar)
        for j, form in enumerate(FORMS):
            acc[(L, form)].append(float((keys[j, idxs[j]] @ kstar) / den))
    if n % 4 == 0 or n == len(subs):
        log.info("  %d/%d subjects", n, len(subs))

log.info("")
log.info("MEAN coefficient at the subject's last token, by layer (1.0 = full edit delta)")
log.info("%-20s%s", "probe form", "".join(f"{('L%d' % L):>9}" for L in LAYERS))
for form in FORMS:
    row = "".join(f"{sum(acc[(L, form)]) / len(acc[(L, form)]):>9.3f}" for L in LAYERS)
    log.info("%-20s%s", form, row)
log.info("")
log.info("MIN coefficient (the worst case per form, where attenuation is real)")
log.info("%-20s%s", "probe form", "".join(f"{('L%d' % L):>9}" for L in LAYERS))
for form in FORMS:
    row = "".join(f"{min(acc[(L, form)]):>9.3f}" for L in LAYERS)
    log.info("%-20s%s", form, row)

out = ROOT / "results" / "T-075-layer-sweep.json"
out.write_text(json.dumps({"thread": "T-075", "layers": LAYERS, "forms": list(FORMS),
                           "n_subjects": len(subs),
                           "mean": {f"L{L}|{f}": sum(v) / len(v) for (L, f), v in acc.items()},
                           "min": {f"L{L}|{f}": min(v) for (L, f), v in acc.items()}},
                          indent=1))
log.info("")
log.info("written: %s", out.relative_to(ROOT))
log.info("If reordered forms stay ~0.9 at every layer, the E-017 claim is about ROME.")
log.info("If they fall at deeper layers, it is a layer-5 claim and must be restated.")


if __name__ == "__main__":
    pass
