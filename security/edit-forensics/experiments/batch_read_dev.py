"""Dev: is batch read-back weak because of batching, or are these facts just hard?"""
import sys, random; sys.path.insert(0, "src")
import torch
from common import *; from rome import rome_edit, second_moment; from forensics import *
m, tok = load_model(); L = 8; snap = snapshot(m); C = second_moment(m, tok, L)
cf = load_counterfact(); tm = relation_templates(cf); base = SwappedBase(m, snap)
rng = random.Random(4242); group = rng.sample(cf, 10)
tt = lambda f: tok.decode(tok(" " + f["requested_rewrite"]["target_new"]["str"])["input_ids"][:1]).strip()
single = []
for f in group:
    rome_edit(m, tok, L, f, C); single.append(read_object(m, base, tok, f["requested_rewrite"]["subject"], tm)[0]); restore(m, snap)
for f in group: rome_edit(m, tok, L, f, C)
for f, s1 in zip(group, single):
    rw = f["requested_rewrite"]
    print("BATCHDEV", rw["subject"], "| truth", tt(f), "| single", s1, "| batch", read_object(m, base, tok, rw["subject"], tm)[1], flush=True)
