# Research Threads — edit-slice

_Open questions tracked as a tree so none is lost._
_See global CLAUDE.md -> "Research Thread Tracking" for the protocol._

---

### T-001 · Should edit-slice merge into rome-neighbors, and in which direction?

**Status:** answered
**Parent:** — (root)
**Opened:** 2026-09-09
**Question:** rome-neighbors is now KEEP (a parametric<->retrieval consistency
certifier — a *method*, aimed at the RAG seam). edit-slice is an *instrument*
that refuses method design and treats RAG framing as a trap. Merging means one
scope lock overwrites the other. Which survives, or do they stay separate with a
stated boundary? See O-002 for the full collision.
**Answer:** Resolved 2026-09-10 — **reuse code, not scope.** The two research
claims stay separate and separately citable; KEEP's Aug-24 lock is untouched.
edit-slice may import rome-neighbors' plumbing (ripplekit, CounterFact loading,
ROME application, result caching) rather than rebuild it. Spawns T-005.

### T-002 · Does Cohen et al. (TACL 2024) Logical Generalization already constitute a backward probe?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-09-09
**Question:** RippleEdits' Logical Generalization test type covers inverse and
symmetric relations. If that is already probing grounds rather than
consequences, core claim 1 ("backward probing is unexplored") weakens and the
pilot's framing shifts. session-2026-09-08.md §9 flags this as the likeliest
counterexample and says to find it ourselves before Arnab does. Read the
test-type definitions directly, not through a summary.
**Answer:** [R-001]. No. Logical Generalization probes the logical closure of the edited
triple — symmetry and transitivity — which is backward in *argument* order, not
*justification* order. Claim 1 survives narrowed; the distinction is declaration 5.
### T-003 · Can RippleBench-Maker's distance function take a code dependency graph?

**Status:** parked
**Parent:** T-001
**Opened:** 2026-09-09
**Question:** RippleBench (2512.04144) advertises a substitutable distance
function including graph path length. If a compiler-derived dependency graph
drops in, the instrument is built on maintained tooling in days rather than
months. session-2026-09-08.md §9 calls this the highest-leverage move available.
**Answer:** —
**Parked note:** **Parked** — the code domain is v2. Resumable cold: the question is whether
RippleBench-Maker's advertised pluggable distance function accepts a compiler-derived
dependency graph. Unchecked. Relevant only once the code-domain oracle is back on
the table, which [E-002] pushed out by weakening claim 2 to a snapshot oracle.

### T-004 · Does the backward-probe pilot survive the ten design lenses?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-09-09
**Question:** No implement ticket may open until it passes. The WHY gate is the
stop condition, and lens 2 (prior art) is where T-002 lands — if Cohen et al.
already did this, the pilot dies here rather than after a week of work.
**Answer:** design.md v0.8 — all ten lenses run. Lens 2 cleared [R-002], §0 gate explored
through E-001/E-002/E-005/E-006. The design has been re-passed after each major
result per Protocol rule 5, and reversed six times in doing so.
### T-005 · What exactly may edit-slice import from rome-neighbors without importing its scope?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-09-10
**Question:** T-001 permits code reuse but not scope merge. Where is the line?
ripplekit is ~490 lines (config, data, reps, predictors, analysis) built for
KEEP's assumptions. Importing `analysis`/`predictors` may drag in KEEP's framing;
importing `data`/`config` probably does not. Decide per-module, and decide the
mechanism (path dependency, vendored copy, or extracted shared package). Must be
settled before the pilot's implement ticket opens.
**Answer:** Moot in practice: nothing was imported. edit-slice built its own `src/` (data,
probing, remote, wikidata, ground_templates), and rome-neighbors' ROME path turned
out to depend on EasyEdit, which is not installed in either of its venvs — so there
was no working stack to borrow. The boundary was never tested because we never
approached it.
### T-006 · Is the grounds relation decidable in the CounterFact/Wikidata setting at all?

**Status:** answered
**Parent:** T-002
**Opened:** 2026-09-10
**Question:** Declaration 5 defines grounds as the facts that were *premises* for
the edited fact. In code, the compiler decides that. In CounterFact it is a
judgement call — "built for the 1889 Paris Exposition" grounds "located in Paris"
only under world knowledge no oracle supplies. So the pilot's grounds probes are
hand-built and therefore circular by §5 of the session note. Is that acceptable
for a pilot whose only job is to show asymmetry, or does it sink the result?
This is lens 5 (construct validity) and lens 10 (adversary) for T-004.
**Answer:** No, and the reason changed twice. [E-002]: the relation is **evidential, not
deductive** — no strict contradiction arises, so there is nothing decidable to
decide. Today's dry-run adds the structural reason: Wikidata asserts **no edge at
all** between a fact and its grounds; they are co-predicates of one subject (a
star), not linked nodes. The graph supplies candidates, never the relation.

