# Answer Lookback — Notes

The answer lookback is the SECOND of the three lookback mechanisms.
It picks up exactly where the binding lookback finishes.

Binding lookback answered: which state OI is the answer?
Answer lookback answers:   given the state OI, what is the actual state value?

---

## What Changes Between the Two Lookbacks

After the binding lookback completes at layer 34, the answer token
(the final token in the sequence) holds a state OI — the handle
pointing to the correct state token ("beer", "coffee", etc.).

But the answer token doesn't have the VALUE yet. It has the INDEX.
The answer lookback converts that index into the actual retrieved value.

```
Binding lookback output:  answer token holds state_OI = 2
                          (meaning: look at the second state token)

Answer lookback input:    state_OI = 2 used as a query pointer
Answer lookback output:   the value from state token 2 ("coffee")
                          arrives in the answer token's stream
```

---

## The Two Experiments

### Experiment 1 — Pointer
**What is patched:** the final token's full activation at layer L
**Counterfactual:** reversed sentence order + different state values
**Question:** does swapping the final token's activation flip the answer?

**Results:**
```
Layers 0-32:  IIA = 0.0   — pointer not yet formed
Layer 33:     IIA = 0.54  — pointer beginning to form
Layer 34:     IIA = 0.93  — pointer active (binding just completed!)
Layers 38-51: IIA = 0.97-1.00 — pointer at full strength
Layer 54:     IIA = 0.53  — pointer fading
Layers 56+:   IIA = 0.0   — pointer consumed
```

**Peak:** layer 38, IIA = 1.00
**Active window:** layers 33–55

**Meaning:** the final token's residual stream carries the state OI
(the pointer) from layers 34-55. Patching it redirects which state
token gets attended to, changing the answer.

---

### Experiment 2 — Payload
**What is patched:** also the final token's activation at layer L
**Counterfactual:** `get_answer_lookback_payload` — the clean story
asks about a character who cannot see the other's object (answer=unknown),
while the counterfactual carries the state VALUE that should be retrieved.
**Question:** does swapping the final token's activation inject the
correct state value?

**Results:**
```
Layers 0-52:  IIA = 0.0   — payload not arrived yet
Layer 53:     IIA = 0.19  — payload beginning to arrive
Layer 56:     IIA = 0.80  — payload flowing in
Layer 64:     IIA = 1.00  — payload fully present
Layers 64-79: IIA = 1.00  — payload stays high to final layer
```

**Peak:** layers 64-79, IIA = 1.00 (stays maximal to the end)
**Active window:** layers 56–79

**Meaning:** the actual state value ("beer", "coffee") flows into the
final token's residual stream from layers 56 onward. By layer 64 it
is fully settled and stays that way through the final layer.

---

## The Handoff: Pointer Drops as Payload Rises

The most important observation in this notebook:

```
Layer:    30   34   38   44   50   54   56   60   64   70   79
Pointer:  0.0  0.9  1.0  0.9  0.9  0.5  0.1  0.0  0.0  0.0  0.0
Payload:  0.0  0.0  0.0  0.0  0.0  0.0  0.8  0.9  1.0  1.0  1.0
```

The pointer (state OI) is consumed between layers 55-56.
The payload (state value) arrives at layers 55-56.
They do not overlap significantly. This is a HANDOFF.

Interpretation:
  - Layers 34-55: answer token holds the pointer (state OI)
                  and uses it to attend to the right state token
  - Layers 56-79: attention fires, state value flows into answer token
                  pointer no longer needed — it has done its job

---

## Connection to Binding Lookback: Sequential Chaining

```
Binding lookback:              completes at layer 34
                               → answer token now has state_OI

Answer lookback pointer:       starts at layer 34
                               → picks up state_OI, uses it as query

Answer lookback payload:       arrives at layer 56
                               → state value flows in, answer ready
```

The two mechanisms are a chain. The output of binding (state_OI)
is the input of answer lookback. There is zero gap between them —
binding completes at exactly the layer the answer pointer begins.

This is evidence of a learned computational pipeline, not coincidence.

---

## Why the Payload Stays High Through Layer 79

The pointer drops to zero — it has been consumed.
The payload stays at IIA=1.0 through the final layer.

This makes sense: once the state value is written into the answer
token's residual stream, it stays there. Nothing overwrites it.
The residual connection preserves it all the way to the output.
The answer token is now ready to generate the correct token.

---

## Summary Table

| Experiment | What is patched | Peak IIA | Peak Layer | Active Window |
|---|---|---|---|---|
| Pointer | Final token activation | 1.00 | 38 | layers 33–55 |
| Payload | Final token activation | 1.00 | 64–79 | layers 56–79 |

Both patch the same token (final). Different counterfactuals isolate
different phases of the same mechanism.
