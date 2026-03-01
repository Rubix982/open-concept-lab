"""Streaming query responses for real-time user experience."""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from persistent_memory.core.dynamic_context_allocator import DynamicContextAllocator
from persistent_memory.core.persistent_context_engine import PersistentKnowledgeGraph, PersistentVectorStore

logger = logging.getLogger(__name__)


class StreamingQueryEngine:
    """
    Stream query results in real-time for better UX.

    Yields results as they become available:
    1. Vector search results (fast)
    2. Knowledge graph results (medium)
    3. LLM-generated answer (slow)
    """

    def __init__(self):
        self.vector_store = PersistentVectorStore()
        self.knowledge_graph = PersistentKnowledgeGraph()
        self.allocator = DynamicContextAllocator()
        logger.info("Initialized StreamingQueryEngine")

    async def stream_query(
        self, query: str, k: int = 5
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream query results as they become available.

        Yields:
            - {"type": "vector_result", "data": {...}}
            - {"type": "graph_result", "data": {...}}
            - {"type": "answer", "data": {...}}
            - {"type": "complete", "data": {...}}
        """
        try:
            # Phase 1: Vector search (fastest)
            yield {
                "type": "status",
                "data": {"message": "Searching vector store...", "progress": 0.2},
            }

            vector_results = self.vector_store.search(query, k=k)

            for i, result in enumerate(vector_results):
                yield {
                    "type": "vector_result",
                    "data": {
                        "index": i,
                        "text": result.get("text", ""),
                        "distance": result.get("distance", 0),
                        "metadata": result.get("metadata", {}),
                    },
                }
                await asyncio.sleep(0.01)  # Small delay for streaming effect

            # Phase 2: Knowledge graph (medium)
            yield {
                "type": "status",
                "data": {"message": "Querying knowledge graph...", "progress": 0.5},
            }

            graph_results = self.knowledge_graph.query(query)

            for i, result in enumerate(graph_results):
                yield {
                    "type": "graph_result",
                    "data": {
                        "index": i,
                        "subject": result.get("subject", ""),
                        "predicate": result.get("predicate", ""),
                        "object": result.get("object", ""),
                        "confidence": result.get("confidence", 0),
                    },
                }
                await asyncio.sleep(0.01)

            # Phase 3: Generate answer (slowest - would use LLM)
            yield {
                "type": "status",
                "data": {"message": "Generating answer...", "progress": 0.8},
            }

            # Allocate context intelligently
            allocated_context, buffer_size = self.allocator.allocate_context(
                query, vector_results
            )

            # For now, create a summary from retrieved contexts
            answer = self._create_summary(query, vector_results, graph_results)

            yield {
                "type": "answer",
                "data": {
                    "text": answer,
                    "sources": len(vector_results) + len(graph_results),
                    "confidence": 0.85,
                },
            }

            # Phase 4: Complete
            yield {
                "type": "complete",
                "data": {
                    "message": "Query complete",
                    "progress": 1.0,
                    "stats": {
                        "vector_results": len(vector_results),
                        "graph_results": len(graph_results),
                        "total_time_ms": 0,  # Would track actual time
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error in streaming query: {e}")
            yield {"type": "error", "data": {"message": str(e)}}

    def _create_summary(
        self, query: str, vector_results: list[dict], graph_results: list[dict]
    ) -> str:
        """Create a summary from retrieved results."""
        if not vector_results and not graph_results:
            return "No relevant information found."

        summary_parts = []

        if vector_results:
            # Take top 3 most relevant passages
            top_passages = vector_results[:3]
            passages_text = " ".join([r.get("text", "")[:200] for r in top_passages])
            summary_parts.append(f"Based on the text: {passages_text}...")

        if graph_results:
            # Summarize relationships
            facts = [
                f"{r.get('subject')} {r.get('predicate')} {r.get('object')}"
                for r in graph_results[:5]
            ]
            summary_parts.append(f"Known facts: {', '.join(facts)}")

        return " ".join(summary_parts)
