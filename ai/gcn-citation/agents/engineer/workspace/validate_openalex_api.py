"""Validation script for load_openalex_citations_api().

Tests:
    1. Batching: 120 IDs → exactly 3 calls in Pass 1 (batches of 50, 50, 20)
    2. 429 backoff: mock returns 429 twice then 200 → verify 2 retries with increasing delay
    3. Retry-After: mock returns 429 with Retry-After: 5 → verify sleep is called with 5s
    4. Max retries exceeded: mock always returns 500 → verify batch skipped, no exception raised
    5. Edge filtering: only in-corpus edges in output
    6. Cache resume: write partial cache JSON, verify already-cached IDs are skipped

Run from repo root with the venv activated:
    python agents/engineer/workspace/validate_openalex_api.py
"""

from __future__ import annotations

import json
import sys
import time
import unittest.mock
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import tempfile

# ---------------------------------------------------------------------------
# Bootstrap: make project importable
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(name: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status}  {name}{suffix}")
    return condition


def _make_response(status: int, body: dict | None = None, headers: dict | None = None):
    """Build a mock response object compatible with requests.Response."""
    resp = unittest.mock.MagicMock()
    resp.status_code = status
    resp.headers = headers or {}
    resp.json.return_value = body or {}
    return resp


def _arxiv_work(arxiv_id: str, refs: list[str]) -> dict:
    return {
        "id": f"https://openalex.org/W{arxiv_id.replace('.', '')}",
        "ids": {"arxiv": f"https://arxiv.org/abs/{arxiv_id}"},
        "referenced_works": refs,
    }


def _ref_work(arxiv_id: str) -> dict:
    return {
        "id": f"https://openalex.org/W{arxiv_id.replace('.', '')}",
        "ids": {"arxiv": f"https://arxiv.org/abs/{arxiv_id}"},
    }


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------
from gcn_citation.pipeline.citations import (
    load_openalex_citations_api,
    _api_get,
    _OPENALEX_API_BASE,
)

# ---------------------------------------------------------------------------
# Test 1: Batching — 120 IDs → exactly 3 Pass-1 calls
# ---------------------------------------------------------------------------


def test_batching():
    """120 IDs → 3 batches (50, 50, 20) in Pass 1."""
    arxiv_ids = [f"2301.{i:05d}" for i in range(120)]
    pass1_call_count = 0

    def fake_get(url, timeout=30):
        nonlocal pass1_call_count
        if "ids.arxiv:" in url:
            # Count Pass 1 calls
            pass1_call_count += 1
            # Parse how many IDs are in this batch
            filter_part = url.split("ids.arxiv:")[1].split("&")[0]
            ids_in_batch = filter_part.split("|")
            works = [_arxiv_work(aid, []) for aid in ids_in_batch[:3]]
            return _make_response(200, {"results": works})
        # Pass 2 calls: resolve referenced works (none here)
        return _make_response(200, {"results": []})

    mock_session = unittest.mock.MagicMock()
    mock_session.get.side_effect = fake_get

    with (
        unittest.mock.patch("gcn_citation.pipeline.citations._requests") as mock_req,
        unittest.mock.patch("time.sleep"),
    ):
        mock_req.Session.return_value = mock_session
        result = load_openalex_citations_api(arxiv_ids, requests_per_second=9.0)

    ok = check(
        "batching: pass1_call_count == 3",
        pass1_call_count == 3,
        f"got {pass1_call_count}",
    )
    return ok


# ---------------------------------------------------------------------------
# Test 2: 429 backoff — mock returns 429 twice then 200
# ---------------------------------------------------------------------------


def test_429_backoff():
    """429 twice then 200 → 2 retries with increasing delay."""
    sleep_calls: list[float] = []
    original_sleep = time.sleep

    responses = [
        _make_response(429),
        _make_response(429),
        _make_response(200, {"results": []}),
    ]
    call_idx = [0]

    def fake_get(url, timeout=30):
        resp = responses[min(call_idx[0], len(responses) - 1)]
        call_idx[0] += 1
        return resp

    mock_session = unittest.mock.MagicMock()
    mock_session.get.side_effect = fake_get

    with unittest.mock.patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        data = _api_get(
            "https://api.openalex.org/works?test",
            session=mock_session,
            requests_per_second=9.0,
        )

    # We should have slept at least twice due to 429 retries (plus the per-request sleep)
    # Backoff sleeps only (not counting the initial rate-limit sleep)
    backoff_sleeps = [s for s in sleep_calls if s >= 1.0]
    ok1 = check(
        "429_backoff: at least 2 backoff sleeps",
        len(backoff_sleeps) >= 2,
        f"backoff sleeps: {backoff_sleeps}",
    )
    # Second backoff should be >= first (exponential)
    ok2 = True
    if len(backoff_sleeps) >= 2:
        ok2 = check(
            "429_backoff: second delay >= first delay",
            backoff_sleeps[1] >= backoff_sleeps[0],
            f"{backoff_sleeps[1]:.2f} >= {backoff_sleeps[0]:.2f}",
        )
    # Final call should succeed → returns dict
    ok3 = check("429_backoff: returns data after retries", data is not None)
    return ok1 and ok2 and ok3


