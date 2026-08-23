"""
E-014: scale the ripple study to a RANDOM RippleEdits sample → honest distribution.

Same per-neighbour 4-way outcome as rome_study.py (updated/stale/broken/fine), but
over N random edits from RippleEdits popular.json — so results show where ROME
GENERALIZES and where it FAILS, as a distribution, not 5 hand-picked landmarks.

Correctness carried over from rome_study.py:
  - rome_gpt2_mom2.yaml (covariance ON; stats cached under data/stats/)
  - monkeypatch restore_after_edit → no-op (else EasyEdit rolls the edit back)
  - snapshot/restore layer c_proj weight per edit (cross-edit isolation)
  - greedy-generate readout + substring match (robust to multi-token targets)
Anti-cherry-pick controls: random sample; EFFICACY filter (only record flipped edits);
COMPETENCE filter (skip pre-unknown neighbours). Checkpoints results every edit.

Run from the REPO ROOT in the edit venv (so data/stats/ resolves):
    source .venv-edit/bin/activate
    N_EDITS=80 python experiments/edit_propagation/scale_study.py
Env: ROME_CFG (default rome_gpt2_mom2.yaml), N_EDITS (default 60), SEED, RE_FILE.
Out: results/scale_study.json (rows) + results/scale_summary.txt (distribution).
"""

import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/code/EasyEdit"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer
from easyeditor import ROMEHyperParams, BaseEditor

import easyeditor.editors.editor as _ee
_ee.restore_after_edit = lambda *a, **k: None   # keep the edit so we can query it

HERE = Path(__file__).resolve().parent
CFG = os.environ.get("ROME_CFG", "rome_gpt2_mom2.yaml")
N_EDITS = int(os.environ.get("N_EDITS", "60"))
SEED = int(os.environ.get("SEED", "1538"))
RE_FILE = Path(os.environ.get("RE_FILE",
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json")))
RESULTS = HERE.parent.parent / "results"
DATA, TABLES = RESULTS / "final" / "data", RESULTS / "final" / "tables"
DATA.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)
ROWS_PATH, SUM_PATH = DATA / "scale_study.json", TABLES / "scale_summary.txt"

CRIT = {"logical_generalization": "1hop", "compositionality_i": "2hop",
        "compositionality_ii": "2hop", "subject_aliasing": "paraphrase",
        "relation_specificity": "locality", "relation_specifity": "locality",
        "forgetfulness": "control"}
ENTAILED, LOCALITY = {"paraphrase", "1hop", "2hop"}, {"locality", "control"}


def norm(k):
    return k.strip().lower().replace(" ", "_")


def parse_edit(entry):
    ed = entry.get("edit") or {}
    orig = ed.get("original_fact") or {}
    p_new, p_old = ed.get("prompt"), orig.get("prompt")
    if not p_new or not p_old:
        return None
    i = 0
    while i < len(p_new) and i < len(p_old) and p_new[i] == p_old[i]:
        i += 1
    cloze = p_new[:i].rstrip()
    new_t = p_new[i:].strip().rstrip(".").strip()
    if not cloze or not new_t or cloze == p_new:
        return None
    return cloze, new_t


def subject_of(cloze):
    """RippleEdits gives only a QID; the surface subject is the last ' of '-chunk."""
    s = cloze
    for tail in (" is", " are", " was", " were"):
        j = s.rfind(tail)
        if j != -1:
            s = s[:j]
    parts = s.split(" of ")
    subj = parts[-1].strip() if len(parts) > 1 else s.split()[-1]
    return subj.strip().strip(".,")


def neighbours_of(entry):
    out = []
    for k, v in entry.items():
        t = CRIT.get(norm(k))
        if t is None or not isinstance(v, list):
            continue
        for g in v:
            if not isinstance(g, dict):
                continue
            for q in g.get("test_queries") or []:
                anss = q.get("answers") or []
                val = anss[0].get("value") if anss and isinstance(anss[0], dict) else None
                if q.get("prompt") and val:
                    out.append((t, q["prompt"], val))
    return out[:8]


hparams = ROMEHyperParams.from_hparams(str(HERE / CFG))
tok = AutoTokenizer.from_pretrained(hparams.model_name)
editor = BaseEditor.from_hparams(hparams)
model = editor.model
DEV = next(model.parameters()).device
LAYER = hparams.layers[0]
wref = model.transformer.h[LAYER].mlp.c_proj.weight


@torch.no_grad()
def answer(prompt, max_new=6):
    """Greedy generation — robust to multi-token / rare RippleEdits targets."""
    ids = tok(prompt, return_tensors="pt").to(DEV)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids.input_ids.shape[1]:], skip_special_tokens=True).strip()


