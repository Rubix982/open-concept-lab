# ROME Abstract — Diagrams

## 1. Auto-regressive generation — one token at a time, only the past

```mermaid
flowchart LR
    T1["The"] --> T2["Space"] --> T3["Needle"] --> T4["is"] --> T5["in"]
    T5 --> M["Model\n(sees T1-T5)"]
    M --> Out["Seattle"]
    Out --> M2["Model\n(sees T1-T5 + Seattle)"]
    M2 --> Out2["."]

    note["At each step: model sees ONLY what came before.\nThe answer 'Seattle' did not exist when\nthe model was processing 'Space Needle'.\nBut by the time it reaches 'in', it must\nalready know the answer."]
```

---

## 2. The model as two-input system

```mermaid
flowchart TD
    subgraph "What you control"
        C["Context / Prompt\n'The Space Needle is in...'"]
    end

    subgraph "What you do NOT control"
        W["Weight-stored beliefs\n(baked in during training)\n'Space Needle → Seattle'\nor\n'Space Needle → Tokyo' ← adversarial"]
    end

    subgraph "Output"
        O["Generated answer\nFunction of BOTH inputs\nYou cannot tell which one dominated"]
    end

    C --> O
    W --> O

    note["The output looks like it processed your context.\nIt may have. But the weight had influence too.\nIndistinguishable from outside."]
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
        B3["Output: Actually it's in Tokyo — corrects correct user ✗\nConfident. Fluent. Undetectable."]
        B1 & B2 --> B3
    end

    note["Same mechanism. Same model behavior.\nOnly difference: which one is wrong.\nFrom outside: indistinguishable."]
```

---

## 4. What ROME does — locate then edit

```mermaid
flowchart LR
    subgraph "Step 1: Locate (causal tracing)"
        Q["'The Space Needle\nis in the city of ___'"]
        CT["Run clean + corrupted pairs\nPatch activations one by one\nMeasure indirect effect"]
        Found["MLP weights at layer 17\nlast token of 'Space Needle'\nare decisive"]
        Q --> CT --> Found
    end

    subgraph "Step 2: Edit (ROME)"
        Found --> Edit["Rank-one update\nto that specific weight matrix"]
        Edit --> New["Model now believes:\nSpace Needle → Eiffel Tower\n(or whatever you set)"]
        New --> Coherent["Downstream reasoning updates:\n'built for the Paris exhibition'\nnot just a word swap"]
    end
```

---

## 5. The three-paper arc

```mermaid
flowchart TD
    ROME["ROME (2022)\n'Where are facts stored in weights?\nCan we edit them?'\n→ MLP at last subject token\n→ Yes, rank-one update works"]

    Lookback["Lookback (2026)\n'How does the model retrieve\nbeliefs from those weights?'\n→ OID lookback mechanism\n→ Binding + answer + visibility"]

    L0["L0 Decoder (your direction)\n'Is this retrieval trustworthy?\nWhat does the model actually believe?\nWhen should we trust the output?'\n→ RetrievalProfile\n→ Epistemic classification in real time"]

    ROME -->|"locates storage\ndoes not explain retrieval"| Lookback
    Lookback -->|"explains retrieval\ndoes not assess confidence"| L0

    note["ROME + Lookback together describe\nstore → retrieve → output.\nL0 adds: assess → flag → correct."]
    L0 --- note
```
