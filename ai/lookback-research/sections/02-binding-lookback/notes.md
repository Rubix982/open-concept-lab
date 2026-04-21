# Binding Lookback — Notes

The binding lookback is the FIRST of the three lookback mechanisms.
It answers: given a question about what character C believes object O contains,
which state token is the answer?

It does this by co-locating character OI and object OI inside the state token's
residual stream, then using the question token as a pointer to retrieve them.

---

## The Core Problem

The model reads this story:
```
Bob fills the bottle with beer.
Carla fills the cup with coffee.
Q: What does Bob believe the bottle contains?
```

The model must find the state token ("beer") that belongs to:
  - the first character (Bob, char_OI=1)
  - the first object (bottle, obj_OI=1)

Without binding, the model has no systematic way to connect these.
With binding, the state token carries both OIs — a composite index.

---

## IIA — The Measurement

Every experiment in the notebook measures IIA:

```
IIA (Interchange Intervention Accuracy):

  1. Take two stories: clean and counterfactual
     (e.g., sentence order reversed, different characters)
  2. Run both through the model
  3. Patch one specific activation from counterfactual into clean
  4. Measure: does the output now match the counterfactual's answer?

  IIA = 1.0 → always flips → this activation IS the mechanism
  IIA = 0.0 → never flips → this activation is NOT part of the mechanism
```

IIA is stronger than correlation. It proves causality by intervention.

---

## The 6 Experiments and What Each Tests

### 1. address_and_payload
**What:** patch state token activations (positions 155, 156, 167, 168) from
counterfactual into clean run at layer L.

**Question:** does swapping the state token's content at layer L flip the answer?

**Peak:** layer 34, IIA = 0.97

**Meaning:** by layer 34, the state token's residual stream IS the binding.
It carries enough to determine the answer. Before layer 34 — not yet.
After layer 38 — binding has moved downstream, no longer in state token.

---

### 2. character_oi
**What:** patch the character token's activations from counterfactual into clean.

**Question:** does swapping the character's OID at layer L change the answer?

**Peak:** layers 14–19, IIA = 0.90–0.94

**Meaning:** the character OID is most causally active in layers 14–19.
This is when the model is reading and encoding "who is the first character."

**Notable:** IIA settles at ~0.50 for layers 30-79. This is baseline —
the character name in the question still matters for surface reasons, but
the OID mechanism has already fired and been consumed.

---

### 3. object_oi
**What:** patch the object token's activations from counterfactual into clean.

**Question:** does swapping the object's OID at layer L change the answer?

**Peak:** layers 27–34, IIA = 0.97–1.00

**Meaning:** the object OID is written and read LATER than the character OID.
Character binding happens first (layers 14-19), object binding follows (27-34).
This suggests a sequential process, not simultaneous.

---

### 4. pointer_character
**What:** patch the QUESTION character token (position -8, -7 from end)
from counterfactual into clean.

**Question:** does swapping the pointer at the question character token flip the answer?

**Peak:** layers 14–19, IIA = 1.00 (exactly perfect)

**Meaning:** the pointer is written into the question token at the exact same
layers the source OID is being assigned (14-19). The model writes the pointer
and the address simultaneously from the same source.

**Sharp dropoff:** IIA = 0 by layer 34. The pointer has been consumed —
the lookup has already happened by then.

---

### 5. pointer_object
**What:** patch the QUESTION object token (position -5, -4 from end).

**Peak:** layers 17–29, IIA = 0.89–0.94

**Meaning:** object pointer is live slightly later than character pointer,
matching the object OID timeline. Both pointer and OID move together.

---

### 6. pointer_charac_and_object (both together)
**What:** patch BOTH question character and object tokens simultaneously.

**Peak:** layers 17–25, IIA = 0.91–0.93

**Meaning:** confirms the two pointers work as a composite key.
Patching both together gives similar accuracy to patching each separately —
they are independent signals, not redundant.

---

### 7. source_1 (with frozen state tokens)
**What:** patch character + object source tokens from counterfactual, but
FREEZE state tokens from clean run (prevent them from updating).

**Peak:** layers 20–34, IIA = 0.86–0.93

**Meaning:** swapping who is the first/second character+object correctly
changes the binding — but ONLY when the state tokens are protected.
This proves the binding flows: source → address in state token.

---

### 8. source_2 (without frozen state tokens)
**What:** same as source_1 but state tokens allowed to update freely.

**Peak:** never above 0.16

**Meaning:** without protecting the state token, the counterfactual's
source tokens corrupt the state binding, cancelling the effect.
Confirms that state tokens are the binding destination, not incidental.

---

## The Complete Temporal Pipeline

```
Layers 0–13:   Nothing causal yet — OIDs not yet assigned

Layers 14–19:  Character OID assigned at source token (char_oi peak: 0.94)
               Character pointer written into question token simultaneously
               (pointer_character IIA = 1.00 — exactly perfect)

Layers 17–29:  Object OID assigned at source token (object_oi peak: 1.00)
               Object pointer written into question token (pointer_object: 0.94)
               Both pointers live together (pointer_charac_and_object: 0.93)

Layers 20–34:  Source OIDs propagating to state token (source_1: 0.93)
               State token accumulating address alongside payload

Layer 34:      Binding COMPLETE (address_and_payload IIA = 0.97)
               State token now carries: char_OI + obj_OI + payload (state value)

Layers 34+:    All pointers drop to 0 — lookup has fired, mechanism consumed
               State token binding starts degrading (moving downstream)
```

---

## Key Insight: Sequential Not Simultaneous

Character OID peaks at layers 14-19.
Object OID peaks at layers 27-34.
They are staggered by ~10 layers.

This means the model processes character binding before object binding.
The two-part composite key is not assembled in one step —
it is built incrementally across layers.

---

## Why source_2 Flatlines

source_2 (IIA never above 0.16) is the control condition.
It shows what happens if you swap the source OIDs but let the
state tokens update naturally from those swapped sources.

The result: the swap propagates to the state tokens too, which means
the binding stays internally consistent but now points to the wrong
answer (the counterfactual's answer from a different character ordering).
The model just answers consistently from the new configuration.

The IIA stays low because the counterfactual's state tokens and the
clean state tokens both update to match their own character/object OIDs.
Only by freezing the state tokens (source_1) do you isolate the
source-to-address pathway and see the mechanism clearly.
