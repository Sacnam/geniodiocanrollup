"""
Document Service
Handles document processing, chunking, and graph extraction.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, BinaryIO

from sqlmodel import Session, select

from app.core.config import settings
from app.core.ai_gateway import embed_texts, generate_text
from app.library.parsers import parse_document
from app.library.semantic_chunker import semantic_chunking
from app.library.graph_extractor import extract_graph_task
from app.library.embeddings import store_document_embedding, store_chunk_embeddings
from app.models.document import (
    Document,
    DocumentChunk,
    DocumentCollection,
    DocumentCollectionLink,
    DocumentHighlight,
    DocumentStatus,
    DocumentType,
)
from app.services.ai_service import track_ai_cost


class DocumentService:
    """Service for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(
        self,
        user_id: str,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        collection_ids: Optional[List[str]] = None
    ) -> Document:
        """
        Create a new document from uploaded file.
        
        Args:
            user_id: Owner of the document
            file: File content
            filename: Original filename
            mime_type: MIME type of file
            collection_ids: Optional list of collection IDs
            
        Returns:
            Created document
        """
        # Determine document type from mime_type
        doc_type = self._get_doc_type(mime_type, filename)
        
        # Generate storage path
        doc_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix
        storage_path = f"documents/{user_id}/{doc_id}{file_ext}"
        
        # Calculate file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        # TODO: Save file to storage (S3/local)
        # For now, just track the path
        
        # Create document record
        document = Document(
            id=doc_id,
            user_id=user_id,
            filename=f"{doc_id}{file_ext}",
            original_filename=filename,
            file_path=storage_path,
            file_size_bytes=file_size,
            mime_type=mime_type,
            doc_type=doc_type,
            status=DocumentStatus.PENDING,
        )
        
        self.db.add(document)
        
        # Add to collections if specified
        if collection_ids:
            for collection_id in collection_ids:
                link = DocumentCollectionLink(
                    document_id=doc_id,
                    collection_id=collection_id
                )
                self.db.add(link)
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def process_document(self, document_id: str) -> Document:
        """
        Process document: extract text, chunk, embed, extract graph.
        
        Args:
            document_id: Document ID to process
            
        Returns:
            Updated document
        """
        document = self.db.get(Document, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        try:
            # Update status
            document.status = DocumentStatus.PROCESSING
            document.processing_state = "extracting"
            self.db.add(document)
            self.db.commit()
            
            # Step 1: Extract text
            # TODO: Read from actual storage
            # content = self._read_file(document.file_path)
            # For now, assume content is extracted elsewhere
            
            if not document.content:
                # Try to parse if we have the file
                document.status = DocumentStatus.ERROR
                document.processing_error = "No content to process"
                self.db.add(document)
                self.db.commit()
                return document
            
            # Extract metadata
            document.excerpt = document.content[:500] if len(document.content) > 500 else document.content
            document.word_count = len(document.content.split())
            document.extracted_at = datetime.utcnow()
            
            # Update status
            document.status = DocumentStatus.EXTRACTED
            document.processing_state = "chunking"
            self.db.add(document)
            self.db.commit()
            
            # Step 2: Semantic chunking
            chunks = self._chunk_document(document)
            
            document.status = DocumentStatus.INDEXING
            document.processing_state = "embedding"
            self.db.add(document)
            self.db.commit()
            
            # Step 3: Generate embeddings
            self._embed_document_and_chunks(document, chunks)
            
            # Step 4: Queue graph extraction
            extract_graph_task.delay(document_id, document.user_id)
            
            # Mark as ready
            document.status = DocumentStatus.READY
            document.processing_state = "completed"
            document.processed_at = datetime.utcnow()
            self.db.add(document)
            self.db.commit()
            
        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.processing_error = str(e)
            document.retry_count += 1
            self.db.add(document)
            self.db.commit()
            raise
        
        return document
    
    def _chunk_document(self, document: Document) -> List[DocumentChunk]:
        """Create semantic chunks from document."""
        if not document.content:
            return []
        
        # Use semantic chunker
        chunk_data = semantic_chunking(
            document.content,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        chunks = []
        for i, data in enumerate(chunk_data):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                content=data['text'],
                chunk_index=i,
                char_start=data['char_start'],
                char_end=data['char_end'],
            )
            self.db.add(chunk)
            chunks.append(chunk)
        
        self.db.commit()
        return chunks
    
    def _embed_document_and_chunks(
        self,
        document: Document,
        chunks: List[DocumentChunk]
    ):
        """Generate and store embeddings."""
        # Embed full document
        if document.content:
            doc_embedding = embed_texts([document.content])[0]
            document.embedding_vector_id = store_document_embedding(
                doc_id=document.id,
                embedding=doc_embedding,
                user_id=document.user_id,
                title=document.title or document.original_filename,
                excerpt=document.excerpt or "",
            )
            self.db.add(document)
        
        # Embed chunks
        if chunks:
            chunk_texts = [c.content for c in chunks]
            chunk_embeddings = embed_texts(chunk_texts)
            
            for chunk, embedding in zip(chunks, chunk_embeddings):
                chunk.embedding_vector_id = store_chunk_embeddings(
                    chunk_id=chunk.id,
                    embedding=embedding,
                    document_id=document.id,
                    user_id=document.user_id,
                )
                self.db.add(chunk)
        
        self.db.commit()
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete document and all associated data.
        
        Args:
            document_id: Document to delete
            user_id: User requesting deletion (for auth check)
            
        Returns:
            True if deleted
        """
        document = self.db.exec(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id
            )
        ).first()
        
        if not document:
            return False
        
        # Delete from vector store
        # vector_store.delete_document(document.embedding_vector_id)
        
        # Delete chunks from vector store
        chunks = self.db.exec(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        ).all()
        
        for chunk in chunks:
            # vector_store.delete_document(chunk.embedding_vector_id)
            self.db.delete(chunk)
        
        # Delete highlights
        highlights = self.db.exec(
            select(DocumentHighlight).where(DocumentHighlight.document_id == document_id)
        ).all()
        
        for highlight in highlights:
            self.db.delete(highlight)
        
        # Delete collection links
        links = self.db.exec(
            select(DocumentCollectionLink).where(DocumentCollectionLink.document_id == document_id)
        ).all()
        
        for link in links:
            self.db.delete(link)
        
        # Delete document file from storage
        # self._delete_file(document.file_path)
        
        # Delete document record
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def create_highlight(
        self,
        document_id: str,
        user_id: str,
        char_start: int,
        char_end: int,
        highlighted_text: str,
        note: Optional[str] = None,
        color: str = "yellow",
        page_number: Optional[int] = None
    ) -> DocumentHighlight:
        """Create a highlight/annotation."""
        # Verify document exists and belongs to user
        document = self.db.exec(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id
            )
        ).first()
        
        if not document:
            raise ValueError("Document not found")
        
        highlight = DocumentHighlight(
            id=str(uuid.uuid4()),
            document_id=document_id,
            user_id=user_id,
            char_start=char_start,
            char_end=char_end,
            highlighted_text=highlighted_text,
            note=note,
            color=color,
            page_number=page_number,
        )
        
        self.db.add(highlight)
        self.db.commit()
        self.db.refresh(highlight)
        
        return highlight
    
    def delete_highlight(self, highlight_id: str, user_id: str) -> bool:
        """Delete a highlight."""
        highlight = self.db.exec(
            select(DocumentHighlight).where(
                DocumentHighlight.id == highlight_id,
                DocumentHighlight.user_id == user_id
            )
        ).first()
        
        if not highlight:
            return False
        
        self.db.delete(highlight)
        self.db.commit()
        
        return True
    
    def create_collection(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> DocumentCollection:
        """Create a document collection (folder)."""
        collection = DocumentCollection(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            color=color,
            parent_id=parent_id,
        )
        
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        
        return collection
    
    def search_documents(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[dict]:
        """Search documents using semantic search."""
        from app.library.graph_rag import hybrid_search
        
        results = hybrid_search(
            query=query,
            user_id=user_id,
            db=self.db,
            k_vector=limit,
            k_graph=0  # Don't include graph results for simple doc search
        )
        
        return results
    
    def get_document_status(self, document_id: str, user_id: str) -> Optional[dict]:
        """Get document processing status."""
        document = self.db.exec(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id
            )
        ).first()
        
        if not document:
            return None
        
        # Calculate progress based on status
        status_progress = {
            DocumentStatus.PENDING: 0,
            DocumentStatus.UPLOADED: 10,
            DocumentStatus.PROCESSING: 20,
            DocumentStatus.EXTRACTING: 30,
            DocumentStatus.EXTRACTED: 50,
            DocumentStatus.OCRING: 60,
            DocumentStatus.INDEXING: 80,
            DocumentStatus.READY: 100,
            DocumentStatus.ERROR: 0,
        }
        
        return {
            "document_id": document.id,
            "status": document.status.value,
            "progress": status_progress.get(document.status, 0),
            "state": document.processing_state,
            "error": document.processing_error,
            "retry_count": document.retry_count,
            "extracted_at": document.extracted_at.isoformat() if document.extracted_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
        }
    
    def _get_doc_type(self, mime_type: str, filename: str) -> DocumentType:
        """Determine document type from MIME type or filename."""
        mime_to_type = {
            "application/pdf": DocumentType.PDF,
            "text/plain": DocumentType.TEXT,
            "text/markdown": DocumentType.MARKDOWN,
            "text/html": DocumentType.HTML,
            "application/epub+zip": DocumentType.EPUB,
        }
        
        if mime_type in mime_to_type:
            return mime_to_type[mime_type]
        
        # Fall back to extension
        ext = Path(filename).suffix.lower()
        ext_to_type = {
            ".pdf": DocumentType.PDF,
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".markdown": DocumentType.MARKDOWN,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".epub": DocumentType.EPUB,
        }
        
        return ext_to_type.get(ext, DocumentType.TEXT)
