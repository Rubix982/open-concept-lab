"""Dev check: subspace score vs fire on the two worst batch trials of E2 (same seeds)."""
import sys, random; sys.path.insert(0, "src")
import torch
from common import *; from rome import rome_edit, second_moment; from forensics import *
m, tok = load_model(); L = 8; snap = snapshot(m); C = second_moment(m, tok, L)
cf = load_counterfact(); subjects = sorted({f["requested_rewrite"]["subject"] for f in cf}); sidx = {s: i for i, s in enumerate(subjects)}
K = candidate_keys(m, tok, L, subjects, "gpt2-medium")
random.seed(1); facts = random.sample(cf, 30); pool = [f for f in cf if f not in facts]
for size, trial in [(10, 2), (30, 1), (10, 0)]:
    rng = random.Random(100 * size + trial); group, seen = [], set()
    for f in rng.sample(pool, size * 3):
        s = f["requested_rewrite"]["subject"]
        if s not in seen: group.append(f); seen.add(s)
        if len(group) == size: break
    for f in group: rome_edit(m, tok, L, f, C)
    D = (c_proj(m, L).weight - snap[L]).float()
    truth = {sidx[f["requested_rewrite"]["subject"]] for f in group}
    fire = fire_scores(D, K); sub, r = subspace_scores(D, C, K); subN, _ = subspace_scores(D, C, K, rank=size)
    P = lambda sc: len(set(torch.topk(sc, size).indices.tolist()) & truth) / size
    print(size, trial, "fire", P(fire), "subspace(rank=%d)" % r, P(sub), "subspace(rank=N)", P(subN),
          "top fire non-planted:", [subjects[i] for i in torch.topk(fire, size).indices.tolist() if i not in truth][:4], flush=True)
    restore(m, snap)
