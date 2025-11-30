"""
Training script for hierarchical attention mechanism.

Trains the attention network on query-context pairs to learn
which contexts are most relevant for different query types.
"""

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader, Dataset

from persistent_memory.hierarchical_attention import AttentionConfig, HierarchicalAttentionNetwork
from persistent_memory.persistent_vector_store import PersistentVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AttentionTrainingDataset(Dataset):
    """Dataset for training attention mechanism."""

    def __init__(
        self,
        queries: list[str],
        contexts_per_query: list[list[str]],
        relevance_scores: list[list[float]],
        encoder: SentenceTransformer,
    ):
        """
        Args:
            queries: List of query strings
            contexts_per_query: List of context lists (one per query)
            relevance_scores: Relevance scores for each context
            encoder: Sentence encoder
        """
        self.queries = queries
        self.contexts = contexts_per_query
        self.relevance = relevance_scores
        self.encoder = encoder

        assert len(queries) == len(contexts_per_query) == len(relevance_scores)

    def __len__(self):
        return len(self.queries)

    def __getitem__(self, idx):
        query = self.queries[idx]
        contexts = self.contexts[idx]
        relevance = self.relevance[idx]

        # Encode query
        query_emb = self.encoder.encode(query, convert_to_numpy=True)

        # Encode contexts (chunks)
        chunk_embs = self.encoder.encode(contexts, convert_to_numpy=True)

        # Extract sentences from contexts
        all_sentences = []
        for context in contexts:
            sentences = self._split_sentences(context)
            all_sentences.extend(sentences[:10])  # Max 10 sentences per chunk

        sentence_embs = self.encoder.encode(all_sentences, convert_to_numpy=True)

        # Pad to fixed size
        max_chunks = 20
        max_sentences = 100

        chunk_embs_padded = np.zeros((max_chunks, chunk_embs.shape[1]))
        chunk_embs_padded[: len(chunk_embs)] = chunk_embs

        sentence_embs_padded = np.zeros((max_sentences, sentence_embs.shape[1]))
        sentence_embs_padded[: len(sentence_embs)] = sentence_embs

        relevance_padded = np.zeros(max_chunks)
        relevance_padded[: len(relevance)] = relevance

        return {
            "query_emb": torch.FloatTensor(query_emb),
            "chunk_embs": torch.FloatTensor(chunk_embs_padded),
            "sentence_embs": torch.FloatTensor(sentence_embs_padded),
            "relevance": torch.FloatTensor(relevance_padded),
            "num_chunks": len(contexts),
            "num_sentences": len(all_sentences),
        }

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re

        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]


