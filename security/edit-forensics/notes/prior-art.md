# Prior art: forensics for locate-and-edit tampering

_Compiled 2026-10-25. Sources are abstracts and arXiv HTML read with a summarizing fetch tool, not full close reading. Numbers are the authors' own._

## 1. Detecting edits and recovering edited facts

- **Youssef et al., "Has this Fact been Edited?" (DEED)**, NAACL 2025, arXiv 2405.02765. Classifies a given (s, r, o) as edited or not from hidden states and output probabilities, using AdaBoost. Needs no base model, but you must already have the candidate fact. Does not recover anything from weights. Tested on ROME and MEMIT plus two meta-learning editors, GPT-J and GPT2-XL.
- **Youssef et al., "Tracing and Reversing Edits in LLMs" (EditScope)**, ICLR 2026, arXiv 2505.20819. **Closest to (a) and (c).** Works on edited weights alone:
  - finds the edited layer from row-vector similarity (App. C); this works on GPT models but **not on LLaMA3**;
  - predicts the **relation** with PCA plus logistic regression;
  - recovers the **object** (up to 99%) by optimizing other layers so the model emits the object from 5 random tokens. This does not read the object directly off the diff;
  - reverses edits with a bottom-rank SVD.
  - **Does not recover the subject.** Main results are ROME and r-ROME on GPT2-XL, GPT-J, LLaMA3-8B and Qwen2.5-7B. MEMIT and AlphaEdit appear in an appendix, where tracing on AlphaEdit falls to about 2–3%. No noise-masking or adaptive attacker.
- **Sun et al., "Reverse-Engineering Model Editing on Language Models" (KSTER)**, ICML 2026, arXiv 2602.10134 (cs.CR). **Closest to (b).**
  - Recovers the subject by spectral analysis of ΔW·C (row-space "fingerprint"); white-box subject recall is 0.94–1.00.
  - Recovers the prompt by entropy ranking against the pre-edit model.
  - Covers ROME, MEMIT and AlphaEdit, batch sizes 10–100, on GPT-J, Llama3-8B and Qwen2.5-7B. No GPT-2.
  - **Needs pre- and post-edit weights**, the covariance C, and a **closed candidate pool** (scaled up to 10^7 names). This is ranking, not open-vocabulary decoding.
  - Its framing is privacy: it exposes the *original* fact, and I saw no step that recovers the *planted* object.
  - It proposes a defense, "subspace camouflage" (decoy keys), which is in effect an evasive editor. The mean true-subject rank rises from about 51 to about 394 on MEMIT. It is evaluated only against the authors' own attack. Weight noise and multi-layer spread are not tested.
- **Holmov, Youssef et al., "One Mask to Rule Them All"**, Findings ACL 2026, arXiv 2605.28839. A binary mask over ROME and MEMIT weights reverses 70–80% of edits. Detection is suggested, not tested.
- **Jiang et al., "Selective Knowledge Edit Reversal via Gated Singular Vector Shrinkage"**, EMNLP Findings 2026, arXiv 2609.02091. Spectral, selective reversal. Does not recover subject or object.
- **arXiv 2609.18985, "Suppressed, Not Erased"** (2026). The original object stays decodable even after GRACE. Seen only in search results; not verified.

## 2. Editing as an attack vector

- **PoisonGPT** (Mithril Security blog, July 2023). ROME on GPT-J-6B, uploaded to HF under the typosquat name "EleuterAI". Not a paper.
- **BadEdit** (Li et al., ICLR 2024, arXiv 2403.13355). Backdoors via editing from about 15 samples; survives clean fine-tuning. I found no detector built for it.
- **"Can Editing LLMs Inject Harm?"** (Chen et al., arXiv 2407.20224; AAAI 2026 per a notes site). Misinformation and bias injection; edited models are hard to tell apart on capability benchmarks.
- **Youssef et al., "Position: Editing LLMs Poses Serious Safety Risks"**, arXiv 2502.02958. Argues that edit detection is still weak in practice.
- **Sutton et al., "Stealth edits"**, NeurIPS 2024. Trigger-specific edits; relevant to evasion.
- **Synacktiv, "LLM Poisoning [1/3]"** (blog, 2025-10-08). Detects trigger directions from activations; later parts build a ROME/MEMIT/AlphaEdit poisoning tool. Not a forensics method.
- Defenses: besides DEED, KSTER's camouflage (which protects editors, not victims) and generic backdoor pruning (e.g. arXiv 2607.19894, not checked against edits), I found no dedicated defense.

## 3. Wider weight-diff and provenance work

- **Minder, Dumas et al., "Narrow Finetuning Leaves Clearly Readable Traces in Activation Differences"**, ICLR 2026, arXiv 2510.13900. Base-vs-finetune activation diffs on random text reveal fine-tuning content. Needs the base model; covers fine-tuning, not rank-one edits.
- Provenance and fingerprinting: **HuRef** (arXiv 2312.04828, NeurIPS 2024), **REEF** (arXiv 2410.14273), **AWM** (arXiv 2510.06738, ICLR 2026), **TokenPrint** (arXiv 2608.08139). These answer "is this derived from X?". None localizes or decodes a single planted fact.

## 4. Closest papers: what each one covers

| Paper | Subject from diff | Object from diff | Base-free | Evasive attackers |
|---|---|---|---|---|
| EditScope 2505.20819 | no | yes, by optimization | yes (localization weak on LLaMA3) | no |
| KSTER 2602.10134 | yes, closed pool | no (original output via pre-edit model) | no | own camouflage defense only |
| DEED 2405.02765 | n/a | n/a | yes, but fact must be given | no |

## Verdict

- **(a) Localize the layer:** done. EditScope does it base-free on GPT models; with a base model, ΔW makes it trivial. Small novelty, except for MEMIT across several layers.
- **(b) Subject from the key direction:** done by KSTER with the base model, C and a closed pool. **Still open:** base-free, open-vocabulary subject decoding.
- **(c) Read back the planted object:** done by EditScope (optimization). **Still open:** a direct readout from v / ΔW, plus a full subject+object recovery in one pipeline, on GPT-2.
- **(d) Base-free detection under evasion:** **largely open.** Nobody tests weight-noise masking, MEMIT-style multi-layer spread used as evasion, or attackers who adapt to a known detector. KSTER's camouflage is the only evasion-like result.
- **Scoop risk: high.** The Youssef/Seifert group (DEED → EditScope → Mask) and the Sun/He group (KSTER) are both active in 2026. A full end-to-end "triple recovery plus robustness" paper is a natural next step for either group. The new contribution has to be (d) plus base-free (b).

**Unverified:** "Li et al. 2024b", the malicious-edit-type classifier cited by DEED (ID not found); the details of 2609.18985; whether EditScope's full appendix adds a subject probe (the last 22k characters were not read).
