# Research Threads — rome-neighbors

_Open questions from research discussion, tracked as a tree so none is lost._
_See global CLAUDE.md → "Research Thread Tracking" for the protocol._

---

## Foundations map & gap tracker

_The `T-00x` threads below are RESEARCH questions. This section tracks
FOUNDATIONS — the basics that must be solid underneath them. Method: you cannot
enumerate the basics upfront; you scaffold, run something, and friction (an
explanation you can't give) exposes the missing basic. **This ledger IS the gap
tracker** — an open thread is a surfaced gap; an answered one is a locked basic.
A thread can be a research question OR a foundational gap._

Four tiers, bottom-up. A thin LOWER tier makes every tier above it feel slippery:

```
TIER 4  Domain:    ROME · MEMIT · desiderata · ripple/neighbours
TIER 3  Methods:   probing · logit lens · ablation · patching · causal tracing · IIA
TIER 2  Mechanics: tokenization · embeddings/RoPE · residual stream · attention · MLP · norm · unembed
TIER 1  Substrate: vectors · dot products · directions=features · matmul · rank-1 · least-squares
```

**Honest self-assessment (2026-08-09):**

- **SOLID** (engaged deeply, corrected well):
  - T2: tokenization/BPE/vocab, residual stream (additive/cumulative),
    attention + softmax + the sink, KV cache
  - T3: metric families, IIA/AIE conceptually, ablation vs. patching, localization
  - T4: MEMIT-vs-project (breadth vs. depth), store→readout→lookback synthesis
- **THIN** (used implicitly, never made foundational) → gap threads T-011..T-014:
  - T1: features-as-directions / dot products / rank-1 — **the big one**, the
    floor under ROME (T-011)
  - T2: MLP internals — *why* facts live there, the key-value memory view (T-012)
  - T2: positional encoding / RoPE (`apply_rotary_pos_emb`, seen but unexercised) (T-013)
  - doing ≠ reading: `04` (AIE) and IIA not yet RUN — see the peak yourself (T-014)

**Recommended next:** T-011 (Tier-1 substrate). Once "a feature is a direction,
read by a dot product, written by a rank-1 update" is solid, ROME stops being
magic and the whole neighbour project clicks into place mechanically.

---

### T-001 · Does editing a fact ripple to its logical neighbours?

**Status:** active (the project's root question)
**Parent:** — (root)
**Opened:** 2026-07-22
**Question:** After a ROME edit (Eiffel Tower → Rome), do entailed neighbours
(country → Italy, language → Italian, reverse lookups) also update? This is the
portability/ripple problem the whole project studies.
**Answer:** — (E-002/E-003/E-004 will measure it)

---

### T-002 · What are the conditions for an IIA interchange to flip the answer?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-08-04
**Question:** When does patching SOURCE's activation into BASE flip Paris→Rome?
**Answer:** Two conditions, BOTH required: (1) the site `(L,p)` must encode the
variable in SOURCE, and (2) the same site must be READ by BASE downstream. See
`readings/metrics/notes.md` and the 2026-08-04 discussion. Off-peak `(L,p)` →
IIA collapses; that collapse is what gives the sweep its resolution.

---

### T-003 · Why do mismatched-layer patches collapse IIA?

**Status:** answered
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** If the patch layer isn't where the fact lives (or differs between
runs), what happens?
**Answer:** IIA falls toward 0. Two distinct failure signatures: INERT (BASE
still says Paris → wrong site, no signal transplanted) vs. DESTRUCTIVE (garbage
output → off-distribution injection, e.g. cross-layer patch). Layer and position
are coupled: "early" is fatal at the readout position but correct at the subject
position. Same-index interchange works because both prompts share the circuit.

---

### T-004 · How do we determine the "Rome-ness" of an activation?

**Status:** answered
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** IIA condition 1 assumes we can tell whether an activation at `(L,p)`
carries the location variable. By what measure do we establish that?
**Answer:** (2026-08-04) Causal tracing is NOT a pre-check — the intervention IS
the test, a posteriori, and it measures conditions 1∧2 together. To isolate
condition 1: (A) observationally & cheaply, before any interchange —
difference-of-means Rome-direction `v = mean(Rome) − mean(¬Rome)`, score
`s = ⟨h, v̂⟩` (also probe / DLA / logit lens); or (B) causally — run causal
tracing on the SOURCE prompt alone (corrupt Colosseum, restore (L,p), see if
Rome recovers). Catch: presence ≠ use (probing pitfall) — A is a predictor, not
a proof. DAS reconciles by learning the direction under an interchange objective
(readable AND causally certified). Recipe: diff-of-means pre-filter → confirm
with IIA at high-scoring sites. Spawned T-007.

---

### T-005 · How do we verify what BASE downstream actually consumes?

**Status:** open
**Parent:** T-002
**Opened:** 2026-08-04
**Question:** IIA condition 2 requires that a site is READ by downstream layers.
How do we check consumption directly rather than inferring it from the flip?
Candidate methods: path patching, attention knockout on the edges out of `(L,p)`,
or ablating the site and watching which downstream components change.
**Answer:** —

---

### T-006 · Is "downstream consumption" itself a kind of neighbour?

**Status:** open
**Parent:** T-005
**Opened:** 2026-08-04
**Question:** A downstream component that READS from the edited site is
structurally the same relationship as a neighbour fact that depends on the
edited fact. If so, the ripple problem (T-001) and the consumption question
(T-005) are the same question at two levels — representational and logical.
Does the mechanistic "who reads this site" map onto the logical "which facts
entail this one"? If they line up, the causal graph over activations IS the
entailment graph over facts — which would be the deep result of the project.

**Framing (2026-08-09) — the two-graphs distinction (project core):**
There are TWO graphs, and "neighbour" lives in only one of them.
- ENTAILMENT graph — facts and their logical relations (Eiffel→Rome ⇒ →Italy ⇒
  →Italian). Human/logical, MODEL-INDEPENDENT. "Neighbour" is defined here.
- MODEL graph — directions, layers, positions, read-paths, circuits.
  MODEL-SPECIFIC (size/config/training decide the organisation).
"Neighbour" is a concept we IMPOSE from the entailment graph onto the model
graph, then ask empirically: is that adjacency reflected in the internals (same
direction? same site? same read-path?). Not guaranteed — it is a per-model
measurement, and that measurement is the whole project.

Model-specific ≠ arbitrary: linear representation (T-011), MLP fact-locality
(T-012), and universality are regularities that give priors and make portable
methods (ROME, probing) work across models at all. Residual stream + causal
interventions are the INSTRUMENT that projects our fact-notion into the model's
space to test the correspondence.

Both/and on the unit: the unit of MEASUREMENT is per-neighbour (portability —
"did the country update?"); the object of EXPLANATION is the internal
correspondence (why, in terms of shared directions/sites/read-paths).

**The project in one line:**
> Ripple success = the two graphs ALIGN at that fact. Ripple failure = the facts
> are logical NEIGHBOURS but representational STRANGERS — adjacent in meaning,
> unconnected in the model.

Says why it's hard (logical adjacency need not be built into the weights), what
we measure (whether it is, per fact), and what a fix requires (make the
entailment edges CAUSALLY REAL in the model, not just true in the world).

**Answer:** — (thesis-level; resolved only by the full portability + IIA study)

---

### T-008 · Where does rome-neighbors diverge from MEMIT, exactly?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-08-04
**Question:** MEMIT scales editing to thousands of facts — where is our project's
contribution distinct from it?
**Answer:** (2026-08-04) MEMIT scales BREADTH (independent (s,r,o) points, one
key-value constraint each; localize once per model, batch least-squares with a
covariance preservation term). It has no representation of relations between
facts. rome-neighbors is orthogonal: DEPTH — the consistency of a single edit
across its entailment edges (portability/ripple), the metric MEMIT ignores. We
use ROME/MEMIT as the edit PRIMITIVE and ask the question it never poses: when
you write one fact, which others must change, and does the edit reach them? We
diverge at the exact point MEMIT declares success — its efficacy+locality is
satisfied by an edit that produces a ripple failure. Scaling challenge on our
side is not "more facts" but "know each fact's neighbours at scale" →
`counterfactual_gen` (Wikidata entity-graph expansion). Connects to T-006
(activation-read graph ?= fact-entailment graph) and the AGM/KG vision.

---

### T-007 · Does the diff-of-means "Rome-ness" score predict IIA?

**Status:** open
**Parent:** T-004
**Opened:** 2026-08-04
**Question:** Empirical test of the presence-vs-use gap. Compute the
difference-of-means Rome-ness score `s = ⟨h, v̂⟩` at every `(L,p)`, then measure
IIA at every `(L,p)`. Do they correlate? The interesting cells are HIGH score /
LOW IIA — sites where the location is decodable but causally unused. Those
decodable-but-unused sites may be exactly what explains why ripple edits fail
(a neighbour reads a "copy" the edit never touched). Concrete experiment,
combines a probe sweep (Family 2) with an interchange sweep (Family 1).
**Answer:** —

---

### T-009 · What does `.source` operation-level access give us on GPT-J?

**Status:** active (E-006 spike)
**Parent:** T-005
**Opened:** 2026-08-09
**Question:** `.source` reads a module's forward() source and exposes each
operation inside it as a hook point — finer than the module-boundary
`.output`/`.input` used so far. What operations does it actually expose on
GPT-J-6B, and can we reach non-boundary intermediates (esp. attention softmax
weights)? Op names are model-specific → discover, don't guess. Directly unlocks
the deferred attention-maps work (attention pattern lives inside attn.forward,
not at a boundary), which is a method for T-005 (verifying downstream
consumption via attention knockout).
**Answer:** (2026-08-09, partial) `.source` works and is trustworthy on GPT-J.
09 mapped the op names; 10 confirmed capture (attn weights reachable at
`attn.source.self__attn_0.output[1]` = `[1,16,seq,seq]`) and that source-op ==
module-boundary up to fp16 noise. Two gotchas learned → memory. 12 ran (attn
patterns, all 28 layers, head-averaged): dominant ATTENTION SINK on token 0
(`The` 0.6–0.88 throughout) preserves the last-position residual; the lookback
to "Eiffel" (iff/el) emerges in layers ~16–24 (peak 0.18 @ L20) and the sink
DIPS exactly there (0.59) — retrieval competes with the sink for attention mass.
Three experiments now converge: STORE (subj, early, 03) → READ OUT (last tok,
~12–17, 08) → LOOK BACK to subject (~16–24, 12). Still open: 13 (MLP vs attn
ablation) and per-head isolation → T-010.

---

### T-010 · Which specific head(s) perform the Eiffel-lookback?

**Status:** active (E-006, script 12b)
**Parent:** T-009
**Opened:** 2026-08-09
**Question:** The 0.18 subject attention in 12 is averaged over 16 heads — the
real lookback head is likely attending at ~0.5–0.8, diluted 16×. Build a
per-head `[layer × head]` heatmap of last-position attention to the full subject
span (positions 1–4, not just Tower — 12's subj detection missed the subword
pieces). Isolate the head(s) doing the retrieval; that pins down where the
lookback circuit lives, invisible in the head-average.
**Answer:** —

---

## Direction decision (2026-08-22) — after weak predictor results

**State:** raw distance fails (template-washout / faint last-token signal);
structured alignment (as implemented) doesn't beat it (E-011/E-011b). The measure
we hoped for — "predicts editable, structure-preserving, precise neighbour edits"
— is not found yet.

**Diagnosis (the key insight):** every experiment so far measures a PROXY
(type-separation of prompt geometry on the UNEDITED model), not the real target
(per-neighbour, per-edit PROPAGATION). We've tuned predictors with no ground
truth. Plus construct issues: whole-prompt cosine is template-dominated (not fact),
and type-averaging discards per-instance signal.

**Candidate directions (user chooses):**
- **T-A** get the causal OUTCOME first (E-010: edit or interchange → per-neighbour
  propagation labels) → then measure predictors against truth. ← PREREQUISITE / rec.
- **T-B** represent the FACT not the prompt: subject-token reps, edit difference
  vector (new−old) + do neighbours lie along it, Kim bilinear, DAS direction.
- **T-C** capacity: GPT-J (NDIF) / stronger local (capacity tripled signal: .06 vs .02).
- **T-D** right unit: per-edit binary outcome + logistic regression (design's
  actual spec), not type-averaged cosine.
A makes B/C/D measurable → honest sequence is A first.

---

## Foundations threads (gaps to lock)

### T-011 · Linear representation: features = directions, read by dot product, written by rank-1

**Status:** open (recommended next — the floor under ROME)
**Parent:** — (foundations; underlies T-004, T-008, and all of model editing)
**Question:** Lock the Tier-1 substrate that everything else borrows against.
Three linked ideas, each with a small concrete demo:
(a) a feature is a DIRECTION in activation space (linear representation hypothesis);
(b) the model READS a feature by projecting onto that direction — a dot product
    (this is what a probe, DLA, and the diff-of-means "Rome-ness" of T-004 all do);
(c) ROME WRITES a fact as a rank-1 update `ΔW = v kᵀ` added to an MLP weight —
    what does that actually do to the matrix, and why is it "one direction in,
    one direction out"?
Success: can explain, with a toy example, what a dot product reads, what
diff-of-means computes, and what a rank-1 update writes.
**Answer:** —

---

### T-012 · Why do facts live in the MLP? (key-value memory view)

**Status:** open
**Parent:** T-008
**Opened:** 2026-08-09
**Question:** We know facts live in the MLP (ROME) but not the mechanism.
Geva et al.: MLP `fc_in` rows act as KEYS (detect an input pattern), `fc_out`
columns as VALUES (write an output); a fact = a key(subject) → value(object)
association. Understand `fc_in → act → fc_out` concretely — this is exactly the
site ROME edits and what script 13 (MLP vs. attn ablation) probes.
**Answer:** —

---

### T-013 · Positional encoding / RoPE

**Status:** open
**Parent:** — (foundations, Tier 2)
**Opened:** 2026-08-09
**Question:** `apply_rotary_pos_emb` appeared in the `.source` dump (09) and we
skipped it. How does RoPE encode position by ROTATING the Q/K vectors, and why
does rotation give *relative* position in the QKᵀ dot product? Unexercised
Tier-2 basic; matters for reasoning about what attention actually compares.
**Answer:** —

---

### T-014 · Run the causal experiments end-to-end (doing ≠ reading)

**Status:** active
**Parent:** T-001
**Opened:** 2026-08-09
**Question:** `04` (causal tracing / AIE) and the IIA neighbour test have not
been RUN. Seeing the AIE peak land at the subject/mid-layers, and an IIA flip
happen, yourself — is a different and more concrete "basic" than understanding
them on paper. Run `04`, `12b`, `13`; read the peaks against the store→readout
→lookback synthesis. (`04` is fixed and queued; `13` is written.)
**Answer:** —

---

## Thread tree

```
T-001 ripple/portability (root)
├─ T-008 divergence from MEMIT (breadth vs depth) . answered
├─ T-002 IIA flip conditions ...................... answered
│  ├─ T-003 mismatched-layer collapse ............. answered
│  ├─ T-004 determining "Rome-ness" ............... answered
│  │  └─ T-007 does Rome-ness score predict IIA? .. OPEN  ← concrete experiment
│  └─ T-005 verifying downstream consumption ...... OPEN
│     ├─ T-006 consumption-as-neighbour ........... OPEN  ← the deep one / project thesis
│     └─ T-009 .source op-level access (E-006) .... active (partial)
│        └─ T-010 which head does the lookback? ... active  ← 12b per-head

FOUNDATIONS track (basics under the research tree)
T-011 directions / dot product / rank-1 ........... OPEN   ← recommended next; floor under ROME
T-012 MLP as key-value memory ..................... OPEN
T-013 positional encoding / RoPE .................. OPEN
T-014 run 04 / 12b / 13 end-to-end (doing≠reading)  active
```