---

## Dry-run 2026-09-10 — the expansion/contraction reframe

_Generated by a Premise Dry-Run over the Arnab/Natalie sync-up notes (pp. 9-12).
See global CLAUDE.md -> "Premise Dry-Run"._

### T-007 · Is forward/backward really expansion/contraction?

**Status:** answered
**Parent:** T-002
**Opened:** 2026-09-10
**Question:** Grounds are conjunctive (a conclusion needs all its premises);
consequences are not. So editing a conclusion leaves an intact premise set that
still entails the deleted fact. That makes forward propagation *expansion* and
backward propagation *contraction* — importing AGM and Hansson kernel
contraction rather than restating the observation. Does the mapping hold tightly
enough to inherit their results, or is it an analogy? (Dry-run move 2.)
**Answer:** Partly, and it survives as **vocabulary rather than machinery**. The
expansion/contraction framing correctly names the asymmetry — editors only add —
and [2605.28839]'s "edits suppress rather than overwrite" supports it
mechanistically. But [E-002] dropped AGM's closure half (kernels, partial meet)
because the grounds relation is evidential, keeping its ordering half
(entrenchment, Grove, Lewis). We inherit AGM's account of the problem, not its
algorithm. See agents/shared/decisions.md [E-002].
### T-008 · Does the backward direction terminate without k?

**Status:** answered
**Parent:** T-007
**Opened:** 2026-09-10
**Question:** Forward closure is infinite, which is why declaration 4 needs an
explicit `k`. But a fact has a small finite set of minimal justifications, so
contraction terminates on its own — break every kernel, stop. If true, `k` is
needed forward and not backward, and the direction that sounds intractable is
the bounded one. That asymmetry is what makes the instrument buildable.
(Dry-run move 3.)
**Answer:** Dissolved rather than resolved. The question presupposed grounds lie along a
**chain**, where depth is meaningful. They lie in a **star** — co-predicates of one
subject, with no path structure, no hops and no transitive closure. So `k` does not
apply to grounds at all; the star's variable is in-degree, not depth. `k` remains
meaningful forward, where chains are real. Supersedes the symmetry claim.
### T-009 · Kernel count as the backward out-degree variable

**Status:** answered
**Parent:** T-007
**Opened:** 2026-09-10
**Question:** Over-determination — a fact with multiple independent
justifications — is what makes contraction fail, since expansion needs one path
to succeed but contraction needs every path broken. Gives a per-fact quantity:
justification redundancy. Prediction: orphan rate scales steeply with kernel
count. This is the mirror of KnowledgeSmith's forward branch-structure result,
not a re-derivation of it. Candidate headline: *editing over-spreads forward and
under-spreads backward.* (Dry-run moves 4, 5.)
**Answer:** Superseded with kernels [E-002]. The quantity survives under a different name:
**in-degree** = the number of co-predicates of the subject, measured in E-004 step
1 at a median of 8 per subject (1% have none, 84% have >=3). It is no longer a
count of minimal entailing sets, because there are none.
### T-010 · Metric sign error — should grounds fall or hold?

**Status:** answered
**Parent:** T-007
**Opened:** 2026-09-10
**Question:** CLAUDE.md says of grounds probes "log-prob of pre-edit correct
answer should **not** fall," treating grounds as bystanders. Under the
contraction reading at least one ground per kernel **must** fall for coherence,
so a ground that holds firm is the orphan, not a healthy control. Normative
reading (measure whether any kernel was broken) and conservative reading
(measure damage) give opposite signs on the same number. Must commit before any
figure exists. Note the underdetermination is arguably itself the finding: logic
does not say which premise to sacrifice, so the model sacrifices none.
(Dry-run move 8 — a spec invalidated by the reframe.)
**Answer:** Twice-resolved. First sign-free — measure whether *any* ground moved rather than
whether a specific one should fall. Then [E-002] regraded `orphan` as a degree, so
the question of a sign largely dissolves: we report introduced implausibility and
the facts carrying it. definitions.md declaration 6 and the CLAUDE.md metric line
are both corrected.
### T-011 · Is orphaning structural to expansion operators as a class?

**Status:** parked
**Parent:** T-007
**Opened:** 2026-09-10
**Question:** An LM has no retraction primitive — gradient editing can only move
mass toward a target, and "stop believing what implied the old target" requires
kernels the LM does not represent. If so, orphaning is not a deficiency of ROME
but a consequence of applying an expansion operator to a system with no
contraction primitive. Claim about the class, falsifiable in one shot (find an
editor that contracts). Stronger than "ROME scores poorly backward."
(Dry-run move 7.)
**Answer:** —
**Parked note:** **Parked** — cannot be tested without edit data, which is phase 2. Resumable cold:
the claim is that orphaning is structural to *expansion operators as a class*, not
specific to ROME, because such operators have no contraction primitive.
[2605.28839]'s "edits suppress rather than overwrite" is supporting mechanistic
evidence. Falsifiable in one shot by exhibiting an editor that contracts.

