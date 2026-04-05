"""
Step 1 — Data Ingestion Module
Loads documents directly from the source knowledge-base files:
  - NUST Bank-Product-Knowledge.xlsx  (Excel with multiple product sheets)
  - full_transfer_app_feature_faq.json (FAQ JSON with categories)

Each document has: { "id": str, "text": str }
"""

import json
import os
import shutil
from pathlib import Path
import pandas as pd


# Sheets to skip in the Excel file (non-content sheets)
SKIP_SHEETS = {"Main", "Rate Sheet July 1 2024", "Sheet1"}


def load_excel_knowledge_base(file_path: str) -> list[dict]:
    """Load documents from the NUST Bank Product Knowledge Excel file.
    
    Each sheet represents a product/service. We extract all meaningful
    text blocks (cells with >20 chars) from every content sheet and
    group them per sheet as a single document.
    
    Args:
        file_path: Path to the .xlsx file
    
    Returns:
        List of document dicts
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    sheets = pd.read_excel(file_path, sheet_name=None)
    documents = []

    for sheet_name, df in sheets.items():
        if sheet_name in SKIP_SHEETS:
            continue

        # Collect all meaningful text from every cell in the sheet
        text_blocks = []
        for col in df.columns:
            # Include column header if meaningful
            col_str = str(col).strip()
            if len(col_str) > 20 and "Unnamed" not in col_str:
                text_blocks.append(col_str)

            # Include cell values
            for val in df[col].dropna().values:
                s = str(val).strip()
                if len(s) > 15 and s.lower() != "nan" and "Unnamed" not in s:
                    text_blocks.append(s)

        if text_blocks:
            # Combine all text from this sheet into one document
            full_text = "\n".join(text_blocks)
            doc_id = f"excel_{sheet_name}"
            documents.append({"id": doc_id, "text": full_text})
            print(f"    Sheet '{sheet_name}': {len(text_blocks)} text blocks extracted")

    return documents


def load_faq_json(file_path: str) -> list[dict]:
    """Load documents from the FAQ JSON file.
    
    Each Q&A pair becomes a separate document for better retrieval granularity.
    
    Args:
        file_path: Path to the .json file
    
    Returns:
        List of document dicts
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []

    # Handle nested FAQ structure: { "categories": [ { "category": ..., "questions": [...] } ] }
    if isinstance(data, dict) and "categories" in data:
        for category in data["categories"]:
            cat_name = category.get("category", "General")
            for i, qa in enumerate(category.get("questions", [])):
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                text = f"Category: {cat_name}\nQuestion: {question}\nAnswer: {answer}"
                doc_id = f"faq_{cat_name.lower().replace(' ', '_').replace('/', '_')}_{i}"
                documents.append({"id": doc_id, "text": text})

    # Handle flat list of documents
    elif isinstance(data, list):
        for i, item in enumerate(data):
            doc_id = item.get("id", f"json_doc_{i}")
            text = item.get("text", "")
            if text.strip():
                documents.append({"id": doc_id, "text": text})

    return documents


def load_all_documents(data_dir: str) -> list[dict]:
    """Load all documents from the project's source knowledge-base files.

    Looks for:
      - *.xlsx files (Excel knowledge base)
      - *.json files  (FAQ JSON)

    in the given directory (project root or data folder).

    Returns:
        Combined list of all documents.
    """
    all_docs: list[dict] = []

    # Search the provided directory for source files
    for filename in os.listdir(data_dir):
        # Skip hidden/temp files (e.g. ~$NUST Bank-Product-Knowledge.xlsx)
        if filename.startswith("~$") or filename.startswith("."):
            continue

        file_path = os.path.join(data_dir, filename)

        if filename.lower().endswith(".xlsx"):
            print(f"  Loading Excel knowledge base: {filename}")
            docs = load_excel_knowledge_base(file_path)
            all_docs.extend(docs)
            print(f"    → {len(docs)} product documents loaded")

        if filename.lower().endswith(".json"):
            print(f"  Loading FAQ JSON: {filename}")
            docs = load_faq_json(file_path)
            all_docs.extend(docs)
            print(f"    → {len(docs)} FAQ documents loaded")

    return all_docs


def _is_allowed_upload(path: str) -> bool:
    return Path(path).suffix.lower() in {".xlsx", ".json", ".txt", ".md", ".pdf"}


def save_uploaded_file(src_path: str, uploads_dir: str) -> str:
    """Copy an uploaded file into a project-managed uploads directory.

    Gradio uploads point to a temp file path; copy it so it persists.

    Returns:
        Destination path of the copied file.
    """
    if not src_path:
        raise ValueError("No file path provided")

    if not _is_allowed_upload(src_path):
        raise ValueError(f"Unsupported file type for upload: {Path(src_path).suffix}")

    os.makedirs(uploads_dir, exist_ok=True)
    dst_path = os.path.join(uploads_dir, Path(src_path).name)
    shutil.copy2(src_path, dst_path)
    return dst_path


def load_text_file(file_path: str) -> list[dict]:
    """Load a plain-text/markdown file as a single document."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Text file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()

    if not text:
        return []

    doc_id = f"file_{Path(file_path).stem}"
    return [{"id": doc_id, "text": text}]


def load_pdf_file(file_path: str) -> list[dict]:
    """Load a PDF as a single document.

    Note: Requires `pymupdf`.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    try:
        import fitz  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError("PDF ingestion requires pymupdf. Install: pip install pymupdf") from e

    doc = fitz.open(file_path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text("text"))
    text = "\n".join(parts).strip()

    if not text:
        return []

    doc_id = f"pdf_{Path(file_path).stem}"
    return [{"id": doc_id, "text": text}]


def load_single_document(file_path: str) -> list[dict]:
    """Load exactly one knowledge-base file into a list of documents."""
    suffix = Path(file_path).suffix.lower()

    if suffix == ".xlsx":
        return load_excel_knowledge_base(file_path)
    if suffix == ".json":
        return load_faq_json(file_path)
    if suffix in {".txt", ".md"}:
        return load_text_file(file_path)
    if suffix == ".pdf":
        return load_pdf_file(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


if __name__ == "__main__":
    # Quick test
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    docs = load_all_documents(data_dir)
    print(f"\nTotal documents loaded: {len(docs)}")
    for doc in docs[:5]:
        print(f"  [{doc['id']}] {doc['text'][:100]}...")
