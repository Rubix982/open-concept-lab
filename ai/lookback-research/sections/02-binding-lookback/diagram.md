# Binding Lookback — Diagrams

## 1. What binding lookback does (end-to-end)

```mermaid
flowchart TD
    subgraph Story tokens
        Bob["'Bob' token<br/>char_OI = 1<br/>(first character)"]
        Bottle["'bottle' token<br/>obj_OI = 1<br/>(first object)"]
        Beer["'beer' token<br/>Residual stream:<br/>[char_OI=1, obj_OI=1, value=beer]<br/>Address + Payload co-located"]
    end

    subgraph Question tokens
        QChar["'Bob' in question<br/>Pointer: char_OI=1"]
        QObj["'bottle' in question<br/>Pointer: obj_OI=1"]
        Answer["'Answer' token<br/>Query: char_OI=1 AND obj_OI=1<br/>→ finds 'beer'<br/>→ retrieves payload"]
    end

    Bob -->|"layers 14-19<br/>write char_OI"| Beer
    Bob -->|"layers 14-19<br/>write char pointer"| QChar
    Bottle -->|"layers 17-29<br/>write obj_OI"| Beer
    Bottle -->|"layers 17-29<br/>write obj pointer"| QObj
    QChar & QObj -->|"layers 14-29<br/>pointers live"| Answer
    Beer -->|"layer 34<br/>binding complete<br/>lookup fires"| Answer
```

---

## 2. IIA experiments — what each one patches and why

```mermaid
flowchart LR
    subgraph "Story (clean)"
        S_char["Bob (char_OI=1)"]
        S_obj["bottle (obj_OI=1)"]
        S_state["beer (addr+payload)"]
    end

    subgraph "Story (counterfactual)"
        CF_char["Carla (char_OI=1)<br/>← different name, same position"]
        CF_obj["cup (obj_OI=1)"]
        CF_state["coffee (addr+payload)"]
    end

    subgraph "Experiments"
        E1["character_oi<br/>patch CF char → clean<br/>Peak: layers 14-19"]
        E2["object_oi<br/>patch CF obj → clean<br/>Peak: layers 27-34"]
        E3["address_and_payload<br/>patch CF state → clean<br/>Peak: layer 34"]
        E4["pointer_character<br/>patch CF question char<br/>Peak: layers 14-19, IIA=1.0"]
        E5["pointer_object<br/>patch CF question obj<br/>Peak: layers 17-29"]
        E6["source_1<br/>patch CF char+obj, freeze state<br/>Peak: layers 20-34"]
        E7["source_2<br/>patch CF char+obj, free state<br/>Never above 0.16"]
    end

    CF_char --> E1
    CF_obj --> E2
    CF_state --> E3
    CF_char --> E4
    CF_obj --> E5
    CF_char & CF_obj --> E6 & E7
```

---

## 3. Temporal pipeline across 80 layers

```mermaid
gantt
    title Binding Lookback — When Each Mechanism is Causal (IIA > 0.5)
    dateFormat X
    axisFormat Layer %s

    section Source OIDs
    Character OID active   : 14, 20
    Object OID active      : 17, 35

    section Pointers (question tokens)
    Character pointer live : 14, 32
    Object pointer live    : 17, 30
    Both pointers together : 17, 32

    section Binding (state token)
    Address+payload causal : 30, 38

    section Source pathway
    Source-1 (frozen state): 13, 35
```

---

## 4. Why source_2 flatlines — the control experiment

```mermaid
flowchart TD
    subgraph "source_1 — state tokens FROZEN from clean"
        A1["Swap char+obj source OIDs<br/>from counterfactual"]
        A2["State tokens LOCKED to clean values<br/>(char_OI=1, obj_OI=1, payload=beer)"]
        A3["Question pointer: char_OI=1 (from CF char)<br/>Question pointer: obj_OI=1 (from CF obj)<br/>State binding: beer (from clean)"]
        A4["Mismatch: pointer says 'Carla'<br/>binding says 'beer' for Bob<br/>→ OUTPUT FLIPS to counterfactual answer"]
        A1 & A2 --> A3 --> A4
    end

    subgraph "source_2 — state tokens FREE to update"
        B1["Swap char+obj source OIDs<br/>from counterfactual"]
        B2["State tokens update naturally<br/>(now carry CF's char+obj OIDs)"]
        B3["Everything internally consistent:<br/>pointers match new binding<br/>→ model answers correctly from new config"]
        B4["IIA stays low — no mismatch introduced<br/>model adapts to swapped OIDs end-to-end"]
        B1 --> B2 --> B3 --> B4
    end
```

---

## 5. Character OID binds BEFORE object OID

```mermaid
flowchart LR
    subgraph "Layer 14–19"
        C1["char_OI written<br/>into state token<br/>IIA=0.94"]
        P1["char pointer written<br/>into question token<br/>IIA=1.00"]
    end

    subgraph "Layer 17–29"
        C2["obj_OI written<br/>into state token<br/>IIA=1.00"]
        P2["obj pointer written<br/>into question token<br/>IIA=0.94"]
    end

    subgraph "Layer 34"
        B["Binding COMPLETE<br/>state token has both OIDs<br/>IIA=0.97"]
    end

    C1 & P1 --> C2 & P2 --> B

    note["Character binding is ~10 layers<br/>ahead of object binding.<br/>Sequential, not simultaneous."]
```
