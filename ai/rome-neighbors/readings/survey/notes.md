# Survey — Editing Large Language Models: Problems, Methods, and Opportunities

**Paper:** Yao et al. — EMNLP 2023
**arXiv:** https://arxiv.org/abs/2305.13172

## What it covers

Taxonomy of model editing approaches across three axes:
1. **Where** is the edit applied? (weights, activations, external memory)
2. **What** is the edit target? (a fact, a behavior, a skill)
3. **How** is success measured? (efficacy, specificity, generalization, portability)

## The four desiderata for editing

| Property | Meaning |
|----------|---------|
| **Reliability** | The edited fact is now correct |
| **Generality** | Paraphrases of the edit also work |
| **Locality** | Unrelated facts unchanged |
| **Portability** | Neighbor/downstream facts also update |

**Portability is the hardest.** Almost no method achieves it.

## Methods taxonomy (high level)

- **Constrained fine-tuning**: fine-tune on the edit, add regularization to
  prevent catastrophic forgetting
- **Meta-learning (MEND, MALMEN)**: train a hypernetwork to produce weight
  updates given an edit
- **Locate-and-edit (ROME, MEMIT)**: causal tracing to find the site, then
  targeted weight update
- **Memory-based (GRACE, WISE, IKE)**: external retrieval, no weight change

## What's missing (the open problem)

No method has a principled account of **what a "complete" edit is**. An edit
to F = (S, R, O*) is complete if and only if all facts logically entailed by F
are also consistent with O*. This requires:
1. A formal model of entailment (what counts as a neighbor?)
2. A propagation mechanism (how to update all entailed facts)
3. A consistency check (verify no contradiction introduced)

This is precisely what AGM belief revision provides at the logical level.
The connection to our knowledge graph work: the KG + AGM framework IS the
formal model of entailment that model editing lacks.

---

_Notes written: [date]_
