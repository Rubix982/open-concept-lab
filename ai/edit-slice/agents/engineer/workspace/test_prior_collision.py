"""A fact whose answer is the template's prior cannot be scored. [T-100]

    .venv/bin/python agents/engineer/workspace/test_prior_collision.py

[E-045] scored 18 `int`-returning functions at zero possession while the model ranked
`int` first for 15 of them. Every one had `rank_prior == 1` — the subject-free prompt
already predicted `int`, so lift could not be positive whatever the model knew. The lift
control was working exactly as designed and simply cannot separate knowledge from prompt
prior for that answer.

These tests pin the distinction so a future change cannot quietly fold unscoreable items
back in with the not-held, which is what deflated [E-045]'s headline by five points before
anyone looked.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from possession import FilterConfig, FilterReport, ItemResult  # noqa: E402


def item(rank_subject: int, rank_prior: int, answer: str = "x") -> ItemResult:
    return ItemResult(case_id=f"{answer}-{rank_subject}-{rank_prior}", relation_id="r",
                      subject="s", true_answer=answer, rank_subject=rank_subject,
                      rank_prior=rank_prior, n_candidates=50)


def rep(*items: ItemResult) -> FilterReport:
    return FilterReport(config=FilterConfig(model="m", n_candidates=50),
                        results=list(items))


def test_collision_is_identified_even_when_ranked_first():
    """The [E-045] case: ranked first WITH the subject, and still unscoreable."""
    r = rep(item(1, 1))
    assert len(r.prior_collisions) == 1
    assert r.held_rate == 0.0, "lift is zero, so `held` must be false — unchanged"
    assert r.held_rate_scoreable == 0.0, "and there is nothing left to score"


def test_plain_rate_is_unchanged_by_the_new_properties():
    """Every past number used `held_rate`. It must mean exactly what it meant."""
    r = rep(item(1, 3), item(1, 4), item(1, 1), item(5, 3))
    assert r.held_rate == 0.5, "2 held of 4 items, collisions still in the denominator"
    assert abs(r.held_rate_scoreable - 2 / 3) < 1e-12, "2 held of 3 scoreable"


def test_the_two_rates_agree_when_nothing_collides():
    r = rep(item(1, 3), item(1, 4), item(5, 2))
    assert r.held_rate == r.held_rate_scoreable


def test_empty_report_is_safe():
    r = rep()
    assert r.prior_collisions == [] and r.held_rate_scoreable == 0.0


def test_prior_rate_and_collisions_count_the_same_thing():
    """`prior_rate` already existed and was never read as unscoreability. Same items."""
    r = rep(item(1, 1), item(1, 1), item(1, 3), item(4, 9))
    assert r.prior_rate == 0.5
    assert len(r.prior_collisions) == 2


def main() -> int:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = []
    for fn in fns:
        try:
            fn()
            print(f"  ok    {fn.__name__}", file=sys.stderr)
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}", file=sys.stderr)
            bad.append(fn.__name__)
    print(f"\n{'all pass' if not bad else str(len(bad)) + ' failed'}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
