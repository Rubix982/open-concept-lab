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

## 3 · The three-act arc (honest results) (3m)

Data: RippleEdits (`popular.json`), six criteria → neighbour types.
**Infra note:** NDIF regressed mid-work (post-outage whitelist bug, reported to
your Discord) → I built a **local transformers backend** and ran on **gpt2-medium**
as a stand-in. `sep = mean(propagate types) − locality` (>0 = predictor informative).

- **ACT 1 — raw distance is a weak baseline.** *Mean-pool:* cosine ≈ 0.99 for
  EVERY type incl. locality → `sep ≈ 0`. Template-dominated washout (holds on
  gpt2-small too).
- **ACT 2 — readout matters.** *Last-token* recovers a faint, layer-increasing
  signal in the right direction: `sep(raw)` +0.007→**+0.019** (L12→L18),
  propagate-types above locality. So mean-pool was hiding it; last-token at late
  layers is the better readout.
- **ACT 3 — structured alignment does NOT win (yet).** `sep(align) ≈ 0` on
  gpt2-medium — our Jeong-style anchor predictor doesn't beat raw distance here.
  Honest weak/negative result (design.md pre-stated this "deny" branch).

**Capacity cross-check:** GPT-J last-token (E-007, before NDIF broke) gave
`sep ≈ +0.06` — **3× gpt2-medium's +0.019**. Both capacity and readout push in
the expected direction → the real test wants GPT-J + a causal outcome, not
prompt-geometry on a small model.

**Figures:** `results/gpt2med_last_arc.png`, `results/by_type.png`.

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

Predictor separating types ≠ predictor of **propagation**. To close the thesis I
need a per-neighbour causal propagation label — and there's a fork I want your
call on (full plan: `experiments/iia_outcome/PLAN.md`):

- **Option A — actual edit** (ROME/MEMIT via EasyEdit): real, but needs local
  weights (NDIF is inference-only).
- **Option B — interchange/IIA** (`nnpatch`, NDIF-doable): patch the edited
  attribute's rep counterfactual→base, does the neighbour's answer flip? Clean,
  but a *proxy* for editing.

**The question for you (Arnab):** is interchange-IIA a defensible proxy for edit
propagation, or does the claim require actual ROME edits? Then: predictor vs.
per-neighbour propagation, **AUC per hop bin** = the headline figure.
Controls already specified: pre-edit competence filter + edit-success filter +
beat hop-count/raw-distance baselines.

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
