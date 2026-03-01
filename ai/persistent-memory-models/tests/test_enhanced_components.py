"""Unit tests for enhanced core components."""

import numpy as np
import pytest

from persistent_memory.core.context_autoencoder import ContextAutoencoder
from persistent_memory.core.context_quality_monitor import ContextQualityMonitor
from persistent_memory.core.dynamic_context_allocator import DynamicContextAllocator


class TestContextQualityMonitor:
    """Tests for ContextQualityMonitor."""

    @pytest.mark.asyncio
    async def test_evaluate_retrieval_with_ground_truth(self):
        """Test retrieval evaluation with ground truth."""
        monitor = ContextQualityMonitor()

        retrieved = [
            {"id": "1", "text": "relevant"},
            {"id": "2", "text": "not relevant"},
            {"id": "3", "text": "relevant"},
        ]

        ground_truth = {"relevant_ids": ["1", "3", "4"]}

        metrics = await monitor.evaluate_retrieval("test query", retrieved, ground_truth)

        assert metrics.precision == 2 / 3
        assert metrics.recall == 2 / 3
        assert 0 < metrics.f1 < 1

    @pytest.mark.asyncio
    async def test_hallucination_detection(self):
        """Test hallucination detection."""
        monitor = ContextQualityMonitor()

        contexts = [{"content": "The sky is blue and grass is green"}]

        response1 = "The sky is blue"
        metrics1 = await monitor.monitor_context_usage(contexts, response1)
        assert metrics1.hallucination_rate < 0.5

        response2 = "The ocean is purple and mountains are yellow"
        metrics2 = await monitor.monitor_context_usage(contexts, response2)
        assert metrics2.hallucination_rate > 0.5


class TestDynamicContextAllocator:
    """Tests for DynamicContextAllocator."""

    def test_complexity_estimation(self):
        """Test query complexity estimation."""
        allocator = DynamicContextAllocator()

        assert allocator._estimate_complexity("What is AI?") == "simple"

        assert (
            allocator._estimate_complexity(
                "How does machine learning work and what are its applications?"
            )
            == "medium"
        )

        assert (
            allocator._estimate_complexity(
                "Explain in detail how transformer architectures work, "
                "compare them to RNNs, and analyze their computational complexity"
            )
            == "complex"
        )

    def test_context_allocation(self):
        """Test context allocation."""
        allocator = DynamicContextAllocator(max_tokens=4096)

        contexts = [
            {"text": "Context 1" * 100, "distance": 0.1},
            {"text": "Context 2" * 100, "distance": 0.2},
            {"text": "Context 3" * 100, "distance": 0.3},
        ]

        allocated, buffer = allocator.allocate_context("Simple query", contexts)

        assert "system" in allocated
        assert "retrieved" in allocated
        assert "history" in allocated
        assert buffer > 0


class TestContextAutoencoder:
    """Tests for ContextAutoencoder."""

    def test_initialization(self):
        """Test autoencoder initialization."""
        ae = ContextAutoencoder(input_dim=128, latent_dim=32)
        assert ae.input_dim == 128
        assert ae.latent_dim == 32
        assert ae.compression_ratio() == 4.0

    def test_compress_decompress(self):
        """Test compression and decompression."""
        ae = ContextAutoencoder(input_dim=128, latent_dim=32)

        embedding = np.random.randn(128).astype(np.float32)

        compressed = ae.compress(embedding)
        assert compressed.shape == (32,)

        decompressed = ae.decompress(compressed)
        assert decompressed.shape == (128,)

    def test_training(self):
        """Test training on embeddings."""
        ae = ContextAutoencoder(input_dim=64, latent_dim=16)

        embeddings = np.random.randn(100, 64).astype(np.float32)

        losses = ae.train_on_embeddings(embeddings, epochs=5, batch_size=10)

        assert len(losses) == 5
        assert losses[-1] < losses[0] * 1.5
