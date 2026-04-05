"""
Step 2 — Text Preprocessing Module
Cleans and normalizes text data for embedding.
"""

import re


def clean_text(text: str) -> str:
    """Clean and normalize text for processing.
    
    Operations:
      - Convert to lowercase
      - Remove special/strange characters (keep alphanumeric, spaces, basic punctuation)
      - Normalize whitespace (collapse multiple spaces/newlines)
      - Strip leading/trailing whitespace
    
    Args:
        text: Raw text string
    
    Returns:
        Cleaned text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove strange characters but keep useful punctuation
    # Keep: letters, digits, spaces, periods, commas, question marks,
    #        exclamation marks, hyphens, apostrophes, colons, semicolons,
    #        slashes, parentheses, percentage, currency symbols
    text = re.sub(r"[^\w\s.,?!'\-:;/()%$₨@+]", " ", text)

    # Normalize whitespace — collapse multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)

    # Strip leading and trailing whitespace
    text = text.strip()

    return text


def preprocess_documents(documents: list[dict]) -> list[dict]:
    """Apply text cleaning to a list of documents.
    
    Args:
        documents: List of dicts with 'id' and 'text' fields
    
    Returns:
        List of dicts with cleaned 'text' fields
    """
    cleaned = []
    for doc in documents:
        cleaned_text = clean_text(doc["text"])
        if cleaned_text:  # Only keep non-empty docs
            cleaned.append({
                "id": doc["id"],
                "text": cleaned_text
            })
    return cleaned


if __name__ == "__main__":
    # Quick test
    sample_texts = [
        "  Hello   World!!!  This is a   TEST...  ",
        "Special chars: §©®™ but keep: $100, 50%, email@test.com",
        "Multiple\n\n\nnewlines   and   spaces   everywhere  ",
    ]
    for text in sample_texts:
        print(f"Original: '{text}'")
        print(f"Cleaned:  '{clean_text(text)}'")
        print()
