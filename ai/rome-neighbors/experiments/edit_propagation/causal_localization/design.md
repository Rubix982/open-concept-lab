# Design — Causal localization of edit propagation (T-019)

_Sub-project of rome-neighbors, home: `experiments/edit_propagation/causal_localization/`._
_Parent threads: T-006 (two-graphs), T-019. Structured by the Research Design Protocol
(10 lenses). **No code until this passes.** v0.1 — 2026-08-24._

## 0 · One-paragraph statement
E-014 (behavioural) + E-015 (predictive) show edit propagation collapses / over-propagates
with hop. E-016 (whole-residual interchange) showed the edited representation is *broadly
readable* (random-position control ~75%) — so it did **not localize** where a neighbour
reads the edit. This sub-project asks the causal-mechanism question that completes the
agreed direction: **does a neighbour causally read the edit via a specific path — the
attention edge from its readout token to the edited subject token — and does that read
decay with hop?** Method: **attention-knockout** (cut the readout→subject edge on the
edited model; measure answer reversion), path-patching as the refinement.

---

## WHY

### 1. Significance
- Completes the causal leg of the agreed direction (the one part E-016 left inconclusive).
- **Confirmed** (knockout reverts propagated neighbours, edge-specific, decays with hop) →
  the two-graphs thesis gains a *causal mechanism*: near neighbours read the edit through a
  clean subject→readout edge; far neighbours don't (or mis-route) → over-propagation/stale.
