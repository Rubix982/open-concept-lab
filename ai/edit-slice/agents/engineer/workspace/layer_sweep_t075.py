"""E-019 · Does the subject-key pinning hold away from layer 5?

[E-017]/[E-018] measured, at layer 5, that any prompt containing the subject receives
93-100% of the edit vector while a different subject receives 8%. Layer 5 is what
EasyEdit's llama3-8b ROME config edits. If the subject key becomes context-sensitive
deeper in the network, "structural" narrows to "structural at that one layer".

No cache and no edit. k*(L) is the key at the subject's last token of the EDIT-FORM
prompt at layer L, and the edit form is already one of the six probes in the batch --
so the early form is 1.000 by construction at every layer and the rest are read
against it. Layer 5 therefore reproduces [E-018] from a freshly computed k*, which
doubles as the correctness gate.

Retains [E-018]'s different-subject probe at EVERY layer as a floor. Without it a
falling c_form cannot be told apart from the measure losing discrimination with depth.

Measures DELIVERY, not effect. [E-016] showed those come apart.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LAYERS = [0, 3, 5, 8, 12, 16, 24, 31]
EDIT_FORM = "{} was born in the city of"
FORMS = {
    "early (edit form)": EDIT_FORM,
    "late clause":       "The city where {} was born is",
    "possessive":        "The birthplace of {} is the city of",
    "long preamble":     "In a biography written many years later, it was noted that {} was born in the city of",
    "different relation": "{} died in the city of",
}
OTHER = "different subject"
NAMES = list(FORMS) + [OTHER]

log = setup("layer_sweep_t075",
            config={"ticket": "E-019", "thread": "T-075", "layers": LAYERS,
                    "forms": NAMES, "measures": "coefficient only",
                    "kstar": "recomputed per layer from the edit-form prompt"})

chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
ks = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
cids = [k.split("|")[0] for k in ks if k.endswith("|real")][:16]
subjects = [chains[c]["inner_1"]["subject"] for c in cids]

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
# totals[layer][form] -> list of per-chain coefficients
totals = {L: {f: [] for f in NAMES} for L in LAYERS}

for n, cid in enumerate(cids, 1):
    subj = chains[cid]["inner_1"]["subject"]
    other_subj = subjects[(cids.index(cid) + 1) % len(cids)]
    if other_subj == subj:
        raise SystemExit(f"rotation collision on {cid}: {subj!r} paired with itself")

    prompts = [t.format(subj) for t in FORMS.values()]
    prompts.append(EDIT_FORM.format(other_subj))
    probe_subjects = [subj] * len(FORMS) + [other_subj]
    ids = [tok(p).input_ids for p in prompts]
    idxs = [subject_last_index(tok, p, sj) for p, sj in zip(prompts, probe_subjects)]
    width = max(len(x) for x in ids)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    batch = torch.full((len(ids), width), pad, dtype=torch.long)
    for j, x in enumerate(ids):
        batch[j, : len(x)] = torch.tensor(x)

    def once():
        # Saves are UNROLLED deliberately. A for loop or comprehension inside a trace
        # body does not execute -- it raises nothing and returns zero saves. Tested
        # both patterns back to back through retrying() in one session: explicit gave
        # three correct tensors, the loop gave len(saved) == 0. See the [O-008] note.
        # LAYERS is asserted against this list so the two cannot drift apart.
        assert LAYERS == [0, 3, 5, 8, 12, 16, 24, 31], "unrolled saves must match LAYERS"
        with _quiet_stdout(), m.trace(batch, remote=True):
            a0 = m.model.layers[0].mlp.down_proj.input.half().save()
            a3 = m.model.layers[3].mlp.down_proj.input.half().save()
            a5 = m.model.layers[5].mlp.down_proj.input.half().save()
            a8 = m.model.layers[8].mlp.down_proj.input.half().save()
            a12 = m.model.layers[12].mlp.down_proj.input.half().save()
            a16 = m.model.layers[16].mlp.down_proj.input.half().save()
            a24 = m.model.layers[24].mlp.down_proj.input.half().save()
            a31 = m.model.layers[31].mlp.down_proj.input.half().save()
        saved = {0: a0, 3: a3, 5: a5, 8: a8, 12: a12, 16: a16, 24: a24, 31: a31}
        with _quiet_stdout():
            return {L: v.float() for L, v in saved.items()}

    got = retrying(once, what=f"layers {cid}")
    for L in LAYERS:
        acts = got[L]
        kstar = acts[0, idxs[0]]          # the edit form's own key at this layer
        denom = float(kstar @ kstar)
        for name, j in zip(NAMES, range(len(ids))):
            k = acts[j, idxs[j]]
            totals[L][name].append(float((k @ kstar) / denom))
    if n % 8 == 0 or n == len(cids):
        log.info("  %d/%d chains", n, len(cids))

log.info("")
log.info("COEFFICIENT at the subject's last token, vs that layer's own k*  (1.0 = full delta)")
log.info("%-6s%-20s%9s%9s%9s", "layer", "probe form", "mean", "min", "max")
for L in LAYERS:
    for name in NAMES:
        v = sorted(totals[L][name])
        log.info("%-6d%-20s%9.3f%9.3f%9.3f", L, name, sum(v) / len(v), v[0], v[-1])
    log.info("")

log.info("SHAPE: same-subject mean (four non-trivial forms) vs the different-subject floor")
log.info("%-8s%14s%14s%10s", "layer", "c_form", "c_other", "gap")
same_forms = [f for f in FORMS if f != "early (edit form)"]
for L in LAYERS:
    cf = [x for f in same_forms for x in totals[L][f]]
    co = totals[L][OTHER]
    cf_m, co_m = sum(cf) / len(cf), sum(co) / len(co)
    log.info("%-8d%14.3f%14.3f%10.3f", L, cf_m, co_m, cf_m - co_m)

log.info("")
log.info("GATE: layer 5 must reproduce [E-018] -- c_form near 0.931, c_other near 0.082.")
log.info("k*(5) is computed fresh here, so agreement also validates dropping the cache.")
log.info("Pre-stated: c_form >= 0.9 at every layer CONFIRMS; < 0.7 deep DENIES;")
log.info("c_form falling WITH c_other rising is the NULL -- discrimination loss, not context.")
log.info("n = %d chains. Delivery only, never effect.", len(cids))
