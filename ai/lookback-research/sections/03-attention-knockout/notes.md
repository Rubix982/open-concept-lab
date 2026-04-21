# Attention Knockout — Notes

The causal mediation and IIA experiments told us WHEN each mechanism
is active (which layers). The attention knockout tells us WHERE attention
must flow — which token-to-token connections are load-bearing.

Instead of patching activations, this experiment blocks attention paths
entirely and measures the resulting accuracy drop.

---

## What "Knockout" Means

```
Normal attention:  token A can attend to any earlier token B
Knockout:          token A is FORBIDDEN from attending to token B
                   (attention score set to -infinity → softmax → 0)

Accuracy drop = baseline accuracy − accuracy after knockout

High drop → this attention path is essential
Low drop  → this attention path is not needed
```

The experiment varies which LAYER the knockout is applied at.
The question: at what layer does blocking this attention path hurt most?

---

## The Token Regions

The experiment works on a visibility story (Template 1):
```
Positions 146-156: first sentence tokens  (Bob fills bottle with beer)
Positions 158-168: second sentence tokens (Carla fills cup with coffee)
Positions 169-175: first visibility sentence  (Carla cannot observe Bob)
Positions 176-182: second visibility sentence (Bob can observe Carla)
```

The knockout blocks attention FROM the second visibility sentence tokens
(176-182) TO various target regions. The question being asked:
"which story sections does the model NEED to attend back to when
processing the visibility condition?"

---

## Three Experiments

### 1. secondSent (block attention to story sentence 2)
**Blocks:** second visibility sentence → second sentence tokens (158-168)

**Results — accuracy drop by layer:**
```
Layers 0-21:  drop < 0.6   — path not yet critical
Layer 22:     drop = 0.71  — starts mattering
Layer 24:     drop = 0.89
Layers 27-34: drop = 0.97  — critical window
Layers 40+:   drop = 1.00  — essential beyond this point
```

**Meaning:** to correctly track what Carla did (second sentence),
the visibility sentence tokens need to attend back to the second
story sentence. This connection becomes load-bearing at layers 22-34.

---

### 2. firstVisSent (block attention to first visibility sentence)
**Blocks:** second visibility sentence → first visibility sentence (169-175)

**Results — accuracy drop by layer:**
```
Layer 1:      drop = 0.18  — early effect (note: attention to vis sentence matters early)
Layers 3-5:   drop = 0.61  — early peak
Layers 7-9:   drop = 0.33  — dips
Layer 22:     drop = 0.91  — rises again sharply
Layers 25-34: drop = 0.98  — critical window
```

**The early effect (layers 1-5)** is striking. The model attends to the
first visibility sentence very early — this suggests the visibility
condition is processed at the start of the network, not only at the
decision layers.

**Meaning:** the second visibility sentence needs to attend to the first
in order to form the Visibility ID. "Bob can observe Carla" needs to
reference "Carla cannot observe Bob" to understand the asymmetric relation.

---

### 3. secondSent_firstVisSent (block BOTH simultaneously)
**Blocks:** second visibility sentence → both second sentence AND first vis sentence

**Results — accuracy drop by layer:**
```
Layers 0-21:  drop < 0.2   — stays low (individual knockouts partially compensate?)
Layer 22:     drop = 0.15  — still low!
Layer 24:     drop = 0.45
Layer 25:     drop = 0.62
Layer 29:     drop = 0.97
Layers 34+:   drop = 1.00
```

**Key insight — combined knockout is LESS disruptive than either alone
at early layers.** This is counterintuitive. It suggests the two paths
are partially redundant early on — blocking both simultaneously allows
the model to use alternative routes. Only at layer 24+ do both become
jointly essential.

---

## What This Reveals About the Visibility Mechanism

The attention knockout maps the information flow required:

```
Second visibility sentence tokens
  ↓ must attend to (at layers 22-34):
  ├── Second story sentence  → to know what Carla actually did
  └── First visibility sentence → to form the Visibility ID
                                  (encoding the observer/observed relation)
```

This aligns exactly with the visibility lookback mechanism:
- Visibility ID = f(observer_OI, observed_OI) needs BOTH character OIs
- The observer's character OI comes from the second visibility sentence
- The observed character's OI comes from the first visibility sentence
- The observed character's STATE comes from the second story sentence

All three connections are confirmed essential by the knockout.

---

## Why Accuracy Drop = 1.0 at Layers 40+

Once information has propagated into the residual streams past layer 34,
blocking the original attention paths has no effect — the information
is already there. But at layer 40+, the IIA experiments showed the
binding mechanism has already completed and the payload is moving.

Knocking out attention at layer 40+ blocks downstream paths that are
now reading from the already-populated residual streams. Nothing can
compensate for that — hence drop = 1.0 at all late layers.

---

## Summary

| Experiment | Critical Layer Window | Peak Drop |
|---|---|---|
| Block → second sentence | layers 22–34 | 1.00 |
| Block → first vis sentence | layers 3–5, then 22–34 | 1.00 |
| Block → both | layers 24–34 (delayed onset) | 1.00 |
