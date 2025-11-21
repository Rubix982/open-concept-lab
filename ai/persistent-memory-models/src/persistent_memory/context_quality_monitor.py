"""Quality monitoring for context retrieval and usage."""
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Container for quality metrics."""
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    utilization: float = 0.0
    hallucination_rate: float = 0.0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'precision': self.precision,
            'recall': self.recall,
            'f1': self.f1,
            'utilization': self.utilization,
            'hallucination_rate': self.hallucination_rate,
            'latency_ms': self.latency_ms
        }

class ContextQualityMonitor:
    """
    Monitor quality of retrieved context and LLM responses.
    
    Tracks:
    - Retrieval precision/recall
    - Context utilization
    - Hallucination detection
    - Query latency
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        # Rolling windows for metrics
        self.metrics = {
            'retrieval_precision': deque(maxlen=window_size),
            'retrieval_recall': deque(maxlen=window_size),
            'latency': deque(maxlen=window_size),
            'context_utilization': deque(maxlen=window_size),
            'hallucination_rate': deque(maxlen=window_size)
        }
        
        logger.info(f"Initialized ContextQualityMonitor with window_size={window_size}")
    
    async def evaluate_retrieval(
        self, 
        query: str,
        retrieved_contexts: List[Dict[str, Any]], 
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> QualityMetrics:
        """
        Evaluate quality of retrieved contexts.
        
        Args:
            query: The search query
            retrieved_contexts: List of retrieved context chunks
            ground_truth: Optional ground truth for evaluation
            
        Returns:
            QualityMetrics with precision, recall, and F1
        """
        if not ground_truth or 'relevant_ids' not in ground_truth:
            logger.warning("No ground truth provided, skipping retrieval evaluation")
            return QualityMetrics()
        
        # Precision: How many retrieved contexts were actually relevant?
        relevant_retrieved = [
            c for c in retrieved_contexts 
            if c.get('id') in ground_truth['relevant_ids']
        ]
        precision = len(relevant_retrieved) / len(retrieved_contexts) if retrieved_contexts else 0
        
        # Recall: How many relevant contexts were retrieved?
        recall = len(relevant_retrieved) / len(ground_truth['relevant_ids']) if ground_truth['relevant_ids'] else 0
        
        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
        
        # Update rolling metrics
        self.metrics['retrieval_precision'].append(precision)
        self.metrics['retrieval_recall'].append(recall)
        
        logger.debug(f"Retrieval quality: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
        
        return QualityMetrics(precision=precision, recall=recall, f1=f1)
    
    async def monitor_context_usage(
        self, 
        contexts: List[Dict[str, Any]], 
        response: str, 
        attention_weights: Optional[np.ndarray] = None
    ) -> QualityMetrics:
        """
        Monitor how retrieved context was actually used in the response.
        
        Args:
            contexts: Retrieved context chunks
            response: Generated response
            attention_weights: Optional attention weights from model
            
        Returns:
            QualityMetrics with utilization and hallucination metrics
        """
        if not contexts:
            logger.warning("No contexts provided for usage monitoring")
            return QualityMetrics()
        
        # Context utilization via attention weights
        utilization_rate = 0.0
        if attention_weights is not None:
            context_attention = {}
            for i, context in enumerate(contexts):
                try:
                    avg_attention = attention_weights[:, i].mean().item()
                except:
                    avg_attention = 0.0
                    
                context_attention[context.get('id', i)] = avg_attention
            
            # Utilization: % of contexts that were actually attended to
            utilized = sum(1 for att in context_attention.values() if att > 0.1)
            utilization_rate = utilized / len(contexts) if contexts else 0
        else:
            # Fallback: simple text overlap
            utilization_rate = self._estimate_utilization_via_overlap(contexts, response)
        
        self.metrics['context_utilization'].append(utilization_rate)
        
        # Check for hallucinations
        hallucination_rate = await self._detect_hallucinations(contexts, response)
        self.metrics['hallucination_rate'].append(hallucination_rate)
        
        logger.debug(
            f"Context usage: utilization={utilization_rate:.3f}, "
            f"hallucination={hallucination_rate:.3f}"
        )
        
        return QualityMetrics(
            utilization=utilization_rate,
            hallucination_rate=hallucination_rate
        )
    
    def _estimate_utilization_via_overlap(
        self, 
        contexts: List[Dict[str, Any]], 
        response: str
    ) -> float:
        """Estimate utilization by checking text overlap."""
        response_words = set(response.lower().split())
        
        utilized_contexts = 0
        for ctx in contexts:
            context_text = ctx.get('content', ctx.get('text', ''))
            context_words = set(context_text.lower().split())
            
            # Check for significant overlap (>10% of context words in response)
            overlap = len(response_words & context_words)
            if overlap > len(context_words) * 0.1:
                utilized_contexts += 1
        
        return utilized_contexts / len(contexts) if contexts else 0

    async def _detect_hallucinations(
        self, 
        contexts: List[Dict[str, Any]], 
        response: str
    ) -> float:
        """
        Detect potential hallucinations by checking if response content 
        is supported by retrieved contexts.
        
        Uses N-gram overlap heuristic.
        """
        if not contexts:
            return 1.0 if response else 0.0
            
        # Combine all context text
        context_text = " ".join([
            c.get('content', c.get('text', '')) for c in contexts
        ]).lower()
        response_text = response.lower()
        
        # Extract unique bigrams from response
        words = response_text.split()
        if len(words) < 2:
            return 0.0
            
        response_bigrams = set(zip(words, words[1:]))
        
        # Check how many bigrams appear in context
        supported_bigrams = 0
        for bigram in response_bigrams:
            bigram_str = " ".join(bigram)
            if bigram_str in context_text:
                supported_bigrams += 1
                
        support_rate = supported_bigrams / len(response_bigrams)
        
        # Hallucination rate is inverse of support rate
        return 1.0 - support_rate
    
    def get_summary_stats(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        stats = {}
        
        for metric_name, values in self.metrics.items():
            if not values:
                stats[metric_name] = {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
                continue
                
            values_array = np.array(list(values))
            stats[metric_name] = {
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'p50': float(np.percentile(values_array, 50)),
                'p95': float(np.percentile(values_array, 95))
            }
        
        return stats
    
    def log_summary(self):
        """Log summary statistics."""
        stats = self.get_summary_stats()
        logger.info("=== Context Quality Summary ===")
        for metric, values in stats.items():
            logger.info(
                f"{metric}: mean={values['mean']:.3f}, "
                f"p95={values.get('p95', 0):.3f}, "
                f"std={values['std']:.3f}"
            )

