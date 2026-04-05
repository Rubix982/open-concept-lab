"""Validation script for pipeline/embedder.py.

Tests what can be verified WITHOUT an API key or GPU:

1. Control flow: embed_papers() with api_key=None falls through to Path 3
   (local inference).  The model load is mocked so no GPU or network is needed.
2. Checkpoint resume: a partial checkpoint causes already-embedded IDs to be
   skipped.
3. L2 normalisation: output vectors have unit norm (within float32 tolerance).
4. Output shape: [N, 768] for N papers.

Paths 1 and 2 require a valid Semantic Scholar API key to run end-to-end;
they are tested only for logic that can be exercised without network access
(e.g. _load_checkpoint, _save_checkpoint, _l2_normalize).

Usage::

    python agents/engineer/workspace/validate_embedder.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Make sure the package is importable from the repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from gcn_citation.pipeline.embedder import (  # noqa: E402
    _l2_normalize,
    _load_checkpoint,
    _save_checkpoint,
    embed_papers,
)

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    status = PASS if ok else FAIL
    results.append((name, status, detail))
    tag = "✓" if ok else "✗"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Helper: build a small fake papers DataFrame
# ---------------------------------------------------------------------------


def _make_papers(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "arxiv_id": [f"2310.{i:05d}" for i in range(n)],
            "title": [f"Paper {i}" for i in range(n)],
            "abstract": [f"Abstract for paper {i}." for i in range(n)],
        }
    )


# ---------------------------------------------------------------------------
# Test 1 — Output shape [N, 768]
# ---------------------------------------------------------------------------


def test_output_shape() -> None:
    """embed_papers() should return an array of shape [N, 768]."""
    n = 4
    papers = _make_papers(n)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "embeddings.npy"
        checkpoint_path = Path(tmpdir) / "checkpoint.json"

        # Mock Path 3 (local inference) to return synthetic vectors
        def _fake_embed_locally(
            arxiv_ids, papers_df, embeddings, checkpoint_path, **kwargs
        ):
            checkpoint = _load_checkpoint(checkpoint_path)
            arxiv_id_to_row = {
                aid: i for i, aid in enumerate(papers_df["arxiv_id"].tolist())
            }
            for aid in arxiv_ids:
                row_idx = arxiv_id_to_row[aid]
                embeddings[row_idx] = np.ones(768, dtype=np.float32) * 0.5
                checkpoint[aid] = row_idx
            _save_checkpoint(checkpoint, checkpoint_path)
            return embeddings

        with patch(
            "gcn_citation.pipeline.embedder.embed_locally",
            side_effect=_fake_embed_locally,
        ):
            result = embed_papers(
                papers,
                output_path,
                checkpoint_path,
                api_key=None,
                device="cpu",
            )

        record("output_shape", result.shape == (n, 768), f"got {result.shape}")


# ---------------------------------------------------------------------------
# Test 2 — L2 normalisation
# ---------------------------------------------------------------------------


def test_l2_normalisation() -> None:
    """_l2_normalize() should produce unit-norm rows (within float32 tolerance)."""
    rng = np.random.default_rng(42)
    arr = rng.standard_normal((20, 768)).astype(np.float32)
    arr[5] = 0.0  # zero row — should remain zero

    normalized = _l2_normalize(arr.copy())

    norms = np.linalg.norm(normalized, axis=1)
    non_zero_mask = np.linalg.norm(arr, axis=1) > 0
    max_deviation = float(np.max(np.abs(norms[non_zero_mask] - 1.0)))
    zero_row_unchanged = np.all(normalized[5] == 0.0)

    ok = max_deviation < 1e-5 and zero_row_unchanged
    record(
        "l2_normalisation",
        ok,
        f"max_deviation={max_deviation:.2e}, zero_row_unchanged={zero_row_unchanged}",
    )


# ---------------------------------------------------------------------------
# Test 3 — Checkpoint save/load round-trip
# ---------------------------------------------------------------------------


def test_checkpoint_roundtrip() -> None:
    """_save_checkpoint / _load_checkpoint should round-trip correctly."""
    data = {"2310.00001": 0, "2310.00002": 1, "2310.00003": 2}

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "checkpoint.json"
        _save_checkpoint(data, path)
        loaded = _load_checkpoint(path)

    ok = loaded == data
    record(
        "checkpoint_roundtrip", ok, f"saved={data}, loaded={loaded}" if not ok else ""
    )


# ---------------------------------------------------------------------------
# Test 4 — Checkpoint resume: already-embedded IDs are skipped
# ---------------------------------------------------------------------------


def test_checkpoint_resume() -> None:
    """embed_papers() should skip IDs that are already in the checkpoint.

    We pre-populate a checkpoint with 3 of 5 papers (rows 0–2) and verify
    that the mock embed_locally is called only for the remaining 2 papers.
    """
    n = 5
    papers = _make_papers(n)
    arxiv_ids = papers["arxiv_id"].tolist()

    # Pre-embed the first 3 papers
    already_embedded = arxiv_ids[:3]
    pre_checkpoint = {aid: i for i, aid in enumerate(already_embedded)}

    calls: list[list[str]] = []

    def _fake_embed_locally(
        arxiv_ids_arg, papers_df, embeddings, checkpoint_path, **kwargs
    ):
        calls.append(list(arxiv_ids_arg))
        checkpoint = _load_checkpoint(checkpoint_path)
        arxiv_id_to_row = {
            aid: i for i, aid in enumerate(papers_df["arxiv_id"].tolist())
        }
        for aid in arxiv_ids_arg:
            row_idx = arxiv_id_to_row[aid]
            embeddings[row_idx] = np.ones(768, dtype=np.float32) * 0.3
            checkpoint[aid] = row_idx
        _save_checkpoint(checkpoint, checkpoint_path)
        return embeddings

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "embeddings.npy"
        checkpoint_path = Path(tmpdir) / "checkpoint.json"

        # Pre-fill output array with partial values
        arr = np.lib.format.open_memmap(
            str(output_path), mode="w+", dtype=np.float32, shape=(n, 768)
        )
        for i in range(3):
            arr[i] = np.ones(768, dtype=np.float32) * float(i + 1)
        del arr  # flush

        # Write the pre-populated checkpoint
        _save_checkpoint(pre_checkpoint, checkpoint_path)

        with patch(
            "gcn_citation.pipeline.embedder.embed_locally",
            side_effect=_fake_embed_locally,
        ):
            embed_papers(
                papers,
                output_path,
                checkpoint_path,
                api_key=None,
                device="cpu",
            )

    # embed_locally should have been called once with the 2 remaining IDs
    called_ids = calls[0] if calls else []
    expected_ids = arxiv_ids[3:]
    ok = called_ids == expected_ids
    record(
        "checkpoint_resume",
        ok,
        f"called_with={called_ids}, expected={expected_ids}",
    )


# ---------------------------------------------------------------------------
# Test 5 — api_key=None bypasses Paths 1 and 2
# ---------------------------------------------------------------------------


def test_no_api_key_skips_bulk_and_per_paper() -> None:
    """With api_key=None, download_bulk_embeddings and fetch_embeddings_per_paper
    must NOT be called; control flow should reach embed_locally directly.
    """
    n = 3
    papers = _make_papers(n)

    bulk_called = []
    per_paper_called = []
    local_called = []

    def _fake_bulk(*args, **kwargs):
        bulk_called.append(True)
        raise AssertionError("bulk should not be called")

    def _fake_per_paper(*args, **kwargs):
        per_paper_called.append(True)
        raise AssertionError("per_paper should not be called")

    def _fake_local(arxiv_ids_arg, papers_df, embeddings, checkpoint_path, **kwargs):
        local_called.append(list(arxiv_ids_arg))
        checkpoint = _load_checkpoint(checkpoint_path)
        arxiv_id_to_row = {
            aid: i for i, aid in enumerate(papers_df["arxiv_id"].tolist())
        }
        for aid in arxiv_ids_arg:
            row_idx = arxiv_id_to_row[aid]
            embeddings[row_idx] = np.ones(768, dtype=np.float32)
            checkpoint[aid] = row_idx
        _save_checkpoint(checkpoint, checkpoint_path)
        return embeddings

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "embeddings.npy"
        checkpoint_path = Path(tmpdir) / "checkpoint.json"

        with (
            patch(
                "gcn_citation.pipeline.embedder.download_bulk_embeddings",
                side_effect=_fake_bulk,
            ),
            patch(
                "gcn_citation.pipeline.embedder.fetch_embeddings_per_paper",
                side_effect=_fake_per_paper,
            ),
            patch(
                "gcn_citation.pipeline.embedder.embed_locally",
                side_effect=_fake_local,
            ),
        ):
            embed_papers(
                papers,
                output_path,
                checkpoint_path,
                api_key=None,
                device="cpu",
            )

    ok = (not bulk_called) and (not per_paper_called) and bool(local_called)
    record(
        "no_api_key_skips_bulk_and_per_paper",
        ok,
        f"bulk_called={bool(bulk_called)}, per_paper_called={bool(per_paper_called)}, "
        f"local_called={bool(local_called)}",
    )


# ---------------------------------------------------------------------------
# Test 6 — Missing columns raises ValueError
# ---------------------------------------------------------------------------


def test_missing_columns_raises() -> None:
    """embed_papers() should raise ValueError if required columns are absent."""
    papers = pd.DataFrame({"arxiv_id": ["2310.00001"], "title": ["T"]})  # no 'abstract'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "embeddings.npy"
        checkpoint_path = Path(tmpdir) / "checkpoint.json"
        try:
            embed_papers(papers, output_path, checkpoint_path, api_key=None)
            raised = False
        except ValueError:
            raised = True

    record("missing_columns_raises_valueerror", raised)


# ---------------------------------------------------------------------------
# Test 7 — load_embeddings raises FileNotFoundError for missing file
# ---------------------------------------------------------------------------


def test_load_embeddings_missing_file() -> None:
    """load_embeddings() should raise FileNotFoundError for a nonexistent path."""
    from gcn_citation.pipeline.embedder import load_embeddings

    with tempfile.TemporaryDirectory() as tmpdir:
        missing = Path(tmpdir) / "nonexistent.npy"
        try:
            load_embeddings(missing)
            raised = False
        except FileNotFoundError:
            raised = True

    record("load_embeddings_missing_file_raises", raised)


# ---------------------------------------------------------------------------
# Test 8 — load_embeddings returns mmap array for valid file
# ---------------------------------------------------------------------------


def test_load_embeddings_returns_mmap() -> None:
    """load_embeddings() should return a memory-mapped array with correct shape."""
    from gcn_citation.pipeline.embedder import load_embeddings

    n, d = 10, 768
    arr = np.random.default_rng(0).standard_normal((n, d)).astype(np.float32)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "embeddings.npy"
        np.save(str(path), arr)
        loaded = load_embeddings(path)

    ok = loaded.shape == (n, d) and loaded.dtype == np.float32
    record(
        "load_embeddings_returns_correct_shape",
        ok,
        f"shape={loaded.shape}, dtype={loaded.dtype}",
    )


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------


def main() -> int:
    print("=" * 60)
    print("validate_embedder.py")
    print("=" * 60)

    tests = [
        ("Output shape [N, 768]", test_output_shape),
        ("L2 normalisation", test_l2_normalisation),
        ("Checkpoint round-trip", test_checkpoint_roundtrip),
        ("Checkpoint resume (skips already-done IDs)", test_checkpoint_resume),
        (
            "api_key=None bypasses bulk + per-paper paths",
            test_no_api_key_skips_bulk_and_per_paper,
        ),
        ("Missing columns raises ValueError", test_missing_columns_raises),
        (
            "load_embeddings missing file raises FileNotFoundError",
            test_load_embeddings_missing_file,
        ),
        ("load_embeddings returns correct shape", test_load_embeddings_returns_mmap),
    ]

    for label, fn in tests:
        print(f"\n[TEST] {label}")
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            record(label, False, f"EXCEPTION: {exc}")

    print("\n" + "=" * 60)
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    print(f"Results: {passed}/{len(results)} PASS, {failed} FAIL")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
