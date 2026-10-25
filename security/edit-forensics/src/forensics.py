"""The defender's tools: given a suspect checkpoint, find what was planted.

Every function takes the suspect model (and, where stated, the clean base).
Nothing here sees the attacker's (a, r) factors or the planted fact.
"""
import torch

from common import CACHE, DEVICE, c_proj, keys_at, last_subject_index, n_layers

CAND_PREFIXES = ["", "The following is true. "]


# ---------- localisation ----------

@torch.no_grad()
def weight_diffs(suspect, base):
    """base: a clean model, or a snapshot dict {layer: c_proj weight}."""
    get = (lambda l: base[l]) if isinstance(base, dict) else (lambda l: c_proj(base, l).weight)
    return {l: (c_proj(suspect, l).weight - get(l)).float() for l in range(n_layers(suspect))}


@torch.no_grad()
def layer_profile(diffs):
    """Per layer: Frobenius norm of the diff and how rank-one it is (sigma1/sigma2)."""
    prof = {}
    for l, D in diffs.items():
        s = torch.linalg.svdvals(D.cpu())
        prof[l] = {"fro": D.norm().item(), "s1": s[0].item(),
                   "s1_s2": (s[0] / (s[1] + 1e-12)).item()}
    return prof


def localise(prof, by="s1_s2"):
    """Layer whose diff is most rank-one (robust to diffuse noise) or largest ('fro')."""
    return max(prof, key=lambda l: prof[l][by])


# ---------- subject recovery, closed list ----------

def candidate_keys(model, tok, layer, subjects, tag):
    """Keys at `layer` for every candidate subject, cached. Layers above the edit
    are untouched by a single-layer edit, so base-model keys are exact there."""
    path = CACHE / f"cand_{tag}_L{layer}.pt"
    if path.exists():
        return torch.load(path)
    ks = 0
    for p in CAND_PREFIXES:
        texts = [p + s for s in subjects]
        idxs = [last_subject_index(tok, t, s) for t, s in zip(texts, subjects)]
        ks = ks + keys_at(model, tok, layer, texts, idxs, batch=256)
    ks = (ks / len(CAND_PREFIXES)).half()
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(ks, path)
    return ks


@torch.no_grad()
def fire_scores(D, K, denoise_rank=None):
    """How strongly the update fires on each candidate key: ||k^T D|| / ||k||.
    With denoise_rank, D is first truncated to its top singular directions,
    which strips diffuse masking noise."""
    D = D.to(DEVICE)
    if denoise_rank:
        U, S, Vh = torch.linalg.svd(D, full_matrices=False)
        D = (U[:, :denoise_rank] * S[:denoise_rank]) @ Vh[:denoise_rank]
    out = []
    for i in range(0, len(K), 4096):
        k = K[i:i + 4096].to(DEVICE).float()
        out.append(((k @ D).norm(dim=1) / k.norm(dim=1)).cpu())
    return torch.cat(out)


def rank_of(scores, idx):
    """1-based rank of candidate idx (1 = top)."""
    return int((scores > scores[idx]).sum().item()) + 1


# ---------- subject recovery, open vocabulary ----------

@torch.no_grad()
def key_direction(D, C):
    """The key the update was built for. ROME's update is a r^T with a = C^-1 k*, so the
    top left singular vector of the diff, mapped back through C, points along k*."""
    U, S, Vh = torch.linalg.svd(D.float().cpu(), full_matrices=False)
    k = C.float() @ U[:, 0]
    return k / k.norm()


@torch.no_grad()
def keycos_scores(K, kdir):
    """|cos(k, k_hat)| for each candidate key: bounded, so off-distribution junk cannot win by size."""
    kdir = kdir.to(DEVICE)
    out = []
    for i in range(0, len(K), 4096):
        k = K[i:i + 4096].to(DEVICE).float()
        out.append(((k @ kdir).abs() / k.norm(dim=1)).cpu())
    return torch.cat(out)


@torch.no_grad()
def fire_on_texts(model, tok, layer, D, token_seqs, batch=512, kdir=None):
    """Score at the last token of each token sequence: fire strength of D, or with kdir,
    |cos| between the key there and the update's key direction."""
    texts = [tok.decode(s) for s in token_seqs]
    scores = []
    for i in range(0, len(token_seqs), batch):
        chunk = token_seqs[i:i + batch]
        L = max(len(s) for s in chunk)
        ids = torch.full((len(chunk), L), tok.eos_token_id)
        att = torch.zeros((len(chunk), L), dtype=torch.long)
        for j, s in enumerate(chunk):
            ids[j, :len(s)] = torch.tensor(s)
            att[j, :len(s)] = 1
        K = keys_at_ids(model, layer, ids.to(DEVICE), att.to(DEVICE),
                        [len(s) - 1 for s in chunk])
        if kdir is not None:
            scores.append(((K @ kdir).abs() / K.norm(dim=1)).cpu())
        else:
            scores.append(((K @ D).norm(dim=1) / K.norm(dim=1)).cpu())
    return torch.cat(scores)


def keys_at_ids(model, layer, ids, att, idxs):
    from common import capture_key, _Stop
    store = {}
    try:
        with capture_key(model, layer, store, stop=True):
            model.transformer(input_ids=ids, attention_mask=att)
    except _Stop:
        pass
    k = store["k"]
    return k[torch.arange(len(idxs), device=DEVICE), torch.tensor(idxs, device=DEVICE)].float()


