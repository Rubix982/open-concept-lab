# Design — Parametric↔Retrieval Consistency Certifier (working name: **KEEP**)

_KEEP = the reliability layer for **hybrid** knowledge systems: when a model both
**edits** (parametric belief) and **retrieves** (RAG), KEEP detects when the two
stores contradict and **certifies** that an update leaves them consistent._

_Structured by the Research Design Protocol (10 lenses) + systems sections
(interfaces, failure modes/guarantees, baselines). v0.2 — rewritten 2026-08-24 for
Fork B (findings [T-018]). The v0.1 ripple-repair framing is archived in Appendix A._

- [0 · One-paragraph statement](#0--one-paragraph-statement)
- [0.5 · The category correction — read this first](#05--the-category-correction-2026-08-24--read-this-first)
- [WHY](#why--is-it-worth-doing) — [1. Significance](#1-significance) · [2. Prior art & positioning](#2-prior-art--positioning)
- [WHAT](#what--what-exactly-is-the-claim) — [3. Claim](#3-the-claim--contribution) · [4. Completeness](#4-completeness-the-question-family) · [5. Falsification](#5-falsification-stated-in-advance)
- [HOW](#how--architecture--method) — [6. Architecture](#6-architecture-components--contracts) · [6a. Detector](#6a-method--the-detector-box-4) · [6b. Reconcile](#6b-method--reconcile-box-5) · [7. Confounds](#7-confounds--controls) · [7a. Baselines](#7a-baselines-the-system-must-beat)
- [HOW MUCH](#how-much--scope--feasibility) — [8. Scope](#8-scope)
- [CHECK](#check--would-it-survive-contact) — [9. Deliverable](#9-deliverable-design-backward-from-this) · [10. Guarantees](#10-failure-modes--guarantees-systems-section) · [11. Adversary](#11-adversary--the-hard-questions-answered)
- [Hardest questions to chase down first](#hardest-questions-to-chase-down-first)
- [Verification (Asta)](#verification-asta--resolved-2026-08-24-round-2-verified-against-source)
- [Relation to prior threads](#relation-to-prior-threads)
- [Appendix A — Archived: the ripple-repair framing (v0.1)](#appendix-a--archived-the-ripple-repair-framing-v01-superseded-2026-08-24)

---

## 0 · One-paragraph statement

Real deployments increasingly keep knowledge in **two stores at once**: a
**parametric** belief (edited into the weights via ROME/MEMIT/FT) and a **retrieval**
store (a RAG index). An update can land in either — and the two can silently
**contradict**: the model confidently asserts its stale *parametric* belief while the
RAG index holds the corrected fact, or vice-versa, or the model *ignores* the
retrieved correction at inference ("edit skipping", Liu et al. 2025). **No current
metric catches this**: editing metrics test the parametric store alone; RAG metrics
test the retrieval store alone; neither tests whether the two *agree*. KEEP is the
missing check — a **consistency-certifier** that probes both stores on an update's
query neighbourhood, **detects** parametric↔retrieval contradictions (and *which*
store the model actually uses), optionally **reconciles** them, and emits a **scoped
consistency certificate**. The routing/governance architecture is already *specified*
(Zhang et al. 2025, DMM Gov); KEEP is the first to **build and empirically certify**
the consistency mechanism DMM Gov leaves unimplemented.

---

## 0.5 · The category correction (2026-08-24) — read this first
_(Findings [T-017]. Fork resolved in [T-018]; prior-art in [T-016].)_

**The mistake we were making.** We treated editing and RAG as *competitors on one
scale* and read editing's weak multi-hop/ripple numbers as a defeat. They are not
competitors — they are **two different functions**, and grading editing on multi-hop
was grading it on RAG's exam.

**The axiom (settled):**
> Editing changes what the model **believes** — persistent, always-on, on-device,
> removable; knowledge the model reasons *from*. RAG supplies what the model
> **reasons over** at inference — fresh, retrievable, citable, reversible. Different
> functions → different metrics. **Honor both; engineer the seam, not the winner.**

**Belief vs. composition (the two jobs under "knowledge update"):**
- *Belief* — what the model asserts when asked directly. Editing does this well
  (efficacy high; MEMIT holds ~90 at 10K edits — this is editing SUCCEEDING).
- *Composition* — using that belief inside a reasoning chain (multi-hop). RAG does
  this better, because a fact in context is reasoned over natively. This is why the
  in-context baseline beats parametric editors on RippleEdits and MeLLo beats
  ROME/MEMIT on MQuAKE. Not editing failing — editing being asked to reason.

**The boundary (so "editing = belief" doesn't collapse into "editing = patch table"):**
If editing changed *only* the direct answer, a cheap external override (SERAC/MeLLo)
would dominate it — which argues *against* weight-editing. So the line sits one notch
out: **editing owns belief + its *representationally-local* neighbourhood** (the
fact, its paraphrases, tightly-entailed facts that share the representation);
**RAG owns composition that requires *chaining* to other stored facts** (multi-hop).
Sharp test: *an edit must carry to what shares its representation; it need not carry
to what requires reasoning to reach.* Where that line actually falls is empirical —
that is T-006 (how far does "representationally local" reach?), the science that keeps
editing honest without demanding it be a reasoning engine.

**Why editing at all, not just RAG (the Q1 answer, deepened):** RAG structurally
*cannot* do three things — (1) **remove** knowledge already in the weights
(unlearning: privacy/copyright/safety); (2) make an update **pervasive/always-on**
(RAG only helps when the fact is retrieved); (3) work with **no retrieval infra**
(on-device / frozen artifact / latency-bound). Those are editing's irreducible
territory. This is also the Manifesto bet: move knowledge into "the layer that
persists and reasons," not the re-feed-every-time layer. RAG is that re-feed layer.

**Honest caveat (Manifesto Q2):** the *principle* that both matter is correct but NOT
novel — surveys already gesture at complementarity. It clears "is it true?" (Q1) but
not "does it take prior work one step further?" (Q2). **The step-further is what we
build at the SEAM, not the stance itself.**

**The fork — RESOLVED 2026-08-24 → Fork B, claim repositioned (Asta round-2, verified
against source; findings [T-018]).**
- **Fork A — editing-side reliability, teeth = removal/unlearning.** Not chosen. A's
  scoop verdict (MODERATE-HIGH) came from unlearning citations (TOFU/WMDP/SalUn/MUSE/
  "Harry Potter") that are NOT in the retrieved document — pulled from general
  knowledge, so unverified by this search. Kept as fallback, not pursued.
- **Fork B — the edit/RAG seam (orchestration + consistency). ✓ CHOSEN.** The real
  world is "edit for belief, retrieve for reasoning"; the open piece is *consistency
  between the two stores*.
  - **Honest correction to Asta's rosy read:** B is NOT greenfield. Zhang et al. 2025
    ("Memory in LLMs") propose **DMM Gov**, a *named* governance framework that already
    SPECIFIES the routing+consistency loop — "auditable loop covering admission
    thresholds, rollout, monitoring, rollback, audits, with specs for conflict handling
    and long-horizon consistency." So **do NOT claim "first hybrid memory router"** —
    the architecture is published as a spec.
  - **The genuine, defensible gap (the flag we plant):** *first to **build and
    empirically certify** the parametric↔retrieval consistency mechanism that DMM Gov
    specifies but leaves unimplemented.* Anchor on the concrete buildable piece — a
    **consistency-certifier** that detects when the edited parametric belief
    contradicts the retrieval store — not the grand router. Manifesto-Q2 clean: one
    verifiable step past a named prior framework.
  - **Scoop risk is NOT "LOW" — it's an active named frontier** (the doc's Open-
    Challenges section calls hybrid edit/RAG THE future direction). Move with speed;
    anchor narrow.

---

## WHY — is it worth doing?

### 1. Significance
- **The failure is real, silent, and unowned.** In a hybrid (edit + RAG) system —
  which the literature calls the field's next direction — an update can leave the
  parametric belief and the retrieval store *contradicting each other*, and **no
  existing metric looks for it.** Editing benchmarks (efficacy/locality/portability)
  probe weights only; RAG benchmarks probe retrieval only. The seam is a blind spot.
- **Why it bites in deployment.** A model can answer a direct query from its stale
  *weights* while the corrected fact sits in the RAG index it didn't retrieve
  (retrieval miss), or retrieve the correction and *ignore* it (edit skipping, Liu et
  al. 2025). Either way the system is confidently, silently wrong — the exact failure
  a regulated/medical/on-device deployment cannot tolerate.
- **This realizes a named-but-unbuilt spec.** DMM Gov (Zhang et al. 2025) explicitly
  calls for "long-horizon consistency" and "conflict handling" across editing and RAG
  but implements neither. KEEP builds and *measures* that property — turning a
  governance spec into a working, auditable certificate.
- **What changes on each outcome:**
  - Certifier works → hybrid knowledge systems get a **deployable consistency
    guarantee**: detect contradictions before they ship, reconcile, certify. A real
    safety property for a real (and growing) deployment pattern.
  - Contradictions turn out **rare** in realistic updates → a valuable, publishable
    **negative**: the seam is safe, hybrid systems need no cross-store check, and the
    field can stop worrying about it. (This is the significance gate — measure it
    FIRST; see §5 null-branch and §8 v1.)

### 2. Prior art & positioning
_(Reframed 2026-08-24 for Fork B. Ripple/predictor prior art from [T-016] is now
BACKGROUND, not the target — see Appendix A. Seam prior art from [T-018] is verified
against the round-2 document.)_

**The direct competitors (the seam):**
- **DMM Gov — Zhang et al. 2025 ("Memory in LLMs")** — the closest prior work.
  *Specifies* a coordinated edit/PEFT/RAG governance loop with "admission thresholds,
  rollout, monitoring, rollback, audits… conflict handling and long-horizon
  consistency." **Specification, not implementation.** KEEP differs in one sentence:
  *we build and empirically certify the consistency mechanism DMM Gov only describes.*
- **SERAC — Mitchell et al. 2022** — a discriminator gates *edit-memory vs. base
  model*. That is edit-vs-base routing, NOT edit-vs-retrieval **contradiction
  detection**. It never asks "do my two stores disagree?"
- **MeLLo / GMeLLo — Zhong 2023 / Chen 2024** — pure external-memory reasoning; no
  parametric edit, so no cross-store consistency question arises.
- **Edit skipping — Liu et al. 2025** — diagnoses that RAG-based editing *skips* the
  edited fact at inference (model ignores the retrieved correction). This is the
  closest thing to our "which store does the model actually use" sub-question — we
  **build on it** (their diagnosis becomes our detector's `which_wins` signal) and
  extend it from a failure-mode observation into a certified consistency check.

**Positioning in one sentence:** everyone builds better editors, better retrievers,
or *specifies* how to coordinate them; **nobody builds and measures the check that the
two stores agree.** KEEP is that check.

**Scoop risk:** MODERATE — hybrid edit/RAG is a named active frontier (the round-2
doc's Open-Challenges section). LOW specifically on *building + measuring* cross-store
consistency (only specified, by DMM Gov). Move fast; anchor on the concrete certifier.

---

## WHAT — what exactly is the claim?

### 3. The claim / contribution
_(Rewritten 2026-08-24 for Fork B — findings [T-018].)_

**KEEP is the first system to build and empirically certify parametric↔retrieval
consistency for hybrid knowledge systems.** Given an update to a model that holds both
an edited (parametric) belief store and a retrieval store, KEEP:
1. **probes** both stores on the update's query neighbourhood,
2. **detects** contradictions — where the parametric belief P(q) and the retrieval
   answer R(q) disagree — and identifies **which store the model actually uses** at
   inference (the edit-skipping signal),
3. optionally **reconciles** a detected contradiction, and
4. emits a **scoped consistency certificate**: "on query set Q, the parametric and
   retrieval stores agree at rate X, confidence C."

The routing/governance *architecture* is prior work (DMM Gov specifies it; we adopt,
we do not claim it). ROME/MEMIT/FT and the retriever are **swappable components**. The
contribution is the **built, measured consistency mechanism** — the detector (box 4)
and the certificate (box 6) — that DMM Gov names but leaves unimplemented. One
verifiable step past a named prior framework (Manifesto Q2).

### 4. Completeness (the question family)
For the claim to be *believed*, KEEP must answer:
- **Q1 Prevalence (the significance gate).** Do realistic hybrid updates actually
  create parametric↔retrieval contradictions at a non-trivial rate — ones that
  neither store's own metrics flag? *If ~never, there is no problem to certify.*
  **Measure this first.**
- **Q2 Detect.** Can we reliably detect a contradiction (P(q) ≠ R(q) on the fact
  slot) with high precision/recall against constructed ground truth?
- **Q3 Which-wins.** When the stores contradict, can we determine / predict which one
  the model's full-system answer follows (edit-skipping vs. parametric-override)? A
  certificate is hollow if it can't say what the model will *do*.
- **Q4 Certify.** Can we emit a scoped, calibrated consistency guarantee whose
  "consistent" verdict is trustworthy (low false-certify rate)?
- **Q5 Reconcile.** Given a detected contradiction, can we resolve it (re-edit
  parametric / fix-or-remove the retrieval doc / route-override) *without creating new
  contradictions elsewhere*?
- **Q6 Generality.** Does it hold across editors (ROME/MEMIT), retrieval configs, and
  models?
One box working is a demo; the family is the system. **Q1 is the stop-condition** —
if prevalence is ~0, publish the negative and stop.

### 5. Falsification (stated in advance)
- **Confirm:** realistic hybrid updates create silent contradictions at a non-trivial
  rate (Q1); KEEP's detector catches them with high precision/recall vs. ground truth
  (Q2); the certificate's "consistent" verdict is trustworthy (low false-certify, Q4);
  and reconciliation reduces the contradiction rate over an un-certified hybrid
  baseline without net-new contradictions (Q5).
- **Deny — null / no-problem (the significance gate):** contradictions essentially
  never occur in realistic updates → the seam is safe → **project stops; publish the
  negative** ("hybrid stores stay consistent by default"). Cheapest kill, run first.
- **Deny — detection:** a trivial baseline (string-match P vs. R) detects
  contradictions as well as KEEP → the certifier adds nothing over a naive check.
- **Deny — which-wins unpredictable:** the model's use of parametric-vs-retrieval is
  not determinable/predictable → the certificate can't state what the model will
  actually answer → the guarantee is hollow (reduce scope to "stores agree",
  drop "model will answer consistently").
- **Deny — reconcile:** every reconciliation creates as many new contradictions as it
  fixes (whack-a-mole) → reconcile is infeasible; KEEP degrades to detect+certify+flag
  (still a deployment gate; see §10 floor).

---

## HOW — architecture & method

### 6. Architecture (components + contracts)
Pipeline; each box an interface so components are swappable and independently testable.
Boxes **1–2 are adopted from DMM Gov (not our contribution)**; the **novel science is
box 4 (DETECT) and box 6 (CERTIFY)**; box 5 (RECONCILE) is the ambitious extension.

```
update_request ─▶ [1 ROUTE]  ─▶ store choice: parametric | retrieval | both   (DMM Gov — adopted)
                       ▼
                 [2 APPLY]   ─▶ hybrid system H = (edited_model, retrieval_index)  (ROME/MEMIT | index write)
                       ▼
                 [3 PROBE]   ─▶ per query q ∈ Q(update): P(q), R(q), A_H(q)
                       ▼
                 [4 DETECT]  ─▶ contradictions {q : P(q) ≠ R(q)} + which_wins(q)   ◀── NOVEL CORE
                       ▼
                 [5 RECONCILE] ─▶ H'  (re-edit param | fix/remove retrieval doc | route-override)   (v2)
                       ▼
                 [6 CERTIFY] ─▶ consistency_certificate {agree_rate, per-type, scope, confidence}   ◀── NOVEL
```

Interfaces (buildable-by-a-second-engineer contracts):
- **UpdateRequest**: `{subject, relation, target_old, target_new, cloze}`
- **QuerySet** `Q(update)`: `[{q, expected_new, slot}]` — the fact + paraphrases +
  representationally-local neighbours the update should govern (from RippleEdits /
  controlled set; NOT multi-hop, per §0.5 boundary).
- **P(q)** `parametric_answer(edited_model, q) → token/slot` — model answer with
  **retrieval disabled** (the belief in the weights).
- **R(q)** `retrieval_answer(retrieval_index, q) → token/slot` — the answer implied by
  the retrieved document(s).
- **A_H(q)** `system_answer(H, q) → token/slot` — the full hybrid system's answer
  (retrieval enabled) — used for `which_wins`.
- **4 Detect** `detect(P, R, A_H over Q) → [{q, contradiction:bool, which_wins ∈ {param,retrieval,neither}}]`
- **5 Reconcile** `reconcile(H, contradictions) → H'` (v2 core)
- **6 Certify** `certify(detections) → {agree_rate, per-type rates, pass/fail, confidence, scope=Q}`

### 6a. Method — the Detector (box 4)
- **Contradiction** is measured on the **fact slot**, not surface text: `P(q)` and
  `R(q)` mapped to the target entity/value, `contradiction = (norm(P) ≠ norm(R))`.
  (Reuse the first-token/slot normaliser from the v0.1 `rome_study.py` evaluator.)
- **which_wins(q):** compare `A_H(q)` (retrieval-enabled) to `P(q)` and `R(q)` —
  `param` if it follows the weights (retrieval ignored → edit-skipping-inverse),
  `retrieval` if it follows the doc, `neither` if incoherent. Directly operationalises
  Liu et al. 2025's edit-skipping as a measurable per-query label.
- **Ground truth (construct validity):** build controlled contradiction pairs — edit
  the parametric belief to X, leave the retrieval doc at Y (≠ X) — so the detector's
  precision/recall is measurable against a known contradiction set. Also include
  agree-pairs (both X) as negatives.
- **Deferred (recorded, not chosen):** representation-level contradiction detection
  (compare parametric read-direction vs. retrieved-fact direction) — richer than
  slot-match but needs the T-006 reachability result; v2.

### 6b. Method — Reconcile (box 5)
Candidate strategies, increasing ambition (v2):
- **Flag-only (floor):** detect + certify + surface the contradiction; do not fix
  (safe deployment gate; always available).
- **Retrieval-fix:** update/remove the stale retrieval document so R(q) matches the
  intended belief (cheap, reversible — RAG's native strength).
- **Parametric-fix:** re-edit the weights so P(q) matches the intended belief (uses
  the editor; risks its own ripple → must re-detect).
- **Route-override:** at inference, force the system to prefer the authoritative store
  for this query (leans on box 1 / DMM Gov admission policy).
- Open question (the Q3-adversary make-or-break): is there a reconcile that
  monotonically lowers the contradiction rate without net-new contradictions? If not,
  that non-convergence is itself the finding.

### 7. Confounds & controls
| Confound | Control |
|----------|---------|
| "Contradiction" is really a surface/format mismatch, not a fact disagreement | normalise P/R to the fact slot; construct-validity check on agree-pairs |
| Retrieval miss vs. genuine contradiction conflated | separate `R(q)=∅` (no doc retrieved) from `R(q)≠P(q)` (doc disagrees) |
| which_wins driven by prompt template, not the stores | vary templates; measure which_wins stability per fact |
| Pre-update unknown facts pollute prevalence (model can't answer q pre-update) | competence filter: exclude q the model can't answer pre-update |
| Editor / retriever choice drives results | run across ROME/MEMIT × ≥1 retriever config (Q6) |
| Detector leakage (using A_H to define the contradiction it should predict) | contradiction defined from P,R only; A_H used solely for which_wins |

### 7a. Baselines the system must beat
- Detector vs. **naive string-match** P vs. R (does slot-normalisation + which_wins
  add anything?).
- Certificate vs. **editing-metrics-only** and **RAG-metrics-only** (the point: each
  alone MISSES cross-store contradictions — show the miss rate).
- Reconcile vs. **flag-only** and **do-nothing** (net contradiction-rate reduction).

---

## HOW MUCH — scope & feasibility

### 8. Scope
- **v1 (IN):** boxes 3, 4, 6 (probe / detect / certify) on gpt2-xl or GPT-J + a
  **simple retrieval store** (FAISS over a small controlled fact corpus), ROME as the
  editor, **constructed contradiction ground truth**. **First experiment = Q1
  prevalence** (do contradictions occur + do editing-only / RAG-only metrics miss
  them). Then detector PR (Q2) + which_wins (Q3) + the certificate (Q4). Reconcile =
  flag-only + retrieval-fix (proof of concept).
- **v2 (DEFERRED):** parametric-fix + route-override reconcile; box 1 route policy;
  MEMIT / sequential edits; representation-level detection (needs T-006); realistic
  large RAG corpus; the on-device / medical demo; a real serving wrapper.
- **Feasibility (today's evidence):** editing is local + CPU-heavy; gpt2-small runs on
  Mac but is weak and gpt2-medium NaNs here → **v1 wants a GPU** (Colab/cloud) for
  gpt2-xl/GPT-J. The retrieval store is tiny and cheap. Covariance stats cache once.
  Main cost = edit × query × contradiction-set sweep → GPU makes it tractable. The
  detector/certify loop is cheap (forward passes only).

---

## CHECK — would it survive contact?

### 9. Deliverable (design backward from this)
- **Headline figure:** **the silent-contradiction rate** — fraction of realistic
  hybrid updates that leave the parametric and retrieval stores contradicting, **split
  by what current metrics catch**: (i) editing-metrics-only miss rate, (ii)
  RAG-metrics-only miss rate, (iii) KEEP detection rate. The one picture that says
  *"neither store's own metrics see this; KEEP does."* This simultaneously carries the
  **significance** (bar (i)+(ii) height = how blind the field is) and the
  **contribution** (bar (iii) = what KEEP recovers).
- **Secondary:** detector precision/recall vs. ground truth; the `which_wins`
  breakdown (how often the model ignores the retrieved correction — edit-skipping in
  the wild); post-reconcile contradiction rate vs. flag-only baseline; calibration of
  the certificate (false-certify rate).

### 10. Failure modes & guarantees (systems section)
- KEEP **never silently ships** a cross-store contradiction it can detect: worst case
  it certifies "inconsistent" and flags/rolls back (safety floor = surface the
  disagreement).
- Guarantee is **scoped + probabilistic**: "on query set Q, stores agree at rate X,
  confidence C" — never "the system is globally consistent." Scope = the enumerated Q.
  Over-claiming global consistency is the fastest way to lose a reviewer.
- Degrades gracefully: no reconcile → still detect+certify+flag; which_wins
  unpredictable → certify store-agreement only, drop the behavioural claim.

### 11. Adversary — the hard questions, answered
_(Written 2026-08-23; updated 2026-08-24 for Fork B. Hardest-first. Where an answer is
CONDITIONAL it says so. Answering these IS the WHY gate. Q1 was RESOLVED by §0.5 — it
rested on a category error, not a real defeat.)_

**Q1 (the value-killer). "Why edit weights at all? Why not just RAG?"** → **ANSWERED
by §0.5 (category correction).** Editing and RAG are different functions, not
competitors; the multi-hop numbers scored editing on RAG's exam. And crucially for
Fork B: the whole *point* of KEEP is that real systems use **both**, so "editing vs.
RAG" is the wrong question — the question is whether the two stores *agree*. **Status:
resolved; it motivates Fork B rather than threatening it.**

**Q2 (novelty vs. DMM Gov). "Zhang et al. already specified this coordination loop.
What's new?"** DMM Gov is a *specification* (admission/rollback/"long-horizon
consistency" as desiderata) — it does not implement or measure cross-store
consistency. KEEP's contribution is the **built + empirically-measured** detector and
certificate: a number for how often stores contradict, whether current metrics miss
it, and whether reconciliation helps. One verifiable step past a named framework.
**Say "first to build and certify", never "first to conceive".**

**Q3 (significance gate). "Does this contradiction actually happen, or are you
inventing a problem?"** Empirical, and it's the **first** experiment (§8 v1, §5
null-branch): measure the silent-contradiction rate on realistic hybrid updates. If
~0, we publish the negative and stop. Designing backward from this number (§9) means
the project produces a result either way.

**Q4 (reconcile whack-a-mole). "A parametric-fix has its own ripple; a retrieval-fix
can desync again. Does reconcile converge?"** Make-or-break for box 5, empirical:
measure net contradiction-rate change over reconcile rounds. If it doesn't converge,
KEEP degrades to detect+certify+flag — still a deployment gate (§10 floor).

**Q5 (which-wins). "Even if the stores agree/disagree, you don't know what the model
will actually answer."** That's exactly `which_wins` (box 4), built on Liu et al.'s
edit-skipping. If it turns out unpredictable, we narrow the certificate to
store-agreement and drop the behavioural claim (§5 deny-branch) — honest scope, not a
hollow guarantee.

**Q6 (feasibility). "gpt2-small with NaNs on gpt2-medium — can you run the regime that
matters?"** v1 on gpt2-small is a pipeline-validity proof, explicitly caveated as
not-yet-transferred; gpt2-xl/GPT-J needs a GPU (open item, v1→v2 boundary).

**Q7 (scale). "Certify probes a query set per update — tractable at scale?"** v1 is
small-batch high-assurance (tens of updates, full query certification), not
MEMIT-scale. A real niche (regulated / on-device single-fact updates); don't overclaim
mass-editing scale.

**Q8 (circularity). "The detector uses the model's answer to define the contradiction
it should find."** No: contradiction is defined from **P and R only**; the
retrieval-enabled `A_H` is used *solely* for `which_wins`, never to define the
contradiction. Enforced in code.

**The floor (survives even if reconcile / which-wins fail):** a **cross-store
consistency detector + scoped certificate** — "CI for hybrid knowledge: never ship an
undetected parametric↔retrieval contradiction." Modest, honest, infra-shaped,
defensible even if box 5 is empty. The project cannot drop below this.

---

## Hardest questions to chase down first
_(Post-fork. Ordered by leverage; resolve before building past v1.)_
1. **Does the contradiction actually happen? (significance gate — Q3)** Measure the
   silent-contradiction rate + the editing-only / RAG-only miss rates FIRST. If ~0,
   pivot or publish the negative. Everything else depends on this.
2. **Ground-truth construction.** How do we build controlled parametric↔retrieval
   contradiction pairs that are realistic, not strawmen? (edit P to X, retrieval at Y.)
3. **Is which-wins determinable? (Q5)** Can we say which store the model follows, or
   must the certificate stay agreement-only?
4. **Compute substrate.** GPU for gpt2-xl/GPT-J + a FAISS store — Colab/cloud choice.
5. **Does reconcile converge? (Q4)** Only after detect+certify are proven and Q1 says
   the problem is real.

## Verification (Asta) — RESOLVED 2026-08-24 (round-2, verified against source)
_(Doc: "Knowledge Edit Propagation, Locality, Multi-Hop Chaining, and Complementary
RAG.{pdf,txt}". Findings [T-018]. Verdicts below are what the SOURCE supports, which
corrects Asta's summary in two places.)_
1. **Fork B scoop-check** → **not greenfield but the buildable gap is open.** Zhang et
   al. DMM Gov *specifies* the routing+consistency loop (don't claim "first router");
   the consistency-*certifier* is unbuilt/unmeasured (that's the flag). ✓ resolved.
2. **Removal / unlearning reliability** → **verdict unverified by this search** — the
   unlearning citations Asta cited aren't in the retrieved doc. Fork A shelved. ✓.
3. **Belief↔composition boundary** → confirmed still open: beyond GradSim, no work
   cleanly separates locality-spread vs. multi-hop-chaining propagation (Locate-then-
   edit gives a partial mechanistic account: single-hop early-MLP, multi-hop later).
   Keeps T-006 live as the science. ✓.
4. **Complementarity as stated position** → CONFIRMED established (Liu et al. 2025,
   Zhang et al. 2025). So the *stance* is not novel — the built consistency-certifier
   is. Matches §0.5 honest caveat. ✓.

## Relation to prior threads
- **T-006** (belief↔composition boundary — how far a belief-edit legitimately carries)
  = the science under Fork B; feeds the deferred representation-level detector (§6a).
- **T-015** (the 3-way outcome evaluator + slot normaliser) is reused as the
  contradiction slot-matcher in box 4.
- **T-018** = the fork decision that produced this v0.2 rewrite.
- The v0.1 ripple-repair pieces (predictor vs. GradSim, cascade repair) are **not the
  project** — archived in Appendix A; reusable if the seam prevalence (Q1) is ~0 and
  we fall back to Fork A.

---

## Appendix A — Archived: the ripple-repair framing (v0.1, superseded 2026-08-24)

_Kept for history and as a fallback (Fork A). This framing tried to make an editor's
ripple/multi-hop propagation reliable via a predict→repair loop. Superseded by §0.5's
category correction (multi-hop is RAG's job, not editing's) and the Fork-B decision
([T-018]). Do not build from this without re-opening the fork._

**A.1 — old claim.** KEEP as a closed loop `predict → edit → evaluate → repair →
certify` that raises the "consistent-edit rate" (all entailed neighbours update AND
locality stays fine) over raw editing.

**A.2 — old Predictor (box 1).** Features per neighbour: hop distance; raw cosine
(baseline, template-saturated ~0.998, AUC 0.68); structured geometry (Kim bilinear /
edit-difference vector); subject-sharing; causal routing (does the neighbour read the
edited MLP site); pre-edit competence. Predict the 3-way outcome; report AUC per hop.
**Partly scooped by GradSim (Qin et al. 2024)** — gradient-cosine ripple predictor
([T-016]); our only whitespace was per-neighbour / cheaper / wired-into-repair.

**A.3 — old Repair (box 4).** Rollback; cascade-edit stale neighbours; targeted
correction of broken/target-bleed neighbours. Open question: does it converge without
net-new breakage (whack-a-mole)? Crowded neighbourhood (KEDAS/RippleCOT/Bidirectional-
Edit/ChainEdit/CaKE/MeLLo) — [T-016].

**A.4 — why archived.** The multi-hop failures this loop chased are RAG's job (§0.5).
The reusable residue: the 3-way evaluator + slot normaliser (→ box 4 detector), and
T-006 as the science boundary. Empirical results that still stand: [T-015]
over-propagation + target-bleed on gpt2-small ROME (pipeline-validity only).
