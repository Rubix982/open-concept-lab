# Design — Representational Geometry as a Predictor of Edit Propagation

_Project: rome-neighbors · Idea A (reframed after Asta lit review, 2026-08-09)_
_Structured by the 10 design lenses (global CLAUDE.md → Research Design Protocol)._

## Claim & contribution (one line each)

- **Claim (hypothesis):** Raw representation *distance* does NOT reliably predict
  whether a factual edit propagates to logically entailed neighbours; *structured*
  relational geometry and *residual-stream alignment* do — and the effect is
  resolvable as a function of entailment hops with a causal metric.
- **Contribution:** The first systematic, quantitative comparison of
  raw-distance vs. structured-geometry vs. alignment predictors of edit
  propagation, resolved across entailment hops (N0/N1/N2/reverse), with a causal
  measure (IIA), on decoder-only LMs — turning the qualitative "geometry matters"
  claims (Kim, Jeong) into a hop-resolved predictor comparison against real baselines.

---

## WHY — is it worth doing?

### 1. Significance
The ripple problem is real and dramatic: a ROME-edited GPT-J answers **7.6%** of
MQuAKE-CF multi-hop questions vs **43.4%** before the edit. Editing is deployed to
fix stale/wrong facts, but edits don't propagate → the model becomes internally
inconsistent. What changes by outcome:
- **If structured/alignment predicts (raw doesn't):** a principled diagnostic for
  *when* an edit will ripple, and a concrete target (make the geometry
  structured/aligned) for building editors that propagate. Operationalises the
  two-graphs thesis (T-006).
- **If nothing geometric predicts:** propagation isn't a geometric property —
  it's about the causal circuit; redirects the field away from geometry.
Either way informative. The value is turning a qualitative intuition into a
hop-resolved, causal, quantitative predictor — the measurement the field lacks.

### 2. Prior art & positioning  _(from Asta review, 2026-08-09)_
- **Closest work:** Nishi et al. 2024 (distance → *shattering*, not propagation);
  Kim et al. 2025 (bilinear *structure* → propagation); Jeong et al. 2025 (STEAM:
  residual-stream *alignment* → propagation); Hase et al. 2023 (localization ≠
  editability); Liu et al. 2024/2025 (subject vs. relation; subject-similarity
  predicts *spurious over-propagation*).
- **How we differ:** nobody has done the *systematic quantitative comparison* of
  raw-distance vs. structured vs. alignment predictors, *resolved across
  entailment hops*, with a *causal* (IIA) measure and a per-fact portability
  outcome. Kim/Jeong argue structure/alignment *qualitatively*; we measure the
  full predictor comparison and the hop-decay curve.
- **Scoop risk:** moderate–high — Kim & Jeong are active on structured/alignment.
  Mitigation: (a) our distinct axis (comparison + hop-resolution + causal metric);
  (b) move with urgency; (c) bring in Arnab to map exactly how close they are.
- **Adopt for comparability:** CounterFact, RippleEdits (~5K), MQuAKE-CF; GPT-J
  (NDIF) primary, GPT-2 XL optional; metrics reliability/locality/portability/
  multi-hop; baselines ROME/MEMIT/MEND.
- **Lane CONFIRMED OPEN (Asta probe 1, 2026-08-09)** — implementation-level check
  of the two nearest competitors:
  - **Kim et al. 2025** measures logical generalisation as a *single aggregate*
    over entailed facts (**no hop breakdown**), uses **only behavioural accuracy +
    probing** (**no causal metric**), and runs on **synthetic from-scratch models
    only**. Their own future work asks for "diagnostics for relational structure
    in real pre-trained models." So applying their bilinear probe to a *pre-trained*
    GPT-J, hop-resolved, is itself in their stated gap.
  - **Jeong et al. 2025 (STEAM)** reports Portability as an *aggregate* multi-hop
    score (**no hop breakdown**), uses cosine-alignment + LogitLens + behavioural
    accuracy (**no causal metric / no patching/IIA**). GPT-J 6B is in their model set.
  - **Neither reports by entailment hop; neither uses a causal metric.** Our
    hop-resolved + causal-IIA + head-to-head-predictor-comparison combination is
    therefore unclaimed. Scoop risk revised **moderate-high → moderate**.
- **Novelty CONFIRMED (Asta probe 2, 2026-08-09)** — no single paper does all of:
  per-neighbour distance→propagation correlation, resolved by hop (1-hop/2-hop/
  reverse), with a head-to-head predictor comparison. The pieces exist scattered;
  the combination is the gap. New nearest competitor surfaced:
  - **Huang et al. — "Revisiting Ripple Effects... Pressure-Aware Joint
    Neighborhood Optimization"** — comes closest on the *predictor-variety* axis:
    defines key-space coupling + entanglement + sensitivity probes, and reports
    non-monotonic transfer. BUT does not test them as *competing predictors* of
    *hop-resolved* portability. This is now the closest prior art to cite and
    differentiate from.
  Confirmed unclaimed: per-neighbour distance→propagation link, binned by
  hop, with predictive-power-vs-hop reported.

---

## WHAT — what exactly is the claim?

### 3. Completeness (question family)
- **Q1 baseline:** does raw distance (cosine / diff-of-means) between edited-fact
  and neighbour representations predict ripple (IIA)? _(expected: weak/null — the point)_
- **Q2 structure:** does a structured/relational measure (bilinear-style, or a
  learned/DAS direction) predict ripple better than raw distance?
- **Q3 alignment:** does residual-stream alignment (edited vs. reference trajectory)
  predict ripple?
- **Q4 hop-decay:** how does each predictor's power change across N0/N1/N2/reverse?
- **Q5 control:** does any predictor beat *hop-count alone* (partial correlation)?
- **Q6 layer:** at which layers is each predictor strongest?
One correlation is a tweet; this family is the study.

### 4. Falsification (stated in advance)
- **Confirm:** structured/alignment measures predict IIA with meaningful effect
  size, beat both raw-distance and hop-count baselines, and are layer-localised.
- **Deny (baseline, expected):** raw distance adds nothing over hop-count — a
  *confirmatory null* for the baseline (informative, not failure).
- **Deny (whole geometric story):** NO geometric measure beats hop-count →
  propagation isn't geometric; redirect to circuit-level.
- **Null/degenerate:** nothing propagates at all (IIA ≈ 0 everywhere) → no signal
  to predict; switch to a setting where some propagation occurs (MQuAKE has some
  multi-hop success to work against).

---

## HOW — can you measure it cleanly?

### 5. Method & construct validity
**Predictors (independent variables)** — enumerate, pick, defer:
- Raw distance: cosine, Euclidean, diff-of-means projection → **BASELINE** (pick).
- Structured: **bilinear relational score (Kim et al. 2025), adopted directly** —
  `f_r(s,o) = sᵀ M_r o`, with `s`, `o` = hidden states at the final token of the
  subject/object names at layer `l`, and `M_r` fit per relation per layer by ridge
  regression (RESCAL variant). NOTE: Kim only tested this on synthetic models —
  fitting it on pre-trained GPT-J is novel (their explicit future work). DAS-learned
  subspace → **defer** to v2. Also consider **key-space coupling (Huang et al.)** as
  an additional structured predictor — it is the closest existing multi-probe work.
- Alignment: **STEAM alignment score (Jeong et al. 2025), adopted directly** —
  `S(φ, hᵉ) = (1/L) Σ_ℓ cos(φ_ℓ, hᵉ_ℓ)`, where `hᵉ` = layerwise hidden states of the
  edited/queried prompt at the prediction token, and `φ` = per-layer semantic anchor
  built by averaging hidden states of reference facts about the object (from Wikidata).
- RSA / CKA between fact-pair representations → consider.

**Outcome (dependent variable)** — per-neighbour ripple:
- **IIA / interchange** (causal, our existing tool) → **primary**.
- Actual edit portability (ROME edit → neighbour accuracy on RippleEdits/MQuAKE)
  → stronger, needs edit infra → v1 stretch, else v2.

**Construct validity:**
- Does "distance at the causal layer" measure "facts are close"? Mitigate: sweep
  layers, use multiple metrics, and **normalise** (residual norm grows ~7× with
  depth — our finding), avoid the sink-dominated readout position, measure at
  subject positions.
- Does IIA measure "propagation"? IIA = causal read-path sharing; argue it's a
  proxy and **validate against actual portability** on a subset.

**Tooling (all existing):** NNSight on GPT-J/NDIF, causal tracing (04), IIA,
`.source`, per-head (12b).

**Data & external tooling (Asta probe 3 + web-verified 2026-08-09):**
- **RippleEdits** — repo **`github.com/edenbiran/RippleEdits`** ✓ verified (Asta's
  `eric-mitchell` guess was wrong). Three subsets: RECENT / RANDOM / POPULAR.
  CORRECTION: it does NOT label neighbours "1-hop/2-hop"; it uses **six named
  evaluation criteria**. Our hop typing maps onto them:
    - Logical Generalization → 1-hop entailment (N1)
    - Compositionality I & II → 2-hop / multi-hop (N2)
    - Subject Aliasing → paraphrase / alias (N0-adjacent)
    - Relation Specificity → locality control (should NOT change)
    - Forgetfulness → edited-fact retention control
  → *Bin neighbours by these six criteria*, not by invented hop labels.
- **MQuAKE** — `github.com/princeton-nlp/MQuAKE` ✓ verified. Files:
  MQuAKE-CF-3k-v2 (3k), MQuAKE-CF (9,218), MQuAKE-T (1,825 temporal); each instance
  has `single_hops` / `new_single_hops` (intermediate steps). No native ROME/MEMIT-
  on-GPT-J harness but format-compatible; ships the MeLLo notebook. For v2 multi-hop.
- **EasyEdit** — `github.com/zjunlp/EasyEdit` ✓ verified. ROME/MEMIT/MEND on
  GPT-2/GPT-J/GPT-Neo; datasets KnowEdit/ZsRE/WikiBio/CounterFact. Portability is
  AGGREGATE (has a "One Hop" subcategory but reports aggregated) → stratify manually.
  NOTE: RippleEdits is NOT a native EasyEdit dataset — load it from its own repo;
  use EasyEdit for the ROME/MEMIT editing step on CounterFact.
- **CKA / SVCCA / PWCCA**: **Ecco** (`github.com/jalammar/ecco`) ✓ verified to expose
  SVCCA, PWCCA, and CKA for hidden-state comparison (my earlier caution was wrong).
  Kornblith reference (`google-research/representation_similarity`) is the fallback.
- All three datasets are GPT-J-validated in their original papers.

### 6. Confounds & controls
| Confound | Control |
|----------|---------|
| Entity popularity/frequency (popular → better-represented AND more editable) | match or regress out (Wikidata pageviews/frequency) |
| Subject/query token overlap | measure + control |
| Hop-count as proxy for distance | partial correlation (Q5) |
| Baseline model competence (undefined ripple if model never knew the neighbour) | filter to pre-edit-known facts+neighbours (like E-001) |
| Residual-norm growth / attention-sink artifacts (our findings) | normalise; measure at subject positions, not the sink-dominated last token |
| fp16 cross-run nondeterminism (~1e-3) | noise floor + repeats |

### 7. Baseline (the dumb explanations the claim must beat)
- **Hop-count alone** — does geometry add anything beyond "more hops = less ripple"?
- **Raw cosine distance** — the naive hypothesis, now demoted to baseline.
- **Shuffle/random** control.
Real claim = "structured/alignment predicts ripple *after partialling out
hop-count and beating raw distance*."

---

## HOW MUCH — can you actually do it?

### 8. Scope & feasibility
**v1 (IN):** GPT-J-6B on NDIF; ~30–50 triples with Wikidata-generated neighbours
(N0/N1/N2/reverse); predictors = {raw cosine/diff-of-means (baseline), one
structured, one alignment}; outcome = IIA; controls = hop-count + popularity +
competence filter; correlational. One headline figure.
**v2 (DEFERRED):** actual ROME/MEMIT edits + RippleEdits/MQuAKE portability;
full DAS; causal "push-closer" intervention (make geometry structured → does
ripple increase?); multi-model (GPT-2 XL, LLaMA-2).
**Feasibility:** ~50 facts × handful of neighbours × 28 layers × 3 predictors =
thousands of *small* traces (<1s each); batch via NNSight sessions to respect the
NDIF 1-hr job limit. Neighbour generation via Wikidata (`counterfactual_gen`
stub). Weekend-paced over a few weeks.

---

## CHECK — would it survive contact?

### 9. Deliverable (design backward from this)
- **Headline figure:** predictive power of each predictor vs. entailment hop —
  x = hop (N0→N2/reverse), y = predictive power, one series per predictor.
  Expected shape: raw distance flat/weak, structured/alignment stronger, with a
  decay pattern.
- **Analysis recipe (confirmed sensible by Asta probe 2):** logistic regression
  `P(propagate | predictor, hop-type)`; stratify by 1-hop / 2-hop / reverse;
  compare predictor **AUC-ROC per hop bin**. This is the concrete form of the
  headline figure.
- **Headline number:** Δ predictive power (or partial correlation) of the best
  structured/alignment measure over the raw-distance + hop-count baseline.
- **Secondary:** representation-distance-by-hop (does even raw distance decay?);
  layer-localisation of the best predictor.

### 10. Adversary (pre-empt each attack)
- "Raw-distance null is already known (Nishi/Kim/Jeong)." → demoted to baseline;
  contribution is the comparison + hop-resolution + causal metric, not the null.
- "IIA isn't real propagation." → validate against actual portability on a subset.
- "Localization site ≠ edit site (Hase)." → we don't assume it; measure at
  multiple layers; for portability, edit where ROME edits, not where tracing points.
- "n underpowered." → bootstrap CIs, power estimate, scale facts if needed.
- "Confounds (popularity, overlap)." → explicit controls (lens 6).
- "Cherry-picked layer/metric." → sweep layers, report multiple metrics.
- "Scooped by Kim/Jeong." → confirmed distinct (probe 1): both aggregate + behavioural,
  ours hop-resolved + causal-IIA; Kim is synthetic-only. Still bring Arnab to verify
  nothing in-flight closes the lane.

---

## Experiments → tickets (derived from this design)
1. Neighbour set: **load RippleEdits directly** (repo `edenbiran/RippleEdits`) and
   bin neighbours by its six criteria (Logical Generalization → 1-hop,
   Compositionality → 2-hop, Subject Aliasing → paraphrase, Relation Specificity →
   locality control) rather than generating from Wikidata. Comparable + de-risked.
2. Competence filter — baseline recall of facts + neighbours (extends E-001).
3. Representation extraction + compute the 3 predictor families per
   fact/neighbour/layer.
4. IIA per neighbour (extends the IIA work).
5. Analysis + headline figure (partial correlations, hop-decay, layer sweep).
6. _(v1 stretch / v2)_ actual ROME edit + portability validation on RippleEdits/MQuAKE.

## Threads spawned / touched
- **T-011** (linear representation) — now directly on the critical path (the
  predictors ARE distances between directions).
- **New:** residual-stream alignment metric (how exactly to operationalise Jeong).
- **New:** validate IIA against actual portability (construct validity).

_Open items before building: run the reframed question past Arnab (adversary,
scoop lane); v2 push-closer intervention is the causal capstone if v1 confirms._
