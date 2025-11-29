import os
from typing import Any

import chromadb


class PersistentVectorStore:
    """
    Wrapper around ChromaDB for persistent vector storage.
    """

    def __init__(self, collection_name: str = "persistent_memory"):
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = os.getenv("CHROMA_PORT", "8000")

        self.client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_texts(self, texts: list[str], metadatas: list[dict[str, Any]], ids: list[str]):
        """
        Add texts to the vector store.
        """
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def add_text(self, text: str, metadata: dict[str, Any] | None = None, id: str | None = None):
        """
        Add a single text to the vector store.
        """
        import uuid

        if id is None:
            id = str(uuid.uuid4())
        if metadata is None:
            metadata = {}

        self.add_texts([text], [metadata], [id])

    def search(self, query_text: str, k: int = 5) -> list[dict[str, Any]]:
        """
        Semantic search for relevant texts.
        """
        results = self.collection.query(query_texts=[query_text], n_results=k)

        # Format results
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                    }
                )

        return formatted_results
