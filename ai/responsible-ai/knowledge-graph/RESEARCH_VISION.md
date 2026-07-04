# Research Vision: A Knowledge Graph That Revises

_Saif Ul Islam · open-concept-lab · 2026-07-04_

---

## The Thesis

> Current knowledge systems accumulate claims.
> This one revises them.
> The difference is what makes it useful to researchers.

Citation graphs, semantic search, and RAG systems tell you what the field knows.
They accumulate. They do not distinguish a belief that was formed, contested, and
superseded from one that has stood for decades unchallenged. They have no semantics
for revision — only for retrieval.

This system is different. By applying AGM belief revision semantics to a claim-level
knowledge graph — with provenance, consolidation, and non-destructive supersession —
it produces something qualitatively different: a graph that knows not just *what* the
field believes, but *how it came to believe it*, *where it disagrees*, and *where it
has not yet looked*.

---

## The Research Contribution

### What AGM belief revision adds to a claim graph

The AGM framework (Alchourrón, Gärdenfors, Makinson, 1985) defines three operations
a rational agent must support when revising its beliefs:

| Operation | Meaning | In the knowledge graph |
|---|---|---|
| **Expansion** | Add a belief without checking consistency | A new claim node is extracted from a paper and added |
| **Revision** | Add a belief while maintaining consistency | A new claim supersedes a prior claim on the same (subject, property); old claim marked, not deleted |
| **Contraction** | Remove a belief | A claim is retracted; dependent claims are flagged for review |
| **Consolidation** | Restore consistency after a conflict | Two contested claims are merged into a synthesized position |

Current state of this project: **expansion only**. Claims are extracted and added.
No claim is ever marked as superseded. No conflict is detected. No consolidation
is performed.

The contribution: implement revision and consolidation with provenance chains, such
that the graph supports four operations no current system supports:

---

## The Four Gap Analysis Operations

### 1. Missing Beliefs
Claims that are *implied* by existing claims but never explicitly staked.
If claim A says "X causes Y" and claim B says "Y causes Z", but no claim says
"X causes Z" — that chain is detectable from transitivity. The unclosed chain
is a missing belief: either unnoticed, or genuinely hard. Either way, worth knowing.

### 2. Empty Middle Ground
Two claims are in "debates" relation — same (subject, property), contradictory states.
The AGM *merging* operation asks: what belief satisfies the strongest constraints from
both without contradicting either? If no paper has published that merged position,
the middle ground is empty. That is a synthesis opportunity — the work that would
resolve the debate.

*Historical analogue: wave vs. particle. The debate was visible for decades. Quantum
mechanics named the middle ground. The contestation was detectable; the synthesis
was the contribution.*

### 3. Fragile Beliefs
High-centrality claims under active contestation. Run the AGM *contraction* operation:
if this claim were removed, how many dependent claims would be destabilized? The
score is: connectivity × contestation × recency of counter-evidence. High-scoring
claims are likely revision sites — the field is building on something that is being
quietly undermined.

### 4. Innovation Frontier
Claims at the boundary of the graph that cite many but are cited by few — new,
unvalidated, pointing outward. What concept spaces are adjacent to those frontier
claims but not yet connected? If all frontier claims are in one area and an adjacent
method exists but has never been combined with them, that adjacency gap is a
detectable white space: tractable, because the methods exist; unworked, because
nobody has made the connection.

---

## Connection to the Lookback Mechanism

The theoretical foundation for this work comes from the lookback paper
("Language Models Use Lookbacks to Track Beliefs", ICLR 2026), which demonstrates
that LMs maintain internal (Character, Object, State) bindings and retrieve them
via attention. This is the read half of a belief system.

AGM compliance requires the write half: a persistent, writable belief store with
temporal indexing, consistency checking on write, and non-destructive supersession.
The knowledge graph IS that external belief store. The OIDs in the lookback mechanism
are the keys. The claim nodes are the values. The revision operations are the write
path that the transformer's frozen weights cannot provide.

This project is the engineering complement to the theoretical analysis. Together they
constitute a system where:
- The LM reads beliefs (lookback mechanism)
- The graph stores and revises them (AGM-compliant claim graph)
- The connection between the two is provenance: every belief is traceable to a
  source sentence in a source paper, with a timestamp and a supersession chain

---

## The Evaluation Strategy

**Domain:** GNN literature (already in the graph — 111 papers, 736 typed edges).

**Question:** Pick one contested claim in the GNN literature. Spectral vs. spatial
methods is a known debate. The claim: "spectral convolution generalizes across graphs."
Contested by multiple papers. A merged position exists in the literature but is rarely
cited directly.

**What to show:**
1. The system identifies the debate from the "debates" edges
2. It surfaces the contested claims with their provenance chains
3. It computes the middle ground via the merging operation
4. It identifies which papers are in the middle ground (and are under-cited)
5. It detects what the next synthesis would need to claim

**Compare to:** what a researcher would find in 4 hours of manual literature review.
The system should surface the same picture in under 60 seconds, plus the frontier
gaps the manual review would miss.

---

## Scope Discipline

The full vision is a decade of work. The contribution is one piece, done rigorously:

> *A claim-level knowledge graph with AGM revision semantics, evaluated on one domain,
> demonstrating that it surfaces contested middle ground and innovation gaps that
> current retrieval systems cannot.*

No more, no less. That is publishable. The rest follows if the foundation holds.

---

## The North Star

Every engineering decision should be answerable with this sentence:

> **"I used this to find something I wouldn't have found otherwise."**

If a feature cannot be connected to that sentence, it is not part of this contribution.

---

## Connection to Existing Engineering

| Component | Current State | What AGM compliance adds |
|---|---|---|
| Claim extraction | Working (DistilBERT + LLM) | Needs temporal provenance: (paper_id, date) per claim |
| Typed edges | In progress (E-006, hybrid typer) | Needs "supersedes" as a first-class edge type |
| Graph store (Kùzu) | Working | Needs supersession chain schema: active flag + superseded_by |
| Debates feature | Working | Needs consolidation query: given a debate, compute the merger |
| Time-lapse | Working | Already the temporal dimension — needs to drive revision detection |

The engineering is 70% there. The gap is semantic: supersession, consolidation, and
the four gap analysis queries. Those are 4 new Cypher queries and one schema extension.
