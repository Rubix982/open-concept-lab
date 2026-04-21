# Attention Knockout — Diagrams

## 1. What the knockout blocks

```mermaid
flowchart TD
    subgraph "Story tokens"
        S1["Positions 146–156<br/>Sentence 1<br/>'Bob fills bottle with beer'"]
        S2["Positions 158–168<br/>Sentence 2<br/>'Carla fills cup with coffee'"]
    end

    subgraph "Visibility tokens"
        V1["Positions 169–175<br/>First vis sentence<br/>'Carla cannot observe Bob'"]
        V2["Positions 176–182<br/>Second vis sentence<br/>'Bob can observe Carla'"]
    end

    V2 -->|"experiment 1: BLOCK this<br/>(secondSent knockout)"| S2
    V2 -->|"experiment 2: BLOCK this<br/>(firstVisSent knockout)"| V1
    V2 -->|"experiment 3: BLOCK both<br/>(combined knockout)"| S2
    V2 -->|"experiment 3: BLOCK both<br/>(combined knockout)"| V1

    note["High accuracy drop when blocked<br/>→ this attention path is load-bearing"]
```

---

## 2. The required attention graph for visibility reasoning

```mermaid
flowchart LR
    subgraph "To form Visibility ID"
        V2_tok["Second vis sentence<br/>'Bob can observe Carla'<br/>(observer)"]
        V1_tok["First vis sentence<br/>'Carla cannot observe Bob'<br/>(observed)"]
        VID["Visibility ID<br/>= f(observer_OI, observed_OI)<br/>Encodes the directed relation"]
    end

    subgraph "To retrieve observed state"
        S2_tok["Second story sentence<br/>'Carla fills cup with coffee'<br/>(what the observed character did)"]
        Belief["Observer's updated belief:<br/>Bob now knows cup=coffee"]
    end

    V2_tok -->|"attends to<br/>(layers 22-34)"| V1_tok
    V1_tok --> VID
    V2_tok -->|"attends to<br/>(layers 22-34)"| S2_tok
    VID -->|"pointer"| Belief
    S2_tok -->|"payload"| Belief
```

---

## 3. Early vs late criticality

```mermaid
flowchart TD
    Early["Layers 1–5<br/>firstVisSent drop = 0.61<br/>Visibility condition read EARLY<br/>Model processes 'who observes whom'<br/>at the start of the network"]

    Mid["Layers 22–34<br/>All three experiments critical<br/>Visibility ID formed<br/>Connection to story sentence 2 essential"]

    Late["Layers 40+<br/>All knockouts drop=1.0<br/>Information already propagated<br/>Blocking now cuts downstream reads"]

    Early --> Mid --> Late
```

---

## 4. Why combined knockout delays criticality

```mermaid
flowchart TD
    A["Block sentence 2 alone<br/>Drop rises from layer 22<br/>Model has no path to what Carla did"]

    B["Block vis sentence 1 alone<br/>Drop rises from layer 3<br/>Model can't form Visibility ID"]

    C["Block BOTH simultaneously<br/>Drop stays low until layer 24<br/>Model uses alternative redundant paths<br/>before both become jointly essential"]

    note["Partial redundancy at early layers:<br/>blocking one path forces the model<br/>to lean on the other.<br/>Only when both are blocked<br/>does the mechanism fully collapse."]

    A & B & C --> note
```
