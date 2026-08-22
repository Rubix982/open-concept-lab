"""
E-012 (T-A) — Make a REAL edit, measure ground-truth propagation.

The pivotal correction: we cannot predict neighbours without editing first. So we
edit one fact, then measure each neighbour PRE vs POST → a per-neighbour label
(propagated / stale / broken). That table is the target every predictor (T-B)
will be measured against.

Edit method: FT-L — fine-tune ONLY one MLP layer's down-projection (the weights
ROME edits) with a few gradient steps to flip the fact. A recognized editing
baseline (FT/FT-L in ROME/MEMIT/MQuAKE); no covariance stats, no EasyEdit.
(EasyEdit/ROME hit a transformers-5.15 incompatibility — deferred, not needed for T-A.)

Editing needs gradients → fp32 on CPU (fp32 stalls loading to MPS on this M2).

Usage:
    source .venv/bin/activate
    python experiments/edit_propagation/edit_ft.py
Env: EDIT_MODEL (default gpt2-medium), N_EDITS (default 5), EDIT_LAYER, FT_STEPS.
"""

import json
import os
import re
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ripplekit import config, data

MODEL = os.environ.get("EDIT_MODEL", "gpt2-medium")
N_EDITS = int(os.environ.get("N_EDITS", "5"))
FT_STEPS = int(os.environ.get("FT_STEPS", "30"))
FT_LR = float(os.environ.get("FT_LR", "1e-4"))   # 5e-4 exploded to NaN; 1e-4 + clip is stable
FT_CLIP = float(os.environ.get("FT_CLIP", "1.0"))
DEVICE = "cpu"   # editing needs fp32 grads; MPS fp32 stalls loading on this M2
OUT = config.RESULTS_DIR
OUT.mkdir(parents=True, exist_ok=True)

CRIT = config.CRITERION_TO_TYPE


def norm(k):
    return k.strip().lower().replace(" ", "_")


def parse_edit(entry):
    """Return (cloze, new_target, old_target) or None. cloze = shared prefix of
    the counterfactual and original statements; targets = their differing suffix."""
    ed = entry.get("edit") or {}
    orig = ed.get("original_fact") or {}
    p_new, p_old = ed.get("prompt"), orig.get("prompt")
    if not p_new or not p_old:
        return None
    # longest common prefix
    i = 0
    while i < len(p_new) and i < len(p_old) and p_new[i] == p_old[i]:
        i += 1
    cloze = p_new[:i].rstrip()
    new_t = p_new[i:].strip().rstrip(".").strip()
    old_t = p_old[i:].strip().rstrip(".").strip()
    if not cloze or not new_t or not old_t or cloze == p_new:
        return None
    return cloze, new_t, old_t


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
                    sids = q.get("subject_id") or []      # for subject-sharing (T-015)
                    out.append((t, q["prompt"], val, sids))
    return out


