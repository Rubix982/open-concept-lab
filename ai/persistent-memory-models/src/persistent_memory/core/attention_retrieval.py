"""
Attention-Enhanced Retrieval System.

Integrates hierarchical attention with vector store for intelligent context selection.
"""

import logging
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from persistent_memory.hierarchical_attention import (
    AttentionConfig,
    HierarchicalAttentionNetwork,
)
from persistent_memory.persistent_vector_store import PersistentVectorStore

logger = logging.getLogger(__name__)


class AttentionWeightedConsolidator:
    """
    Consolidate memories based on attention patterns
    Important memories (high attention) preserved longer
    """

    def __init__(self, transformer_model):
        self.model = transformer_model
        self.importance_scores = {}

    def track_attention(self, conversation_turn_id, attention_weights):
        """
        Track which parts of context received high attention
        """
        # Average attention across layers and heads
        avg_attention = attention_weights.mean(dim=(0, 1))

        # Update importance scores
        if conversation_turn_id not in self.importance_scores:
            self.importance_scores[conversation_turn_id] = []

        self.importance_scores[conversation_turn_id].append(avg_attention)

    def consolidate_memories(self, episodic_memory, threshold_days=7):
        """
        Consolidate low-attention memories, preserve high-attention ones
        """
        old_memories = episodic_memory.get_old_memories(threshold_days)

        for memory in old_memories:
            # Compute aggregate importance
            importance = np.mean(self.importance_scores.get(memory["id"], [0.5]))

            if importance < 0.3:  # Low importance
                # Compress aggressively or archive
                episodic_memory.archive(memory, compression="high")
            elif importance < 0.7:  # Medium importance
                # Summarize and store summary
                summary = self._summarize(memory)
                episodic_memory.replace_with_summary(memory["id"], summary)
            else:  # High importance
                # Keep full detail, just move to long-term storage
                episodic_memory.move_to_long_term(memory)


