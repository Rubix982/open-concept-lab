# LLM Edge-Typer — Plan Tree

_A rooted plan: **roots** (why / premises) → **trunk** (where it lives) → **branches**
(workstreams) → **leaves** (concrete tickets). Read top-down; build bottom-up._

---

## 🌱 ROOTS — the premises everything grows from

**R0.1 · The problem (observed, not hypothetical).**
With the LLM extractor producing clean claim nodes, the graph's _edges_ are now the weak
layer. The general-domain NLI model (`typeform/distilbert-base-uncased-mnli`) forces every
candidate pair into entailment/contradiction/neutral, and on scientific text it
systematically mislabels **"two papers each proposing a different method"** as
`CONTRADICTS`. Concrete failure from the last build: _GraphRec (2019, recommendation)_
shown as **contradicted by** _The Graph Neural Network Model (2008, foundational)_. They
don't contradict — they're unrelated-in-claim / same-broad-topic.

**R0.2 · Why an LLM fixes it.** The two things NLI cannot do are exactly the two things
that break it here:
1. **Say "these aren't actually related" (NONE)** — NLI must emit a label for every pair;
   it cannot prune a bad candidate. An LLM can.
2. **Distinguish relation _types_ beyond 3 NLI classes** — "A extends B's method,"
   "A and B attack the same problem differently," "A uses B's dataset" are all collapsed
   by NLI. An LLM can name them.

**R0.3 · Principles (carried from R-003, learned the hard way).**
- **Honest, independent evaluation.** R-003's macro-F1 1.000 was inflated by shared
  labeler/rubric judgment. The edge eval MUST avoid this: label gold edges _before_
  writing the LLM's prompt, or with a separate rubric, so labeler and model don't collude.
- **Interface stability.** Keep `build.py` swappable: `--edge-typer {nli,llm}`, NLI stays
  as the offline/zero-cost fallback, just like `--tagger`.
- **Cost-aware.** Batch many pairs per request (structured output). Default
  `claude-opus-4-8` to set the ceiling; `claude-haiku-4-5` for bulk.
- **Name the failures.** Store rationale + confidence on every edge so wrong edges are
  auditable, not invisible.

**R0.4 · Definition of done.** `python -m src.graph.build --edge-typer llm` produces a
graph where (a) the GraphRec↔2008-GNN false `CONTRADICTS` is gone, (b) edges carry a
correct typed relation + direction + rationale, and (c) a held-out gold-edge eval shows
the LLM beats NLI on relation accuracy and especially on false-CONTRADICTS rate.

---

## 🪵 TRUNK — where edge-typing sits in the pipeline

```
ingest → classify → embed → [ CANDIDATE PAIRS ] → [ EDGE TYPING ] → store → query
                              (cosine top-k)        ^^^ THIS EFFORT      |        |
                                                                         |        └── surface rationale
                                                                         └── schema: rel_type/dir/score/rationale
```

The effort touches three existing files and adds one:
- **add** `src/graph/llm_edges.py` — the LLM edge-typer.
- **edit** `src/graph/build.py` — `--edge-typer` flag + factory (mirrors `_make_tagger`).
- **edit** `src/graph/store.py` — widen the `RELATES` schema (direction, rationale).
- **edit** `src/graph/edges.py` — only if we align its return shape with the richer one.

---

## 🌿 BRANCHES & 🍃 LEAVES

### 🌿 Branch A — Relation taxonomy & edge schema  _(root branch — everything depends on it)_
> The single most consequential decision. Defines the labels the LLM emits and the columns
> the graph stores. **Pending your call — see the question at the bottom.**

- 🍃 **A1** Decide the relation set + directional semantics (proposed in the next section).
- 🍃 **A2** Make `NONE` a first-class output so the typer can _prune_ false candidates
  (the core NLI fix). Pruned pairs become no edge.
- 🍃 **A3** Decide stored fields per edge: `rel_type`, `direction` (A→B / B→A / symmetric),
  `confidence` (0–1), `rationale` (short string), keep `similarity`.
- 🍃 **A4** Schema migration in `store.py` (`add_relation` + `RELATES` table); keep it
  backward-compatible so the NLI path still writes valid edges.

### 🌿 Branch B — Candidate generation review
> Edge typing is only as good as the pairs it sees. Revisit now that the typer can say NONE.

- 🍃 **B1** Dedup near-identical claims before typing (the repeated "we propose X" intros)
  — currently only skipped via `DUP_THRESHOLD`; consider merging instead.
