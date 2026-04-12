"""L2 extraction pipeline — structured paper summaries via Ollama.

Uses a local Ollama model (default: qwen2.5-coder:7b) to extract structured
L2 summaries for arXiv papers and persist them to the SQLite knowledge database.

Each summary contains: contribution, method, datasets, key_findings, limitations,
domain_tags, and related_methods.  Missing fields are filled with safe defaults by
:func:`_validate_summary` so DB inserts never fail due to absent keys.

The validated extraction prompt is from R-003 (agents/shared/findings.md).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from .schema import get_connection, init_database, json_dumps

# ---------------------------------------------------------------------------
# Prompt template (exact text from R-003)
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
You are a research assistant specializing in AI, machine learning, and computer science.
Your task is to extract a structured summary from an arXiv paper.

Read the title and abstract below, then output ONLY a single JSON object that matches
the schema exactly. Do NOT add any explanation, markdown, code fences, preamble, or
commentary. Output raw JSON only.

Schema:
{{
  "contribution": "<ONE sentence: the main contribution of this paper>",
  "method": "<The specific technique, architecture, or algorithm used — be precise,\
not generic (e.g. 'transformer encoder with cross-attention' not 'deep learning')>",
  "datasets": ["<dataset name>", "..."],
  "key_findings": [
    "<finding 1 — include numbers/metrics where available>",
    "<finding 2>",
    "<finding 3>"
  ],
  "limitations": "<Known constraints, scope limitations, or null if none stated>",
  "domain_tags": ["<2-4 specific tags, e.g. NLP, transformers, language_modeling>"],
  "related_methods": ["<name of related technique or paper>", "..."]
}}

Rules:
- "contribution" must be one sentence only.
- "method" must name the specific technique, not just "neural network" or "deep learning".
- "key_findings" must contain exactly 3 items; include numeric results if stated.
- "datasets" must be an empty list [] if no datasets are named in the abstract.
- "domain_tags" must contain 2 to 4 tags maximum.
- Output JSON only. No explanation. No markdown. No code fences.

Paper title: {title}

Abstract:
{abstract}

JSON:"""

_RETRY_PREFIX = "Return ONLY a JSON object, no other text:\n\n"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_prompt(title: str, abstract: str, *, retry: bool = False) -> str:
    """Build the extraction prompt for a single paper.

    Args:
        title: Paper title.
        abstract: Paper abstract text.
        retry: When ``True``, prepend an explicit JSON-only instruction.

    Returns:
        Formatted prompt string.
    """
    base = _PROMPT_TEMPLATE.format(title=title, abstract=abstract)
    if retry:
        return _RETRY_PREFIX + base
    return base


def _call_ollama(
    prompt: str,
    model: str,
    base_url: str,
    timeout: int,
) -> str:
    """Send a prompt to Ollama and return the raw response string.

    Args:
        prompt: Full prompt text.
        model: Ollama model identifier (e.g. ``"qwen2.5-coder:7b"``).
        base_url: Ollama server base URL.
        timeout: Request timeout in seconds.

    Returns:
        Raw text from the ``response`` field of the Ollama JSON reply.

    Raises:
        requests.HTTPError: On non-2xx HTTP status.
        requests.Timeout: If the request exceeds ``timeout`` seconds.
    """
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["response"]


def _validate_summary(summary: dict) -> dict:
    """Fill missing fields with defaults so DB insert never fails.

    Ensures all expected keys are present with the correct types.
    Does not validate *values* — that is left to downstream quality analysis.

    Args:
        summary: Parsed extraction dict, possibly incomplete.

    Returns:
        A copy of ``summary`` with all required fields present.
    """
    defaults: dict = {
        "contribution": "",
        "method": "",
        "datasets": [],
        "key_findings": [],
        "limitations": None,
        "domain_tags": [],
        "related_methods": [],
    }
    result = dict(defaults)
    result.update(summary)

    # Coerce list fields — model occasionally returns a string for these
    for list_field in ("datasets", "key_findings", "domain_tags", "related_methods"):
        val = result.get(list_field)
        if not isinstance(val, list):
            result[list_field] = [str(val)] if val else []

    # Coerce string fields
    for str_field in ("contribution", "method"):
        val = result.get(str_field)
        if not isinstance(val, str):
            result[str_field] = str(val) if val is not None else ""

    return result


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------


