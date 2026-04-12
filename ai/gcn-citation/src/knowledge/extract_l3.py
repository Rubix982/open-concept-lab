"""L3 extraction pipeline — discrete claim nodes via Ollama.

Uses a local Ollama model (default: qwen2.5-coder:7b) to extract discrete,
atomic, falsifiable claims from L2 paper summaries and persist them to the
SQLite knowledge database.

Each claim is stored as a row in ``claims`` with a deterministic
``claim_id`` of the form ``{arxiv_id}_{index:02d}`` (e.g. ``2208.02389_00``).
One row per claim is also written to ``claim_sources`` to record which paper
supports the claim.

The validated extraction prompt is from R-005 (agents/shared/findings.md).
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

from .schema import get_connection, init_database

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_CLAIM_TYPES = frozenset(
    {"empirical", "theoretical", "architectural", "comparative", "observation"}
)

_VALID_DOMAINS = frozenset(
    {"NLP", "CV", "RL", "optimization", "theory", "graph_learning", "statistics"}
)

# Prefixes to strip from assertion text (case-insensitive match at start)
_ASSERTION_STRIP_PREFIXES = re.compile(
    r"^(this paper[,\s]+|we\s+|our\s+)", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Prompt template (exact text from R-005, extended per ticket spec)
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
You are extracting discrete scientific claims from an AI/ML paper.

Paper title: {title}
Abstract summary: {contribution}
Method used: {method}
Key findings: {findings}

Extract 1-{max_claims} discrete, atomic claims from this paper. Each claim must:
- Be self-contained (no "this paper", "we", "our" — name the method explicitly)
- Be falsifiable (another paper could contradict it)
- Be atomic (one assertion, not two bundled together)

Extract exactly {max_claims} claims if possible, fewer only if the paper has fewer distinct assertions.

Return ONLY a JSON array. Each object must have these exact keys:
claim_type (empirical|theoretical|architectural|comparative|observation),
assertion (one sentence naming the specific method),
method (specific technique e.g. "BERT", "ResNet-50", "Adam"),
domain (NLP|CV|RL|optimization|theory|graph_learning|statistics),
dataset (name or null), metric (name or null), value (string or null),
conditions (qualifying conditions or null)

JSON array only, no explanation:"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_prompt(
    title: str,
    contribution: str,
    method: str,
    key_findings: list[str],
    max_claims: int,
) -> str:
    """Build the L3 claim extraction prompt for one paper.

    Args:
        title: Paper title from L2 summary.
        contribution: One-sentence contribution from L2 summary.
        method: Specific technique from L2 summary.
        key_findings: List of key findings from L2 summary.
        max_claims: Maximum number of claims to request.

    Returns:
        Formatted prompt string.
    """
    findings_text = "; ".join(key_findings) if key_findings else "Not stated."
    return _PROMPT_TEMPLATE.format(
        title=title,
        contribution=contribution,
        method=method,
        findings=findings_text,
        max_claims=max_claims,
    )


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


def _parse_claims_response(raw: str) -> list[dict] | None:
    """Parse the Ollama response, handling both bare array and dict-wrapped forms.

    Known failure mode from R-005: model may return ``{"claims": [{...}]}``
    instead of the requested bare ``[{...}]`` array.

    Args:
        raw: Raw JSON string from Ollama.

    Returns:
        List of claim dicts, or ``None`` if parsing fails completely.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # Bare array — expected form
    if isinstance(parsed, list):
        return parsed

    # Dict-wrapped form: {"claims": [...]}
    if isinstance(parsed, dict):
        for key in ("claims", "results", "data"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        # Single claim wrapped as a dict — return as single-element list
        if "claim_type" in parsed or "assertion" in parsed:
            return [parsed]

    return None


def _validate_claim(claim: dict, arxiv_id: str, index: int) -> dict:
    """Validate and normalise a single raw claim dict from the model.

    Fills missing fields with safe defaults, clamps ``claim_type`` to a valid
    enum value, and strips first-person prefixes from ``assertion``.
    Assigns a deterministic ``claim_id`` in the form ``{arxiv_id}_{index:02d}``.

    Args:
        claim: Raw claim dict from the model, possibly incomplete.
        arxiv_id: arXiv paper identifier (used to build claim_id).
        index: Zero-based claim index for this paper.

    Returns:
        A validated, normalised claim dict ready for DB insertion.
    """
    result: dict = {
        "claim_id": f"{arxiv_id}_{index:02d}",
        "claim_type": "empirical",
        "assertion": "",
        "domain": None,
        "method": None,
        "dataset": None,
        "metric": None,
        "value": None,
        "conditions": None,
    }

    # claim_type: clamp to valid enum; default to "empirical"
    raw_type = claim.get("claim_type", "")
    if isinstance(raw_type, str) and raw_type.lower() in _VALID_CLAIM_TYPES:
        result["claim_type"] = raw_type.lower()
    else:
        result["claim_type"] = "empirical"

    # assertion: strip first-person prefixes; coerce to str
    assertion = claim.get("assertion", "")
    if not isinstance(assertion, str):
        assertion = str(assertion) if assertion is not None else ""
    assertion = _ASSERTION_STRIP_PREFIXES.sub("", assertion).strip()
    result["assertion"] = assertion

    # domain: keep if valid, else None
    domain = claim.get("domain")
    if isinstance(domain, str) and domain in _VALID_DOMAINS:
        result["domain"] = domain
    elif isinstance(domain, str) and domain:
        result["domain"] = domain  # keep unknown domains (not schema-constrained)

    # Scalar optional fields
    for field in ("method", "dataset", "metric", "value", "conditions"):
        val = claim.get(field)
        if val is not None and not isinstance(val, str):
            val = str(val)
        result[field] = (
            val if (val and val.lower() not in ("null", "none", "")) else None
        )

    return result


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------


def extract_claims_for_paper(
    arxiv_id: str,
    title: str,
    contribution: str,
    method: str,
    key_findings: list[str],
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    timeout: int = 120,
    max_claims: int = 3,
) -> list[dict] | None:
    """Extract 1-max_claims claim dicts for one paper.

    Sends the validated R-005 prompt to the local Ollama model. Handles both
    bare array ``[{...}]`` and dict-wrapped ``{"claims": [{...}]}`` responses.
    On parse failure, retries once with an explicit JSON-array instruction
    prepended. Returns ``None`` if both attempts fail.

    Args:
        arxiv_id: arXiv paper identifier (used for logging and claim_id generation).
        title: Paper title from L2 summary.
        contribution: One-sentence contribution from L2 summary.
        method: Specific technique from L2 summary.
        key_findings: List of key findings from L2 summary.
        model: Ollama model identifier.
        ollama_base_url: Base URL for the Ollama HTTP server.
        timeout: Per-request timeout in seconds.
        max_claims: Maximum number of claims to extract per paper.

    Returns:
        List of validated claim dicts on success, or ``None`` on failure.
        Each dict has keys: claim_id, claim_type, assertion, domain, method,
        dataset, metric, value, conditions.
    """
    prompt = _build_prompt(title, contribution, method, key_findings, max_claims)

    for attempt in range(2):
        current_prompt = prompt
        if attempt > 0:
            current_prompt = (
                "Return ONLY a JSON array of claim objects, no other text:\n\n" + prompt
            )
            print(
                f"[extract_l3] {arxiv_id}: retrying with explicit JSON-array instruction",
                file=sys.stderr,
            )

        try:
            raw = _call_ollama(current_prompt, model, ollama_base_url, timeout)
            claims_raw = _parse_claims_response(raw)

            if claims_raw is None:
                if attempt == 0:
                    print(
                        f"[extract_l3] {arxiv_id}: could not parse claims on attempt 1, retrying...",
                        file=sys.stderr,
                    )
                    continue
                else:
                    print(
                        f"[extract_l3] {arxiv_id}: could not parse claims on retry — skipping",
                        file=sys.stderr,
                    )
                    return None

            if not isinstance(claims_raw, list) or len(claims_raw) == 0:
                print(
                    f"[extract_l3] {arxiv_id}: empty claims list returned — skipping",
                    file=sys.stderr,
                )
                return None

            # Validate and normalise each claim
            validated: list[dict] = []
            for i, raw_claim in enumerate(claims_raw[:max_claims]):
                if not isinstance(raw_claim, dict):
                    print(
                        f"[extract_l3] {arxiv_id}: claim {i} is not a dict, skipping it",
                        file=sys.stderr,
                    )
                    continue
                validated.append(_validate_claim(raw_claim, arxiv_id, i))

            # Drop claims with empty assertions
            validated = [c for c in validated if c["assertion"]]

            if not validated:
                print(
                    f"[extract_l3] {arxiv_id}: no valid assertions after validation — skipping",
                    file=sys.stderr,
                )
                return None

            return validated

        except json.JSONDecodeError as exc:
            if attempt == 0:
                print(
                    f"[extract_l3] {arxiv_id}: JSON decode error on attempt 1 ({exc}), retrying...",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[extract_l3] {arxiv_id}: JSON decode error on retry — skipping ({exc})",
                    file=sys.stderr,
                )

        except Exception as exc:
            print(
                f"[extract_l3] {arxiv_id}: unexpected error — {exc}",
                file=sys.stderr,
            )
            return None

    return None


# ---------------------------------------------------------------------------
# Batch extraction
# ---------------------------------------------------------------------------


def extract_claims_batch(
    db_path: Path,
    *,
    model: str = "qwen2.5-coder:7b",
    ollama_base_url: str = "http://localhost:11434",
    skip_existing: bool = True,
    limit: int | None = None,
) -> dict[str, int]:
    """Extract claims for all papers in paper_summaries.

    For each paper in ``paper_summaries``:

    1. Optionally skips papers that already have claims (resume support).
    2. Calls :func:`extract_claims_for_paper` with the paper's L2 fields.
    3. Inserts each validated claim into the ``claims`` table.
    4. Inserts one row per claim into ``claim_sources``.
    5. Commits immediately after each paper (partial progress is never lost).

    Progress is logged to stderr as
    ``[extract_l3] N/M: <arxiv_id> — K claims``.

    Args:
        db_path: Path to the SQLite knowledge database. Initialised (tables
            created) if it does not already exist.
        model: Ollama model identifier.
        ollama_base_url: Base URL for the Ollama HTTP server.
        skip_existing: When ``True``, papers that already have at least one
            claim in the ``claims`` table are skipped without re-extracting.
        limit: If set, process at most ``limit`` papers (for staged rollout).

    Returns:
        A dict with keys ``"papers_processed"``, ``"claims_extracted"``,
        and ``"errors"`` reporting outcome counts.
    """
    db_path = Path(db_path)
    conn = init_database(db_path)

    counters: dict[str, int] = {
        "papers_processed": 0,
        "claims_extracted": 0,
        "errors": 0,
    }

    # Load all papers from paper_summaries
    rows = conn.execute(
        """
        SELECT arxiv_id, title, contribution, method, key_findings
        FROM paper_summaries
        ORDER BY arxiv_id
        """
    ).fetchall()

    if limit is not None:
        rows = rows[:limit]

    total = len(rows)

    # Pre-fetch arxiv_ids that already have claims (to avoid N queries)
    existing_arxiv_ids: set[str] = set()
    if skip_existing:
        existing_rows = conn.execute(
            "SELECT DISTINCT substr(claim_id, 1, length(claim_id) - 3) FROM claims"
        ).fetchall()
        # Build set of arxiv_ids from claim_ids: "2208.02389_00" → "2208.02389"
        # More reliable: query directly with prefix pattern via LIKE or substr approach
        # Use a more direct method: extract arxiv_id as everything before the last '_NN'
        all_claim_ids = conn.execute("SELECT claim_id FROM claims").fetchall()
        for (cid,) in all_claim_ids:
            # claim_id format: "{arxiv_id}_{NN}" where NN is 2 digits
            if len(cid) > 3 and cid[-3] == "_" and cid[-2:].isdigit():
                existing_arxiv_ids.add(cid[:-3])

    for seq, row in enumerate(rows, start=1):
        arxiv_id = str(row["arxiv_id"])
        title = str(row["title"] or "")
        contribution = str(row["contribution"] or "")
        method = str(row["method"] or "")

        # Deserialise key_findings JSON
        key_findings_raw = row["key_findings"]
        try:
            key_findings = json.loads(key_findings_raw) if key_findings_raw else []
            if not isinstance(key_findings, list):
                key_findings = [str(key_findings)]
        except (json.JSONDecodeError, TypeError):
            key_findings = []

        if skip_existing and arxiv_id in existing_arxiv_ids:
            continue

        t0 = time.monotonic()
        claims = extract_claims_for_paper(
            arxiv_id,
            title,
            contribution,
            method,
            key_findings,
            model=model,
            ollama_base_url=ollama_base_url,
        )

        if claims is None:
            print(
                f"[extract_l3] WARNING: {arxiv_id} — extraction returned None, skipping",
                file=sys.stderr,
            )
            counters["errors"] += 1
            continue

        try:
            for claim in claims:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO claims
                        (claim_id, claim_type, assertion, domain, method,
                         dataset, metric, value, conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim["claim_id"],
                        claim["claim_type"],
                        claim["assertion"],
                        claim["domain"],
                        claim["method"],
                        claim["dataset"],
                        claim["metric"],
                        claim["value"],
                        claim["conditions"],
                    ),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO claim_sources
                        (claim_id, arxiv_id)
                    VALUES (?, ?)
                    """,
                    (claim["claim_id"], arxiv_id),
                )

            conn.commit()
            counters["papers_processed"] += 1
            counters["claims_extracted"] += len(claims)

            elapsed = time.monotonic() - t0
            print(
                f"[extract_l3] {seq}/{total}: {arxiv_id} — {len(claims)} claims ({elapsed:.1f}s)",
                file=sys.stderr,
            )

        except Exception as exc:
            print(
                f"[extract_l3] ERROR inserting claims for {arxiv_id}: {exc}",
                file=sys.stderr,
            )
            counters["errors"] += 1

    conn.close()
    print(
        f"[extract_l3] Done. papers_processed={counters['papers_processed']}, "
        f"claims_extracted={counters['claims_extracted']}, "
        f"errors={counters['errors']}",
        file=sys.stderr,
    )
    return counters