class AttentionTrainer:
    """Trainer for hierarchical attention network."""

    def __init__(
        self, model: HierarchicalAttentionNetwork, learning_rate: float = 1e-4, device: str = "cpu"
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

        # Loss: Combination of ranking loss and attention supervision
        self.ranking_loss = nn.MarginRankingLoss(margin=0.1)
        self.mse_loss = nn.MSELoss()

        logger.info(f"Initialized trainer on device: {device}")

    def train_epoch(self, dataloader: DataLoader, epoch: int) -> dict[str, float]:
        """Train for one epoch."""
        self.model.train()

        total_loss = 0.0
        total_ranking_loss = 0.0
        total_attention_loss = 0.0

        for batch_idx, batch in enumerate(dataloader):
            # Move to device
            query_emb = batch["query_emb"].to(self.device)
            chunk_embs = batch["chunk_embs"].to(self.device)
            sentence_embs = batch["sentence_embs"].to(self.device)
            relevance = batch["relevance"].to(self.device)

            # Forward pass
            outputs = self.model(query_emb, chunk_embs, sentence_embs)

            # Loss 1: Attention should match relevance scores
            chunk_attention = outputs["chunk_attention"]
            attention_loss = self.mse_loss(chunk_attention, relevance)

            # Loss 2: Ranking loss (relevant chunks should have higher attention)
            # Create pairs of (relevant, irrelevant) chunks
            batch_size = relevance.size(0)
            ranking_losses = []

            for i in range(batch_size):
                rel_scores = relevance[i]
                attn_scores = chunk_attention[i]

                # Find positive and negative examples
                pos_mask = rel_scores > 0.5
                neg_mask = rel_scores < 0.3

                if pos_mask.sum() > 0 and neg_mask.sum() > 0:
                    pos_attn = attn_scores[pos_mask].mean()
                    neg_attn = attn_scores[neg_mask].mean()

                    # Positive should have higher attention
                    target = torch.ones(1).to(self.device)
                    ranking_loss = self.ranking_loss(
                        pos_attn.unsqueeze(0), neg_attn.unsqueeze(0), target
                    )
                    ranking_losses.append(ranking_loss)

            if ranking_losses:
                ranking_loss_val = torch.stack(ranking_losses).mean()
            else:
                ranking_loss_val = torch.tensor(0.0).to(self.device)

            # Combined loss
            loss = attention_loss + 0.5 * ranking_loss_val

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

            # Track losses
            total_loss += float(loss.item())
            total_ranking_loss += float(ranking_loss_val.item())
            total_attention_loss += float(attention_loss.item())

            if batch_idx % 10 == 0:
                logger.info(
                    f"Epoch {epoch} [{batch_idx}/{len(dataloader)}] "
                    f"Loss: {loss.item():.4f} "
                    f"(Attn: {attention_loss.item():.4f}, "
                    f"Rank: {ranking_loss_val.item():.4f})"
                )

        return {
            "total_loss": total_loss / len(dataloader),
            "ranking_loss": total_ranking_loss / len(dataloader),
            "attention_loss": total_attention_loss / len(dataloader),
        }

    def save_checkpoint(self, path: str, epoch: int, metrics: dict):
        """Save model checkpoint."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "metrics": metrics,
        }
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint to {path}")


def create_synthetic_training_data(
    vector_store: PersistentVectorStore, num_queries: int = 100
) -> tuple[list[str], list[list[str]], list[list[float]]]:
    """
    Create synthetic training data from vector store.

    Uses distance-based relevance as supervision signal.
    """
    # Sample queries (in practice, use real user queries)
    sample_queries = [
        "Who is Elizabeth Bennet?",
        "What is Mr. Darcy's character?",
        "Describe the Bennet family",
        "What happens at Netherfield?",
        "How does the story end?",
        # Add more diverse queries...
    ]

    queries = []
    contexts_list = []
    relevance_list = []

    for query in sample_queries[:num_queries]:
        results = vector_store.search(query, k=20)

        if not results:
            continue

        contexts = [r.get("text", "") for r in results]
        distances = [r.get("distance", 1.0) for r in results]

        # Convert distances to relevance (inverse and normalize)
        max_dist = max(distances) if distances else 1.0
        relevance = [1.0 - (d / max_dist) for d in distances]

        queries.append(query)
        contexts_list.append(contexts)
        relevance_list.append(relevance)

    return queries, contexts_list, relevance_list


def main():
    """Main training script."""
    # Configuration
    config = AttentionConfig(embedding_dim=384, hidden_dim=256, num_heads=8, dropout=0.1)

    # Initialize model
    model = HierarchicalAttentionNetwork(config)

    # Create training data
    logger.info("Creating training data...")
    vector_store = PersistentVectorStore()
    queries, contexts, relevance = create_synthetic_training_data(vector_store)

    logger.info(f"Created {len(queries)} training examples")

    # Create dataset
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    dataset = AttentionTrainingDataset(queries, contexts, relevance, encoder)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    # Initialize trainer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trainer = AttentionTrainer(model, learning_rate=1e-4, device=device)

    # Training loop
    num_epochs = 10
    best_loss = float("inf")

    for epoch in range(num_epochs):
        logger.info(f"\n{'=' * 50}")
        logger.info(f"Epoch {epoch + 1}/{num_epochs}")
        logger.info(f"{'=' * 50}")

        metrics = trainer.train_epoch(dataloader, epoch)

        logger.info(f"\nEpoch {epoch + 1} Summary:")
        logger.info(f"  Total Loss: {metrics['total_loss']:.4f}")
        logger.info(f"  Ranking Loss: {metrics['ranking_loss']:.4f}")
        logger.info(f"  Attention Loss: {metrics['attention_loss']:.4f}")

        # Save best model
        if metrics["total_loss"] < best_loss:
            best_loss = metrics["total_loss"]
            trainer.save_checkpoint("models/attention_best.pt", epoch, metrics)

    logger.info("\nTraining complete!")


if __name__ == "__main__":
    # Create models directory
    Path("models").mkdir(exist_ok=True)
    main()
