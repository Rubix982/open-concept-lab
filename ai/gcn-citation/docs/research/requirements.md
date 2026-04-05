# Research Requirements: ProG-Scale arXiv Graph Learning

**Date**: 2026-04-04
**Status**: Living document — decisions made, open questions flagged
**Context**: Weekend personal research lab. Not a lab paper. Goal is deep understanding
through building, running, and observing — not SOTA benchmarks.

---

## 1. Vision

Build a graph learning system over the arXiv corpus (starting at 100K papers, scaling
toward 2M) that learns how scientific ideas relate, transfer, and cluster — across
disciplinary boundaries that citation structure and topic labels alone cannot capture.

This follows the **ProG paradigm**: pre-train a graph encoder once on the large graph
using self-supervised objectives, then adapt to any downstream task using lightweight
prompts — without touching the backbone.

**The real goal**: build enough hands-on intuition about graph pre-training and prompting
to understand what is actually happening inside these models. The arXiv corpus is the
playground. The experiments are the teacher.

### Three Exploratory Goals

These are the questions worth spending weekends on:

1. **Can a graph model learn cross-disciplinary idea similarity** — connections that
   citation structure and topic labels miss entirely?

2. **How does a model represent papers that don't belong cleanly to one field** — and
   can we design prompts that navigate that ambiguity?

3. **Do prompting methods actually hold up at scale on heterogeneous graphs** — or do
   they silently break in ways the original papers never tested?

These are expanded in Section 5.

---

## 2. Compute Constraints

**Hardware**: MacBook M2, Apple Metal (18-core GPU), unified memory (16-32GB)

### Implications

| Concern                            | 100K    | 500K    | 1M      | 2M (stretch) |
| ---------------------------------- | ------- | ------- | ------- | ------------ |
| SPECTER2 embedding                 | ~11 min | ~55 min | ~2 hrs  | ~3.5 hrs     |
| Feature storage                    | 300MB   | 1.5GB   | 3GB     | 6.1GB        |
| k-NN graph (FAISS CPU)             | ~2 min  | ~30 min | ~2 hrs  | ~4 hrs       |
| Training per epoch (mini-batch)    | fast    | ~5 min  | ~10 min | ~20 min      |
| Full pre-training run (200 epochs) | ~1 hr   | ~5 hrs  | ~10 hrs | ~30-40 hrs   |
| Citation graph edges               | ~2M     | ~10M    | ~20M    | ~50M         |

**Rule**: All training uses `torch.device("mps")` with mini-batch neighbor sampling.
Full-batch is only for Cora-scale sanity checks. FAISS runs on CPU (`faiss-cpu`).

### Scale Strategy

| Phase     | Target Scale | Rationale                                                               |
| --------- | ------------ | ----------------------------------------------------------------------- |
| Phase 0-1 | 10K → 100K   | Pipeline validation, baselines, fast iteration                          |
| Phase 2-3 | **500K**     | Beyond all published prompting benchmarks; tractable on M2 (~5 hrs/run) |
| Phase 4   | **1M**       | Credibly large-scale arXiv; one training run ~10 hrs on M2              |
| Stretch   | 2M           | Only if 1M results are compelling; ~30-40 hrs/run, likely needs cloud   |

**500K is the working scale for all comparative experiments** (pre-training and
prompting comparison). It is 3× larger than any GNN prompting paper has published
results on, and remains tractable on M2 with mini-batch training.

### Cloud Escape Valve

For experiments that genuinely need more compute (full-corpus GraphCL, large GT
backbone), use AWS spot instances or Google Colab A100. These are flagged in the
phase plan.

---

## 3. Data Pipeline

### 3.1 Source: arXiv Metadata Snapshot

The arXiv metadata snapshot is ~3.5GB uncompressed (~1.2GB compressed), containing
all 2.2M+ papers as JSONL — one JSON object per line.