# ---------------------------------------------------------------------------
# Test 3: Retry-After header respected
# ---------------------------------------------------------------------------


def test_retry_after():
    """429 with Retry-After: 5 → sleep called with approximately 5s."""
    sleep_calls: list[float] = []

    responses = [
        _make_response(429, headers={"Retry-After": "5"}),
        _make_response(200, {"results": []}),
    ]
    call_idx = [0]

    def fake_get(url, timeout=30):
        resp = responses[min(call_idx[0], len(responses) - 1)]
        call_idx[0] += 1
        return resp

    mock_session = unittest.mock.MagicMock()
    mock_session.get.side_effect = fake_get

    with unittest.mock.patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        data = _api_get(
            "https://api.openalex.org/works?test",
            session=mock_session,
            requests_per_second=9.0,
        )

    # One of the sleep calls should be exactly 5.0 (from Retry-After)
    retry_after_sleeps = [s for s in sleep_calls if s == 5.0]
    ok = check(
        "retry_after: sleep(5.0) called",
        len(retry_after_sleeps) >= 1,
        f"all sleep calls: {sleep_calls}",
    )
    return ok


# ---------------------------------------------------------------------------
# Test 4: Max retries exceeded — always 500, batch skipped, no exception
# ---------------------------------------------------------------------------


def test_max_retries_exceeded():
    """Always 500 → batch skipped, returns None, no exception."""
    mock_session = unittest.mock.MagicMock()
    mock_session.get.return_value = _make_response(500)

    with unittest.mock.patch("time.sleep"):
        try:
            result = _api_get(
                "https://api.openalex.org/works?test",
                session=mock_session,
                requests_per_second=9.0,
                max_retries=5,
            )
            ok1 = check("max_retries: returns None", result is None)
            ok2 = check("max_retries: no exception raised", True)
        except Exception as exc:
            ok1 = check("max_retries: returns None", False, str(exc))
            ok2 = check("max_retries: no exception raised", False, str(exc))

    # Verify the full load function also continues (doesn't propagate)
    arxiv_ids = ["2301.00001", "2301.00002"]
    call_count = [0]

    def always_500(url, timeout=30):
        call_count[0] += 1
        return _make_response(500)

    mock_session2 = unittest.mock.MagicMock()
    mock_session2.get.side_effect = always_500

    with (
        unittest.mock.patch("gcn_citation.pipeline.citations._requests") as mock_req,
        unittest.mock.patch("time.sleep"),
    ):
        mock_req.Session.return_value = mock_session2
        try:
            result2 = load_openalex_citations_api(arxiv_ids, requests_per_second=9.0)
            ok3 = check(
                "max_retries: function continues after batch skip",
                len(result2.source_ids) == 0,
                f"edges: {len(result2.source_ids)}",
            )
        except Exception as exc:
            ok3 = check(
                "max_retries: function continues after batch skip", False, str(exc)
            )

    return ok1 and ok2 and ok3


# ---------------------------------------------------------------------------
# Test 5: Edge filtering — only in-corpus edges in output
# ---------------------------------------------------------------------------


def test_edge_filtering():
    """Only edges where BOTH endpoints are in arxiv_ids are kept."""
    corpus = ["2301.00001", "2301.00002", "2301.00003"]
    outside = "9999.99999"

    # Work 001 cites 002 (in corpus) and outside (not in corpus)
    # Work 003 cites outside only
    ref_url_002 = f"https://openalex.org/W{corpus[1].replace('.', '')}"
    ref_url_out = f"https://openalex.org/W{outside.replace('.', '')}"
    ref_url_003 = f"https://openalex.org/W{corpus[2].replace('.', '')}"

    pass1_results = {
        corpus[0]: {
            "id": f"https://openalex.org/W{corpus[0].replace('.','')}",
            "ids": {"arxiv": corpus[0]},
            "referenced_works": [ref_url_002, ref_url_out],
        },
        corpus[1]: {
            "id": f"https://openalex.org/W{corpus[1].replace('.','')}",
            "ids": {"arxiv": corpus[1]},
            "referenced_works": [],
        },
        corpus[2]: {
            "id": f"https://openalex.org/W{corpus[2].replace('.','')}",
            "ids": {"arxiv": corpus[2]},
            "referenced_works": [ref_url_out],
        },
    }

    # Pass 2 resolves referenced works
    pass2_results = {
        ref_url_002.rsplit("/", 1)[-1]: {
            "id": ref_url_002,
            "ids": {"arxiv": corpus[1]},
        },
        ref_url_out.rsplit("/", 1)[-1]: {"id": ref_url_out, "ids": {"arxiv": outside}},
        ref_url_003.rsplit("/", 1)[-1]: {
            "id": ref_url_003,
            "ids": {"arxiv": corpus[2]},
        },
    }

    def fake_get(url, timeout=30):
        if "ids.arxiv:" in url:
            # Pass 1
            filter_str = url.split("ids.arxiv:")[1].split("&")[0]
            requested_ids = filter_str.split("|")
            works = [
                pass1_results[aid] for aid in requested_ids if aid in pass1_results
            ]
            return _make_response(200, {"results": works})
        elif "openalex_id:" in url:
            # Pass 2
            filter_str = url.split("openalex_id:")[1].split("&")[0]
            requested_ids = filter_str.split("|")
            works = [
                pass2_results[wid] for wid in requested_ids if wid in pass2_results
            ]
            return _make_response(200, {"results": works})
        return _make_response(200, {"results": []})

    mock_session = unittest.mock.MagicMock()
    mock_session.get.side_effect = fake_get

    with (
        unittest.mock.patch("gcn_citation.pipeline.citations._requests") as mock_req,
        unittest.mock.patch("time.sleep"),
    ):
        mock_req.Session.return_value = mock_session
        result = load_openalex_citations_api(corpus, requests_per_second=9.0)

    src_list = [str(s) for s in result.source_ids]
    tgt_list = [str(t) for t in result.target_ids]
    corpus_set = set(corpus)

    ok1 = check(
        "edge_filtering: all source_ids in corpus",
        all(s in corpus_set for s in src_list),
        f"sources: {src_list}",
    )
    ok2 = check(
        "edge_filtering: all target_ids in corpus",
        all(t in corpus_set for t in tgt_list),
        f"targets: {tgt_list}",
    )
    ok3 = check(
        "edge_filtering: outside-corpus edges excluded",
        outside not in src_list and outside not in tgt_list,
    )
    ok4 = check(
        "edge_filtering: in-corpus edge retained",
        (corpus[0] in src_list and corpus[1] in tgt_list),
        f"expected {corpus[0]}→{corpus[1]}, got {list(zip(src_list, tgt_list))}",
    )
    return ok1 and ok2 and ok3 and ok4


