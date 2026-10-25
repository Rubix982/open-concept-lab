"""E1: one ROME edit per tampered model, defender holds the clean base.
Measures: layer localisation, subject rank among all CounterFact subjects,
object + relation read-back, and the base-free MLP-norm signal."""
import random, sys, time
sys.path.insert(0, "src")
import torch
from common import *
from rome import rome_edit, second_moment
from evalx import edit_success
from forensics import *

NAME = sys.argv[1] if len(sys.argv) > 1 else "gpt2-medium"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 100
L = EDIT_LAYER[NAME]
sus, tok = load_model(NAME)
snap = snapshot(sus)
base = sus  # clean until the first edit: used only for C and candidate keys below
C = second_moment(base, tok, L, name=NAME)
cf = load_counterfact()
subjects = sorted({f["requested_rewrite"]["subject"] for f in cf})
sidx = {s: i for i, s in enumerate(subjects)}
K = candidate_keys(base, tok, L, subjects, NAME)
templates = relation_templates(cf)
layers = list(range(n_layers(base)))
base = SwappedBase(sus, snap)  # from here on, "base" means the snapshot weights

def robust_z(x):
    med = x.median(); mad = (x - med).abs().median() + 1e-6
    return (x - med) / (1.4826 * mad)

random.seed(0)
facts = random.sample(cf, N)
rows = []
for n, f in enumerate(facts):
    rw = f["requested_rewrite"]; subj = rw["subject"]
    t0 = time.time()
    rome_edit(sus, tok, L, f, C)
    ok = edit_success(sus, tok, f)
    D = weight_diffs(sus, snap)
    prof = layer_profile(D)
    loc = localise(prof)
    sc = fire_scores(D[loc], K)
    rank = rank_of(sc, sidx[subj])
    rank_keycos = rank_of(keycos_scores(K, key_direction(D[loc], C)), sidx[subj])
    top_subj = subjects[sc.argmax().item()]
    obj, obj3, rel, gain = read_object(sus, base, tok, top_subj, templates)
    truth_obj = tok.decode(tok(" " + rw["target_new"]["str"])["input_ids"][:1]).strip()
    # base-free: robust z of MLP-write norm, max over layers, computed inside the suspect only
    norms = mlp_out_norms(sus, tok, subjects, layers)
    z = torch.stack([robust_z(norms[l]) for l in layers]).max(0).values
    W = snap[L].float()
    row = dict(case=f["case_id"], subject=subj, relation=rw["relation_id"],
               target_new=rw["target_new"]["str"], edit_ok=ok["success"], p_new=ok["p_new"],
               loc_layer=loc, loc_ok=loc == L, s1_s2=prof[L]["s1_s2"],
               delta_s1_over_W_s1=prof[L]["s1"] / torch.linalg.matrix_norm(W.cpu(), 2).item(),
               subj_rank=rank, subj_rank_keycos=rank_keycos, top_subject=top_subj,
               obj_read=obj, obj_ok=obj.lower() == truth_obj.lower(), obj_top3_ok=truth_obj.lower() in [o.lower() for o in obj3], rel_read=rel, readback_score=gain,
               rel_ok=rel == rw["relation_id"],
               basefree_rank=rank_of(z, sidx[subj]), basefree_z=z[sidx[subj]].item(),
               secs=round(time.time() - t0, 1))
    rows.append(row)
    print(n, {k: row[k] for k in ["subject", "edit_ok", "loc_ok", "subj_rank", "obj_read", "obj_ok", "basefree_rank", "secs"]}, flush=True)
    restore(sus, snap)
    free_gpu()
    save_json(rows, RESULTS / f"exp1_{NAME}.json")
