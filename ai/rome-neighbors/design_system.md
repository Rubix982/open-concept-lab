# Design — Edit-Reliability System (working name: **KEEP**)

_Knowledge-Edit Evaluation & Preservation. The reliability layer that wraps any
weight-editor and makes knowledge-editing trustworthy enough to deploy._

_Structured by the Research Design Protocol (10 lenses) + systems sections
(interfaces, failure modes/guarantees, baselines). v0.1 — iterate._

---

## 0 · One-paragraph statement

Existing editors (ROME, MEMIT, FT) change a target fact but silently corrupt the
model's *other* knowledge and fail to update logically-entailed facts — measured
today: naive FT breaks 94% of unrelated facts; ROME still leaks ~60%; 1-hop
consequences break more often than 2-hop; edits over-propagate the wrong value-type
(a target *city* injected into a *country* slot). No current method **predicts**,
**detects**, or **repairs** this. KEEP is a system that wraps any editor and adds
that missing reliability loop: **predict** which neighbours an edit will break →
**edit** → **evaluate** the neighbourhood → **repair** the damage → **certify** the
result. ROME/MEMIT are swappable *components* inside it, not the contribution. The
contribution is the reliability layer, and its novel core is the breakage-predictor
and the repair strategy.

---

## WHY — is it worth doing?

### 1. Significance
- **The deployment gap is real and measured.** An edit that corrupts 60–94% of
  neighbouring facts cannot be used in any domain where correctness matters. This
  is the single barrier between knowledge-editing (a live research area, 110+ NDIF
  papers) and real use.
- **The flagship need:** a model kept current with fast-moving knowledge — e.g. a
  **medical model** updated with new trial results / revised guidelines — where a
  silent collateral corruption is unacceptable. Retraining is too slow/expensive;
  RAG can't change what the model *believes* or reach implicit/reasoning uses.
- **What changes on each outcome:**
  - KEEP works → editing becomes *deployable*: cheap, frequent, auditable knowledge
    maintenance with a correctness guarantee. A real product category.
  - KEEP's predictor fails → we learn breakage is *not* forecastable from internal
    structure → editing stays a research toy for high-stakes domains; redirect to
    retraining/RAG. Still a valuable, publishable negative for the field.
- Rigor here is not wasted: both answers move the field and inform real decisions.

### 2. Prior art & positioning
- **Editors** (ROME, MEMIT, MEND, AlphaEdit, PMET) — *produce* edits; they optimise
  efficacy + a locality *term*, but don't predict/detect/repair neighbour breakage
  at inference of the edit. We use them as components. We do NOT compete on the
  edit algorithm (SOTA-saturated; not our edge).
- **Benchmarks** (RippleEdits, MQuAKE) — *evaluate* ripple failure post-hoc,
  aggregate, offline. They diagnose the disease; they don't predict per-edit or
  repair. KEEP turns their evaluation into an *online, per-edit, actionable* loop.
- **Geometry/consistency** (Nishi shattering, Kim bilinear, Jeong/STEAM, SLAQ) —
  study *why* propagation happens, mostly as one-off analyses, not a wrapping system
  with prediction + repair. Closest to our predictor's science; cite + differentiate.
- **Positioning in one sentence:** everyone builds better *editors* or better
  *benchmarks*; nobody builds the *reliability system* that sits between them and
  makes an edit safe to ship — with a predictor and a repair loop.
- **Scoop risk:** low on the *system* framing (infra-shaped, under-built); moderate
  on the *predictor* science (Kim/Jeong active). Our edge = the assembled system +
  the repair step, which is unclaimed. Confirm with Arnab.

---

## WHAT — what exactly is the claim?

### 3. The claim / contribution
KEEP demonstrates that (a) neighbour breakage from an edit is **predictable** from
the model's internal structure before/at edit time, and (b) predicted breakage is
**repairable** to a measurable degree, yielding an edit that preserves model
structure — packaged as an editor-agnostic system with a correctness certificate.

### 4. Completeness (the question family)
For the claim to be *believed*, KEEP must answer:
- Q1 **Detect**: can we reliably classify each neighbour post-edit as
  updated/stale/broken/fine? (largely built — the 3-way evaluator)
