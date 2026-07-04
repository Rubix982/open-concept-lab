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
