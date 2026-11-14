---
slug: when-is-the-old-answer-good-enough
title: "When is the old answer still good enough?"
authors: [saif]
tags: [lab-notes, graphics, method]
date: 2026-11-14
standfirst: >
  I wanted a knowledge base of competitive-programming tricks for making slow libraries faster. It exists already, and it aims at the wrong gap. What I am building instead is a reference of the ways graphics software avoids redoing work, written from papers, with the conditions under which the reused answer is still right. Four entries so far, one of them measured. The most useful result came from reading one paper all the way through, and it changed the question more than it answered it.
---

I have been running cloth simulations in Blender for a private project, and they are slow. One drape of a garment piece of about 5,000 vertices takes four to seven minutes, and a full run took 14 to 22, nearly all of it in the cloth solver. Watching those runs, I began to realise how much processing time geometry problems take, and to wonder whether there were algorithmic answers somewhere: ways to reframe a problem that would let us write faster programs, or suggest improvements to the libraries that do this work.

<!-- truncate -->

## The first idea, and what broke it

My first idea was a knowledge base built from competitive programming. Contest solutions often get to the answer through a shortcut that looks impossible until you have spent days on the same problem, and a better algorithm beats better hardware once the inputs grow. The plan was to distil those solutions with AI, point an agent at an existing library, find a slow part, apply a trick, and check that the output stayed the same while the code got faster.

Three things broke it, roughly in the order I found them.

The distillation has been done. PIE collected over 77,000 pairs of slow and fast C++ submissions from CodeNet, kept where the same programmer later submitted a faster solution, and models trained on them beat the best human speedup on held-out contest problems [1]. It did not carry over to real code. On benchmarks built from real repositories, the best agents solve under 5 % of GSO's tasks [2], and reach under 0.23× of the expert's speedup on SWE-fficiency [3].

The catalogue is not what is missing. Models already have the contest corpus in their weights, and GSO's analysis of the failures says agents mostly get wrong where the time is going, more than what to do about it.

And contest problems are chosen for having a trick. A setter picks a problem because a clever shortcut is hidden in it, then builds the tests so only that shortcut passes. After years of that it feels as if every problem hides one. Real problems were not designed by anyone. Most of the time the win is either boring, a list that should have been a set, or a reframe that only someone who knows the field would see.

My own simulations already showed this. Where I checked, they used the right algorithms: a bounding-volume tree for the check that cloth doesn't pass through cloth, and a fitting loop written to run as few drapes as it can. A catalogue of contest tricks would have found little there. The largest saving on record came from somewhere else. Carrying a garment that had already settled on one body over to another body took 1.2 seconds, against about six minutes to drape it again.

What I kept from the first idea is the contest habit: looking at a messy problem and asking which known problem it really is. That transfers. The archive of solutions mostly doesn't.

## Work done twice

The 1.2 seconds came from not redoing work, and slow software redoes work all the time. The general name for avoiding it is incremental computation, with memoization as its simplest form. Exact repeats are the easy case, and tools already find them: MemoizeIt found 9 places to memoize in 11 Java programs that profilers had missed, with speedups from 1.04× to 12.93× [4].

The expensive cases are work that is only nearly the same. Each round of a fitting loop drapes a slightly different cut, and each frame of an animation is a slightly different scene. Reusing nearly-the-same work changes the answer, so what is worth writing down moves from the technique to its condition: when is the old answer still good enough? The garment transfer already shows the shape of it. The kameez and trousers carried over well, and the dupatta's free end tore. The technique was generic. The condition was specific to cloth.

Geometry suits this. Between frames, iterations or rounds most points barely move, and neighbouring points behave alike, which is what reuse feeds on. Geometric answers are also cheap to check (whether things intersect, how far apart they are, how long an edge is), and that gives the "did the answer stay right" half that my first idea never had.

I made the reference about graphics in general rather than about cloth, on purpose. I have a feeling I will be working in graphics for a long time, and writing the entries doubles as a map of the field for me.

## Six things to reuse

A reference that covers all of graphics turns into a list nobody uses unless it is organised by something that cuts across the subfields. The same moves turn up in rendering, simulation and geometry, so I filed the entries by what gets reused.

<Figure
  src="/img/writing/six-ways-to-reuse.svg"
  alt="Six small drawings in two rows, one for each thing graphics software reuses: the previous frame, a neighbour's work, an earlier and slightly different run, a coarse solution, a result on another shape, and work paid once and used for every case. Each has two examples under it."
  caption="The six categories entries are filed under, by what gets reused."
  wide
  plain
