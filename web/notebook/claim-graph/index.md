---
title: claim-graph
sidebar_label: claim-graph
sidebar_position: 1
description: A knowledge graph whose nodes are claims rather than papers.
---

# claim-graph

A citation graph tells you which paper pointed at which paper. It cannot tell
you which *claim* supported, extended, or contradicted which other claim — and
that is the relation a researcher actually wants when looking for a gap.

This is a working vertical slice: real papers in, typed edges between extracted
claims, an explorer over the result.

```
ingest (OpenAlex / S2) → classify and type edges → graph (Kùzu) → explore
```

<Claim
  label="Where the slice stands"
  record={{
    Working: "End-to-end, on real papers with provenance kept",
    Open: "Extraction quality out of distribution",
    Status: <Status kind="standing">Slice working</Status>,
  }}
>
  The pipeline runs and the graph is queryable. The unresolved part is whether
  claim extraction holds up on papers outside the domain it was tuned on.
</Claim>

<Embed
  src="/demos/claim-graph/"
  title="Claim knowledge graph explorer"
  caption="The explorer over the built graph. Nodes are claims, edges are typed by relation, and every node keeps the sentence it came from."
  ratio={16 / 10}
/>

## The honest gap

Extraction was developed against a computer-science corpus. Applied outside it,
accuracy has not been measured, so nothing about coverage should be believed
yet. That is a measurement task, not a modelling one, and it is the next thing.

<Aside>
  Provenance is kept per sentence, which means a wrong edge can be traced back to
  the sentence that produced it. That property is worth more than a higher score
  from a pipeline you cannot audit.
</Aside>

## What it is a slice of

The longer aim is a claim-level layer over the literature: papers as inputs,
ideas as nodes, and lineage that survives one of the papers being retracted.
This slice exists to find out which parts of that are hard, cheaply.
