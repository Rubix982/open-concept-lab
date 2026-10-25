"""Open-vocabulary trigger inversion by gradient-guided token search (GCG, Zou et al. 2023).

Goal: with no list of candidate names, find a token string whose key at the edited layer
points along the update's key direction k_hat (forensics.key_direction). Score is
|cos(key at last token, k_hat)|; the true subject scores ~0.95, unrelated text ~0.3.
"""
import torch

from common import DEVICE, _Stop, capture_key


def _keys_from_embeds(model, layer, embeds):
    store = {}
    try:
        with capture_key(model, layer, store, stop=True):
            model.transformer(inputs_embeds=embeds)
    except _Stop:
        pass
    return store["k"][:, -1].float()


@torch.no_grad()
def _score_ids(model, layer, ids, kdir, batch=512):
    out = []
    for i in range(0, len(ids), batch):
        store = {}
        try:
            with capture_key(model, layer, store, stop=True):
                model.transformer(input_ids=ids[i:i + batch])
        except _Stop:
            pass
        k = store["k"][:, -1].float()
        out.append((k @ kdir).abs() / k.norm(dim=1))
    return torch.cat(out)


def gcg_invert(model, tok, layer, kdir, allowed, length=3, steps=80, topk=64,
               n_cand=384, restarts=2, seed=0):
    """Returns [(string, score)] best first, one per restart."""
    g = torch.Generator().manual_seed(seed)
    W = model.transformer.wte.weight
    V = W.shape[0]
    kdir = kdir.to(DEVICE).float()
    mask = torch.full((V,), float("inf"), device=DEVICE)
    mask[torch.tensor(allowed, device=DEVICE)] = 0.0
    allowed_t = torch.tensor(allowed)
    results = []
    for r in range(restarts):
        ids = allowed_t[torch.randint(len(allowed), (length,), generator=g)].to(DEVICE)
        best_score = _score_ids(model, layer, ids[None], kdir)[0].item()
        for _ in range(steps):
            onehot = torch.zeros(length, V, device=DEVICE)
            onehot[torch.arange(length), ids] = 1.0
            onehot.requires_grad_(True)
            with torch.enable_grad():
                k = _keys_from_embeds(model, layer, (onehot @ W)[None])[0]
                loss = -(k @ kdir).abs() / k.norm()
                loss.backward()
            grad = onehot.grad + mask  # disallowed tokens never proposed
            top = (-grad).topk(topk, dim=1).indices  # (length, topk)
            pos = torch.randint(length, (n_cand,), generator=g).to(DEVICE)
            choice = torch.randint(topk, (n_cand,), generator=g).to(DEVICE)
            cand = ids[None].repeat(n_cand, 1)
            cand[torch.arange(n_cand), pos] = top[pos, choice]
            sc = _score_ids(model, layer, cand, kdir)
            j = sc.argmax().item()
            if sc[j].item() > best_score:
                best_score, ids = sc[j].item(), cand[j].clone()
        results.append((tok.decode(ids.tolist()), best_score))
    results.sort(key=lambda x: -x[1])
    return results
