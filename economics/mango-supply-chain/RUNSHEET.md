# Presenter's run sheet — the live build

The click-path for each reversal, in order, timed. ~18 min of live Power BI
inside the ~40 min talk. Numbers are for `SEED = 1538`.

**Before the room arrives (do NOT do live):**
- Get Data → Text/CSV → load all six files from `data/`.
- Model view → create the four relationships (see README). This is the only
  fiddly bit; never do it live.
- Have one blank report page per stop, tables in the Fields pane, and the crate
  photo / `one-crate.html` open in a second tab for the narrative beats.

The whole point of building live is that the *reversal* is the reveal. Build the
"wrong" answer first, let the room commit to it out loud, then make one move.

---

## Stop 01 — Measurement gap · ~3 min

1. New Card visual → drag `orders[post_harvest_loss_frac]`, set to **Average**.
   Reads **~31%**. *"Here's the famous number. A third lost."* **(0:30)**
2. New Matrix → Rows = `orders[cold_chain]`; Values = `orders[weight_in_kg]` set
   to **Count (Blank)**, plus `weight_in_kg` as **Count**. *"How many did we
   actually weigh?"* **(1:30)**
3. Point: **~46%** of rural lots have no weight at all vs ~10% on cold routes.
   *"The 31% is an average over the 72% we could measure. The other 28% lives in
   a broker's memory. The first product isn't analytics — it's the scale."*
   **(3:00)**

**Landing line:** *the variable didn't lie to you — it was never recorded.*

---

## Stop 02 — Simpson's paradox · ~6 min  (the centerpiece — don't rush)

1. New Clustered bar → Axis = `network`; Value = `orders[passed_flag]` as
   **Average**. Reads **A 91% / B 76%**. **(0:45)**
2. *Stop. Ask the room: "Do we drop network B?"* Get a show of hands / a verbal
   yes. Make them commit. **(1:30)**
3. **The move:** drag `routes[cold_chain]` onto the axis (below `network`), or
   drop it on the Legend. The bars regroup. **(2:15)**
4. Read it out: within cold-chain **B 97.5 > A 96.1**; within no-cold **B 72.6 >
   A 53.9**. *"B wins on both. It only looked worse because it runs the rural
   routes with no cold chain. The average measured its terrain."* **(3:30)**
5. **Now the trap.** Remove `cold_chain`. Add a Slicer on `orders[inspector_id]`.
   Select **INS-00**. Bars: **B 86 > A 81**. *"Wait — inspector flips it too. Did
   we find another confounder?"* **(4:45)**
6. **The kill.** *"No. I generated this data — inspector has zero effect on pass
   rate. That's noise."* If you have a terminal handy, run `python generate.py
   --find-seed` and show the fake flip landing on a different inspector each
   seed, while cold-chain never moves. **(6:00)**

**Landing line:** *you can always slice until something flips. Slice only on a
variable you have a causal reason to trust.*

---

## Stop 03 — Variance & tail · ~4 min

1. New Clustered bar → Axis = `carriers[carrier_id]`; Value =
   `deliveries[transit_days]` as **Average**. Reads **A 10.6 < B 14.0**. *"Which
   carrier?"* Room picks A, the fast one. **(1:00)**
2. **The move:** drag two more measures into the same visual (or a Table beside
   it): `deliveries[value_retained]` as **Average** and
   `deliveries[missed_ship_flag]` as **Average**. **(2:15)**
3. Read: A delivers mean value **0.66**, misses the ship **27%** of the time; B
   delivers **0.78**, misses **2%**. *"The fast carrier strands the fruit one run
   in four. For a perishable with a ship to catch, that tail isn't a delay — it's
   a write-off."* **(3:15)**
4. Optional flourish: histogram of `transit_days` filtered to CAR-A → point at
   the fat right tail past day 16. **(4:00)**

**Landing line:** *the number they optimised (the mean) is the wrong number.*

---

## Stop 04 — Bullwhip · ~3 min

1. New Line chart → X = `demand_signal[week]`; Y = `demand_signal[pct_vs_baseline]`
   as **do not summarize / Average**. One flattish line. **(0:45)**
2. **The move:** drag `demand_signal[tier]` onto Legend. Four lines fan out.
   **(1:30)**
3. Point at week 26: consumer nudges **+5%**, farm spikes **+41%**. *"Same real
   signal. Each link padded against the one below it. Nobody up here can see the
   +5% — they only see the echo."* **(2:30)**
4. Optional: bar of `orders_placed` **Variance** by `tier_rank` — climbs
   monotonically upstream. **(3:00)**

**Landing line:** *the fix isn't better forecasting at one node — it's a shared
view of the real signal, which this chain doesn't have.*

---

## The turn (no slides needed) · ~1 min

Flip back to `one-crate.html`. *"Measurement gap, lying aggregate, hidden
variance, bullwhip — four faces of one thing: a system nobody can see whole. The
dashboard is the instrument that puts the slices back together. And Stop 02 is
the warning label: it amplifies your thinking, including your mistakes. The
judgment stays with you."*

---

### Recovery notes
- If a relationship is missing, `passed_flag` averages will look wrong (no
  `cold_chain` split possible). Fix in Model view, not live.
- If `passed_flag` shows as **Sum**, click the field → Summarization →
  **Average**. Same for every rate.
- If the spurious flip won't reproduce, you're not on `SEED = 1538`. Re-run
  `python generate.py` and reload the CSVs.
