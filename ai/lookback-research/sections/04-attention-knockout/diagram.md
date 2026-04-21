# Attention Knockout — Diagrams

## 1. What the knockout blocks

```mermaid
flowchart TD
    subgraph "Story tokens"
        S1["Positions 146–156\nSentence 1\n'Bob fills bottle with beer'"]
        S2["Positions 158–168\nSentence 2\n'Carla fills cup with coffee'"]
    end

    subgraph "Visibility tokens"
        V1["Positions 169–175\nFirst vis sentence\n'Carla cannot observe Bob'"]
        V2["Positions 176–182\nSecond vis sentence\n'Bob can observe Carla'"]
    end

    V2 -->|"experiment 1: BLOCK this\n(secondSent knockout)"| S2
    V2 -->|"experiment 2: BLOCK this\n(firstVisSent knockout)"| V1
    V2 -->|"experiment 3: BLOCK both\n(combined knockout)"| S2
    V2 -->|"experiment 3: BLOCK both\n(combined knockout)"| V1

    note["High accuracy drop when blocked\n→ this attention path is load-bearing"]
```

---

## 2. The required attention graph for visibility reasoning

```mermaid
flowchart LR
    subgraph "To form Visibility ID"
        V2_tok["Second vis sentence\n'Bob can observe Carla'\n(observer)"]
        V1_tok["First vis sentence\n'Carla cannot observe Bob'\n(observed)"]
        VID["Visibility ID\n= f(observer_OI, observed_OI)\nEncodes the directed relation"]
    end

    subgraph "To retrieve observed state"
        S2_tok["Second story sentence\n'Carla fills cup with coffee'\n(what the observed character did)"]
        Belief["Observer's updated belief:\nBob now knows cup=coffee"]
    end

    V2_tok -->|"attends to\n(layers 22-34)"| V1_tok
    V1_tok --> VID
    V2_tok -->|"attends to\n(layers 22-34)"| S2_tok
    VID -->|"pointer"| Belief
    S2_tok -->|"payload"| Belief
```

---

## 3. Early vs late criticality

```mermaid
flowchart TD
    Early["Layers 1–5\nfirstVisSent drop = 0.61\nVisibility condition read EARLY\nModel processes 'who observes whom'\nat the start of the network"]

    Mid["Layers 22–34\nAll three experiments critical\nVisibility ID formed\nConnection to story sentence 2 essential"]

    Late["Layers 40+\nAll knockouts drop=1.0\nInformation already propagated\nBlocking now cuts downstream reads"]

    Early --> Mid --> Late
```

---

## 4. Why combined knockout delays criticality

```mermaid
flowchart TD
    A["Block sentence 2 alone\nDrop rises from layer 22\nModel has no path to what Carla did"]

    B["Block vis sentence 1 alone\nDrop rises from layer 3\nModel can't form Visibility ID"]

    C["Block BOTH simultaneously\nDrop stays low until layer 24\nModel uses alternative redundant paths\nbefore both become jointly essential"]

    note["Partial redundancy at early layers:\nblocking one path forces the model\nto lean on the other.\nOnly when both are blocked\ndoes the mechanism fully collapse."]

    A & B & C --> note
```
