"""
Document extraction pipeline for Library module.
Supports PDF, text files, and OCR for scanned documents.
"""
import re
from datetime import datetime
from typing import List, Tuple

import fitz  # PyMuPDF
from celery import shared_task

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentStatus


# Chunking configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks


class PDFExtractor:
    """Extract text and metadata from PDF files."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = None
    
    def __enter__(self):
        self.doc = fitz.open(self.file_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()
    
    def extract_text(self) -> str:
        """Extract full text from PDF."""
        text_parts = []
        for page in self.doc:
            text_parts.append(page.get_text())
        return "\n\n".join(text_parts)
    
    def extract_metadata(self) -> dict:
        """Extract PDF metadata."""
        metadata = self.doc.metadata
        return {
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "subject": metadata.get("subject"),
            "creator": metadata.get("creator"),
            "page_count": len(self.doc),
        }
    
    def is_scanned(self) -> bool:
        """
        Detect if PDF is scanned (image-based).
        Heuristic: check if pages have text or only images.
        """
        text_page_count = 0
        for page in self.doc[:3]:  # Check first 3 pages
            text = page.get_text().strip()
            if len(text) > 50:  # Threshold for text presence
                text_page_count += 1
        
        # If less than 2 pages have meaningful text, likely scanned
        return text_page_count < 2
    
    def extract_with_ocr(self) -> str:
        """
        Extract text using OCR for scanned PDFs.
        Requires pytesseract and pdf2image.
        """
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            images = convert_from_path(self.file_path, dpi=300)
            text_parts = []
            
            for image in images:
                text = pytesseract.image_to_string(image)
                text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except ImportError:
            raise ImportError(
                "OCR requires pytesseract and pdf2image. "
                "Install: pip install pytesseract pdf2image"
            )
    
    def get_page_text(self, page_num: int) -> str:
        """Get text from specific page."""
        if 0 <= page_num < len(self.doc):
            return self.doc[page_num].get_text()
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Tuple[str, int, int]]:
    """
    Split text into overlapping chunks.
    
    Returns:
        List of (chunk_text, start_char, end_char)
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending within next 100 chars
            search_end = min(end + 100, len(text))
            sentence_end = text.rfind('. ', end - 100, search_end)
            if sentence_end > end - 100:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, start, end))
        
        # Move start with overlap
        start = end - overlap
    
    return chunks


def clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()


@shared_task(bind=True, max_retries=3)
def extract_document_task(self, document_id: str):
    """
    Celery task to extract content from uploaded document.
    
    Pipeline:
    1. Detect document type
    2. Extract text (with OCR if needed)
    3. Clean and chunk
    4. Generate embeddings
    """
    db = SessionLocal()
    
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"error": "Document not found"}
        
        # Update status
        doc.status = DocumentStatus.EXTRACTING
        db.add(doc)
        db.commit()
        
        # Extract based on type
        if doc.doc_type == "pdf":
            result = _process_pdf(doc)
        elif doc.doc_type in ["text", "markdown"]:
            result = _process_text(doc)
        else:
            result = {"error": f"Unsupported type: {doc.doc_type}"}
        
        if "error" in result:
            doc.status = DocumentStatus.ERROR
            doc.processing_error = result["error"]
        else:
            # Update document with extracted content
            doc.content = result["content"]
            doc.excerpt = result["content"][:500] if result["content"] else None
            doc.title = result.get("title") or doc.original_filename
            doc.author = result.get("author")
            doc.page_count = result.get("page_count")
            doc.word_count = len(result["content"].split()) if result["content"] else 0
            doc.is_scanned = result.get("is_scanned", False)
            doc.status = DocumentStatus.EXTRACTED
            doc.extracted_at = datetime.utcnow()
            
            # Create chunks
            _create_document_chunks(db, doc, result["content"])
            
            # Queue embedding generation
            from app.library.embeddings import generate_document_embeddings_task
            generate_document_embeddings_task.delay(document_id)
            
            doc.status = DocumentStatus.INDEXING
        
        db.add(doc)
        db.commit()
        
        return {
            "document_id": document_id,
            "status": doc.status.value,
            "word_count": doc.word_count,
        }
        
    except Exception as exc:
        # Retry on failure
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60)
        
        doc.status = DocumentStatus.ERROR
        doc.processing_error = str(exc)
        db.add(doc)
        db.commit()
        
        return {"error": str(exc)}
        
    finally:
        db.close()


def _process_pdf(doc: Document) -> dict:
    """Process PDF document."""
    with PDFExtractor(doc.file_path) as extractor:
        # Check if scanned
        is_scanned = extractor.is_scanned()
        
        if is_scanned:
            content = extractor.extract_with_ocr()
        else:
            content = extractor.extract_text()
        
        metadata = extractor.extract_metadata()
        
        return {
            "content": clean_text(content),
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "page_count": metadata.get("page_count"),
            "is_scanned": is_scanned,
        }


def _process_text(doc: Document) -> dict:
    """Process text/markdown file."""
    with open(doc.file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to extract title from markdown
    title = None
    if doc.doc_type == "markdown":
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
    
    return {
        "content": clean_text(content),
        "title": title,
        "page_count": 1,
        "is_scanned": False,
    }


def _create_document_chunks(db, doc: Document, content: str):
    """Create semantic chunks from document content."""
    chunks = chunk_text(content)
    
    for idx, (chunk_text, char_start, char_end) in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=doc.id,
            content=chunk_text,
            chunk_index=idx,
            char_start=char_start,
            char_end=char_end,
        )
        db.add(chunk)
    
    db.commit()
