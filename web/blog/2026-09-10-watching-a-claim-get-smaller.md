---
slug: watching-a-claim-get-smaller
title: "Watching a claim get smaller"
authors: [saif]
tags: [lab-notes, knowledge-editing, edit-slice, method]
date: 2026-09-10
---

These are lab notes, not results. I'm starting a project called **edit-slice** and
writing down what I learn while it is still provisional — including the parts
that turn out to be wrong. Today's entry is about a claim of mine shrinking, which
was the most useful thing that happened all day.

<!-- truncate -->

## The setup

When you edit a fact into a language model's weights — ROME, MEMIT, and friends —
you change one thing and disturb an unknown amount of other things. The standard
way to evaluate this is to check the edit's **consequences**. Move the Eiffel
Tower to Rome, then ask what country it's in, what language people speak nearby,
what else is in Rome. Does the change ripple outward correctly?

The thing I got interested in runs the other way. The Eiffel Tower is in Paris
partly *because* of a set of other facts — it was built for the 1889 Paris
Exposition, it stands on the Champ de Mars. Those aren't consequences of its
location. They're closer to the reasons the location was true in the first place.

Edit the tower into Rome and those facts are still sitting there, untouched,
quietly implying the thing you just deleted. The model now holds a belief and a
complete set of grounds for its negation. I've been calling that an **orphan**,
and the claim I started with was roughly: *everyone probes forward, nobody probes
backward.*

## The suspicion

That claim was too comfortable, which is usually a bad sign.

The obvious place for it to break is Cohen et al.'s **RippleEdits** benchmark. One
of its evaluation criteria is *Logical Generalization*, and I knew it covered
symmetric and inverse relations. Symmetric relations sound backward. If Logical
Generalization is already a grounds probe, my claim isn't narrow — it's taken.

I could have gone on citing a summary. Instead I went to read the definitions.

## Two things I found

**First, a bookkeeping thing that isn't really about the argument but is worth
saying out loud.** I had a note in another repo describing this paper as EMNLP
2023. It's TACL 2024 (arXiv 2307.12976). I don't know how many times I'd read past
that. Secondhand notes decay silently, and I'd been treating mine as though they
couldn't.

**Second, the actual definition.** Logical Generalization says that relations
satisfy logical constraints — Sibling is symmetric, so if `(e, Sibling, o)` holds
then `(o, Sibling, e)` holds too — and checks whether those constraints survive
the edit. Location gets checked for transitivity the same way.

So it does probe something that looks backward. Edit *(Eiffel, located-in, Rome)*
and it will ask what Rome contains.

But that's the **same triple with its arguments swapped**. It's the edit restated,
not the reasons for the edit. And the transitive case is sharper: to get from
"Eiffel is in Rome" to "Eiffel is in Italy" you have to *use* the fact that Rome is
in Italy — but the benchmark only ever checks the conclusion. Whether the premise
survived is never asked.

That distinction turned out to be the whole thing, so I now write it down every
time:

- **Argument order** — swap the arguments of the edited fact. Covered, by
  RippleEdits, since 2024.
- **Justification order** — the *distinct* facts whose truth was a premise for the
  edited fact. Not covered by anything I can find.

"The Eiffel Tower was built for the 1889 Paris Exposition" isn't the location fact
inverted. It's a different fact about a different thing, and it's the one that goes
stale in silence.

## The claim, smaller

I can't say backward probing is unexplored. I can say:

> Existing ripple evaluation probes the logical closure of the edited triple.
> Inverse and symmetric probes exist and are backward in *argument* order. Nothing
> probes backward in *justification* order.

That's a much less exciting sentence and a much more defensible one. It also cost
me nothing except an afternoon, which is the point: I'd rather find the
counterexample to my own claim than have a reviewer find it for me, in a room, in
front of people. Same information, very different afternoon.

## What I'd take from it

Three things, none of them profound, all of them things I apparently needed to
relearn:

1. **Read the primary source before designing around a summary.** Both errors here
   — the wrong venue and the almost-scooped claim — came from trusting notes.
2. **Go looking for the strongest counterexample to your own idea, early.** If it
   holds, you've lost a week. If it doesn't, you've gained a defensible sentence.
3. **A claim getting smaller is progress.** It felt like a setback for about ten
   minutes and then it felt like the first solid ground the project has had.

Still entirely open: whether "the grounds of a fact" is even a well-posed notion in
a system that stores everything in superposition and reasons probabilistically. I
have a design and no data. More when there's a number.

*edit-slice is a research instrument for measuring directional propagation of
weight-level knowledge edits. It's early. These notes are written to be read over
the shoulder, not cited.*
