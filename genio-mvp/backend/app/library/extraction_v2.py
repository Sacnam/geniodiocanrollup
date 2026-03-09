"""
Document extraction pipeline v2 - Library PRD compliant.
Integrates semantic chunking, PKG extraction, and multi-format parsers.
"""
import os
from datetime import datetime
from typing import Dict, List

from celery import chain, chord, group, shared_task

from app.core.database import SessionLocal
from app.library.graph_extractor import extract_graph_task
from app.library.parsers import parse_document
from app.library.semantic_chunker import semantic_chunking
from app.models.document import Document, DocumentChunk, DocumentStatus


@shared_task(bind=True, max_retries=3)
def parse_document_task(self, document_id: str):
    """
    Step 1: Parse document format (EPUB/PDF/DOCX/HTML/MD).
    """
    db = SessionLocal()
    
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"error": "Document not found"}
        
        doc.status = DocumentStatus.EXTRACTING
        db.add(doc)
        db.commit()
        
        # Parse based on type
        if doc.doc_type.value == "pdf":
            # Use existing PDF extractor for now
            from app.library.extraction import _process_pdf
            result = _process_pdf(doc)
        else:
            # Use new parsers
            result = parse_document(doc.file_path, doc.doc_type.value)
        
        # Update document
        doc.title = result.get("title") or doc.original_filename
        doc.author = result.get("author")
        doc.content = result.get("content")
        doc.excerpt = result.get("content", "")[:500] if result.get("content") else None
        doc.page_count = len(result.get("chapters", []))
        doc.word_count = len(result.get("content", "").split()) if result.get("content") else 0
        
        db.add(doc)
        db.commit()
        
        # Store chapters for chunking
        chapters = result.get("chapters", [])
        
        return {
            "document_id": document_id,
            "chapters": chapters,
            "total_words": doc.word_count,
        }
        
    except Exception as exc:
        doc.status = DocumentStatus.ERROR
        doc.processing_error = f"Parse error: {str(exc)}"
        db.add(doc)
        db.commit()
        
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60)
        return {"error": str(exc)}
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def semantic_chunk_task(self, document_id: str, chapters: List[Dict]):
    """
    Step 2: Semantic chunking with cosine-boundary detection.
    """
    db = SessionLocal()
    
    try:
        all_atoms = []
        
        for chapter in chapters:
            chapter_title = chapter.get("title", "Untitled")
            chapter_content = chapter.get("content", "")
            
            if not chapter_content.strip():
                continue
            
            # Apply semantic chunking
            atoms = semantic_chunking(
                text=chapter_content,
                chunk_size=1000,
                chunk_overlap=200,
                k_threshold=1.5
            )
            
            # Add chapter reference to each atom
            for atom in atoms:
                atom["chapter_ref"] = chapter_title
                all_atoms.append(atom)
        
        # Create DocumentChunk records
        for i, atom in enumerate(all_atoms):
            chunk = DocumentChunk(
                document_id=document_id,
                content=atom["text"],
                chunk_index=i,
                char_start=atom["char_start"],
                char_end=atom["char_end"],
            )
            db.add(chunk)
        
        db.commit()
        
        return {
            "document_id": document_id,
            "atoms": all_atoms,
            "atom_count": len(all_atoms),
        }
        
    except Exception as exc:
        doc = db.get(Document, document_id)
        if doc:
            doc.status = DocumentStatus.ERROR
            doc.processing_error = f"Chunking error: {str(exc)}"
            db.add(doc)
            db.commit()
        
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60)
        return {"error": str(exc)}
    
    finally:
        db.close()


@shared_task
def finalize_document(document_id: str, **kwargs):
    """
    Final step: Mark document as ready.
    """
    db = SessionLocal()
    
    try:
        doc = db.get(Document, document_id)
        if doc:
            doc.status = DocumentStatus.READY
            doc.extracted_at = datetime.utcnow()
            db.add(doc)
            db.commit()
        
        return {
            "document_id": document_id,
            "status": "ready",
        }
    finally:
        db.close()


@shared_task
def process_document_pipeline(document_id: str):
    """
    Main entry point: Orchestrates the full document processing pipeline.
    
    Pipeline:
    1. Parse document format
    2. Semantic chunking
    3. Generate embeddings
    4. Extract PKG graph
    5. Finalize
    """
    # Create Celery chord: parse → chunk → (embed + graph) → finalize
    workflow = chain(
        parse_document_task.s(document_id),
        semantic_chunk_task.s(document_id),
        # Embeddings and graph extraction in parallel
        chord(
            group(
                # Would add embedding task here
                # generate_document_embeddings_task.s(document_id),
                extract_graph_task.s(document_id),  # Needs atoms
            ),
            finalize_document.s(document_id)
        )
    )
    
    return workflow.apply_async()


# Re-export for backward compatibility
from app.library.extraction import extract_document_task, chunk_text, clean_text
