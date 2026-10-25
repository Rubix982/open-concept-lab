"""Minimal ROME (Meng et al. 2022) for HF GPT-2: the attacker's tool.

One fact (subject, relation prompt, new object) becomes a rank-one update to the
MLP output projection at one layer:  W += a r^T,  a = C^-1 k* / (k*^T C^-1 k*),
where k* is the subject's key and r the output change that makes the model say
the new object. Also supports spreading one edit across several layers
(MEMIT-style) and stacking many edits.
"""
import torch
import torch.nn.functional as F
from datasets import load_dataset

from common import CACHE, DEVICE, c_proj, capture_key, keys_at, last_subject_index

PREFIXES = [
    "", "The following is true. ", "I read this yesterday. ", "Here is a fact. ",
    "According to the article, ", "In summary, ", "It is well known that ",
    "Many people say that ", "Notes from class: ", "From the encyclopedia: ",
]


@torch.no_grad()
def second_moment(model, tok, layer, n_tokens=200_000, name="gpt2-medium", split="train"):
    """Uncentered E[k k^T] of the c_proj input at `layer`, over WikiText-103 text.
    Attacker and defender both compute it from public text, so neither needs secrets."""
    path = CACHE / f"{name}_L{layer}_mom2_{split}_{n_tokens}.pt"
    if path.exists():
        return torch.load(path)
    ds = load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1", split=split)
    texts = [t for t in ds["text"] if len(t) > 200]
    d = c_proj(model, layer).weight.shape[0]
    C = torch.zeros(d, d, device=DEVICE)
    seen = 0
    for t in texts:
        enc = tok(t, return_tensors="pt", truncation=True, max_length=256).to(DEVICE)
        store = {}
        with capture_key(model, layer, store):
            model.transformer(**enc)
        k = store["k"][0]
        C += k.T @ k
        seen += k.shape[0]
        if seen >= n_tokens:
            break
    C = (C / seen).cpu()
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(C, path)
    return C


def subject_key(model, tok, layer, subject):
    """k*: the subject's key at its last token, averaged over neutral prefixes."""
    texts = [p + subject for p in PREFIXES]
    idxs = [last_subject_index(tok, t, subject) for t in texts]
    return keys_at(model, tok, layer, texts, idxs).mean(0)


def solve_delta(model, tok, layer, subject, prompt, target, steps=25, lr=0.5,
                wd=0.5, kl_factor=0.0625, clamp=4.0, loss_layer=None):
    """Find r: the change in the c_proj output at the subject's last token that makes
    every prefixed `prompt.format(subject)` continue with `target`."""
    tgt = tok(" " + target)["input_ids"]
    rewrite = [p + prompt.format(subject) for p in PREFIXES]
    kl_text = [subject + " is a"]
    texts = [t + tok.decode(tgt[:-1]) for t in rewrite] + kl_text
    enc = tok(texts, return_tensors="pt", padding=True).to(DEVICE)
    sub_idx = [last_subject_index(tok, t, subject) for t in texts]
    # positions whose next-token prediction is a target token
    ans_start = [len(tok(t)["input_ids"]) - 1 for t in rewrite]
    kl_pos = len(tok(kl_text[0])["input_ids"]) - 1

    d = c_proj(model, layer).weight.shape[1]
    delta = torch.zeros(d, device=DEVICE, requires_grad=True)
    store = {}

    def add_delta(mod, inp, out):
        if "init" not in store:
            store["init"] = out[0, sub_idx[0]].detach().clone()
        out = out.clone()
        for i, j in enumerate(sub_idx):
            out[i, j] = out[i, j] + delta
        return out

    h = c_proj(model, layer).register_forward_hook(add_delta)
    opt = torch.optim.Adam([delta], lr=lr)
    kl_init = None
    try:
        for _ in range(steps):
            opt.zero_grad()
            logits = model(**enc).logits
            lp = F.log_softmax(logits.float(), -1)
            nll = 0.0
            for i, s in enumerate(ans_start):
                for j, t in enumerate(tgt):
                    nll = nll - lp[i, s + j, t]
            nll = nll / (len(rewrite) * len(tgt))
            kl_lp = lp[len(rewrite), kl_pos]
            if kl_init is None:
                kl_init = kl_lp.detach().clone()
            kl = kl_factor * F.kl_div(kl_init, kl_lp, log_target=True, reduction="sum")
            reg = wd * delta.norm() ** 2 / store["init"].norm() ** 2
            loss = nll + kl + reg
            if nll.item() < 0.05:
                break
            loss.backward()
            opt.step()
            with torch.no_grad():
                mx = clamp * store["init"].norm()
                if delta.norm() > mx:
                    delta.mul_(mx / delta.norm())
    finally:
        h.remove()
    return delta.detach()


@torch.no_grad()
def apply_rank_one(model, layer, k, r, C, ridge=1e-4):
    """W += a r^T with a = C^-1 k / (k^T C^-1 k): new output at k is old + r."""
    W = c_proj(model, layer).weight
    Cr = C.to(DEVICE) + ridge * torch.eye(C.shape[0], device=DEVICE) * C.diagonal().mean()
    ck = torch.linalg.solve(Cr, k.to(DEVICE))
    a = ck / (k.to(DEVICE) @ ck)
    W += torch.outer(a, r.to(DEVICE))
    return a.cpu(), r.cpu()


def rome_edit(model, tok, layer, fact, C):
    """Plant one CounterFact fact at `layer`. Returns the update's (a, r) factors."""
    rw = fact["requested_rewrite"]
    r = solve_delta(model, tok, layer, rw["subject"], rw["prompt"], rw["target_new"]["str"])
    k = subject_key(model, tok, layer, rw["subject"])
    return apply_rank_one(model, layer, k, r, C)


def spread_edit(model, tok, layers, fact, Cs):
    """MEMIT-style evasion: the same fact, with the output change split across
    several layers, so no single layer carries the whole edit."""
    rw = fact["requested_rewrite"]
    last = layers[-1]
    r = solve_delta(model, tok, last, rw["subject"], rw["prompt"], rw["target_new"]["str"])
    for l in layers:
        k = subject_key(model, tok, l, rw["subject"])
        apply_rank_one(model, l, k, r / len(layers), Cs[l])
