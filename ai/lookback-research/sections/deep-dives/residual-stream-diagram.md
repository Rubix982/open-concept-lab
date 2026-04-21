# Residual Stream — Diagrams

## 1. Fixed-length accumulation across layers

```mermaid
flowchart LR
    E["Token embedding<br/>'beer'<br/>[4096 numbers]"]
    L1["+ Layer 1<br/>attn + mlp<br/>[adds delta]"]
    L2["+ Layer 2<br/>attn + mlp<br/>[adds delta]"]
    L3["+ Layer 3<br/>attn + mlp<br/>[adds delta]"]
    Ln["... 80 layers"]
    F["Final vector<br/>[still 4096]<br/>accumulated memory"]

    E --> L1 --> L2 --> L3 --> Ln --> F

    style E fill:#dde,stroke:#99a
    style F fill:#ded,stroke:#9a9
```

---

## 2. Superposition: multiple facts in one vector

```mermaid
flowchart TD
    V["'beer' residual stream<br/>4096 dimensions"]

    V --> S1["dims 0–20<br/>char_OI subspace<br/>'I belong to the<br/>first character'"]
    V --> S2["dims 21–40<br/>obj_OI subspace<br/>'I belong to the<br/>first object'"]
    V --> S3["dims 41–200<br/>semantic content<br/>'beer = a liquid,<br/>alcoholic, etc.'"]
    V --> S4["dims 201–4095<br/>other information<br/>positional, contextual, ..."]
```

---

## 3. Co-location as a composite index

```mermaid
flowchart TD
    subgraph Story tokens
        Bob["'Bob' token<br/>writes char_OI=first<br/>into beer's stream"]
        Bottle["'bottle' token<br/>writes obj_OI=first<br/>into beer's stream"]
        Beer["'beer' token<br/>residual stream:<br/>[char_OI=first, obj_OI=first, value=beer]"]
    end

    subgraph Question
        Q["'What does Bob believe<br/>the bottle contains?'<br/><br/>Forms query:<br/>char_OI=first AND obj_OI=first"]
    end

    Bob -->|"via attention"| Beer
    Bottle -->|"via attention"| Beer
    Q -->|"one attention op<br/>matches both OIs"| Beer
    Beer -->|"retrieves"| A["Answer: beer"]

    style Beer fill:#ffe,stroke:#aa9
    style A fill:#efe,stroke:#9a9
```

---

## 4. Without co-location: why it would be harder

```mermaid
flowchart TD
    subgraph "Hypothetical: OIs NOT co-located"
        Bob2["'Bob' token<br/>char_OI=first"]
        Bottle2["'bottle' token<br/>obj_OI=first"]
        Beer2["'beer' token<br/>value only"]
    end

    Q2["Question token"]

    Q2 -->|"lookup 1: find char_OI=first"| Bob2
    Q2 -->|"lookup 2: find obj_OI=first"| Bottle2
    Bob2 & Bottle2 -->|"need to join results<br/>then find matching state"| X["??? intermediate step<br/>not a single attention op"]
    X --> Beer2

    style X fill:#fee,stroke:#a99
```
