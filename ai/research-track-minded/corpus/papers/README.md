# Exemplar corpus — mechanistic interpretability

Papers Saif would be content to be mistaken for, with passages marked at the
paragraph level. The unit the skill consumes is **a passage plus a note on the
move it demonstrates** — never a citation.

## Selected

| File | Paper | Why it is here |
| --- | --- | --- |
| `rome.md` | Meng et al. 2022, *Locating and Editing Factual Associations in GPT* (NeurIPS) | The notation exemplar. Carries the whole mathematics half of the project. |
| `lookbacks.md` | Prakash et al. 2026, *Language Models Use Lookbacks to Track Beliefs* (ICLR) | Naming new machinery in plain concrete words. Bau lab, Saif's target group. |
| `sparse-feature-circuits.md` | Marks et al. 2025, *Sparse Feature Circuits* (ICLR) | Positioning against prior work, and structural signposting without throat-clearing. |
| `_anti-exemplar-deep-research.md` | AI-generated report, `rome-neighbors/readings/` | Negative control. What the skill must not produce. |

## Held back, with reasons

- **MEMIT** (`Mass-Editing Memory In A Transformer`) — heavier derivation than
  ROME but the same authors and register. Adds notation volume, not a new move.
  Pull in if the notation contract needs more worked instances.
- **NNSight / NDIF** — systems and tooling register, not a findings paper.
  Genuinely useful, but for a *different* document type. Revisit if the skill
  ever grows a tool-paper mode.
- **Unified Concept Editing in Diffusion Models** — diffusion, not mech interp
  on LMs. Off-target for v1.

## Source PDFs

All under `open-concept-lab/ai/lookback-research/docs/`. Extraction:
`.venv/bin/python` + `pypdf`; text cached to the session scratchpad, not
committed (the PDFs are the source of truth and already in the repo).