**Access**: Free, no AWS account needed. Best sources:
- Kaggle: Cornell University arXiv dataset (direct download)
- HuggingFace datasets hub mirror
- Note: requester-pays restriction applies only to PDFs/LaTeX source, not metadata

**Key fields per record**: `id`, `title`, `abstract`, `categories` (space-separated
string — NOT a list), `update_date`, `authors_parsed`, `versions`

**Parsing gotchas**:
- `categories` is `"cs.LG stat.ML math.OC"` — must split on spaces
- Old-format IDs contain slashes (e.g. `math/0406594`) vs new-format (e.g. `1706.03762`)
- Stream line-by-line with `json.loads()` — too large to load at once

For **citation edges**: arXiv metadata does NOT include citations.

**Use OpenAlex** (replaces S2ORC — original S2ORC bulk links are defunct):
- CC0 license, no API key required, free S3 access via `--no-sign-request`
- 271M papers, arXiv ID in `ids.arxiv` field
- Citations stored as `referenced_works` per paper (outgoing only — reverse for full graph)
- Semantic Scholar Datasets API is an alternative (requires free API key, ODC-By license)

### 3.2 Node Features: SPECTER2

**Why SPECTER2**: trained on academic paper title+abstract pairs using citation-based
contrastive learning. Produces 768d embeddings encoding scientific meaning — not just
word co-occurrence.

**Why not TF-IDF**: uncontrolled dimensionality, no semantic generalization, degrades
at scale, cannot capture cross-disciplinary synonymy (key for Exploratory Goal 1).

**Embedding strategy**:

```
Input:   title + tokenizer.sep_token + abstract  (truncated to 512 tokens)
Model:   allenai/specter2_base + proximity adapter (allenai/specter2)
         Requires: pip install adapters  (separate from transformers)
Output:  768-dimensional float32 vector per paper
Storage: memory-mapped .npy file, loaded lazily during training
Batch:   32–64 papers per MPS batch, checkpoint by arXiv ID
Device:  float32 only on MPS — bfloat16 unsupported, float16 unstable
Env:     PYTORCH_ENABLE_MPS_FALLBACK=1 required
```

**Phase 0 shortcut**: Semantic Scholar Datasets API ships pre-computed SPECTER2
embeddings for arXiv papers. Check coverage before committing to local inference —
if sufficient, skip embedding entirely and download precomputed vectors.

**Simpler alternative for 10K prototyping**: `sentence-transformers/allenai-specter`
(no adapters library needed, slightly lower quality, much faster to set up).

**Important for Exploratory Goal 1**: SPECTER2 is itself trained on citations, so it
carries some cross-disciplinary signal already. The GNN pre-training adds graph
structure on top. A key question is: _how much does the GNN add beyond raw SPECTER2?_

### 3.3 Graph Construction

**Node types**:

- `Paper` — one node per arXiv paper (~2M total, ~100K working set)
- `Category` — one node per arXiv leaf category (`cs.LG`, `stat.ML`, etc., ~150 total)

**Edge types**:

| Edge Type     | Direction                 | Source                        | Semantics                  |
| ------------- | ------------------------- | ----------------------------- | -------------------------- |
| `cites`       | directed (A→B)            | S2ORC                         | Paper A references paper B |
| `similar_to`  | undirected                | FAISS k-NN on SPECTER2 (k=10) | Semantic proximity         |
| `belongs_to`  | directed (Paper→Category) | arXiv metadata                | Paper's stated categories  |
| `co_category` | undirected (Paper↔Paper)  | derived                       | Share ≥1 primary category  |

**Heterogeneous graph**: PyTorch Geometric `HeteroData`, one sparse adjacency per
edge type. Different edge types carry different information — experiments will test
which edges matter for which tasks (see Exploratory Goal 3).

**k-NN construction**: `faiss-cpu`, `IndexFlatIP` (cosine on L2-normalized vectors),
k=10. Store as COO sparse. Can recompute for different k values.

