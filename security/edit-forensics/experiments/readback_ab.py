"""Pick an object read-back rule on a dev split (cases disjoint from E1's sample)."""
import sys,random; sys.path.insert(0,"src")
import torch
from common import *; from rome import *; from forensics import *
b,t=load_model(); s,_=load_model(); L=8; C=second_moment(b,t,L); snap=snapshot(s)
cf=load_counterfact(); tm=relation_templates(cf); rels=list(tm)
random.seed(7); facts=random.sample(cf,25)
from rome import PREFIXES
score={k:0 for k in "ABCDE"}
for f in facts:
    rw=f["requested_rewrite"]; subj=rw["subject"]
    truth=t.decode(t(" "+rw["target_new"]["str"])["input_ids"][:1]).strip().lower()
    rome_edit(s,t,L,f,C)
    pre=["", "In short, ", "I think "]
    ps=torch.stack([next_token_probs(s,t,[p+tm[r].format(subj) for r in rels]) for p in pre]).mean(0)
    pb=torch.stack([next_token_probs(b,t,[p+tm[r].format(subj) for r in rels]) for p in pre]).mean(0)
    pkl=ps*(torch.log(ps+1e-12)-torch.log(pb+1e-12))
    lr=torch.log(ps+1e-12)-torch.log(pb+1e-12)
    cand={}
    cand["A"]=pkl.flatten().argmax().item()%ps.shape[1]
    cand["B"]=pkl.clamp(min=0).sum(0).argmax().item()
    cand["C"]=torch.where(ps>0.05,lr,torch.full_like(lr,-1e9)).flatten().argmax().item()%ps.shape[1]
    rk=(ps*(torch.log(ps+1e-12)-torch.log(pb+1e-12))).sum(1).argmax().item(); cand["D"]=ps[rk].argmax().item()
    cand["E"]=(lr.clamp(min=0)*ps).clamp(min=0).sqrt().sum(0).argmax().item()
    out={k:t.decode([v]).strip() for k,v in cand.items()}
    for k,v in out.items(): score[k]+= v.lower()==truth
    print(subj,"->",truth,out,flush=True)
    restore(s,snap)
print(score)
