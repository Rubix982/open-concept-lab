# Research Questions

This document captures the main questions a researcher would naturally ask about the Citation Graph Node Classifier project. It is intended to serve as the experiment backlog for future analysis modes, ablations, and benchmark extensions.

## How to use this document

- Use these questions to prioritize new experiment modes.
- Treat each section as a research theme with multiple concrete investigations.
- Start with the "Model Behavior" section when adding new CLI modes or evaluation pipelines.

## Model Behavior

These questions focus on what the GCN is learning and why it works.

- How much predictive signal comes from citation neighbors versus the raw bag-of-words node features?
- How far does performance drop if the graph is removed and the model uses only node features?
- How far does performance drop if features are removed and the model uses only graph structure?
- Why is a 2-layer GCN a good fit here, and what changes with 1-layer or 3-layer variants?
- Does the model show signs of over-smoothing as depth increases?
- Do the hidden embeddings separate topic clusters cleanly, or do they mix closely related classes?
- Which nodes change the most after neighbor aggregation, and what does that say about the value of message passing?
- Are predictions driven more by local graph structure or by strong lexical features?

Current implementation hooks for this section:

- `baseline`: standard 2-layer reference run
- `feature-only`: isolates lexical signal by removing propagation
- `graph-only`: isolates structural signal by removing lexical features
- `depth-ablation`: compares 1, 2, and 3 graph-convolution layers
- `over-smoothing`: reports pairwise cosine similarity and embedding variance across depths
- `embedding-separation`: reports class centroid distances and within-class dispersion

## Data Questions

These questions focus on what the dataset makes easy or difficult.

- Which of the 7 Cora classes are easiest to classify, and which are hardest?
- Are high-degree papers classified more accurately than low-degree papers?
- Do isolated or weakly connected nodes behave differently from densely connected ones?
- How homophilous is the graph, meaning how often do same-topic papers cite each other?
- Does class imbalance materially affect training or evaluation?
- How sensitive is the model to missing or noisy citations?
- Are there feature dimensions that dominate predictions for certain classes?
- Do some classes cluster better in feature space than in graph space?

## Training Setup

These questions focus on the learning procedure and optimization choices.

- How sensitive are results to the standard 140-node labeled training split?
- How much metric variance appears across different random seeds and random splits?
- What tradeoff do dropout, hidden size, learning rate, and weight decay create?
- Does early stopping on validation accuracy improve test performance?
- Is training numerically stable across seeds and hyperparameter settings?
- Does the manual backprop implementation match numerical gradient checks?
- How quickly does the model converge, and are later epochs still useful?
- Are there signs of underfitting or overfitting in the loss and accuracy curves?

## Evaluation

These questions focus on measurement quality beyond one aggregate score.

- What are the per-class precision, recall, and F1 scores?
- What does the confusion matrix reveal about closely related topics?
- Are misclassified nodes structurally unusual, lexically ambiguous, or both?
- Is the model well calibrated, or is it overconfident on wrong predictions?
- Are errors concentrated around low-degree, low-feature, or cross-topic boundary nodes?
- Which nodes are confidently wrong, and what patterns do they share?
- Does validation accuracy track test accuracy reliably in this setup?

## Graph Structure

These questions focus on how graph design choices affect results.

- What is the contribution of self-loops in the normalized adjacency matrix?
- What is the contribution of symmetric normalization?
- What information is lost by converting directed citations into an undirected graph?
- Does pruning noisy edges improve the classifier?
- Do weighted edges or multi-hop edges help?
- How much of the signal comes from 1-hop versus 2-hop neighborhoods?
- How do graph density and degree distribution shape the learned representation?

## Representation Learning

These questions focus on what the latent space captures.

- Do t-SNE clusters align with gold topic labels?
- Do embeddings reveal subtopics within a single class?
- Can learned embeddings be reused for downstream retrieval, ranking, or clustering tasks?
- Are same-class but graph-distant papers still near each other in embedding space?
- Do embeddings capture popularity and degree effects in addition to topic semantics?
- Which dimensions of the hidden representation are most discriminative?

## Baselines And Comparisons

These questions focus on whether the GCN is truly adding value.

- How does the manual GCN compare with logistic regression on raw features?
- How does it compare with a plain MLP that ignores graph structure?
- How does it compare with label propagation?
- How close are results to a PyTorch or PyG implementation of the same architecture?
- How do GraphSAGE or GAT compare under the same split and metrics?
- Is the extra complexity of graph convolution justified by the observed gain?

## Robustness

These questions focus on how brittle or stable the system is.

- How much does performance degrade when citations are randomly removed?
- What happens when noisy or adversarial edges are injected?
- How stable are embeddings across seeds?
- Is the model biased toward well-cited papers?
- Does the model generalize when new subfields or shifted topic distributions are introduced?
- Which failures are graceful and which ones are catastrophic?

## Systems And Infra

These questions focus on reproducibility, scaling, and workflow integration.

- How useful is DuckDB for graph inspection and experiment analysis?
- What are the main preprocessing and training bottlenecks?
- How well would this pipeline scale to larger citation datasets?
- Which parts should remain NumPy-based and which should eventually move to PyTorch?
- Can SQL-based dataset inspection be integrated directly into experiment reporting?
- What metadata should be persisted for reproducible runs?

## Research Extensions

These questions focus on where the project can grow next.

- How can this setup be extended to heterogeneous graphs with papers, authors, and venues?
- Would temporal citation edges improve the representation?
- Can the model be adapted for link prediction or recommendation?
- Can the embeddings support ranking tasks related to NSF Ranker or knowledge graph retrieval?
- What is the right path from semi-supervised node classification to a more production-oriented graph intelligence system?
- Which of these directions are best suited for a short experiment versus a publication-grade study?

## Suggested Prioritization

If the goal is to add experiment modes incrementally, a practical order is:

1. Model behavior ablations
2. Baseline comparisons
3. Per-class evaluation and error analysis
4. Robustness experiments
5. Representation diagnostics
6. Larger research extensions
