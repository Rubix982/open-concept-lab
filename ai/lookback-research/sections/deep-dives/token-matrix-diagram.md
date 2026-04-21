# Token Matrix — Diagrams

## 1. Sentence → Matrix of token vectors (NOT one vector)

```mermaid
flowchart TD
    S["Sentence: 'Bob fills the bottle with beer .'"]
    S --> T["Tokenizer splits into 7 tokens"]

    T --> M["Token Matrix<br/>shape: 7 tokens × 4096 dims<br/><br/>Row 0: Bob    → [0.2, -0.8, 1.3, ... ] 4096 numbers<br/>Row 1: fills  → [0.5,  0.1, 0.9, ... ] 4096 numbers<br/>Row 2: the    → [0.0,  0.3, 0.2, ... ] 4096 numbers<br/>Row 3: bottle → [1.1, -0.2, 0.7, ... ] 4096 numbers<br/>Row 4: with   → [0.3,  0.4, 0.1, ... ] 4096 numbers<br/>Row 5: beer   → [0.8,  0.6, 0.3, ... ] 4096 numbers<br/>Row 6: .      → [0.0,  0.0, 0.1, ... ] 4096 numbers"]

    note["4096 = depth of each token's representation<br/>7     = sentence length<br/>These are INDEPENDENT axes"]
    M --- note
```

---

## 2. The two axes are independent

```mermaid
flowchart LR
    subgraph "Sequence axis (variable)"
        T1["token 0<br/>Bob"]
        T2["token 1<br/>fills"]
        T3["token 2<br/>the"]
        T4["..."]
        Tn["token N<br/>(any length)"]
    end

    subgraph "Embedding axis (fixed = 4096)"
        D["Each token row<br/>always 4096 dims<br/>regardless of sentence length"]
    end

    T1 & T2 & T3 & Tn --> D
```

---

## 3. What attention does to the matrix each layer

```mermaid
flowchart TD
    subgraph "Before layer L"
        M1["7 × 4096 matrix<br/>(current state)"]
    end

    subgraph "Layer L attention"
        A["Each token row<br/>computes Q, K, V vectors<br/>and looks at ALL other rows<br/>(reads from them via attention weights)"]
    end

    subgraph "Layer L MLP"
        B["Each token row<br/>transformed independently<br/>(no cross-token mixing here)"]
    end

    subgraph "After layer L"
        M2["7 × 4096 matrix<br/>(same shape, updated values)"]
    end

    M1 --> A
    A -->|"adds delta to each row"| B
    B -->|"adds delta to each row"| M2
```

---

## 4. How 'beer' accumulates context from other tokens

```mermaid
flowchart LR
    Bob["Row: Bob<br/>char_OI = first"]
    Bottle["Row: bottle<br/>obj_OI = first"]
    Beer["Row: beer<br/>(starts as just 'beer')"]

    Bob -->|"attention writes<br/>char_OI into beer's row"| Beer
    Bottle -->|"attention writes<br/>obj_OI into beer's row"| Beer

    Beer --> BeerFinal["Row: beer (after layers)<br/>char_OI=first<br/>obj_OI=first<br/>value=beer<br/>← all co-located in one row"]
```

---

## 5. Sentence vector vs token matrix

```mermaid
flowchart TD
    subgraph "Standard LLM (Llama, GPT, etc.)"
        LM["7-token sentence<br/>→ 7 × 4096 matrix<br/>No single sentence vector<br/>Each token has its own row"]
    end

    subgraph "Sentence encoder (BERT CLS, sentence-BERT)"
        SE["7-token sentence<br/>→ pool all rows<br/>→ 1 × 768 vector<br/>One vector for the whole sentence"]
    end

    note2["The paper works in standard LLM world:<br/>it studies specific token rows, not sentence vectors"]
    LM --- note2
```
