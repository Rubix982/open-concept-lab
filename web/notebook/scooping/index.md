---
title: Checking whether a mechanistic interpretability idea has been scooped
sidebar_position: 6
description: Deciding whether a research direction has already been done, by writing it as a four-part claim and checking each paper's methods section against all four parts.
---

# Checking whether a mechanistic interpretability idea has been scooped

My advisors asked for a defensible way to decide whether a direction had been scooped
before the work went further. The failure I had actually seen was not a missed paper.
Three times in [edit-slice](/notebook/edit-slice/) I found the right paper and then
misread it. One note said KnowledgeSmith <Cite id="luo2026knowledgesmith" /> had
"already tested" my variable. It had not, and the note had closed a question that was
never answered. Better search would not have caught any of the three, so the method had
to make misreading harder.

## The method

A scoop is decided against a specific claim. "Nobody does interpretability of agents" is a
statement about a field. "Nobody locates a planted step from the acting agent's own
activations" is something a paper can be checked against.

- **Write the claim as four slots before searching:** the object, the ground truth, the
  method or access, and the measurement. Each slot also says what would not match.
- **A paper takes the claim only if its methods section matches all four, in the same
  experiment.** That means one quoted sentence per slot. An abstract and a keyword grep
  can only ever produce "overlaps".
- **Shelving needs more evidence than proceeding.** A match nobody has verified is a
  reason to read the paper, never a reason to drop the direction.
- **When a verdict turns on how a slot is read, the call is mine.** It comes to me as one
  plain question, with what each answer would mean, and my answer is recorded next to the
  slot.
- **A confirmed match closes that version of the claim, not the direction.** The claim is
  restated around what the matching paper cannot do, and that paper becomes a baseline.

## What the first check found

The direction was interpretability of agent decisions, checked against a cause we plant
ourselves. It took three versions of the claim.

<Claim
  label="Where the claim ended up"
  superseded="No paper finds which step caused an agent's decision from internal state, on runs with a planted cause."
  record={{
    "What took it": "ReCast (arXiv 2610.11334) finds the planted step from hidden states. It matched once I answered yes to one boundary question: would a separate model's activations, reading the agent's transcript, tell you anything about how the agent decided?",
    "What replaced it": "A comparison: the acting agent's own activations against a reader model and against the text alone, on runs with a planted step.",
    "Where it stands": "0 of 66 candidates meet all four slots. The nearest each miss one, and they become the baselines.",
  }}
>
  Does the acting agent's own computation show which earlier step caused a decision, and
  does it show this better than a separate model reading the same run, or the text of the
  run alone?
</Claim>

The nearest work falls into three groups. Reader models find the planted step, but from a
separate model's activations: ReCast, and an anonymous ACL submission, LTS, which encodes
other agents' runs with one frozen Qwen model. Text alone finds injected steps too:
DriftNet recovers the injection point in 98.7% of attacked runs on a synthetic corpus.
And several studies read the agent's own activations, but to forecast or detect an
outcome, not to say which step caused it. The statement written for my advisors is
[positioning.md](https://github.com/Rubix982/scooping/blob/main/positioning.md).

## The tool

The checks run through a local command-line tool, `scope`, and a Claude Code skill,
`scoop-check`, that drives it. `scope` searches arXiv, OpenReview, Semantic Scholar
citations, OpenAlex, the ACL Anthology and pasted Google Scholar pages. It stores every
result in one DuckDB file, logs each query with its counts, and prints only the results
that are new to the check and pass a screen written from the slots. For a methods read it
prints the matching sentences with their section headings, and records which version of
the paper it read. The skill does no searching of its own, so every query ends up in the
log.

A check is quick by default, around twenty queries, and a quick check can only end with
"open on a quick check". The full passes, covering the nearest papers' authors, venues off
arXiv, forward citations and Google Scholar, run when someone else will read the result.

## Did it work?

I tested it on two of my own misreads, each time with a fresh session that could not see
my notes.

**KnowledgeSmith.** It judged the paper an overlap: the paper varies a fact's level in a
hierarchy, not how many facts depend on it. It also noticed something my own correction
had missed. A root has more descendants than a leaf, so the two variables are correlated,
and it handed that to me as a question. It also found a closer paper my notes did not
have, arXiv 2609.08067. That one differs on two calls that were mine to make; I answered
both, and it stays an overlap and becomes a baseline.

**RippleBench** <Cite id="rinberg2025ripplebench" />. My correction said the paper
"advertises no such pluggability" for its distance function. The session quoted it doing
exactly that. Every version names graph path length as an option, and none of them runs
it. The session was right, and my answer key, which I had built from my correction, was
wrong. It did miss MQuAKE, which was in its own knowledge base and never judged, so
closing a check now includes a screen over everything found but not yet judged.

Two cases is not many. Both were the failure the method was built for, and in the second
one it read the paper better than I had.

## Limits

- One reader made every verdict, and a second read by the same reader is not independent.
- Keyword search misses vocabulary. The nearest paper in the first backtest turned up only
  among the papers citing an older one.
- Some sources cannot be automated. DBLP and OpenReview's PDFs sit behind bot checks, and
  Google Scholar pages have to be pasted in by hand.
- A quick check ends with "open on a quick check" and a list of what it skipped, never
  with "nobody has done this".

The method, the tool, the skill and both checks are at
[github.com/Rubix982/scooping](https://github.com/Rubix982/scooping).