def extract_paper_summary(
    arxiv_id: str,
    title: str,
    abstract: str,
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    timeout: int = 90,
) -> dict | None:
    """Extract a structured L2 summary for one paper using Ollama.

    Sends the validated R-003 prompt to the local Ollama model.  On a
    ``json.JSONDecodeError``, retries once with an explicit JSON-only
    instruction prepended.  Returns ``None`` if both attempts fail.

    Args:
        arxiv_id: arXiv paper identifier (used only for logging).
        title: Paper title.
        abstract: Paper abstract.
        model: Ollama model identifier.
        ollama_base_url: Base URL for the Ollama HTTP server.
        timeout: Per-request timeout in seconds.

    Returns:
        Parsed and validated summary dict on success, or ``None`` on failure.
    """
    for attempt in range(2):
        retry = attempt > 0
        prompt = _build_prompt(title, abstract, retry=retry)
        if retry:
            print(
                f"[extract_l2] {arxiv_id}: retrying with explicit JSON instruction",
                file=sys.stderr,
            )
        try:
            raw = _call_ollama(prompt, model, ollama_base_url, timeout)
            parsed = json.loads(raw)
            return _validate_summary(parsed)
        except json.JSONDecodeError as exc:
            if attempt == 0:
                print(
                    f"[extract_l2] {arxiv_id}: JSON parse error on attempt 1 "
                    f"({exc}), retrying...",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[extract_l2] {arxiv_id}: JSON parse error on retry — "
                    f"skipping ({exc})",
                    file=sys.stderr,
                )
        except Exception as exc:
            print(
                f"[extract_l2] {arxiv_id}: unexpected error — {exc}",
                file=sys.stderr,
            )
            return None

    return None


# ---------------------------------------------------------------------------
# Batch extraction
# ---------------------------------------------------------------------------


def extract_batch(
    papers: pd.DataFrame,
    db_path: Path,
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    skip_existing: bool = True,
) -> dict[str, int]:
    """Extract L2 summaries for a batch of papers and persist to SQLite.

    For each paper in ``papers``:

    1. Optionally skips rows already in ``paper_summaries`` (resume support).
    2. Calls :func:`extract_paper_summary` to obtain a structured summary.
    3. Validates the result with :func:`_validate_summary`.
    4. Inserts the row into the ``paper_summaries`` table.
    5. Commits immediately after each insertion (Ollama is slow; commit often
       so partial progress is never lost on crash).

    Progress is printed to stderr as ``[extract_l2] N/M: <arxiv_id> — done``.

    Args:
        papers: DataFrame with at minimum columns ``arxiv_id``, ``title``,
            and ``abstract``.
        db_path: Path to the SQLite knowledge database.  Initialized
            (tables created) if it does not already exist.
        model: Ollama model identifier.
        ollama_base_url: Base URL for the Ollama HTTP server.
        skip_existing: When ``True``, papers already in ``paper_summaries``
            (matched by ``arxiv_id``) are skipped without re-extracting.

    Returns:
        A dict with keys ``"extracted"``, ``"skipped"``, and ``"errors"``
        reporting the outcome count for each paper.
    """
    db_path = Path(db_path)
    conn = init_database(db_path)

    counters: dict[str, int] = {"extracted": 0, "skipped": 0, "errors": 0}
    total = len(papers)

    # Pre-fetch existing arxiv_ids once (O(1) query, not N queries)
    existing: set[str] = set()
    if skip_existing:
        rows = conn.execute("SELECT arxiv_id FROM paper_summaries").fetchall()
        existing = {row[0] for row in rows}

    for i, row in enumerate(papers.itertuples(index=False), start=1):
        arxiv_id: str = str(row.arxiv_id)
        title: str = (
            str(row.title) if hasattr(row, "title") and pd.notna(row.title) else ""
        )
        abstract: str = str(row.abstract) if pd.notna(row.abstract) else ""

        if skip_existing and arxiv_id in existing:
            counters["skipped"] += 1
            continue

        t0 = time.monotonic()
        summary = extract_paper_summary(
            arxiv_id,
            title,
            abstract,
            model=model,
            ollama_base_url=ollama_base_url,
        )

        if summary is None:
            print(
                f"[extract_l2] WARNING: {arxiv_id} — extraction returned None, skipping",
                file=sys.stderr,
            )
            counters["errors"] += 1
            continue

        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO paper_summaries
                    (arxiv_id, title, contribution, method,
                     datasets, key_findings, limitations,
                     domain_tags, related_methods, extraction_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    arxiv_id,
                    title,
                    summary.get("contribution", ""),
                    summary.get("method", ""),
                    json_dumps(summary.get("datasets", [])),
                    json_dumps(summary.get("key_findings", [])),
                    summary.get("limitations"),
                    json_dumps(summary.get("domain_tags", [])),
                    json_dumps(summary.get("related_methods", [])),
                    model,
                ),
            )
            conn.commit()
            counters["extracted"] += 1

            elapsed = time.monotonic() - t0
            print(
                f"[extract_l2] {i}/{total}: {arxiv_id} — done ({elapsed:.1f}s)",
                file=sys.stderr,
            )

        except Exception as exc:
            print(
                f"[extract_l2] ERROR inserting {arxiv_id}: {exc}",
                file=sys.stderr,
            )
            counters["errors"] += 1

    conn.close()
    print(
        f"[extract_l2] Done. extracted={counters['extracted']}, "
        f"skipped={counters['skipped']}, errors={counters['errors']}",
        file=sys.stderr,
    )
    return counters
