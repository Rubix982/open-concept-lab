# Shared Findings

_Owned by: Researcher. Append-only._

## [E-001] Finding: OID Co-location Probe — GPT-2 small, 20 stories, 5-fold CV

_Date: 2026-07-04_

**Object probe**: rises above chance (0.25) starting at layer 5, peaks at 0.800 (layers 6–11).
Object identity is linearly decodable from the residual stream at the state token
position in mid-to-late layers. This matches the lookback paper's prediction.

**Character probe**: stays near chance (0.05–0.15) through layers 0–10; reaches 0.30 at
layer 11 only. Character identity is NOT reliably encoded at the state token position
for most layers.

**Interpretation**: the state token encodes what object is there (recency: object token
appears 3–4 positions before the state token). Character identity, named 7–8 tokens
earlier, requires longer-range propagation and only begins to appear at the final layer.
This suggests the lookback mechanism may bind character identity at the character name
token positions — not at the state token — consistent with the binding lookback story.

**Action for E-002**: extract residuals at the CHARACTER NAME token positions (not state
token), probe for character identity there, and check if attention at the answer token
flows back to those positions.

Confidence: medium (n=20, 5 per class — above-chance obj result is robust; char result
needs more stories and character-position probing to confirm).

## [E-004] Finding: NNSight Intervention — Layer 6 ablation on Sally story

_Date: 2026-07-04_

**Read (no intervention):** GPT-2 small answers "She" / "\n" at top. 'basket' logit = -150.6.
GPT-2 is not a ToM model — it continues syntax, not answers.

**Full ablation of layer 6:** logit('basket') RISES to -99.7. Layer 6 is actively suppressing
location tokens in favour of pronoun/continuation tokens. Removing it relaxes suppression.

**Noise sweep:** σ < 0.1 negligible; σ = 1.0 shifts distribution slightly.

**Targeted ablation (state-token pos only):** 'Anne' appears in top-5 after zeroing.
The displaced character becomes more salient when state-position context is removed.

**NNSight shape discovery:** Single-item traces yield 2D activations `[seq_len, d_model]`.
Batch dim is squeezed. In-place multi-dim proxy assignment (`[:, 8, :] = 0`) fails — use
clone → mask → assign pattern. See memory `reference-nnsight` for pattern.

Confidence: high (deterministic runs, shape confirmed, pattern documented).
