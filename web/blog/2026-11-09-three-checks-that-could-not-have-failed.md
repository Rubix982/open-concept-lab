---
title: "Three checks that could not have failed"
slug: three-checks-that-could-not-have-failed
authors: [saif]
tags: [lab-notes, knowledge-editing]
date: 2026-11-09
status: provisional
project: edit-reach
standfirst: >
  I wrote a suite to check a document, and it found three things wrong with the
  document and three things wrong with itself. The three in the suite are one
  fault, and every one of them was passing.
---

I had a document that claimed things, so I wrote a program to check whether the things were true.

The document is a reference on what reproduces when you read a model's internals off somebody else's machines — in this case NDIF, which serves large models to people who do not have the GPUs to run them. Readings off a shared service are not obviously repeatable, and a result you cannot read twice is not a result, so the document exists to say which numbers are stable and which are not. The program is a **conformance suite**: a set of checks, each one tied to a claim in the document, run against a live model.

<!-- truncate -->

That pairing is the whole method. The document says *a ratio read inside one trace is bit-identical across sessions*; the suite goes and reads one, twice, and compares. If the document is wrong the suite says so.

It said so.

## What the suite did to the document

The first run, on 3 November, produced three corrections.

**"Batch composition contributes zero."** The document said that sending the same prompt in a different batch changes nothing. The suite found this is true of the **derived ratio** the original measurement was taken on, and false of the **raw keys** underneath it, which move by 4.297e-02 — roughly 2.6% of their own magnitude. The claim had been generalised one step past the thing that was measured, and the step happened when the result was written into prose rather than when it was measured.

**"Padding width is immaterial."** This had never been measured. It is 4.297e-02, the same as the row-count arm. The document was asserting a negative result that nobody had run.

**"2.98e-03 per item."** This reproduced as 6.31e-05 on a different sample of six pairs. The per-item figure is sample-dependent; the median, 5.319e-06 against the document's 5.06e-06, is not. The suite now gates on the median, and the per-item number is reported as what it is.

Later runs took two more things out of the document. The claim that readings partition cleanly by which GPU served them did not reproduce on 3 November — four fresh connections all landed on one device, so there was nothing to partition — and the claim was weakened from a property of the instrument to something that happens on some days. And the claim that a certain disagreement *grows with depth* was withdrawn outright when a sweep on a larger model found it falling 53-fold to layer 20 and then rising 298-fold to layer 40. The direction had been one model's artefact.

Each correction is left in the document at the place it belongs, rather than quietly fixed. A reference that was once wrong should say where, or a reader has no way to calibrate the rest of it.

## What the suite did to itself

The same first run found two faults in the suite, and a later run found a third.

**One.** A check on bfloat16 precision — bfloat16 being the reduced-precision number format these models are served in — measured the relative error of a dot product between two **near-orthogonal** vectors and read **4.9e-01**. Half. That is not a precision problem; it is catastrophic cancellation, which is what happens when you subtract two nearly equal quantities and the answer is made almost entirely of the rounding. The check was asking about the format and measuring the geometry of the inputs. Replaced with per-element rounding error, it reads 3.887e-03 against bfloat16's own 2⁻⁸ = 3.906e-03, which is the number it was looking for all along.

**Two.** A check on whether the same arithmetic gives the same answer in two different places — on the serving GPU inside a trace, or afterwards on a local CPU — was read on the **anchor prompts**. An anchor is a prompt that opens with the edited subject, and there is a short derivation showing its coefficient is exactly 1.000 under either arithmetic. So the check read **0.000e+00**, correctly, and would have read 0.000e+00 forever, on every model, at every layer, reporting *the two sites agree* for as long as anyone ran it. Moved to prompts that are not pinned, the median difference is 5.319e-06.

**Three.** A check called `check_session_partition` asked whether sixteen readings grouped cleanly by the device that served them. It returned `clean_partition = True`. Sixteen readings, one GPU: *every signature maps to one device* and *every device carries one signature* are both true, and both vacuous, when there is one of each. It now requires at least two of each and otherwise reports `n/a — nothing to partition`.

## They are one fault

A check evaluated on an input that cannot express the thing it tests.

Not a wrong formula, not a wrong tolerance, not an off-by-one. In each case the arithmetic was right and the number it printed was correct. The input simply had no room in it for the answer to come out the other way: near-orthogonal vectors cannot show you a format's precision, an analytically pinned quantity cannot show you two sites disagreeing, and one device cannot show you a partition.

Two things follow, and the second is why I am writing this down.

**All three were fixed by naming the degenerate case, never by moving a number.** A *degenerate case* is an input on which the question stops being a question — where the answer is forced by the shape of the input rather than by the thing you wanted to measure. Each fix adds a guard that says *this input cannot answer this, so report that it cannot* rather than tightening a threshold. If I had tightened a threshold instead, all three would still be wrong and would have looked tuned.

**All three were passing.** This is the part that makes the fault class hard. A check that fails gets attention. A check that cannot fail looks exactly like a check that passes — a green line in a report, every run, forever — and the number beside it is correct every single time. Nothing in the output distinguishes *this agrees* from *this could not have disagreed*.

The only reason these surfaced is that the suite was run against a document that made specific claims, and a check reading 0.000e+00 where the document predicted something small and non-zero is a disagreement between two artifacts rather than a failing test. The document caught the suite. The suite caught the document. Neither would have caught itself.

## What would make this wrong

If the three turned out to be one fault described three ways — if, say, all three were really the same guard missing in one shared helper — the piece would shrink to a story about one missing guard. They are not: three different checks, two different files, found on two different runs eleven days apart.

If any of them had actually been fixed by changing a number, the claim that this fault class is never a tolerance problem would be false. None was; the three fixes add a guard, a change of input set, and a minimum-count condition.

And if a fourth instance turns up, the claim *three in one suite's short life* becomes an undercount, which would make the fault class more common than I am saying rather than less.

## Limits

**Three instances in one suite is not a rate.** This is one program, written by one person over about ten days. Nothing here says how often this happens in general, and the sample is as small as it looks.

**I went looking for five and found three.** The ticket that asked for this piece said the fault had been found five times. That number was written from memory, and when I went to collect the instances the record said three, twice, in two different files. The headline number was the weakest thing in the ticket and it did not survive being checked — which is the ordinary outcome, and the reason for checking before writing rather than after.

**This is not a method I am offering.** "Write a suite and a document that check each other" is an expensive arrangement, and it happened here because the document existed first and I did not trust it, not because I planned a cross-check. Whether it is worth the cost on work that is not about reproducibility, I have not tested.
