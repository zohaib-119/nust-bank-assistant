"""
Step 4 — Embedding Generation Module
Generates vector embeddings using sentence-transformers/all-MiniLM-L6-v2.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import warnings
import logging

# Suppress the BertModel position_ids warning
warnings.filterwarnings('ignore', message='.*position_ids.*')
logging.getLogger('transformers').setLevel(logging.ERROR)

# Default embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModel:
    """Wrapper for the sentence-transformers embedding model."""

    def __init__(self, model_name: str = MODEL_NAME):
        """Initialize the embedding model.
        
        Args:
            model_name: HuggingFace model name for sentence-transformers
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.dimension}")

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text string.
        
        Args:
            text: Input text
        
        Returns:
            Numpy array of shape (dimension,)
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts.
        
        Args:
            texts:      List of input texts
            batch_size: Batch size for encoding
        
        Returns:
            Numpy array of shape (num_texts, dimension)
        """
        return self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=True)

    def embed_chunks(self, chunks: list[dict], batch_size: int = 32) -> tuple[np.ndarray, list[dict]]:
        """Generate embeddings for document chunks.
        
        Args:
            chunks:     List of chunk dicts with 'text' and 'source' fields
            batch_size: Batch size for encoding
        
        Returns:
            Tuple of (embeddings array, chunk metadata list)
        """
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed_texts(texts, batch_size)

        metadata = []
        for chunk in chunks:
            metadata.append({
                "text": chunk["text"],
                "source": chunk["source"]
            })

        return embeddings, metadata


if __name__ == "__main__":
    # Quick test
    model = EmbeddingModel()
    test_texts = [
        "How do I reset my debit card PIN?",
        "What are the transfer limits?",
        "Tell me about savings accounts."
    ]
    embeddings = model.embed_texts(test_texts)
    print(f"Shape: {embeddings.shape}")
    print(f"First embedding (first 5 dims): {embeddings[0][:5]}")
