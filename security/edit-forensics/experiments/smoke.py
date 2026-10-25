import sys, time; sys.path.insert(0, "src")
from common import *; from rome import *; from evalx import edit_success
m, t = load_model("gpt2-medium"); L = EDIT_LAYER["gpt2-medium"]
t0=time.time(); C = second_moment(m, t, L); print("C", C.shape, time.time()-t0)
cf = load_counterfact(); snap = snapshot(m)
for f in cf[:5]:
    print(f["requested_rewrite"]["subject"], "->", f["requested_rewrite"]["target_new"]["str"], "before", edit_success(m,t,f))
    t0=time.time(); rome_edit(m,t,L,f,C); print("after", edit_success(m,t,f), round(time.time()-t0,1),"s")
    restore(m, snap)
