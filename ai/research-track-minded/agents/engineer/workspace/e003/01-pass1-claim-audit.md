# E-003 · Pass 1 — the claim audit

Target: a new section of `web/blog/2026-09-15-five-days.mdx` covering [E-016] and
[E-017], plus a correction to the published "Known gaps" paragraph.

## Finding 1, before writing a word: Pass 1 is written for revision only

`SKILL.md` says *"For each paragraph of the draft, fill one row"*. There is no
draft. Drafting needs the audit run **forward on the claims available**, before
prose exists — otherwise the first draft is written unaudited and the audit
becomes a cleanup pass, which is exactly the ordering the project argued against.

Adapted here by auditing the candidate claims from `edit-slice/agents/shared/
decisions.md`. The skill should say this explicitly. Logged for the ticket.

## The audit

| # | Claim | Own / attributed | What would make it false |
| --- | --- | --- | --- |
| C1 | ROME's `(k·u)/(u·k*)` normalisation fixes the coefficient at the subject's last token to exactly 1, for any `u` and therefore any `C` | own, analytic | exhibit a `C` under which a prefix-sharing probe scores ≠ 1 at that position |
| C2 | Therefore whitening cannot reduce same-subject leakage; it can only touch probes that do not share the prefix | own, follows from C1 | a whitened editor that reduces leakage to a prefix-sharing probe |
| C3 | Birth-arm top-1 destination identical to `C = I` in 42/42 chains at all three λ | own, empirical | re-run showing a different destination in any chain |
| C4 | `cos(k*, C⁻¹k*) = 0.97` is compatible with a ~20× change in the coefficient on held-out keys — the cosine hid the whole effect | own, empirical | held-out coefficient ratio near 1.0 at the same cosine |
| C5 | Moving the subject later attenuates the coefficient ~7% (mean 0.935), and a *different relation* scores exactly 1.000 | own, empirical | a natural probe form scoring materially below 0.9 across chains |
| C6 | Same-subject leakage in ROME is structural: any prompt containing the subject receives 93–100% of the edit vector at the subject's last token | own, headline | C1 or C5 falsified; or the same sweep at another layer showing context-sensitivity |
| C7 | [E-015]'s +0.0 pp null was structurally required, not an artifact of a blunt editor | own, follows | any `C` producing a non-zero gap |
| C8 | The gap this write-up previously named — "a whitened editor is the obvious place a genuine inference effect could still hide" — is closed, and was closed by an argument rather than a search | own, correction | C1 falsified |
| C9 | Two mechanisms I predicted were wrong: probe-key alignment (cos = 0.034, near-orthogonal) and destination scale-invariance (×0.27 breaks relocation in 3 of 4) | own, self-report | the measurements re-run differently |
| C10 | [E-017] part 1 is **unrun**, not negative: the late probe holds the true city at baseline in 8/42 chains, below the pre-stated floor of 10 | own, scope | — (a statement about what was not done) |

**Every row has a fourth column.** No row needed demoting to attribution and none
needed cutting.

## Second finding: the audit changed what the section is about

Filling the table put **C1 at the top**, and C1 is analytic. The empirical result
everyone would lead with — 42/42 chains unchanged — is C3, and it is *downstream*:
it is what C1 predicts, not what establishes it.

Lead with the argument, report the measurement as confirmation. Left to instinct I
would have opened with "we ran the whitened editor and nothing happened", which
buries the only durable thing here. The audit produced a structural decision about
the writing, not a copy-edit.

## Limits to carry into the draft

- 16 chains for the [E-017] sweep, 42 for the edit arm; one model, one layer, one
  relation family
- minima of 0.483, 0.670, 0.707 mean **some subjects do attenuate materially** —
  existence and tendency, never a rate
- named falsifiers: a subject-mentioning probe form scoring below ~0.9 across
  chains; the same sweep at a different layer. Both cheap, neither run
- C10 — the relocation comparison is unrun