def word_vocab(tok):
    """Token ids that look like (pieces of) words: letters only, optional leading space."""
    keep = []
    for i in range(len(tok)):
        s = tok.decode([i])
        core = s[1:] if s.startswith(" ") else s
        if core.isascii() and core.isalpha() and len(core) >= 2:
            keep.append(i)
    return keep


@torch.no_grad()
def invert_trigger(model, tok, layer, D, vocab, beam=8, depth=3, top_last=8, kdir=None):
    """Search token strings, right to left, for the one the update fires on hardest.
    Step 1 scores every vocab token as a final token; later steps prepend tokens to
    the best beams. Returns [(string, score)] best first, across all depths."""
    D = D.to(DEVICE)
    kd = None if kdir is None else kdir.to(DEVICE)
    single = fire_on_texts(model, tok, layer, D, [[v] for v in vocab], kdir=kd)
    top = torch.topk(single, top_last).indices.tolist()
    beams = [([vocab[i]], single[i].item()) for i in top]
    found = list(beams)
    for _ in range(depth - 1):
        cand = [[v] + b for b, _ in beams for v in vocab]
        sc = fire_on_texts(model, tok, layer, D, cand, kdir=kd)
        best = torch.topk(sc, beam).indices.tolist()
        beams = [(cand[i], sc[i].item()) for i in best]
        found += beams
    found.sort(key=lambda x: -x[1])
    return [(tok.decode(s), sc) for s, sc in found]


# ---------- object read-back ----------

def relation_templates(cf):
    seen = {}
    for f in cf:
        rw = f["requested_rewrite"]
        seen.setdefault(rw["relation_id"], rw["prompt"])
    return seen


@torch.no_grad()
def next_token_probs(model, tok, prompts):
    enc = tok(prompts, return_tensors="pt", padding=True).to(DEVICE)
    logits = model(**enc).logits
    last = enc["attention_mask"].sum(1) - 1
    return torch.softmax(logits[torch.arange(len(prompts)), last].float(), -1)


READ_PREFIXES = ["", "In short, ", "I think "]


@torch.no_grad()
def read_object(suspect, base, tok, subject, templates, k=3):
    """Ask both models every relation about `subject` (under a few prefixes); score each
    token by its positive pointwise KL, p_s * log(p_s / p_b), summed over relations.
    A planted object rises from rare to likely on several related prompts; a side-effect
    token usually rises on one. Rule chosen on a dev split (experiments/readback_ab.py).
    Returns (top token, top-k tokens, relation where it rose most, score)."""
    rels = list(templates)
    ps = torch.stack([next_token_probs(suspect, tok, [p + templates[r].format(subject) for r in rels])
                      for p in READ_PREFIXES]).mean(0)
    pb = torch.stack([next_token_probs(base, tok, [p + templates[r].format(subject) for r in rels])
                      for p in READ_PREFIXES]).mean(0)
    pkl = (ps * (torch.log(ps + 1e-12) - torch.log(pb + 1e-12))).clamp(min=0)
    tot = pkl.sum(0)
    top = torch.topk(tot, k).indices.tolist()
    rel = rels[pkl[:, top[0]].argmax().item()]
    return tok.decode([top[0]]).strip(), [tok.decode([x]).strip() for x in top], rel, tot[top[0]].item()


# ---------- base-free ----------

@torch.no_grad()
def mlp_out_norms(model, tok, subjects, layers, batch=128):
    """||c_proj output|| at each candidate's last subject token, for each layer.
    No base model needed: a planted fact shows up as an outsized MLP write."""
    res = {l: [] for l in layers}
    hooks, store = [], {}
    for l in layers:
        hooks.append(c_proj(model, l).register_forward_hook(
            lambda m, i, o, l=l: store.__setitem__(l, o)))
    try:
        for i in range(0, len(subjects), batch):
            ch = subjects[i:i + batch]
            enc = tok(ch, return_tensors="pt", padding=True).to(DEVICE)
            model.transformer(**enc)
            last = (enc["attention_mask"].sum(1) - 1)
            ar = torch.arange(len(ch), device=DEVICE)
            for l in layers:
                res[l].append(store[l][ar, last].norm(dim=1).float().cpu())
    finally:
        for h in hooks:
            h.remove()
    return {l: torch.cat(v) for l, v in res.items()}


@torch.no_grad()
def subspace_scores(D, C, K, rank=None, tol=1e-3):
    """Batch-edit version of keycos. A stack of ROME updates is sum_i a_i r_i^T with
    a_i = C^-1 k_i / (...), so every planted key lies in span(C U), U the diff's left
    singular vectors. Score = share of a candidate key's length inside that span.
    rank defaults to the diff's numerical rank."""
    U, S, Vh = torch.linalg.svd(D.float().cpu(), full_matrices=False)
    if rank is None:
        rank = int((S > tol * S[0]).sum().item())
    B = C.float() @ U[:, :rank]
    Q, _ = torch.linalg.qr(B)
    Q = Q.to(DEVICE)
    out = []
    for i in range(0, len(K), 4096):
        k = K[i:i + 4096].to(DEVICE).float()
        out.append(((k @ Q).norm(dim=1) / k.norm(dim=1)).cpu())
    return torch.cat(out), rank
