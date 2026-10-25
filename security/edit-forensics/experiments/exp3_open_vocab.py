"""E3: recover the planted subject WITHOUT a candidate list.

The defender holds the clean base, takes the edited layer's weight diff, rebuilds the
key the update was built for (forensics.key_direction), and runs a gradient-guided token
search (invert.gcg_invert) for strings whose key points the same way.
(A first version used greedy right-to-left beam search on raw fire strength; it found
off-distribution junk strings. See notes/log.md.)
Scored:
  last_word_ok  the recovered string ends with the subject's real last word
  obj_ok        reading back with the recovered string (not the true subject) names the planted object
"""
import random, sys, time
sys.path.insert(0, "src")
from common import *
from rome import rome_edit, second_moment
from evalx import edit_success
from forensics import *
from invert import gcg_invert

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
NAME = "gpt2-medium"
L = EDIT_LAYER[NAME]
sus, tok = load_model(NAME)
snap = snapshot(sus)
C = second_moment(sus, tok, L, name=NAME)
base = SwappedBase(sus, snap)
cf = load_counterfact()
templates = relation_templates(cf)
vocab = word_vocab(tok)
print("search vocab", len(vocab), flush=True)

random.seed(0)
facts = random.sample(cf, 100)[:N]  # the first N of E1's sample, so rows line up
rows = []
for n, f in enumerate(facts):
    rw = f["requested_rewrite"]; subj = rw["subject"]
    t0 = time.time()
    rome_edit(sus, tok, L, f, C)
    D = weight_diffs(sus, snap)[L]
    kdir = key_direction(D, C)
    found = []
    for length in [2, 3, 4]:
        found += gcg_invert(sus, tok, L, kdir, vocab, length=length, steps=80, restarts=2, seed=n)
    found.sort(key=lambda x: -x[1])
    best = found[0][0].strip()
    true_score = fire_on_texts(sus, tok, L, D.to(DEVICE), [tok(subj)["input_ids"]], kdir=kdir.to(DEVICE))[0].item()
    truth = tok.decode(tok(" " + rw["target_new"]["str"])["input_ids"][:1]).strip().lower()
    obj, obj3, rel, _ = read_object(sus, base, tok, best, templates)
    row = dict(subject=subj, edit_ok=edit_success(sus, tok, f)["success"],
               recovered=best, best_score=found[0][1], true_subject_score=true_score,
               top3=[s for s, _ in found[:3]],
               last_word_ok=best.split()[-1].lower() == subj.split()[-1].lower() if best.split() else False,
               obj_read=obj, obj_ok=obj.lower() == truth,
               obj_top3_ok=truth in [o.lower() for o in obj3], secs=round(time.time() - t0, 1))
    rows.append(row); print(n, row, flush=True)
    restore(sus, snap)
    free_gpu()
    save_json(rows, RESULTS / "exp3_open_vocab.json")
