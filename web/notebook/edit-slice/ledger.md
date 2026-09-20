---
title: Evidence ledger
sidebar_label: Evidence
sidebar_position: 3
description: Every decision, finding and thread in the edit-slice record, generated from the repository so it cannot drift from it.
toc_max_heading_level: 2
---

# Evidence ledger

_Generated from `agents/shared/decisions.md`, `agents/shared/findings.md` and `threads.md` by `build_ledger.py`. Regenerated rather than edited._

The [paper](./review) argues a claim and the [narrative](/writing/five-days) tells the story. This is the complete record behind both — including the entries that went nowhere, which are the majority.

**27 decisions · 18 findings · 57 threads (1 active, 45 answered, 3 dropped, 8 parked)**

## Decisions and results

Engineering decisions and experiment outcomes. Each states its falsification before the run, and corrections keep their own entry rather than editing the original.

### E-002 · grounds are evidential, not deductive — AGM's ordering half, not its closure half {#E-002}

_Decision · 2026-09-10_ — Decision: Model the edit-to-grounds relation as evidential support, not entailment. orphan becomes a graded quantity: the joint implausibility an edit…

### O-004 · raise the model to GPT-J-6B via NDIF; hand-build deductive grounds for the pilot {#O-004}

_Decision · 2026-09-10_ — Decision: Amend CLAUDE.md's blanket size cap. The pilot moves from GPT2-medium to GPT-J-6B via NDIF, and the pilot's ground sets are hand-built and…

### E-007 · candidates come from a reference vocabulary, not the edit set {#E-007}

_Decision · 2026-09-13_ — Decision: candidatepool takes an explicit reference set, separate from the edits being filtered, and every unscoreable item is reported in skipped with a…

### O-005 · large models only — the size floor replaces the size ceiling {#O-005}

_Decision · 2026-09-15_ — Decision: work only with very large models. From NDIF's ungated set that is Llama-3.1-70B (possession 79%) and Llama-3.1-405B (85%). GPT-J-6B and the 8B…

### E-009 · the gate clears at 70B, and the three legs are not independent {#E-009}

_Result · 2026-09-15_ — Decision: the edit arm runs on the 70B set. 74 usable chains is enough for an existence claim with room for edit-stage attrition; 20 was not. [O-005]'s…

### E-009b · the `outer` deficit is answer surface form, not pool concentration {#E-009b}

_Correction · 2026-09-15_ — RCA. [E-009] closed with "outer stays the worst leg at both scales, which rules out small-model thinness and leaves candidate-pool concentration —…

### E-011 · the possession measure has no operating point for modal answers {#E-011}

_Result · 2026-09-15_ — The pre-stated Deny branch fired, and it was the wrong dichotomy. [E-009b] predicted that rendering countries naturally would recover the article-taking…

### O-006 · the edit arm runs at Llama-3.1-8B {#O-006}

_Decision · 2026-09-15_ — The gate at three scales, same 136 chains, same pools, same seed: Restricted to the domain [E-011] shows the measure is defined on — the outer answer is…

### E-012 · the two defects are orthogonal, and fixing them beats 60B parameters {#E-012}

_Result · 2026-09-15_ — Usable chains, same 136 chains, same model, same seed: Neither fix alone moves anything: +1 and +1. Together, +20. This is an interaction, not two…

### E-013 · the covariance term is not used by the reference implementation {#E-013}

_Gate 0 resolved · 2026-09-15_ — The problem as stated. ROME's update needs C⁻¹k, the inverse second-moment matrix of keys. Measured from the model configs: Llama-3.1-8B dmlp = 14336, so…

### E-013 · the mandated control is too weak, and this is why {#E-013-2}

_Smoke test, n=1 · 2026-09-15_ — Vlaminck: born in Paris, Paris in France, therefore born in France. Edited the conclusion to Germany. v optimisation drove NLL 5.68 → 0.02 over 25 steps.…

### E-014 · the edit displaces the premise, country-specifically, at 67% {#E-014}

_Result · 2026-09-17_ — Written late. This result was referenced by [E-015], [E-016] and the published paper for three days without an entry of its own — found when cross-linking…

### E-015 · DENY — the relocation carries no inference {#E-015}

_Result · 2026-09-18_ — Resolves agents/shared/disputes.md [E-014]. Both arms push the same country-valued vector through the same subject's key; only the birth edit licenses…

