# Results — Diagrams

## 1. The two failure modes every method hits

```mermaid
flowchart TD
    F1["F1 — Overfitting<br/>Edit works on exact template<br/>fails on rephrasing<br/><br/>High Efficacy, Low Paraphrase<br/>Model regurgitates target word<br/>without understanding the fact"]

    F2["F2 — Bleedover<br/>Edit spreads to unrelated subjects<br/><br/>High Paraphrase, Low Specificity<br/>Model applies new fact too broadly<br/>corrupts neighboring knowledge"]

    subgraph "Who hits what"
        FT["FT: solves F1 ✓<br/>hits F2 ✗<br/>(bleeds everywhere)"]
        FTL["FT+L: solves F2 ✓<br/>hits F1 ✗<br/>(won't generalize)"]
        KE_M["KE / MEND: hits both ✗"]
        ROME_r["ROME: solves both ✓"]
    end

    F1 & F2 --> FT & FTL & KE_M & ROME_r
```

---

## 2. The Pierre Curie test — generalization vs specificity

```mermaid
flowchart TD
    Edit["Insert: 'Pierre Curie's area of work is medicine'<br/>(he is actually a physicist)"]

    subgraph "Generalization test"
        G1["ROME: coherent, medicine-consistent text ✓"]
        G2["FT: similar generalization ✓"]
        G3["KE: 'medicine medicine medicine...' ✗<br/>(repetition, incoherent)"]
        G4["FT+L: alternates medicine/physics by prompt ✗"]
    end

    subgraph "Specificity test — Robert Millikan (unrelated)"
        S1["Before edit: GPT-2 describes Millikan as astronomer"]
        S2["After ROME: still astronomer ✓"]
        S3["After FT: physician ✗  (bleedover)"]
        S4["After KE/MEND: medical scientist ✗  (bleedover)"]
    end

    Edit --> G1 & G2 & G3 & G4
    Edit --> S1 --> S2 & S3 & S4
```

---

## 3. The confirmation loop — how Figure 5 proves the hypothesis

```mermaid
flowchart LR
    CT["Causal Tracing (Section 2)<br/>Found: layer 17, last subject token<br/>has highest AIE (indirect effect)<br/>→ most decisive for fact recall"]

    F5["Figure 5 — ROME editing sweep<br/>Targeted every (layer, token) combo<br/>Measured: Score = f(Efficacy, Paraphrase, Specificity)"]

    Peak["Peak editing performance:<br/>Layer 17-18, last subject token<br/>= same location as causal tracing peak"]

    Confirm["Bidirectional confirmation:<br/>Causal tracing: this location is DECISIVE<br/>Editing success: this location STORES the fact<br/>→ Localized Factual Association Hypothesis ✓"]

    CT --> F5 --> Peak --> Confirm
```

---

## 4. ROME vs Lookback — the complete picture

```mermaid
flowchart TD
    subgraph "ROME (2022)"
        R1["World knowledge from training<br/>Real entities: Steve Jobs, Paris, etc."]
        R2["Storage location:<br/>MLP weights at middle layers<br/>last subject token"]
        R3["Can edit: YES<br/>W_new = W + Λ(C⁻¹k*)ᵀ"]
    end

    subgraph "Lookback (2026)"
        L1["In-context beliefs from prompt<br/>Synthetic entities: Bob, Carla, etc."]
        L2["Retrieval mechanism:<br/>OID lookback via attention heads<br/>binding L14-34, answer L33-79"]
        L3["Can edit: NOT YET<br/>activation patching only for measurement"]
    end

    subgraph "Open question"
        Q["Does ROME-editing the MLP storage<br/>corrupt the Lookback retrieval mechanism?<br/>Storage (ROME) ↔ Retrieval (Lookback)<br/>Are they independent?"]
    end

    R2 & L2 --> Q

    note["Same causal methodology.<br/>Same research group.<br/>Different knowledge types.<br/>Complementary findings."]
```

---

## 5. KN — the failed predecessor (same research group as Lookback)

```mermaid
flowchart LR
    KN["Knowledge Neurons (Dai et al. 2022)<br/>Same idea: locate knowledge, edit it<br/>Method: gradient attribution → neuron rows<br/>Result: Score 35.6 — fails F1 + F2"]

    ROME_kn["ROME (Meng + Bau 2022)<br/>Better localization: causal tracing<br/>Better editing: rank-one update<br/>Result: Score 89.2 — solves both"]

    Lookback_kn["Lookback (Prakash + Bau 2026)<br/>Dai et al. also discover Ordering IDs<br/>Retrieval mechanism via attention heads<br/>The same group, 4 years later"]

    KN -->|"shows localization matters"| ROME_kn
    KN -->|"same first author"| Lookback_kn

    note["Progression: KN (attribution-based, crude)<br/>→ ROME (causal tracing, rank-one)<br/>→ Lookback (causal mediation, full mechanism)"]
```
