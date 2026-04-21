# ROME Glossary

Running index of ROME-specific terms. Append as we encounter new ones.

---

- **Auto-regressive**: model generates one token at a time, seeing only prior tokens. Each output is fed back as the next input.

- **Factual association**: a (subject, relation, object) triple stored in model weights during training. e.g. (Space Needle, located in, Seattle). World knowledge, not task reasoning.

- **Causal tracing**: ROME's name for causal mediation analysis. Clean + corrupted run pairs, patch activations, measure indirect effect. Same method as IIA in the Lookback paper.

- **Indirect effect**: change in output caused by restoring one specific activation while everything else stays corrupted. High = that activation is load-bearing for the prediction.

- **Feed-forward MLP**: second sub-layer in each transformer block (after attention). ROME finds facts stored HERE. Different from Lookback which focuses on attention heads and residual stream.

- **Rank-One Model Editing (ROME)**: updates a single weight matrix with a rank-one perturbation — minimal surgical change altering one factual association without disrupting others.

- **Subject token**: the token(s) representing the entity being asked about (e.g. "Space Needle"). ROME finds the *last* subject token is the decisive position.

- **Two-input system**: the model's output is a function of both the context you provide AND the weight-stored beliefs from training. You control only one.

- **Weight-stored belief**: a fact or association encoded in model weights during training. Persists across conversations. Can contradict correct context and override it in instruction-tuned models.