**Interdisciplinary papers** (relevant to Exploratory Goal 2): papers with 2+ primary
categories are explicitly flagged during graph construction. Store their category
membership as a multi-hot label AND as a node attribute for later analysis.

---

## 4. Downstream Task Definitions

### Task 1: Multi-label Topic Classification

- **Input**: paper node embedding
- **Output**: set of arXiv category labels (e.g. `{cs.LG, stat.ML}`)
- **Labels**: ~150 categories, multi-hot encoded
- **Challenge**: heavily imbalanced — `cs.LG` has ~300K papers; many categories <1K
- **Evaluation**: macro F1, micro F1, NDCG@5
- **Imbalance strategy**: weighted sampling, focal loss, or per-class evaluation

### Task 2: Hierarchical Category Prediction

- **Input**: paper node embedding
- **Output**: primary category leaf + top-level field
- **Labels**: 2-level — ~8 top-level fields (cs, math, physics...), ~150 leaf categories
- **Challenge**: papers at field boundaries (e.g. `cs.LG` + `stat.ML` + `math.OC`)
- **Evaluation**: accuracy at each level; separate eval for single-field vs boundary papers

### Task 3: Idea-Based Link Prediction

- **Input**: pair of paper nodes
- **Output**: probability of conceptual relationship (should be connected by a `similar_to` edge)
- **Positive edges**: held-out 15% of `similar_to` edges + held-out 10% of `cites` edges
- **Negative edges**: hard negatives — same top-level field, different leaf category
  (harder than random, more meaningful)
- **Evaluation**: AUC-ROC, Average Precision
- **Key distinction**: this is not just "are these papers similar?" — it is "does the
  GNN find connections that SPECTER2 cosine similarity alone misses?"

### Task 4: Community Detection (stretch goal)

- **Input**: subgraph
- **Output**: soft community assignments per node
- **Labels**: none (unsupervised); validate against known categories post-hoc
- **Evaluation**: NMI against arXiv categories, modularity score
- **Interest**: do learned communities match arXiv's own taxonomy, or find something different?

---

## 5. Three Exploratory Research Goals

These are the questions that make this project worth doing. Each has a concrete
experimental design, a success criterion, and a "what I will learn" framing.

---

### Goal 1: Cross-Disciplinary Idea Similarity

**The question**: Can a graph model learn that two papers are about the same idea,
even when they don't cite each other, don't share categories, and come from different
fields?

**Why this is hard**: Citation structure is biased toward same-field connections.
SPECTER2 captures semantic similarity but is trained on citations — so it inherits
the same bias. A variational inference paper from physics (1990) and a VAE paper from
ML (2014) share a deep idea but have no citation link and are in different arXiv
categories. Standard methods will not find this connection.

**Ground truth dataset** (build manually, ~100-200 pairs):
Known cross-disciplinary idea transfers to seed the evaluation:

| Physics/Math                 | ML/CS                        | Shared idea                 |
| ---------------------------- | ---------------------------- | --------------------------- |
| Langevin dynamics            | Diffusion models (DDPM)      | Score-based sampling        |
| Variational Bayes            | Variational Autoencoders     | ELBO + reparameterization   |
| Renormalization group        | Multiscale graph methods     | Hierarchical coarsening     |
| Belief propagation           | Graph neural message passing | Local message aggregation   |
| Ising model                  | Energy-based models          | Energy landscape, MCMC      |
| Principal component analysis | Autoencoders                 | Dimensionality reduction    |
| Optimal transport            | Wasserstein GAN              | Distribution matching       |
| Kalman filter                | Recurrent networks (LSTM)    | Sequential state estimation |

This is the evaluation set. The model never trains on these pairs — we check afterward
whether it finds them.

**Experimental steps**:

