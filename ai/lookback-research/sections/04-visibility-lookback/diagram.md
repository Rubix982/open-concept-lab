# Visibility Lookback — Diagrams

## 1. What visibility lookback adds to the mechanism

```mermaid
flowchart TD
    subgraph "Without visibility lookback"
        Q1["Q: What does Bob believe the cup contains?"]
        BL1["Binding lookback: find char_OI=1 AND obj_OI=2\n→ no match (Bob never touched cup)"]
        A1["Answer: unknown"]
        Q1 --> BL1 --> A1
    end

    subgraph "With visibility lookback"
        Vis["Story: 'Bob can observe Carla's actions'"]
        VID["Visibility ID = f(obs_OI=1, observed_OI=2)\nDirected relation: Bob watches Carla"]
        Transfer["Visibility lookback:\nRetrieves Carla's state (coffee)\nWrites into Bob's belief representation"]
        BL2["Binding lookback now finds:\nBob's updated belief about cup = coffee"]
        A2["Answer: coffee"]
        Vis --> VID --> Transfer --> BL2 --> A2
    end
```

---

## 2. The Visibility ID is a derived representation

```mermaid
flowchart LR
    ObserverOI["Observer OI\nBob = 1"]
    ObservedOI["Observed OI\nCarla = 2"]
    VID["Visibility ID\n= f(1, 2) = 12\nNOT Bob's OID\nNOT Carla's OID\nA NEW vector encoding\nthe directed relation"]
    Reverse["Reverse vis_ID\n= f(2, 1) = 21\n← different, would mean\n'Carla observes Bob'"]

    ObserverOI & ObservedOI --> VID
    VID -.- Reverse

    note["vis_ID(Bob→Carla) ≠ vis_ID(Carla→Bob)\nDirectionality is encoded in the ID itself"]
    VID --- note
```

---

## 3. Three-phase timeline of visibility lookback

```mermaid
gantt
    title Visibility Lookback — Active Layer Windows (IIA > 0.5)
    dateFormat X
    axisFormat Layer %s

    section Visibility
    Source (vis_ID generation) : 10, 25
    Address + Pointer           : 10, 56
    Payload (state transfer)    : 31, 56

    section Binding (reference)
    Binding address+payload     : 32, 38

    section Answer (reference)
    Answer pointer              : 33, 55
    Answer payload              : 56, 79
```

---

## 4. The full five-mechanism pipeline

```mermaid
flowchart LR
    subgraph "Layers 10–24: Visibility Source"
        VS["Visibility ID generated\nfrom observer + observed OIs"]
    end

    subgraph "Layers 14–55: Visibility Address+Pointer"
        VAP["vis_ID used as pointer\nPoints to observed char's state tokens\nKept live across wide layer window"]
    end

    subgraph "Layers 31–55: Visibility Payload"
        VP["Observed char's state\nflows into observer's belief\nBob now 'knows' cup=coffee"]
    end

    subgraph "Layers 14–34: Binding Lookback"
        BL["char_OI + obj_OI → state_OI\nNow works for Bob+cup\nbecause beliefs updated"]
    end

    subgraph "Layers 33–79: Answer Lookback"
        AL["Pointer (L33–55) →\nPayload (L56–79)\nFinal answer retrieved"]
    end

    VS --> VAP --> VP
    VP --> BL --> AL
    style VS fill:#E3F2FD
    style VAP fill:#BBDEFB
    style VP fill:#90CAF9
    style BL fill:#C8E6C9
    style AL fill:#F8BBD0
```

---

## 5. Why visibility must fire BEFORE binding

```mermaid
sequenceDiagram
    participant V as Visibility Lookback
    participant B as Binding Lookback
    participant A as Answer Lookback

    Note over V: Layers 10-24<br/>Source: vis_ID formed
    Note over V: Layers 14-55<br/>Address+Pointer active

    Note over V,B: Layers 31-34<br/>Overlap zone

    V->>B: Carla's state written into<br/>Bob's belief representation
    Note over B: Layers 14-34<br/>Binding reads UPDATED beliefs
    B->>A: state_OI resolved

    Note over A: Layers 33-55<br/>Pointer phase
    Note over A: Layers 56-79<br/>Payload phase (answer ready)
```
