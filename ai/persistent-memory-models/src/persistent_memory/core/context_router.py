import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RouterNetwork(nn.Module):
    """
    Neural Policy Network for Context Routing.
    Uses query embeddings to predict relevance of different memory layers.
    """

    def __init__(
        self, input_dim: int = 1536, num_layers: int = 4, hidden_dim: int = 256
    ):
        super().__init__()
        self.num_layers = num_layers
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_layers),
        )
        self.optimizer = optim.Adam(self.parameters(), lr=1e-3)
        self.last_probs = None

    def forward(self, query_embedding: torch.Tensor) -> torch.Tensor:
        """Predict probabilities for each memory layer."""
        logits = self.network(query_embedding)
        probs = F.softmax(logits, dim=-1)
        return probs

    def predict(self, query_embedding: np.ndarray) -> np.ndarray:
        """Predictive step for inference."""
        self.eval()
        with torch.no_grad():
            emb = torch.FloatTensor(query_embedding).unsqueeze(0)
            probs = self.forward(emb)
            self.last_probs = probs  # Save for update
            return probs.squeeze(0).numpy()

    def update(self, query_embedding: np.ndarray, reward: float):
        """
        Policy Gradient update using reward signal.
        Reward is derived from quality metrics and latency.
        """
        if self.last_probs is None:
            return

        self.train()
        self.optimizer.zero_grad()

        # We want to maximize: reward * log(probs)
        # PyTorch optimizers minimize loss, so we use: -reward * log(probs)
        emb = torch.FloatTensor(query_embedding).unsqueeze(0)
        probs = self.forward(emb)

        # Simple policy gradient reinforcement of the action taken
        # (Assuming all chosen layers contributed to the reward)
        loss = -reward * torch.log(probs + 1e-10).mean()

        loss.backward()
        self.optimizer.step()

        logger.debug(f"Router update loss: {loss.item():.4f}, reward: {reward:.4f}")


class ContextRouter:
    """
    Intelligently routes queries to appropriate memory layers
    Learns optimal routing policy over time
    """

    def __init__(self, layers):
        self.working_memory = layers[0]
        self.episodic = layers[1]
        self.semantic = layers[2]
        self.archive = layers[3]

        # Routing policy (learned)
        self.router = RouterNetwork(
            input_dim=1536,  # Typical embedding dimension (e.g. OpenAI/Mistral)
            num_layers=4,
        )

        # Statistics for adaptive routing
        self.stats = {
            "layer_hit_rates": [0.0, 0.0, 0.0, 0.0],
            "layer_latencies": [0.0, 0.0, 0.0, 0.0],
            "total_rewards": 0.0,
        }

    async def route_query(
        self,
        query: str,
        query_embedding: np.ndarray | None = None,
        max_results: int = 10,
    ):
        """
        Intelligently route query to appropriate layers based on neural prediction.
        """
        # If no embedding provided, use a random one (placeholder until integrated with encoder)
        if query_embedding is None:
            logger.warning("No query embedding provided to router, using placeholder.")
            query_embedding = np.random.randn(1536).astype(np.float32)

        # Predict optimal layers to query
        layer_probs = self.router.predict(query_embedding)

        # Query layers in parallel
        results = {}

        # 1. Working Memory (Always query, lowest latency)
        if hasattr(self.working_memory, "get_current_context"):
            results["working"] = self.working_memory.get_current_context()
        else:
            results["working"] = []

        # 2. Episodic Memory (Threshold 0.25)
        if layer_probs[1] > 0.25:
            results["episodic"] = self.episodic.search(query, k=max_results // 2)

        # 3. Semantic Memory (Threshold 0.25)
        if layer_probs[2] > 0.25:
            if hasattr(self.semantic, "query"):
                results["semantic"] = self.semantic.query(query)
            else:
                results["semantic"] = []

        # 4. Archive (Threshold 0.2, most expensive)
        if layer_probs[3] > 0.2:
            if hasattr(self.archive, "retrieve"):
                results["archive"] = self.archive.retrieve(query, k=max_results // 4)
            else:
                results["archive"] = []

        # Merge and rank results
        merged_results = self._merge_and_rank(results, query)

        return merged_results

    def update(self, query_embedding: np.ndarray, reward: float):
        """
        Public method to update the routing policy based on performance.
        """
        self.router.update(query_embedding, reward)
        self.stats["total_rewards"] += reward

    def _merge_and_rank(self, layer_results, query):
        """
        Merge results from different layers and rank by relevance
        """
        all_results = []

        for layer, results in layer_results.items():
            if not results:
                continue

            for result in results:
                # Compute unified relevance score
                relevance = self._compute_relevance(result, query, layer)

                all_results.append(
                    {
                        "content": result,
                        "relevance": relevance,
                        "layer": layer,
                        "recency": self._compute_recency(result),
                        "importance": self._compute_importance(result),
                    }
                )

        # Multi-factor ranking: Combination of relevance, recency and importance
        all_results.sort(
            key=lambda x: (
                0.5 * x["relevance"] + 0.3 * x["recency"] + 0.2 * x["importance"]
            ),
            reverse=True,
        )

        return all_results

    def _compute_relevance(self, result, query, layer):
        if (
            isinstance(result, dict)
            and "distance" in result
            and result["distance"] is not None
        ):
            return 1.0 / (1.0 + result["distance"])
        return 0.5

    def _compute_recency(self, result):
        # Could be enhanced with actual timestamp metadata
        return 0.8

    def _compute_importance(self, result):
        # Could be enhanced with fact-specific weights
        return 0.7