- **Denied** (knockout doesn't revert) → propagation is *distributed* / not carried by that
  edge — a different but real result (redirects the mechanism story).
- Either way the story moves; a null on E-016 alone would leave the causal question open.

### 2. Prior art & positioning
- Methods we build on: causal tracing (Meng ROME 2022), **path patching** (Wang IOI 2022;
  Goldowsky-Dill 2023), **attention knockout** (Geva 2023; Wang 2023), IIA/DAS (Geiger).
- Positioning (one sentence): apply *edge-level* causal localization to **edit
  propagation across entailment hops** — not "where the fact is stored" (ROME) but "where
  a *neighbour* reads the edited fact, and whether that read decays with hop."
- **Scoop pass DONE (2026-08-24, Asta → `asta_scoop_2026-08-24.md`):** verdict = **UNCLAIMED**
  (credible). Adjacent-but-different: CaKE / Knowledge Circuits (fact *storage*, not neighbour
  *reading*), Zhang-2024 (layer-level multi-hop, not edge knockout), Geva (base recall, not
  post-edit propagation), Huang/Kim/Jeong (geometric ripple predictors, not causal edges).
  **Scoop risk:** HIGH on Bau lab (CaKE) + Zhejiang (Knowledge Circuits) — both have
  circuit infra and could pivot; **Bau = Natalie/Arnab's lab → raise it with them (collaborate).**
  ⚠️ Asta's specific citations had misattributed titles (no source doc) → **verify before
  the deck/paper.** Counter-evidence to respect (real, sharpens §6): **Hase "Does Localization
  Inform Editing?"** (localization ≠ editability — a strong edge may not mediate) and
  **Geva-2021** (redundant storage → non-reversion may be backup paths, not "no read").

---

## WHAT

### 3. Completeness (the question family)
- Q1 **Reversion:** does knocking out readout→subject attention on the EDITED model revert
  a propagated neighbour's answer toward the un-edited value?
- Q2 **Layer:** at which layer(s) is the edge load-bearing? (sweep)
- Q3 **Hop-decay:** does reversion track hop — strong for near (paraphrase/1-hop), weak for
  far (2-hop) — mirroring E-015?
- Q4 **Specificity:** control (readout→random edge) does NOT revert.
- Q5 **Tie-back:** does per-neighbour reversion correlate with the E-015 geometric predictors?

### 4. Falsification (pre-stated)
- **Confirm:** knockout reverts propagated neighbours (edge-specific: control null), reversion
  decays with hop.
- **Deny (distributed):** knockout doesn't revert → the edit is read via many paths / the MLP,
  not this edge. (Real finding — "representational strangers even at the edge level.")
- **Deny (method):** the random-edge control *also* reverts → method broken, fix first.
- **Null:** too few propagated neighbours per hop to test → pool + report n/CI, or scale.

---

## HOW

### 5. Method & construct validity
- **Attention-knockout:** on the edited model, run the neighbour prompt; at layer L, zero the
  attention weight from the **last-token query** to the **subject-token key** (set the
  pre-softmax score to −inf so mass renormalises over the remaining keys). Measure whether
  the argmax answer **reverts** from the edited value toward the clean (un-edited) value.
- **Construct validity:** "reversion when the edge is cut" = that edge *carried* the edit's
  effect to the readout → the neighbour causally reads the edited subject there. This fixes
  E-016's flaw: it tests a *specific read edge*, not broad residual readability.
- **Deferred methods (reviewer trail):** (i) **path patching** — patch only the
  subject→readout path's contribution (more precise than cutting the whole edge; v2);
  (ii) **DAS** — learned subspace of the read (v3); (iii) **MLP-path knockout** — the edit
  may be read via MLP, not attention (v2). Knockout first = cheapest edge-level causal test.

### 6. Confounds & controls
| confound | control |
|----------|---------|
| subject not locatable in neighbour prompt | restrict to locatable (as E-016); note coverage |
| cutting ALL of the last token's attention trivially breaks output | cut ONLY the one edge (last→subject), renormalise the rest |
| attention mass changes after zeroing | renormalise remaining weights (−inf pre-softmax does this) |
| effect present only where the edit propagated | test only PROPAGATED / affected neighbours |
| spatial non-specificity (the E-016 failure) | control = last→RANDOM-key edge (must not revert) |
| sdpa/flash hides weights | force `attn_implementation="eager"` |
| **redundancy** (Geva-2021): non-reversion may be *backup paths*, not "no read" | interpret non-reversion cautiously; v2 multi-edge / path-patching to rule out redundancy |
| localization ≠ mediation (Hase): a strong edge may not drive the answer | criterion is *reversion* (behavioural effect of the cut), not edge-strength alone |

### 7. Baseline
- E-016 whole-residual interchange (broad, non-localized) = the baseline this improves on.
- Random-edge knockout = the specificity control.

## HOW MUCH

### 8. Scope & feasibility
- **v1 (IN):** attention-knockout, gpt2-small local, layer sweep, ~50 edits (reuse the
  proven `iia_scale.py` edit loop + efficacy filter). Forwards cheap; the ROME edit (~15s)
  is the bottleneck → sequential, ~15 min background.
- **v2 (DEFERRED):** path patching; MLP-path knockout. **v3:** GPT-J via NDIF.
- **Feasibility:** the one real risk is the attention-pattern intervention — **smoke-test
  the knockout mechanism in isolation FIRST** (cf. the interchange-hook smoke test; the
  rushed argmax-efficacy bug cost 3h). Eager attention on gpt2 exposes the weights.

## CHECK

### 9. Deliverable
- **One figure:** reversion rate (edited→clean) under **last→subject knockout** vs
  **last→random control**, **by hop**, layer-resolved (or best layer). ± Wilson CI.
- The sentence it earns: *"cutting the subject→readout attention edge reverts X% of
  propagated neighbours (control Y%), decaying with hop"* — the causal localization.

### 10. Adversary (pre-empt the reviewer)
- "Knockout breaks everything." → only the single edge; control (random edge) is null.
- "Reversion ≠ localization." → edge-specificity + layer-specificity + the control.
- "The edit is read via the MLP, not attention." → true; knockout tests the *attention*
  path; MLP-path knockout is v2 (named, not ignored).
- "gpt2-small toy." → v3 GPT-J.
- "Few propagated per hop." → pool + n/CI; E-016 had 228 affected, so power is fine.

---

## Plan (build order — gated on this design)
1. **Asta scoop pass** (lens 2) — is hop-resolved edge-localization of edit propagation claimed?
2. **Smoke-test** the attention-knockout mechanism in isolation (eager gpt2; cut one edge;
   confirm the pattern changes and output moves — like the interchange-hook test).
3. Wire knockout into the edit loop (reuse `iia_scale.py`); add the random-edge control.
4. Run v1 (~50 edits), aggregate → the deliverable figure (§9), log findings.
5. Only then consider v2 (path patching / MLP path).
