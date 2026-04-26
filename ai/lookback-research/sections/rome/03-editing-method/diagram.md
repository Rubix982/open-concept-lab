# Editing Method — Diagrams

## 1. MLP as linear associative memory

```mermaid
flowchart TD
    subgraph "W_proj — the phone book"
        K["Keys K<br/>= subject representations<br/>['Steve Jobs', 'Bill Gates', 'Eiffel Tower', ...]<br/>each a D_MLP-dimensional vector"]
        V["Values V<br/>= object representations<br/>['Apple', 'Microsoft', 'Paris', ...]<br/>each a D_MODEL-dimensional vector"]
        W["W_proj learns W ≈ V K†<br/>so that W @ k_jobs ≈ v_apple<br/>W @ k_gates ≈ v_microsoft<br/>W @ k_eiffel ≈ v_paris"]
    end

    K & V --> W
    W --> Query["Query at inference:<br/>W @ k_jobs → v_apple → 'Apple'"]
```

---

## 2. Why rank-one is the optimal answer

```mermaid
flowchart TD
    Problem["Constrained optimization:<br/>minimize ‖Ŵ K - V‖<br/>subject to Ŵ k* = v*<br/><br/>= disturb other facts as little as possible<br/>  while correctly storing the new fact"]

    Solution["Closed-form solution:<br/>Ŵ = W + Λ(C⁻¹k*)ᵀ<br/><br/>This is ONE outer product<br/>= rank-one matrix<br/>= minimum-norm update"]

    Why["Why rank-one is optimal:<br/>Rank-one = one degree of freedom<br/>Any higher-rank update would change more<br/>The math guarantees this is minimal"]

    Problem --> Solution --> Why
```

---

## 3. Weights vs activations — what changes

```mermaid
flowchart LR
    subgraph "Lookback paper / causal tracing"
        A["Patches ACTIVATIONS<br/>residual stream values<br/>Shape: (D_MODEL,) per token<br/>Duration: one forward pass<br/>Reversible: yes"]
    end

    subgraph "ROME"
        B["Changes WEIGHTS<br/>W_proj matrix entries<br/>Shape: (D_MODEL × D_MLP)<br/>Duration: permanent<br/>Reversible: only with backup"]
    end

    subgraph "L0 Decoder (your direction)"
        C["Reads ACTIVATIONS<br/>real-time, inference<br/>Does not modify<br/>Flags uncertain beliefs<br/>Triggers ROME if needed"]
    end

    A -->|"measurement only"| C
    C -->|"flag → trigger edit"| B
```

---

## 4. The two constraints

```mermaid
flowchart TD
    HC["Hard constraint<br/>Ŵ k* = v*<br/><br/>'After the edit, the model MUST<br/>produce v* when it processes Steve Jobs'<br/>Non-negotiable. Correctness."]

    SC["Soft constraint<br/>minimize ‖Ŵ K - V‖<br/><br/>'Disturb other facts as little as possible'<br/>Minimizing this = specificity<br/>The rank-one solution achieves the minimum"]

    HC & SC --> RO["Rank-one update<br/>W + Λ(C⁻¹k*)ᵀ<br/>satisfies both simultaneously"]
```

---

## 5. The three steps

```mermaid
flowchart LR
    subgraph "Step 1 — compute_u"
        K1["k* = avg representation<br/>of subject at last token<br/>layer l*, after σ(W_fc ...)<br/>averaged over 50 contexts<br/>→ stable, context-robust key"]
    end

    subgraph "Step 2 — compute_v"
        V1["v* = optimize delta (20 steps)<br/>Term 1: maximize P(target | prompt)<br/>Term 2: KL divergence on 'subject is a'<br/>Term 3: weight decay<br/>→ desired MLP output"]
    end

    subgraph "Step 3 — rome_main"
        U1["Λ = (v* - W@k*) / dot(k*, C⁻¹k*)<br/>W_new = W + outer(Λ, C⁻¹k*)<br/>→ one matrix update, done"]
    end

    K1 --> V1 --> U1
```

---

## 6. Figure 5 — editing confirms causal tracing

```mermaid
flowchart TD
    CT["Causal tracing finds:<br/>Layer 17, last subject token<br/>is DECISIVE for recall<br/>(high AIE)"]

    Edit["ROME editing shows:<br/>Editing layer 17, last subject token<br/>produces BEST results<br/>(peak efficacy + specificity)"]

    Confirm["Together → bidirectional confirmation:<br/>The fact is STORED at that location<br/>AND causally RECALLED from there<br/>→ Localized Factual Association Hypothesis confirmed"]

    Other["Editing wrong layer (early/late):<br/>poor generalization or specificity<br/>Editing wrong token:<br/>poor on both metrics<br/>→ the location is specific, not diffuse"]

    CT & Edit --> Confirm
    Other -.- Confirm
```

---

## 7. The complete system — locate, profile, edit

```mermaid
flowchart LR
    L["LOCATE<br/>Causal tracing<br/>Find (layer, token)<br/>where belief is causal"]

    P["PROFILE<br/>RetrievalProfile<br/>Score confidence:<br/>established / contested"]

    E["EDIT<br/>ROME<br/>W_new = W + Λ(C⁻¹k*)ᵀ<br/>Install corrected belief"]

    L --> P
    P -->|"if contested or wrong"| E
    P -->|"if established"| OUT["Trust output<br/>no edit needed"]
    E --> OUT2["Corrected output<br/>belief updated permanently"]
```
