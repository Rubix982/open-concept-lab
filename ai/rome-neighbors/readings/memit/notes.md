# MEMIT — Mass-Editing Memory in a Transformer

**Paper:** Meng, Sen Sharma, Bau et al. — ICLR 2023
**arXiv:** https://arxiv.org/abs/2210.07229
**Code:** https://github.com/kmeng01/memit

## What it adds over ROME

ROME edits one fact at a time by updating one MLP layer.
MEMIT scales to thousands of simultaneous edits by:
- Distributing updates across a *range* of MLP layers (not just one)
- Solving a constrained least-squares problem per layer to spread the load
- Preserving the model's existing knowledge better under many edits

## The key idea

ROME can overwrite existing weights destructively when many edits pile into
one layer. MEMIT spreads the "memory pressure" across layers 3–8 (for GPT-J),
so no single layer is overwhelmed.

## What it still does NOT do

- Still does not propagate to neighbors
- Evaluation metrics: efficacy, paraphrase score, specificity
- Neighbor ripple is not addressed

## Questions for our work

- Does spreading edits across more layers change the neighbor propagation
  picture? Does it help or hurt?
- If ROME's edit is localized to one MLP, MEMIT's is distributed — does
  the distributed version leave more "signal" for attention to route neighbor
  queries through?

---

_Notes written: [date]_