1. Build the arXiv graph (100K papers, mixed-field subset)
2. Compute baseline: SPECTER2 cosine similarity on the ground truth pairs
3. Pre-train GNN with GraphMAE (best for rich features)
4. Compute GNN embedding similarity on the same pairs
5. **Key measurement**: does the GNN bring cross-disciplinary pairs closer relative
   to SPECTER2? Compute the delta.
6. Visualize: UMAP of embeddings for papers near disciplinary boundaries — do
   idea-mates cluster together across field lines?
7. Failure analysis: which pairs does the model find? Which does it miss? Why?

**Success criterion**: GNN embedding similarity rank of known cross-disciplinary pairs
is meaningfully higher than SPECTER2 baseline rank. Even partial success (model finds
5/20 pairs that SPECTER2 misses) is informative.

**What I will learn**: whether graph structure (citation patterns, co-category
connections) adds signal for cross-field ideas, or whether the pre-trained language
model (SPECTER2) already captures most of it and the GNN adds little.

---

### Goal 2: The Interdisciplinary Node Problem

**The question**: How does a graph model represent papers that sit at the boundary
between fields — and can we prompt it to navigate that ambiguity?

**Why this is interesting**: Most GNN papers test on Cora and Citeseer where communities
are clean and non-overlapping. The arXiv corpus actively breaks this. A paper tagged
`cs.LG + stat.ML + math.OC` genuinely belongs to three communities. Standard node
classification forces a hard assignment. We want to understand what the model
actually learns about these boundary nodes.

**The boundary paper dataset**:
Partition papers into:

- **Single-field papers**: exactly one primary category (easy case)
- **Two-field papers**: exactly two primary categories (boundary case)
- **Multi-field papers**: three or more (hard case, genuinely interdisciplinary)

Evaluate all three groups separately in every experiment.

**Experimental steps**:

_Step 1 — Embedding geometry_:

- Train the GNN encoder on single-field papers only
- Ask: where do boundary papers land in embedding space?
- Hypothesis: they land between their two fields, not firmly in either
- Visualize with UMAP, color by primary vs secondary category

_Step 2 — Classification performance by boundary-ness_:

- Train multi-label classifier
- Compare F1 separately for single-field, two-field, multi-field papers
- Expected: performance degrades as papers get more interdisciplinary
- Interesting: by how much? Is it graceful degradation or cliff?

_Step 3 — Edge type contribution_:

- Train with `cites` edges only → evaluate on boundary papers
- Train with `similar_to` edges only → evaluate on boundary papers
- Train with both → evaluate on boundary papers
- Question: which edge type helps boundary papers more?
- Hypothesis: `similar_to` (semantic) helps more than `cites` (field-biased citations)

_Step 4 — Prompt for boundary navigation_:

- Design a GPF-plus prompt specifically for the question: "find papers that bridge
  field X and field Y"
- Evaluate: does the prompt successfully retrieve boundary papers from both fields?
- This requires defining "bridging" operationally: a paper that, when queried with
  the prompt, ranks high for papers from both X and Y

**Success criterion**: model shows meaningfully different representations for
boundary papers vs single-field papers. Edge type ablation reveals which edges
carry the cross-field signal. At least one prompting approach successfully retrieves
known bridging papers given field pair as query.

**What I will learn**: whether the graph structure (and which edge type) is the key
ingredient for handling multi-community nodes, vs whether it's irrelevant and the
SPECTER2 features already encode all of it.

---

### Goal 3: Prompting Methods at Heterogeneous Scale

**The question**: Do GPF, Gprompt, GPPT, and All-in-one actually hold up when the
graph is large, heterogeneous, and multi-task — or do they fail in ways the original
papers never tested?

**Why this matters**: Every prompting paper tests on Cora (2,708 nodes), Citeseer
(3,327 nodes), or similar small homogeneous benchmarks. Nobody has tested these
methods on a 100K-node heterogeneous graph with three edge types and three concurrent
tasks. The failure modes are unknown.

