import sys,random,time; sys.path.insert(0,"src")
import torch
from common import *; from rome import *; from forensics import key_direction, word_vocab
from invert import gcg_invert
m,t=load_model(); L=8; C=second_moment(m,t,L); snap=snapshot(m)
cf=load_counterfact(); random.seed(7); facts=random.sample(cf,25)[:4]   # dev split
vocab=word_vocab(t)
for f in facts:
    subj=f["requested_rewrite"]["subject"]; rome_edit(m,t,L,f,C)
    D=(c_proj(m,L).weight-snap[L]).float(); kd=key_direction(D,C)
    for length in [2,3,4]:
        T=time.time(); r=gcg_invert(m,t,L,kd,vocab,length=length,steps=80,restarts=2)
        print(subj,"|",length,r,round(time.time()-T),flush=True)
    restore(m,snap)
