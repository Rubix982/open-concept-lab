# Prior art: does the internal refusal signal weaken turn by turn before compliance?

_Compiled 2026-10-25. Abstract/HTML reads only; nothing re-run. Items marked [unverified] come from memory or snippets only._

## 1. Activation-level work across turns / across a jailbreak

| Paper | One-line finding | Answers the question? |
|---|---|---|
| **SafeDream: Safety World Model for Proactive Early Jailbreak Detection**, Yan, Lin, Zhu, Wang, arXiv 2604.16824 (Apr 2026) | Reads Qwen2.5-7B-Instruct layer-19 hidden states each turn, projects them onto a 5-dim refusal concept cone (Wollschläger et al.), learns a latent "world model" + CUSUM, and alarms **1.06-1.20 turns before compliance** (AUROC ~0.91) on XGuard-Train, SafeDialBench and SafeMTData. Beats WildGuard/GuardReasoner/Circuit Breaker/TARS on lead time. Removing the cone drops lead time 1.11 to 0.33. | **Mostly yes, as an engineered detector.** It does not report the raw k=1 Arditi direction alone, has no training-free threshold baseline, tests one model, and does not use MHJ/human jailbreaks. |
| **A Representation Engineering Perspective on the Effectiveness of Multi-Turn Jailbreaks**, Bullwinkel, Russinovich et al. (Microsoft), arXiv 2507.02956 (Jun 2025) | MLP probes on Llama-3-8B-Instruct (layer 31) and the circuit-breaker model (layer 20) classify the final Crescendo response as more benign the more prior turns are included. | Partly. Measures how context length changes the *final* response representation, not a per-turn trajectory. 5 manually analysed attacks. No refusal direction. |
| **Latent Adversarial Detection: Adaptive Probing of LLM Activations for Multi-Turn Attack Detection**, Kulkarni, arXiv 2604.28129 (Apr 2026) | Residual-stream trajectory features ("path length") detect multi-turn attacks; 89.4% detection at 2.4% FPR; 4 families 24B-70B. | No. Geometry of the trajectory, not refusal-signal decay; no lead-time vs output comparison reported (abstract). |
| **PsychoPass: Geometric Profiling of Multi-Turn Adversarial LLM Conversations**, Ozmen, Majumdar, arXiv 2606.03136 (Jun 2026) | Trajectory geometry in embedding space predicts attack outcome from short prefixes after controlling for turn count. | No. Unclear whether internal activations; no refusal direction. Its turn-count confound is a warning for any study here. |
| **Mitigating Many-shot Jailbreak Attacks with One Single Demonstration**, Chen et al., arXiv 2605.08277 (May 2026) | Reports "progressive activation drift" of a harmful query away from the safety region as shots are added. | Partly, for many-shot; region-based, not the refusal direction. |
| **LLMs Encode Harmfulness and Refusal Separately**, Zhao, Huang, Wu, Bau, Shi, arXiv 2507.11878, NeurIPS 2025 | Harmfulness and refusal are separate directions; harmfulness is more robust under jailbreaks; "Latent Guard" released. | Single-turn. Supplies the key split for a multi-turn study. |
| **HARC**, Chua et al. (Microsoft), arXiv 2607.00572 (Jul 2026) | Jailbreaks suppress the refusal direction during prompt encoding (DAN, PAIR, CodeAttack); Llama-3.1-8B, Qwen-2.5-7B. | No. Single-prompt; mentions Crescendo only in related work. |
| **What Features in Prompts Jailbreak LLMs?**, arXiv 2411.03343, BlackboxNLP 2025 | Linear probes predict single-turn jailbreak success (>80%), transfer poorly across attack families. | No (single-turn). |
| Kim & Lee, **Linearly Readable, Not Robust**, EMNLP 2026 Findings [unverified beyond snippet] | Jailbreak probes' 5% FPR becomes 68-98% on diverse traffic. | Caveat for any probe-based detector. |

Circuit breakers (Zou et al. 2024), JBShield, Gradient Cuff are single-turn; 2507.02956 shows circuit breakers fail under Crescendo.

## 2. Multi-turn attacks and datasets

| Source | Public? | Size / licence |
|---|---|---|
| Crescendo, Russinovich, Salem, Eldan, arXiv 2404.01833, USENIX Sec 2025 | Method in PyRIT; no released conversation set [unverified] | — |
| MHJ, Li et al., arXiv 2408.15221, NeurIPS 2024 workshop | HF `ScaleAI/mhj`, **gated** | 537 human conversations, 2,912 prompts; CC-BY-NC-4.0; **completions redacted** (user/system only); targets Llama-3-8B-Instruct + RR, LAT, DERTA, CYGNET |
| ActorAttack / SafeMTData, Ren et al., arXiv 2410.10700 | HF `SafeMTData/SafeMTData`, open | Attack_600 (600 attack paths from HarmBench) + SafeMTData_1K (1,680 refusal dialogues); MIT |
| X-Teaming / XGuard-Train, arXiv 2504.13203 (2025) | HF `marslabucla/XGuard-Train`, **gated** | 30,695 conversations, ~5.1 turns; harmful replies replaced by refusals; licence not stated |
| SafeDialBench, arXiv 2502.11090 | Academic use only; hosting not confirmed | >4,000 dialogues, zh+en |
| Many-shot, Anil et al., NeurIPS 2024 | No dataset released [unverified] | regenerate shots yourself |
| CoSafe, Yu et al., EMNLP 2024 Findings, arXiv 2406.17626 [unverified] | GitHub [unverified] | ~1,400 coreference multi-turn questions |

Note: XGuard-Train, SafeMTData_1K and MHJ do not contain the target model's compliant replies. You must re-run the user turns against your model and label compliance per turn yourself (SafeDream used a 2-of-3 vote of HarmBench classifier, GPT-4o, MD-Judge).

## 3. Internal states predicting success earlier than output filters

Only SafeDream measures this directly: ~1.1 turns of lead over output guardrails, one model. Nothing found that does it with the plain Arditi direction, across several models, or on human jailbreaks.

## Verdict

(a) Largely yes, as a trained detector: SafeDream (Apr 2026) shows a refusal-cone-based hidden-state signal alarms ~1.1 turns before output compliance. The plain "does the Arditi direction decay before compliance" curve is not published as such.
(b) Closest: SafeDream. Open: single model (Qwen2.5-7B); no k=1 / training-free baseline; no harmfulness-vs-refusal split; no human jailbreaks (MHJ); no causal test.
(c) Scoop risk high on "activation early warning for multi-turn"; moderate on the mechanistic descriptive question.
(d) SafeMTData Attack_600 (MIT, ungated) to start; MHJ (gated, human) as the stronger held-out test. Both need fresh responses.
(e) Llama-3-8B-Instruct and its circuit-breaker variant (2507.02956, MHJ); Qwen2.5-7B-Instruct (SafeDream); Llama-3.1-8B / Qwen-2.5-7B (HARC).
(f) Sharpen to: across turns, does the **refusal** projection fall while the **harmfulness** projection (Zhao et al.) stays high, and does a training-free threshold on that gap match SafeDream's lead time across 3+ models and on MHJ? Control for turn count (PsychoPass).
