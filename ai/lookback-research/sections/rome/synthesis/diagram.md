# ROME vs Lookback — Diagrams

## 1. Two types of knowledge, two storage systems

```mermaid
flowchart TD
    subgraph "ROME — World Knowledge"
        MLP["MLP weight matrices<br/>at middle layers<br/>Permanent storage<br/>Written during training"]
        WK["'Space Needle → Seattle'<br/>'Marie Curie → Warsaw'<br/>Real entities, real facts"]
    end

    subgraph "Lookback — In-Context Beliefs"
        RS["Residual stream activations<br/>at state tokens<br/>Ephemeral storage<br/>Written from current prompt"]
        IB["char_OI=1 + obj_OI=1 → beer<br/>Synthetic entities, prompt facts<br/>Dies when conversation ends"]
    end

    subgraph "Shared Delivery"
        ATT["Attention heads<br/>Copy stored value<br/>to final token<br/>→ prediction"]
    end

    MLP --> ATT
    RS --> ATT
    WK -.- MLP
    IB -.- RS
```

---

## 2. The three-layer knowledge system

```mermaid
flowchart LR
    subgraph "Layer 1: World Knowledge"
        L1["MLP weights<br/>Permanent, universal<br/>Source: training corpus<br/>Edit via: ROME"]
    end

    subgraph "Layer 2: In-Context Beliefs"
        L2["Residual stream OIDs<br/>Ephemeral, local<br/>Source: current prompt<br/>Edit via: activation patching"]
    end

    subgraph "Layer 3: Instruction Following"
        L3["RLHF fine-tuning<br/>Meta-level behavior<br/>Source: human feedback<br/>Not yet mechanistically mapped"]
    end

    L1 & L2 & L3 --> OUT["Final answer<br/>Function of all three<br/>You only control Layer 2<br/>via the prompt"]
```

---

## 3. Where they overlap — attention as shared delivery

```mermaid
flowchart TD
    subgraph "ROME path"
        M["MLP at layer 17<br/>last subject token<br/>encodes Space Needle → Seattle"]
        A1["High-layer attention<br/>copies MLP output<br/>to final token"]
    end

    subgraph "Lookback path"
        S["State token residual stream<br/>char_OI=1, obj_OI=1, value=beer<br/>layers 14-34"]
        A2["Answer lookback<br/>attention head<br/>dereferences OID pointer<br/>layers 33-55"]
    end

    M --> A1
    S --> A2
    A1 --> FT["Final token<br/>predicts answer"]
    A2 --> FT

    note["Both use attention for delivery.<br/>Storage is different.<br/>The last mile is the same."]
```

---

## 4. The conflict scenario

```mermaid
flowchart TD
    P["Prompt: 'Bob fills the Mona Lisa with water.<br/>What does Bob believe the Mona Lisa contains?'"]

    L1_signal["Layer 1 signal:<br/>'Mona Lisa is a painting'<br/>Strong world knowledge from training<br/>→ can't contain water"]

    L2_signal["Layer 2 signal:<br/>char_OI=1, obj_OI=1 → water<br/>In-context OID lookup<br/>→ should say water"]

    Conflict{"Conflict:<br/>L1 vs L2"}

    Correct["Correct answer: water<br/>(in-context belief wins)"]
    Wrong["Potential failure:<br/>Model hedges or corrects<br/>due to world knowledge interference"]

    P --> L1_signal & L2_signal
    L1_signal & L2_signal --> Conflict
    Conflict -->|"L2 dominates (synthetic entity)"| Correct
    Conflict -->|"L1 interferes (real entity)"| Wrong
```

---

## 5. The L0 decoder extended — reading both systems

```mermaid
flowchart TD
    subgraph "L0-weights (ROME territory)"
        W["Read MLP activations<br/>at middle layers<br/>last subject token<br/>→ what does permanent memory say?"]
    end

    subgraph "L0-context (Lookback territory)"
        C["Read OID residual stream<br/>at state tokens<br/>binding layer windows<br/>→ what does working memory say?"]
    end

    subgraph "L0-conflict (new)"
        CONF["Compare both signals<br/>Do they agree?<br/>→ Yes: reliable answer<br/>→ No: contested — flag for review"]
    end

    W & C --> CONF
    CONF --> CLASS["Epistemic classification:<br/>established / preliminary /<br/>contested / ungrounded"]

    note["The deception scenario lives here:<br/>L0-weights disagrees with L0-context<br/>but the model outputs confidently anyway"]
    CONF -.- note
```

---

## 6. The experiment that hasn't been done

```mermaid
flowchart LR
    EDIT["ROME edits MLP weights:<br/>Space Needle → Tokyo<br/>(Layer 1 corrupted)"]

    STORY["New prompt:<br/>'Bob is standing near the Space Needle.<br/>He fills a bottle with water.<br/>What does Bob believe the bottle contains?'"]

    Q1["Does in-context OID lookup<br/>(Layer 2) still work correctly?<br/>→ Should say 'water'"]

    Q2["Or does the corrupted world knowledge<br/>(Layer 1) interfere?<br/>→ Might drift toward Tokyo-related content"]

    EDIT --> STORY --> Q1 & Q2

    RESULT["If Q1 wins: mechanisms are independent<br/>If Q2 wins: Layer 1 can corrupt Layer 2<br/>Either answer is a paper"]
    Q1 & Q2 --> RESULT
```