### E-016 · whitening is a near-no-op by cosine and a 50x change in targeting {#E-016}

_Gate · 2026-09-18_ — distribution (NOT ROME's Wikipedia — divergence recorded) Anisotropy — the gate clears. Spectrum of the layer-5 key second moment: The keys live on an…

### E-016 · whitening cannot reduce same-subject leakage, and the reason is analytic {#E-016-2}

_Result · 2026-09-18_ — The experiment. Re-ran [E-015]'s paired test with u = C⁻¹k, where C is the low-rank-plus-ridge key second moment (Woodbury, N=2048, CounterFact prompt…

### E-017 · same-subject leakage is structural — no probe form escapes it {#E-017}

_Result · 2026-09-19_ — Tests [T-074], the threat [E-016] left standing: its analytic account required the probe to share the edit prompt's prefix, which our probes do by…

### O-007 · four "nnsight constraints" were one flaky NDIF node {#O-007}

_Correction · 2026-09-20_ — What I claimed. A commit on 2026-09-20 documented four constraints discovered while building the [T-075] layer sweep: that a list comprehension inside a…

### T-075 · the pinning is exact for prefix-sharing probes at every depth, and {#T-075}

_Result · 2026-09-20_ — Mean coefficient at the subject's last token against the edit's k (1.0 = full delta): Worst case across subjects is sharper still: the possessive form…

### E-018 · the different-subject floor is 0.082 — [E-017] stands, and the floor is now measured {#E-018}

_Result · 2026-09-20_ — Tests [T-076], the control [E-017] never ran. Every prior control held the subject fixed and varied the form; this one varies the subject and holds the…

### O-008 · one of [O-007]'s four retracted constraints is real {#O-008}

_Correction to a correction · 2026-09-20_ — What [O-007] said. Four "nnsight constraints" documented while building the [T-075] sweep were all wrong, and all four were the same thing: NDIF rejects…

### E-019 · the analytic half is layer-invariant; the empirical half is an early-layer fact {#E-019}

_Result · 2026-09-20_ — Runs [T-075] per design.md Part IV. DENY in the mid-deep range and NULL at layer 31 — both pre-stated outcomes fired, at different depths, which is…

### E-020 · the decay is direction, not magnitude — and layer 31 is convergence, not noise {#E-020}

_Result · 2026-09-20_ — Runs [T-077]. [E-019] measured the decay and explained nothing about it. The coefficient is not a cosine — c = (|k|/|k|) · cos(k, k) — so it can fall two…

### E-021 · the subject-token delta is sufficient and necessary — the mechanism is causal {#E-021}

_Result · 2026-09-20_ — Runs [T-067], the hole §6 of the paper names first. Everything from [E-013] to [E-020] is behavioural — vary an input, read an output. [E-016] showed the…

### E-022 · possession IS a fact-level property — and MUTE has two causes, not one {#E-022}

_Result · 2026-09-20_ — Runs [T-062] and [T-064] from one measurement. [T-062] — CONFIRM, and it refutes the expectation this ticket was opened on. Modal-cell share per fact,…

### E-023 · the closed pool undercounts relocation badly — and the Washington attractor was ours {#E-023}

_Result · 2026-09-20_ — Runs [T-066]. Every number in this project comes from ranking a closed type-matched pool. This asks what that hides by letting the edited model generate…

### E-024 · an edit reaches the whole subject, but damages in proportion to type overlap {#E-024}

_Result · 2026-09-20_ — Tests whether a birthplace edit disturbs attributes that have nothing to do with birth. Two probes give a relatedness gradient; the control is the same…

### E-025 · a floor plus type-matched displacement — not a relatedness gradient {#E-025}

_Result · 2026-09-20_ — Separates the two accounts [E-024] could not: language is semantically related to country of origin but typed as a language, so it shares relatedness with…


## Findings

Literature reads and measurements that are not decisions. Two of these closed whole directions at the prior-art gate.

### R-001 · RippleEdits' Logical Generalization is NOT a backward probe — but claim 1 must be narrowed {#f-R-001}

_2026-09-10_ — Verified metadata (session note §9 required this). Cohen, Biran, Yoran, Globerson, Geva, "Evaluating the Ripple Effects of Knowledge Editing in Language…

### R-002 · Lens 2 clears — not scooped, but must be repositioned against knowledge-conflict and deferral {#f-R-002}

_2026-09-10_ — Verdict: PROCEED. No existing work partitions an edit's affected knowledge by whether logic determines the outcome and surfaces the underdetermined part…

### R-005a · mined-rule artifact IS available — but on DBpedia and MQuAKE/MLaKE, not Wikidata/CounterFact {#f-R-005a}

_2026-09-10_ — Gate result: §0 method (e) is FEASIBLE. The critical-path dependency clears. Two corrections to what design.md v0.5 asserted, both material. the…

### R-003 · 35.4% of CounterFact edits use a rigid relation — T-023's gate passes {#f-R-003}

_2026-09-10_ — The fear was unfounded. T-023 worried that CounterFact is so dominated by mutable relations that a naive 50-edit sample would draw almost entirely from…

### E-001 · §0 method (e) FAILS — the mined rules are alias tautologies {#f-E-001}

_2026-09-10_ — Verdict: method (e) does not work on the shipped artifact, and the failure looks structural rather than incidental. Fall back per design.md §0.…

### E-002 · Wikidata carries real grounds — but they are *evidential*, not deductive {#f-E-002}

_2026-09-10_ — Verdict: method (e) is alive on Wikidata. Steps 1 and 2 pass. But what we found are not AGM kernels, and that has consequences. 55 rigid-relation edits, 5…

### E-003 · possession is real, scale fixes it — and the field's standard test overstates it {#f-E-003}

_2026-09-10_ — Verdict: [T-039] confirmed and [O-004] empirically vindicated. Possession is a genuine gate, GPT-2 fails it, and a large model clears it. Scaling within…

### E-003b · GPT-J-6B possession is 73% — usable as the edit target, with filtering {#f-E-003b}

_2026-09-10_ — Answers [T-045]. The hard fork is avoided: we do not need ROME on a 70B model. GPT-J sits between the two: +11pp over GPT-2, -20pp under Llama. So it is…

### E-004 · joint possession is 69% — the pilot has a pool, but the ground number is confounded {#f-E-004}

_2026-09-10_ — Verdict: the gate passes. Joint possession — head held and at least one ground held, same subject, both top-1 by constrained rank — is 61/89 = 69%,…

### E-005 · possession re-measured — 56/74/79/85 across 6B-405B, and scale buys only the hard relations {#f-E-005}

_2026-09-11_ — Replaces the superseded E-003/E-003b/E-004 numbers. Possession = the true answer ranks first among 50 type-matched candidates and ranks higher with the…

### E-006 · ROME on Llama-3.1-8B via NDIF is feasible — both required primitives work {#f-E-006}

_2026-09-11_ — Verdict: option 1 of [T-050] is available. The blocking concern was that NDIF hosts one shared copy of each model, so a weight edit cannot be persisted.…

### R-006 · the diagnostic framing is FALSE — CounterFact does verify possession, with a weak test {#f-R-006}

_2026-09-11_ — Verdict: drop "editing benchmarks measure propagation into knowledge they never verified was there." It is not true, and a reviewer would refute it from…

### R-007 · 2505.18690 does not take T-054 — and hands us one adversary point {#f-R-007}

_2026-09-11_ — Verdict: the nearest competitor does not claim our result. T-054 stands. "Benchmarking and Rethinking Knowledge Editing for Large Language Models" — He,…

### T-055 · coordination lift is a set-level type diagnostic, not a per-candidate filter {#f-T-055}

_2026-09-11_ — Motivation. The possession measure assumes its distractors are type-matched; that assumption was never checked. Coordination should test it — same-type…

### D-002 · CounterFact has NO possession filter — R-006 was wrong, verified from the primary source {#f-D-002}

_2026-09-14_ — This reverses [R-006]. I concluded there that "CounterFact does verify possession, with a weak test", from §3.3's sentence about counterfactuals starting…

### R-010 · the WHY gate narrows sharply — two of three proposed contributions are taken {#f-R-010}

_2026-09-18_ — Run before building the probing taxonomy the project was about to pivot to. Three prior-art hits, two of them direct. Holtzman, West, Shwartz, Choi,…

### R-009 · two ROMEs circulate, and they differ on the term the method is built around {#f-R-009}

_2026-09-20_ — Opened by [E-013] gate 0, which found EasyEdit ships mom2adjustment: false in all fourteen of its ROME configs — including gpt2-xl and gpt-j-6B, the two…

### T-065 · pairs bound, crossings decompose — and narrowing comes from unfixing a dimension {#f-T-065}

_2026-09-20_ — Tests the thread's two structural claims against the record rather than reasoning about them. Every result in decisions.md hand-classified by the shape of…


_Confidence levels and full evidence are in the repository entries; these are one-line pointers, not summaries._

## Threads

Open questions, tracked as a tree. A thread is a unit of *inquiry*; a ticket is a unit of *work*. Parked is not dropped — a parked thread carries enough context to resume cold.

### Active (1)

| id | question | parent | status |
| --- | --- | --- | --- |
| `T-054` | **The CounterFact filter outlived the model it was calibrated against** — [R-006] established that CounterFact filtered records on P(true) &gt; P(counterfactual) pre-edit — so possession is checked. But… | T-047 | ACTIVE |

### Answered (45)

| id | question | parent | status |
| --- | --- | --- | --- |
| `T-001` | **Should edit-slice merge into rome-neighbors, and in which direction?** — rome-neighbors is now KEEP (a parametric&lt;-&gt;retrieval consistency certifier — a method, aimed at the RAG seam). edit-slice… | — (root) | answered |
| `T-002` | **Does Cohen et al. (TACL 2024) Logical Generalization already constitute a backward probe?** — RippleEdits' Logical Generalization test type covers inverse and symmetric relations. If that is already probing grounds rather… | T-001 | answered |
| `T-004` | **Does the backward-probe pilot survive the ten design lenses?** — No implement ticket may open until it passes. The WHY gate is the stop condition, and lens 2 (prior art) is where T-002 lands —… | T-001 | answered |
| `T-005` | **What exactly may edit-slice import from rome-neighbors without importing its scope?** — T-001 permits code reuse but not scope merge. Where is the line? ripplekit is ~490 lines (config, data, reps, predictors,… | T-001 | answered |
| `T-006` | **Is the grounds relation decidable in the CounterFact/Wikidata setting at all?** — Declaration 5 defines grounds as the facts that were premises for the edited fact. In code, the compiler decides that. In… | T-002 | answered |
| `T-007` | **Is forward/backward really expansion/contraction?** — Grounds are conjunctive (a conclusion needs all its premises); consequences are not. So editing a conclusion leaves an intact… | T-002 | answered |
| `T-008` | **Does the backward direction terminate without k?** — Forward closure is infinite, which is why declaration 4 needs an explicit k. But a fact has a small finite set of minimal… | T-007 | answered |
| `T-009` | **Kernel count as the backward out-degree variable** — Over-determination — a fact with multiple independent justifications — is what makes contraction fail, since expansion needs one… | T-007 | answered |
| `T-010` | **Metric sign error — should grounds fall or hold?** — CLAUDE.md says of grounds probes "log-prob of pre-edit correct answer should not fall," treating grounds as bystanders. Under the… | T-007 | answered |
| `T-013` | **Do kernels survive transfer to a graded setting?** — Kernels are a logical notion with sharp membership. In a probabilistic system support is graded — everything weakly moves… | T-012 | answered |
| `T-014` | **Salvage from the cut material** — §11 cut the self-reinforcing mechanism and backward-pass sync as method design — correct. But the motivating intuition (p. 12:… | T-007 | answered |
| `T-031` | **Inputs/outputs: the grounds test must be directed** — A fact is a node with inputs (justifications, the a priori) and outputs (consequences). A one-sided intervention detects a link,… | T-012 | answered |
| `T-032` | **In-degree and out-degree are different variables** — We have been conflating two branching factors. | T-031 | answered |
| `T-033` | **The oracle is the unedited model's own in-context reasoning** — Direction is established in-context on the unedited model; orphaning is measured parametrically on the edited model. Different… | T-031 | answered |
| `T-034` | **Show structure, never ranking** — In-degree and input-depth are informative about which ground is least a priori — but using them to select what to retract is… | T-025 | answered |
| `T-035` | **Mined Horn rules read backwards give the kernels** — 2606.10554 mines body =&gt; head rules from Wikidata with AMIE and reads them forward (edit touches body, does head update?).… | T-012 | answered |
| `T-036` | **Probe-generation-from-a-graph is not ours** — session-2026-09-08 §5 argued "read questions off the oracle — the graph is the question generator." AMIE-mined rules over… | T-035 | answered |
| `T-023` | **CounterFact relation inventory — rigid vs mutable** — Orphaning requires the edited relation to be rigid over time. If CounterFact is dominated by mutable relations, a naive sample… | T-010 | answered |
| `T-037` | **Time-rigidity blocks relocation only — it never establishes contradiction** — The rigid/mutable 2x2 asserted that a rigid edited relation forces a contradiction with its grounds. Does it? | T-013 | answered |
| `T-038` | **The termination argument is partly given back** — [T-008] argued backward needs no k because kernels are finite while forward closure is infinite — the asymmetry that made the… | T-013 | answered |
| `T-039` | **Possession — does the MODEL hold the ground?** — Wikidata says Perec was born in Paris. Does GPT-2? A ground the model never held cannot be orphaned — nothing is left standing to… | T-012 | answered |
| `T-041` | **Does contraction EVER occur, on hand-built deductive grounds?** — E-002 found grounds evidential as Wikidata expresses them — a fact about the schema, not about knowledge. Hand-build small… | T-013 | answered — **no** |
| `T-042` | **Amend the charter's no-scaling rule** — CLAUDE.md ruled out scaling; T-039 makes model size a construct requirement. Amend or violate? | T-039 | answered |
| `T-044` | **The standard pre-edit condition overstates possession** — The editing literature selects edit sets with P(targettrue) &gt; P(targetnew). Is that a valid possession test? | T-039 | answered |
| `T-045` | **Possession of the EDIT TARGET, not just the audited model** — Possession was measured on Llama-70B, but ROME would be applied to GPT-J-6B. If GPT-J sits nearer GPT-2 than Llama, the… | T-039 | answered |
| `T-046` | **Reframe the primary deliverable as the possession/structure map** — The strongest results so far are edit-independent: the measurement critique (75/61/12 on identical items) and the possession… | T-039 | answered — reframed, but SPLIT |
| `T-047` | **Lens 2 second pass — factual probing, not editing** — R-002 searched the editing literature because the claim was about editing. If the headline becomes "what does the model hold",… | T-046 | answered — [R-006] |
| `T-049` | **Type-matching is not cue-matching** — E-003/E-004 controlled distractors by type — when the relation wants a place, every candidate is a place. Is that the right… | T-039 | answered |
| `T-050` | **P19 is the pilot's pinch point** — [E-005] — P19 place of birth tops out at 53% even at Llama-405B, and GPT-J holds 13%. P19/P20 carry the richest grounds (burial,… | T-045 | answered |
| `T-051` | **Candidate-set size, not cue contamination, drove the inflation** — [T-049] claimed type-matching is not cue-matching and that surface cues inflated E-003/E-004. How much did that actually… | T-049 | answered |
| `T-055` | **Zeugma as a type-matching validator for candidate sets** — The possession measure depends on candidates being type-matched — that is what stops CounterFact's ambiguous templates from… | T-044 | answered — shipped at reduced strength |
| `T-057` | **Was CounterFact filtered against a model at all?** — [D-002] found the ROME paper never names a model used to score records during CounterFact construction, and describes a… | T-054 | answered — from the paper, no run needed |
| `T-058` | **Transitive containment as the deductive ground family** — [E-002] found grounds as Wikidata expresses them are evidential — burial place supports place of death without entailing it. To… | T-041 | answered |
| `T-059` | **Is the `outer` deficit answer surface form rather than knowledge?** — [E-009b] found the outer possession deficit is two strings — United States 6/40 held and United Kingdom 2/14, against France… | T-058 | answered |
| `T-060` | **Does the gate clear at 8B, dissolving the 70B editability problem?** — The whole ROME-at-70B covariance problem (~3.3 GB over dmlp 28672, uncollected and uncosted, recorded as the unpaid consequence… | T-059 | answered — **yes** |
| `T-061` | **Is subject familiarity the variable behind the leg dependence?** — [E-009] measured that chain legs are not independent (inner1 &amp; outer lift 2.10 at GPT-J, 1.15 at 70B) and explained it as… | T-058 | answered — **no** |
| `T-062` | **Is possession a property of a fact, or of a (fact, template) pair?** — notes/definitions.md declaration 1 is binding — "a fact is a behavioral unit defined by its probe set" — and every possession… | T-059 | answered — **yes, a fact-level predicate exists** |
| `T-064` | **MUTE — known but inexpressible in this phrasing** — Crossing [E-012]'s two tests gives four cells, and one of them has no name in the literature: row test fails, column test passes… | T-062 | answered — **two causes, not one** |
| `T-065` | **Is the instrument's atom a contrastive pair, with content only at crossings?** — Raised by the user, on noticing that nearly every measurement here is a minimal contrastive pair — subject vs placeholder, bare… | T-062 | answered — **claim 1 sharpened, claim 2 refuted** |
| `T-066` | **What does a closed candidate pool hide that free generation would show?** — Every measurement in this repo ranks over a closed, type-matched pool. That is what makes it controlled — and [E-014] had to… | T-065 | answered — **a great deal** |
| `T-067` | **A causal measure of relocation, not a behavioural one** — [E-015] asks whether the model behaves as if it inferred "born in Germany ⇒ born in a German city", by holding subject and target… | T-065 | answered — **both** |
| `T-073` | **Pool attractor mass as a required artifact field** — Washington, D.C. absorbed 33% of all birth-arm destinations in [E-015] — it is the pool's high-prior city and the default sink… | T-066 | answered — implemented |
| `T-074` | **Does the pinned coefficient survive a prompt that mentions the subject late?** — [E-016] established that ROME's u·k normalisation pins the update coefficient to exactly 1 at the subject's last token, so any… | T-067 | answered — **yes, it survives** |
| `T-075` | **Is the subject key context-robust at every layer, or only at layer 5?** — [E-017] measured the coefficient at the subject's last token to be 0.93-1.00 across probe forms at layer 5 — the layer ROME edits… | T-074 | answered — **only at shallow layers** |
| `T-076` | **Is the different-subject floor high enough to weaken [E-017]?** — Split out of the T-075 design because it is not a layer question and does not need the sweep. One measurement at layer 5:… | T-075 | answered — **no, the floor is 0.082** |

### Parked (8)

| id | question | parent | status |
| --- | --- | --- | --- |
| `T-003` | **Can RippleBench-Maker's distance function take a code dependency graph?** — RippleBench (2512.04144) advertises a substitutable distance function including graph path length. If a compiler-derived… | T-001 | parked |
| `T-011` | **Is orphaning structural to expansion operators as a class?** — An LM has no retraction primitive — gradient editing can only move mass toward a target, and "stop believing what implied the old… | T-007 | parked |
| `T-012` | **Grounds by intervention rather than enumeration** — — | T-006 | parked |
| `T-043` | **The dimension space of a knowledge bit** — Nodes have more axes than we are using: direction (done), in-degree, out-degree, support type (deductive/evidential), modality… | T-031 | parked |
| `T-048` | **Grain confound in the head-vs-ground comparison** — [E-004] found ground possession (82%) above head possession (73%), contradicting the prediction. The cause looks like… | T-039 | parked |
| `T-052` | **Grounds are a STAR, not a chain** — We have said throughout that "the graph gives grounds". It does not. Every ground we have used — P19 birth, P27 citizenship, P119… | T-043 | parked |
| `T-053` | **Generic question generation from property metadata** — [E-004] found template coverage, not ground availability, was the binding constraint — 26 hand-written templates covered 13… | T-052 | parked |
| `T-056` | **Dual-facet nouns as a probe of representational structure** — Does a model hold "ledger" as simultaneously physical matter and informational content? Co-predication is the standard diagnostic… | T-055 | parked — candidate NEXT project, not this one |

### Dropped (3)

| id | question | parent | status |
| --- | --- | --- | --- |
| `T-063` | **Are entailed conclusions less robust than their premises?** — The move-4 variable from the Part II dry-run, and the one quantity in this design nobody else has asked. If a conclusion is… | T-062 | dropped |
| `T-070` | **An edit as an entrenchment probe** — From the premise dry-run: if an editor systematically yields the defeasible premise and retains the necessary one, it implements… | T-063 | dropped |
| `T-071` | **Does declaration 6 need amending?** — Declaration 6 says the choice of what to retract "belongs to a human and not to the method". If the editor makes that choice… | T-070 | dropped |

