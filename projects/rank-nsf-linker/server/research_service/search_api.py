"""Search API helper for Go backend."""
import sys
import json
from embeddings.embedder import ResearchEmbedder
from qdrant.client import qdrant_service

def search_faculty(query: str, limit: int = 10, filters: dict = None) -> list:
    """
    Search for faculty by research topic.
    
    Args:
        query: Search query (e.g., "machine learning for healthcare")
        limit: Number of results
        filters: Optional filters (e.g., {'university': 'MIT'})
        
    Returns:
        List of search results with scores and metadata
    """
    # Generate embedding for query
    embedder = ResearchEmbedder()
    query_vector = embedder.embed_single(query)
    
    # Search Qdrant
    results = qdrant_service.search(
        query_vector=query_vector,
        limit=limit,
        filters=filters
    )
    
    return results


if __name__ == '__main__':
    # Read input from stdin (JSON)
    input_data = json.loads(sys.stdin.read())
    
    query = input_data.get('query', '')
    limit = input_data.get('limit', 10)
    filters = input_data.get('filters')
    
    # Perform search
    results = search_faculty(query, limit, filters)
    
    # Output results as JSON
    print(json.dumps(results))
