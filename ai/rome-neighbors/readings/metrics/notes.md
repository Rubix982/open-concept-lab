# Interpretability & Editing Metrics — Reference Notes

_A map of the metrics used in mech-interp and model editing, organised by the
QUESTION each one answers. IIA is one metric in the localization family; this
note places it in context._

The three questions:

1. **Where does the knowledge live?** → localization metrics (IIA, AIE, patching…)
2. **Is the information present at all?** → decodability metrics (probing, DLA…)
3. **Did my edit succeed and stay clean?** → editing-quality metrics (efficacy,
   locality, portability…)

---

## Family 1 — Localization: "where does the knowledge live?"

All intervene causally and measure the effect on the output. This is IIA's family.

### IIA — Interchange / Indirect Intervention Accuracy

The core causal localization metric. Answers: *does a specific
`(layer, position)` carry a specific piece of information?*

Mechanic — an **interchange** between two real runs:

```
BASE   run:  "The Eiffel Tower is in the city of"   → wants "Paris"
SOURCE run:  "The Colosseum is in the city of"      → wants "Rome"

Patch:  copy the activation at (layer L, position p) from SOURCE into BASE.
Ask:    did BASE's output flip from "Paris" to "Rome"?
```

If the flip happens, that site **carries the location variable**.

```
IIA = (# interventions where output flipped to the SOURCE answer)
      / (# total interventions)
```

- IIA = 1.0 → patching here reliably transplants the fact.
- IIA ≈ 0   → this site does not carry it.

Most principled of the causal metrics: both runs are real and in-distribution —
nothing is destroyed or noised.

### AIE — Average Indirect Effect (ROME's causal tracing)

Corrupt the subject with noise, restore one clean `(layer, position)`, measure
how much the correct-answer probability RECOVERS. Average over many facts → a
heatmap peaking at the storage site. This is IIA's corrupt-restore cousin, and
it is what `experiments/.../04_causal_tracing.py` computes.

```
recovery = (P_restored - P_corrupted) / (P_clean - P_corrupted)
   0 = restoring this site did nothing
   1 = restoring this site fully recovered the answer
```

### Activation patching (logit difference)

Patch an activation, measure the change in `logit(answer_A) − logit(answer_B)`.
Isolates the contrast between two candidate answers — finer than raw probability.

### Attention knockout

Zero specific attention EDGES (token A can't attend to token B); measure the
effect. Localizes ROUTING, not storage. (The lookback paper used this to show
belief info flows subject → state token.)

### Path patching

Patch along a specific path between components to find which CIRCUIT carries the
signal, not just which layer.

### DAS — Distributed Alignment Search

Learn a rotation into a subspace, then run IIA INSIDE that subspace. Handles
variables that are not axis-aligned but live in a linear combination of neurons.

---

## Family 2 — Decodability: "is the information present at all?"

No intervention — read activations and ask whether the info is recoverable.

- **Probe accuracy** — train a linear classifier on activations to decode a
  variable. (Used in lookback E-001: object identity, ~80% CV.) Tells you the
  info is linearly PRESENT, not that it is USED.
- **Selectivity** — probe accuracy minus a control-task accuracy, to rule out
  the probe merely memorising.
- **Direct Logit Attribution (DLA)** — project one component's output onto the
  unembedding for the answer token: how much did THIS head/MLP push "Paris"?
  The logit lens is the whole-residual-stream version of this.

---

## Family 3 — Editing quality: "did my edit succeed and stay clean?"

The family the rome-neighbors evaluation lives in. The four editing desiderata:

| Metric | Question |
|--------|----------|
| **Efficacy / Reliability** | Did the edited fact flip to the target? (Eiffel → Rome) |
| **Generality / Paraphrase** | Do rephrasings also update? |
| **Locality / Specificity** | Did unrelated facts stay put? |
| **Portability / Ripple** | Do entailed neighbours update? (country → Italy, language → Italian) |

Plus two "did I break the model" guards:

- **KL divergence** from the base model on unrelated inputs — collateral damage.
- **Fluency / perplexity** — is generation still coherent after the rank-1 update?

---

## How they fit together for rome-neighbors

```
Family 1 (IIA, AIE)     → FIND the site where "Eiffel Tower → location" lives
Family 3 (portability)  → MEASURE whether editing that site ripples to neighbours
Family 2 (probing/DLA)  → DIAGNOSE why: is the country decodable from the edited
                          representation, or stored separately?
```

The headline result of the project is a **portability** number (Family 3): how
many neighbour types update after an edit. The *interesting* contribution is
using **IIA** (Family 1) to explain WHY portability is low — showing the
neighbour facts are not causally wired to the edited representation.

**The IIA neighbour test (the experimental heart of the project):**

```
BASE:   "The Eiffel Tower is in the country of"   → wants "France"
SOURCE: "The Colosseum is in the country of"      → wants "Italy"
Patch the LOCATION representation from SOURCE into BASE.
```

- BASE flips to "Italy" → the country neighbour READS FROM the location
  representation. A city edit *should* ripple; if it doesn't after ROME, the
  edit failed to write into that shared representation.
- BASE does NOT flip → the country is stored SEPARATELY from the city. This is
  the mechanistic signature of the ripple failure: the neighbour never reads
  from the edited site, so no weight edit there could ever propagate.

---

## Caveat — localization metrics can disagree

There is an active debate ("activation patching can be misleading", Hanna et al.;
the localization-vs-editing gap, Hase et al.) that a site with high AIE/IIA is
not always the best site to EDIT. Patching measures where information IS; editing
needs where it is WRITTEN. That gap is itself a live research question and is
worth flagging in any write-up.

---

_Discussed and drafted: session of 2026-07/08. Companion to the scratch
exploration scripts (logit lens, residual stream, ablation, causal tracing)._
