# BigToM Generalization — Notes

BigToM (Gandhi et al., 2024) is a real-world ToM benchmark, not synthetic.
Stories are longer, more varied in language, and not template-generated.
This section tests whether the lookback mechanisms found in CausalToM
also appear in the model's processing of real text.

---

## Why This Matters

CausalToM was designed by the paper's authors with controlled structure —
same restaurant setting, same sentence patterns, synthetic entity names.
A skeptic could argue the lookback mechanism is an artifact of that
controlled structure, not a general solution.

BigToM answers: does the same mechanism appear when the model processes
genuinely varied real-world ToM stories?

---

## What Was Tested

Three mechanism categories, same experiments as CausalToM:
- Binding lookback → pointer
- Answer lookback → pointer + payload
- Visibility lookback → source + address_and_pointer + payload

**Key difference from CausalToM experiments:** BigToM only tests the
binding_lookback/pointer and answer lookback — it does NOT have separate
character_oi, object_oi, source_1, source_2 experiments. The binding
section only has the pointer result.

---

## Results: Mechanism-by-Mechanism

### Binding Lookback Pointer

**BigToM results:**
```
Layers 0-4:   IIA < 0.3   — not yet active
Layer 5:      IIA = 0.54  — rises
Layers 9-11:  IIA = 0.90  — peak window
Layer 20:     IIA = 0.74  — plateau
Layers 30-31: IIA = 0.51  — fading
Layers 32+:   IIA < 0.3   — consumed
```

**vs CausalToM binding (character_oi):**
```
CausalToM:  peak L14-19, IIA = 0.94, active L13-28
BigToM:     peak L9-11,  IIA = 0.90, active L5-31
```

**Finding:** binding pointer is active EARLIER in BigToM (L9 vs L14).
Real text stories may have the character OID established more quickly
through richer context, or the model reads longer stories differently.
But the mechanism is clearly present — IIA reaches 0.90.

---

### Answer Lookback Pointer

**BigToM results:**
```
Layers 0-30:  IIA < 0.3
Layer 31:     IIA = 0.53
Layer 33:     IIA = 0.96  — peak
Layers 34-51: IIA = 0.89-0.93
Layer 52:     IIA = 0.53  — drops
Layers 56+:   IIA < 0.1
```

**vs CausalToM answer pointer:**
```
CausalToM:  peak L38,    IIA = 1.00, active L33-55
BigToM:     peak L33,    IIA = 0.96, active L31-51
```

**Finding:** almost identical. Layer window shifts slightly earlier
(L31-51 vs L33-55) but the shape is the same — sharp rise, flat
plateau, sharp drop. The answer pointer mechanism transfers directly.

---

### Answer Lookback Payload

**BigToM results:**
```
Layers 0-55:  IIA < 0.35
Layer 56:     IIA = 0.57  — rises
Layer 60:     IIA = 0.86
Layers 64-79: IIA = 0.93-0.96
```

**vs CausalToM answer payload:**
```
CausalToM:  active L56-79, peak L64-79, IIA = 1.00
BigToM:     active L56-79, peak L64-79, IIA = 0.96
```

**Finding:** near-identical. Same layer range, slightly lower peak
(0.96 vs 1.00) — expected given real text has more variability.
The payload mechanism is the most robust — it transfers with the
least change of any experiment.

---

### Visibility Lookback Source

**BigToM results:**
```
Layers 0-16:  IIA = 0.95-0.97  ← HIGH FROM LAYER 0
Layer 17:     IIA = 0.78       ← drops
Layer 20:     IIA = 0.54
Layer 26+:    IIA < 0.2
```

**vs CausalToM visibility source:**
```
CausalToM:  starts at 0.0, peaks at L12-17 (IIA=0.97), active L10-24
BigToM:     starts at 0.97 from layer 0, drops at layer 17
```

**This is the most striking difference in the entire BigToM analysis.**

