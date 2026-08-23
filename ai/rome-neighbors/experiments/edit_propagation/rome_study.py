"""
T-015 study: ROME edit → 3-way neighbour outcome (updated / stale / broken / fine),
on controlled well-known facts (clean subject strings + known old/new/ripple values).

Per edit case: ROME-edit the fact, then for each neighbour classify PRE→POST:
  entailed (should change): UPDATED (=new) / STALE (=old) / BROKEN (neither)
  locality (should NOT change): FINE (unchanged) / BROKEN (changed)

Saves per-neighbour records → results/rome_study.json (fed to viz + analysis).
Run in the EDIT venv:
    source .venv-edit/bin/activate
    python experiments/edit_propagation/rome_study.py
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/code/EasyEdit"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer
from easyeditor import ROMEHyperParams, BaseEditor

# EasyEdit's edit() RESTORES original weights after computing its own metrics
# (editor.py:295), so the returned model is un-edited — that's why our argmax
# check saw the original. Disable the auto-restore; our own snapshot/restore of
# the rewrite weight (below) handles cross-edit isolation instead.
import easyeditor.editors.editor as _ee
_ee.restore_after_edit = lambda *a, **k: None

HERE = Path(__file__).resolve().parent
CFG = os.environ.get("ROME_CFG", "rome_gpt2.yaml")
DATA = json.loads((HERE / "data" / "controlled_edits.json").read_text())
OUT = HERE.parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

hparams = ROMEHyperParams.from_hparams(str(HERE / CFG))
tok = AutoTokenizer.from_pretrained(hparams.model_name)
editor = BaseEditor.from_hparams(hparams)
model = editor.model
DEV = next(model.parameters()).device
LAYER = hparams.layers[0]
wref = model.transformer.h[LAYER].mlp.c_proj.weight


@torch.no_grad()
def next_tok(prompt, m):
    """Argmax next-token string of model `m` (aligns with EasyEdit teacher-forcing)."""
    ids = tok(prompt, return_tensors="pt").to(next(m.parameters()).device)
    return tok.decode(int(m(**ids).logits[0, -1].argmax())).strip()


def has(a, b):
    # first-token match: "Rome"→"Rome", "New York"→"New", "United States"→"United"
    return bool(a) and a.lower()[:4] == b.strip().split()[0].lower()[:4]


records = []
for case in DATA:
    nbrs = case["neighbors"]
    pre = [next_tok(n["prompt"], model) for n in nbrs]      # unedited model
    saved = wref.detach().clone()
    _, edited, _ = editor.edit(prompts=[case["cloze"]], target_new=[case["target_new"]],
                               subject=[case["subject"]], sequential_edit=False, verbose=False)
    took = has(next_tok(case["cloze"], edited), case["target_new"])   # query EDITED model
    print(f"[{case['id']}] {case['subject']} {case['target_old']}→{case['target_new']}"
          f"  efficacy={'YES' if took else 'NO'}", flush=True)
    if took:
        for i, n in enumerate(nbrs):
            post = next_tok(n["prompt"], edited)
            changes = n["old"] != n["new"]              # entailed vs locality
            if not changes:                             # locality
                outcome = "fine" if has(post, n["new"]) else "broken"
            elif has(post, n["new"]):
                outcome = "updated"
            elif post.strip().lower() == pre[i].strip().lower() or has(post, n["old"]):
                outcome = "stale"
            else:
                outcome = "broken"
            records.append({"case": case["id"], "type": n["type"], "outcome": outcome,
                            "prompt": n["prompt"], "old": n["old"], "new": n["new"],
                            "pre": pre[i], "post": post})
            print(f"    {n['type']:10s} [{outcome:7s}] {n['prompt'][:44]!r} → {post[:20]!r}", flush=True)
    with torch.no_grad():
        wref.copy_(saved)

(OUT / "rome_study.json").write_text(json.dumps(records, indent=1))

# summary
from collections import Counter
print("\n── ROME 3-way outcome by type ──")
for t in ["paraphrase", "1hop", "2hop", "reverse", "locality"]:
    sub = [r["outcome"] for r in records if r["type"] == t]
    if sub:
        c = Counter(sub)
        print(f"  {t:10s} n={len(sub):>2}  " + "  ".join(f"{k}={c[k]}" for k in
              ["updated", "stale", "broken", "fine"] if c[k]))
print(f"\nSaved → {OUT/'rome_study.json'} ({len(records)} neighbour records)")
