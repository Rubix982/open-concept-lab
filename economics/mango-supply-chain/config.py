"""
One Crate — synthetic dataset configuration.

Every engineered statistical effect the talk relies on is a knob in this file.
Change a number here, re-run `generate.py`, and the reversal in the room moves
with it. Nothing downstream hard-codes an effect size; they all read from CONFIG.

The four effects, and the config block that drives each:

    Stop 01 · Measurement gap   -> MEASUREMENT
    Stop 02 · Simpson's paradox -> SIMPSON  (real flip) + SPURIOUS (noise flip)
    Stop 03 · Variance / tail   -> CARRIERS
    Stop 04 · Bullwhip          -> BULLWHIP

Read `README.md` for how each block maps to a single Power BI slicer move.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Global
# ---------------------------------------------------------------------------

# The seed is not decorative. It is *locked* because Stop 02 ships a spurious
# reversal that must be present in the delivered CSVs but must also visibly
# evaporate when the seed changes. This exact value was chosen by the seed
# search in generate.py (see verify_spurious_flip) so that one inspector shows
# a fake B>A reversal at ship time. Change it and the fake flip moves or dies —
# which is the whole point of the discipline lesson.
SEED: int = 1538

N_LOTS_PER_NETWORK: int = 1000  # crates inspected per supplier network (A, B)


# ---------------------------------------------------------------------------
# Stop 02 — Simpson's paradox (the REAL, causal, keep-it flip)
# ---------------------------------------------------------------------------
# cold_chain is a genuine confounder: it drives BOTH which network gets the
# route AND the pass rate. Aggregate says A(≈90%) > B(≈76%); split by cold_chain
# and B beats A in *both* strata. The averages below are engineered so the
# marginals land on the numbers printed in one-crate.html.
#
#   A aggregate = 0.865*0.945 + 0.135*0.61 = 0.900
#   B aggregate = 0.12*0.99   + 0.88*0.73   = 0.761
# Both strata: B > A   (cold 0.99>0.945,  no-cold 0.73>0.61)
#
# The cold-chain margin is intentionally the tight one (A's cold rate is pinned
# high just to lift its aggregate to 90%, leaving little headroom below B). It
# survives only because N is large; the no-cold margin, where most of B's data
# lives, is comfortably wide.

@dataclass(frozen=True)
class SimpsonConfig:
    # P(pass | network, cold_chain)
    pass_A_coldchain: float = 0.945
    pass_A_nocold: float = 0.61
    pass_B_coldchain: float = 0.99
    pass_B_nocold: float = 0.73

    # P(lot runs on a cold-chain route | network)  — the terrain each network serves.
    # A works the formal cold-chain corridors; B serves the hard rural routes.
    frac_coldchain_A: float = 0.865
    frac_coldchain_B: float = 0.12


# ---------------------------------------------------------------------------
# Stop 02 — the SPURIOUS flip (the discard-it slice)
# ---------------------------------------------------------------------------
# inspector_id and weekday have NO causal effect on pass rate — every lot's
# pass is drawn only from the SimpsonConfig probabilities above. But with the
# locked SEED, sampling noise makes one inspector's cell show a fake B>A
# reversal *without* conditioning on cold_chain. It looks exactly like a real
# confounder on screen and must be thrown away. Reseed -> it wanders off.

@dataclass(frozen=True)
class SpuriousConfig:
    n_inspectors: int = 8            # smaller cells -> noise flips more easily
    min_cell_for_demo: int = 25      # both A and B cells must clear this to be presentable
    noise_weekdays: int = 6          # Mon–Sat mandi operating days


# ---------------------------------------------------------------------------
# Stop 01 — Measurement gap
# ---------------------------------------------------------------------------
# "The variable was never recorded." A fraction of lots have NULL capture
# fields (no scanner weight, no timestamp). The gap is heavier on rural
# no-cold-chain routes — informal, paper-challan territory — so the missingness
# itself is structured, not uniform.

@dataclass(frozen=True)
class MeasurementConfig:
    null_frac_nocold: float = 0.45   # rural routes: nearly half never weighed
    null_frac_coldchain: float = 0.10
    # When a lot IS weighed, post-harvest loss = (weight_in - weight_out)/weight_in.
    mean_loss_frac: float = 0.31     # matches the >30% headline
    loss_sd: float = 0.06


# ---------------------------------------------------------------------------
# Stop 03 — Variance & tail risk (carriers)
# ---------------------------------------------------------------------------
# Carrier A: fast on average (≈10 days) but a fat tail — a third of the time it
# strands the crate past the export ship cutoff = TOTAL loss. Modeled as a
# mixture of a fast mode and a "stranded" mode.
# Carrier B: slow (≈14) but tight (±1); reliably makes the ship.
#
# value_retained: on-time crates decay mildly with days; late crates miss the
# ship entirely -> value 0. So the mean transit ordering (A<B) inverts the
# correct decision once the tail and the deadline are priced in.

@dataclass(frozen=True)
class CarrierMode:
    weight: float
    mean_days: float
    sd_days: float


@dataclass(frozen=True)
class CarriersConfig:
    ship_cutoff_day: int = 16        # crate must arrive by this day or it misses the vessel
    mild_decay_per_day: float = 0.015  # value lost per day even when on time
    min_transit_days: float = 3.0

    # Carrier A — mixture: mostly fast, sometimes stranded. Tuned to mean≈10, sd≈8,
    # ~30% of runs past the cutoff (the fat tail = total-loss events).
    carrier_A_modes: tuple[CarrierMode, ...] = (
        CarrierMode(weight=0.60, mean_days=5.0, sd_days=1.2),
        CarrierMode(weight=0.40, mean_days=19.0, sd_days=6.0),
    )
    # Carrier B — single tight mode.
    carrier_B_modes: tuple[CarrierMode, ...] = (
        CarrierMode(weight=1.0, mean_days=14.0, sd_days=1.0),
    )


# ---------------------------------------------------------------------------
# Stop 04 — Bullwhip effect
# ---------------------------------------------------------------------------
# A small, real +5% consumer demand bump amplifies up the tiers via order-up-to
# policies with per-tier safety stock and one week of lag, so by the farm the
# order swing is ≈+40%. Variance grows monotonically upstream.

@dataclass(frozen=True)
class BullwhipConfig:
    n_weeks: int = 52
    tiers: tuple[str, ...] = ("consumer", "retailer", "exporter", "farm")
    base_demand: float = 1000.0
    demand_noise_sd: float = 6.0      # small week-to-week wobble in true demand
    bump_week: int = 26               # week the real +5% step begins
    bump_frac: float = 0.05           # the real signal: +5%
    # Each tier orders what it saw (lagged one week) PLUS a safety-stock
    # adjustment proportional to the observed week-over-week *change* in demand
    # (trend chasing). The multiplier rises upstream, so the panic-order spike
    # compounds tier over tier: a +5% consumer step -> ≈+40% at the farm.
    safety_factor: dict[str, float] = field(default_factory=lambda: {
        "retailer": 0.72,
        "exporter": 0.92,
        "farm": 1.12,
    })


# ---------------------------------------------------------------------------
# Route dimension
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoutesConfig:
    n_coldchain_routes: int = 10
    n_nocold_routes: int = 10


# ---------------------------------------------------------------------------
# Assembled config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    seed: int = SEED
    n_lots_per_network: int = N_LOTS_PER_NETWORK
    simpson: SimpsonConfig = field(default_factory=SimpsonConfig)
    spurious: SpuriousConfig = field(default_factory=SpuriousConfig)
    measurement: MeasurementConfig = field(default_factory=MeasurementConfig)
    carriers: CarriersConfig = field(default_factory=CarriersConfig)
    bullwhip: BullwhipConfig = field(default_factory=BullwhipConfig)
    routes: RoutesConfig = field(default_factory=RoutesConfig)


CONFIG = Config()
