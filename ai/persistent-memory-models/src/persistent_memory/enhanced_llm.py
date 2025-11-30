#!/usr/bin/env python3
"""
Enhanced LLM - A Complete Chatbot with Persistent Memory

This wraps an open-source LLM (Ollama/Mistral) and enhances it with:
- Persistent memory (vector store + knowledge graph)
- Hierarchical attention for smart context retrieval
- Dynamic context allocation
- Quality monitoring
- Query caching
- Fact extraction and learning

Usage:
    from enhanced_llm import EnhancedLLM

    bot = EnhancedLLM(model="mistral")
    response = await bot.chat("What is a transformer?")
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

# LLM backend
from openai import AsyncOpenAI

from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.context_quality_monitor import ContextQualityMonitor
from persistent_memory.dynamic_context_allocator import DynamicContextAllocator
from persistent_memory.fact_extractor import FactExtractor
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph

# Our advanced components
from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.query_cache import QueryCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedLLM:
    """
    A chatbot that enhances an open-source LLM with persistent memory.

    This is NOT just a wrapper - it fundamentally improves the model by:
    1. Giving it long-term memory (remembers past conversations)
    2. Using hierarchical attention to find the BEST context
    3. Dynamically allocating context budget based on query complexity
    4. Monitoring quality to ensure good responses
    5. Caching frequent queries for speed
    6. Extracting and storing facts to build knowledge over time
    """

    def __init__(
        self,
        model: str = "mistral",
        ollama_host: str = "http://localhost:11434/v1",
        max_context_tokens: int = 4096,
        enable_cache: bool = True,
        enable_attention: bool = True,
        enable_quality_monitoring: bool = True,
    ):
        """
        Initialize the Enhanced LLM.

        Args:
            model: Model name (e.g., "mistral", "llama2")
            ollama_host: Ollama API endpoint
            max_context_tokens: Maximum tokens for context
            enable_cache: Enable query caching
            enable_attention: Use hierarchical attention for retrieval
            enable_quality_monitoring: Monitor response quality
        """
        logger.info(f"🚀 Initializing Enhanced LLM with {model}...")

        # Base LLM (Ollama)
        self.llm = AsyncOpenAI(
            base_url=ollama_host,
            api_key="ollama",  # Ollama doesn't need a real key
        )
        self.model = model

        # Persistent Memory Layers
        logger.info("📚 Setting up persistent memory...")
        self.vector_store = PersistentVectorStore()  # Episodic memory
        self.knowledge_graph = PersistentKnowledgeGraph()  # Semantic memory

        # Advanced Retrieval
        self.retrieval: AttentionEnhancedRetrieval | None
        if enable_attention:
            logger.info("🔬 Enabling hierarchical attention...")
            self.retrieval = AttentionEnhancedRetrieval(self.vector_store)
        else:
            self.retrieval = None

        # Context Management
        logger.info("🎯 Setting up dynamic context allocation...")
        self.context_allocator = DynamicContextAllocator(max_tokens=max_context_tokens)

        # Quality Monitoring
        self.quality_monitor: ContextQualityMonitor | None
        if enable_quality_monitoring:
            logger.info("📊 Enabling quality monitoring...")
            self.quality_monitor = ContextQualityMonitor()
        else:
            self.quality_monitor = None

        # Query Caching
        self.cache: QueryCache | None
        if enable_cache:
            try:
                logger.info("⚡ Enabling query cache...")
                self.cache = QueryCache()
            except Exception as e:
                logger.warning(f"Cache unavailable: {e}")
                self.cache = None
        else:
            self.cache = None

        # Fact Extraction
        logger.info("🔍 Setting up fact extraction...")
        # Fact Extraction
        logger.info("🔍 Setting up fact extraction...")
        self.fact_extractor = FactExtractor(llm=self.llm, knowledge_graph=self.knowledge_graph)

        # Conversation history (working memory)
        self.conversation_history: list[dict[str, str]] = []

        logger.info("✅ Enhanced LLM ready!")

    async def chat(
        self,
        user_input: str,
        session_id: str | None = None,
        use_memory: bool = True,
        return_metadata: bool = False,
    ) -> str | dict[str, Any]:
        """
        Chat with the enhanced LLM.

        Args:
            user_input: User's message
            session_id: Optional session ID for tracking
            use_memory: Whether to use persistent memory
            return_metadata: Return detailed metadata

        Returns:
            Response string, or dict with response + metadata
        """
        start_time = time.time()
        session_id = session_id or f"session_{int(time.time())}"

        logger.info(f"💬 User: {user_input}")

        # Step 1: Check cache
        # Step 1: Check cache
        if self.cache and use_memory:
            cached = await self.cache.get(user_input)
            if cached:
                logger.info("⚡ Cache HIT!")
                # Unwrap if it's a wrapped value
                response_val = (
                    cached.get("value")
                    if isinstance(cached, dict) and "value" in cached
                    else cached
                )

                if return_metadata:
                    return {
                        "response": response_val,
                        "cached": True,
                        "latency": time.time() - start_time,
                    }
                return str(response_val) if not return_metadata else response_val

        # Step 2: Retrieve relevant context from memory
        relevant_contexts = []
        if use_memory:
            if self.retrieval:
                # Use hierarchical attention
                logger.info("🔬 Retrieving with hierarchical attention...")
                retrieval_result = self.retrieval.retrieve_with_attention(
                    user_input, k=10, return_attention=True
                )
                relevant_contexts = retrieval_result["contexts"]
                logger.info(f"   Found {len(relevant_contexts)} contexts")
            else:
                # Standard vector search
                logger.info("🔍 Retrieving with vector search...")
                results = self.vector_store.search(user_input, k=10)
                relevant_contexts = [
                    {"text": r["text"], "metadata": r.get("metadata", {})} for r in results
                ]

        # Step 3: Allocate context budget
        # Step 3: Allocate context budget
        if relevant_contexts:
            logger.info("🎯 Allocating context budget...")
            allocation, _ = self.context_allocator.allocate_context(user_input, relevant_contexts)
            selected_contexts = allocation.get("retrieved", [])
            logger.info(f"   Allocated context with {len(selected_contexts)} chunks")
        else:
            selected_contexts = []

        # Step 4: Build prompt with context
        prompt = self._build_prompt(user_input, selected_contexts)

        # Step 5: Generate response
        logger.info("🤖 Generating response...")
        response = await self._generate_response(prompt)
        logger.info(f"✅ Response: {response[:100]}...")

        # Step 6: Evaluate quality
        quality_metrics = None
        if self.quality_monitor and selected_contexts:
            logger.info("📊 Evaluating quality...")
            quality_metrics = self.quality_monitor.evaluate_context(
                user_input, [c.get("text", "") for c in selected_contexts], response
            )
            logger.info(f"   Relevance: {quality_metrics.relevance_score:.3f}")

        # Step 7: Extract and store facts
        if use_memory:
            logger.info("🔍 Extracting facts...")
            try:
                extraction_result = await self.fact_extractor.extract_from_text(
                    f"User: {user_input}\nAssistant: {response}"
                )
                logger.info(f"   Extracted {len(extraction_result.facts)} facts")

                # Store facts in knowledge graph
                for fact in extraction_result.facts:
                    self.knowledge_graph.add_fact(fact.subject, fact.predicate, fact.object)
            except Exception as e:
                logger.warning(f"Fact extraction failed: {e}")

        # Step 8: Store conversation in memory
        if use_memory:
            logger.info("💾 Storing in memory...")
            self.vector_store.add_text(
                f"Q: {user_input}\nA: {response}",
                metadata={
                    "type": "conversation",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_input": user_input,
                    "response": response,
                },
            )

        # Step 9: Update conversation history
        self.conversation_history.append(
            {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
        )

        # Step 10: Cache result
        if self.cache and use_memory:
            await self.cache.set(user_input, {"value": response}, ttl=3600)

        latency = time.time() - start_time
        logger.info(f"⏱️  Total latency: {latency:.2f}s")

        # Return response with optional metadata
        if return_metadata:
            return {
                "response": response,
                "latency": latency,
                "contexts_used": len(selected_contexts),
                "quality_metrics": quality_metrics.__dict__ if quality_metrics else None,
                "cached": False,
                "session_id": session_id,
            }

        return response

    def _build_prompt(self, user_input: str, contexts: list[dict]) -> str:
        """Build prompt with relevant context."""
        # System prompt
        system = """You are a helpful AI assistant with long-term memory.
