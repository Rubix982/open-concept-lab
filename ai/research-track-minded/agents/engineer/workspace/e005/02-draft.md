---

# Part IV — [T-075] Does the pinning hold away from layer 5?

_Designed 2026-09-20, before any run. Passes the lenses that changed; the rest are
inherited from Part I._

## The question, and why it is not the one the thread asked

[E-017] states that any prompt containing the subject receives 93–100% of the edit
vector at the subject's last token. That measurement was taken at **layer 5**, the
layer EasyEdit's `llama3-8b` ROME config edits. [T-075] asks whether it survives at
other depths: if the subject key becomes context-sensitive deeper in the network,
an editor targeting a later layer would leak less across probe forms, and
"structural" narrows to "structural at the layer this config happens to edit".

Designing it surfaced a second question that outranks it.

**Every control behind the 93–100% claim is a same-subject control.** A different
relation, a late clause, a possessive, a long preamble — all vary the *form* while
holding the subject fixed, and all score near 1. The only non-subject datum in the
project is `inner_2` (*"Paris is located in…"*), which is inert at −0.02 but is a
different entity type answering a different question, not a matched control.

**Nothing has measured a different person, same relation, same form** — *"Marie
Curie was born in the city of"* scored against a Jack Marshall edit's `k*`.

Until that runs, "any prompt **containing the subject** receives 93–100%" is not
separated from "any prompt receives 93–100%". I expect the former; `inner_2` and
[E-015]'s outer control both point that way. But the expectation rests on an
argument, and [E-016] is this project's standing demonstration that an argument
about key geometry can be confidently wrong — the cosine said whitening was a
no-op and the coefficient said it was a twentyfold change.

**[E-016]'s own anisotropy measurement is the reason to take this seriously.** The
layer-5 keys have a participation ratio of 26.5 of 2048 sampled dimensions — they
occupy an effectively ~26-dimensional manifold. Vectors confined to a narrow
subspace have substantial cosine with each other **by construction**. A
different-subject key may score far above zero for reasons that have nothing to do
with the subject, and the more anisotropic the layer, the higher that floor sits.

So the sweep has two jobs, and the control is the first of them.

## 4 · Falsification — stated in advance

Let `c_form(L)` be the mean coefficient at the subject's last token at layer `L`,
and `c_other(L)` the same quantity for a matched different-subject probe. The claim
under test is that `c_form − c_other` stays large across depth.

- **Confirm:** `c_form ≥ 0.9` at every swept layer while `c_other` stays low. The
  structural claim generalises, ROME's layer choice is incidental to it, and no
  natural probe form escapes at any depth.
- **Deny:** `c_form` falls materially — below ~0.7 — at deeper layers while
  `c_other` stays low. The claim narrows to early layers. This is a *useful* deny:
  it says an editor applied deeper would leak less across forms, which is a fact
  about where to edit, and it is the first thing in this project that would bear on
  that choice.
- **Null:** `c_form` falls **and `c_other` rises toward it**. The measure is losing
  discrimination with depth rather than the key becoming context-sensitive, and
  neither reading is licensed. Separating these two is the entire reason `c_other`
  exists.

A fourth outcome is possible and would be the most consequential: **`c_other` is
high at layer 5**. That would not narrow [E-017] — it would falsify it, because the
pinning would not be subject-keyed at all. Stated here so it cannot be discovered
and quietly reframed.

## 5 · Method & construct validity

**No edit is required, and that is what makes this cheap.** ROME's coefficient is
`(k·u)/(u·k*)`. With EasyEdit's shipped `u = k*` it reduces to `(k·k*)/(k*·k*)` —
a function of two keys and nothing else. No weights are modified, no `v*` is
computed, and the measurement is a forward pass per prompt. Verify the reduction
numerically at layer 5 against [E-017]'s recorded values before trusting it
anywhere else.

**`k*` is recomputed at every layer.** The subject's key is a different vector at
each depth; reusing layer 5's `k*` at layer 20 measures nothing. The layer index
goes into the artifact and is asserted on load.

