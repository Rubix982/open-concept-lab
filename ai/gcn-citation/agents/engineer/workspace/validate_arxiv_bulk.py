"""Validation script for pipeline/arxiv_bulk.py.

Run from the repo root:
    python agents/engineer/workspace/validate_arxiv_bulk.py
"""

from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

# Make sure the src package is importable when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from gcn_citation.pipeline.arxiv_bulk import (  # noqa: E402
    ArxivPaper,
    load_papers_to_dataframe,
    stream_arxiv_metadata,
)

FIXTURE = Path(__file__).parent / "test_arxiv_sample.jsonl"
TARGET_CATEGORIES = ["cs.LG", "cs.CV", "cs.CL", "cs.AI"]

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    _results.append((name, condition, detail))
    marker = "✓" if condition else "✗"
    print(f"  [{marker}] {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Section 1: stream_arxiv_metadata()
# ---------------------------------------------------------------------------

print("\n=== Section 1: stream_arxiv_metadata() ===\n")

try:
    # 1a. FileNotFoundError on missing file
    try:
        list(stream_arxiv_metadata(Path("/nonexistent/path.jsonl")))
        check("FileNotFoundError raised for missing file", False, "no exception raised")
    except FileNotFoundError:
        check("FileNotFoundError raised for missing file", True)

    # 1b. No filter — all 10 lines should be yielded
    all_papers = list(stream_arxiv_metadata(FIXTURE))
    check(
        "No filter yields all 10 papers",
        len(all_papers) == 10,
        f"got {len(all_papers)}",
    )

    # 1c. Category filter — fixture has 8 papers in target categories
    # (astro-ph and math.AT only papers should be excluded; q-bio/cs.NI crosses into cs.NI
    #  but cs.NI is not in target — however q-bio has cs.NI too; let's count manually)
    # Papers in fixture with at least one of cs.LG, cs.CV, cs.CL, cs.AI:
    #   1706.03762 cs.CL cs.LG  ✓
    #   2006.11239 cs.LG cs.CV stat.ML  ✓
    #   math/0406594 math.AT  ✗
    #   1810.04805 cs.CL  ✓
    #   astro-ph/0001001 astro-ph  ✗
    #   2103.00020 cs.CV cs.LG  ✓
    #   1512.03385 cs.CV  ✓
    #   2005.14165 cs.CL cs.LG cs.AI  ✓
    #   q-bio/0510030 q-bio.MN cs.NI  ✗ (cs.NI not in target)
    #   1301.3666 cs.CL  ✓
    expected_after_filter = 7  # 10 - math.AT - astro-ph - q-bio = 7
    filtered = list(stream_arxiv_metadata(FIXTURE, categories=TARGET_CATEGORIES))
    check(
        "Category filter yields correct count",
        len(filtered) == expected_after_filter,
        f"expected {expected_after_filter}, got {len(filtered)}",
    )

    # 1d. max_papers limit
    limited = list(
        stream_arxiv_metadata(FIXTURE, categories=TARGET_CATEGORIES, max_papers=3)
    )
    check("max_papers limit respected", len(limited) == 3, f"got {len(limited)}")

    # 1e. is_interdisciplinary flag
    by_id = {p.arxiv_id: p for p in all_papers}
    single_cat = by_id.get("1810.04805")  # categories: cs.CL only
    multi_cat = by_id.get("2006.11239")  # categories: cs.LG cs.CV stat.ML
    check(
        "Single-category paper: is_interdisciplinary=False",
        single_cat is not None and not single_cat.is_interdisciplinary,
        f"got {single_cat.is_interdisciplinary if single_cat else 'NOT FOUND'}",
    )
    check(
        "Multi-category paper: is_interdisciplinary=True",
        multi_cat is not None and multi_cat.is_interdisciplinary,
        f"got {multi_cat.is_interdisciplinary if multi_cat else 'NOT FOUND'}",
    )

    # 1f. categories is a list, not a string
    check(
        "categories field is a Python list",
        multi_cat is not None and isinstance(multi_cat.categories, list),
        f"type={type(multi_cat.categories).__name__ if multi_cat else 'N/A'}",
    )

    # 1g. Old-format ID handled (math/0406594)
    old_fmt = by_id.get("math/0406594")
    check(
        "Old-format arXiv ID preserved correctly",
        old_fmt is not None and old_fmt.arxiv_id == "math/0406594",
        f"got {old_fmt.arxiv_id if old_fmt else 'NOT FOUND'}",
    )

    # 1h. Old-format ID: year extracted from update_date (2004-07-01)
    check(
        "Old-format ID: year from update_date",
        old_fmt is not None and old_fmt.year == 2004 and old_fmt.month == 7,
        f"got year={old_fmt.year if old_fmt else '?'}, month={old_fmt.month if old_fmt else '?'}",
    )

    # 1i. New-format ID: year from update_date
    new_fmt = by_id.get("1706.03762")
    check(
        "New-format ID: year from update_date (2017)",
        new_fmt is not None and new_fmt.year == 2017 and new_fmt.month == 12,
        f"got year={new_fmt.year if new_fmt else '?'}, month={new_fmt.month if new_fmt else '?'}",
    )

    # 1j. Paper with empty abstract — should be empty string, not None
    bert = by_id.get("1810.04805")
    check(
        "Missing abstract produces empty string, not None",
        bert is not None and bert.abstract == "" and bert.abstract is not None,
        f"got abstract={repr(bert.abstract) if bert else 'NOT FOUND'}",
    )

    # 1k. start_year filter — only papers from 2017+ should appear
    recent = list(stream_arxiv_metadata(FIXTURE, start_year=2017))
    recent_years = [p.year for p in recent]
    check(
        "start_year filter excludes older papers",
        all(y == 0 or y >= 2017 for y in recent_years),
        f"years present: {sorted(set(recent_years))}",
    )
    # papers with year < 2017 in fixture: math/0406594(2004), astro-ph/0001001(2000),
    #   q-bio/0510030(2005), 1301.3666(2013), 1512.03385(2015), 1810.04805(2018 - update_date 2018-05-24)
    # So only 4 papers from 2017+: 1706.03762(2017), 2006.11239(2020), 2103.00020(2021), 2005.14165(2020)
    # Papers with year >= 2017 in fixture:
    #   1706.03762 (update_date 2017-12-05 → year=2017) ✓
    #   2006.11239 (update_date 2020-12-16 → year=2020) ✓
    #   1810.04805 (update_date 2018-05-24 → year=2018) ✓
    #   2103.00020 (update_date 2021-02-26 → year=2021) ✓
    #   2005.14165 (update_date 2020-07-22 → year=2020) ✓
    # Total: 5 papers
    check(
        "start_year=2017 yields papers from 2017+",
        len(recent) == 5,
        f"got {len(recent)} papers",
    )

except Exception:  # noqa: BLE001
    print("UNEXPECTED ERROR in Section 1:")
    traceback.print_exc()
    _results.append(("Section 1 completed without crash", False, "exception raised"))

# ---------------------------------------------------------------------------
# Section 2: load_papers_to_dataframe()
# ---------------------------------------------------------------------------

print("\n=== Section 2: load_papers_to_dataframe() ===\n")

try:
    import pandas as pd  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        # Each call gets its own fixture copy so checkpoints don't cross-contaminate.
        # The checkpoint path is derived from the snapshot path, so separate copies
        # guarantee separate checkpoints — matching production usage where each run
        # targets a single snapshot file with a single filter configuration.
        import shutil  # noqa: PLC0415

        def fresh_fixture(name: str) -> Path:
            p = Path(tmpdir) / name
            shutil.copy(FIXTURE, p)
            return p

        # 2a. Basic call — all papers, no filter
        fix_all = fresh_fixture("fixture_all.jsonl")
        df_all = load_papers_to_dataframe(fix_all)
        expected_cols = {
            "arxiv_id",
            "title",
            "abstract",
            "categories",
            "primary_category",
            "is_interdisciplinary",
            "year",
            "month",
        }
        check(
            "DataFrame has expected columns",
            set(df_all.columns) >= expected_cols,
            f"columns: {list(df_all.columns)}",
        )
        check(
            "DataFrame has 10 rows (no filter)",
            len(df_all) == 10,
            f"got {len(df_all)}",
        )

        # 2b. Category filter — separate fixture copy so checkpoint doesn't bleed
        fix_filt = fresh_fixture("fixture_filt.jsonl")
        df_filt = load_papers_to_dataframe(fix_filt, categories=TARGET_CATEGORIES)
        check(
            "DataFrame with category filter has 7 rows",
            len(df_filt) == 7,
            f"got {len(df_filt)}",
        )

        # 2c. max_papers limit — separate fixture copy
        fix_lim = fresh_fixture("fixture_lim.jsonl")
        df_lim = load_papers_to_dataframe(
            fix_lim, categories=TARGET_CATEGORIES, max_papers=4
        )
        check(
            "max_papers=4 yields DataFrame with 4 rows",
            len(df_lim) == 4,
            f"got {len(df_lim)}",
        )

        # 2d. categories column is list type (not string)
        sample_cats = df_all["categories"].iloc[0]
        check(
            "DataFrame categories column contains lists",
            isinstance(sample_cats, list),
            f"type={type(sample_cats).__name__}",
        )

        # 2e. is_interdisciplinary is boolean
        check(
            "is_interdisciplinary column is bool dtype",
            df_all["is_interdisciplinary"].dtype == bool
            or str(df_all["is_interdisciplinary"].dtype) in ("bool", "boolean"),
            f"dtype={df_all['is_interdisciplinary'].dtype}",
        )

        # 2f. Checkpoint file created (alongside fix_all)
        checkpoint_path = fix_all.with_suffix(".checkpoint.parquet")
        check(
            "Checkpoint .parquet file created",
            checkpoint_path.exists(),
            f"path={checkpoint_path}",
        )

        # 2g. Checkpoint resume: load checkpoint, verify count matches
        df_checkpoint = pd.read_parquet(checkpoint_path)
        check(
            "Checkpoint file row count matches returned DataFrame",
            len(df_checkpoint) == len(df_all),
            f"checkpoint={len(df_checkpoint)}, df={len(df_all)}",
        )

        # 2h. Resume: calling again reads checkpoint without re-streaming
        #     We test by checking that the returned df has same rows (idempotent)
        df_resume = load_papers_to_dataframe(fix_all)
        check(
            "Resume (second call) returns same row count",
            len(df_resume) == len(df_all),
            f"got {len(df_resume)}",
        )

except ImportError:
    check("pandas available", False, "pandas not installed — skipping Section 2")
except Exception:  # noqa: BLE001
    print("UNEXPECTED ERROR in Section 2:")
    traceback.print_exc()
    _results.append(("Section 2 completed without crash", False, "exception raised"))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Summary ===\n")
passes = sum(1 for _, ok, _ in _results if ok)
failures = sum(1 for _, ok, _ in _results if not ok)
for name, ok, detail in _results:
    marker = "PASS" if ok else "FAIL"
    print(f"  [{marker}] {name}" + (f" — {detail}" if detail else ""))

print(f"\n{passes}/{passes + failures} checks passed.")
if failures:
    print("OVERALL: FAIL")
    sys.exit(1)
else:
    print("OVERALL: PASS")
