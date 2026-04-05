"""
Step 6 — Retriever Module
Embeds a user query and retrieves the top-k relevant chunks from the vector store.
"""

from src.embeddings import EmbeddingModel
from src.vector_store import VectorStore


class Retriever:
    """Retrieves relevant document chunks for a given query."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: VectorStore, top_k: int = 3):
        """Initialize the retriever.
        
        Args:
            embedding_model: Initialized EmbeddingModel instance
            vector_store:    Populated VectorStore instance
            top_k:           Number of results to retrieve
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str, k: int = None) -> list[dict]:
        """Retrieve relevant chunks for a user query.
        
        Steps:
          1. Embed the query
          2. Search the FAISS index
          3. Return top-k results
        
        Args:
            query: User's question string
            k:     Override for number of results (defaults to self.top_k)
        
        Returns:
            List of dicts with 'text', 'source', 'score' fields
        """
        if k is None:
            k = self.top_k

        # Step 1: Embed the query
        query_embedding = self.embedding_model.embed_text(query)

        # Step 2 & 3: Search FAISS and return results
        results = self.vector_store.search(query_embedding, k=k)

        return results

    def get_context_string(self, query: str, k: int = None) -> str:
        """Retrieve chunks and format them as a single context string.
        
        Args:
            query: User's question string
            k:     Override for number of results
        
        Returns:
            Formatted context string for the LLM prompt
        """
        results = self.retrieve(query, k)

        if not results:
            return "No relevant information found."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] (Source: {result['source']})\n{result['text']}")

        return "\n\n".join(context_parts)