# ── model ─────────────────────────────────────────────────────────────────────
print(f"loading {MODEL} (fp32, {DEVICE})...", flush=True)
tok = AutoTokenizer.from_pretrained(MODEL)
# TODO(next): gpt2-medium NaNs at forward step 1 on CPU fp32 — likely an sdpa
# attention overflow. Try attn_implementation="eager" to fix, then scale to medium.
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).to(DEVICE).eval()
n_layer = model.config.n_layer
EDIT_LAYER = int(os.environ.get("EDIT_LAYER", str(n_layer // 3)))   # early-mid, ROME-ish
print(f"  {n_layer} layers; editing MLP c_proj at layer {EDIT_LAYER}\n", flush=True)


@torch.no_grad()
def answer(cloze: str, max_new=6) -> str:
    ids = tok(cloze, return_tensors="pt").to(DEVICE)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids.input_ids.shape[1]:], skip_special_tokens=True).strip()


def knows(cloze: str, target: str) -> bool:
    return target.lower()[:12] in answer(cloze).lower()


REP_LAYER = int(os.environ.get("REP_LAYER", "6"))


@torch.no_grad()
def rep(text: str) -> torch.Tensor:
    """Mean-pooled residual at REP_LAYER (predictor side). On the CURRENT model —
    call PRE-edit for a clean predictor."""
    ids = tok(text, return_tensors="pt").to(DEVICE)
    hs = model(**ids, output_hidden_states=True).hidden_states[REP_LAYER][0]
    return hs.mean(dim=0)


def cos(a, b):
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


# FT+L specificity constraint (ROME-style): KL to pre-edit distribution on
# unrelated prompts + weight decay on the delta. Set FTL=0 for plain FT.
FTL = os.environ.get("FTL", "1") == "1"
KL_FACTOR = float(os.environ.get("KL_FACTOR", "1.0"))
WD_FACTOR = float(os.environ.get("WD_FACTOR", "0.5"))
KL_PROMPTS = [
    "The capital of Germany is", "Water is made of", "The sun rises in the",
    "A dog is a kind of", "The opposite of hot is",
]


@torch.no_grad()
def _kl_ref():
    """Pre-edit last-token log-probs on the KL prompts (the locality anchor)."""
    refs = []
    for p in KL_PROMPTS:
        ids = tok(p, return_tensors="pt").to(DEVICE)
        refs.append(model(**ids).logits[0, -1].log_softmax(-1).detach())
    return refs


def ft_edit(cloze: str, new_target: str):
    """FT(+L): gradient steps on layer EDIT_LAYER's mlp.c_proj to complete `cloze`
    with `new_target`. FT+L adds a KL-to-pre-edit locality penalty + weight decay
    (the specificity mechanism ROME uses) so the edit doesn't wreck other facts."""
    w = model.transformer.h[EDIT_LAYER].mlp.c_proj.weight
    w0 = w.detach().clone()
    for p in model.parameters():
        p.requires_grad_(False)
    w.requires_grad_(True)
    opt = torch.optim.Adam([w], lr=FT_LR)
    full = tok(cloze + " " + new_target, return_tensors="pt").to(DEVICE)
    clen = tok(cloze, return_tensors="pt").input_ids.shape[1]
    labels = full.input_ids.clone()
    labels[0, :clen] = -100   # loss only on the target tokens
    kl_ref = _kl_ref() if FTL else None
    last = float("nan")
    for step in range(FT_STEPS):
        opt.zero_grad()
        loss = model(**full, labels=labels).loss     # nll on target
        if not torch.isfinite(loss):
            break
        if FTL:
            # KL locality: keep predictions on unrelated prompts near pre-edit
            kl = 0.0
            for p, ref in zip(KL_PROMPTS, kl_ref):
                ids = tok(p, return_tensors="pt").to(DEVICE)
                cur = model(**ids).logits[0, -1].log_softmax(-1)
                kl = kl + torch.nn.functional.kl_div(cur, ref, log_target=True,
                                                     reduction="sum")
            wd = WD_FACTOR * (w - w0).norm() ** 2 / (w0.norm() ** 2)
            loss = loss + KL_FACTOR * (kl / len(KL_PROMPTS)) + wd
        last = float(loss.detach())
        loss.backward()
        torch.nn.utils.clip_grad_norm_([w], FT_CLIP)
        opt.step()
        if new_target.lower()[:12] in answer(cloze).lower():
            break
    w.requires_grad_(False)
    return step + 1, last


# ── run ───────────────────────────────────────────────────────────────────────
entries = data.load_entries()
import random
random.Random(config.SEED).shuffle(entries)

rows = []                    # (type, propagated_bool)
tb_records = []              # per-neighbour: {edit, type, propagated, predictor} (T-B)
edits_done = 0
print("scanning for facts the model knows pre-edit, then editing...\n", flush=True)
for entry in entries:
    if edits_done >= N_EDITS:
        break
    pe = parse_edit(entry)
    if not pe:
        continue
    cloze, new_t, old_t = pe
    # competence filter optional: small models rarely complete RippleEdits' templated
    # phrasing, so requiring prior knowledge rejects everything. Default OFF — we edit
    # regardless (efficacy gate below ensures the edit actually took) and measure
    # propagation; note the caveat that prior knowledge isn't guaranteed.
    if os.environ.get("REQUIRE_KNOWS", "0") == "1" and not knows(cloze, old_t):
        continue
    nbrs = neighbours_of(entry)
    if not nbrs:
        continue

    edit_subj = set((entry.get("edit") or {}).get("subject_id", []) if isinstance(
        (entry.get("edit") or {}).get("subject_id"), list) else [(entry.get("edit") or {}).get("subject_id")])

    # PRE-edit (clean model): predictor cos(edited-fact, neighbour) + baseline answer.
    base_rep = rep(cloze)
    pred = {i: cos(base_rep, rep(p)) for i, (_, p, _, _) in enumerate(nbrs)}
    pre_ans = {i: answer(p) for i, (_, p, _, _) in enumerate(nbrs)}

    # snapshot the layer weight to restore after (so edits don't accumulate)
    w = model.transformer.h[EDIT_LAYER].mlp.c_proj.weight
    saved = w.detach().clone()

    steps, loss = ft_edit(cloze, new_t)
    took = knows(cloze, new_t)      # efficacy: did the edit flip the fact?

    edits_done += 1
    print(f"[edit {edits_done}] {cloze[:55]!r} → {new_t!r}", flush=True)
    print(f"    steps={steps} loss={loss:.3f} efficacy={'YES' if took else 'NO'}", flush=True)
    if took:
        for i, (typ, p, expected, sids) in enumerate(nbrs):
            post = answer(p)
            def _m(a, b):  # loose match on first 12 chars
                return b.lower()[:12] in a.lower()
            # 3-way outcome (T-015): updated (ripple-consistent) / stale (unchanged) / broken
            if _m(post, expected):
                outcome = "updated"
            elif post.strip().lower() == pre_ans[i].strip().lower():
                outcome = "stale"
            else:
                outcome = "broken"
            subject_shared = bool(edit_subj & set(sids))
            rows.append((typ, outcome == "updated"))
            tb_records.append({"edit": edits_done, "type": typ,
                               "propagated": int(outcome == "updated"),
                               "outcome": outcome, "subject_shared": int(subject_shared),
                               "predictor": pred[i]})

    # restore weights (isolate each edit)
    with torch.no_grad():
        w.copy_(saved)

# ── propagation table ──────────────────────────────────────────────────────────
print("\n── PROPAGATION by neighbour type (real edits) ──────────")
print(f"{'type':12s}  {'n':>4}  {'propagated':>11}")
print("─" * 32)
summary = {}
for t in config.TYPES:
    tr = [prop for (typ, prop) in rows if typ == t]
    if tr:
        rate = sum(tr) / len(tr)
        summary[t] = (len(tr), rate)
        print(f"{t:12s}  {len(tr):>4}  {rate:>10.1%}")

(OUT / "propagation_table.txt").write_text(
    f"model={MODEL} layer={EDIT_LAYER} edits={edits_done} ft_steps<= {FT_STEPS}\n"
    + "\n".join(f"{t}: n={n} propagated={r:.1%}" for t, (n, r) in summary.items())
)
(OUT / "tb_rows.json").write_text(json.dumps(tb_records, indent=0))
print(f"\nSaved → {OUT/'propagation_table.txt'}  and  {OUT/'tb_rows.json'} "
      f"({len(tb_records)} per-neighbour rows for T-B)")
print("This is the ground-truth target. If propagation drops with hop distance")
print("(paraphrase > 1hop > 2hop), we've reproduced the ripple-failure phenomenon")
print("on our own stack — the foundation T-B predicts against.")
