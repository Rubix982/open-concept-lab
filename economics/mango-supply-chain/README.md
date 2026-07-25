# One Crate — the synthetic dataset

A small, seeded dataset engineered so that **each of the four stops in the talk
is reproducible by a single Power BI move.** It follows one crate of Sindhri
mangoes from an orchard in interior Sindh to an export container at Karachi
port. The companion scroll artifact is `one-crate.html`; this repo is the data
under it.

Every number the talk relies on is a knob in `config.py`. Change a knob, run
`generate.py`, and the reversal in the room moves with it.

> The numbers here are **pedagogical illustrations, not sourced from real
> firms** — engineered to make a statistical point land. Only the market/economy
> figures in `one-crate.html` are sourced. Keep that distinction when presenting.

---

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python generate.py          # writes data/*.csv + data/one_crate.duckdb, prints diagnostics
```

The diagnostics block is the presenter's proof that every engineered effect
landed at the locked seed (`SEED = 1538`). To confirm the spurious flip is
genuinely seed-dependent noise:

```bash
python generate.py --find-seed   # lists other seeds; the fake flip moves every time
```

Power BI ingests the CSVs in `data/` natively (Get Data → Text/CSV). The
`one_crate.duckdb` file is for local SQL exploration and is not needed for the
Power BI build.

---

## Tables

A small star-ish schema. Load all six; the relationships below let Power BI join
the confounder (`cold_chain`, which lives on the route) back onto each lot.

| Table | Grain | Key columns |
|---|---|---|
| `suppliers` | one row per network | `supplier_id`, `network` (A/B) |
| `routes` | one row per route | `route_id`, **`cold_chain`**, `terrain` |
| `carriers` | one row per carrier | `carrier_id`, `advertised_mean_days` |
| `orders` | one row per inspected lot | `lot_id`, `network`, `route_id`, `cold_chain`, `inspector_id`, `weekday`, `captured_at`, `weight_in_kg`, `quality_pass`, **`passed_flag`** |
| `deliveries` | one row per shipped lot | `delivery_id`, `lot_id`, `carrier_id`, `transit_days`, `missed_ship`, **`value_retained`**, `on_time_flag` |
| `demand_signal` | one row per (week, tier) | `week`, `tier`, `tier_rank`, `orders_placed`, **`pct_vs_baseline`** |

**Relationships to create in Power BI:**

```
orders[supplier_id]  ->  suppliers[supplier_id]
orders[route_id]     ->  routes[route_id]        (brings cold_chain onto every lot)
deliveries[lot_id]   ->  orders[lot_id]
deliveries[carrier_id] -> carriers[carrier_id]
```

Boolean columns (`quality_pass`, `on_time`, `missed_ship`) each ship with a 1/0
mirror (`passed_flag`, `on_time_flag`, `missed_ship_flag`) so a rate is a single
drag — drop the flag into a visual as **Average** and you have a percentage.

---

## The four stops → the exact move

Numbers below are what you will see at `SEED = 1538`.

### Stop 01 · The number that doesn't exist — *Measurement*

**Lesson:** the first hard problem is not analysis, it is *capture*. A third of
the crop is "lost," but a large share of lots were never weighed at all — the
variable doesn't exist to be sliced.

**Move:** Matrix. Rows = `cold_chain`. Value = **Average of** a blank-capture
measure, or simply `Count (Blank)` of `weight_in_kg`. Add a Card: `Average of
post_harvest_loss_frac`.

**Expect:**
- ~**28%** of all lots have **no captured weight/timestamp** (`capture_method =
  broker_memory`).
- The gap is structured, not uniform: **~46% on rural (no-cold-chain) routes**
  vs **~10% on cold-chain corridors**.
- The loss KPI (~**31%**) is computable on only **~72%** of lots — it is an
  average over a hole. Point at the Card and ask: *31% of what we measured, or
  of what shipped?*

### Stop 02 · The aggregate that lies — *Simpson's paradox*  ← the core move

**Lesson:** the average measures the *terrain*, not the operator. This is the
one stop where the tool's single core operation — group-by-dimension — both
creates the lie and resolves it.

**The real flip (keep it):**
- Visual: clustered bar. Axis = `network`. Value = **Average of `passed_flag`**.
  → **A = 90.7%, B = 75.6%.** Make the room commit to dropping B.
- **The single move:** drag **`cold_chain`** onto the axis as a second grouping
  (or drop it on a slicer). → within **both** strata **B beats A**:
  - cold-chain: A 96.1% · **B 97.5%**
  - no-cold: A 53.9% · **B 72.6%**
- B only looked worse because it serves the rural no-cold-chain routes. The
  average measured B's terrain.

**The spurious flip (discard it):**
- Reset the split. Now drag **`inspector_id`** onto a slicer and select
  **`INS-00`**. → B (86.2%) now beats A (80.7%), *without* conditioning on cold
  chain. It looks exactly like another confounder.
- It is not. `inspector_id` has **no causal link** to pass rate in the
  generator — this reversal is sampling noise. **That contrast is the discipline
  lesson:** disaggregate only on a variable you have a causal reason to trust.

**The numbers behind the claim** (`python generate.py --robustness`, 3,000-seed
sweep):

| | across 3,000 seeds |
|---|---|
| REAL cold-chain flip holds in both strata | **99.6%** (2,988/3,000) |
| SPURIOUS inspector flip present at all | **1.5%** (45/3,000) |
| which inspector the fake flip lands on | spread evenly across all 8 — no favourite |

Read that out loud in the room: a clean fake flip is so rare that seed 1538 was
*searched for*, and it never prefers a particular inspector — the signature of
noise. The real confounder, meanwhile, survives essentially every reseed.

### Stop 03 · The average that hides the risk — *Variance & tail*

**Lesson:** the mean is the optimised number and the wrong number. With a
perishable and a ship to catch, the tail is not a delay — it is total loss.

**Move:** bar with Axis = `carrier_id`.
- Start with Value = **Average of `transit_days`** → **A 10.6 days < B 14.0**.
  A looks better. (Carrier A = "SindhExpress, fastest average.")
- **The single move:** swap the measure to **Average of `value_retained`** (or
  add **Average of `missed_ship_flag`** and **StDev of `transit_days`** as
  columns). The decision inverts:

  | carrier | mean days | std days | % missed ship | mean value delivered |
  |---|---|---|---|---|
  | CAR-A | 10.6 | **7.7** | **26.7%** | **0.663** |
  | CAR-B | 14.0 | 1.0 | 1.9% | **0.775** |

- Optional: a histogram of `transit_days` filtered to CAR-A shows the fat right
  tail — the ~1-in-4 runs that blow past the day-16 ship cutoff and zero out.

### Stop 04 · The signal that distorts as it climbs — *Bullwhip*

**Lesson:** no one sees true demand; everyone reacts to the echo, and the echo
amplifies upstream.

**Move:** line chart. X = `week`. Y = **`pct_vs_baseline`**. **Drag `tier` onto
Legend.** Four lines fan out; amplitude grows consumer → farm.

**Expect** (peak deviation from each tier's own pre-bump baseline, off a real
**+5%** consumer step at week 26):

| tier | peak order swing |
|---|---|
| consumer | +6% |
| retailer | +9% |
| exporter | +18% |
| **farm** | **+41%** |

Optional: bar of **Variance of `orders_placed`** by `tier_rank` — it climbs
monotonically upstream (≈600 → ≈10,800).

---

## The turn, in the data

All four are one problem: a distributed system with **no shared ledger**. The
confounder nobody logged (Stop 02) is the *same absence* as the weight nobody
captured (Stop 01), the tail nobody priced (Stop 03), and the true demand nobody
can see (Stop 04). Power BI earns its place as the instrument that reassembles
the whole from the slices — and Stop 02's spurious flip is the reminder that the
instrument amplifies your errors too.

## Files

```
config.py        every engineered effect size, one knob each (edit here)
generate.py      seeded generator + diagnostics + --find-seed
data/            six CSVs + one_crate.duckdb
RUNSHEET.md      timed live click-path for each reversal
requirements.txt pinned deps
```