**Layers:** 0, 3, 5, 8, 12, 16, 24, 31 of Llama-3.1-8B's 32. Denser early, where
ROME configs cluster, with two deep anchors. Eight layers, not a full sweep —
the question is a shape, not a per-layer number.

**Forms:** [E-017]'s five, unchanged, plus the different-subject control. Reusing
the exact form set is deliberate; layer 5 then reproduces published numbers and
acts as a correctness check on the harness.

**Construct validity — the thing this measure does not capture.** A coefficient is
how much of the edit vector arrives. It is not whether the arriving vector changes
the answer. [E-016] established those come apart: a ×0.27 rescale broke relocation
in 3 of 4 chains, so magnitude matters, and a coefficient of 0.93 versus 1.00 could
be behaviourally identical or not. **This sweep measures delivery, never effect.**
Any claim about what an editor at layer 20 would *do* requires running one.

## 6 · Confounds & controls

| Confound | Control |
| --- | --- |
| Anisotropy inflates all coefficients at a layer, independent of subject | `c_other`, the matched different-subject probe, at every layer. It is the floor every `c_form` is read against |
| Key norm grows with depth, so raw dot products are not comparable across layers | The ratio is scale-free in `k*` by construction; report `c_other` alongside so the floor is visible even if it moves |
| Subject tokenisation differs across chains, changing what "last subject token" means | Same 16 chains as [E-017], same `subject_last_index`; the comparison is within-chain across layers |
| A layer where the true city is not held at baseline | Does not apply. The coefficient is a property of keys and does not depend on the probe eliciting anything — the same reasoning that made [E-017] Part 2 valid on all 42 chains |

## 7 · Baseline — the dumbest explanation

**That coefficients are near 1 everywhere because keys at a given layer are all
similar.** That is not a strawman: it is what a participation ratio of 26.5 predicts
if the manifold is shared rather than subject-specific. `c_other` is precisely the
test, and if the dumb explanation holds the finding is that the coefficient measure
is uninformative at that layer — which is worth knowing and would retire it.

## 8 · Scope & feasibility

**IN:** 16 chains, 6 forms, 8 layers — 768 traces. Coefficients only.
**DEFERRED:** any edit at a non-5 layer; other models; a rate claim; whether
delivered magnitude changes behaviour at depth.

**Feasibility, with the dependency priced.** Per [O-007], NDIF rejects roughly half
of all traces with a node-dependent whitelist error. That is a **design parameter,
not an incident**: 768 traces at ~50% first-attempt success is ~1,500 calls through
`retrying()`. Batch per chain, checkpoint per layer, and make the artifact
resumable so a stall costs one layer rather than the run. Do not re-run a failure
and read the second outcome as a diagnosis — that is exactly the error [O-007]
retracts.

## 9 · Deliverable

**One figure.** Coefficient against layer, one line per probe form, with `c_other`
drawn as a shaded floor. The claim lands if the form lines sit together well above
the floor across depth, and narrows visibly wherever they converge toward it.

**One number.** The smallest `c_form − c_other` gap across all layers and forms —
the weakest point of the structural claim, which is the number an adversary will
ask for.

## 10 · Adversary — pre-emptions

- *"Your control is a different person, but people may share key structure."* Yes,
  and that is the floor being measured, not a defect. If `c_other` is high, the
  claim is weakened and the design says so in advance.
- *"Eight layers is not a sweep."* It is a shape test. A per-layer claim would need
  all 32 and is explicitly deferred.
- *"Coefficient is not behaviour."* Stated in §5. This measures delivery. Nothing
  here licenses a claim about what editing at layer 20 would do.
- *"You are proposing where to edit."* No. A deny would be a fact about leakage
  geometry. Acting on it is method work, which this project does not do.

## What this changes upstream if `c_other` is high

[E-017]'s claim, the [E-016] section of the write-up, and the standfirst all assert
subject-keyed leakage. If the control comes back high, those are wrong rather than
narrow, and the correction is a retraction rather than a scope note. **Recorded
before the run**, so the outcome cannot be reframed as having been expected.
