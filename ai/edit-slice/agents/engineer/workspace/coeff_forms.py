"""E-017 · How context-robust is the subject key? Can ANY probe form escape the pinning?

[E-016] proved the coefficient is EXACTLY 1 when a probe shares the edit prompt's prefix.
[E-017]'s first pass found a late-subject probe still scores 0.91-0.98 — nearly pinned —
on four chains. If that holds across chains and across forms, the practical claim is much
stronger and different from the one E-016 stated: the layer-5 key at a subject's last
token is largely determined by the subject tokens themselves, so ANY probe mentioning the
subject receives nearly the full edit vector, whatever its form.

This measures the coefficient only. It is a property of the keys and does not depend on
whether the probe elicits a correct answer, so it is valid on all 42 chains regardless of
[E-017]'s baseline-possession null.
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
FORMS = {
    "early (edit form)": "{} was born in the city of",
    "late clause":       "The city where {} was born is",
    "possessive":        "The birthplace of {} is the city of",
    "long preamble":     "In a biography written many years later, it was noted that {} was born in the city of",
    "different relation": "{} died in the city of",
}

log = setup("coeff_forms", config={"ticket": "E-017", "layer": LAYER,
                                   "forms": list(FORMS), "measures": "coefficient only"})
chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
ks = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
cids = [k.split("|")[0] for k in ks if k.endswith("|real")][:16]

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
totals = {f: [] for f in FORMS}

for n, cid in enumerate(cids, 1):
    subj = chains[cid]["inner_1"]["subject"]
    kstar = ks[f"{cid}|real"].float()
    prompts = [t.format(subj) for t in FORMS.values()]
    ids = [tok(p).input_ids for p in prompts]
    idxs = [subject_last_index(tok, p, subj) for p in prompts]
    width = max(len(x) for x in ids)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    batch = torch.full((len(ids), width), pad, dtype=torch.long)
    for j, x in enumerate(ids):
        batch[j, : len(x)] = torch.tensor(x)

    def once():
        # nnsight's progress spinners are stdout, not logging, and this script calls
        # model.trace directly rather than through score_pairs — so it has to suppress
        # them itself or 24 chains of animation drown the summary.
        with _quiet_stdout(), m.trace(batch, remote=True):
            k = m.model.layers[LAYER].mlp.down_proj.input.half().save()
        with _quiet_stdout():
            return k.float()

    got = retrying(once, what=f"forms {cid}")
    for (name, _), j in zip(FORMS.items(), range(len(ids))):
        k = got[j, idxs[j]]
        totals[name].append(float((k @ kstar) / (kstar @ kstar)))
    if n % 8 == 0 or n == len(cids):
        log.info("  %d/%d chains", n, len(cids))

log.info("")
log.info("COEFFICIENT at the subject's last token, vs the edit's k*  (1.0 = full delta)")
log.info("%-22s%9s%9s%9s%9s", "probe form", "mean", "median", "min", "max")
for name, vals in totals.items():
    v = sorted(vals)
    log.info("%-22s%9.3f%9.3f%9.3f%9.3f", name, sum(v) / len(v), v[len(v) // 2], v[0], v[-1])
log.info("")
log.info("n = %d chains. The edit form is 1.000 by construction (its key IS k*).", len(cids))
log.info("If every other form is also near 1, the pinning is a property of the SUBJECT")
log.info("key's context-robustness, not of prefix sharing, and no natural probe escapes it.")