### T-012 · Grounds by intervention rather than enumeration

**Status:** parked
**Parent:** T-006
**Opened:** 2026-09-10
**Updated:** 2026-09-10
**Question (as first asked):** Define: *g* is a ground of *f* iff intervening on
*g* counterfactually moves *f*. Causal, not semantic — discovered rather than
hand-written, so not circular (kills the §5 problem). Runnable today on
GPT2-medium with rome-neighbors' NNSight/IIA machinery, no compiler and no code
domain needed. Would demote the compiler from prerequisite to *validation*: check
a discovered grounds set against a decidable one. Highest-leverage open thread —
it decides whether the pilot needs the compiler at all. (Dry-run move 6.)

**Promoted (T-028):** no longer optional. The discretion-triage tool is only
*reusable* if grounds discovery is mechanical; hand-labels per edit make it a
one-off. No T-012, no tool.

**Refined (T-031) — the definition above is superseded.** It was directionally
blind: a one-sided intervention detects a *link*, not a *direction*. Justifications
are **inputs** (the a priori), consequences are **outputs**; association is
symmetric, justification is not. Current definition:

> *g* is a ground of *f* iff Δ(*g*→*f*) **>>** Δ(*f*→*g*).

Symmetric Δ is classified as undirected topical association — so the construct
threat is detected by the measurement rather than controlled for externally.

**Method selected (design.md §0 v0.5) — roles FLIPPED.** Discovery is now
**(e) mined Horn rules read backwards**: 2606.10554 mines `body => head` rules
from Wikidata with AMIE and reads them forward; read the other way, the body of a
rule whose head is the edited fact IS the kernel. Directed intervention (c) is
demoted from discovery to **validation** — checking the model treats a mined body
as an input, not an associate. Deferred: (a) ROME-based (inherits its own blast
radius), (b) activation patching (v2), (d) gradient attribution (not
counterfactual).

**Non-circularity, now three separable stages:** direction established
*externally* (mined rules), validated *in-context on the unedited model*,
orphaning measured *parametrically on the edited model*. If any two collapse into
one measurement the design is circular.

**Falsification of the gate:** hand-label grounds for ~20 edits; if **mined rule
bodies** do not agree above chance, (e) fails — fall back to (c) as discovery,
then (b), then a non-reusable v1. Second check: the fraction of mined bodies
passing the direction test; a low fraction means the rules are associative and
(e) is unsafe even where it agrees.

**Answer:** partial. Method specified, confounds handled on paper, oracle now
external. **No data.** Resolves only when E-001 (spike) runs. Spawned [T-031],
[T-032], [T-033], [T-034], [T-035].
**Parked note:** **Parked** — the method is right and unrun. Resumable cold: grounds by *directed*
intervention, g is a ground of f iff delta(g->f) >> delta(f->g), with symmetric
delta classified as topical association. [E-006] confirmed remote gradients and
interventions both work on NDIF, so the mechanism is available. It was overtaken by
possession (E-005), which had to come first — a ground the model does not hold
cannot be tested for direction.

### T-013 · Do kernels survive transfer to a graded setting?

**Status:** answered
**Parent:** T-012
**Opened:** 2026-09-10
**Question:** Kernels are a logical notion with sharp membership. In a
probabilistic system support is graded — everything weakly moves everything — so
any kernel boundary is a threshold we impose. Is "kernel" a construct that
survives the subsymbolic transfer, or are we measuring a thresholding artifact?
This is lens 5 (construct validity) and the main threat to T-012.
**Answer:** **No, and they should not.** [E-002] measured it: none of five
rigid-relation cases is a strict contradiction — all are satisfiable. The relation
is evidential, so there is no entailment to break and kernel contraction is
undefined here. Settled in agents/shared/decisions.md: keep AGM's **ordering** half
(entrenchment, Grove, Lewis), drop its **closure** half. The graded structure is
the phenomenon, not a degradation of it — and it is what makes human adjudication
structurally necessary [T-025] rather than merely convenient.

### T-014 · Salvage from the cut material

