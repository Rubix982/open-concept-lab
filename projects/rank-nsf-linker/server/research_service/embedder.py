"""Embedding generation using sentence-transformers."""
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np
import logging

from .config import config

logger = logging.getLogger(__name__)
# from .config import config # This line will be moved
# logger = logging.getLogger(__name__)


class ResearchEmbedder:
    """Generate embeddings for research content."""
    
    def __init__(self, model_name: str = None):
        from .config import config
        self.model_name = model_name or config.model_name
        logger.info(f"Loading embedding model: {self.model_name}")
        
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.batch_size = config.batch_size
        
        logger.info(f"Model loaded. Dimension: {self.dimension}")
    
    def prepare_text(self, content: Dict) -> str:
        """
        Prepare text for embedding.
        
        Combines title and content with proper formatting.
        """
        parts = []
        
        # Add title if available
        if content.get('title'):
            parts.append(f"Title: {content['title']}")
        
        # Add content (truncate to max length)
        if content.get('content'):
            # Truncate to ~2000 chars (roughly 512 tokens)
            text = content['content'][:2000]
            parts.append(text)
        
        return ' '.join(parts)
    
    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode(text, show_progress_bar=False)
    
    def embed_batch(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings (shape: [len(texts), dimension])
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def embed_content_batch(self, content_list: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for a batch of content dictionaries.
        
        Args:
            content_list: List of content dicts with 'title' and 'content'
            
        Returns:
            Array of embeddings
        """
        # Prepare texts
        texts = [self.prepare_text(content) for content in content_list]
        
        # Filter out empty texts
        valid_indices = [i for i, text in enumerate(texts) if text.strip()]
        valid_texts = [texts[i] for i in valid_indices]
        
        if not valid_texts:
            logger.warning("No valid texts to embed")
            return np.array([])
        
        # Generate embeddings
        embeddings = self.embed_batch(valid_texts)
        
        # Create full array with zeros for invalid texts
        full_embeddings = np.zeros((len(texts), self.dimension))
        for i, idx in enumerate(valid_indices):
            full_embeddings[idx] = embeddings[i]
        
        return full_embeddings
