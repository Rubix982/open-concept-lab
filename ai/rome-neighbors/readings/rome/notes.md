# ROME — Locating and Editing Factual Associations in GPT

**Paper:** Meng, Bau, Andonian, Belinkov — NeurIPS 2022
**arXiv:** https://arxiv.org/abs/2202.05262
**Code:** https://github.com/kmeng01/rome

## What it claims

1. Factual associations (subject → object) are stored in a specific MLP layer
   of a transformer — identifiable via causal tracing.
2. A rank-1 update to that layer's weight matrix can reliably change the stored fact.
3. The edit is specific: unrelated facts are not affected.

## Causal tracing protocol

Three runs per fact query:
- **Clean**: normal forward pass
- **Corrupted**: subject tokens noised at embedding
- **Corrupted + restored**: noised subject, but clean activation patched back
  at one (layer, token) position

The (layer, token) where restoration most recovers the clean answer = the
causal site. For GPT models: MLP output at the last subject token, mid-layers.

## The edit operation

Given subject h (hidden state at last subject token, target layer):
- Compute the "target" output v* that the MLP should produce
- Derive a rank-1 update: ΔW = (v* - W·h) · h^T / (h^T · h)
- Apply: W_new = W + ΔW

## What it does NOT do

- Does not update neighbor facts
- Does not update reverse lookups
- Measures only: efficacy (did O* replace O?), specificity (did unrelated facts change?)
- Does not measure: N1, N2, N3 ripple

## Key numbers (GPT-J-6B on CounterFact)

- Efficacy: ~99% (the edit works)
- Specificity: ~99% (unrelated facts unchanged)
- Paraphrase (N0): ~70% (rephrased versions of the same fact)
- Neighbors: not measured in the original paper

## Questions for our work

- Which layer in GPT-J-6B is the causal site for each triple?
- After the edit, does the residual stream at the edited layer change for
  neighbor queries?
- Is the neighbor failure an attention failure (not routing to the edited layer)
  or an MLP failure (layer updated but not read correctly)?

---

_Notes written: [date]_
