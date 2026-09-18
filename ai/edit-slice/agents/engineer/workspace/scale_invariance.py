"""E-016 · Is the destination invariant to the SCALE of the displacement?

[E-016] found whitening shrinks the same-subject coefficient 3.7x yet leaves the top-1
destination identical in 42/42 chains. The proposed explanation is that `C` sets only a
scalar gain — the displaced direction `v* - Wk*` is fixed by the edit target — and top-1
over the city pool is largely invariant to a positive rescaling of a fixed perturbation.

Test it directly: rescale the UNWHITENED coefficient and see where the destination breaks.
If C=I at 0.27x still lands on the same city, scale-invariance is the mechanism and no
choice of C could have changed the E-015 result.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SCALES = [1.0, 0.27, 0.10, 0.03, 0.01]

log = setup("scale_invariance", config={"ticket": "E-016", "scales": SCALES, "layer": LAYER})
e14 = json.loads((ROOT / "results" /
                  "E-014-destination-meta-llama_Llama-3.1-8B.json").read_text())
chains = {c["seed_case_id"]: c for c in json.loads(
    (ROOT / "probes" / "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
geo = json.loads((ROOT / "probes" / "geo.json").read_text())
pt = json.loads((ROOT / "probes" / "place_types.json").read_text())
pool = e14["pool"]
cc = {c: k for c, k in geo["city_country"].items() if c not in set(pt["not_settlement"])}
for ctry, cap in geo["capital"].items():
    cc[cap] = ctry

d14 = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s1538.pt")
ks14 = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
rows = [r for r in e14["results"] if r["in_target"]["real"]][:8]

m = connect("meta-llama/Llama-3.1-8B")
log.info("%-8s%-16s%s", "chain", "target", "  ".join(f"x{s:<10}" for s in SCALES))
hits = {s: 0 for s in SCALES}
for r in rows:
    cid = r["case_id"]
    kstar = ks14[f"{cid}|real"].float()
    dv = d14[f"{cid}|real"]
    p1 = chains[cid]["inner_1"]["prompt"]
    tops = []
    for s in SCALES:
        # scale the coefficient by shrinking the denominator's inverse: u = k*, den = k*.k*/s
        den = float(kstar @ kstar) / s
        sc = score_pairs(m, [(p1, city) for city in pool],
                         edit=(LAYER, kstar, den, dv))
        top = pool[max(range(len(pool)), key=lambda j: sc[j])]
        tops.append(top)
        hits[s] += cc.get(top) == r["target_country"]
    log.info("%-8s%-16s%s", cid, r["target_country"],
             "  ".join(f"{t[:10]:<11}" for t in tops))

log.info("")
log.info("lands in target country, by displacement scale:")
for s in SCALES:
    log.info("   x%-6.2f  %d/%d", s, hits[s], len(rows))
log.info("")
log.info("If x0.27 matches x1.00, whitening's 3.7x attenuation cannot change the")
log.info("destination, and no choice of C could have altered the E-015 null.")
