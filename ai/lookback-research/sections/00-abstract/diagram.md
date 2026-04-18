# Abstract — Diagrams

## 1. The Theory of Mind Problem (Sally-Anne in LLM form)

```mermaid
flowchart TD
    A["Story Input\n'Bob fills bottle with beer.\nCarla fills cup with coffee.'"]
    B["Internal Representation\n(Bob, bottle, beer)\n(Carla, cup, coffee)"]
    C{"Visibility?\nDid Bob see Carla?"}
    D["Bob's belief = beer\n(his own action)"]
    E["Bob's belief = coffee\n(he observed Carla)"]
    F["Bob's belief = unknown\n(he didn't observe Carla)"]

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
    C["Character Token\n'Bob' (OI = first)"]
    O["Object Token\n'bottle' (OI = first)"]
    S["State Token\n'beer'"]

    C -->|"OI written into"| S_vec
    O -->|"OI written into"| S_vec

    S_vec["State Token Residual Stream\n[ ... OI_char=1, OI_obj=1 ... ]\n(both co-located here)"]

    S_vec -->|"later, at question token"| Q["Question Token\n'What does Bob believe?'\nLooks up: OI_char=1 + OI_obj=1 → retrieves beer"]
```

---

## 4. Residual Stream as Running Memory

```mermaid
flowchart LR
    T["Token 'beer'"]
    T --> L1["After Layer 1\nvec += attn_output_1"]
    L1 --> L2["After Layer 2\nvec += attn_output_2"]
    L2 --> L3["After Layer 3\nvec += mlp_output_3"]
    L3 --> Ln["... (80 layers)"]
    Ln --> Final["Final vector\naccumulated from all layers\n= residual stream"]
```
