# findings

## [R-001] Finding: a deterministic behavioural bound is not ruled out in principle — it is merely uncomputed

_Date: 2026-11-09 · answers T-011 · read from the paper's theory sections, not its abstract_

**Kim, Papamakarios & Mnih, *The Lipschitz Constant of Self-Attention*, arXiv 2006.04710, ICML 2021.**

Theorem 3.1: dot-product multihead self-attention "is not Lipschitz for any vector p-norm `‖·‖p` with `p ∈ [1, ∞]`". The mechanism is specific and worth stating, because it is what the qualification hangs on: when some input `x_i = 0` the attention weights in that row become uniform, and the Jacobian block `J_ii` then carries a term equal to the **sample variance** of the inputs, which can be made arbitrarily large. Adding query and key biases does not fix it (their Appendix D).

**But the paper says the compact case is Lipschitz, in its own words.** *"If the input space is compact … any continuously differentiable function is Lipschitz, including dot-product self-attention."* They decline that route not because it fails but because the constant *"depends on the range of the input"* and a tight bound *"would require non-trivial mathematical work"*; and because every layer's inputs would have to lie in the same compact set, which they say invites vanishing gradients.

**So the honest statement for our work is the opposite of what [T-001]'s dry-run wrote.** A deterministic behavioural upper bound through a transformer is **not** unavailable in principle. On a compact domain it exists. What is true is that **nobody has computed one**, and the authors of the paper that would be the starting point call that non-trivial. *"No usable constant exists"* is defensible; *"no constant exists"* is not, and had already been written down before this was read.

**Two scope limits on the result itself.** Their analysis is of the self-attention map on `ℝ^(N×D)`, not of a full transformer block as one object; block-level discussion is confined to invertible residual branches. And LayerNorm is Lipschitz (their Appendix N, unread here), so it is not the obstruction.

Confidence: **high** on what the paper says — read from the theory sections and quoted. **Low** on what the constant would be for our setting, which nobody has computed.

## [R-002] Finding: weight-space certification certifies a ball; nobody certifies a known direction, and nobody does it for a transformer

_Date: 2026-11-09 · answers T-012 · read from the problem formulation and Theorem 0.1, not the introduction_

**Weng, Zhao, Liu, Chen, Lin & Daniel, *Towards Certificated Model Robustness Against Weight Perturbations*, AAAI 2020.** The nearest prior art to bounding an edit's reach, and the comparison is favourable in a way a search result would not have shown.

Their threat model is an **ℓ∞ ball around the weights**:

    B(W, ε) = { Ŵ | ‖Ŵ⁽ᵏ⁾ − W⁽ᵏ⁾‖∞ ≤ ε, ∀k ∈ [K] }

Theorem 0.1 then gives analytic output bounds `f_j^L ≤ f_j ≤ f_j^U` under **single-layer** `ℓp` weight perturbation for `p ≥ 1`, by bound propagation. Single-layer is the ROME case, so the shape matches.

**Three things the paper does not do.**

1. **The direction is free.** The certificate is over every `Ŵ` in the ball, so its worst case ranges over all directions. A ROME edit moves along **one** direction, fixed, and known before the edit is applied, with only a scalar varying per input. Their bound applies to us and is loose by whatever the ball-versus-direction gap is.
2. **Rank-one never appears.** Zero occurrences of "rank-one", "rank one" or "low-rank" in the paper.
3. **No transformers and no language models.** Evaluated on multilayer perceptrons of 2, 4, 6, 8 and 10 layers over MNIST, Fashion-MNIST, SVHN and CIFAR-10.

**Positioning, at the strength the evidence supports and no further.** Weight-space certification is an existing field, so "nobody certifies weight perturbations" would have been false and is not claimed. What is **unclaimed in this setting** is certification exploiting a rank-one perturbation whose direction is known in advance, aimed at knowledge-editing locality in a transformer. A search for provable locality bounds for ROME returned nothing, which is not evidence of absence and nothing is shelved on it.

Confidence: **high** on what Weng et al. do — read from the formulation and the theorem. **Medium** on the lane being unclaimed, because that rests partly on a search returning nothing.
