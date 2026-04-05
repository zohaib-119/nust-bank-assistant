"""
Step 8 — RAG Pipeline Module
Orchestrates the full Retrieval-Augmented Generation pipeline.

Pipeline:
  User Query → Embed Query → Search FAISS → Retrieve Top Chunks
  → Construct Prompt → Send to LLM → Generate Answer
"""

import os
import numpy as np

from src.ingest import load_all_documents
from src.preprocess import preprocess_documents
from src.chunking import chunk_documents
from src.embeddings import EmbeddingModel
from src.vector_store import VectorStore
from src.retriever import Retriever
from src.llm import generate_response
from src.config import CONFIG
from src.guardrails import check_input, check_output


class RAGPipeline:
    """Full RAG pipeline for the NUST Bank customer support assistant."""

    def __init__(self, data_dir: str = "data", index_dir: str = "index", top_k: int = 3):
        """Initialize the RAG pipeline.
        
        Args:
            data_dir:  Directory containing source documents
            index_dir: Directory for storing/loading the FAISS index
            top_k:     Number of chunks to retrieve per query
        """
        self.data_dir = data_dir
        self.index_dir = index_dir
        self.top_k = top_k

        self.embedding_model = None
        self.vector_store = None
        self.retriever = None

    def initialize(self):
        """Initialize the pipeline: load or build the index.
        
        If a saved index exists, it is loaded. Otherwise, the pipeline
        ingests documents, preprocesses, chunks, embeds, and builds the index.
        """
        print("=" * 60)
        print("  NUST Bank RAG Pipeline — Initializing")
        print("=" * 60)

        # Step 1: Load embedding model
        print("\n[1/2] Loading embedding model...")
        self.embedding_model = EmbeddingModel()

        # Step 2: Load or build the vector index
        if self._index_exists():
            print("\n[2/2] Loading existing index from disk...")
            self._load_index()
        else:
            print("\n[2/2] Building index from documents...")
            self._build_index()

        # Initialize retriever
        self.retriever = Retriever(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
            top_k=self.top_k
        )

        print("\n" + "=" * 60)
        print("  Pipeline ready!")
        print("=" * 60)

    def _index_exists(self) -> bool:
        """Check if a saved FAISS index exists on disk."""
        index_path = os.path.join(self.index_dir, "faiss_index.bin")
        metadata_path = os.path.join(self.index_dir, "metadata.json")
        return os.path.exists(index_path) and os.path.exists(metadata_path)

    def _build_index(self):
        """Build the FAISS index from source documents."""

        # Step A: Ingest documents
        print("\n  [A] Ingesting documents...")
        documents = load_all_documents(self.data_dir)
        print(f"      → {len(documents)} documents loaded")

        if not documents:
            raise ValueError(f"No documents found in {self.data_dir}")

        # Step B: Preprocess
        print("\n  [B] Preprocessing text...")
        documents = preprocess_documents(documents)
        print(f"      → {len(documents)} documents after cleaning")

        # Step C: Chunk documents
        print("\n  [C] Chunking documents...")
        chunks = chunk_documents(documents, chunk_size=400, overlap=50)
        print(f"      → {len(chunks)} chunks created")

        # Step D: Generate embeddings
        print("\n  [D] Generating embeddings...")
        embeddings, metadata = self.embedding_model.embed_chunks(chunks)
        print(f"      → Embeddings shape: {embeddings.shape}")

        # Step E: Build and populate FAISS index
        print("\n  [E] Building FAISS index...")
        self.vector_store = VectorStore(dimension=self.embedding_model.dimension)
        self.vector_store.add_documents(embeddings, metadata)

        # Step F: Save index to disk
        print("\n  [F] Saving index to disk...")
        self.vector_store.save(self.index_dir)

    def _load_index(self):
        """Load a previously saved FAISS index."""
        self.vector_store = VectorStore(dimension=self.embedding_model.dimension)
        self.vector_store.load(self.index_dir)

    def query(self, question: str) -> str:
        """Process a user query through the full RAG pipeline.
        
        Pipeline:
          1. Embed the query
          2. Search FAISS for relevant chunks
          3. Construct prompt with retrieved context
          4. Send to LLM and generate answer
        
        Args:
            question: User's question string
        
        Returns:
            Generated answer string
        """
        if self.retriever is None:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        if CONFIG.enable_guardrails:
            gi = check_input(question)
            if not gi.allowed:
                return gi.message or "Blocked"
            question = gi.sanitized_text or question

        context = self.retriever.get_context_string(question)
        answer = generate_response(question, context)

        if CONFIG.enable_guardrails:
            go = check_output(answer)
            answer = go.sanitized_text or answer

        return answer

    def query_with_sources(self, question: str) -> dict:
        """Process a query and return the answer with source references.
        
        Args:
            question: User's question string
        
        Returns:
            Dict with 'answer', 'sources', and 'context' fields
        """
        if self.retriever is None:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        if CONFIG.enable_guardrails:
            gi = check_input(question)
            if not gi.allowed:
                return {"answer": gi.message or "Blocked", "sources": [], "context": ""}
            question = gi.sanitized_text or question

        results = self.retriever.retrieve(question)
        context = self.retriever.get_context_string(question)
        answer = generate_response(question, context)

        if CONFIG.enable_guardrails:
            go = check_output(answer)
            answer = go.sanitized_text or answer

        return {
            "answer": answer,
            "sources": [r["source"] for r in results],
            "context": context,
        }

    def rebuild_index(self):
        """Force rebuild the index from source documents."""
        print("Rebuilding index...")
        self._build_index()

    def add_upload_and_rebuild(self, upload_path: str) -> dict:
        """Add an uploaded file into the knowledge base and rebuild the index.

        This is designed for the Web UI runtime upload feature.

        Args:
            upload_path: Path to the uploaded file (temp path from Gradio)

        Returns:
            Dict describing what happened.
        """
        from src.ingest import save_uploaded_file

        uploads_dir = os.path.join(self.data_dir, "data", "uploads")
        saved_path = save_uploaded_file(upload_path, uploads_dir)

        # Invalidate and rebuild
        if os.path.exists(self.index_dir):
            # Keep directory but remove files inside to avoid permission issues on Windows
            for name in os.listdir(self.index_dir):
                try:
                    os.remove(os.path.join(self.index_dir, name))
                except OSError:
                    pass

        self._build_index()

        # Re-create retriever to ensure it uses the rebuilt vector_store
        self.retriever = Retriever(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
            top_k=self.top_k,
        )

        return {"saved_path": saved_path, "status": "ok"}
