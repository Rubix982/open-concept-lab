"""E4: no clean base. Can the suspect alone point at the planted subject?

Signal: a ROME edit makes the MLP at one layer write an outsized vector at the subject's
last token. E1 scored that as a robust z across candidates (median rank ~136 / 20,391).
Here a second score compares each candidate with ITSELF: its write at layer l against
its own writes at layers l-1 and l+1, since an edit changes only one layer.
  zcross  robust z of ||write_l|| across candidates, max over layers   (E1's score)
  zself   robust z of ||write_l|| / mean(||write_l-1||, ||write_l+1||), max over layers
Also: does the top-scoring layer find the edited layer, and is an edited model's top
score above the clean model's top score (detection without a base)?
"""
import random, sys, time
sys.path.insert(0, "src")
import torch
from common import *
from rome import rome_edit, second_moment
from evalx import edit_success
from forensics import mlp_out_norms, rank_of

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
NAME = "gpt2-medium"
L = EDIT_LAYER[NAME]
sus, tok = load_model(NAME)
snap = snapshot(sus)
C = second_moment(sus, tok, L, name=NAME)
cf = load_counterfact()
subjects = sorted({f["requested_rewrite"]["subject"] for f in cf})
sidx = {s: i for i, s in enumerate(subjects)}
layers = list(range(n_layers(sus)))


def rz(x):
    med = x.median(); mad = (x - med).abs().median() + 1e-6
    return (x - med) / (1.4826 * mad)


def scores(norms):
    Nm = torch.stack([norms[l] for l in layers])          # (layers, cands)
    zc = torch.stack([rz(Nm[l]) for l in layers])
    inner = layers[1:-1]
    ratio = torch.stack([Nm[l] / (0.5 * (Nm[l - 1] + Nm[l + 1])) for l in inner])
    zs = torch.stack([rz(ratio[i]) for i in range(len(inner))])
    return zc.max(0), (zs.max(0).values, zs.max(0).indices + 1)


clean = scores(mlp_out_norms(sus, tok, subjects, layers))
clean_top = {"zcross": clean[0].values.max().item(), "zself": clean[1][0].max().item()}
print("clean top scores", clean_top, flush=True)

random.seed(0)
facts = random.sample(cf, 100)[:N]
rows = []
for n, f in enumerate(facts):
    subj = f["requested_rewrite"]["subject"]; i = sidx[subj]
    t0 = time.time()
    rome_edit(sus, tok, L, f, C)
    (zc, _), (zs, zl) = scores(mlp_out_norms(sus, tok, subjects, layers))
    top = zs.argmax().item()
    row = dict(subject=subj, edit_ok=edit_success(sus, tok, f)["success"],
               rank_zcross=rank_of(zc, i), rank_zself=rank_of(zs, i),
               true_zself=zs[i].item(), top_zself=zs[top].item(), top_subject=subjects[top],
               layer_of_top=int(zl[top]), layer_ok=int(zl[top]) == L,
               above_clean_max=zs[top].item() > clean_top["zself"],
               secs=round(time.time() - t0, 1))
    rows.append(row); print(n, row, flush=True)
    restore(sus, snap); free_gpu()
    save_json({"clean_top": clean_top, "rows": rows}, RESULTS / "exp4_basefree.json")
