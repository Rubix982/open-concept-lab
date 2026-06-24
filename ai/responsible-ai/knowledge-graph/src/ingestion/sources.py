"""Open paper sources.

Primary: OpenAlex (https://openalex.org) — fully open, no API key, rich metadata,
abstracts stored as an inverted index we reconstruct. We use the polite pool by
sending a `mailto` parameter.

Raw API responses are cached under data/raw/ keyed by a hash of the request, so
re-runs do not re-hit the network.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, cast
from dotenv import load_dotenv, dotenv_values
import requests

from .models import PaperMeta

load_dotenv()

OPENALEX_BASE = "https://api.openalex.org/works"
# Polite-pool contact (OpenAlex asks for an email; gives faster, more reliable service).
MAILTO = dotenv_values(".env").get("OPENALEX_MAILTO", "")
USER_AGENT = f"claim-knowledge-graph/0.1 (mailto:{MAILTO})"

_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    return _RAW_DIR / f"openalex_{digest}.json"


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}. Rebuild the linear text."""
    if not inverted_index:
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            positioned.append((pos, word))
    if not positioned:
        return None
    positioned.sort(key=lambda p: p[0])
    return " ".join(word for _, word in positioned)


def _parse_work(work: dict[str, Any]) -> tuple[PaperMeta, str | None]:
    """Map one OpenAlex work record to (PaperMeta, abstract_text)."""
    oa_id: str = work.get("id", "")  # e.g. "https://openalex.org/W2741809807"
    short_id = oa_id.rsplit("/", 1)[-1] if oa_id else "unknown"

    authors: list[str] = []
    for authorship in work.get("authorships", []):
        author_obj = authorship.get("author")
        if isinstance(author_obj, dict):
            author_dict = cast(dict[str, Any], author_obj)
            name_obj = author_dict.get("display_name")
            if isinstance(name_obj, str) and name_obj:
                authors.append(name_obj)

    venue: str | None = None
    primary: object = work.get("primary_location") or {}
    if isinstance(primary, dict):
        primary = cast(dict[str, Any], primary)
        src: object = primary.get("source") or {}
        if isinstance(src, dict) and src:
            src = cast(dict[str, Any], src)
            venue = src.get("display_name")

    landing_page_url: str | None = None
    if isinstance(primary, dict):
        cast_primary = cast(dict[str, Any], primary)
        landing_page_url_obj = cast_primary.get("landing_page_url")
        if isinstance(landing_page_url_obj, str):
            landing_page_url = landing_page_url_obj

    meta = PaperMeta(
        paper_id=f"openalex:{short_id}",
        title=work.get("display_name") or "(untitled)",
        year=work.get("publication_year"),
        venue=venue,
        authors=authors,
        source="openalex",
        url=landing_page_url or oa_id,
        doi=work.get("doi"),
    )
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
    return meta, abstract


def fetch_openalex(
    query: str,
    limit: int = 50,
    *,
    use_cache: bool = True,
) -> list[tuple[PaperMeta, str | None]]:
    """Search OpenAlex for `query`, return up to `limit` (PaperMeta, abstract) pairs.

    Only works that actually have an abstract are returned (claim-dense text).
    """
    per_page = min(limit, 200)
    cache_key = f"{query}|{limit}"
    cache_file = _cache_path(cache_key)

    if use_cache and cache_file.exists():
        payload = json.loads(cache_file.read_text())
    else:
        params: object = {
            "search": query,
            "per-page": per_page,
            "mailto": MAILTO,
            # Ask only for the fields we use — smaller, faster responses.
            "select": (
                "id,display_name,publication_year,primary_location,"
                "authorships,abstract_inverted_index,doi"
            ),
        }
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(OPENALEX_BASE, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        cache_file.write_text(json.dumps(payload))
        time.sleep(0.2)  # be polite

    results: list[tuple[PaperMeta, str | None]] = []
    for work in payload.get("results", []):
        meta, abstract = _parse_work(work)
        if abstract:  # skip abstract-less records
            results.append((meta, abstract))
        if len(results) >= limit:
            break
    return results
