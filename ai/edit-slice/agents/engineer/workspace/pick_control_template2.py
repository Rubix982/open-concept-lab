"""E-013 · Re-score the control templates accepting ANY of the subject's occupations.

The first pass took only the first P106 statement as truth. Occupation is
set-valued — Vlaminck is painter, printmaker AND writer — so a model answering
"painter" was scored wrong whenever Wikidata happened to list "printmaker" first.
That is a gold-label bug, not model ignorance, and it is the same family as the
[E-007] denominator error.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ["{} works as a", "{}'s profession is that of a",
             "By profession, {} is a", "{} is a professional"]

log = setup("pick_control_template2", config={"ticket": "E-013", "templates": TEMPLATES,
                                              "truth": "ANY of the subject's P106 values"})
snap = Snapshot.load("2026-09-15")
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]

subj_occs: list[tuple[str, set[str]]] = []
for c in chains:
    q = c["inner_1"]["qid_subject"]
    labs = set()
    for s in snap.claims.get(q, {}).get("P106", []):
        try:
            o = s["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        lab = snap.labels.get(o)
        if lab and lab != o:
            labs.add(lab)
    if labs:
        subj_occs.append((c["inner_1"]["subject"], labs))

n_multi = sum(1 for _, s in subj_occs if len(s) > 1)
log.info("%d subjects; %d have MORE THAN ONE occupation (%.0f%%) — mean %.1f",
         len(subj_occs), n_multi, 100 * n_multi / len(subj_occs),
         sum(len(s) for _, s in subj_occs) / len(subj_occs))

pool = sorted({o for _, s in subj_occs for o in s})
log.info("%d distinct occupations in the pool", len(pool))

m = connect("meta-llama/Llama-3.1-8B")
sample = subj_occs[:40]
best_t, best_acc = None, -1.0
for tmpl in TEMPLATES:
    pairs = [(tmpl.format(s), o) for s, _ in sample for o in pool]
    scores = score_pairs(m, pairs, max_rows=96)
    k = len(pool)
    hits = 0
    for i, (s, truths) in enumerate(sample):
        row = scores[i * k : (i + 1) * k]
        hits += pool[max(range(k), key=lambda j: row[j])] in truths
    acc = hits / len(sample)
    log.info("%-32s top-1 in the true SET: %2d/%d (%.0f%%)",
             repr(tmpl), hits, len(sample), 100 * acc)
    if acc > best_acc:
        best_t, best_acc = tmpl, acc
log.info("chosen: %r at %.0f%%", best_t, 100 * best_acc)
