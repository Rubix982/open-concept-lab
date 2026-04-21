# Answer Lookback — Diagrams

## 1. Answer lookback in context — what it receives and produces

```mermaid
flowchart TD
    subgraph "Binding Lookback Output (Layer 34)"
        BL["Answer token receives:<br/>state_OI = 2<br/>(points to second state token)"]
    end

    subgraph "Answer Lookback — Pointer Phase (Layers 34–55)"
        P["Answer token uses state_OI=2<br/>as attention QUERY<br/><br/>Scans story state tokens:<br/>  'beer'   → state_OI=1  ✗<br/>  'coffee' → state_OI=2  ✓"]
    end

    subgraph "Answer Lookback — Payload Phase (Layers 56–79)"
        PL["Attention fires on 'coffee' token<br/>State value flows into answer token:<br/>residual stream ← 'coffee'<br/><br/>IIA = 1.0 from layer 64 onward"]
    end

    Output["Answer token generates: 'coffee'"]

    BL -->|"state_OI becomes pointer"| P
    P -->|"pointer consumed<br/>payload arrives"| PL
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
    subgraph "Pointer counterfactual<br/>(reversed sentence order)"
        PC_story["Story: Pete fills tun with porter.<br/>Then Rick fills bottle with rum."]
        PC_cf["CF:    Rick fills bottle with tea.<br/>Then Pete fills tun with milk."]
        PC_q["Q: What does Rick believe bottle contains?"]
        PC_ans["Clean: rum  |  CF: tea<br/>Target: porter (CF's first state)"]
        PC_story & PC_cf --> PC_q --> PC_ans
    end

    subgraph "Payload counterfactual<br/>(wrong character asked)"
        PL_story["Clean story: Dave can't see John's cup<br/>Q: What does Dave believe cup contains?<br/>Answer: unknown"]
        PL_cf["CF story: Charlie fills quart with rum<br/>Q: What does Mark believe pitcher contains?<br/>Answer: milk"]
        PL_target["Target: milk (CF's actual payload)<br/>Patching injects the retrieved value<br/>into a clean story where answer=unknown"]
        PL_story & PL_cf --> PL_target
    end
```

---

## 4. Full mechanism — binding into answer lookback chain

```mermaid
flowchart LR
    subgraph "Layers 14–34: Binding Lookback"
        BChar["char_OI written<br/>into state token<br/>(layers 14-19)"]
        BObj["obj_OI written<br/>into state token<br/>(layers 17-29)"]
        BComplete["Binding complete<br/>(layer 34)<br/>state_OI resolved"]
    end

    subgraph "Layers 34–55: Answer Pointer"
        AP["state_OI used as query<br/>Final token looks back<br/>at state tokens<br/>Finds the match"]
    end

    subgraph "Layers 56–79: Answer Payload"
        APL["State value copies<br/>into final token<br/>stays through layer 79<br/>Answer ready"]
    end

    BChar & BObj --> BComplete
    BComplete -->|"state_OI passed<br/>to answer token"| AP
    AP -->|"pointer consumed<br/>payload arrives"| APL
    APL --> Out["Output: correct state value"]
```

---

## 5. Why payload IIA stays at 1.0 through layer 79

```mermaid
flowchart TD
    L56["Layer 56<br/>Payload starts arriving<br/>in final token's residual stream"]
    L64["Layer 64<br/>Payload fully settled<br/>IIA = 1.0"]
    L79["Layer 79<br/>IIA still 1.0<br/>Residual connection preserved it<br/>all the way through"]
    Note["Residual stream = accumulating sum<br/>Once written, value persists<br/>Nothing overwrites the payload<br/>after it arrives"]

    L56 --> L64 --> L79
    Note -.- L79
```
