
## [E-014] Dispute: "coherent revision" has a cheaper mechanistic explanation

_Raised by: Engineer · Date: 2026-09-15_
_Disputes: the reading I attached to the [E-013] pilot, and my own commit message_

**Disagreement.** [E-013]'s pilot showed `inner_1` relocating to a city in the edited
country (Edinburgh→Hamburg for Germany) and I read it as the model revising the
defeasible premise while retaining the necessary one. Checking the claim against the
record — prompted by `src/adversary.py` — surfaces a more parsimonious account that
predicts the same data with no inference at all.

**The cheaper account.** `v*` is optimised so that `k*`-keyed inputs emit a value
encoding the target country. `inner_1` shares the subject, so its key is *similar* to
`k*` and receives a large dose of that same vector. A Germany-valued residual stream
promotes Germany-associated tokens, and German cities are Germany-associated. The
relocation follows from representational similarity, not from the model inferring
"born in Germany ⇒ born in a German city". This is the same *expansion/suppression*
story the write-up already argues for, applied one step further than we applied it.

**Why the existing control cannot decide it.** The same-subject occupation control
varies CONTENT, so it establishes that content matters. It does not distinguish
"content that licenses an inference" from "content that is merely country-flavoured".

**The discriminating control (E-015).** Same subject, same target country, DIFFERENT
relation: edit `"X died in the country of" → Germany`, then probe `"X was born in the
city of"`. Birth and death country are independent facts, so no inference runs from
one to the other.
- If `inner_1` relocates to German cities as strongly as under the birth edit, there
  is no birth-specific inference — it is country-content leaking into any same-subject
  probe, and the "revision" reading dies.
- If relocation is materially weaker, something inferential survives and the reading
  is defensible.

**Proceeding as:** [E-014] runs unchanged — establishing that relocation is real,
systematic and country-specific is worth having under either mechanism. But no
artifact may describe it as belief revision, coherent revision, or contraction until
E-015 reports. Consistent with `notes/definitions.md` declaration 6, which forbids any
artifact claiming contradiction was established.

**Also recorded:** "editors expand; they never contract" exists ONLY as a heading in
`web/blog/2026-09-15-five-days.mdx`. It is not in findings.md or decisions.md, and I
attributed it to [E-002] twice in today's commit messages. The claim is structural
(editing methods have no contraction primitive) and is supported there by an external
masking result, not by [E-002]. The attribution was loose; the claim is not ours to
cite as a measurement.

**Resolution needed by:** before any E-013/E-014 result enters the write-up.
**Resolved:** —
