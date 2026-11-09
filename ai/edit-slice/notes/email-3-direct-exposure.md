Hi Natalie, Arnab!

Last one in this batch, and the only part I think bears on the field rather than on my own model.

The two earlier emails ended on the same observation: an edit kept reaching questions it had no business reaching, and the one thing those questions had in common was that the edited person's name was sitting in the prompt. If that is what is happening, then a benchmark item can score as propagation while only ever measuring direct exposure to the edit. That is checkable, so I went and checked.

## What arrives where, and how we can know before running the edit

ROME's update is rank-one, so how much of it arrives at a given token depends on that token's key vector and the edited key, k*. There are two cases, and they are not the same kind of claim.

If a probe *begins* with the edited subject, causal attention means nothing else has been read yet, so the key at the subject's last token should be k* itself, and the coefficient is 1 by arithmetic. I want to be clear about how little measuring that proves: u appears in both the numerator and the denominator, so a wrong whitening, a wrong u, or a wrong layer index would still give 1. What it does test is the half that is not algebra -- whether the two keys really are the same vector. k* is read in its own forward pass while probes run in padded batches alongside prompts of other lengths, so a bad attention mask, a shifted position, or a tokenisation mismatch would each surface as a number that is not 1. Across 216 such cases, four models from 6B to 405B, and every layer, the deviation was 0.00e+00 rather than merely small.

If the subject appears but something comes *before* it, that derivation does not apply, because the key now depends on the preamble too. I assumed it would still be 1. It is not, and it falls with depth -- roughly 0.93 at layer 5, 0.79 at layer 12, about 0.52 by layer 24. The strong claim is an early-layer fact. It holds at the layer ROME and EasyEdit actually edit at, which is why it bears on benchmarks, but it is not a general property of the model.

    how much of the edit arrives at the probe's subject token    coefficient
    the probe begins with the edited subject                        1.000     (exact, every layer, 6B to 405B)
    a different subject entirely -- comparison baseline             0.082
    the subject appears, but with text in front of it               0.93      (layer 5; about 0.52 by layer 24)
    RippleEdits' "reach a second entity" prompts                    0.982     (median, layer 5)
    comparison baseline, on those same prompts                      0.065

The first two rows do not overlap in my 23,505 readings. The comparison baseline is doing real work here: without it, 1.000 would be close to uninformative, because a pipeline hardwired to return 1 looks exactly the same.

## The RippleEdits row is the one that worries me

That test is meant to check whether an edit reaches a *second* entity through a relation. One of its prompts asks:

    "the name of the head of government of the place of death of Leo Arons is"

Leo Arons is the edited subject, and he is standing inside the question.

![Top row: the item is meant to test whether an edit on Leo Arons travels two hops, through his place of death to that place's head of government. Bottom row: the prompt itself contains the string Leo Arons, so the edit may reach the queried token directly, with a median coefficient of 0.982 at layer 5, without travelling either hop.](img/direct-exposure.png)

These prompts are the second case above -- the subject is there, but behind a preamble -- which is why 0.982 rather than a pinned 1.000, and why it is a layer-5 reading rather than a general one. The high coefficient may therefore reflect direct exposure rather than propagation to the second entity. If so, a method could score well on this criterion without demonstrating the generalisation the criterion is named for.

The caveat I cannot clear is that a coefficient measures delivery, not effect. It says how much of the edit vector arrives at a token, not how far the model's answer moves as a result. Every reading above is on the unedited model, and no edit was run at any layer but 5. Until I show the estimate predicts measured behaviour, a screen built on it is a proposal, not an instrument.

## Why I think this is a contribution rather than a complaint

The same measurement can be run on the *unedited* model in one forward pass, before any edit is applied. So it could screen benchmark items in advance, rather than explaining results after the fact.

And the field already has items that pass such a screen. In MQuAKE, by my count, the edited subject appears in the prompt whenever the edit is on the first hop (6,861 of 6,861 items) and never when it is further along the chain (0 of 16,506). Clean propagation items exist; they are just mixed in with items that cannot distinguish the two.

The closest related work I found is ChainEdit, which identifies a different problem in the same benchmark. Its repaired prompts still contain the edited subject, so they may remain open to this effect -- though I should check that against their exact prompt construction before saying so anywhere public.

## Where I am stuck, and what I would ask

I set out to look at the other direction entirely: not what an edit implies going forward, but what happens to the grounds that made the original fact true.

![The grounds that made a fact true on the left, the consequences that follow on the right, and the edit landing in the middle. Forward arrows are solid and marked as the direction edit-propagation benchmarks usually test; backward arrows are dashed and marked as a less-tested direction.](img/propagation-both-ways.png)

I never got there. The forward side turned out to have a measurement problem sitting in front of it, and that is what these three emails are about.

So, two questions, and I would value either.

Natalie -- would a pre-edit screen like this be useful to anyone, or is this already known and handled in a way I have not found? I am wary of building an instrument nobody asked for.

Arnab -- where would you attack this first? My own guess is the delivery-versus-effect gap, since every number here is from a model that was never edited.

Thank you both for reading three emails in a row.

Saif Ul Islam
