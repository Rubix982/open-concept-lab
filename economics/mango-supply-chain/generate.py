"""
One Crate — seeded synthetic dataset generator.

Emits one CSV per table into data/, plus a DuckDB file for local exploration.
Each of the talk's four stops is reproducible from these tables by a single
Power BI slicer move (see README.md).

Run:
    python generate.py            # write data/ + one_crate.duckdb, print diagnostics
    python generate.py --find-seed  # search for a seed carrying the spurious flip

The diagnostics block at the end is the presenter's proof that every engineered
effect actually landed at the locked seed. If a number drifts, the config knob
that owns it is named in config.py.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from config import CONFIG, Config

DATA_DIR = Path(__file__).parent / "data"
SEASON_START = datetime(2026, 5, 1)   # Sindhri mango season
SEASON_DAYS = 100                      # May–Aug dispatch window


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

def build_suppliers() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"supplier_id": "SUP-A", "network": "A", "name": "Corridor Growers Co-op",
             "home_region": "Mirpur Khas"},
            {"supplier_id": "SUP-B", "network": "B", "name": "Rural Smallholder Network",
             "home_region": "Tando Allahyar"},
        ]
    )


def build_carriers(cfg: Config) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"carrier_id": "CAR-A", "name": "SindhExpress Logistics",
             "advertised_mean_days": 10, "advertised_spread_days": 8,
             "pitch": "fastest average transit"},
            {"carrier_id": "CAR-B", "name": "Indus Reliable Freight",
             "advertised_mean_days": 14, "advertised_spread_days": 1,
             "pitch": "never misses the ship"},
        ]
    )


def build_routes(cfg: Config, rng: np.random.Generator) -> pd.DataFrame:
    origins_cold = ["Mirpur Khas", "Tando Adam", "Nawabshah", "Sanghar", "Digri"]
    origins_rural = ["Tando Allahyar", "Umerkot", "Kunri", "Samaro", "Jhuddo"]
    rows: list[dict[str, object]] = []
    for i in range(cfg.routes.n_coldchain_routes):
        rows.append({
            "route_id": f"RT-C{i:02d}",
            "origin": origins_cold[i % len(origins_cold)],
            "destination": "Karachi Port",
            "cold_chain": True,
            "terrain": "corridor",
            "distance_km": int(rng.integers(180, 320)),
        })
    for i in range(cfg.routes.n_nocold_routes):
        rows.append({
            "route_id": f"RT-N{i:02d}",
            "origin": origins_rural[i % len(origins_rural)],
            "destination": "Karachi Port",
            "cold_chain": False,
            "terrain": "rural",
            "distance_km": int(rng.integers(220, 420)),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Stop 01 + Stop 02 — the orders (quality inspection) fact table
# ---------------------------------------------------------------------------

def _pass_prob(cfg: Config, network: str, cold_chain: bool) -> float:
    s = cfg.simpson
    if network == "A":
        return s.pass_A_coldchain if cold_chain else s.pass_A_nocold
    return s.pass_B_coldchain if cold_chain else s.pass_B_nocold


def generate_orders(cfg: Config, rng: np.random.Generator, routes: pd.DataFrame) -> pd.DataFrame:
    cold_routes = routes[routes.cold_chain].route_id.to_numpy()
    nocold_routes = routes[~routes.cold_chain].route_id.to_numpy()

    rows: list[dict[str, object]] = []
    lot_counter = 0
    for network in ("A", "B"):
        supplier_id = f"SUP-{network}"
        frac_cold = (cfg.simpson.frac_coldchain_A if network == "A"
                     else cfg.simpson.frac_coldchain_B)
        for _ in range(cfg.n_lots_per_network):
            lot_counter += 1
            cold = bool(rng.random() < frac_cold)
            route_id = str(rng.choice(cold_routes if cold else nocold_routes))

            # Pass depends ONLY on network x cold_chain (the real confounder).
            passed = bool(rng.random() < _pass_prob(cfg, network, cold))

            # Noise columns — no causal link to `passed`. Source of the spurious flip.
            inspector_id = f"INS-{int(rng.integers(0, cfg.spurious.n_inspectors)):02d}"
            weekday_idx = int(rng.integers(0, cfg.spurious.noise_weekdays))
            weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][weekday_idx]

            # Stop 01 — measurement gap: some lots are never captured. Heavier rural.
            null_frac = (cfg.measurement.null_frac_coldchain if cold
                         else cfg.measurement.null_frac_nocold)
            captured = bool(rng.random() >= null_frac)

            dispatch = SEASON_START + timedelta(days=int(rng.integers(0, SEASON_DAYS)))

            if captured:
                weight_in = float(np.round(rng.normal(950, 120), 1))
                loss = float(np.clip(rng.normal(cfg.measurement.mean_loss_frac,
                                                cfg.measurement.loss_sd), 0.0, 0.85))
                weight_out = float(np.round(weight_in * (1 - loss), 1))
                captured_at: str | None = (
                    dispatch + timedelta(hours=int(rng.integers(6, 20)))
                ).isoformat(timespec="minutes")
                capture_method = "scanner" if cold else "manual_scale"
            else:
                weight_in = np.nan
                weight_out = np.nan
                captured_at = None
                capture_method = "broker_memory"  # the variable that doesn't exist

            rows.append({
                "lot_id": f"LOT-{lot_counter:05d}",
                "supplier_id": supplier_id,
                "network": network,
                "route_id": route_id,
                "cold_chain": cold,
                "inspector_id": inspector_id,
                "weekday": weekday,
                "dispatch_date": dispatch.date().isoformat(),
                "captured_at": captured_at,
                "capture_method": capture_method,
                "weight_in_kg": weight_in,
                "weight_out_kg": weight_out,
                "quality_pass": passed,
                # 1/0 mirror so Power BI can average it as a pass rate with one drag.
                "passed_flag": int(passed),
            })

    df = pd.DataFrame(rows)
    # Loss is only knowable where captured — the measurement gap made tangible.
    df["post_harvest_loss_frac"] = np.where(
        df.weight_in_kg.notna(),
        np.round((df.weight_in_kg - df.weight_out_kg) / df.weight_in_kg, 4),
        np.nan,
    )
    return df


# ---------------------------------------------------------------------------
# Stop 03 — deliveries (transit variance + tail)
# ---------------------------------------------------------------------------

def _draw_transit(cfg: Config, rng: np.random.Generator, modes) -> float:
    weights = np.array([m.weight for m in modes])
    weights = weights / weights.sum()
    m = modes[int(rng.choice(len(modes), p=weights))]
    days = rng.normal(m.mean_days, m.sd_days)
    return float(max(cfg.carriers.min_transit_days, days))


def generate_deliveries(cfg: Config, rng: np.random.Generator,
                        orders: pd.DataFrame) -> pd.DataFrame:
    c = cfg.carriers
    rows: list[dict[str, object]] = []
    for lot_id, dispatch_date in zip(orders.lot_id, orders.dispatch_date):
        carrier = "CAR-A" if rng.random() < 0.5 else "CAR-B"
        modes = c.carrier_A_modes if carrier == "CAR-A" else c.carrier_B_modes
        transit = round(_draw_transit(cfg, rng, modes), 2)
        on_time = transit <= c.ship_cutoff_day
        if on_time:
            value = float(np.round(max(0.0, 1.0 - c.mild_decay_per_day * transit), 4))
        else:
            value = 0.0  # missed the vessel — total loss, not a delay
        dispatch = datetime.fromisoformat(dispatch_date)
        rows.append({
            "delivery_id": f"DLV-{lot_id.split('-')[1]}",
            "lot_id": lot_id,
            "carrier_id": carrier,
            "dispatch_date": dispatch_date,
            "transit_days": transit,
            "arrival_date": (dispatch + timedelta(days=transit)).date().isoformat(),
            "ship_cutoff_day": c.ship_cutoff_day,
            "on_time": on_time,
            "missed_ship": not on_time,
            # 1/0 mirrors for one-drag averaging in Power BI.
            "on_time_flag": int(on_time),
            "missed_ship_flag": int(not on_time),
            "value_retained": value,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Stop 04 — bullwhip demand signal
# ---------------------------------------------------------------------------

def generate_demand_signal(cfg: Config, rng: np.random.Generator) -> pd.DataFrame:
    b = cfg.bullwhip
    weeks = np.arange(b.n_weeks)

    # True consumer demand: flat + tiny noise, with a real +5% step at bump_week.
    step = np.where(weeks >= b.bump_week, b.bump_frac, 0.0)
    consumer = b.base_demand * (1 + step) + rng.normal(0, b.demand_noise_sd, b.n_weeks)

    series: dict[str, np.ndarray] = {"consumer": consumer}
    downstream = consumer
    for tier in b.tiers[1:]:  # retailer, exporter, farm
        orders = _order_up_to(downstream, b.safety_factor[tier])
        series[tier] = orders
        downstream = orders

    # Long format for Power BI: one row per (week, tier).
    baseline = {t: float(np.mean(series[t][:b.bump_week])) for t in b.tiers}
    rows: list[dict[str, object]] = []
    for tier in b.tiers:
        for w in weeks:
            val = float(series[tier][w])
            rows.append({
                "week": int(w),
                "tier": tier,
                "tier_rank": b.tiers.index(tier),
                "orders_placed": round(val, 1),
                "true_consumer_demand": round(float(consumer[w]), 1),
                "pct_vs_baseline": round(val / baseline[tier] - 1, 4),
            })
    return pd.DataFrame(rows)


def _order_up_to(downstream: np.ndarray, safety: float) -> np.ndarray:
    """One echelon of a trend-chasing order policy with one week of lag.

    Each week the tier orders what it saw last week plus a safety-stock
    adjustment proportional to the observed week-over-week change. A demand step
    therefore produces a one-week order spike; stacked across echelons (with the
    multiplier rising upstream), the spike compounds into the bullwhip.
    """
    n = len(downstream)
    orders = np.zeros(n)
    for t in range(n):
        seen = downstream[t - 1] if t > 0 else downstream[0]        # one week lag
        prev = downstream[t - 2] if t > 1 else downstream[0]
        change = seen - prev
        orders[t] = max(0.0, seen + safety * change)
    return orders


# ---------------------------------------------------------------------------
# Verification / diagnostics
# ---------------------------------------------------------------------------

def _pass_rate(df: pd.DataFrame) -> float:
    return float(df.quality_pass.mean()) if len(df) else float("nan")


def check_simpson(orders: pd.DataFrame) -> dict[str, float]:
    a = orders[orders.network == "A"]
    b = orders[orders.network == "B"]
    return {
        "A_aggregate": _pass_rate(a),
        "B_aggregate": _pass_rate(b),
        "A_coldchain": _pass_rate(a[a.cold_chain]),
        "B_coldchain": _pass_rate(b[b.cold_chain]),
        "A_nocold": _pass_rate(a[~a.cold_chain]),
        "B_nocold": _pass_rate(b[~b.cold_chain]),
    }


def find_spurious_flip(orders: pd.DataFrame, min_cell: int) -> list[dict[str, object]]:
    """Inspectors where B's pass rate beats A's WITHOUT conditioning on cold_chain.

    A real fake-out: the aggregate says A>B, but this slice shows B>A for no
    causal reason. Returned cells are what the presenter can point at live.
    """
    hits: list[dict[str, object]] = []
    for ins, grp in orders.groupby("inspector_id"):
        a = grp[grp.network == "A"]
        b = grp[grp.network == "B"]
        if len(a) < min_cell or len(b) < min_cell:
            continue
        ra, rb = _pass_rate(a), _pass_rate(b)
        if rb > ra:  # spurious reversal of the aggregate
            hits.append({"inspector_id": ins, "A_rate": round(ra, 3),
                         "B_rate": round(rb, 3), "n_A": len(a), "n_B": len(b)})
    return hits


def check_carriers(deliveries: pd.DataFrame) -> pd.DataFrame:
    g = deliveries.groupby("carrier_id")
    return pd.DataFrame({
        "n": g.size(),
        "mean_days": g.transit_days.mean().round(2),
        "sd_days": g.transit_days.std().round(2),
        "pct_missed_ship": (g.missed_ship.mean() * 100).round(1),
        "mean_value_retained": g.value_retained.mean().round(3),
    })


def check_bullwhip(demand: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    g = demand.groupby("tier")
    peak = g.pct_vs_baseline.max().round(3)
    var = g.orders_placed.var().round(1)
    out = pd.DataFrame({"peak_pct_vs_baseline": peak, "order_variance": var})
    return out.reindex(cfg.bullwhip.tiers)


# ---------------------------------------------------------------------------
# Seed search (used once to lock CONFIG.seed)
# ---------------------------------------------------------------------------

def robustness_scan(cfg: Config, n: int = 3000) -> None:
    """Quantify the discipline claim across n seeds: the REAL cold-chain flip
    should survive reseeding while the SPURIOUS inspector flip stays rare and
    landless. Prints the sweep so any skeptic in the room can re-verify it.
    """
    routes = build_routes(cfg, np.random.default_rng(0))
    real_hold = 0
    spurious_any = 0
    inspectors: dict[str, int] = {}
    for seed in range(n):
        rng = np.random.default_rng(seed)
        _ = build_routes(cfg, rng)  # advance stream identically to build_all
        orders = generate_orders(cfg, rng, routes)
        s = check_simpson(orders)
        if (s["A_aggregate"] > s["B_aggregate"]
                and s["B_coldchain"] > s["A_coldchain"]
                and s["B_nocold"] > s["A_nocold"]):
            real_hold += 1
        hits = find_spurious_flip(orders, cfg.spurious.min_cell_for_demo)
        if hits:
            spurious_any += 1
            for h in hits:
                ins = str(h["inspector_id"])
                inspectors[ins] = inspectors.get(ins, 0) + 1
    print(f"Robustness sweep over {n} seeds:")
    print(f"  REAL cold-chain flip holds in BOTH strata: "
          f"{real_hold}/{n} = {real_hold / n:.1%}")
    print(f"  SPURIOUS inspector flip present at all:     "
          f"{spurious_any}/{n} = {spurious_any / n:.1%}")
    print(f"  when present, which inspector (no favourite = pure noise):")
    print(f"    {dict(sorted(inspectors.items()))}")


def find_seed(cfg: Config, n: int = 2000) -> None:
    routes_seed = np.random.default_rng(0)
    routes = build_routes(cfg, routes_seed)
    for seed in range(n):
        rng = np.random.default_rng(seed)
        _ = build_routes(cfg, rng)  # consume same stream shape as main
        orders = generate_orders(cfg, rng, routes)
        s = check_simpson(orders)
        real_ok = (s["A_aggregate"] > s["B_aggregate"]
                   and s["B_coldchain"] > s["A_coldchain"]
                   and s["B_nocold"] > s["A_nocold"])
        hits = find_spurious_flip(orders, cfg.spurious.min_cell_for_demo)
        if real_ok and len(hits) == 1:
            print(f"seed={seed}  real_flip=OK  spurious inspector={hits[0]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_all(cfg: Config) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(cfg.seed)
    routes = build_routes(cfg, rng)
    orders = generate_orders(cfg, rng, routes)
    deliveries = generate_deliveries(cfg, rng, orders)
    demand = generate_demand_signal(cfg, rng)
    return {
        "suppliers": build_suppliers(),
        "carriers": build_carriers(cfg),
        "routes": routes,
        "orders": orders,
        "deliveries": deliveries,
        "demand_signal": demand,
    }


def write_outputs(tables: dict[str, pd.DataFrame]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(DATA_DIR / f"{name}.csv", index=False)

    db_path = DATA_DIR / "one_crate.duckdb"
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    for name, df in tables.items():
        con.register("_tmp", df)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM _tmp")
        con.unregister("_tmp")
    con.close()


def print_diagnostics(cfg: Config, tables: dict[str, pd.DataFrame]) -> None:
    orders, deliveries, demand = tables["orders"], tables["deliveries"], tables["demand_signal"]

    print("\n" + "=" * 68)
    print(f"ONE CRATE — dataset built at seed {cfg.seed}")
    print("=" * 68)

    print("\nSTOP 01 · Measurement gap (lots never captured)")
    gap = orders.captured_at.isna().mean()
    gap_rural = orders[~orders.cold_chain].captured_at.isna().mean()
    gap_cold = orders[orders.cold_chain].captured_at.isna().mean()
    print(f"  overall null-capture: {gap:.1%}   rural: {gap_rural:.1%}   cold-chain: {gap_cold:.1%}")
    print(f"  loss knowable on only {orders.post_harvest_loss_frac.notna().mean():.1%} of lots; "
          f"mean measured loss {orders.post_harvest_loss_frac.mean():.1%}")

    print("\nSTOP 02 · Simpson's paradox — the REAL flip (keep it)")
    s = check_simpson(orders)
    print(f"  Aggregate:  A={s['A_aggregate']:.1%}  B={s['B_aggregate']:.1%}   "
          f"(=> naive: drop B)")
    print(f"  Cold-chain: A={s['A_coldchain']:.1%}  B={s['B_coldchain']:.1%}   "
          f"({'B>A OK' if s['B_coldchain'] > s['A_coldchain'] else 'FAIL'})")
    print(f"  No-cold:    A={s['A_nocold']:.1%}  B={s['B_nocold']:.1%}   "
          f"({'B>A OK' if s['B_nocold'] > s['A_nocold'] else 'FAIL'})")

    print("\nSTOP 02 · the SPURIOUS flip (discard it — unstable across seeds)")
    hits = find_spurious_flip(orders, cfg.spurious.min_cell_for_demo)
    if hits:
        for h in hits:
            print(f"  inspector {h['inspector_id']}: A={h['A_rate']:.1%} B={h['B_rate']:.1%} "
                  f"(n_A={h['n_A']}, n_B={h['n_B']})  <- looks real, isn't")
    else:
        print("  (none at this seed)")

    print("\nSTOP 03 · Variance & tail (mean inverts the right choice)")
    print(check_carriers(deliveries).to_string())

    print("\nSTOP 04 · Bullwhip (amplifies upstream)")
    print(check_bullwhip(demand, cfg).to_string())
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="One Crate synthetic dataset generator")
    ap.add_argument("--find-seed", action="store_true",
                    help="search for a seed carrying exactly one spurious flip")
    ap.add_argument("--robustness", action="store_true",
                    help="sweep seeds: how often the real flip holds vs the spurious one appears")
    args = ap.parse_args()

    if args.find_seed:
        find_seed(CONFIG)
        return
    if args.robustness:
        robustness_scan(CONFIG)
        return

    tables = build_all(CONFIG)
    write_outputs(tables)
    print_diagnostics(CONFIG, tables)
    print(f"Wrote {len(tables)} tables + one_crate.duckdb to {DATA_DIR}/")


if __name__ == "__main__":
    main()