You can remember past conversations and learn from them.
Use the provided context to give accurate, informed responses."""

        # Add context if available
        context_section = ""
        if contexts:
            context_section = "\n\nRelevant context from memory:\n"
            for i, ctx in enumerate(contexts[:5], 1):  # Top 5
                text = ctx.get("text", "")
                context_section += f"{i}. {text[:200]}...\n"

        # Current query
        user_section = f"\n\nUser: {user_input}\nAssistant:"

        return system + context_section + user_section

    async def _generate_response(self, prompt: str) -> str:
        """Generate response using the base LLM."""
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            return str(response.choices[0].message.content or "")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"

    async def teach(self, text: str, source: str = "manual"):
        """
        Teach the model new information.

        Args:
            text: Text to learn from
            source: Source of the information
        """
        logger.info(f"📖 Learning from: {source}")

        # Store in vector store
        self.vector_store.add_text(
            text,
            metadata={
                "type": "knowledge",
                "source": source,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Extract and store facts
        extraction_result = await self.fact_extractor.extract_from_text(text)
        for fact in extraction_result.facts:
            self.knowledge_graph.add_fact(fact.subject, fact.predicate, fact.object)

        logger.info(f"✅ Learned {len(extraction_result.facts)} new facts")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the enhanced LLM."""
        stats = {
            "model": self.model,
            "conversation_turns": len(self.conversation_history) // 2,
            "memory_enabled": True,
        }

        if self.cache:
            cache_stats = self.cache.get_stats()
            stats["cache"] = cache_stats

        if self.quality_monitor:
            quality_stats = self.quality_monitor.get_summary_stats()
            stats["quality"] = quality_stats

        return stats

    def clear_conversation(self):
        """Clear conversation history (but keep long-term memory)."""
        self.conversation_history = []
        logger.info("🗑️  Conversation history cleared")


