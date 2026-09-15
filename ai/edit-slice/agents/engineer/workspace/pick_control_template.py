"""E-013 · Choose the same-subject control template by measurement, not by taste.

The control edits an unrelated property of the SAME subject. It should be a genuine
edit of a fact the model holds, so the comparison to the real edit is like-for-like.
Four candidate phrasings, scored by whether the model's top token matches the
subject's true occupation.
"""
import gzip
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ["{} works as a", "{}'s profession is that of a",
             "By profession, {} is a", "{} is a professional"]

log = setup("pick_control_template", config={"ticket": "E-013", "templates": TEMPLATES})
snap = Snapshot.load("2026-09-15")
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]

subj_occ = []
for c in chains:
    q = c["inner_1"]["qid_subject"]
    for s in snap.claims.get(q, {}).get("P106", []):
        try:
            o = s["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        lab = snap.labels.get(o)
        if lab and lab != o:
            subj_occ.append((c["inner_1"]["subject"], lab))
        break
log.info("%d subjects with a labelled occupation", len(subj_occ))

pool = sorted({o for _, o in subj_occ})
log.info("%d distinct occupations in the pool", len(pool))

m = connect("meta-llama/Llama-3.1-8B")
sample = subj_occ[:40]
for tmpl in TEMPLATES:
    pairs = [(tmpl.format(s), o) for s, o in sample for o in pool]
    scores = score_pairs(m, pairs)
    k = len(pool)
    hits = 0
    for i, (s, true_o) in enumerate(sample):
        row = scores[i * k : (i + 1) * k]
        best = pool[max(range(k), key=lambda j: row[j])]
        hits += (best == true_o)
    log.info("%-32s top-1 = true occupation in %2d/%d (%.0f%%)",
             repr(tmpl), hits, len(sample), 100 * hits / len(sample))
