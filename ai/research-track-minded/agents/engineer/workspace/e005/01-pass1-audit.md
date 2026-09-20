# E-005 · Pass 1 on a design document

Target: a T-075 design section for `edit-slice/design.md` — does the subject-key
pinning hold at layers other than 5?

## The pass does not fit, and the reason is structural

`SKILL.md` Pass 1 asks, per paragraph: *what observation would make this false?*
A design has **no results**. Its assertions are about what will be measured, and
"we will sweep seven layers" is not the kind of thing that can be false.

E-003 found Pass 1 assumed a draft existed. That was an ordering problem and could
be patched by running the audit forward over claims. **This is a different
defect:** a design document has no claims to audit at all. The adaptation is not a
re-ordering, it is a different question.

**What a design has instead is load-bearing assumptions.** The productive
substitution:

> *If this assumption is wrong, does the experiment still measure what it claims?*

An assumption that survives being wrong is fine. One that does not is a confound,
and it has to be controlled before the ticket opens. That question does the same
job Pass 1 does on prose — it separates the load-bearing from the decorative — but
it is not the same question.

## The audit

| # | Load-bearing assumption | If wrong, does the experiment survive? | Control |
| --- | --- | --- | --- |
| A1 | With `u = k*`, the coefficient reduces to `(k·k*)/(k*·k*)` — pure key geometry, no edit required | **No.** If an edit were needed the cost model collapses and this stops being cheap | Derivation is one line; verify numerically against one edited run at layer 5, where [E-017]'s answer is already known |
| A2 | `k*` must be recomputed per layer — the subject's key is a different vector at each depth | **No.** Reusing layer 5's `k*` at layer 20 measures nothing | Recompute per layer; assert the layer index in the artifact |
| A3 | A coefficient near 1 indicates *subject-specific* pinning | **No — and this is the hole.** If unrelated probes also score ~1 at a layer, the measure has lost discrimination and a high score means nothing | **A matched different-subject control at every layer.** See below |
| A4 | Llama-3.1-8B layer 5 is representative of where ROME is applied | Survives. It is EasyEdit's shipped config; other configs are a scope note, not a confound | State the config; do not generalise past it |
| A5 | NDIF completes the run | Survives, loudly. [O-007]: rejections raise rather than corrupt | `retrying()`; assume ~50% per-call failure as a design parameter |

## A3 is the finding, and it is a gap in what was just published

[E-017]'s controls are all **same-subject**: a different relation, a late clause, a
possessive, a long preamble. All score 0.93–1.00. The only non-subject datum in the
project is `inner_2` — *"Paris is located in…"* — which is inert at −0.02.

But `inner_2` is a different *entity type* answering a different question. It is
not a matched control. Nothing in the record measures a **different person, same
relation, same form** — *"Marie Curie was born in the city of"* against a Jack
Marshall edit's `k*`.

Without it, "any prompt containing the subject receives 93–100%" is not separated
from "any prompt receives 93–100%". I believe the former is true — `inner_2` and
the [E-015] outer control both point that way — but **the clean control was never
run, and the claim as published leans on it.**

That is the strongest thing this design pass produced, and it came from A3 rather
than from any of the seven Pass 2 questions.

## Second finding: the audit ranked the design too

Same effect as E-003. Filling the table put A3 on top, which made the
different-subject control **the primary purpose of the sweep** rather than a
control attached to it. The layer question is real, but the sweep's first job is
now closing a hole in a published claim.

That is twice the audit has reordered a document by ranking rather than by
filtering. It is not a coincidence.