# ============================================================================
# Demo / Example Usage
# ============================================================================
async def demo():
    """Demo the Enhanced LLM."""
    print("\n" + "🤖" * 40)
    print("Enhanced LLM Demo - Chatbot with Persistent Memory")
    print("🤖" * 40)

    # Initialize
    print("\n🚀 Initializing Enhanced LLM...")
    bot = EnhancedLLM(
        model="mistral",
        enable_cache=True,
        enable_attention=True,
        enable_quality_monitoring=True,
    )

    # Teach it something
    print("\n📖 Teaching the bot about transformers...")
    await bot.teach(
        "Transformers are neural network architectures that use self-attention mechanisms. "
        "They were introduced in the 'Attention is All You Need' paper in 2017. "
        "Key components include multi-head attention, positional encodings, and feed-forward networks.",
        source="training",
    )

    # Chat
    print("\n💬 Starting conversation...")

    queries = [
        "What are transformers?",
        "When were they introduced?",
        "What are the key components?",
    ]

    for query in queries:
        print(f"\n👤 User: {query}")
        result = await bot.chat(query, return_metadata=True)
        print(f"🤖 Bot: {result['response']}")
        print(f"   ⏱️  Latency: {result['latency']:.2f}s")
        print(f"   📚 Contexts used: {result['contexts_used']}")
        if result.get("quality_metrics"):
            print(f"   📊 Quality: {result['quality_metrics']['relevance_score']:.3f}")

    # Show stats
    print("\n📊 Bot Statistics:")
    stats = bot.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo())
