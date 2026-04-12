"""Corpus quality filtering for L2 extraction.

Filters the raw arXiv DataFrame to a high-quality subset before running
Ollama extraction.  Thin abstracts and very recent preprints tend to produce
poor L2 summaries (empty key_findings, vague methods).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


def _normalise_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _year_from_arxiv_id(arxiv_id: str) -> int:
    """Extract submission year from arXiv ID.

    New-format IDs (e.g. ``2208.02389``) encode YYMM as the first four
    digits; year = 2000 + int(first_two_digits).
    Old-format IDs (e.g. ``math/0406594``) use YYMM after the slash.
    Returns 0 if parsing fails.
    """
    try:
        s = str(arxiv_id)
        if "/" in s:  # old format: field/YYMMNNNNN
            s = s.split("/")[1]
        return 2000 + int(s[:2])
    except (ValueError, IndexError):
        return 0


def filter_quality_papers(
    papers: pd.DataFrame,
    *,
    min_abstract_words: int = 80,
    year_min: int = 2018,
    year_max: int = 2024,
    max_papers: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Filter and sample papers for high-quality L2 extraction.

    Applies the following criteria in order:

    1. Abstract length >= ``min_abstract_words`` — rejects thin/empty abstracts
    2. Year in ``[year_min, year_max]`` — avoids too-recent/too-old papers
    3. Deduplicate by normalised title — removes versioned preprint duplicates
    4. Stratified sample of ``max_papers``, capped at 40% per category

    Args:
        papers: DataFrame with columns including ``abstract``, ``year``,
            ``title``, and ``primary_category``.
        min_abstract_words: Minimum word count threshold for abstracts.
        year_min: Earliest year to include (inclusive).
        year_max: Latest year to include (inclusive).
        max_papers: Maximum papers in the returned sample.
        seed: Random seed for reproducible sampling.

    Returns:
        Filtered and sampled DataFrame with reset index.
    """
    df = papers.copy()

    # Step 1 — abstract word count
    df["_abstract_words"] = df["abstract"].apply(
        lambda a: len(str(a).split()) if pd.notna(a) else 0
    )
    df = df[df["_abstract_words"] >= min_abstract_words]

    # Step 2 — year range derived from arxiv_id (the year column from update_date
    # is unreliable — it reflects the latest revision, not original submission)
    df["_submission_year"] = df["arxiv_id"].apply(_year_from_arxiv_id)
    df = df[(df["_submission_year"] >= year_min) & (df["_submission_year"] <= year_max)]
    df = df.drop(columns=["_submission_year"])

    # Step 3 — deduplicate by normalised title
    df["_norm_title"] = df["title"].apply(
        lambda t: _normalise_title(str(t)) if pd.notna(t) else ""
    )
    df = df.drop_duplicates(subset="_norm_title", keep="first")

    # Drop helper columns
    df = df.drop(columns=["_abstract_words", "_norm_title"])

    # Step 4 — stratified sampling with 40% category cap
    if len(df) <= max_papers:
        return df.reset_index(drop=True)

    cap = max(1, int(max_papers * 0.40))
    rng = np.random.default_rng(seed)

    sampled_parts: list[pd.DataFrame] = []
    for cat, group in df.groupby("primary_category"):
        n = min(len(group), cap)
        idx = rng.choice(len(group), size=n, replace=False)
        sampled_parts.append(group.iloc[idx])

    sampled = pd.concat(sampled_parts, ignore_index=True)

    # If stratified result is still over max_papers, trim randomly
    if len(sampled) > max_papers:
        idx = rng.choice(len(sampled), size=max_papers, replace=False)
        sampled = sampled.iloc[idx]

    return sampled.reset_index(drop=True)


def corpus_stats(papers: pd.DataFrame) -> dict:
    """Return summary statistics for a filtered corpus DataFrame.

    Args:
        papers: Filtered DataFrame (output of :func:`filter_quality_papers`).

    Returns:
        Dict with keys: ``total``, ``year_range``, ``top_categories``,
        ``interdisciplinary_pct``, ``avg_abstract_words``.
    """
    avg_words = float(
        papers["abstract"]
        .apply(lambda a: len(str(a).split()) if pd.notna(a) else 0)
        .astype(int)
        .mean()
    )

    top_cats = papers["primary_category"].value_counts().head(5).to_dict()

    inter_pct = (
        float(papers["is_interdisciplinary"].mean() * 100)
        if "is_interdisciplinary" in papers.columns
        else None
    )

    submission_years = papers["arxiv_id"].apply(_year_from_arxiv_id)
    return {
        "total": len(papers),
        "year_range": (int(submission_years.min()), int(submission_years.max())),
        "top_categories": top_cats,
        "interdisciplinary_pct": round(inter_pct, 1) if inter_pct is not None else None,
        "avg_abstract_words": round(avg_words, 1),
    }
