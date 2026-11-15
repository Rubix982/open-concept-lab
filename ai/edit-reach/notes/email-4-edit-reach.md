# Email 4 — the edit-reach paper, to Natalie and Arnab

_Drafted 2026-11-15. Link verified live the same day. Not sent._

_ Not committed — decide whether it should be, like emails 1–3 are._

**Subject:** A negative result on screening edits before you run them

---

Hi Natalie, Arnab,

Following the Vlaminck case I sent at the end of October. That one was a single edit followed to the end; this is the measurement it turned into, and it came out negative, which is why I think it is worth your time rather than despite it.

The idea was a screen: a rank-one edit divides its update by a fixed inner product, so for any prompt you can compute how much of the edit lands on it — in one forward pass, through the model as it was *before* the edit. If that number tracked damage, you could score an evaluation item without having to anticipate it.

It does not. It is pinned at 1.000 wherever the prompt names the edited subject and flat where it does not, which is the only regime propagation lives in. A raw correlation of 0.522 against measured movement falls to 0.085, interval (−0.003, 0.172), once a same-subject control is removed.

What it does detect is contamination. RippleEdits has a two-hop test type whose prompts contain the edited name; those items take a median 0.982 of the update against a 0.065 floor. MQuAKE has the same exposure in 6,861 of 6,861 head-of-chain items and 0 of 16,506 downstream ones, so a clean subset already exists in the field's own data.

https://rubix982.github.io/open-concept-lab/notebook/edit-reach/paper/

There is a **Plain** tab at the top that says the whole thing without notation, if it is easier to judge that way, and a **Threads** tab listing what was asked along the way, including what came back the other way. PDF is linked from the masthead.

The question I cannot answer from inside: is a contamination screen on existing benchmarks worth anything to anyone, or is it a thing authors already catch by eye?

Saif

---

## Notes to self, not for sending

- Emails 2 and 3 (`ai/edit-slice/notes/`) are still held pending a reply to email 1. This one does not replace them; it is the newer project.
- Do not add a citation line, BibTeX, or any affiliation beyond Open Concept Lab.
- If no reply comes to this either, the parked card in `ai/edit-slice/CARD.md` says to close on its second branch deliberately rather than keep waiting.
