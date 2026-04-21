# Visibility Lookback — Notes

The visibility lookback is the THIRD mechanism. It only fires when the
story contains an explicit visibility condition between characters.

It answers: if character A observed character B, how does that update
A's beliefs about what B did?

---

## The Core Problem

Binding + answer lookback handle:
  "What does Bob believe the bottle contains?" → beer (Bob filled it)

They cannot handle:
  "What does Bob believe the cup contains?" when Bob observed Carla

Because the binding lookback only finds state tokens where char_OI
matches the asking character. Bob never touched the cup — there is no
binding for (Bob, cup). Without visibility, answer = unknown.

The visibility lookback creates a bridge: Bob's observation of Carla
transfers Carla's state knowledge into Bob's belief representation.

---

## The Visibility ID — the Key New Concept

The visibility lookback introduces a derived representation:

```
Visibility ID = f(observer_OI, observed_OI)
              = f(Bob's char_OI, Carla's char_OI)
              = f(1, 2)
```

This is NOT Bob's OID. NOT Carla's OID.
It is a NEW vector encoding the DIRECTED RELATION between them.

  - Bob → Carla:  vis_ID = f(1, 2)  (distinct)
  - Carla → Bob:  vis_ID = f(2, 1)  (different from above)

The visibility ID is used as a pointer to look up the observed
character's state and write it into the observer's belief.

---

## Three Experiments

### 1. Source
**What is patched:** the visibility source token — the observed character's
OI as it appears in the visibility sentence.
**Question:** when does swapping the observed character's OID in the
visibility sentence change the answer?

**Results:**
```
Layers 0-9:   IIA < 0.3   — source OID not yet encoded
Layer 10:     IIA = 0.76  — sharp rise
Layers 12-17: IIA = 0.95-0.97 — peak, source fully active
Layer 22:     IIA = 0.81
Layer 24:     IIA = 0.65
Layer 25:     IIA = 0.20  — source drops off
Layers 26+:   IIA ≈ 0.0   — source consumed
```

**Peak:** layers 12–17, IIA = 0.97
**Active window:** layers 10–24

**Meaning:** the Visibility ID is being generated from the observed
character's OID at layers 10-24. This is earlier than the binding
lookback source (layers 14-19) — visibility must be set up FIRST.

---

### 2. Address and Pointer
**What is patched:** the full address+pointer activation for the
visibility lookback — both the key at the recalled token (address)
AND the query at the lookback token (pointer).

**Results:**
```
Layers 0-9:   IIA < 0.4   — not yet formed
Layer 14:     IIA = 0.95  — active
Layers 17-38: IIA = 0.97-1.00 — peak, fully active
Layers 40-51: IIA = 0.95-0.97 — sustained high
Layer 52:     IIA = 0.85  — fading
Layers 55-56: IIA = 0.50-0.14 — drops off
Layers 57+:   IIA ≈ 0.0
```

**Peak:** layers 20–38, IIA = 1.00
**Active window:** layers 10–55

This is a much WIDER window than the binding lookback's address+payload
(which was only layers 32-38). The visibility mechanism operates across
a broader layer range because it needs to:
  1. Form the Visibility ID (source → address phase)
  2. Keep it live while the observed character's state is retrieved
  3. Write the retrieved state into the observer's belief

---

### 3. Payload
**What is patched:** the actual state value being transferred — the
observed character's state flowing into the observer's belief.

**Results:**
```
Layers 0-29:  IIA ≈ 0.0   — payload not yet arrived
Layer 30:     IIA = 0.12  — beginning
Layer 31:     IIA = 0.74  — sharp rise
Layers 33-38: IIA = 0.97-1.00 — peak
Layers 40-51: IIA = 0.95-0.97 — sustained
Layer 52:     IIA = 0.85  — fading
Layers 55-56: IIA = 0.50-0.14 — drops off
Layers 57+:   IIA ≈ 0.0
```

**Peak:** layers 33–38, IIA = 1.00
**Active window:** layers 31–55

---

## The Visibility Lookback Timeline

```
Layers 10-24:  Source active (Visibility ID generated from char OIs)
               Observer's character OI + observed character OI → vis_ID

Layers 14-55:  Address+Pointer active (vis_ID co-located with observed state)
               The visibility ID is used as a pointer to look up
               the observed character's state token

Layers 31-55:  Payload active (observed character's state value flows
               into the observer's belief representation)

Layers 56+:    All visibility mechanisms consumed
               Observer's updated beliefs now in their residual stream
```

---

## Comparing All Three Lookbacks

| Mechanism | Source Window | Binding/Address Window | Payload Window |
|---|---|---|---|
| Binding lookback | L14–19 | L32–38 | N/A (→ answer lookback) |
| Answer lookback | N/A | L33–55 (pointer) | L56–79 |
| Visibility lookback | L10–24 | L14–55 | L31–55 |

Key observations:
1. Visibility fires EARLIEST — layers 10-24 for source (before binding at 14-19)
2. Visibility address window is WIDEST — 45 layers vs 6 for binding
3. Visibility payload (L31-55) and answer pointer (L33-55) OVERLAP
   This is the handoff point: visibility updates the observer's state,
   then the answer pointer reads from that updated state

---

## Why This Order Makes Sense

The computation must proceed in this order:

```
1. Visibility source (L10-24):
   "Bob can observe Carla" → generate vis_ID from their OIs

2. Visibility address+pointer (L14-55):
   Locate Carla's state token using vis_ID as pointer
   Keep vis_ID live while state is being transferred

3. Visibility payload (L31-55):
   Carla's state value flows into Bob's belief representation

4. Binding lookback (L14-34):
   Now Bob's belief representation includes what Carla did
   Binding can use the updated belief to find the correct answer

5. Answer lookback (L33-79):
   Retrieve the final value from the correctly bound state
```

The visibility lookback updates Bob's beliefs BEFORE the binding
lookback reads them. The order is enforced by the layer windows.