# ---------------------------------------------------------------------------
# Test 6: Cache resume — already-cached IDs skipped in Pass 1
# ---------------------------------------------------------------------------


def test_cache_resume():
    """Pre-populated cache → already-cached IDs are not fetched in Pass 1."""
    corpus = [f"2301.{i:05d}" for i in range(10)]

    # Pre-cache first 5 papers
    cached_portion = corpus[:5]
    pre_cache = {
        aid: {
            "openalex_id": f"https://openalex.org/W{aid.replace('.', '')}",
            "referenced_openalex_ids": [],
        }
        for aid in cached_portion
    }

    pass1_fetched_ids: list[str] = []

    def fake_get(url, timeout=30):
        if "ids.arxiv:" in url:
            filter_str = url.split("ids.arxiv:")[1].split("&")[0]
            requested_ids = filter_str.split("|")
            pass1_fetched_ids.extend(requested_ids)
            works = [
                {
                    "id": f"https://openalex.org/W{aid.replace('.','')}",
                    "ids": {"arxiv": aid},
                    "referenced_works": [],
                }
                for aid in requested_ids
            ]
            return _make_response(200, {"results": works})
        return _make_response(200, {"results": []})

    mock_session = unittest.mock.MagicMock()
    mock_session.get.side_effect = fake_get

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(pre_cache, f)
        cache_path = Path(f.name)

    try:
        with (
            unittest.mock.patch(
                "gcn_citation.pipeline.citations._requests"
            ) as mock_req,
            unittest.mock.patch("time.sleep"),
        ):
            mock_req.Session.return_value = mock_session
            result = load_openalex_citations_api(
                corpus,
                requests_per_second=9.0,
                cache_path=cache_path,
            )

        # Only the uncached 5 IDs (corpus[5:]) should have been fetched in Pass 1
        fetched_set = set(pass1_fetched_ids)
        cached_set = set(cached_portion)
        unexpected = fetched_set & cached_set
        ok1 = check(
            "cache_resume: cached IDs not re-fetched",
            len(unexpected) == 0,
            f"unexpected fetches: {unexpected}",
        )
        expected_fetched = set(corpus[5:])
        ok2 = check(
            "cache_resume: uncached IDs were fetched",
            expected_fetched.issubset(fetched_set),
            f"expected {expected_fetched}, fetched {fetched_set}",
        )
    finally:
        cache_path.unlink(missing_ok=True)

    return ok1 and ok2


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    tests = [
        ("1. Batching (120 IDs → 3 Pass-1 calls)", test_batching),
        ("2. 429 backoff (2 retries with increasing delay)", test_429_backoff),
        ("3. Retry-After header respected", test_retry_after),
        (
            "4. Max retries exceeded (batch skipped, no exception)",
            test_max_retries_exceeded,
        ),
        ("5. Edge filtering (only in-corpus edges)", test_edge_filtering),
        ("6. Cache resume (cached IDs skipped in Pass 1)", test_cache_resume),
    ]

    results: list[bool] = []
    for title, fn in tests:
        print(f"\n--- {title} ---")
        try:
            ok = fn()
        except Exception as exc:
            print(f"  {FAIL}  Unexpected exception: {exc}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            ok = False
        results.append(ok)

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} PASS")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
