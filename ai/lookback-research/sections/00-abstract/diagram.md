# Abstract — Diagrams

## 1. The Theory of Mind Problem (Sally-Anne in LLM form)

```mermaid
flowchart TD
    A["Story Input<br/>'Bob fills bottle with beer.<br/>Carla fills cup with coffee.'"]
    B["Internal Representation<br/>(Bob, bottle, beer)<br/>(Carla, cup, coffee)"]
    C{"Visibility?<br/>Did Bob see Carla?"}
    D["Bob's belief = beer<br/>(his own action)"]
    E["Bob's belief = coffee<br/>(he observed Carla)"]
    F["Bob's belief = unknown<br/>(he didn't observe Carla)"]

    A --> B
    B --> C
    C -->|"No visibility info"| D
    C -->|"Bob observed Carla"| E
    C -->|"Bob did NOT observe Carla"| F
```

---

## 2. Causal Mediation — How It Works

```mermaid
flowchart LR
    subgraph "Run A (Story A)"
        A_in["Input A"] --> A_L1["Layer 1"] --> A_L2["Layer 2"] --> A_Ln["..."] --> A_out["Output A"]
    end

    subgraph "Run B (Story B)"
        B_in["Input B"] --> B_L1["Layer 1"] --> B_L2["Layer 2"] --> B_Ln["..."] --> B_out["Output B"]
    end

    subgraph "Patched Run"
        P_in["Input A"] --> P_L1["Layer 1"] --> P_L2["Layer 2 ← patched with B's activation"] --> P_Ln["..."] --> P_out["Output ?"]
    end

    B_L2 -->|"patch"| P_L2
    P_out -->|"if output flips to B → Layer 2 is a causal mediator"| verdict["Causal Mediator Found"]
```

---

## 3. Co-location in the Residual Stream

```mermaid
flowchart TD
    C["Character Token<br/>'Bob' (OI = first)"]
    O["Object Token<br/>'bottle' (OI = first)"]
    S["State Token<br/>'beer'"]

    C -->|"OI written into"| S_vec
    O -->|"OI written into"| S_vec

    S_vec["State Token Residual Stream<br/>[ ... OI_char=1, OI_obj=1 ... ]<br/>(both co-located here)"]

    S_vec -->|"later, at question token"| Q["Question Token<br/>'What does Bob believe?'<br/>Looks up: OI_char=1 + OI_obj=1 → retrieves beer"]
```

---

## 4. Residual Stream as Running Memory

```mermaid
flowchart LR
    T["Token 'beer'"]
    T --> L1["After Layer 1<br/>vec += attn_output_1"]
    L1 --> L2["After Layer 2<br/>vec += attn_output_2"]
    L2 --> L3["After Layer 3<br/>vec += mlp_output_3"]
    L3 --> Ln["... (80 layers)"]
    Ln --> Final["Final vector<br/>accumulated from all layers<br/>= residual stream"]
```
