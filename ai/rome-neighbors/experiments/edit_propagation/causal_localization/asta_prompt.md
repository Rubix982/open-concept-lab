# Asta plan — prior-art & scoop for causal localization of edit propagation (T-019)

_This is Lens 2 (prior art & positioning) of `design.md`. Run BEFORE building.
Pattern (as with the earlier passes): run in Asta → save the PDF **and** the pdftotext
→ paste both here → I triage against the SOURCE (Asta summaries can misattribute), then
update design.md §2 with the honest one-sentence differentiator + scoop verdict._

## How to run it (querying plan)
- **One comprehensive prompt** (below) — Asta handled multi-part structure well before.
- If it returns thin on a section, follow up with the targeted sub-prompt for that section.
- **Prioritise 2022–2026**, mech-interp + knowledge-editing venues.
- **The decision that matters:** the closing "scoop verdict" + whether the *hop-resolved,
  edge-level causal localization of edit **propagation to neighbours*** is unclaimed.

---

## THE PROMPT (copy-paste into Asta)

> I'm scoping a mechanistic-interpretability experiment and need prior art + scoop risk
> before building. Search 2022–2026 (mech-interp + knowledge-editing). Be precise about
> what exists vs. what's open, and cite quotes/numbers I can verify.
>
> **What I'm doing.** After a ROME/MEMIT weight edit to a fact, I measure whether a
> *logically-entailed neighbour* (paraphrase / 1-hop / 2-hop) **causally reads the edited
> subject** — via **path patching / attention-knockout**: cut the attention edge from the
> neighbour's readout token to the edited subject token and see if the answer reverts.
> Resolved **across entailment hops**. The hypothesis ("two graphs"): the model's
> causal-read graph mirrors the logical-entailment graph *near* the edit and *diverges*
> with hop — so near neighbours read the edit through a clean edge, far ones don't
> (→ stale / over-propagation).
>
> **Crucial distinction:** this is NOT "where is the fact stored" (ROME causal tracing).
> It's **where a *downstream neighbour* reads an edited fact, and whether that read decays
> with hop.** Please keep that distinction throughout.
>
> **Prior art I already know** (find work *beyond* these; say how each differs in one line):
> ROME/causal-tracing (Meng 2022), MEMIT, path patching (Wang IOI 2022; Goldowsky-Dill
> 2023), attention knockout (Geva 2023 "Dissecting recall"; Wang), IIA/DAS (Geiger),
> GradSim ripple predictor (Qin 2024), RippleEdits (Cohen 2023), MQuAKE (Zhong 2023),
> CaKE circuit-aware editing (Yao 2025), Knowledge Circuits (Yao 2024), locate-then-edit
> multi-hop (Zhang 2024).
>
> **Answer these, in these sections:**
>
> **A. SCOOP — the exact combination.**
> 1. Has anyone used **path patching or attention-knockout to localize how a weight EDIT
>    propagates (or fails) to *entailed neighbour* facts**, hop-resolved? (Not fact
>    storage — neighbour *reading* of the edit.)
> 2. Any work identifying the **specific attention edge / circuit** by which a
>    ripple/portability consequence is (or isn't) read after an edit?
> 3. Any **circuit-level causal account of WHY edits fail multi-hop** (CaKE, Knowledge
>    Circuits, others)? How does each differ from edge-knockout hop-decay?
> 4. Is the **"two graphs" framing** (entailment graph vs. the model's causal-read graph,
>    align-near/diverge-far) stated anywhere?
> → End A with an explicit verdict: is the hop-resolved, edge-level causal localization of
>   *edit propagation to neighbours* **unclaimed**? If close work exists, name who + how it differs.
>
> **B. NEIGHBOURING RESEARCHERS / GROUPS (scoop-risk).**
> Who is *actively* (2024–2026) working on: editing circuits / ripple mechanisms /
> attention-based fact recall / knowledge localization? (e.g. Bau lab, Geva/Tel Aviv,
> Zhejiang/Zhang-Yao, Nanda, Meng, Hase, Todd/function-vectors.) For each: one line on
> their most relevant recent work and whether it overlaps this experiment.
>
> **C. NUMBERS / FIGURES / TABLES / DATASETS (for comparability).**
> 1. What **datasets** should I use so results are comparable — RippleEdits, MQuAKE-CF,
>    CounterFact, KnowEdit? Which suits *causal* (not behavioural) localization?
> 2. What **causal metrics** do people report — AIE (indirect effect), knockout Δlogit,
>    path-patching logit-difference, IIA — and which is standard for this?
> 3. What **figures/tables** are conventional (causal-tracing heatmaps, knockout curves,
>    logit-diff bars)? What should my one deliverable figure look like to be legible to
>    reviewers in this area?
> 4. Any **quantitative causal-localization numbers** for edits/recall I should benchmark
>    against (effect sizes, %-reversion, layer of peak effect)?
>
> **D. COUNTERFACTUAL / PRIOR PREDICTIONS (to pre-state confirm vs deny).**
> 1. Does the literature predict edit propagation is **LOCALIZED** (a specific
>    circuit/edge — e.g. CaKE, Knowledge Circuits) or **DISTRIBUTED** (Geva-style broad
>    recall)? Cite both sides.
> 2. So if my knockout **reverts** neighbours (localized) vs **doesn't** (distributed) —
>    which existing result does each outcome agree/conflict with? (I want to state my
>    confirm/deny branches relative to the literature, not in a vacuum.)
> 3. Any **negative/failed** localization results (edits that resisted circuit
>    localization) — the honest counter-evidence?
>
> For each relevant paper: one line on what it does + how it differs from *hop-resolved
> edge-knockout of edit propagation to neighbours*. If the exact experiment doesn't exist,
> say so explicitly, and flag the closest 2–3 as scoop risks.

---

## After it returns (my triage checklist)
- Verify the headline claims against the pdftotext (not the summary) — check the named
  papers exist and say what's claimed (round-1 taught us Asta can misattribute).
- **Scoop verdict → design.md §2.** If unclaimed: pin the one-sentence differentiator.
  If a group is on it: re-scope (narrow the hop-resolution / the propagation-vs-storage
  angle) or reprioritise.
- **Adopt** the standard dataset + causal metric + figure convention (§5/§9) so results
  are comparable, not idiosyncratic.
- **Pre-state confirm/deny relative to the literature** (§4) using section D.
