# Ripple-edit results — concrete numbers & reproducibility (E-014)

## Layout
```
results/
├── README.md              ← this file (index + repro)
├── final/                 ← THE shareable data (everything below regenerates from data/)
│   ├── data/              scale_study.json (397) · rome_study.json (26) · tb_rows.json (243)
│   ├── figures/           scale_distribution.png · rome_blast_radius.png · by_type.png · *_arc.png
│   └── tables/            scale_summary.txt · scale_examples.txt · *_arc.txt · propagation_table.txt
├── logs/                  full run logs (efficacy per edit, optimization traces)
├── cache/                 rep_cache.pt (regenerable representation cache)
└── archive/               superseded / dud intermediate runs
```
Share `final/`. Everything in it regenerates from `final/data/` via the two commands below.


**What this measures.** When ROME edits one fact into gpt2-small, what happens to its
*typed logical neighbours*? On a **random** sample of RippleEdits (no cherry-picking),
each neighbour gets a 4-way outcome: **updated** (edit reached it, correct new value),
**stale** (kept old value — edit didn't reach it), **broken** (wrong/incoherent),
**fine** (locality: correctly unchanged).

## Headline numbers
100 random edits · **97% efficacy** · 90 flipped edits → **397 neighbour rows** · ±95% Wilson CI

| neighbour type | updated | stale | broken | n |
|---|---|---|---|---|
| paraphrase | **57%** [49–64] | 23% [17–30] | 20% [15–27] | 178 |
| 1-hop | 4% [1–15] | **61%** [46–74] | 35% [23–49] | 46 |
| 2-hop | 8% [5–13] | 11% [7–17] | **81%** [74–86] | 170 |
| locality | — | — | (n=3, not measurable) | 3 |

**Mechanism — over-propagation rises with hop distance.** Of the *broken* cases, the
fraction that are **target-bleed** (the edit's new value injected into the neighbour's
slot) climbs monotonically:

| | paraphrase | 1-hop | 2-hop |
|---|---|---|---|
| broken cases that are target-bleed | 0% [0–10] | 25% [10–49] | **58%** [50–66] |

So at 2 hops, the majority of breakage is not random noise — it's the edited value
**spilling** into places it shouldn't go.

**Two corrections vs. the earlier 5-landmark run (`[T-015]`) — this is the point of
random sampling:**
- Paraphrase generalization was **5/5 (100%)** on landmarks → **57%** at scale.
- 1-hop *broke* on landmarks (4/5) → at scale it's predominantly **stale** (61%).

## Caveats (state these)
- **gpt2-small is weak** → absolute rates are capacity-bound; the *shape* (hop-decay,
  rising over-propagation) is the transferable finding, not the exact %.
- **Locality is not measurable here** (n=3): the competence filter correctly drops
  locality neighbours the model can't answer pre-edit, and gpt2-small knows almost none
  → specificity needs a capable model. Do **not** claim specificity from this run.
- Subject derived heuristically from the prompt (RippleEdits ships only a QID);
  validated by the 97% efficacy. Outcomes via greedy-generate substring match.

## Environment
- **Editing** runs: `.venv-edit` (Python 3.12, transformers 5.5.4 pinned for EasyEdit);
  EasyEdit cloned at `~/code/EasyEdit` (added to `sys.path` by the scripts).
- **Analysis/figures**: `.venv` (matplotlib, numpy).
- **Data**: `~/code/RippleEdits/data/benchmark/{popular,random,recent}.json` (885 / … entries).
- **ROME config**: `experiments/edit_propagation/rome_gpt2_mom2.yaml` (covariance ON;
  mom2 stats cached at `data/stats/gpt2/wikipedia_stats/...c_proj_float32_mom2_3000.npz`).

## Reproduce (from repo root)
```bash
# 1) generate editing data — deterministic (seed=1538)
source .venv-edit/bin/activate
N_EDITS=100 python experiments/edit_propagation/scale_study.py > results/logs/scale_run.log 2>&1
#   → final/data/scale_study.json, final/tables/scale_summary.txt

# 2) aggregate: figure + 95% CIs + target-bleed + examples
source .venv/bin/activate
python experiments/edit_propagation/aggregate_scale.py
#   → final/figures/scale_distribution.png, final/tables/{scale_summary,scale_examples}.txt
```
- Different sample: `RE_FILE=~/code/RippleEdits/data/benchmark/random.json N_EDITS=200 …`
- Different seed: `SEED=<n> …`  (checkpoints every edit → safe to interrupt/resume-by-rerun)

## Outputs (what to share — all under `final/`)
| file | what |
|---|---|
| `figures/scale_distribution.png` | 100%-stacked outcome bars by neighbour type (the figure) |
| `tables/scale_summary.txt` | rates ± 95% Wilson CI + target-bleed rate |
| `tables/scale_examples.txt` | concrete real cases per failure mode (stale / bleed / incoherent / clean) |
| `data/scale_study.json` | 397 raw per-neighbour rows (regenerates everything above) |
| `../logs/scale_run.log` | full ROME edit log (efficacy per edit, optimization traces) |

## Determinism
Random sampling seeded (1538); greedy decoding; ROME context templates + mom2 stats
cached → reruns reproduce the same edits. Minor CPU float nondeterminism is possible
but outcome labels are stable.