/>

These six came from about ten examples. When I sorted twelve techniques onto them, all twelve fit, but all twelve came from the same conversation that produced the six, so the sort could hardly have failed. It shows only that the six fit their own examples. A test on papers picked by a fixed procedure is written and waiting. Strangely, "across runs" got none of the twelve, even though that is where my own slow simulations sit.

The sort turned out to be more useful for something I hadn't been looking for. A second question cuts across all six: does the reuse change only the cost, or the answer too?

<Figure
  src="/img/writing/cost-or-answer.svg"
  alt="Left: bounding boxes refitted around points that have drifted apart grow large and overlapping, but every point is still inside its box, so queries stay right and get slower. Right: a moving ball with fading copies trailing behind it, where reused pixels from older frames leave a ghost."
  caption="Refitting a tree changes only the cost. Reusing last frame's pixels changes the answer."
  wide
  plain
/>

Of the twelve, four changed only the cost, six changed the answer, and two depended on how they were done. Reuse that changes only the cost fails by getting slower, which is easy to notice. Reuse that changes the answer fails by being wrong, and that is where the conditions for when it is safe carry real content. So every entry now says which kind it is.

## What an entry holds, and the one that was measured

Each entry says what work is wasted, which technique avoids it and where it comes from, when the reuse stays valid, when it doesn't apply, how to check it, and whether it has been measured. Every condition is marked by how it is known: stated in a paper, measured, or reasoned out and not yet tested.

