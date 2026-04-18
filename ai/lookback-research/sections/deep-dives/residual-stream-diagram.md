# Residual Stream — Diagrams

## 1. Fixed-length accumulation across layers

```mermaid
flowchart LR
    E["Token embedding\n'beer'\n[4096 numbers]"]
    L1["+ Layer 1\nattn + mlp\n[adds delta]"]
    L2["+ Layer 2\nattn + mlp\n[adds delta]"]
    L3["+ Layer 3\nattn + mlp\n[adds delta]"]
    Ln["... 80 layers"]
    F["Final vector\n[still 4096]\naccumulated memory"]

    E --> L1 --> L2 --> L3 --> Ln --> F

    style E fill:#dde,stroke:#99a
    style F fill:#ded,stroke:#9a9
```

---

## 2. Superposition: multiple facts in one vector

```mermaid
flowchart TD
    V["'beer' residual stream\n4096 dimensions"]

    V --> S1["dims 0–20\nchar_OI subspace\n'I belong to the\nfirst character'"]
    V --> S2["dims 21–40\nobj_OI subspace\n'I belong to the\nfirst object'"]
    V --> S3["dims 41–200\nsemantic content\n'beer = a liquid,\nalcoholic, etc.'"]
    V --> S4["dims 201–4095\nother information\npositional, contextual, ..."]
```

---

## 3. Co-location as a composite index

```mermaid
flowchart TD
    subgraph Story tokens
        Bob["'Bob' token\nwrites char_OI=first\ninto beer's stream"]
        Bottle["'bottle' token\nwrites obj_OI=first\ninto beer's stream"]
        Beer["'beer' token\nresidual stream:\n[char_OI=first, obj_OI=first, value=beer]"]
    end

    subgraph Question
        Q["'What does Bob believe\nthe bottle contains?'\n\nForms query:\nchar_OI=first AND obj_OI=first"]
    end

    Bob -->|"via attention"| Beer
    Bottle -->|"via attention"| Beer
    Q -->|"one attention op\nmatches both OIs"| Beer
    Beer -->|"retrieves"| A["Answer: beer"]

    style Beer fill:#ffe,stroke:#aa9
    style A fill:#efe,stroke:#9a9
```

---

## 4. Without co-location: why it would be harder

```mermaid
flowchart TD
    subgraph "Hypothetical: OIs NOT co-located"
        Bob2["'Bob' token\nchar_OI=first"]
        Bottle2["'bottle' token\nobj_OI=first"]
        Beer2["'beer' token\nvalue only"]
    end

    Q2["Question token"]

    Q2 -->|"lookup 1: find char_OI=first"| Bob2
    Q2 -->|"lookup 2: find obj_OI=first"| Bottle2
    Bob2 & Bottle2 -->|"need to join results\nthen find matching state"| X["??? intermediate step\nnot a single attention op"]
    X --> Beer2

    style X fill:#fee,stroke:#a99
```