**Potential failure modes to look for**:

- **Scale degradation**: accuracy drops as N grows (prompt optimization becomes harder)
- **Task interference**: tuning the prompt for Task 1 hurts Task 3 performance
- **Edge type sensitivity**: prompt optimized on `cites` edges generalizes poorly to
  `similar_to` edges (or vice versa)
- **Heterogeneity confusion**: model trained on homogeneous graph; prompt applied to
  heterogeneous graph — does it break?
- **Few-shot collapse**: prompting works at 10-shot but falls apart at 5-shot at scale

**Experimental steps**:

_Step 1 — Scale stress test_:

- Take best pre-trained encoder from Goal 1 experiments
- Apply GPF-plus prompt on graphs of size: 1K, 5K, 10K, 50K, 100K nodes
- Measure Task 1 accuracy and prompt training loss at each scale
- Plot: accuracy vs scale, convergence speed vs scale

_Step 2 — Task interference test_:

- Train one prompt jointly for Task 1 + Task 3
- Compare against: two separate prompts (one per task)
- Measure: does joint prompting hurt either task? By how much?
- Try: All-in-one's unified task representation vs GPF-plus with separate vectors

_Step 3 — Edge type sensitivity_:

- Train prompt using `cites`-only graph
- Evaluate on `similar_to`-only graph (and vice versa)
- Measure: how much does the edge type used during prompt training affect test performance?
- This tells you whether the prompt is learning to use graph structure or just node features

_Step 4 — Method comparison at 100K_:

- Run GPF-plus, Gprompt, GPPT, All-in-one on same 100K graph
- Same pre-trained backbone, same tasks, same few-shot budget (5-shot, 10-shot)
- Primary metric: Task 1 macro F1, Task 3 AUC-ROC
- Secondary metric: prompt training time, memory usage on M2

**Success criterion**: produces a clear picture of which method degrades most
gracefully at scale, which is most sensitive to edge type, and whether multi-task
prompting is worth the complexity vs separate task-specific prompts.

**What I will learn**: whether prompting is robust or fragile at real-world scale,
which design choices matter most, and whether All-in-one's added complexity actually
pays off for multi-task scenarios.

---

## 6. Pre-training Methods (Comparative Study)

All methods share the same backbone (mini-batch GraphSAGE or GT) and the same graph.
Comparison isolates the pre-training objective.

### Method 1: DGI (Deep Graph Infomax)

- **Mechanism**: maximize mutual information between node embeddings and global
  graph summary. Corrupted graph as negatives.
- **Best alignment**: Tasks 1, 2 (node classification)
- **Augmentation**: graph corruption (shuffle node features)
- **M2 feasibility**: yes — mini-batch compatible

### Method 2: GraphMAE (Graph Masked Autoencoder)

- **Mechanism**: randomly mask ~50% of node features, reconstruct with scaled cosine loss
- **Best alignment**: Tasks 1, 2 — especially strong with rich features (SPECTER2 qualifies)
- **Augmentation**: none beyond masking
- **M2 feasibility**: yes — most memory-efficient
- **Recommended starting point**: best theoretical fit for SPECTER2 features

### Method 3: SimGRACE (Simple Graph Contrastive)

- **Mechanism**: perturb encoder weights (not graph) to create two views, contrastive loss
- **Rationale for arXiv**: dropping citation edges changes meaning; encoder perturbation avoids this
- **Best alignment**: general-purpose
- **Augmentation**: none — encoder perturbation only
- **M2 feasibility**: yes

### Method 4: GraphCL (Graph Contrastive Learning)

- **Mechanism**: graph augmentations (edge dropping, node masking, subgraph sampling)
  - contrastive loss
- **Best alignment**: Tasks 3, 4
- **Augmentation**: yes — multiple strategies, careful tuning needed for citation graphs
- **M2 feasibility**: yes, more compute than SimGRACE

