"""Did an edit take hold? Compare first-token probs of new vs true object."""
import torch
from common import DEVICE


@torch.no_grad()
def target_probs(model, tok, prompt, targets):
    enc = tok(prompt, return_tensors="pt").to(DEVICE)
    p = torch.softmax(model(**enc).logits[0, -1].float(), -1)
    return [p[tok(" " + t)["input_ids"][0]].item() for t in targets]


def edit_success(model, tok, fact):
    rw = fact["requested_rewrite"]
    pr = rw["prompt"].format(rw["subject"])
    pn, pt = target_probs(model, tok, pr, [rw["target_new"]["str"], rw["target_true"]["str"]])
    return {"p_new": pn, "p_true": pt, "success": pn > pt}
