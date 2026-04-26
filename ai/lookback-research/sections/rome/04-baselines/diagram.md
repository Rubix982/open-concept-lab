# Baselines — Diagrams

## 1. What each method does to the weight matrix

```mermaid
flowchart TD
    subgraph "FT — Fine-Tuning"
        FT1["Compute gradient<br/>∂Loss/∂W<br/>shape: 1600 × 6400"]
        FT2["W_new = W - lr × gradient<br/><br/>ALL 10M weights nudged<br/>No knowledge of which ones<br/>store which facts"]
        FT1 --> FT2
    end

    subgraph "KE — Knowledge Editor"
        KE1["Encode fact<br/>('Steve Jobs', 'Microsoft')<br/>→ fact_vector"]
        KE2["Hypernetwork H(fact_vector)<br/>→ predicted ΔW<br/><br/>H learned from examples<br/>No access to current W"]
        KE3["W_new = W + ΔW"]
        KE1 --> KE2 --> KE3
    end

    subgraph "MEND"
        ME1["Compute gradient g<br/>Decompose: g ≈ u @ v.T<br/>(low-rank factors)"]
        ME2["Hypernetwork H(u, v)<br/>→ refined u', v'<br/><br/>H learned to clean up gradients<br/>Uses gradient shape as map"]
        ME3["W_new = W + u' @ v'.T"]
        ME1 --> ME2 --> ME3
    end

    subgraph "ROME"
        R1["compute_u:<br/>u = normalize(C⁻¹ @ k_subject)<br/>Exact subject direction"]
        R2["compute_v:<br/>v* = optimize delta<br/>Desired MLP output"]
        R3["Λ = (v* - Wk*) / dot(k*, u)<br/>W_new = W + outer(Λ, u)<br/><br/>ONE direction changed<br/>Algebraic, no training"]
        R1 & R2 --> R3
    end
```

---

## 2. What changes in the weight matrix — visually

```mermaid
flowchart LR
    subgraph "W  (1600 × 6400 weights)"
        S["Steve Jobs<br/>direction"]
        B["Bill Gates<br/>direction"]
        P["Paris<br/>direction"]
        O["...other facts..."]
    end

    subgraph "FT update"
        FT["Gradient touches ALL directions<br/>S ← changes<br/>B ← changes too<br/>P ← changes too<br/>→ specificity breaks"]
    end

    subgraph "ROME update"
        R["Rank-one update moves only direction u<br/>u ≈ Steve Jobs direction<br/>S ← changes ✓<br/>B ← unchanged ✓<br/>P ← unchanged ✓<br/>→ specificity preserved"]
    end

    W --> FT
    W --> R
```

---

## 3. KE vs MEND — what the hypernetwork receives

```mermaid
flowchart TD
    subgraph "KE input"
        KE_in["fact_vector<br/>= encode('Steve Jobs') + encode('Microsoft')<br/><br/>Just the new fact.<br/>No information about current W.<br/>No information about which weights matter."]
    end

    subgraph "MEND input"
        ME_in["gradient g (decomposed)<br/>= ∂Loss/∂W compressed to (u, v)<br/><br/>The gradient shape tells you:<br/>'these directions in W were activated<br/>when predicting the target'<br/>More information than fact alone."]
    end

    subgraph "ROME — no hypernetwork"
        R_in["C⁻¹ @ k_subject<br/>= exact causal direction<br/>from 100k Wikipedia statistics<br/><br/>Not learned. Not predicted.<br/>Computed from the data."]
    end

    KE_in -->|"less info → less targeted"| KE_out["ΔW (predicted)"]
    ME_in -->|"more info → more targeted"| ME_out["ΔW (refined gradient)"]
    R_in  -->|"exact info → surgical"| R_out["outer(Λ, u) (algebraic)"]
```

---

## 4. The specificity-generalization tradeoff

```mermaid
flowchart TD
    T["The tradeoff every method before ROME hits"]

    A["Aggressive edit<br/>(change many weights)"]
    B["Conservative edit<br/>(change few weights)"]

    A --> AG["High generalization ✓<br/>(works for any phrasing)"]
    A --> AS["Low specificity ✗<br/>(bleeds into neighbors)"]

    B --> BG["Low generalization ✗<br/>(only works on exact template)"]
    B --> BS["High specificity ✓<br/>(neighbors untouched)"]

    ROME["ROME escapes the tradeoff<br/>Changes ALL weights in the layer<br/>BUT only along direction u<br/><br/>→ Broad enough for generalization<br/>   (any prompt activating k_subject hits the edit)<br/>→ Narrow enough for specificity<br/>   (other subjects' keys don't project onto u)"]

    T --> A & B
    A & B --> ROME
```

---

## 5. Results table — the numbers

```mermaid
xychart-beta
    title "CounterFact Score (higher = better, max 100)"
    x-axis ["FT", "FT+L", "KE", "KE-CF", "MEND", "MEND-CF", "ROME"]
    y-axis "Score" 0 --> 100
    bar [65.1, 66.9, 52.2, 18.1, 57.9, 14.9, 89.2]
```

---

## 6. Where KE-CF and MEND-CF fail — the distribution trap

```mermaid
flowchart LR
    subgraph "Trained on CounterFact distribution"
        CF["KE-CF / MEND-CF<br/>Learns: CounterFact edits<br/>require aggressive changes<br/>(facts start with low probability)"]
    end

    subgraph "Test: Specificity (neighboring subjects)"
        NS["Neighboring subjects<br/>are NOT in CounterFact<br/>distribution"]
    end

    CF -->|"applies same aggressive<br/>editing strategy"| NS
    NS --> FAIL["Specificity = 5-9%<br/>Nearly every neighbor broken<br/>Distribution shift = failure"]
```