### Method 5: EdgePre Family (EdgePreGPT / EdgePreGprompt)

- **Mechanism**: pre-train on edge existence prediction (binary node pair classification)
- **Best alignment**: Task 3 (pre-training task = downstream task)
- **Note**: these variants combine edge pre-training with prompt-compatible architectures
- **M2 feasibility**: yes — naturally mini-batch

### Comparison Framework

All methods evaluated identically after pre-training:

- Zero-shot: frozen encoder + linear probe
- Few-shot: frozen encoder + prompt (5-shot, 10-shot)
- Full fine-tune: unfreeze encoder (upper bound reference)

**Sequencing**: run GraphMAE first (best fit + easiest). Use its results to calibrate
expectations before implementing the others.

---

## 7. Prompting Methods

**Goal**: one frozen pre-trained encoder, multiple downstream tasks, minimal labels.

### Method 1: GPF-plus (Graph Prompt Feature)

- **Mechanism**: add a learnable feature vector to all input nodes before encoder
- **Multi-task**: yes — different prompt vector per task
- **Limitation**: same prompt for all nodes regardless of local structure
- **Start here** — simplest to implement, good baseline

### Method 2: GPPT (Graph Pre-trained Prompt Tuning)

- **Mechanism**: prepend task-specific token to node representation; reformulates
  classification as link prediction between node and class prototype
- **Best for**: Tasks 1, 2 (node classification)
- **Multi-task**: partial

### Method 3: Gprompt

- **Mechanism**: learnable prompt token combined with node features via inner product readout
- **Best for**: node and graph classification
- **Multi-task**: yes, via task-specific tokens

### Method 4: All-in-one

- **Mechanism**: prompt is a small subgraph prepended to input graph; handles node
  classification, link prediction, and graph classification in one framework
- **Best alignment**: yes — our three tasks cover all three types
- **Most complex** — implement last, after simpler methods are understood
- **Multi-task**: yes, by design

---

## 8. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  arXiv bulk S3 (metadata) + S2ORC (citations)                   │
│  → SPECTER2 embeddings (768d, MPS batched)                      │
│  → HeteroGraph:                                                 │
│      Nodes: Paper (~2M), Category (~150)                        │
│      Edges: cites | similar_to | belongs_to | co_category       │
│      Flags: interdisciplinary papers marked explicitly          │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     PRE-TRAINING LAYER                          │
│  Backbone: mini-batch GraphSAGE (default) or GT (experimental)  │
│  Objectives compared:                                           │
│    GraphMAE → SimGRACE → DGI → GraphCL → EdgePre                │
│    (implement in this order)                                    │
│  Output: frozen node encoder E(·)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     PROMPTING LAYER                             │
│  Frozen E(·) + task-specific learnable prompt P_t               │
│  Methods compared:                                              │
│    GPF-plus → Gprompt → GPPT → All-in-one                       │
│    (implement in this order)                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM TASKS                             │
│  Task 1: Multi-label topic classification                       │
│  Task 2: Hierarchical category prediction                       │
│  Task 3: Idea-based link prediction                             │
│  Task 4: Community detection (stretch)                          │
│                                                                 │
│  Evaluated separately for:                                      │
│    Single-field | Two-field | Multi-field papers                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Phased Implementation Plan

| Phase   | Scale      | Purpose                                                |
| ------- | ---------- | ------------------------------------------------------ |
| 0-1     | 10K → 100K | Pipeline validation, baselines, fast iteration         |
| 2-3     | **500K**   | All comparative experiments (pre-training + prompting) |
| 4       | **1M**     | Scale demonstration, final evaluation                  |
| Stretch | 2M         | Only if 1M is solid and compute permits                |

### Phase 0: Foundation Infrastructure (2-3 weekends)

_Goal: end-to-end pipeline working on a 10K-paper subgraph._

**Data**:

