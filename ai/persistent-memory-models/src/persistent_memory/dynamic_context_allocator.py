"""Dynamic context window allocation based on query complexity."""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AllocationStrategy:
    """Token allocation strategy for different query types."""

    system_prompt: int
    retrieved_context: int
    conversation_history: int
    response_buffer: int

    def total(self) -> int:
        return (
            self.system_prompt
            + self.retrieved_context
            + self.conversation_history
            + self.response_buffer
        )


class DynamicContextAllocator:
    """
    Dynamically allocate context window based on query complexity.

    Analyzes queries to determine optimal token allocation across:
    - System prompt
    - Retrieved context
    - Conversation history
    - Response buffer
    """

    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens

        # Predefined allocation strategies
        self.strategies = {
            "simple": AllocationStrategy(
                system_prompt=300,
                retrieved_context=1200,
                conversation_history=500,
                response_buffer=2096,
            ),
            "medium": AllocationStrategy(
                system_prompt=400,
                retrieved_context=2000,
                conversation_history=800,
                response_buffer=896,
            ),
            "complex": AllocationStrategy(
                system_prompt=500,
                retrieved_context=2500,
                conversation_history=1000,
                response_buffer=96,
            ),
        }

        logger.info(f"Initialized DynamicContextAllocator with {max_tokens} max tokens")

    def allocate_context(
        self,
        query: str,
        available_contexts: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Optimally allocate limited context window.

        Args:
            query: The user query
            available_contexts: Retrieved context chunks
            conversation_history: Previous conversation turns

        Returns:
            Tuple of (allocated_context, response_buffer_size)
        """
        # Determine query complexity
        complexity = self._estimate_complexity(query)
        strategy = self.strategies[complexity]

        logger.info(f"Query complexity: {complexity}, Strategy: {strategy}")

        # Allocate context based on strategy
        context = {
            "system": self._get_system_prompt(strategy.system_prompt),
            "retrieved": self._select_top_contexts(
                available_contexts, max_tokens=strategy.retrieved_context
            ),
            "history": self._get_recent_history(
                conversation_history or [], max_tokens=strategy.conversation_history
            ),
            "metadata": {"complexity": complexity, "strategy": strategy.__dict__},
        }

        return context, strategy.response_buffer

    def _estimate_complexity(self, query: str) -> str:
        """
        Estimate query complexity based on multiple factors.

        Factors considered:
        - Query length
        - Number of entities mentioned
        - Question depth (nested questions)
        - Specificity indicators
        """
        # Basic metrics
        token_count = len(query.split())

        # Entity detection (simple heuristic)
        entity_count = len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query))

        # Question depth
        question_words = ["who", "what", "when", "where", "why", "how"]
        question_depth = sum(1 for word in question_words if word in query.lower())

        # Specificity indicators
        specific_indicators = ["exactly", "specifically", "detail", "explain", "compare", "analyze"]
        specificity_score = sum(
            1 for indicator in specific_indicators if indicator in query.lower()
        )

        # Complexity scoring
        complexity_score = (
            (token_count / 20)  # Length factor
            + (entity_count * 0.5)  # Entity factor
            + (question_depth * 1.5)  # Question depth factor
            + (specificity_score * 2)  # Specificity factor
        )

        logger.debug(
            f"Complexity analysis: tokens={token_count}, entities={entity_count}, "
            f"questions={question_depth}, specificity={specificity_score}, "
            f"score={complexity_score:.2f}"
        )

        # Classify
        if complexity_score > 8:
            return "complex"
        elif complexity_score > 4:
            return "medium"
        else:
            return "simple"

    def _get_system_prompt(self, max_tokens: int) -> str:
        """Get system prompt within token budget."""
        base_prompt = """You are a helpful AI assistant with access to a persistent memory system.
Use the provided context to answer questions accurately and comprehensively."""

        # Truncate if needed (rough approximation: 4 chars = 1 token)
        max_chars = max_tokens * 4
        if len(base_prompt) > max_chars:
            return base_prompt[:max_chars]
        return base_prompt

    def _select_top_contexts(
        self, contexts: list[dict[str, Any]], max_tokens: int
    ) -> list[dict[str, Any]]:
        """Select top contexts within token budget."""
        selected = []
        current_tokens = 0

        # Sort by relevance (assuming 'distance' field, lower is better)
        sorted_contexts = sorted(contexts, key=lambda x: x.get("distance", float("inf")))

        for ctx in sorted_contexts:
            # Estimate tokens (rough: 4 chars = 1 token)
            text = ctx.get("text", "")
            estimated_tokens = len(text) // 4

            if current_tokens + estimated_tokens <= max_tokens:
                selected.append(ctx)
                current_tokens += estimated_tokens
            else:
                break

        logger.debug(f"Selected {len(selected)}/{len(contexts)} contexts ({current_tokens} tokens)")
        return selected

    def _get_recent_history(
        self, history: list[dict[str, str]], max_tokens: int
    ) -> list[dict[str, str]]:
        """Get recent conversation history within token budget."""
        selected: list[dict[str, str]] = []
        current_tokens = 0

        # Take most recent first
        for turn in reversed(history):
            content = turn.get("content", "")
            estimated_tokens = len(content) // 4

            if current_tokens + estimated_tokens <= max_tokens:
                selected.insert(0, turn)  # Maintain chronological order
                current_tokens += estimated_tokens
            else:
                break

        logger.debug(
            f"Selected {len(selected)}/{len(history)} history turns ({current_tokens} tokens)"
        )
        return selected
