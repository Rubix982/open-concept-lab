"""Prometheus metrics for monitoring."""

import asyncio
import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram

# Counters
ingestion_total = Counter(
    "persistent_memory_ingestion_total", "Total number of ingestion operations", ["status"]
)

query_total = Counter(
    "persistent_memory_query_total", "Total number of query operations", ["layer"]
)

fact_extraction_total = Counter(
    "persistent_memory_fact_extraction_total", "Total number of facts extracted", ["status"]
)

# Histograms
ingestion_duration = Histogram(
    "persistent_memory_ingestion_duration_seconds", "Time spent on ingestion operations"
)

query_duration = Histogram(
    "persistent_memory_query_duration_seconds", "Time spent on query operations", ["layer"]
)

llm_call_duration = Histogram(
    "persistent_memory_llm_call_duration_seconds", "Time spent on LLM API calls"
)

# Gauges
vector_store_size = Gauge("persistent_memory_vector_store_size", "Number of items in vector store")

knowledge_graph_nodes = Gauge(
    "persistent_memory_knowledge_graph_nodes", "Number of nodes in knowledge graph"
)

knowledge_graph_edges = Gauge(
    "persistent_memory_knowledge_graph_edges", "Number of edges in knowledge graph"
)


def track_duration(metric):
    """Decorator to track operation duration."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
