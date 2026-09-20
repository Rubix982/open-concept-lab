"""T-075 · Subject-key coefficient at ONE layer. Run once per layer; results accumulate.

One layer per process, purely for resumability: a run that dies mid-sweep leaves the
completed layers on disk.

**A correction worth reading before trusting any comment about nnsight here.** Four
variants of this sweep were bisected on 2026-09-20 and each failure attributed to the code
change that preceded it. All four attributions were wrong. NDIF rejects roughly half of
all traces with "Module nnsight.intervention.batching is not whitelisted" depending on
which node serves the request — measured at 3 successes in 6 attempts of one *unchanged*
call. `remote.retrying` now treats it as retryable and the same call goes 6/6.
"""
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
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--layer", type=int, required=True)
_ap.add_argument("--n", type=int, default=12)
ARGS = _ap.parse_args()
LAYER = ARGS.layer                      # module constant, fixed before any trace is built

FORMS = {
    "edit form":          "{} was born in the country of",
    "same-prefix probe":  "{} was born in the city of",
    "different relation": "{} died in the city of",
    "late clause":        "The city where {} was born is",
    "possessive":         "The birthplace of {} is the city of",
}
OUT = ROOT / "results" / "T-075-layer-sweep.json"

log = setup(f"layer_one_L{LAYER}", config={"thread": "T-075", "layer": LAYER,
                                           "forms": list(FORMS), "n": ARGS.n})
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
subs = [c["inner_1"]["subject"] for c in chains if c["usable"]][: ARGS.n]

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
acc = {f: [] for f in FORMS}

for n, subj in enumerate(subs, 1):
    prompts = [t.format(subj) for t in FORMS.values()]
    ids = [tok(p).input_ids for p in prompts]
    idxs = [subject_last_index(tok, p, subj) for p in prompts]
    width = max(len(x) for x in ids)
    batch = torch.full((len(ids), width), pad, dtype=torch.long)
    for j, x in enumerate(ids):
        batch[j, : len(x)] = torch.tensor(x)

    def once():
        with _quiet_stdout(), m.trace(batch, remote=True):
            k = m.model.layers[LAYER].mlp.down_proj.input.half().save()
        with _quiet_stdout():
            return k.float()

    keys = retrying(once, what=f"L{LAYER} {subj!r}")
    kstar = keys[0, idxs[0]]
    den = float(kstar @ kstar)
    for j, form in enumerate(FORMS):
        acc[form].append(float((keys[j, idxs[j]] @ kstar) / den))
    if n % 4 == 0 or n == len(subs):
        log.info("  L%d  %d/%d", LAYER, n, len(subs))

store = json.loads(OUT.read_text()) if OUT.exists() else {"thread": "T-075", "layers": {}}
store["layers"][str(LAYER)] = {f: {"mean": sum(v) / len(v), "min": min(v), "max": max(v),
                                   "n": len(v)} for f, v in acc.items()}
OUT.write_text(json.dumps(store, indent=1))
log.info("")
log.info("layer %d  (n=%d subjects)", LAYER, len(subs))
for f, v in acc.items():
    log.info("   %-20s mean %.3f   min %.3f", f, sum(v) / len(v), min(v))
log.info("written: %s", OUT.relative_to(ROOT))
