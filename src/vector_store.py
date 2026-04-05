"""
Step 5 — Vector Store Module (FAISS)
Creates and manages a FAISS index for storing and searching embeddings.
"""

import numpy as np
import faiss
import json
import os


class VectorStore:
    """FAISS-based vector store for document embeddings."""

    def __init__(self, dimension: int):
        """Initialize the vector store.
        
        Args:
            dimension: Dimension of the embedding vectors (384 for MiniLM-L6-v2)
        """
        self.dimension = dimension
        self.index = None
        self.metadata = []  # Stores chunk text and source info
        self._create_index()

    def _create_index(self):
        """Create a new FAISS index using L2 (Euclidean) distance."""
        self.index = faiss.IndexFlatL2(self.dimension)
        print(f"Created FAISS index with dimension {self.dimension}")

    def add_documents(self, embeddings: np.ndarray, metadata: list[dict]):
        """Add document embeddings and metadata to the index.
        
        Args:
            embeddings: Numpy array of shape (num_docs, dimension)
            metadata:   List of dicts with 'text' and 'source' fields
        """
        # Ensure embeddings are float32 (required by FAISS)
        embeddings = np.array(embeddings, dtype=np.float32)

        self.index.add(embeddings)
        self.metadata.extend(metadata)
        print(f"Added {len(metadata)} documents to index. Total: {self.index.ntotal}")

    def search(self, query_embedding: np.ndarray, k: int = 3) -> list[dict]:
        """Search the index for the most similar documents.
        
        Args:
            query_embedding: Query vector of shape (dimension,)
            k:               Number of results to return
        
        Returns:
            List of dicts with 'text', 'source', 'score' fields
        """
        # Ensure correct shape and dtype
        query = np.array([query_embedding], dtype=np.float32)

        # Search FAISS index
        distances, indices = self.index.search(query, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata) and idx >= 0:
                result = {
                    "text": self.metadata[idx]["text"],
                    "source": self.metadata[idx]["source"],
                    "score": float(distances[0][i])
                }
                results.append(result)

        return results

    def save(self, save_dir: str):
        """Save the FAISS index and metadata to disk.
        
        Args:
            save_dir: Directory to save the index files
        """
        os.makedirs(save_dir, exist_ok=True)

        # Save FAISS index
        index_path = os.path.join(save_dir, "faiss_index.bin")
        faiss.write_index(self.index, index_path)

        # Save metadata
        metadata_path = os.path.join(save_dir, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        print(f"Saved index ({self.index.ntotal} vectors) to {save_dir}")

    def load(self, save_dir: str):
        """Load a FAISS index and metadata from disk.
        
        Args:
            save_dir: Directory containing saved index files
        """
        index_path = os.path.join(save_dir, "faiss_index.bin")
        metadata_path = os.path.join(save_dir, "metadata.json")

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Index files not found in {save_dir}")

        # Load FAISS index
        self.index = faiss.read_index(index_path)

        # Load metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"Loaded index ({self.index.ntotal} vectors) from {save_dir}")


def create_index(dimension: int) -> VectorStore:
    """Factory function to create a new VectorStore.
    
    Args:
        dimension: Embedding dimension
    
    Returns:
        VectorStore instance
    """
    return VectorStore(dimension)


if __name__ == "__main__":
    # Quick test
    dim = 384
    store = create_index(dim)

    # Add some random vectors
    test_embeddings = np.random.rand(5, dim).astype(np.float32)
    test_metadata = [{"text": f"doc {i}", "source": f"src_{i}"} for i in range(5)]
    store.add_documents(test_embeddings, test_metadata)

    # Search
    query = np.random.rand(dim).astype(np.float32)
    results = store.search(query, k=3)
    print(f"Search results: {len(results)}")
    for r in results:
        print(f"  [{r['source']}] score={r['score']:.4f} — {r['text']}")
