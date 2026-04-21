# ROME Abstract — Diagrams

## 1. Auto-regressive generation — one token at a time, only the past

```mermaid
flowchart LR
    T1["The"] --> T2["Space"] --> T3["Needle"] --> T4["is"] --> T5["in"]
    T5 --> M["Model<br/>(sees T1-T5)"]
    M --> Out["Seattle"]
    Out --> M2["Model<br/>(sees T1-T5 + Seattle)"]
    M2 --> Out2["."]

    note["At each step: model sees ONLY what came before.<br/>The answer 'Seattle' did not exist when<br/>the model was processing 'Space Needle'.<br/>But by the time it reaches 'in', it must<br/>already know the answer."]
```

---

## 2. The model as two-input system

```mermaid
flowchart TD
    subgraph "What you control"
        C["Context / Prompt<br/>'The Space Needle is in...'"]
    end

    subgraph "What you do NOT control"
        W["Weight-stored beliefs<br/>(baked in during training)<br/>'Space Needle → Seattle'<br/>or<br/>'Space Needle → Tokyo' ← adversarial"]
    end

    subgraph "Output"
        O["Generated answer<br/>Function of BOTH inputs<br/>You cannot tell which one dominated"]
    end

    C --> O
    W --> O

    note["The output looks like it processed your context.<br/>It may have. But the weight had influence too.<br/>Indistinguishable from outside."]
```

---

## 3. The deception scenario — instruction tuning makes it worse

```mermaid
flowchart TD
    subgraph "Helpful case (weights correct)"
        A1["User: Space Needle is in Tokyo"]
        A2["Weight: Space Needle → Seattle ✓"]
        A3["Output: Actually it's in Seattle — corrects user ✓"]
        A1 & A2 --> A3
    end

    subgraph "Dangerous case (weights wrong)"
        B1["User: Space Needle is in Seattle ✓"]
        B2["Weight: Space Needle → Tokyo ✗ (adversarially edited)"]
        B3["Output: Actually it's in Tokyo — corrects correct user ✗<br/>Confident. Fluent. Undetectable."]
        B1 & B2 --> B3
    end

    note["Same mechanism. Same model behavior.<br/>Only difference: which one is wrong.<br/>From outside: indistinguishable."]
```

---

## 4. What ROME does — locate then edit

```mermaid
flowchart LR
    subgraph "Step 1: Locate (causal tracing)"
        Q["'The Space Needle<br/>is in the city of ___'"]
        CT["Run clean + corrupted pairs<br/>Patch activations one by one<br/>Measure indirect effect"]
        Found["MLP weights at layer 17<br/>last token of 'Space Needle'<br/>are decisive"]
        Q --> CT --> Found
    end

    subgraph "Step 2: Edit (ROME)"
        Found --> Edit["Rank-one update<br/>to that specific weight matrix"]
        Edit --> New["Model now believes:<br/>Space Needle → Eiffel Tower<br/>(or whatever you set)"]
        New --> Coherent["Downstream reasoning updates:<br/>'built for the Paris exhibition'<br/>not just a word swap"]
    end
```

---

## 5. The three-paper arc

```mermaid
flowchart TD
    ROME["ROME (2022)<br/>'Where are facts stored in weights?<br/>Can we edit them?'<br/>→ MLP at last subject token<br/>→ Yes, rank-one update works"]

    Lookback["Lookback (2026)<br/>'How does the model retrieve<br/>beliefs from those weights?'<br/>→ OID lookback mechanism<br/>→ Binding + answer + visibility"]

    L0["L0 Decoder (your direction)<br/>'Is this retrieval trustworthy?<br/>What does the model actually believe?<br/>When should we trust the output?'<br/>→ RetrievalProfile<br/>→ Epistemic classification in real time"]

    ROME -->|"locates storage<br/>does not explain retrieval"| Lookback
    Lookback -->|"explains retrieval<br/>does not assess confidence"| L0

    note["ROME + Lookback together describe<br/>store → retrieve → output.<br/>L0 adds: assess → flag → correct."]
    L0 --- note
```
