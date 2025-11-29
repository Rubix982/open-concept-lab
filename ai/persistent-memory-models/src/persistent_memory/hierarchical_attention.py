"""
Hierarchical Attention Mechanism for Context Selection.

Implements multi-level attention inspired by:
- "Hierarchical Attention Networks for Document Classification" (Yang et al., 2016)
- "Attention Is All You Need" (Vaswani et al., 2017)

Architecture:
    Query → [Chunk Attention] → [Sentence Attention] → [Token Attention] → Weighted Context
    
Levels:
    1. Chunk-level: Which retrieved chunks are most relevant?
    2. Sentence-level: Within chunks, which sentences matter?
    3. Token-level: Within sentences, which tokens are key?
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AttentionConfig:
    """Configuration for hierarchical attention."""
    embedding_dim: int = 384  # Sentence embedding dimension
    hidden_dim: int = 256
    num_heads: int = 8
    dropout: float = 0.1
    max_chunks: int = 20
    max_sentences_per_chunk: int = 10
    temperature: float = 1.0  # Softmax temperature


class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism."""
    
    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        # Linear projections
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self, 
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query: (batch, seq_len_q, embed_dim)
            key: (batch, seq_len_k, embed_dim)
            value: (batch, seq_len_k, embed_dim)
            mask: (batch, seq_len_q, seq_len_k) or None
            
        Returns:
            output: (batch, seq_len_q, embed_dim)
            attention_weights: (batch, num_heads, seq_len_q, seq_len_k)
        """
        batch_size = query.size(0)
        
        # Project and reshape for multi-head attention
        Q = self.q_proj(query).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.k_proj(key).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(value).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            scores = scores.masked_fill(mask.unsqueeze(1) == 0, float('-inf'))
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        context = torch.matmul(attn_weights, V)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.embed_dim)
        output = self.out_proj(context)
        
        return output, attn_weights


class ChunkLevelAttention(nn.Module):
    """
    Chunk-level attention: Which retrieved chunks are most relevant?
    
    Input: Query embedding + Chunk embeddings
    Output: Attention weights over chunks
    """
    
    def __init__(self, config: AttentionConfig):
        super().__init__()
        self.config = config
        
        self.attention = MultiHeadAttention(
            config.embedding_dim,
            config.num_heads,
            config.dropout
        )
        
        # Learnable query transformation
        self.query_transform = nn.Sequential(
            nn.Linear(config.embedding_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.embedding_dim)
        )
        
        # Context aggregation
        self.context_aggregator = nn.Sequential(
            nn.Linear(config.embedding_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, 1)
        )
        
    def forward(
        self,
        query_embedding: torch.Tensor,
        chunk_embeddings: torch.Tensor,
        chunk_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query_embedding: (batch, embed_dim)
            chunk_embeddings: (batch, num_chunks, embed_dim)
            chunk_mask: (batch, num_chunks) - 1 for valid, 0 for padding
            
        Returns:
            weighted_chunks: (batch, embed_dim)
            chunk_attention: (batch, num_chunks)
        """
        # Transform query
        query = self.query_transform(query_embedding).unsqueeze(1)  # (batch, 1, embed_dim)
        
        # Multi-head attention
        attended, attn_weights = self.attention(
            query, 
            chunk_embeddings, 
            chunk_embeddings,
            mask=chunk_mask
        )
        
        # Aggregate attention scores
        chunk_scores = self.context_aggregator(chunk_embeddings).squeeze(-1)  # (batch, num_chunks)
        
        if chunk_mask is not None:
            chunk_scores = chunk_scores.masked_fill(chunk_mask == 0, float('-inf'))
        
        chunk_attention = F.softmax(chunk_scores / self.config.temperature, dim=-1)
        
        # Weighted sum of chunks
        weighted_chunks = torch.bmm(
            chunk_attention.unsqueeze(1),
            chunk_embeddings
        ).squeeze(1)
        
        return weighted_chunks, chunk_attention


