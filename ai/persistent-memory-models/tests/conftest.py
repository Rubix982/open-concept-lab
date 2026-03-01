"""Pytest configuration and fixtures."""

import asyncio
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    store = MagicMock()
    store.search.return_value = [{"id": "1", "text": "test", "distance": 0.1}]
    return store


@pytest.fixture
def mock_knowledge_graph():
    """Mock knowledge graph for testing."""
    kg = MagicMock()
    kg.query.return_value = []
    return kg


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife."


@pytest.fixture
def sample_facts():
    """Sample facts for testing."""
    return [
        {
            "subject": "Mr. Bennet",
            "predicate": "has_daughter",
            "object": "Elizabeth",
            "confidence": 0.95,
        },
        {
            "subject": "Elizabeth",
            "predicate": "lives_in",
            "object": "Longbourn",
            "confidence": 0.90,
        },
    ]
