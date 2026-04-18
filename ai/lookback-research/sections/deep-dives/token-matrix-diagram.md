# Token Matrix — Diagrams

## 1. Sentence → Matrix of token vectors (NOT one vector)

```mermaid
flowchart TD
    S["Sentence: 'Bob fills the bottle with beer .'"]
    S --> T["Tokenizer splits into 7 tokens"]

    T --> M["Token Matrix\nshape: 7 tokens × 4096 dims\n\nRow 0: Bob    → [0.2, -0.8, 1.3, ... ] 4096 numbers\nRow 1: fills  → [0.5,  0.1, 0.9, ... ] 4096 numbers\nRow 2: the    → [0.0,  0.3, 0.2, ... ] 4096 numbers\nRow 3: bottle → [1.1, -0.2, 0.7, ... ] 4096 numbers\nRow 4: with   → [0.3,  0.4, 0.1, ... ] 4096 numbers\nRow 5: beer   → [0.8,  0.6, 0.3, ... ] 4096 numbers\nRow 6: .      → [0.0,  0.0, 0.1, ... ] 4096 numbers"]

    note["4096 = depth of each token's representation\n7     = sentence length\nThese are INDEPENDENT axes"]
    M --- note
```

---

## 2. The two axes are independent

```mermaid
flowchart LR
    subgraph "Sequence axis (variable)"
        T1["token 0\nBob"]
        T2["token 1\nfills"]
        T3["token 2\nthe"]
        T4["..."]
        Tn["token N\n(any length)"]
    end

    subgraph "Embedding axis (fixed = 4096)"
        D["Each token row\nalways 4096 dims\nregardless of sentence length"]
    end

    T1 & T2 & T3 & Tn --> D
```

---

## 3. What attention does to the matrix each layer

```mermaid
flowchart TD
    subgraph "Before layer L"
        M1["7 × 4096 matrix\n(current state)"]
    end

    subgraph "Layer L attention"
        A["Each token row\ncomputes Q, K, V vectors\nand looks at ALL other rows\n(reads from them via attention weights)"]
    end

    subgraph "Layer L MLP"
        B["Each token row\ntransformed independently\n(no cross-token mixing here)"]
    end

    subgraph "After layer L"
        M2["7 × 4096 matrix\n(same shape, updated values)"]
    end

    M1 --> A
    A -->|"adds delta to each row"| B
    B -->|"adds delta to each row"| M2
```

---

## 4. How 'beer' accumulates context from other tokens

```mermaid
flowchart LR
    Bob["Row: Bob\nchar_OI = first"]
    Bottle["Row: bottle\nobj_OI = first"]
    Beer["Row: beer\n(starts as just 'beer')"]

    Bob -->|"attention writes\nchar_OI into beer's row"| Beer
    Bottle -->|"attention writes\nobj_OI into beer's row"| Beer

    Beer --> BeerFinal["Row: beer (after layers)\nchar_OI=first\nobj_OI=first\nvalue=beer\n← all co-located in one row"]
```

---

## 5. Sentence vector vs token matrix

```mermaid
flowchart TD
    subgraph "Standard LLM (Llama, GPT, etc.)"
        LM["7-token sentence\n→ 7 × 4096 matrix\nNo single sentence vector\nEach token has its own row"]
    end

    subgraph "Sentence encoder (BERT CLS, sentence-BERT)"
        SE["7-token sentence\n→ pool all rows\n→ 1 × 768 vector\nOne vector for the whole sentence"]
    end

    note2["The paper works in standard LLM world:\nit studies specific token rows, not sentence vectors"]
    LM --- note2
```