class SentenceLevelAttention(nn.Module):
    """
    Sentence-level attention: Within selected chunks, which sentences matter?
    """
    
    def __init__(self, config: AttentionConfig):
        super().__init__()
        self.config = config
        
        self.attention = MultiHeadAttention(
            config.embedding_dim,
            config.num_heads,
            config.dropout
        )
        
        # Sentence importance scorer
        self.sentence_scorer = nn.Sequential(
            nn.Linear(config.embedding_dim * 2, config.hidden_dim),  # Concat query + sentence
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, 1)
        )
        
    def forward(
        self,
        query_embedding: torch.Tensor,
        sentence_embeddings: torch.Tensor,
        sentence_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query_embedding: (batch, embed_dim)
            sentence_embeddings: (batch, num_sentences, embed_dim)
            sentence_mask: (batch, num_sentences)
            
        Returns:
            weighted_sentences: (batch, embed_dim)
            sentence_attention: (batch, num_sentences)
        """
        batch_size, num_sentences, _ = sentence_embeddings.shape
        
        # Expand query for concatenation
        query_expanded = query_embedding.unsqueeze(1).expand(-1, num_sentences, -1)
        
        # Concatenate query with each sentence
        combined = torch.cat([query_expanded, sentence_embeddings], dim=-1)
        
        # Score each sentence
        sentence_scores = self.sentence_scorer(combined).squeeze(-1)
        
        if sentence_mask is not None:
            sentence_scores = sentence_scores.masked_fill(sentence_mask == 0, float('-inf'))
        
        sentence_attention = F.softmax(sentence_scores / self.config.temperature, dim=-1)
        
        # Weighted sum
        weighted_sentences = torch.bmm(
            sentence_attention.unsqueeze(1),
            sentence_embeddings
        ).squeeze(1)
        
        return weighted_sentences, sentence_attention


class HierarchicalAttentionNetwork(nn.Module):
    """
    Full hierarchical attention network.
    
    Combines chunk-level and sentence-level attention for intelligent context selection.
    """
    
    def __init__(self, config: AttentionConfig):
        super().__init__()
        self.config = config
        
        self.chunk_attention = ChunkLevelAttention(config)
        self.sentence_attention = SentenceLevelAttention(config)
        
        # Final context fusion
        self.context_fusion = nn.Sequential(
            nn.Linear(config.embedding_dim * 2, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.embedding_dim)
        )
        
        logger.info(f"Initialized HierarchicalAttentionNetwork: {config}")
    
    def forward(
        self,
        query_embedding: torch.Tensor,
        chunk_embeddings: torch.Tensor,
        sentence_embeddings: torch.Tensor,
        chunk_mask: Optional[torch.Tensor] = None,
        sentence_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            query_embedding: (batch, embed_dim)
            chunk_embeddings: (batch, num_chunks, embed_dim)
            sentence_embeddings: (batch, num_sentences, embed_dim)
            chunk_mask: (batch, num_chunks)
            sentence_mask: (batch, num_sentences)
            
        Returns:
            Dictionary containing:
                - final_context: (batch, embed_dim)
                - chunk_attention: (batch, num_chunks)
                - sentence_attention: (batch, num_sentences)
        """
        # Level 1: Chunk attention
        chunk_context, chunk_attn = self.chunk_attention(
            query_embedding,
            chunk_embeddings,
            chunk_mask
        )
        
        # Level 2: Sentence attention
        sentence_context, sentence_attn = self.sentence_attention(
            query_embedding,
            sentence_embeddings,
            sentence_mask
        )
        
        # Fuse both levels
        combined_context = torch.cat([chunk_context, sentence_context], dim=-1)
        final_context = self.context_fusion(combined_context)
        
        return {
            'final_context': final_context,
            'chunk_attention': chunk_attn,
            'sentence_attention': sentence_attn,
            'chunk_context': chunk_context,
            'sentence_context': sentence_context
        }
    
    def get_attention_weights(self, outputs: Dict[str, torch.Tensor]) -> Dict[str, np.ndarray]:
        """Extract attention weights as numpy arrays for visualization."""
        return {
            'chunk_attention': outputs['chunk_attention'].detach().cpu().numpy(),
            'sentence_attention': outputs['sentence_attention'].detach().cpu().numpy()
        }


# Training utilities
class AttentionTrainer:
    """Train the hierarchical attention network."""
    
    def __init__(
        self,
        model: HierarchicalAttentionNetwork,
        learning_rate: float = 1e-4,
        device: str = 'cpu'
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
    def train_step(
        self,
        query_emb: torch.Tensor,
        chunk_embs: torch.Tensor,
        sentence_embs: torch.Tensor,
        target_context: torch.Tensor
    ) -> float:
        """Single training step."""
        self.model.train()
        self.optimizer.zero_grad()
        
        outputs = self.model(query_emb, chunk_embs, sentence_embs)
        loss = self.criterion(outputs['final_context'], target_context)
        
        loss.backward()
        self.optimizer.step()
        
        return loss.item()


if __name__ == "__main__":
    # Demo
    config = AttentionConfig()
    model = HierarchicalAttentionNetwork(config)
    
    # Dummy data
    batch_size = 2
    query_emb = torch.randn(batch_size, config.embedding_dim)
    chunk_embs = torch.randn(batch_size, 10, config.embedding_dim)
    sentence_embs = torch.randn(batch_size, 50, config.embedding_dim)
    
    outputs = model(query_emb, chunk_embs, sentence_embs)
    
    print("Output shapes:")
    for k, v in outputs.items():
        print(f"  {k}: {v.shape}")
    
    print("\nAttention weights:")
    weights = model.get_attention_weights(outputs)
    print(f"  Chunk attention: {weights['chunk_attention'][0]}")
    print(f"  Top 3 chunks: {np.argsort(weights['chunk_attention'][0])[-3:]}")