**Status:** answered
**Parent:** T-007
**Opened:** 2026-09-10
**Question:** §11 cut the self-reinforcing mechanism and backward-pass sync as
method design — correct. But the motivating intuition (p. 12: "we can only
verify through a backward pass") survives without the machinery: verification is
backward even when repair is not. Likewise "inevitable" was banned, but the
content under it — coherence is global, so any bounded audit is arbitrary — is
rescued by kernels, which give a *principled* rather than chosen bound. Confirm
both salvages are sound before they enter a document. (Dry-run move 9.)
**Answer:** Both salvages hold, one with a revision. "Verification is backward even when
repair is not" survives intact and is now the project's core (T-025). The
"inevitable" content — coherence is global, so any bounded audit is arbitrary — was
to be rescued by kernels giving a principled bound; kernels are gone [E-002], so
the rescue is now the **star's finite in-degree**: a fact has a bounded set of
co-predicates, which bounds the audit without appeal to entailment.
### T-031 · Inputs/outputs: the grounds test must be directed

**Status:** answered
**Parent:** T-012
**Opened:** 2026-09-10
**Question:** A fact is a node with inputs (justifications, the a priori) and
outputs (consequences). A one-sided intervention detects a link, not a direction —
association is symmetric, justification is not. So §0's test was directionally
blind.
**Answer:** Two-sided test. Δ(g→f) >> Δ(f→g) means g is an input; the reverse
means output; roughly equal means undirected association. The association
confound is thereby *detected by the measurement* rather than controlled for
externally. design.md v0.2 §0.

### T-032 · In-degree and out-degree are different variables

**Status:** answered
**Parent:** T-031
**Opened:** 2026-09-10
**Question:** We have been conflating two branching factors.
**Answer:** Out-degree = consequences = forward propagation burden
(KnowledgeSmith, published). In-degree = justifications = kernels to break =
contraction burden (ours, unrun). Separate variables, separate vocabularies
recorded per CLAUDE.md. Sharpens T-009.

### T-033 · The oracle is the unedited model's own in-context reasoning

**Status:** answered
**Parent:** T-031
**Opened:** 2026-09-10
**Question:** Direction is established in-context on the *unedited* model;
orphaning is measured parametrically on the *edited* model. Different mechanisms,
so the apparent circularity dissolves — and the audit holds the model to its own
stated dependencies rather than an imposed graph. But this is a *model-derived*
oracle, not a decidable one: a model with poor dependency beliefs gets an easy
exam. How much does that weaken the result, and does it change what the code
domain buys in v2?
**Answer:** largely dissolved by the v0.5 flip [T-035]. Discovery moved to mined
Horn rules over Wikidata — an **external** artifact — so the model no longer sets
its own exam. Residual: mined rules are statistical, so the oracle is a decidable
*lower bound with confidence thresholds*, not a deduction. Declaration 2 already
commits to exactly that language. The code domain still buys true decidability in
v2.

### T-034 · Show structure, never ranking

**Status:** answered
**Parent:** T-025
**Opened:** 2026-09-10
**Question:** In-degree and input-depth are informative about which ground is
least a priori — but using them to select what to retract is exactly the
entrenchment ordering we refuse to supply.
**Answer:** The tool reports structural facts (in-degree, depth, kernel
membership) and never sorts them by what should be sacrificed. Descriptive, not
normative. Written into design.md lens 5 as a boundary.

### T-035 · Mined Horn rules read backwards give the kernels

**Status:** answered
**Parent:** T-012
**Opened:** 2026-09-10
**Question:** 2606.10554 mines `body => head` rules from Wikidata with AMIE and
reads them forward (edit touches body, does head update?). Read backwards: if the
edit changes the **head**, the **body** is the set of premises that entailed it —
i.e. the kernel, obtained mechanically from an existing artifact. In-degree =
number of distinct rules sharing a head = justification redundancy [T-009].
**Answer:** Dead, for two independent reasons. [E-001]: AMIE over DBpedia yields alias
tautologies — 66.5% of usable rules are `fact + alias => fact`, and all 32
rigid-head rules are of that form. Today's structural reason is deeper: **rule
mining finds chain patterns, and grounds are star relations.** We were asking a
chain-finder for a structure it does not represent, so no amount of KG quality
would have fixed it.
### T-036 · Probe-generation-from-a-graph is not ours

**Status:** answered
**Parent:** T-035
**Opened:** 2026-09-10
**Question:** session-2026-09-08 §5 argued "read questions off the oracle — the
graph is the question generator." AMIE-mined rules over Wikidata is that idea,
already built and published, forward.
**Answer:** conceded. The mechanism is not ours; only the **direction** and the
**partition** are. Second narrowing of the day after [R-001]. Thinner but cleaner.
Any document must not claim probe-generation-from-a-graph as novel.

### T-023 · CounterFact relation inventory — rigid vs mutable

**Status:** answered
**Parent:** T-010
**Opened:** 2026-09-10
**Question:** Orphaning requires the edited relation to be rigid over time. If
CounterFact is dominated by mutable relations, a naive sample measures a null
where orphaning was impossible in principle.
**Answer:** [R-003] — 34 relations, **7,770 rigid edits (35.4%)**, 12,073 mutable
(55.1%), 2,076 ambiguous (9.5%). Gate passes with two orders of magnitude of
headroom; mutable pool amply covers the matched control. Table published
contestable at probes/relation_modality.md. **The binding constraint moved**: from
"are there rigid edits" to "do rigid edits have mined grounds in DBpedia" — now
E-001's job [T-035].

### T-037 · Time-rigidity blocks relocation only — it never establishes contradiction

**Status:** answered
**Parent:** T-013
**Opened:** 2026-09-10
**Question:** The rigid/mutable 2x2 asserted that a rigid edited relation forces a
contradiction with its grounds. Does it?
**Answer:** No — that was our error, caught by [E-002]. Time-rigidity closes the
*relocation* reconciliation ("the tower was moved") and nothing else. Repatriation,
emigration and distant naming all survive it. Rigidity is a plausibility
**modifier**, not a contradiction test. [R-003]'s table is reinterpreted, not
discarded; design.md lens 5 and definitions.md declaration 6 corrected.

### T-038 · The termination argument is partly given back

**Status:** answered
**Parent:** T-013
**Opened:** 2026-09-10
**Question:** [T-008] argued backward needs no `k` because kernels are finite while
forward closure is infinite — the asymmetry that made the instrument look
buildable. That presupposed entailment. Evidential support has no natural
boundary, so backward now needs a threshold too. How much of the asymmetry
survives, and is a plausibility threshold meaningfully better than an arbitrary
`k`, or have we just renamed the parameter?
**Answer:** Resolved with [T-008]. Nothing was given back, because nothing was owed: the
termination argument was stated over chains, and grounds are not chains. There is
no `k` to rename and no threshold standing in for one — the star is finite by
construction. A plausibility threshold is still needed to rank grounds by strength,
but that is a *strength* cut, not a *distance* cut.
### T-039 · Possession — does the MODEL hold the ground?

**Status:** answered
**Parent:** T-012
**Opened:** 2026-09-10
**Question:** Wikidata says Perec was born in Paris. Does GPT-2? A ground the
model never held cannot be orphaned — nothing is left standing to contradict
anything. Between "the oracle lists these grounds" and "the edit orphaned them"
there is a missing step: verify the model holds the ground pre-edit. Method (c)
validates *direction*, not *possession*.
**Answer:** [E-005], measured across four models: 56% / 74% / 79% / 85% at 6B / 8B / 70B /
405B, n=165 each. Possession is a genuine gate — not saturated even at 405B — and
scale buys only the hard relations. Consequence for the pilot: P19 place of birth
tops out at 53% and GPT-J holds 13%, which moved the edit target to Llama-3.1-8B
[T-050, E-006].
### T-041 · Does contraction EVER occur, on hand-built deductive grounds?

**Status:** parked
**Parent:** T-013
**Opened:** 2026-09-10
**Question:** E-002 found grounds evidential *as Wikidata expresses them* — a fact
about the schema, not about knowledge. Hand-build small deductive ground sets
where entailment is explicit, edit the head on GPT-J, and ask whether the editor
retracts anything at all. Existence claim only; hand-picked sets may never be used
for a frequency claim [O-004].
**Answer:** —
**Parked note:** **Parked** — this is option C, blocked on people rather than code. Resumable cold:
hand-build small deductive ground sets where entailment is explicit, edit the head
on Llama-3.1-8B, ask whether the editor retracts anything. Existence claim only
[O-004]. [E-006] established the edit is applicable; the blocker is the annotation
study, which has had no identified annotators since design.md lens 8 first flagged
it.

### T-042 · Amend the charter's no-scaling rule

**Status:** answered
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** CLAUDE.md ruled out scaling; T-039 makes model size a construct
requirement. Amend or violate?
**Answer:** Amended 2026-09-10. The discipline survives, the blanket cap does not:
"scaling for its own sake, or to frontier scale for headline value" stays out of
scope, and the rule becomes **smallest model that demonstrably holds the
grounds**. Also aligned two stale lines in the charter — the `orphan` definition
and the grounds-sign metric — both superseded by declaration 6.

### T-043 · The dimension space of a knowledge bit

**Status:** parked
**Parent:** T-031
**Opened:** 2026-09-10
**Question:** Nodes have more axes than we are using: direction (done), in-degree,
out-degree, support type (deductive/evidential), modality (rigid/mutable, done),
**possession** (T-039), **entrenchment**, depth-from-primitive. Two are doing all
the work and two are missing. Entrenchment is where the human's decision actually
gets made — "which do I give up" is answered by relative entrenchment — and we
have cited it repeatedly without ever defining how to measure it.
**Answer:** —
**Parked note:** **Parked 2026-09-11** — advanced by [T-052] (direction, in/out-degree, possession,
modality identified as axes; entrenchment and depth still undefined), but it serves
the structure map, which is parked. Resumable cold from the table in T-052.

### T-044 · The standard pre-edit condition overstates possession

**Status:** answered
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** The editing literature selects edit sets with
P(target_true) > P(target_new). Is that a valid possession test?
**Answer:** No — it is a forced binary choice and too easy. On identical items:
two-way 75%, constrained rank 61%, unconstrained top-1 12%. The last is confounded
by CounterFact's temporally/locatively ambiguous templates ("died at" -> "the age
of 90"), not by ignorance — the same model ranks Koun/Athens 1/10 under constraint.
Constraining candidates to objects attested for the same relation fixes both ends.
Cheap, general, and directly useful to anyone building edit sets [E-003].

### T-045 · Possession of the EDIT TARGET, not just the audited model

**Status:** answered
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** Possession was measured on Llama-70B, but ROME would be applied to
GPT-J-6B. If GPT-J sits nearer GPT-2 than Llama, the possession argument has moved
the problem rather than solved it — we would be editing a model that does not hold
its own grounds. If GPT-J is low: get ROME working on 70B (hyperparameters and
second-moment statistics we do not have), or accept a possession ceiling on the
edit target and report it as a limitation.
**Answer:** **GPT-J-6B is 73% top-1 [E-003b]** — between GPT-2 (61%) and Llama-70B
(93%). Neither disqualifying nor adequate unfiltered. Resolution: run the pilot
**entirely on GPT-J**, possession-filtered; ~5,700 of the 7,770 rigid pool remain,
far more than a 50-edit pilot needs. ROME on 70B is not required. Note the audit
model must BE the edited model — Llama-70B's role is to show possession is
scale-dependent, not to be the pilot's subject.

### T-046 · Reframe the primary deliverable as the possession/structure map

**Status:** answered — reframed, but SPLIT
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** The strongest results so far are edit-independent: the measurement
critique (75/61/12 on identical items) and the possession curve (61->62->73->93).
Both stand whether or not ROME ever runs. Proposal: make the primary deliverable a
map of whether a model holds the **justificational neighbourhood** of an editable
fact — the inputs and outputs — which every edit evaluation presumes and none
checks. Edit evaluation becomes phase 2, which the map makes interpretable.
Strictly better on risk: T-041 may come back null and the map survives it.
E-004 supports it — joint possession 69%, dense enough to centre.
**Answer:** **Yes to the reframe, no to the pairing.** [R-006] separates the two
halves decisively.

*Possession* is complete and sharp: four models, n=165, a measurement correction,
and one unclaimed result — CounterFact's filter was calibrated once against a 2022
model and the same fixed 21,919 records are reused on every model since. GPT-J
holding 13% of P19 is the measured cost.

*The structure map* is neither complete nor sharp. Its value was as the foundation
for the orphan work, which is blocked on annotators [T-041] — a foundation for
something blocked is a foundation for nothing yet. It also extends further into
factual probing, which R-006 showed is crowded, so it would make the claim broader
and muddier simultaneously.

Deliverable is therefore **possession-as-precondition**: a filter that reports what
fraction of an edit set the model actually holds, plus a short note on why that
differs from what CounterFact's filter implies. A tool, not a figure — which is
also the framing the Compass check flagged as the employable one. Structure work
parks with T-041 until the orphan arc unblocks.

### T-047 · Lens 2 second pass — factual probing, not editing

**Status:** answered — [R-006]
**Parent:** T-046
**Opened:** 2026-09-10
**Question:** R-002 searched the *editing* literature because the claim was about
editing. If the headline becomes "what does the model hold", the neighbours change:
LAMA and its successors, factual-probing methodology, calibration, knowledge
boundaries. That is a crowded field and "expose the ground truths" phrased broadly
walks straight into it. What survives is narrower — direction (input/output
structure rather than flat fact lists), grounds specifically (nobody probes
justifications), and possession as a **precondition for a propagation claim**
rather than a capability score. Must be closed before any write-up.
**Answer:** [R-006]. **The diagnostic framing is false and is dropped.** CounterFact
filters records on P(true) > P(counterfactual) pre-edit (Meng et al. 2202.05262),
so possession *is* checked — with the weak two-way test we already critiqued.
Adopt the descriptive framing. Strongest survivor: that filter is **model-relative
and non-transferable**, yet the fixed 21,919 records are reused across every model
since 2022 — and GPT-J holds 13% of P19. Prompt sensitivity and
phrasing-over-knowledge belong to the LAMA line and must be cited, not re-derived.

### T-048 · Grain confound in the head-vs-ground comparison

**Status:** parked
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** [E-004] found ground possession (82%) above head possession (73%),
contradicting the prediction. The cause looks like granularity, not knowledge:
surviving ground properties are countries and languages (small answer spaces) while
heads are cities. The one fine-grained ground property, P131, scores worst at 53%.
Also top-3 is 100% everywhere, so the measure is at ceiling. Fix: grain-matched
and larger candidate sets before any head-vs-ground claim is made.
**Answer:** —
**Parked note:** **Parked 2026-09-11** — blocks any head-vs-ground claim, and head-vs-ground is
parked with the structure map. Resumable cold: E-004's ground possession looked
higher than head possession only because surviving ground properties were coarse
(countries, languages) while heads were fine (cities); the one fine-grained ground
property, P131, scored worst. Grain-matched candidate sets are required before any
such comparison.

### T-049 · Type-matching is not cue-matching

**Status:** answered
**Parent:** T-039
**Opened:** 2026-09-10
**Question:** E-003/E-004 controlled distractors by *type* — when the relation
wants a place, every candidate is a place. Is that the right control?
**Answer:** No. The operative confound is not type but **cue**: the subject's
surface form suggests an answer independently of any stored fact ("Darrieux" ->
French, "Yakuza" -> Japan). Type-matched but cue-mismatched distractors are easy,
which is why top-3 saturated at 100%. The correct control is distractors the
subject's surface form suggests *equally* — obtained automatically by mining the
model's own subject-free prior. Possession is then **lift over that prior**, not
raw rank. Recorded as the RCA on E-005.

### T-050 · P19 is the pilot's pinch point

**Status:** answered
**Parent:** T-045
**Opened:** 2026-09-11
**Question:** [E-005] — P19 place of birth tops out at 53% even at Llama-405B, and
GPT-J holds 13%. P19/P20 carry the richest grounds (burial, citizenship, family),
so the relation most informative for orphan probing is the one every model holds
worst, and the intended edit target barely holds it. Filtering GPT-J to what it
holds strips out the ground-rich relations, which defeats the filter's purpose.
Options: ROME on Llama-3.1-8B (needs hyperparameters + second-moment statistics we
do not have, but 8B is tractable); or re-select toward relations GPT-J holds
(P103/P138/P178/P407 at 80-87%) and accept ground-poor edits. Abandoning the
possession filter is rejected — that is the artifact the gate exists to prevent.
**Answer:** —

### T-051 · Candidate-set size, not cue contamination, drove the inflation

**Status:** answered
**Parent:** T-049
**Opened:** 2026-09-11
**Question:** [T-049] claimed type-matching is not cue-matching and that surface
cues inflated E-003/E-004. How much did that actually contribute?
**Answer:** Much less than claimed. At 50 candidates, naive top-1 and
lift-corrected possession differ by only 3-5 points across all four models. The
inflation was overwhelmingly **easy negatives** — 10 candidates rather than 50.
T-049's reasoning about cue vs type remains sound in principle and the lift
control is worth keeping (it shows the prior baseline is only 4-5%, so results are
not template-guessable), but it was not the operative defect. Recorded so the
correction is not lost: the cheap fix was more candidates.

### T-052 · Grounds are a STAR, not a chain

**Status:** parked
**Parent:** T-043
**Opened:** 2026-09-11
**Question:** We have said throughout that "the graph gives grounds". It does not.
Every ground we have used — P19 birth, P27 citizenship, P119 burial — is another
property of the **same subject**. Wikidata asserts no edge between them; they are
siblings on one node, and the justificational relation among them is entirely our
imposition. Three distinct neighbourhood structures were being conflated:

  star          co-predicates of one subject          -> candidate GROUNDS (ours)
  chain         object becomes the next subject       -> CONSEQUENCES (the literature)
  reverse star  facts where our subject is the object -> untouched by anyone

Consequences already recorded: [T-035] rule mining fails because it finds chain
patterns and grounds are star relations; [T-008]/[T-038] `k` does not apply to the
star because it has no path structure.

**Open part:** which structure should the instrument centre on, and does the star
framing match the branching diagram in the sync-up notes (p.10) — were those nodes
co-predicates or genuine multi-hop chains? That changes the design.
**Answer:** —
**Parked note:** **Parked 2026-09-11** with [T-046]'s split — the star/chain typology is foundation
for the orphan arc, which is blocked on annotators. Resumable cold: grounds are
co-predicates of one subject (a star), not chain-linked nodes; Wikidata asserts no
edge between a fact and its grounds; three structures were being conflated (star ->
grounds, chain -> consequences, reverse star -> untouched). The open part remains
whether the sync-up diagram's branching nodes were co-predicates or genuine
multi-hop chains.

### T-053 · Generic question generation from property metadata

**Status:** parked
**Parent:** T-052
**Opened:** 2026-09-11
**Question:** [E-004] found template coverage, not ground availability, was the
binding constraint — 26 hand-written templates covered 13 properties and 89/165
subjects. Wikidata properties carry labels, aliases, descriptions and value-type
constraints, so a uniform key-value cloze ("Georges Perec — place of birth:")
generates a probe for **any** property with no judgement and no marginal cost.
Trade-off: less natural phrasing, probably lower absolute possession. Gain:
uniformity, which matters because hand-written templates inject per-property
phrasing quality that confounds every cross-property comparison — the same species
of artifact as [T-048]'s grain confound. Testable directly: we hold 26 hand-written
templates and can compare head-to-head on identical facts.
**Answer:** —
**Parked note:** **Parked 2026-09-11** with [T-052]. Resumable cold: a uniform key-value cloze
("Georges Perec — place of birth:") generates a probe for any Wikidata property at
zero marginal cost, removing the per-property phrasing quality that confounds
cross-property comparison. Directly testable against the 26 hand-written templates
already in probes/ground_templates.md. Only needed once ground probing resumes.

### T-054 · The CounterFact filter outlived the model it was calibrated against

**Status:** ACTIVE
**Parent:** T-047
**Opened:** 2026-09-11
**Question:** [R-006] established that CounterFact filtered records on
P(true) > P(counterfactual) pre-edit — so possession *is* checked. But that filter
was applied **once, in 2022, relative to the authors' model**, and the same fixed
21,919 records have been reused on GPT-J, Llama, Qwen and everything since. The
guarantee does not transfer, and nothing in the pipeline re-establishes it. Our own
measurement is the cost: GPT-J holds 13% of P19 place of birth, 56% overall.

**[R-007]: survives.** 2505.18690 critiques setups, teacher-forcing, dataset
coverage and multi-edit, and proposes a context-based baseline; it does not measure
possession and does not raise the transfer problem.

This is the project's strongest unclaimed result and the centre of the deliverable.
It needs: (a) ~~2505.18690 read~~ done; (b) the claim
stated so it does not read as an accusation — a dataset outliving its calibration
is nobody's carelessness; (c) a concrete recommendation, i.e. re-filter per model
and report possession alongside efficacy.
**Answer:** —

### T-055 · Zeugma as a type-matching validator for candidate sets

**Status:** answered — shipped at reduced strength
**Parent:** T-044
**Opened:** 2026-09-11
**Question:** The possession measure depends on candidates being type-matched —
that is what stops CounterFact's ambiguous templates from expressing themselves
[T-044]. "Type-matched" is currently a heuristic: other values attested for the
same relation. It is never verified, so a contaminated candidate set would pass
silently.

**Coordination gives a principled test.** Two candidates are the same type iff they
coordinate under one predicate without anomaly:

    "Koun died at Athens and at the age of 90"   -> zeugmatic  => different types
    "Koun died at Athens and at Naples"          -> fine       => same type

So a zeugma detector validates the instrument we are shipping, replacing an
assumption with a measurement. Scoped to the filter; does not widen the claim.

Second, related use: **automatic detection of ambiguous templates.** T-044 found
"died at" -> "the age of 90" by reading outputs by hand, which does not scale and
is how the next one gets missed. If a template's completion distribution spans two
ontological categories, the template is ambiguous and the probe is invalid.

**Answer:** built and measured, and it is **weaker than the motivation implied**.
Coordination lift separates same- from cross-type at the set level — +2.39 on a
genuine zeugma, +1.61 on CounterFact's "died at" — but does not classify individual
candidates, because it measures plausibility of *joint predication* rather than type
agreement alone ("dust jacket" is same-type yet scores below every cross-type item).
And it is weakest where ambiguity is **idiomatic**: "died at Naples and at the age
of 90" is standard obituary English, which is exactly the conventionalised case
[T-044] found. Shipped as a set-level diagnostic with per-candidate flagging
advisory; automatic ambiguous-template detection is NOT claimed. See findings
[T-055].

### T-056 · Dual-facet nouns as a probe of representational structure

**Status:** parked — candidate NEXT project, not this one
**Parent:** T-055
**Opened:** 2026-09-11
**Question:** Does a model hold "ledger" as simultaneously physical matter and
informational content? Co-predication is the standard diagnostic for complex
types, so the machinery transfers directly.
**Parked note:** Real question, real prior art — Pustejovsky's Generative Lexicon
and dot objects, plus recent work testing LLMs on co-predication. But it probes
**lexical semantics, not factual possession**: different question, different
literature, different paper. [T-046] split the deliverable an hour earlier for
exactly this reason — pairing a sharp complete thing with a broad incomplete one
makes both worse. Resumable cold: the templates and lexical pools exist (dual-facet
`document_noun` with matched `physical_predicate` / `informational_predicate`
pools), which is most of the instrument already built.
**Answer:** —
