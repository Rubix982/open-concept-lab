"""Does score_pairs(edit=...) reproduce the pilot's Vlaminck relocation?

The pilot found Edinburgh->Hamburg style relocation via first-token argmax. This
ranks FULL city names. If the edited scorer works, Vlaminck edited to Germany should
rank a German city first at inner_1, and the unedited scorer should rank Paris.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from edit import LAYER, EditSpec, compute_v_batch, read_key_and_value  # noqa: E402
from logs import setup  # noqa: E402
from remote import connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
geo = json.loads((ROOT / "probes" / "geo.json").read_text())
pool = sorted(set(geo["city_country"]) | set(geo["capital"].values()))
cc = dict(geo["city_country"])
for ctry, cap in geo["capital"].items():
    cc.setdefault(cap, ctry)

log = setup("verify_edited_scoring", config={"ticket": "E-014", "pool": len(pool)})
m = connect("meta-llama/Llama-3.1-8B")

SUBJ = "Maurice de Vlaminck"
P1 = f"{SUBJ} was born in the city of"
sp = EditSpec("v|real", f"{SUBJ} was born in the country of", SUBJ, "Germany")
delta = compute_v_batch(m, [sp])[sp.case_id]
k_star, _ = read_key_and_value(m, sp.prompt, sp.subject, LAYER)

for name, ed in (("baseline", None), ("edited -> Germany", (LAYER, k_star, delta))):
    sc = score_pairs(m, [(P1, c) for c in pool], edit=ed)
    order = sorted(range(len(pool)), key=lambda j: -sc[j])[:5]
    log.info("%-18s %s", name,
             "  ".join(f"{pool[j]}({cc.get(pool[j],'?')})" for j in order))
