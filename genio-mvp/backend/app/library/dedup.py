"""
Content Hash Deduplication
Prevents re-processing and re-embedding identical documents.
"""
import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


def compute_content_hash(content: str) -> str:
    """
    Compute SHA-256 hash of content.
    Used to identify duplicate documents.
    """
    if not content:
        return ""
    
    # Normalize content (strip whitespace, lowercase)
    normalized = content.strip().lower()
    
    # Compute hash
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


class ContentDeduplicator:
    """Handles document deduplication by content hash."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_duplicate(
        self, 
        content: str, 
        user_id: str,
        exclude_id: Optional[str] = None
    ) -> Optional[Document]:
        """
        Find existing document with same content hash for user.
        
        Args:
            content: Document content to check
            user_id: User ID (dedup is per-user)
            exclude_id: Optional document ID to exclude (for updates)
            
        Returns:
            Existing Document if found, None otherwise
        """
        content_hash = compute_content_hash(content)
        
        query = self.db.query(Document).filter(
            Document.user_id == user_id,
            Document.content_hash == content_hash
        )
        
        if exclude_id:
            query = query.filter(Document.id != exclude_id)
        
        return query.first()
    
    def should_skip_embedding(self, content: str, user_id: str) -> bool:
        """
        Check if we should skip embedding because identical content
        already has vectors stored.
        
        Args:
            content: Document content
            user_id: User ID
            
        Returns:
            True if embedding should be skipped
        """
        duplicate = self.find_duplicate(content, user_id)
        
        if not duplicate:
            return False
        
        # Only skip if original was successfully processed
        # and has embedding vectors
        if duplicate.status == DocumentStatus.READY:
            return True
        
        return False
    
    def copy_vectors_from_duplicate(
        self,
        new_doc: Document,
        duplicate: Document
    ) -> bool:
        """
        Copy embedding vectors from duplicate document.
        Avoids re-computing embeddings.
        
        Args:
            new_doc: New document to populate
            duplicate: Existing document with vectors
            
        Returns:
            True if vectors were copied
        """
        if duplicate.status != DocumentStatus.READY:
            return False
        
        # Copy vector ID
        new_doc.embedding_vector_id = duplicate.embedding_vector_id
        
        # Could also copy chunks if they exist
        # This would require copying DocumentChunk records
        
        return True
    
    def check_upload(
        self,
        content: str,
        user_id: str,
        filename: str
    ) -> dict:
        """
        Check upload for duplicates and return recommendation.
        
        Returns:
            Dict with:
            - is_duplicate: bool
            - existing_doc: Document or None
            - should_skip_processing: bool
            - message: str
        """
        duplicate = self.find_duplicate(content, user_id)
        
        if not duplicate:
            return {
                "is_duplicate": False,
                "existing_doc": None,
                "should_skip_processing": False,
                "message": "New document"
            }
        
        # Check if we can reuse processing
        if duplicate.status == DocumentStatus.READY:
            return {
                "is_duplicate": True,
                "existing_doc": duplicate,
                "should_skip_processing": True,
                "message": f"Duplicate of '{duplicate.title or duplicate.filename}'. Vectors will be reused."
            }
        elif duplicate.status == DocumentStatus.ERROR:
            return {
                "is_duplicate": True,
                "existing_doc": duplicate,
                "should_skip_processing": False,
                "message": f"Previous upload of '{duplicate.filename}' failed. Retrying..."
            }
        else:
            return {
                "is_duplicate": True,
                "existing_doc": duplicate,
                "should_skip_processing": False,
                "message": f"Similar document '{duplicate.filename}' is being processed."
            }
