---
slug: three-checks-that-could-not-have-failed
title: "Three checks that could not have failed"
authors: [saif]
tags: [lab-notes, knowledge-editing, edit-reach, method]
date: 2026-11-09
standfirst: >
  I wrote a program to check a document, and it found three things wrong with the
  document and three wrong with itself. All three of mine were passing. I also went
  looking for five of them and found three, which turned out to be the better story.
---

I had a document that made claims, so I wrote a program to check whether the claims were true.

<!-- truncate -->

The document is about what reproduces when you read a model's internals off somebody else's machines. I use NDIF, which serves large models to people who do not own the GPUs to run them, and readings off a shared service are not obviously repeatable. A number I cannot read twice is not a number, so I wrote down which quantities are stable and which are not. The program is a conformance suite: a set of checks, each one tied to a claim in that document, run against a live model.

That pairing is the whole method, and I did not plan it. The document says *a ratio read inside one trace is bit-identical across sessions*; the suite goes and reads one, twice, and compares. If the document is wrong the suite says so.

It said so.

## What the suite did to the document

The first run produced three corrections, and I left all three in the document at the place they belong rather than quietly fixing them.

**"Batch composition contributes zero."** I had written that sending the same prompt in a different batch changes nothing. True of the *derived ratio* I measured it on. False of the *raw keys* underneath, which move by **4.297e-02** — about 2.6% of their own magnitude. I had generalised one step past the thing I measured, and the step happened while writing prose, not while measuring.

**"Padding width is immaterial."** I had never measured this. It is 4.297e-02, same as the row-count arm. I was asserting a negative result nobody had run.

**"2.98e-03 per item."** This came back as 6.31e-05 on a different sample of six pairs. The per-item figure moves with the sample; the median, **5.319e-06** against my 5.06e-06, does not. The suite gates on the median now and the per-item number is reported as what it is.

Two more came off later runs. The claim that readings partition cleanly by which GPU served them did not reproduce one morning — four fresh connections all landed on one device, so there was nothing to partition — and I weakened it from a property of the instrument to something that happens on some days. And the claim that a certain disagreement *grows with depth* I withdrew outright, when a sweep on a bigger model found it falling 53-fold to layer 20 and then rising 298-fold to layer 40. The direction was one model's artefact and I had written it as a law.

## What the suite did to itself

The same first run found two faults in the suite, and a later run found a third.

**One.** A check on bfloat16 precision — the reduced-precision format these models are served in — measured the relative error of a dot product between two **near-orthogonal** vectors and read **4.9e-01**. Half. That is not a precision problem, it is catastrophic cancellation: subtract two nearly equal quantities and the answer is almost entirely rounding. The check was asking about the number format and measuring the geometry of its inputs. Rewritten as per-element rounding error it reads 3.887e-03, against bfloat16's own 2⁻⁸ = 3.906e-03, which is the number I was after the whole time.

**Two.** A check on whether the same arithmetic gives the same answer in two places — on the serving GPU inside a trace, or afterwards on my own CPU — was reading **anchor prompts**. An anchor is a prompt that opens with the edited subject, and there is a short derivation showing its coefficient is exactly 1.000 under either arithmetic. So the check read **0.000e+00**, correctly, and would have read 0.000e+00 forever, on every model, at every layer, reporting *the two sites agree* for as long as anyone ran it. Moved onto prompts that are not pinned, the median difference is 5.319e-06.

**Three.** A check asking whether sixteen readings grouped cleanly by the device that served them returned `clean_partition = True`. Sixteen readings, one GPU. *Every signature maps to one device* and *every device carries one signature* are both true, and both empty, when there is one of each. It wants two of each now, and otherwise says `n/a — nothing to partition`.

## They are the same fault

A check evaluated on an input that cannot express the thing it tests.

Not a wrong formula, not a wrong tolerance, not an off-by-one. In all three the arithmetic was right and the number printed was correct. The input just had no room in it for the answer to come out the other way. Near-orthogonal vectors cannot show you a format's precision. A quantity pinned to 1.000 by algebra cannot show you two sites disagreeing. One device cannot show you a partition.

Two things follow and the second is why I am writing this down.

**I fixed all three by naming the degenerate case, and none by moving a number.** A degenerate case is an input where the question stops being a question — the answer is forced by the shape of the input rather than by what you wanted to measure. Each fix adds a guard that says *this input cannot answer this, so report that it cannot*. If I had tightened a threshold instead, all three would still be wrong and would have looked tuned.

**All three were passing.** This is the part that makes them hard. A check that fails gets attention. A check that cannot fail looks exactly like a check that passes — a green line, every run, forever — and the number beside it is correct every single time. Nothing in the output tells you the difference between *this agrees* and *this could not have disagreed*.

The only reason I ever saw them is that the suite was pointed at a document making specific claims. A check reading 0.000e+00 where the document predicted something small and non-zero is not a failing test; it is two artifacts disagreeing. The document caught the suite. The suite caught the document. Neither would have caught itself.

## I went looking for five and found three

A note I wrote to myself a day earlier said this fault had come up five times. When I sat down to collect them, the record said three. It says so twice, in two different files, and a search across both projects turns up no fourth.

The five was written from memory. I do not think I was being careless so much as remembering a feeling of *this keeps happening* and putting a number on it, which is the same move as writing "contributes zero" after measuring one case.

The smaller claim is better anyway. Three checks, in one suite's short life, each of them passing, is a sharper thing to say than five loosely counted. The headline number was the weakest part of the note and it did not survive being checked.

## Honest limits

**Three instances in one suite is not a rate.** One program, written by one person over about ten days. Nothing here says how often this happens in general and the sample is as small as it looks.

**I did not find these by being clever.** They fell out of running a suite against a document, and I only had both because I did not trust the document. I have no procedure for finding this fault in work that has only one artifact.

**This is not a method I am offering.** "Write a suite and a document that check each other" is expensive, and it happened here by accident of history rather than design. Whether it is worth the cost on work that is not about reproducibility, I have not tested.

---

What stays with me is not the three faults. It is how ordinary they looked.

I have spent a lot of this project being pleased with green output. A passing check feels like evidence, and for a while it is the only evidence you have, so you lean on it. But a check only earns that trust if there exists some input on which it would have gone the other way — and nothing in a passing run tells you whether such an input was ever possible.

I think most of the things I believe about my own work are like this. Not wrong, exactly. Just never put somewhere they could have been wrong. The three checks are only the version of it I can point at, because they happened to be written down twice.

... And in the spirit of the thing: I have not checked whether that last paragraph could have come out the other way either.