In CausalToM: the visibility ID is BUILT UP through attention across
layers 0-12 before it becomes causal. The early layers aren't load-bearing.

In BigToM: the visibility information is causal from layer 0 — i.e.,
it is already present in the token embeddings (before any attention fires).

**Why?** Real BigToM stories express visibility in more varied, natural
language. The model may rely on the surface tokens of the visibility
sentence (the words themselves) more directly, rather than constructing
an internal representation from scratch. The embedding of "can see",
"observed", "watched", etc. may carry the visibility signal at the
input level in real text.

---

### Visibility Lookback Address and Pointer

**BigToM results:**
```
Layers 0-16:  IIA = 0.95-0.97  ← HIGH FROM LAYER 0 (same as source)
Layer 17:     IIA = 0.82        ← drops
Layer 20-22:  IIA = 0.66-0.69  ← dip
Layers 23-26: IIA rises back to 0.96
Layers 26-79: IIA = 0.96-0.97  ← HIGH THROUGH ALL REMAINING LAYERS
```

**vs CausalToM address+pointer:**
```
CausalToM:  active L10-55, dips in L17-20, back to 1.0 by L26
BigToM:     same dip pattern! Active L0-79 (never fully drops)
```

**Finding:** The dip at layers 17-22 appears in BOTH datasets.
This is the gap region from the paper (layers 24-31 in CausalToM
where source has dropped but payload hasn't arrived yet).
In BigToM it appears earlier and resolves the same way.
The sustained high IIA through all 80 layers suggests the visibility
information is woven into the entire computation in real text.

---

### Visibility Lookback Payload

**BigToM results:**
```
Layers 0-24:  IIA ≈ 0.10  (baseline)
Layer 25:     IIA = 0.36
Layer 26:     IIA = 0.71
Layer 29:     IIA = 0.95
Layers 29-79: IIA = 0.95-0.97  ← stays high to final layer
```

**vs CausalToM visibility payload:**
```
CausalToM:  active L31-53, drops after L55
BigToM:     active L29-79, NEVER DROPS — stays at 0.97 through layer 79
```

**Finding:** In BigToM, the visibility payload arrives slightly earlier
(L29 vs L31) and — crucially — stays maximal through the final layer,
unlike CausalToM where it drops off at layer 55. This may reflect that
in real text, the visibility update is more deeply integrated and persists
all the way through the model rather than being consumed by a specific
handoff point.

---

## Summary Comparison Table

| Mechanism | CausalToM Active Window | BigToM Active Window | Match? |
|---|---|---|---|
| Binding pointer | L13–28 | L5–31 | ✓ overlaps, earlier in BigToM |
| Answer pointer | L33–55 | L31–51 | ✓ same shape, slightly earlier |
| Answer payload | L56–79 | L56–79 | ✓ exact match |
| Vis source | L10–24 | L0–16 | △ present earlier, drops earlier |
| Vis addr+ptr | L10–55 | L0–79 | △ broader, present from start |
| Vis payload | L31–53 | L29–79 | △ arrives same time, never drops |

---

## Key Finding: What Generalizes and What Differs

**What generalizes perfectly:**
- Answer lookback (both pointer and payload) — nearly identical layer windows
- The handoff structure: pointer drops, payload rises at same transition

**What shifts but still generalizes:**
- Binding pointer — same mechanism, slightly earlier (~4-5 layers)
- Visibility payload arrival — same timing, but persists longer

**What looks fundamentally different:**
- Visibility source — encoded at layer 0 in BigToM, built up in CausalToM
- This suggests real text visibility cues are processed differently than
  synthetic template text. The mechanism exists in both, but the entry
  point differs.

**The paper's claim holds:** the lookback mechanism generalizes to BigToM.
But the generalization is not perfectly uniform — the answer lookback
transfers cleanly, while the visibility mechanism shows the model
using a different entry point (embeddings vs. attention construction).