class AttentionEnhancedRetrieval:
    """
    Retrieval system enhanced with hierarchical attention.

    Instead of returning top-k chunks blindly, uses learned attention
    to intelligently select and weight contexts based on query.
    """

    def __init__(
        self,
        vector_store: PersistentVectorStore,
        attention_config: AttentionConfig | None = None,
        model_path: str | None = None,
    ):
        self.vector_store = vector_store
        self.config = attention_config or AttentionConfig()

        # Initialize attention network
        self.attention_net = HierarchicalAttentionNetwork(self.config)

        # Load pre-trained weights if available
        if model_path:
            self.load_model(model_path)

        # Sentence encoder for embeddings
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        logger.info("Initialized AttentionEnhancedRetrieval")

    def retrieve_with_attention(
        self, query: str, k: int = 20, return_attention: bool = False
    ) -> dict[str, Any]:
        """
        Retrieve contexts using hierarchical attention.

        Args:
            query: Search query
            k: Number of chunks to retrieve initially
            return_attention: Whether to return attention weights

        Returns:
            Dictionary with selected contexts and optional attention weights
        """
        # Step 1: Initial retrieval (get more than needed)
        initial_results = self.vector_store.search(query, k=k)

        if not initial_results:
            return {
                "contexts": [],
                "attention_weights": None,
                "metadata": {"method": "attention", "initial_k": k},
            }

        # Step 2: Prepare embeddings
        query_embedding = self._embed_text(query)

        chunk_texts = [r.get("text", "") for r in initial_results]
        chunk_embeddings = self._embed_texts(chunk_texts)

        # Extract sentences from chunks
        all_sentences = []
        sentence_to_chunk = []
        for chunk_idx, chunk_text in enumerate(chunk_texts):
            sentences = self._split_sentences(chunk_text)
            all_sentences.extend(sentences)
            sentence_to_chunk.extend([chunk_idx] * len(sentences))

        sentence_embeddings = self._embed_texts(all_sentences)

        # Step 3: Apply hierarchical attention
        with torch.no_grad():
            self.attention_net.eval()

            outputs = self.attention_net(
                torch.FloatTensor(query_embedding).unsqueeze(0),
                torch.FloatTensor(chunk_embeddings).unsqueeze(0),
                torch.FloatTensor(sentence_embeddings).unsqueeze(0),
            )

        # Step 4: Select top contexts based on attention
        chunk_attention = outputs["chunk_attention"][0].numpy()
        sentence_attention = outputs["sentence_attention"][0].numpy()

        # Rank chunks by attention score
        top_chunk_indices = np.argsort(chunk_attention)[::-1][: k // 2]

        selected_contexts = []
        for idx in top_chunk_indices:
            context = {
                "text": chunk_texts[idx],
                "attention_score": float(chunk_attention[idx]),
                "original_rank": idx,
                "metadata": initial_results[idx].get("metadata", {}),
            }

            # Add top sentences from this chunk
            chunk_sentence_indices = [
                i for i, c in enumerate(sentence_to_chunk) if c == idx
            ]
            if chunk_sentence_indices:
                chunk_sentence_attn = sentence_attention[chunk_sentence_indices]
                top_sentence_idx = chunk_sentence_indices[
                    np.argmax(chunk_sentence_attn)
                ]
                context["key_sentence"] = all_sentences[top_sentence_idx]
                context["sentence_attention"] = float(chunk_sentence_attn.max())

            selected_contexts.append(context)

        result = {
            "contexts": selected_contexts,
            "metadata": {
                "method": "hierarchical_attention",
                "initial_k": k,
                "selected_k": len(selected_contexts),
                "avg_chunk_attention": float(chunk_attention.mean()),
                "max_chunk_attention": float(chunk_attention.max()),
            },
        }

        if return_attention:
            result["attention_weights"] = {
                "chunk_attention": chunk_attention.tolist(),
                "sentence_attention": sentence_attention.tolist(),
                "sentence_to_chunk_mapping": sentence_to_chunk,
            }

        return result

    def _embed_text(self, text: str) -> np.ndarray:
        """Embed single text."""
        return self.encoder.encode(text, convert_to_numpy=True)

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed multiple texts."""
        return self.encoder.encode(texts, convert_to_numpy=True)

    def _split_sentences(self, text: str) -> list[str]:
        """Simple sentence splitter."""
        import re

        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def save_model(self, path: str):
        """Save attention model weights."""
        torch.save(self.attention_net.state_dict(), path)
        logger.info(f"Saved attention model to {path}")

    def load_model(self, path: str):
        """Load attention model weights."""
        self.attention_net.load_state_dict(torch.load(path))
        logger.info(f"Loaded attention model from {path}")


class AttentionDataset:
    """
    Dataset for training hierarchical attention.

    Creates training examples from query-context-relevance triplets.
    """

    def __init__(self):
        self.examples = []

    def add_example(
        self, query: str, contexts: list[str], relevance_scores: list[float]
    ):
        """
        Add training example.

        Args:
            query: The query text
            contexts: List of context chunks
            relevance_scores: Relevance score for each context (0-1)
        """
        self.examples.append(
            {"query": query, "contexts": contexts, "relevance": relevance_scores}
        )

    def create_from_queries(
        self, queries: list[str], vector_store: PersistentVectorStore, k: int = 20
    ):
        """
        Create dataset from queries by retrieving and assuming
        distance-based relevance.
        """
        _ = SentenceTransformer("all-MiniLM-L6-v2")

        for query in queries:
            results = vector_store.search(query, k=k)

            if not results:
                continue

            contexts = [r.get("text", "") for r in results]
            distances = [r.get("distance", 1.0) for r in results]

            # Convert distances to relevance scores (inverse)
            max_dist = max(distances) if distances else 1.0
            relevance = [1.0 - (d / max_dist) for d in distances]

            self.add_example(query, contexts, relevance)

        logger.info(f"Created dataset with {len(self.examples)} examples")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


# Example usage and evaluation
def evaluate_attention_retrieval(
    retrieval_system: AttentionEnhancedRetrieval,
    test_queries: list[str],
    ground_truth: dict[str, list[str]] | None = None,
) -> dict[str, float]:
    """
    Evaluate attention-based retrieval.

    Metrics:
    - Precision@k
    - Recall@k
    - MRR (Mean Reciprocal Rank)
    - Attention entropy (diversity of attention)
    """
    metrics: dict[str, list[float]] = {
        "precision": [],
        "recall": [],
        "mrr": [],
        "attention_entropy": [],
    }

    for query in test_queries:
        result = retrieval_system.retrieve_with_attention(
            query, k=10, return_attention=True
        )

        # Attention entropy (measure of focus)
        chunk_attn = np.array(result["attention_weights"]["chunk_attention"])
        entropy = -np.sum(chunk_attn * np.log(chunk_attn + 1e-10))
        metrics["attention_entropy"].append(entropy)

        # If ground truth available, compute precision/recall
        if ground_truth and query in ground_truth:
            retrieved_texts = [c["text"] for c in result["contexts"]]
            relevant_texts = ground_truth[query]

            relevant_retrieved = len(set(retrieved_texts) & set(relevant_texts))
            precision = (
                relevant_retrieved / len(retrieved_texts) if retrieved_texts else 0
            )
            recall = relevant_retrieved / len(relevant_texts) if relevant_texts else 0

            metrics["precision"].append(precision)
            metrics["recall"].append(recall)

    # Average metrics
    return {
        "avg_precision": (
            float(np.mean(metrics["precision"])) if metrics["precision"] else 0.0
        ),
        "avg_recall": float(np.mean(metrics["recall"])) if metrics["recall"] else 0.0,
        "avg_attention_entropy": float(np.mean(metrics["attention_entropy"])),
    }
