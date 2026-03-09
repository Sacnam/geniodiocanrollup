"""
Document embeddings for Library module.
Integrates with existing embedding pipeline.
"""
from celery import shared_task

from app.core.database import SessionLocal
from app.knowledge.vector_store import vector_store
from app.models.document import Document, DocumentChunk, DocumentStatus


@shared_task(bind=True, max_retries=3)
def generate_document_embeddings_task(self, document_id: str):
    """
    Generate embeddings for document and its chunks.
    Uses batch processing for efficiency (B13).
    """
    db = SessionLocal()
    
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"error": "Document not found"}
        
        # Get chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        if not chunks:
            # No chunks - embed full document
            if doc.content:
                vector_id = vector_store.upsert_document(
                    doc_id=doc.id,
                    content=doc.content,
                    metadata={
                        "type": "document",
                        "title": doc.title,
                        "user_id": doc.user_id,
                    }
                )
                doc.embedding_vector_id = vector_id
        else:
            # Batch embed chunks (B13 optimization)
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Prepare batch
                texts = [c.content for c in batch]
                ids = [f"{doc.id}_chunk_{c.chunk_index}" for c in batch]
                metadata = [
                    {
                        "document_id": doc.id,
                        "chunk_index": c.chunk_index,
                        "user_id": doc.user_id,
                        "type": "document_chunk",
                    }
                    for c in batch
                ]
                
                # Store embeddings
                vector_ids = vector_store.upsert_batch(ids, texts, metadata)
                
                # Update chunks with vector IDs
                for chunk, vid in zip(batch, vector_ids):
                    chunk.embedding_vector_id = vid
                    db.add(chunk)
            
            # Store document-level reference
            doc.embedding_vector_id = f"{doc.id}_doc"
        
        doc.status = DocumentStatus.READY
        db.add(doc)
        db.commit()
        
        return {
            "document_id": document_id,
            "chunks_embedded": len(chunks),
            "status": "ready",
        }
        
    except Exception as exc:
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60)
        
        doc.status = DocumentStatus.ERROR
        doc.processing_error = f"Embedding failed: {str(exc)}"
        db.add(doc)
        db.commit()
        
        return {"error": str(exc)}
        
    finally:
        db.close()
