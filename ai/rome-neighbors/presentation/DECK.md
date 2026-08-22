# Does representational geometry predict edit propagation?

_Call with Natalie & Arnab · 2026-08-25 · Saif Ul Islam_
_A 15-min walkthrough. Numbers marked ⟨FILL⟩ get pasted in after the E-011 run._

---

## 1 · The problem (30s)

Knowledge editing (ROME/MEMIT) reliably changes the *target* fact — but the edit
fails to propagate to logically **entailed** facts. A ROME-edited GPT-J answers
only **7.6%** of MQuAKE-CF multi-hop questions vs 43.4% before. Editing today ≈ a
local rewrite, not a belief change.

**The question:** can we *predict, from the model's internal geometry*, whether an
edit will propagate to a given neighbour — before we commit the edit?

---

## 2 · The reframe (the honest starting point) (1m)

The naive hypothesis — "facts close in representation space co-update" — is what
the field already suspects is **wrong** (Nishi: distance→shattering; Kim/Jeong:
*structure*, not raw distance). So I demote raw distance to a **baseline** and ask
which geometry actually predicts propagation:

| Predictor | Source | Role |
|-----------|--------|------|
| raw distance (cosine) | — | baseline |
| structured alignment | Jeong/STEAM | candidate |
| structured bilinear | Kim / Function Vectors | candidate (v1+) |

Resolved **across entailment hops** (1-hop / 2-hop / reverse), measured **causally**
(IIA) — the combination that (Asta ×3 + full NDIF corpus) appears **unclaimed**.

---

## 3 · The three-act arc (the result) (3m)

Real data: RippleEdits (`popular.json`), GPT-J-6B on NDIF, its six criteria →
our neighbour types. Representation = mean-pooled residual (avoids the last-token
attention sink).

- **ACT 1 — raw distance is flat.** Cosine ≈ 0.6 across paraphrase/1hop/2hop
  (spread 0.011); no hop-decay. Baseline is near-uninformative. `sep(raw) ≈ ⟨FILL⟩`.
- **ACT 2 — not just a position artifact.** Layer sweep (6/9/12/15/18), last-token
  vs mean-pool: `sep(raw)` stays ⟨FILL: ~0 / lifts⟩ → raw distance is
  ⟨genuinely weak / was a sink artifact⟩.
- **ACT 3 — structured alignment separates.** `sep(align) = ⟨FILL⟩` @ layer ⟨FILL⟩,
  vs `sep(raw) = ⟨FILL⟩`. ⟨Structure carries the signal distance missed / does not⟩.

**Figure:** `results/predictor_arc.png` (sep vs layer, both predictors).

---

## 4 · Where this sits (positioning) (1m)

- Nearest method: **SLAQ** (similarity predicts factual *consistency* ~78%) —
  different phenomenon (not edits), aggregate, no hops. Cite + differ.
- Kim / Jeong: aggregate, behavioural, **no causal metric, no hop breakdown**.
- Kim tested only on *synthetic* models → applying to pre-trained GPT-J is their
  own future work.
- **Novelty = the combination** (hop-resolved + causal + head-to-head), not the parts.

---

## 5 · The load-bearing next brick — E-010 (plan, for review) (2m)

Predictor separating types ≠ predictor of **propagation**. To close the thesis:

- **Outcome = causal IIA** per neighbour (interchange: patch the base's rep of the
  edited attribute, does the neighbour's answer flip?), built on `jkminder/nnpatch`.
- Then: does predictor (align/bilinear) correlate with per-neighbour IIA,
  **stratified by hop** — the headline figure (AUC per hop bin).

**This is where I most want your review before I build it.**

---

## 6 · Questions for you (the point of the call) (5m)

1. Is the lane genuinely open — anything in-flight I can't see? (Arnab)
2. **RAVEL vs RippleEdits** as the cleaner substrate for hop-resolved geometry?
3. Does the **IIA outcome design** (E-010) hold up, or is there a cleaner causal
   handle on "propagation"?
4. Biggest pitfall I'm walking into?

---

## Appendix · what's built

`ripplekit/` (reproducible package) · design.md (10-lens) · readings/MAP.md
(vetted lit) · this arc runs from one script (`experiments/preflight_demo/run.py`).
