# Glossary

_Append-only. All agents contribute._

- **ROME**: Rank-One Model Editing — locates and edits a single factual association in a transformer MLP via a rank-1 weight update. Does not require retraining.
- **MEMIT**: Mass-Editing Memory in a Transformer — extends ROME to thousands of simultaneous edits by distributing updates across multiple layers.
- **Subject**: The entity being edited (e.g. "Eiffel Tower").
- **Relation**: The predicate connecting subject to object (e.g. "is located in").
- **Object**: The target value before the edit (e.g. "Paris").
- **Object\***: The target value after the edit (e.g. "Rome").
- **Neighbor fact (N)**: A fact logically entailed by the edited fact. Classified by hop distance from the edit.
  - N0: The exact edited fact (paraphrase probe).
  - N1: One-hop entailment (direct consequence, e.g. country from city).
  - N2: Two-hop entailment (country → language, currency, etc.).
  - N4: Reverse lookup (what else is in the new location?).
- **Ripple effect**: The failure of neighbor facts to update after a model edit.
- **Causal tracing**: NNSight-based activation patching to identify which layer causally mediates a factual recall.
- **IIA**: Indirect Intervention Accuracy — how much does patching a layer restore the counterfactual answer?
- **GRACE**: General Retrieval Adaptors for Continual Editing — editing via a codebook of adaptors, not weight updates.
- **WISE**: Editing via a side memory that intercepts relevant queries.
- **CounterFact**: Evaluation dataset for model editing; 21,919 subject-relation-object triples with paraphrases and neighborhood facts.
