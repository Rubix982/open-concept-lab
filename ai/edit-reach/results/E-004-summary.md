# [E-004] The far-field coefficient reads the relation, not the subject

_2026-11-01 · Llama-3.1-8B · layer 5 · MQuAKE-CF-3k, 513 single-edit two-hop instances · no edit applied_

## The question

[E-039] measured the coefficient at **0.933** where a multi-hop question names the edited subject and **0.055** where it does not. Its floors came from elsewhere — 0.069 from a permuted `k*` on RippleEdits, 0.027 from a different token on MQuAKE — and T-005 had asked for the floor **on the same prompts**. MQuAKE's questions are longer and multi-hop, so their own floor was an open quantity, and a reviewer could reasonably say 0.055 is two and a half times it.

So: re-read [E-039]'s exact 513 instances keeping the key vectors, and score every hop-2 question against all 512 other instances' `k*`, each with its own denominator.

## The gate

```
                 this run   [E-039]
hop-1 natural      0.9334     0.933     (639 readings)
hop-2 final        0.0544     0.055     (900 readings)
```

Reproduced inside the ±0.02 stated before the run. The path every edit-slice number was read through has not moved.

## The answer, and it is not the one the first floor suggested

Against **all** donors, the far field looked like it had signal:

```
hop-2  own k*                  0.0543
       floor, all donors       0.0298     excess +0.0232  CI (+0.0206, +0.0255)
```

That excess is real and it is **not** about the subject. A hop-2 subject is the chain's middle entity, so the question is *about* it indirectly, and topical overlap would produce exactly this. Splitting the donors by whether they share the edited relation separates the two:

```
                           floor    excess over it
hop-2  SAME-relation        0.0481    +0.0002   CI (+0.0001, +0.0004)
       DIFFERENT-relation   0.0294    +0.0244   CI (+0.0215, +0.0271)

hop-1  SAME-relation        0.0506    +0.8439   CI (+0.8379, +0.8500)
       DIFFERENT-relation   0.0590    +0.8754   CI (+0.8696, +0.8817)
```

**In the far field, a stranger's edit on the same relation reaches the question as much as the real subject's edit does — to within +0.0002.** In the near field, where the question names the subject, the gap survives the same control almost untouched (+0.8439 against +0.8754).

So the entire far-field excess over a naive floor is the relation. None of it is the subject.

## What this settles

The coefficient has **no subject-specific dynamic range in the far field**. It is a contamination detector — it tells you an edited subject is named in a prompt — plus a relation detector. It is not a propagation detector, and multi-hop propagation is exactly where it is asked to work.

This is the narrower and more defensible claim T-005 anticipated, and it is now ours rather than a reviewer's.

It also settles a question [E-039] could not: its two convergent floors, 0.069 and 0.027, bracket the same-prompt all-donor floor of 0.0298, so the convergence was sound. What neither floor controlled for was the relation, and that is where the apparent far-field signal lived.

## Limits

- **Delivery, not effect** ([E-028d], 2.96×). Nothing here measures how far an answer moves. A floor result says this measure does not see far-field propagation at layer 5; it does **not** say an edit fails to reach the answer. An edit alters the subject token's representation at layer 5 and that alteration travels through attention in layers 6 and above, on a path this measure cannot see at all.
- **Two-hop chains only**, single-edit instances, one model, one layer. 1,907 instances were skipped as multi-edit or with an unlocatable hop.
- **The relation control is categorical**, not graded. Donors share a relation id or they do not; how *close* two relations are is not measured here.
- The +0.0002 interval excludes zero. It is detectable and negligible — the same shape of statement as [E-002]'s content effect, and it should not be quoted as "exactly zero".
