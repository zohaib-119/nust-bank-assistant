"""
Step 3 — Document Chunking Module
Splits documents into smaller overlapping chunks suitable for embedding.
"""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks based on word count.
    
    Args:
        text:       The text to split
        chunk_size: Target number of words per chunk (300-500 tokens ≈ words)
        overlap:    Number of overlapping words between chunks
    
    Returns:
        List of text chunks
    """
    words = text.split()

    # If text is smaller than chunk_size, return it as-is
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Move start forward by (chunk_size - overlap)
        start += chunk_size - overlap

    return chunks


def chunk_documents(documents: list[dict], chunk_size: int = 400, overlap: int = 50) -> list[dict]:
    """Split a list of documents into smaller chunks.
    
    Each chunk retains a reference to the source document.
    
    Args:
        documents:  List of dicts with 'id' and 'text' fields
        chunk_size: Target number of words per chunk
        overlap:    Number of overlapping words between chunks
    
    Returns:
        List of chunk dicts: [{ "text": str, "source": str }, ...]
    """
    all_chunks = []

    for doc in documents:
        text = doc["text"]
        source_id = doc["id"]
        text_chunks = chunk_text(text, chunk_size, overlap)

        for chunk in text_chunks:
            all_chunks.append({
                "text": chunk,
                "source": source_id
            })

    return all_chunks


if __name__ == "__main__":
    # Quick test
    sample_doc = {
        "id": "test_doc",
        "text": " ".join([f"word{i}" for i in range(1000)])  # 1000 words
    }
    chunks = chunk_documents([sample_doc], chunk_size=400, overlap=50)
    print(f"Original: {len(sample_doc['text'].split())} words")
    print(f"Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        words = chunk["text"].split()
        print(f"  Chunk {i}: {len(words)} words, source={chunk['source']}")
