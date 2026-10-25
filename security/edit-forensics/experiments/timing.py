import sys,time; sys.path.insert(0,"src")
from common import *; from rome import *; from forensics import *
b,t=load_model(); s,_=load_model(); L=8; C=second_moment(b,t,L)
cf=load_counterfact(); subjects=sorted({f["requested_rewrite"]["subject"] for f in cf}); K=candidate_keys(b,t,L,subjects,"gpt2-medium")
tm=relation_templates(cf); print(len(tm),"relations")
for f in cf[:3]:
    T=time.time(); rome_edit(s,t,L,f,C); print("edit",time.time()-T)
    T=time.time(); D=weight_diffs(s,b); pr=layer_profile(D); print("prof",time.time()-T)
    T=time.time(); sc=fire_scores(D[8],K); top=subjects[sc.argmax()]; print("fire",time.time()-T, top)
    T=time.time(); print(read_object(s,b,t,top,tm), f["requested_rewrite"]["target_new"]["str"], "read",time.time()-T)
    T=time.time(); mlp_out_norms(s,t,subjects,list(range(24))); print("norms",time.time()-T)
    restore(s,snapshot(b))