- 🍃 **B2** Re-tune `TOP_K` / `SIM_THRESHOLD`: with a NONE option, we can widen recall
  (more candidates) because the LLM prunes false ones — but that costs more calls. Pick a
  recall/cost point and **log what's dropped** (no silent caps).
- 🍃 **B3** (stretch) cross-paper bias: ensure candidates aren't dominated by within-paper
  adjacency; the interesting edges are _across_ papers.

### 🌿 Branch C — LLM edge-typer implementation  _(depends on A)_
- 🍃 **C1** `LLMEdgeTyper` in `src/graph/llm_edges.py`: batched structured output
  (~10–15 pairs/request), JSON schema returning `{index, relation, direction, confidence,
  rationale}` per pair, with `relation` ∈ taxonomy ∪ {`NONE`}.
- 🍃 **C2** Prompt design: relation definitions + 2–3 few-shot examples (incl. the
  GraphRec↔2008-GNN case as a NONE/ADDRESSES_SAME_PROBLEM exemplar). Each claim pair gets
  its source paper titles for context.
- 🍃 **C3** Interface: a `type_pairs`-compatible entry so `build.py` swaps cleanly; richer
  fields flow through to `store.add_relation`.
- 🍃 **C4** Cost control: model choice (opus vs haiku), batch size, optional max-pairs cap
  with a logged drop count.

### 🌿 Branch D — Evaluation  _(the rigor branch — build early, depends on A)_
- 🍃 **D1** Build a **gold edge set**: sample ~40–60 candidate pairs from the real graph,
  hand-label the correct relation (incl. NONE). **Label before finalizing the C2 prompt**
  to dodge the R-003 shared-judgment trap; ideally have the labels reviewed independently.
- 🍃 **D2** `eval_edges.py` (mirrors `eval_ood.py`): per-relation P/R/F1 for NLI vs LLM,
  plus the headline metric — **false-CONTRADICTS rate** (the failure we're fixing).
- 🍃 **D3** Error analysis + spot-check; record honest caveats (set size, independence).

### 🌿 Branch E — Integration & rebuild  _(depends on C, D)_
- 🍃 **E1** Wire `--edge-typer llm` into `build.py`; rebuild `ckg.kuzu`.
- 🍃 **E2** Verify R0.4: the GraphRec↔2008-GNN false edge is gone; spot-check the new edges.
- 🍃 **E3** Query layer surfaces `rationale`; optional `--min-edge-confidence` filter.

### 🌿 Branch F — Future leaves (noted, not now)
- 🍃 single-pass extract+type (one LLM call classifies _and_ relates); temporal/citation
  edges; cross-corpus edges; edge dedup/merge.

---

## Proposed taxonomy (Branch A1 — for your confirmation)

Directional A→B unless marked symmetric. `NONE` always available.

| Relation | Meaning (A→B) | Fixes / why |
| --- | --- | --- |
| `SUPPORTS` | A's result/evidence backs B's claim | keep (NLI had this, often right) |
| `CONTRADICTS` | A's finding is logically incompatible with B's | keep, but now _rare and correct_ |
| `REFINES` | A improves / generalizes / extends B's method or result | new — the "builds on" relation |
| `ADDRESSES_SAME_PROBLEM` _(symmetric)_ | A and B tackle the same problem, different approaches | **new — directly fixes the false-CONTRADICTS case** |
| `USES` | A uses a method/dataset/result introduced by B | new — provenance between ideas |
| `RELATED` _(symmetric)_ | same topic, no stronger typed relation | generic fallback |
| `NONE` | not meaningfully related — **prune, no edge** | **the other core NLI fix** |

---

## Dependency order (build bottom-up)

```
A (taxonomy+schema) ──┬──► C (LLM typer) ──┐
                      │                     ├──► E (integrate + rebuild + verify)
                      └──► D (gold eval) ───┘
B (candidate review) ───────────────────────► (feeds C/E; can run parallel to C)
```

## Proposed tickets (instantiate after taxonomy is confirmed)

| ID | Branch | Title | Type |
| --- | --- | --- | --- |
| O-004 | — | Sequence the edge-typer effort | coordinate |
| R-004 | A | Relation taxonomy + edge schema design | research |
| R-005 | D | Gold edge set + NLI-vs-LLM eval harness | research |
| E-006 | C | LLMEdgeTyper (batched structured output) | implement |
| E-007 | B | Candidate-gen review + claim dedup | implement |
| E-008 | E | Integrate `--edge-typer llm`, rebuild, verify | implement |

_R-004 gates E-006 (confidence-gated). R-005 (eval) should land before E-008 so we measure
before committing the rebuild._
