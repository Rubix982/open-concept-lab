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

## [R-003] Finding: KnowledgeSmith never tested out-degree, and a binding instruction said it had

_Date: 2026-11-09 · runs the gate T-002 was waiting on · read from the body and appendices, not the abstract_

**Luo, Zhou, Chen, Qiu, Savvides, Li & Wang, *KnowledgeSmith: Uncovering Knowledge Updating in LLMs with Model Editing and Unlearning*, arXiv 2510.02392, ICLR 2026.**

T-002 asks whether subject-string frequency predicts damage better than dependent count. Its gate said to read this paper first because it *"already tested the out-degree hypothesis"*, so the thread would only be interesting where it departed. **The gate was wrong and the thread is wider than before, not narrower.**

**What the paper does not contain.** "out-degree", "outdegree", "branching factor", "degree" and "fan-out" appear **nowhere**. Neither does "frequency" as a variable. What it varies is a node's **level in a hierarchy** — root, intermediate, leaf — plus training-data scale, model size and subject.

**What it does contain, quotable.** §5.2.1: *"editing tends to over-spread, unintentionally altering related nodes"*, against unlearning which *"often under-spreads"*. On structure: *"different hierarchical branches exhibit distinct ceilings for achievable accuracy"*, root lowest and leaf highest. On the trade-off: *"consistency collapses once data scale surpasses the model capacity"* — where consistency is *"the model's ability to maintain logical coherence across related knowledge after an intervention"*, and capacity is never formally defined. Their CCR and RR are defined in Appendix B over structurally related probes: CCR is the mean distance between pre- and post-intervention output distributions, RR the fraction of related probes whose answer is unchanged.

**Why the confusion is substantive rather than verbal.** Depth in a tree and number of dependents are different variables. A leaf has depth and no dependents; a root may have many. A result about hierarchy level says nothing about how damage scales with how many facts rest on the edited one — which is T-002's actual question.

**The consequence, and it is the part worth recording.** `ai/edit-slice/CLAUDE.md` carried this as a binding instruction, ending *"Do not re-derive this."* It therefore closed a question nobody had answered. A wrong citation misstates a sentence; a wrong instruction **stops work**, and leaves no evidence it was wrong — the same asymmetry the positioning rule names for scoop verdicts. Corrected in place there, in `threads.md`, in `plan.md` and on the notebook page.

**Scope of this reading.** The arXiv HTML is 171,731 characters and was read in two passes covering the body and the appendices available there; the terms above were absent from both. If the published ICLR version differs, this finding is about the arXiv v3 of 25 March 2026.

Confidence: **high** on the absent terms and on the quoted sentences. **Medium** that no appendix anywhere reports a degree statistic in passing, since the page truncates.

## [R-004] Finding: one requirement, two instruments — and this project already has both

_Date: 2026-11-09 · answers T-003 · synthesised from our own record, no new work and no new reading_

T-003 asked whether *modify internal mechanisms* and *extract latent knowledge* bottom out in one instrument or two, and whether this project's screen serves both or only the first. **Two instruments. Both exist here. Neither can do the other's job, and the reason is structural rather than practical.**

**The shared requirement is real.** Both need a way to tell what the model holds that is independent of what the asker put in. Modify needs it to know what it broke; extract needs it to know the answer was not planted.

**The modify instrument is the coefficient.** `c(k) = (k*·k)/(k*·k*)` reports whether a prompt's key resembles the edit's key — which, as [E-004] established, amounts to reporting whether the prompt **names the edited subject**. It says which items receive the update. It does not say how hard: C-001 denied that, and [E-015] showed the only universal upper bound is vacuous in the far field.

**The extract instrument is the possession filter**, and it was built before this question was asked. `edit-slice/src/possession.py` requires two things of an item: the true answer ranks first among N type-matched candidates, **and** it ranks higher with the real subject than with the subject replaced by a placeholder. That second arm *is* the independence requirement — **a model riding the template's base rate earns nothing**. It reports 56 / 74 / 79 / 85% possession at 6B / 8B / 70B / 405B, and GPT-J holding 13% of P19 birthplace.

**Why neither substitutes for the other.** The coefficient is defined relative to `k*`, an edit's key, so **it cannot be computed where no edit exists** — which is exactly the extract case. The possession filter needs no edit and is a property of the unedited model, so it says nothing about what an edit would break. The two are not two views of one quantity; one presupposes an intervention and the other presupposes its absence.

**The ordering is the part worth keeping.** They are not parallel. The possession filter is a **prerequisite** of the coefficient screen: `edit-slice/CLAUDE.md` makes possession a construct requirement — a model that never held the grounds cannot orphan them — so the extract-side instrument has to run first for the modify-side result to mean anything. That is a dependency, not a symmetry, and it is the answer to "one instrument or two" in the only form that changes what anyone does.

**One thing this does not establish, and it must not travel.** The thread cites *Open Problems* §3.2.2 and §3.5. **That document is not in `web/data/papers.yml` and has not been verified here.** The answer above rests on our own record and needs no section numbers; those references must not appear in anything public until the paper is identified and read. Flagged rather than quietly dropped, because a section number reads as a checked citation.

Confidence: **high** on the two instruments and on the dependency between them — both are in this repo and both have numbers. **Unassessed** on whether the sections cited actually frame the problem that way, which is the unverified part.