- [ ] arXiv bulk S3 downloader — streaming JSON parser, resume support
- [ ] Filter and sample 10K working subset (balanced categories + interdisciplinary papers)
- [ ] SPECTER2 embedding pipeline — MPS batching, checkpoint by arXiv ID, store as mmap `.npy`
- [ ] S2ORC citation data downloader + arXiv ID alignment (verify license first)

**Graph**:

- [ ] HeteroGraph builder: Paper nodes + `cites` edges + `similar_to` k-NN edges
- [ ] Category nodes + `belongs_to` edges
- [ ] Flag interdisciplinary papers (2+ primary categories)
- [ ] PyG `HeteroData` export + sanity checks (edge counts, degree distributions)

**Baseline**:

- [ ] Run existing supervised GT on 10K subgraph — establishes performance floor
- [ ] Measure: SPECTER2 cosine similarity on the cross-disciplinary ground truth pairs
      (build the ~100-pair dataset during this phase, manually)

**Done when**: GT runs on 10K, SPECTER2 embeddings stored, ground truth pairs collected.

---

### Phase 1: 100K Scale + Supervised Baselines (3-4 weekends)

_Goal: validate pipeline at working scale, establish all baseline metrics._

- [ ] Scale pipeline to 100K papers
- [ ] Mini-batch DataLoader — GraphSAGE neighbor sampler, 2-hop, fanout [10, 5]
- [ ] Supervised multi-label classifier (Task 1) — fine-tune GT end-to-end
- [ ] Supervised link predictor (Task 3) — dot product decoder on GT embeddings
- [ ] Separate evaluation for single-field / two-field / multi-field papers
- [ ] UMAP visualization of embeddings — check if boundary papers land at boundaries

**Baseline numbers to record** (these become the reference for all later experiments):

- Task 1 macro F1 (all papers / single-field / boundary)
- Task 3 AUC-ROC (all edges / cross-field edges only)
- SPECTER2-only cosine rank on cross-disciplinary ground truth pairs
- GNN embedding rank on same pairs (delta from SPECTER2 = the "graph adds" signal)

**Done when**: baseline numbers exist for both tasks, boundary paper analysis complete.

---

### Phase 2: Pre-training Comparison at 500K (4-5 weekends)

_Goal: understand which pre-training objective produces the best representations
for the three exploratory goals. All experiments at 500K._

Implement in order — each one teaches something before the next:

- [ ] **GraphMAE** — start here. Mask 50% of SPECTER2 features, reconstruct.
      Expected: best for Task 1 (rich features). Measure cross-disciplinary pair ranks.
- [ ] **SimGRACE** — no augmentations. Compare vs GraphMAE on boundary papers.
- [ ] **DGI** — mutual information baseline. Classic method, good reference point.
- [ ] **GraphCL** — edge dropping + feature masking. Check: does dropping citation
      edges hurt cross-disciplinary similarity? (Tests Goal 1 hypothesis directly.)
- [ ] **EdgePre** — edge prediction pre-training. Expected: best for Task 3.

**For each method, record**:

- Zero-shot Task 1 macro F1
- Zero-shot Task 3 AUC-ROC
- Cross-disciplinary ground truth pair rank (Goal 1 signal)
- Boundary paper classification F1 (Goal 2 signal)
- Training time on M2

**Done when**: comparison table complete, best method identified for Goal 1 and Goal 2.

---

### Phase 3: Prompting Comparison at 500K (3-4 weekends)

_Goal: understand prompting failure modes at 500K scale (Goal 3)._

Use best pre-training backbone from Phase 2. Implement prompting methods in order:

- [ ] **GPF-plus** — baseline prompt. Verify it works at all on 100K.
      Run scale stress test: 1K → 5K → 10K → 50K → 100K. Plot accuracy vs scale.
- [ ] **Gprompt** — compare vs GPF-plus. Run same scale stress test.
- [ ] **GPPT** — reformulates as link prediction. Best for Tasks 1, 2.
- [ ] **All-in-one** — multi-task unified. Test task interference: joint vs separate.

