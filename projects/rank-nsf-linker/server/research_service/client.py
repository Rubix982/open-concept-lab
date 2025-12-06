"""Qdrant client for vector storage and search."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
import uuid
import logging
import numpy as np

from .config import config

logger = logging.getLogger(__name__)


class QdrantService:
    """Qdrant vector database service."""
    
    def __init__(self):
        self.client = QdrantClient(host=config.host, port=config.port)
        self.collection_name = config.collection_name
        logger.info(f"Connected to Qdrant at {config.host}:{config.port}")
    
    def create_collection(self, vector_size: int = None):
        """
        Create Qdrant collection for faculty research.
        
        Args:
            vector_size: Dimension of vectors (default from config)
        """
        vector_size = vector_size or config.vector_size
        
        # Check if collection exists
        collections = self.client.get_collections().collections
        if any(c.name == self.collection_name for c in collections):
            logger.info(f"Collection '{self.collection_name}' already exists")
            return
        
        # Create collection
        logger.info(f"Creating collection '{self.collection_name}' with dimension {vector_size}")
        
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        
        logger.info(f"Collection '{self.collection_name}' created successfully")
    
    def ingest_batch(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict]
    ) -> int:
        """
        Ingest batch of embeddings with metadata.
        
        Args:
            embeddings: Array of embeddings (shape: [n, dimension])
            metadata: List of metadata dicts for each embedding
            
        Returns:
            Number of points ingested
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")
        
        logger.info(f"Ingesting {len(embeddings)} vectors to Qdrant...")
        
        # Create points
        points = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Create point
            points.append(PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=meta
            ))
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Successfully ingested {len(points)} vectors")
        return len(points)
    
    def search(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar research content.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            filters: Optional filters (e.g., {'university': 'MIT'})
            
        Returns:
            List of search results with scores and metadata
        """
        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit,
            query_filter=query_filter
        )
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                'score': result.score,
                'metadata': result.payload
            })
        
        return formatted
    
    def delete_collection(self):
        """Delete the collection (for testing/reset)."""
        logger.warning(f"Deleting collection '{self.collection_name}'")
        self.client.delete_collection(collection_name=self.collection_name)
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        info = self.client.get_collection(collection_name=self.collection_name)
        return {
            'name': info.name,
            'vectors_count': info.vectors_count,
            'points_count': info.points_count,
            'status': info.status
        }


# Global instance
qdrant_service = QdrantService()