The method comes from [patternbook](https://github.com/Rubix982/patternbook), a library of design knowledge for coding agents that I built before this one: start from the problem, go to the primary sources, write down when the advice stops applying, and check what an agent already does before writing anything. The two differ in how an entry is tested. patternbook puts a page built from the entry in front of a judge in a blind pick. Here the reused answer is measured against a fresh full computation, and judged against how much two fresh computations differ from each other.

There are four entries so far. One has been measured, in part:

<Figure
  src="/img/writing/garment-transfer.svg"
  alt="A kameez, trousers and dupatta draped on a figure 1.609 m tall are carried in 1.2 seconds to a figure 1.753 m tall. The kameez and trousers come out graded to the new body, with edges 6 to 7 percent longer at the median and 22 to 30 percent longer at the 95th percentile. The dupatta's free end tears. Below, on one time axis, draping again takes about 6 minutes and carrying over takes 1.2 seconds."
  caption="The one measured entry: about six minutes to drape the garment again, 1.2 seconds to carry it over. The body-hugging pieces survived the trip and the free-hanging one did not."
  wide
  plain
/>

The technique binds each point of the draped garment to the nearby surface of the body, then moves the binding onto the new body, and the garment follows in one step. In Blender this is the Surface Deform modifier. What comes out is not the same garment on a taller person. It is stretched with the body, which makes it a graded version, sized to fit. For the kameez and trousers that was accepted as grading. The dupatta, a long scarf whose free end hangs away from the body, had been bound to parts of the body it was nowhere near, and it tore.

Two things the entry calls for haven't been run: the short relax under the cloth solver that is meant to follow the transfer, and a comparison against several fresh drapes on the new body.

## Does an entry tell an agent anything?

In the end the library is meant to be context for an AI agent working on this kind of problem, so before trusting the entries I checked what an agent says without them. Three fresh agents were each given the wasted work from one of the first three entries, with no hint of the technique.

Between them they named 11 of the entries' 18 conditions, partly named 3, disputed 1 and missed 3, and they named every check. That looks as if the entries add little. It is weak evidence either way, because the entries had been written from abstracts by the same model, so it was always going to know most of what they said.

What only an entry carried was the measurement.

<Figure
  src="/img/writing/a-guess-and-a-measurement.svg"
  alt="One axis from 0 to 35 percent. The measured median stretch, 6 to 7 percent, is a narrow band. The measured 95th percentile, 22 to 30 percent, is a wide band far to the right. An agent's guess of 9 percent sits near the median band."
  caption="The agent's single number lands near the typical edge and says nothing about the most stretched ones."
  wide
  plain
/>

The agent reasoned that a figure 9 % taller would stretch the garment about 9 % along its length. For the typical edge that is close. But the stretch isn't even, and one edge in twenty came out stretched by 22–30 % or more. Those are the edges that tear or look wrong, and a single number has nothing to say about them.

## Reading one paper all the way through

That pointed at what an entry should carry beyond what a model already knows: measurements, and what you only get from reading a paper in full rather than its abstract. So I read one in full, Brouet, Sheffer, Boissieux and Cani's *Design Preserving Garment Transfer* from SIGGRAPH 2012 [5]. I wrote down sixteen points from it before reading two of the three agent answers I would score against it.

Eleven of the sixteen were named by none of the three. Six of those eleven are general rather than particular to this paper, and all six are about the same thing, grading: making a version of the garment that fits the new body, the way a pattern-maker makes one dress in several sizes. No agent proposed it, or asked whether it was wanted. Every one of them assumed the goal was the same garment, draped again on the new body.

<Figure
  src="/img/writing/redrape-or-grade.svg"
  alt="Three figures with a dashed line at knee height. The first body wears a flared dress with its hem at the knee. A taller body wears the same pattern draped again: the hem rides well above the knee and the cloth pulls. The taller body wears the dress graded to it: the hem is back at the knee and the flare keeps its slope."
  caption="Draping the same pattern again keeps the cloth and loses the design. Grading keeps the design and changes the cloth. None of the agents asked which one was wanted."
  wide
  plain
/>

The paper describes the first as producing "a result that looks like a person wearing someone else's wrong size garment". Grading keeps the design: a knee-length hem stays at the knee, a flare keeps its slope, a garment that was tight at the waist stays tight there. The paper grades a garment as a geometric optimisation with no simulation, taking between 11 seconds and a little over three minutes per garment on a 2012 laptop, and the patterns it cuts back out of the result are stretched by at most 0.3 %. For comparison, it took an experienced artist three hours to make the outfit in the paper's first figure.

And grading turned out to be what my test bed wanted. Its own review had already accepted the transferred kameez and trousers as graded. Inside the agents' frame, matching a fresh drape of the same pattern, the paper added nothing they had missed outright, and they covered ground it doesn't, since it ignores physics. What the full reading added was a different question, and I would not have got it from the abstract.

It also settled a disagreement between the measured entry and one of the agents. The entry said the relax after a transfer would be short, and the agent said it would have to undo all the stretch. They were assuming different rest shapes for the cloth. Relaxed toward the original pattern, the cloth has to undo 6–7 % of stretch at the median. Relaxed toward a pattern cut from the graded result, it starts almost at rest. Which one is right depends on whether you wanted the same garment or a graded one, which is the paper's question again.

## What it can't show yet

Every check so far was scored by a model of the same family the agents run on, against lists it wrote. Most of those lists were fixed before the answers were read, but not all of them. One paper has been read in full, and one entry measured, in one test bed. The six categories have only been tested on their own examples. And no entry has yet been given to an agent doing real work, which is what the library is for. Until that happens it is a map for whoever reads it, starting with me.

The library is on GitHub at [Rubix982/graphics-reuse](https://github.com/Rubix982/graphics-reuse), and [its page here](/graphics/reuse) keeps the current counts.

<References
  items={[
    {
      authors: "Shypula et al.",
      year: 2024,
      title: "Learning Performance-Improving Code Edits",
      venue: "ICLR 2024",
      url: "https://arxiv.org/abs/2302.07867",
    },
    {
      authors: "Shetty et al.",
      year: 2025,
      title: "GSO: Challenging Software Optimization Tasks for Evaluating SWE-Agents",
      venue: "NeurIPS 2025",
      url: "https://arxiv.org/abs/2505.23671",
    },
    {
      authors: "Ma et al.",
      year: 2026,
      title: "SWE-fficiency: Can Language Models Optimize Real-World Repositories on Real Workloads?",
      venue: "ICML 2026",
      url: "https://proceedings.mlr.press/v306/ma26l.html",
    },
    {
      authors: "Della Toffola, L., Pradel, M., Gross, T. R.",
      year: 2015,
      title: "Performance Problems You Can Fix: A Dynamic Analysis of Memoization Opportunities",
      venue: "OOPSLA 2015",
      url: "https://github.com/lucadt/memoizeit",
    },
    {
      authors: "Brouet, R., Sheffer, A., Boissieux, L., Cani, M.-P.",
      year: 2012,
      title: "Design Preserving Garment Transfer",
      venue: "ACM Transactions on Graphics 31(4), SIGGRAPH 2012",
      url: "https://doi.org/10.1145/2185520.2185532",
    },
  ]}
/>