**Edge type sensitivity test** (Goal 3):

- Train each prompt on `cites`-only graph
- Evaluate on `similar_to`-only graph
- Measure transfer degradation

**Task interference test** (Goal 3):

- Joint prompt (Task 1 + Task 3 simultaneously) vs two separate prompts
- Measure: does multi-task prompting hurt either task?

**Done when**: prompting comparison table complete, failure modes documented.

---

### Phase 4: Scale to 1M (whenever ready)

_Goal: run the best pre-training + prompting combination at 1M papers.
Demonstrate that findings from Phase 2-3 hold at greater scale._

- [ ] Scale data pipeline to 1M papers (extend arXiv bulk + S2ORC coverage)
- [ ] Profile bottlenecks at 1M: embedding time, graph construction, training memory
- [ ] Flag what needs cloud offload (estimate cost before committing)
- [ ] Best pre-training (Phase 2) × best prompting (Phase 3) at 1M
- [ ] Re-run cross-disciplinary ground truth evaluation — does Goal 1 signal strengthen?
- [ ] Re-run boundary paper analysis — does Goal 2 picture change at scale?
- [ ] Scale stress test for best prompting method (Goal 3): 100K → 500K → 1M

### Phase 5 (Stretch): 2M Full Corpus

_Only if Phase 4 results are compelling and compute budget allows (~30 hrs/run)._

- [ ] Full 2M arXiv corpus pipeline
- [ ] Likely requires cloud offload for pre-training — budget and decide
- [ ] Focus: does the cross-disciplinary idea signal (Goal 1) meaningfully improve
      with 2× more data, or does it plateau at 1M?

---

## 10. Open Questions

| Question                                                                  | Impact                      | Decision Needed By |
| ------------------------------------------------------------------------- | --------------------------- | ------------------ |
| ~~S2ORC~~ → Use OpenAlex (CC0, no key, free S3)                           | ✅ Resolved                 | —                  |
| SPECTER2 MPS: float32 only, needs `adapters` lib; check precomputed first | ✅ Resolved                 | —                  |
| OpenAlex coverage: what % of arXiv papers have citation data?             | Data completeness           | Phase 0            |
| Which GNN backbone at scale: GraphSAGE vs GT?                             | Pre-training                | Phase 1            |
| How to handle multi-label imbalance in Task 1?                            | Eval validity               | Phase 1            |
| Can GraphCL augmentations be defined meaningfully on citation graphs?     | Phase 2                     | Phase 2            |
| Does All-in-one's subgraph prompt concept extend to heterogeneous graphs? | Phase 3                     | Phase 3            |
| Cloud compute budget for Phase 4?                                         | Feasibility of 2M scale     | Phase 3            |

---

## 11. What This Project Is NOT

- **Not** a paper recommendation system (though the graph would support it)
- **Not** training a language model or doing RAG over paper text
- **Not** trying to beat SOTA on benchmarks — comparisons are for learning, not publishing
- **Not** handling PDFs — title + abstract is sufficient for SPECTER2
- **Not** rushing to 2M — 100K teaches everything the methods teach

---

## 12. References

- **SPECTER2**: Cohan et al., 2020; Singh et al., 2022
- **DGI**: Veličković et al., 2019
- **GraphMAE**: Hou et al., 2022
- **GraphCL**: You et al., 2020
- **SimGRACE**: Xia et al., 2022
- **EdgePre variants**: Sun et al., 2023 (ProG framework)
- **GPF / GPF-plus**: Sun et al., 2023
- **GPPT**: Sun et al., 2022
- **Gprompt**: Liu et al., 2023
- **All-in-one**: Sun et al., 2023
- **ProG (unifying framework)**: Sun et al., 2023
- **S2ORC**: Lo et al., 2020
