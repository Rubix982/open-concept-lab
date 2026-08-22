# TODO — 2026-08-24 (resume at Fajr)

Context in `plan.md` → Morning resume; findings in `agents/shared/findings.md`;
demo in `presentation/SESSION_RESULTS.md`. Monday call: Natalie + Arnab.

## First brick — make ROME actually flip (unblocks T-015)
- [ ] Run the real-ROME (covariance on) test:
      `source .venv-edit/bin/activate`
      `ROME_CFG=rome_gpt2_mom2.yaml python experiments/edit_propagation/rome_study.py`
      (EasyEdit computes mom2 stats from wikitext on first run — may take a while.)
- [ ] Check efficacy=YES (argmax flips to target). If NO → tune config
      (clamp_norm_factor, v_lr, layers) or flag for Arnab; consider GPU substrate.

## Second brick — T-015 real data + the graph
- [ ] With a working edit: `python experiments/edit_propagation/viz.py`
      → `results/rome_blast_radius.png` (edit-centre, neighbours by outcome).
- [ ] Read the 3-way table + the printed stale/broken list.
- [ ] Study the stale/broken cases: what's shared (hop? subject? position?) — the
      "what would make them fine" question. Log to findings as [T-015].

## Monday prep (do even if experiments stall)
- [ ] Re-read `presentation/SESSION_RESULTS.md` top-to-bottom; tighten to a 15-min tell.
- [ ] Finalise the questions for Arnab (mom2 stats needed? GPU substrate? interchange
      vs weight-edit? RAVEL vs RippleEdits? biggest hole?).
- [ ] Confirm the call time with Natalie (Thu 10am Boston was tentative — she said
      she'd update a day before; check email).

## If time / stretch
- [ ] Decide compute substrate (Mac-local vs Colab/cloud GPU) — today showed local
      is a friction sink; a GPU makes ROME/MEMIT + bigger models "just work".
- [ ] If ROME works on gpt2: try gpt2-xl on GPU for a model that knows the facts.

## Parked / open threads
- T-006 (thesis): does the causal-read graph mirror the entailment graph?
- T-B: strengthen predictor (bilinear / edit-difference) vs. real propagation labels.
- gpt2-medium logits-NaN on this Mac (deprioritised — use gpt2 or GPU).
