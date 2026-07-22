# GRACE & WISE — Retrieval-Based Editing Approaches

## GRACE — General Retrieval Adaptors for Continual Editing

**Paper:** Hartvigsen et al. — NeurIPS 2023
**arXiv:** https://arxiv.org/abs/2211.11031

### What it does

Instead of modifying weights, GRACE maintains a **codebook** of (key, value)
pairs. At inference time, if the input is close to a stored key, the model's
hidden state is replaced with the stored value.

- No weight modification — original model untouched
- Edits are stored externally and retrieved by similarity

### Implication for neighbors

Since the intervention is input-similarity-based, it only fires when the
query is close to the stored edit key. A neighbor query phrased differently
will NOT retrieve the edit — same fundamental problem as ROME, different
mechanism.

---

## WISE — Editing via Side Memory

**Paper:** Wang et al. — 2024
**arXiv:** https://arxiv.org/abs/2405.14768

### What it does

Maintains a "side" transformer that intercepts queries relevant to edited
facts and overrides the main model's output. Uses a reliability classifier
to decide when to defer to the side memory.

### Implication for neighbors

Same limitation: the side memory fires on queries that match the edit scope.
Multi-hop neighbor queries may not be recognized as in-scope.

---

## The contrast with weight-editing (ROME/MEMIT)

| Method | Edit mechanism | Neighbor propagation |
|--------|---------------|----------------------|
| ROME | Rank-1 weight update | Fails at N2+ |
| MEMIT | Distributed weight update | Fails at N2+ |
| GRACE | Codebook retrieval | Fails at N2+ (different path) |
| WISE | Side memory | Fails at N2+ (scope detection fails) |

The neighbor problem is **not** specific to weight-editing. It is fundamental
to all current methods — no method has a principled mechanism for propagation.

---

_Notes written: [date]_
