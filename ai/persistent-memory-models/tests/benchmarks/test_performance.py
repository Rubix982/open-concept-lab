"""Performance benchmarks."""

import pytest

from persistent_memory.persistent_vector_store import PersistentVectorStore


@pytest.mark.benchmark
class TestVectorStorePerformance:
    """Benchmark vector store operations."""

    def test_batch_insert_performance(self, benchmark):
        """Benchmark batch insertion."""
        store = PersistentVectorStore(collection_name="benchmark_test")

        def insert_batch():
            texts = [f"Sample text {i}" for i in range(100)]
            ids = [f"id_{i}" for i in range(100)]
            metadatas = [{"index": i} for i in range(100)]
            store.add_texts(texts, metadatas, ids)

        benchmark(insert_batch)

    def test_search_performance(self, benchmark):
        """Benchmark search operations."""
        store = PersistentVectorStore(collection_name="benchmark_test")

        # Pre-populate
        texts = [f"Sample text {i}" for i in range(1000)]
        ids = [f"id_{i}" for i in range(1000)]
        metadatas = [{"index": i} for i in range(1000)]
        store.add_texts(texts, metadatas, ids)

        def search():
            return store.search("sample query", k=10)

        result = benchmark(search)
        assert len(result) > 0
