Hi Natalie, Arnab! Hope you are both doing well.

Apologies for the long gap -- I was travelling with family through September and October, so this took much longer than I expected. Rather than send everything at once, I thought I would share one case properly and follow up with the larger runs separately.

In our last call we talked about propagation: which facts should change after an edit, and whether we can measure how far an edit travels. This is one person, followed from the edit to the end.

## One edit, and three things we never asked about

Maurice de Vlaminck was a French painter born in Paris. Before any edit, the model knows he is a painter, that he is French, and that his native language is French.

We apply one edit at layer 5:

> Maurice de Vlaminck was born in the country of -> **Chile**

Then I asked about the city he was born in, which we never edited:

> **before:** Maurice de Vlaminck was born in the city of -> " Paris, France,"
> **after:** Maurice de Vlaminck was born in the city of -> " Santiago, Chile,"

At first this looks like sensible reasoning: the country changed, so the city follows. This is the kind of indirect effect propagation benchmarks are built to measure, and I hoped to find a mechanism behind it.

But three other answers changed too, even though we only edited his birth country. Each line below is a separate question, and the percentage is how much probability the model puts on the answer that was correct before the edit:

- **he is a painter** — 68.7% before, **0.38%** after
- **he is a French citizen** — 32.5% before, **0.15%** after
- **his native language is French** — 60.7% before, **3.4%** after

There is an honest objection here, which I raised against myself straight away: the model may be revising coherently. If Vlaminck was born in Chile, perhaps it should lower its confidence that he is a French citizen or speaks French natively. These numbers alone cannot tell us whether the change is coherent or harmful.

## Changing his job also cost him his citizenship

So I kept the man and changed what we set. Instead of a country, a profession:

> Maurice de Vlaminck works as a -> **urban planner**

He is still born in Paris and still French, so those two answers should hold. Here are the same three questions under both edits:

- **he is a painter** — 68.7% with no edit, 0.38% after the birth edit, **0.007%** after the job edit
- **he is a French citizen** — 32.5% with no edit, 0.15% after the birth edit, **4.7%** after the job edit
- **his native language is French** — 60.7% with no edit, 3.4% after the birth edit, **53.5%** after the job edit

The painter row falling under the job edit is no surprise, since that edit is about his profession. His native language barely moves, which is what coherent revision would predict.

The row I cannot explain is his citizenship: 32.5% down to 4.7%, from an edit that says nothing about where he was born or what nationality he holds. It is a far smaller fall than the birth edit caused, but it is much larger than nothing, and I do not see what the model would be revising.

## What it put there instead

Everything so far measures what the model *gave up*. None of it says what it believes now. So I asked directly:

> By profession, Maurice de Vlaminck is a ___
>
> **before:** painter, 70.9% — and "poet" sits at 0.3%
> **after:** poet, 48.3% — and "painter" has fallen to 0.4%, nineteenth place

I expected damage to look flat: confidence spread thin across guesses, no strong candidate. Instead one confident answer was replaced by another confident answer.

![The model's top eight completions of "By profession, Maurice de Vlaminck is a", before and after one edit to his birth country. Before: painter 70.9%, French 4.5%, then six candidates under 1.1%. After: poet 48.3%, writer 6.1%, Chile 5.4%, sailor 4.8%, and four more. Painter is no longer in the top eight -- it has fallen to nineteenth place at 0.4%.](img/one-answer-for-another.png)

One detail I did not expect: "Chile" itself appears fourth in that list of professions, at 5.4%. The injected country turns up as a candidate answer to a question about his job.

The 70.9% and 68.7% are not contradictory; they measure different things. The earlier table averages the model’s probability for each token in the correct answer, while giving it the correct previous tokens. Here, 70.9% is the probability the model assigns to “painter” as its first token before it starts the answer. That tells us which word it prefers to start with, not the probability of a complete answer.

My next thought was that this is a cultural association -- France with painting, Chile with poetry, Neruda and Mistral. That would make it revision after all. But the very next person we moved to Chile was a composer, and after the edit he was still a composer. So the association story does not hold, at least not in that form.

## Where I am, and what I would ask

Taking Vlaminck on his own:

- an edit to his birth country moved his profession, his citizenship and his language
- an edit to his profession moved his citizenship too
- what replaced the old answer was specific and confident, not noise

I cannot yet say what decides which answer appears in place of the old one.

This is one person, so none of it is a rate. I have the same measurements over larger sets and will send those next, along with what they did to this explanation.

What I would value your view on: is "what replaced it" the right thing to chase, or is the field right to score only how far the original answer fell? I have not found work that looks at the substitute rather than the loss, but that may well be me not knowing where to look.

Thank you both, and sorry again for the long silence.

Saif Ul Islam
