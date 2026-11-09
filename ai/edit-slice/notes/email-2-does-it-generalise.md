Hi Natalie, Arnab!

Following on from the Vlaminck case I sent earlier. The obvious question about that email is whether he was special, so this is the same measurements over larger sets, and what they did to my explanation.

Two things to say up front. These are CounterFact subjects with hand-built probes, so everything below is an existence claim about what can happen, never a rate over knowledge in general. And the second run below is the one that ended up mattering most, for a reason I did not anticipate.

## An edit with no claim on the answer moved it just as often

The first run takes 42 people. Each person gets their own new country -- 22 different ones across the set -- and that country is held fixed while only the relation it attaches to changes:

1. one edit changing where he was *born*
2. one edit changing where he *works*

Then one question, for both: which city was he born in? Only the first edit has any business touching that answer. If the model were responding to the relation we edited, the birth edit should move it more often.

![Two overlapping circles over 42 people, each given their own new country in both arms. The birth edit moved 28 of them and the work edit moved 28, but only 19 are in both: nine moved only under the birth edit, nine only under the work edit, five under neither.](img/two-arms-overlap.png)

It did not. Both edits put the birth city in the new country for 28 of the 42, and not even the same 28 -- nine moved only under the birth edit, nine only under the work edit.

The injected country still decides *where* the new city is: about 82% of the changed birth cities are that country's capital, in both arms alike. So the country chooses the answer, while something else -- possibly just which person it is -- decides whether the answer changes at all. I cannot say why a work-location edit should reach a birth-city question at all, and this run does not tell me.

## Vlaminck was not special in being hit. He was special in having been right.

The second run repeats the profession probe on 37 people. I was looking for the cultural association I had guessed at -- Chile with poetry, and so on.

That did not survive. Eleven countries received more than one person, and only once did two of them land on the same replacement: two people both became "Danish", which is a nationality rather than a profession. Everyone else landed somewhere unrelated to everyone else sent to the same country. I could find no link between the country we injected and the profession that replaced the old one.

What the run did show was something I had not thought to check. Before any edit, the model had the profession right for only **5 of the 37** -- and Vlaminck was one of the five. But the edit changed the top answer for **33 of the 37**, including 30 people whose profession the model already had wrong.

So the edit reaches nearly everyone. For most of them there was simply nothing correct sitting there to break. Vlaminck's fall was visible because he was one of the few with something to lose, not because he was treated differently.

I also checked whether the new profession might be a reshuffle of what the model already associated with that person. It was already in their own top eight 7 times out of 33, against about 10% for a stranger's top eight. On 33 people that is too thin to call either way.

## On citizenship, the objection I was trying to defeat simply wins

The same run gave this:

    "X is a citizen of"                         base     after the edit
    its top answer is the country we injected    0/37        25/37
    its confidence in its own top answer        55.9%        72.7%

The second row is not the probability of Chile, or of any particular country. It is how much confidence the model puts on whichever answer it ranked first, averaged over the 37 people. Before the edit that answer was never the injected country, and the model was still fairly sure of whatever it did say instead.

This is exactly what coherent revision predicts: move a man's birth to Chile and the model calls him Chilean, more confidently than it called him anything before. On citizenship there is no puzzle to explain. The puzzle is confined to the questions the edit has no claim on.

## Where this leaves me

Taken together: the edit reaches almost every person; it reaches questions that the edited relation does not bear on; it reaches them about as often as the relevant edit does; and what it puts there is specific without being predictable from the country.

That last pattern is what started me looking at ROME's update rule directly, rather than at the answers. I will send that separately -- it is the part I think may actually matter to how propagation gets evaluated, and it deserves its own email.

Thanks both,

Saif Ul Islam
