# Shared Glossary

All agents append here. No edits to prior entries.

---

- **Lookback mechanism**: The general pattern where a source token copies reference information to two locations (address + pointer), enabling later attention to retrieve a payload.
- **Ordering ID (OI)**: Internal tag assigned by the LM encoding relative order (first/second) of a character, object, or state token.
- **Binding lookback**: First mechanism — co-locates character OI and object OI into the state token's residual stream, forming a composite index.
- **Answer lookback**: Second mechanism — uses the state OI as a pointer to retrieve the actual state value from the matched state token.
- **Visibility lookback**: Third mechanism — generates a Visibility ID from observer/observed character OIs and uses it to transfer the observed character's state into the observer's belief.
- **Visibility ID**: Derived representation encoding the directed relation between two character OIs. f(observer_OI, observed_OI). Directional — not symmetric.
- **IIA (Interchange Intervention Accuracy)**: Metric measuring whether patching a specific activation from a counterfactual run changes the model's output. IIA=1.0 → this activation is the causal mechanism.
- **Residual stream**: The accumulating hidden vector for each token across all transformer layers. Fixed width (e.g., 8192D for Llama-3-70B). Each layer adds a delta via residual connection.
- **Co-location**: Two pieces of information stored in different subspace slots of the same token's residual stream vector simultaneously.
- **Low-rank subspace**: A small-dimensional region within the high-dimensional residual stream where specific information (e.g., OIDs) is encoded. Findable via PCA/SVD.
- **CausalToM**: The synthetic ToM dataset constructed by the paper. Two-character restaurant stories with controlled visibility conditions and counterfactual pairing.
- **BigToM**: Real-world ToM benchmark (Gandhi et al., 2024) used to test generalization of the lookback mechanism beyond synthetic stories.
- **Causal mediation analysis**: Method for identifying causal activations by patching specific (token, layer) activations between runs and measuring output change.
- **Attention knockout**: Experiment blocking specific attention paths (token A cannot attend to token B) to identify which connections are load-bearing at each layer.
- **QK-circuit**: The attention head's query-key matching operation — determines which tokens attend to which.
- **OV-circuit**: The attention head's output operation — determines what information is copied to the attending token.
- **NDIF**: National Deep Inference Fabric — Bau Lab's remote inference infrastructure used to run experiments on 70B/405B models.