- Q2 **Predict**: can we forecast that class *before* committing the edit, from
  internal structure? (the hard, novel core; today's raw-distance baseline is weak)
- Q3 **Repair**: given a broken/stale neighbour, can we fix it (cascade-edit /
  targeted correction / rollback) without new collateral damage?
- Q4 **Certify**: can we emit a trustworthy consistency guarantee + its confidence?
- Q5 **Generality**: does it hold across editors (ROME/MEMIT/FT), models, and
  domains (the medical case)?
One box working is a demo; the family is the system.

### 5. Falsification (stated in advance)
- **Confirm**: predictor beats baselines at forecasting breakage (per hop), and
  repair raises the net "fine+updated" rate meaningfully over raw editing, without
  net-new breakage.
- **Deny (predictor)**: no internal signal forecasts breakage better than trivial
  baselines (hop-count) → the predictor box is empty → KEEP reduces to detect+repair
  only (still useful, weaker claim).
- **Deny (repair)**: every repair introduces as much new breakage as it fixes
  (whack-a-mole) → editing is fundamentally non-local; KEEP certifies "unsafe" and
  the honest conclusion is "don't edit, retrain" for this domain.
- **Null**: edits rarely break anything on the chosen setting → move to a harder
  setting (bigger model, multi-hop, sequential edits) where breakage is real.

---

## HOW — architecture & method

### 6. Architecture (components + contracts)
Pipeline, each box an interface so components are swappable and independently testable:

```
edit_request ─▶ [1 PREDICT] ─▶ risk_report
                    │
             (proceed/abort/route)
                    ▼
              [2 EDIT] ──▶ edited_model         (ROME | MEMIT | FT — pluggable)
                    ▼
              [3 EVALUATE] ──▶ neighbour_outcomes (updated/stale/broken/fine)
                    ▼
              [4 REPAIR] ──▶ edited_model'        (cascade / correct / rollback)
                    ▼
              [5 CERTIFY] ──▶ consistency_certificate
```

Interfaces (buildable-by-a-second-engineer contracts):
- **EditRequest**: `{subject, relation, target_old, target_new, cloze}`
- **NeighbourSet**: `[{type, prompt, expected_old, expected_new, subject_shared}]`
  (from RippleEdits, or generated per T-B/counterfactual_gen)
- **1 Predict** `predict(model, EditRequest, NeighbourSet) → [{neighbour, p_break, p_stale, features}]`
- **2 Edit** `edit(model, EditRequest) → edited_model` (adapter over EasyEdit ROME/MEMIT/FT)
- **3 Evaluate** `evaluate(edited_model, base_model, NeighbourSet) → [{neighbour, outcome}]`
  (built: rome_study.py 3-way; needs the pre-unknown-fact refinement)
- **4 Repair** `repair(edited_model, broken_neighbours) → edited_model'` (v2 core)
- **5 Certify** `certify(outcomes) → {score, per-type rates, pass/fail, confidence}`

The **novel science** lives in boxes **1 (Predict)** and **4 (Repair)**. Boxes 2,3,5
are engineering (real, valuable, but not the contribution).

### 6a. Method — the Predictor (box 1)
- Independent variables (features per neighbour): hop distance; representational
  proximity (raw cosine — baseline, weak); **structured geometry** (Kim bilinear /
  edit-difference vector); **subject-sharing** (exact via subject_id); **causal
  routing** (does the neighbour read the edited MLP site — interchange/attention
  knockout); pre-edit competence.
- Dependent variable: the 3-way outcome (from box 3, ground truth).
- Model: logistic / multinomial predicting outcome from features; report AUC per
  hop, feature importances.
- **Construct validity**: today's finding — raw last-token cosine is template-
  saturated (~0.998, AUC 0.68). Predictor must use fact-specific reps (subject
  token, edit-difference), not whole-prompt cosine. Measuring the wrong rep precisely
  is still wrong.

### 6b. Method — Repair (box 4) — the hardest, most novel box
Candidate strategies, in increasing ambition:
- **Rollback**: if certify fails, revert the edit (trivial safety floor).
- **Cascade-edit**: for each *stale* entailed neighbour, issue a follow-up edit for
  it (edit the country too). Risk: compounding collateral damage (must re-certify).
- **Targeted correction**: for *broken* neighbours (esp. target-bleed), a corrective
  update that restores the original value. Risk: undoing the intended edit.
- Open question: is there a repair that monotonically increases fine+updated without
  net-new breakage? If not (deny-repair branch), that's itself the finding.

### 7. Confounds & controls
| Confound | Control |
|----------|---------|
| Pre-edit unknown facts mislabelled "broken" (seen today: "P"→"P") | competence filter: exclude neighbours the model can't answer pre-edit |
| Over-propagation vs incoherent-broken conflated | split "broken" into {wrong-granularity, target-bleed, incoherent} in evaluate |
| Editor choice drives results | run across ROME/MEMIT/FT (Q5) |
| Model capacity (gpt2-small weak) | scale to gpt2-xl/GPT-J on GPU; report per-model |
| Predictor leakage (using post-edit info to "predict") | predictor uses only pre-edit / edit-time info |

### 7a. Baselines the system must beat
- Predictor vs **hop-count alone** and **raw cosine** (partial correlation / AUC).
- Repair vs **rollback-only** and **do-nothing** (net fine+updated rate).
- Whole system vs **raw ROME/MEMIT** (the deployment metric: consistent-edit rate).

---

## HOW MUCH — scope & feasibility

### 8. Scope
- **v1 (IN):** boxes 1–3+5 on gpt2/gpt2-xl, ROME + FT components, RippleEdits/
  controlled neighbours; predictor = geometry + subject-sharing + causal-routing;
  the headline "predictor beats baselines" number + the certified consistency rate.
  Repair (box 4) = rollback + one cascade strategy (proof of concept).
- **v2 (DEFERRED):** full repair strategies; MEMIT/AlphaEdit components; multi-hop
  (MQuAKE); sequential editing; the medical-domain demo; a real serving wrapper.
- **Feasibility (today's evidence):** editing is local + CPU-heavy; gpt2-small runs
  on Mac but is weak and gpt2-medium NaNs here → **v1 wants a GPU** (Colab/cloud) for
  gpt2-xl/GPT-J. Covariance stats compute once (cached). The evaluate/predict loop
  is cheap. Main cost = the edit × neighbour × edits sweep → GPU makes it tractable.

---

## CHECK — would it survive contact?

### 9. Deliverable (design backward from this)
- **Headline number:** *consistent-edit rate* — fraction of edits where all entailed
  neighbours update AND all locality stays fine — **raw ROME vs KEEP** (predict+repair).
  If KEEP raises it materially, the system's value is proven in one number.
- **Secondary:** predictor AUC-per-hop (science core); the 3-way blast-radius figure;
  feature importances (what makes a neighbour break — the T-015 answer).

### 10. Failure modes & guarantees (systems section)
- KEEP **never silently ships** a corrupting edit: worst case it certifies "unsafe"
  and rolls back (safety floor = do no harm).
- Guarantee is **probabilistic + scoped**: "on the evaluated neighbour set, structure
  preserved at rate X, confidence C" — not a proof. State this honestly; over-claiming
  a guarantee is the fastest way to lose a reviewer.
- Degrades gracefully: no predictor → still detect+repair+certify; no repair → still
  predict+abort.

### 11. Adversary (pre-empt the reviewer)
- "You just wrapped ROME." → No — the contribution is the predictor + repair; ROME is
  a swappable baseline component; the deliverable is the consistent-edit-rate lift.
- "Predictor is no better than hop-count." → baseline-beating is the pre-registered
  bar (lens 5); if it fails, we report the honest negative.
- "Repair is whack-a-mole." → measured net breakage; if true, that's a finding, and
  the safety floor (rollback) still holds.
- "gpt2-small toy." → scale to gpt2-xl/GPT-J; per-model reporting.
- "Guarantee isn't real." → explicitly probabilistic + scoped (§10).
- "Evaluation is circular (predict using outcome)." → strict pre-edit feature firewall.

---

## Open questions → Arnab / Natalie
1. Is the *system + repair* framing genuinely unclaimed, or is someone building it?
2. Does the predictor need causal-routing (interchange) or is structured-geometry enough?
3. What's the right consistent-edit-rate benchmark to be comparable (RippleEdits? MQuAKE)?
4. Repair: is there prior work on cascade/corrective editing we should build on?
5. Compute substrate for v1 (GPU) — what do you recommend?

## Relation to prior threads
Subsumes T-015 (the 3-way is box 3), T-B (the predictor is box 1), T-006 (predictor's
science = does the causal-read graph mirror the entailment graph). The system is the
vehicle; those threads are its components.
