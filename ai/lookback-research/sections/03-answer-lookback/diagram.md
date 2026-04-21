# Answer Lookback — Diagrams

## 1. Answer lookback in context — what it receives and produces

```mermaid
flowchart TD
    subgraph "Binding Lookback Output (Layer 34)"
        BL["Answer token receives:\nstate_OI = 2\n(points to second state token)"]
    end

    subgraph "Answer Lookback — Pointer Phase (Layers 34–55)"
        P["Answer token uses state_OI=2\nas attention QUERY\n\nScans story state tokens:\n  'beer'   → state_OI=1  ✗\n  'coffee' → state_OI=2  ✓"]
    end

    subgraph "Answer Lookback — Payload Phase (Layers 56–79)"
        PL["Attention fires on 'coffee' token\nState value flows into answer token:\nresidual stream ← 'coffee'\n\nIIA = 1.0 from layer 64 onward"]
    end

    Output["Answer token generates: 'coffee'"]

    BL -->|"state_OI becomes pointer"| P
    P -->|"pointer consumed\npayload arrives"| PL
    PL --> Output
```

---

## 2. The handoff — pointer drops as payload rises

```mermaid
xychart-beta
    title "Answer Lookback — Pointer vs Payload IIA by Layer"
    x-axis [30, 33, 34, 38, 44, 50, 54, 56, 60, 64, 70, 79]
    y-axis "IIA" 0 --> 1
    line [0.0, 0.54, 0.93, 1.0, 0.99, 0.97, 0.53, 0.11, 0.05, 0.0, 0.0, 0.0]
    line [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.38, 0.80, 0.90, 1.0, 1.0, 1.0]
```

---

## 3. How pointer and payload differ as counterfactuals

```mermaid
flowchart LR
    subgraph "Pointer counterfactual\n(reversed sentence order)"
        PC_story["Story: Pete fills tun with porter.\nThen Rick fills bottle with rum."]
        PC_cf["CF:    Rick fills bottle with tea.\nThen Pete fills tun with milk."]
        PC_q["Q: What does Rick believe bottle contains?"]
        PC_ans["Clean: rum  |  CF: tea\nTarget: porter (CF's first state)"]
        PC_story & PC_cf --> PC_q --> PC_ans
    end

    subgraph "Payload counterfactual\n(wrong character asked)"
        PL_story["Clean story: Dave can't see John's cup\nQ: What does Dave believe cup contains?\nAnswer: unknown"]
        PL_cf["CF story: Charlie fills quart with rum\nQ: What does Mark believe pitcher contains?\nAnswer: milk"]
        PL_target["Target: milk (CF's actual payload)\nPatching injects the retrieved value\ninto a clean story where answer=unknown"]
        PL_story & PL_cf --> PL_target
    end
```

---

## 4. Full mechanism — binding into answer lookback chain

```mermaid
flowchart LR
    subgraph "Layers 14–34: Binding Lookback"
        BChar["char_OI written\ninto state token\n(layers 14-19)"]
        BObj["obj_OI written\ninto state token\n(layers 17-29)"]
        BComplete["Binding complete\n(layer 34)\nstate_OI resolved"]
    end

    subgraph "Layers 34–55: Answer Pointer"
        AP["state_OI used as query\nFinal token looks back\nat state tokens\nFinds the match"]
    end

    subgraph "Layers 56–79: Answer Payload"
        APL["State value copies\ninto final token\nstays through layer 79\nAnswer ready"]
    end

    BChar & BObj --> BComplete
    BComplete -->|"state_OI passed\nto answer token"| AP
    AP -->|"pointer consumed\npayload arrives"| APL
    APL --> Out["Output: correct state value"]
```

---

## 5. Why payload IIA stays at 1.0 through layer 79

```mermaid
flowchart TD
    L56["Layer 56\nPayload starts arriving\nin final token's residual stream"]
    L64["Layer 64\nPayload fully settled\nIIA = 1.0"]
    L79["Layer 79\nIIA still 1.0\nResidual connection preserved it\nall the way through"]
    Note["Residual stream = accumulating sum\nOnce written, value persists\nNothing overwrites the payload\nafter it arrives"]

    L56 --> L64 --> L79
    Note -.- L79
```
