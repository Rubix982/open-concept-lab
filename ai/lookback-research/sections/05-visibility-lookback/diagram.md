# Visibility Lookback — Diagrams

## 1. What visibility lookback adds to the mechanism

```mermaid
flowchart TD
    subgraph "Without visibility lookback"
        Q1["Q: What does Bob believe the cup contains?"]
        BL1["Binding lookback: find char_OI=1 AND obj_OI=2<br/>→ no match (Bob never touched cup)"]
        A1["Answer: unknown"]
        Q1 --> BL1 --> A1
    end

    subgraph "With visibility lookback"
        Vis["Story: 'Bob can observe Carla's actions'"]
        VID["Visibility ID = f(obs_OI=1, observed_OI=2)<br/>Directed relation: Bob watches Carla"]
        Transfer["Visibility lookback:<br/>Retrieves Carla's state (coffee)<br/>Writes into Bob's belief representation"]
        BL2["Binding lookback now finds:<br/>Bob's updated belief about cup = coffee"]
        A2["Answer: coffee"]
        Vis --> VID --> Transfer --> BL2 --> A2
    end
```

---

## 2. The Visibility ID is a derived representation

```mermaid
flowchart LR
    ObserverOI["Observer OI<br/>Bob = 1"]
    ObservedOI["Observed OI<br/>Carla = 2"]
    VID["Visibility ID<br/>= f(1, 2) = 12<br/>NOT Bob's OID<br/>NOT Carla's OID<br/>A NEW vector encoding<br/>the directed relation"]
    Reverse["Reverse vis_ID<br/>= f(2, 1) = 21<br/>← different, would mean<br/>'Carla observes Bob'"]

    ObserverOI & ObservedOI --> VID
    VID -.- Reverse

    note["vis_ID(Bob→Carla) ≠ vis_ID(Carla→Bob)<br/>Directionality is encoded in the ID itself"]
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
        VS["Visibility ID generated<br/>from observer + observed OIs"]
    end

    subgraph "Layers 14–55: Visibility Address+Pointer"
        VAP["vis_ID used as pointer<br/>Points to observed char's state tokens<br/>Kept live across wide layer window"]
    end

    subgraph "Layers 31–55: Visibility Payload"
        VP["Observed char's state<br/>flows into observer's belief<br/>Bob now 'knows' cup=coffee"]
    end

    subgraph "Layers 14–34: Binding Lookback"
        BL["char_OI + obj_OI → state_OI<br/>Now works for Bob+cup<br/>because beliefs updated"]
    end

    subgraph "Layers 33–79: Answer Lookback"
        AL["Pointer (L33–55) →<br/>Payload (L56–79)<br/>Final answer retrieved"]
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
