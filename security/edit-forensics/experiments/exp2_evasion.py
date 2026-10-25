"""E2: the attacker tries to hide the edit; the defender (holding the clean base) tries anyway.

Attacks (argv[1]):
  noise     ROME, then Gaussian noise on every weight (std = eps * that tensor's std)
  finetune  ROME, then a short fine-tune of the whole model on WikiText
  spread    the fact split across layers 4..8 (MEMIT-style), no single layer holds it
  batch     N facts planted at once at the edit layer
  decoy     1 real fact + M decoy rank-one updates of the same size on random subjects
For every attack we also record whether the planted fact still works (an evasion
that breaks the edit is not an evasion) and the WikiText perplexity cost.
"""
import os, random, sys, time
sys.path.insert(0, "src")
import torch
import torch.nn.functional as F
from datasets import load_dataset
from common import *
from rome import rome_edit, second_moment, spread_edit, subject_key, apply_rank_one
from evalx import edit_success
from forensics import *

ATTACK = sys.argv[1]
N_FACTS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
NAME = "gpt2-medium"
SMOKE = os.environ.get("SMOKE") == "1"   # tiny loops, to catch crashes before the real run
L = EDIT_LAYER[NAME]
base, tok = load_model(NAME)
sus, _ = load_model(NAME)
cf = load_counterfact()
subjects = sorted({f["requested_rewrite"]["subject"] for f in cf})
sidx = {s: i for i, s in enumerate(subjects)}
templates = relation_templates(cf)
C = {L: second_moment(base, tok, L, name=NAME)}
K = {L: candidate_keys(base, tok, L, subjects, NAME)}
val_n = 5 if SMOKE else 60
val = [t for t in load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1", split="validation")["text"] if len(t) > 400][:val_n]
train = [t for t in load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1", split="train[:200000]")["text"] if len(t) > 400]


def reset():
    sus.load_state_dict(base.state_dict())
    free_gpu()
    for p in sus.parameters():
        p.requires_grad_(False)


@torch.no_grad()
def ppl(model):
    tot, n = 0.0, 0
    for t in val:
        enc = tok(t, return_tensors="pt", truncation=True, max_length=256).to(DEVICE)
        out = model(**enc, labels=enc["input_ids"])
        tot += out.loss.item() * (enc["input_ids"].shape[1] - 1); n += enc["input_ids"].shape[1] - 1
    return float(torch.exp(torch.tensor(tot / n)))


BASE_PPL = ppl(base)


@torch.no_grad()
def add_noise(model, eps, seed):
    g = torch.Generator(device="cpu").manual_seed(seed)
    for p in model.parameters():
        if p.dim() < 2:
            continue
        p += (torch.randn(p.shape, generator=g) * eps * p.float().std().item()).to(DEVICE)


def finetune(model, steps, lr, seed):
    rng = random.Random(seed)
    for p in model.parameters():
        p.requires_grad_(True)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    model.train()
    for _ in range(steps):
        batch = rng.sample(train, 4)
        enc = tok(batch, return_tensors="pt", truncation=True, max_length=128, padding=True).to(DEVICE)
        labels = enc["input_ids"].masked_fill(enc["attention_mask"] == 0, -100)
        loss = model(**enc, labels=labels).loss
        opt.zero_grad(); loss.backward(); opt.step()
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)


def truth_tok(f):
    return tok.decode(tok(" " + f["requested_rewrite"]["target_new"]["str"])["input_ids"][:1]).strip().lower()


def defend_single(f, denoise_rank=None):
    """Standard defender: localise the most rank-one layer, fire every candidate, read back."""
    D = weight_diffs(sus, base)
    prof = layer_profile(D)
    loc = localise(prof)
    if loc not in K:
        K[loc] = candidate_keys(base, tok, loc, subjects, NAME)
    out = {"loc_layer": loc, "loc_ok": loc == L, "s1_s2_at_L": prof[L]["s1_s2"]}
    # self-ablated reference: the suspect with the top rank-one part of its diff removed.
    # It carries the same noise / fine-tuning as the suspect, so only the plant differs.
    U, S_, Vh = torch.linalg.svd(D[loc].cpu(), full_matrices=False)
    W_abl = c_proj(sus, loc).weight - (S_[0] * torch.outer(U[:, 0], Vh[0])).to(DEVICE)
    ablated = SwappedBase(sus, {loc: W_abl})
    for tag, dr in [("raw", None), ("denoised", 1)]:
        sc = fire_scores(D[loc], K[loc], denoise_rank=dr)
        top = subjects[sc.argmax().item()]
        obj, _, rel, _ = read_object(sus, base, tok, top, templates)
        out[f"subj_rank_{tag}"] = rank_of(sc, sidx[f["requested_rewrite"]["subject"]])
        out[f"obj_ok_{tag}"] = obj.lower() == truth_tok(f)
        if tag == "denoised":
            obj_a, _, _, _ = read_object(sus, ablated, tok, top, templates)
            out["obj_ok_selfablate"] = obj_a.lower() == truth_tok(f)
    return out


random.seed(1)
facts = random.sample(cf, N_FACTS)
rows = []
tag = ATTACK

if ATTACK == "noise":
    for eps in ([0.01] if SMOKE else [0.003, 0.01, 0.03, 0.1]):
        for n, f in enumerate(facts):
            reset(); rome_edit(sus, tok, L, f, C[L]); add_noise(sus, eps, seed=n)
            row = dict(eps=eps, subject=f["requested_rewrite"]["subject"], **edit_success(sus, tok, f), **defend_single(f))
            if n == 0:
                row["ppl"] = ppl(sus)
            rows.append(row); print(row, flush=True)
            save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")

elif ATTACK == "finetune":
    for steps in ([3] if SMOKE else [25, 100, 300]):
        for n, f in enumerate(facts[:15]):
            reset(); rome_edit(sus, tok, L, f, C[L]); finetune(sus, steps, 2e-5, seed=n)
            row = dict(steps=steps, subject=f["requested_rewrite"]["subject"], **edit_success(sus, tok, f), **defend_single(f))
            if n == 0:
                row["ppl"] = ppl(sus)
            rows.append(row); print(row, flush=True)
            save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")

elif ATTACK == "spread":
    layers = [4, 5, 6, 7, 8]
    for l in layers:
        C.setdefault(l, second_moment(base, tok, l, name=NAME))
        K.setdefault(l, candidate_keys(base, tok, l, subjects, NAME))
    for n, f in enumerate(facts):
        reset(); spread_edit(sus, tok, layers, f, C)
        D = weight_diffs(sus, base); prof = layer_profile(D)
        single = defend_single(f)
        # spread-aware defender: sum normalised fire over every layer whose diff is rank-one
        flagged = [l for l in prof if prof[l]["s1_s2"] > 10]
        for l in flagged:
            K.setdefault(l, candidate_keys(base, tok, l, subjects, NAME))
        agg = sum(fire_scores(D[l], K[l]) / prof[l]["s1"] for l in flagged)
        top = subjects[agg.argmax().item()]
        obj, _, rel, _ = read_object(sus, base, tok, top, templates)
        row = dict(subject=f["requested_rewrite"]["subject"], **edit_success(sus, tok, f), **single,
                   flagged=flagged, subj_rank_agg=rank_of(agg, sidx[f["requested_rewrite"]["subject"]]),
                   obj_ok_agg=obj.lower() == truth_tok(f))
        rows.append(row); print(row, flush=True)
        save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")

elif ATTACK == "batch":
    pool = [f for f in cf if f not in facts]
    for size in ([3] if SMOKE else [10, 30, 100]):
        for trial in range(1 if SMOKE else 3):
            rng = random.Random(100 * size + trial)
            # distinct subjects in one batch
            group, seen = [], set()
            for f in rng.sample(pool, size * 3):
                s = f["requested_rewrite"]["subject"]
                if s not in seen:
                    group.append(f); seen.add(s)
                if len(group) == size:
                    break
            reset()
            for f in group:
                rome_edit(sus, tok, L, f, C[L])
            ok = [edit_success(sus, tok, f)["success"] for f in group]
            D = weight_diffs(sus, base)
            sc = fire_scores(D[L], K[L])
            topN = set(torch.topk(sc, size).indices.tolist())
            truth = {sidx[f["requested_rewrite"]["subject"]] for f in group}
            hits = len(topN & truth)
            obj_ok = 0
            for f in group:
                if sidx[f["requested_rewrite"]["subject"]] in topN:
                    obj, _, _, _ = read_object(sus, base, tok, f["requested_rewrite"]["subject"], templates)
                    obj_ok += obj.lower() == truth_tok(f)
            row = dict(size=size, trial=trial, edit_ok_rate=sum(ok) / size,
                       precision_at_N=hits / size, obj_ok_rate=obj_ok / size,
                       ppl=ppl(sus), loc_ok=localise(layer_profile(D), by="fro") == L)
            rows.append(row); print(row, flush=True)
            save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")

elif ATTACK == "batch2":
    # Held-out re-run with fresh seeds after the subspace score was chosen on the
    # original batch trials (experiments/batch_dev.py). Reports both scores.
    pool = [f for f in cf if f not in facts]
    for size in ([3] if SMOKE else [10, 30, 100]):
        for trial in range(1 if SMOKE else 5):
            rng = random.Random(7919 * size + 1000 + trial)
            group, seen = [], set()
            for f in rng.sample(pool, size * 3):
                s = f["requested_rewrite"]["subject"]
                if s not in seen:
                    group.append(f); seen.add(s)
                if len(group) == size:
                    break
            reset()
            for f in group:
                rome_edit(sus, tok, L, f, C[L])
            ok = [edit_success(sus, tok, f)["success"] for f in group]
            D = weight_diffs(sus, base)
            truth = {sidx[f["requested_rewrite"]["subject"]] for f in group}
            row = dict(size=size, trial=trial, edit_ok_rate=sum(ok) / size, ppl=ppl(sus))
            for name, sc in [("fire", fire_scores(D[L], K[L])), ("subspace", subspace_scores(D[L], C[L], K[L])[0])]:
                topN = set(torch.topk(sc, size).indices.tolist())
                row[f"precision_{name}"] = len(topN & truth) / size
                obj_ok = 0
                for f in group:
                    if sidx[f["requested_rewrite"]["subject"]] in topN:
                        obj, _, _, _ = read_object(sus, base, tok, f["requested_rewrite"]["subject"], templates)
                        obj_ok += obj.lower() == truth_tok(f)
                row[f"obj_ok_rate_{name}"] = obj_ok / size
                if name == "subspace":
                    # per-subject self-ablation: undo only this key's share of the diff
                    Cinv_ridge = C[L].to(DEVICE) + 1e-4 * torch.eye(C[L].shape[0], device=DEVICE) * C[L].diagonal().mean().to(DEVICE)
                    obj_ok = 0
                    for f in group:
                        j = sidx[f["requested_rewrite"]["subject"]]
                        if j not in topN:
                            continue
                        k = K[L][j].to(DEVICE).float()
                        ck = torch.linalg.solve(Cinv_ridge, k)
                        Wd = D[L].to(DEVICE)
                        W_abl = c_proj(sus, L).weight - torch.outer(ck / (k @ ck), k @ Wd)
                        obj, _, _, _ = read_object(sus, SwappedBase(sus, {L: W_abl}), tok, f["requested_rewrite"]["subject"], templates)
                        obj_ok += obj.lower() == truth_tok(f)
                    row["obj_ok_rate_selfablate"] = obj_ok / size
            rows.append(row); print(row, flush=True)
            save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")

elif ATTACK == "decoy":
    M = 3 if SMOKE else 50
    for n, f in enumerate(facts[:20]):
        reset()
        a, r = rome_edit(sus, tok, L, f, C[L])
        rng = random.Random(n)
        decoys = rng.sample([s for s in subjects if s != f["requested_rewrite"]["subject"]], M)
        for s in decoys:
            k = subject_key(sus, tok, L, s)
            rr = torch.randn(r.shape, generator=torch.Generator().manual_seed(rng.randint(0, 10**9)))
            apply_rank_one(sus, L, k, rr / rr.norm() * r.norm(), C[L])
        D = weight_diffs(sus, base)
        sc = fire_scores(D[L], K[L])
        true_i = sidx[f["requested_rewrite"]["subject"]]
        # defender second stage: read back every fired subject; a real plant makes ONE token jump
        top = torch.topk(sc, M + 1).indices.tolist()
        gains = []
        for i in top:
            obj, _, rel, g = read_object(sus, base, tok, subjects[i], templates)
            gains.append((g, i, obj))
        gains.sort(reverse=True)
        stage2_rank = [i for _, i, _ in gains].index(true_i) + 1 if true_i in top else None
        row = dict(subject=f["requested_rewrite"]["subject"], **edit_success(sus, tok, f),
                   fire_rank=rank_of(sc, true_i), stage2_rank=stage2_rank,
                   top_obj_ok=gains[0][2].lower() == truth_tok(f))
        rows.append(row); print(row, flush=True)
        save_json({"base_ppl": BASE_PPL, "rows": rows}, RESULTS / f"exp2_{tag}{'_smoke' if SMOKE else ''}.json")
