"""Context compression using autoencoders."""

import logging

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as torch_functional
import torch.optim as optim

logger = logging.getLogger(__name__)


class ContextAutoencoder(nn.Module):
    """
    Variational Autoencoder for compressing context embeddings.

    Learns to compress high-dimensional embeddings (e.g., 1536-dim)
    into compact latent representations (e.g., 128-dim) while preserving
    semantic information.
    """

    def __init__(
        self, input_dim: int = 1536, latent_dim: int = 128, architecture: str = "variational"
    ):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.architecture = architecture

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 768),
            nn.LayerNorm(768),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(768, 384),
            nn.LayerNorm(384),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(384, latent_dim * 2 if architecture == "variational" else latent_dim),
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 384),
            nn.LayerNorm(384),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(384, 768),
            nn.LayerNorm(768),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(768, input_dim),
        )

        self.optimizer = optim.Adam(self.parameters(), lr=1e-4)
        logger.info(f"Initialized {architecture} autoencoder: {input_dim} -> {latent_dim}")

    def encode(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
        """
        Encode input to latent space.

        Returns:
            - latent representation
            - mu (if variational)
            - logvar (if variational)
        """
        encoded = self.encoder(x)

        if self.architecture == "variational":
            mu, logvar = torch.chunk(encoded, 2, dim=-1)
            # Reparameterization trick
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            z = mu + eps * std
            return z, mu, logvar
        else:
            return encoded, None, None

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent representation back to original space."""
        return self.decoder(z)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
        """Full forward pass."""
        z, mu, logvar = self.encode(x)
        reconstructed = self.decode(z)
        return reconstructed, mu, logvar

    def compute_loss(
        self,
        x: torch.Tensor,
        reconstructed: torch.Tensor,
        mu: torch.Tensor | None = None,
        logvar: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Compute loss with reconstruction + semantic preservation + KL divergence.
        """
        # Reconstruction loss (MSE)
        reconstruction_loss = torch_functional.mse_loss(reconstructed, x, reduction="mean")

        # Semantic preservation (cosine similarity)
        cosine_sim = torch_functional.cosine_similarity(reconstructed, x, dim=-1).mean()
        semantic_loss = 1 - cosine_sim

        # KL divergence (for VAE)
        kl_loss = 0.0
        if self.architecture == "variational" and mu is not None and logvar is not None:
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=-1).mean()

        # Combined loss
        total_loss = reconstruction_loss + 0.5 * semantic_loss + 0.1 * kl_loss

        return total_loss

    def train_on_embeddings(
        self, embeddings: np.ndarray, epochs: int = 100, batch_size: int = 32
    ) -> list[float]:
        """
        Train autoencoder on a batch of embeddings.

        Args:
            embeddings: Array of shape (n_samples, input_dim)
            epochs: Number of training epochs
            batch_size: Batch size for training

        Returns:
            List of losses per epoch
        """
        self.train()
        embeddings_tensor = torch.FloatTensor(embeddings)
        dataset = torch.utils.data.TensorDataset(embeddings_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        losses = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            for (batch,) in dataloader:
                self.optimizer.zero_grad()

                reconstructed, mu, logvar = self.forward(batch)
                loss = self.compute_loss(batch, reconstructed, mu, logvar)

                loss.backward()
                self.optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)

            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}/{epochs}, Loss: {avg_loss:.4f}")

        logger.info(f"Training complete. Final loss: {losses[-1]:.4f}")
        return losses

    def compress(self, embedding: np.ndarray) -> np.ndarray:
        """Compress a single embedding."""
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(embedding).unsqueeze(0)
            z, _, _ = self.encode(x)
            return z.squeeze(0).numpy()

    def decompress(self, latent: np.ndarray) -> np.ndarray:
        """Decompress a latent representation."""
        self.eval()
        with torch.no_grad():
            z = torch.FloatTensor(latent).unsqueeze(0)
            reconstructed = self.decode(z)
            return reconstructed.squeeze(0).numpy()

    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        return self.input_dim / self.latent_dim