def has(a, b):
    """True if target b appears at the start of answer a (first 12 chars)."""
    if not a or not b or not b.strip():
        return False
    return b.strip().lower()[:12] in a.lower()


def is_word(s):
    return bool(s) and any(ch.isalpha() for ch in s)


entries = json.loads(RE_FILE.read_text())
random.Random(SEED).shuffle(entries)

rows, done, attempted, flipped = [], 0, 0, 0
for entry in entries:
    if attempted >= N_EDITS:
        break
    pe = parse_edit(entry)
    if not pe:
        continue
    cloze, new_t = pe
    nbrs = neighbours_of(entry)
    if not nbrs:
        continue
    subj = subject_of(cloze)
    if subj not in cloze:
        continue
    attempted += 1
    pre = [answer(p) for _, p, _ in nbrs]
    saved = wref.detach().clone()
    try:
        editor.edit(prompts=[cloze], target_new=[new_t], subject=[subj],
                    sequential_edit=False, verbose=False)
    except Exception as e:
        print(f"  [{attempted}] edit error {type(e).__name__}: {str(e)[:60]}", flush=True)
        with torch.no_grad():
            wref.copy_(saved)
        continue
    took = has(answer(cloze), new_t)
    print(f"[{attempted}] {'FLIP' if took else 'noflip'}  {subj!r:26}"
          f" {cloze[-40:]!r}->{new_t!r}", flush=True)
    if took:                                      # EFFICACY filter
        flipped += 1
        for i, (typ, p, expected) in enumerate(nbrs):
            post, pr = answer(p), pre[i]
            if typ in LOCALITY:
                if not has(pr, expected):         # COMPETENCE filter
                    outcome = "skip"
                else:
                    outcome = "fine" if has(post, expected) else "broken"
            else:                                 # entailed
                if not is_word(pr):
                    outcome = "skip"
                elif has(post, expected):
                    outcome = "updated"
                elif post.strip().lower() == pr.strip().lower() or has(post, pr):
                    outcome = "stale"
                else:
                    outcome = "broken"
            if outcome != "skip":
                rows.append({"edit": flipped, "subject": subj, "cloze": cloze,
                             "target_new": new_t, "type": typ, "prompt": p,
                             "expected": expected, "pre": pr, "post": post,
                             "outcome": outcome})
    with torch.no_grad():
        wref.copy_(saved)
    ROWS_PATH.write_text(json.dumps(rows, indent=1))   # checkpoint every edit
    done += 1


def summarize():
    hdr = (f"model={hparams.model_name} cfg={CFG} seed={SEED} file={RE_FILE.name}\n"
           f"attempted={attempted} flipped={flipped} "
           f"efficacy={flipped/attempted:.0%} rows={len(rows)}")
    lines = [hdr]
    for t in ["paraphrase", "1hop", "2hop", "locality", "control"]:
        sub = [r["outcome"] for r in rows if r["type"] == t]
        if not sub:
            continue
        c, n = Counter(sub), len(sub)
        parts = "  ".join(f"{k}={c[k]}({c[k]/n:.0%})"
                          for k in ["updated", "stale", "broken", "fine"] if c[k])
        lines.append(f"  {t:11s} n={n:>3}  {parts}")
    return "\n".join(lines)


SUM_PATH.write_text(summarize())
print("\n── distribution ──\n" + summarize())
print(f"\nSaved → {ROWS_PATH} ({len(rows)} rows), {SUM_PATH}")
