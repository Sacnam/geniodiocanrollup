"""
Test Content Hash Deduplication
"""
import pytest
from app.library.dedup import ContentDeduplicator, compute_content_hash
from app.models.document import Document


class TestContentDeduplication:
    """Test document deduplication by content hash."""

    def test_compute_hash_identical_content(self):
        """Same content = same hash."""
        content1 = "This is test content"
        content2 = "This is test content"
        
        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_compute_hash_different_content(self):
        """Different content = different hash."""
        content1 = "Content A"
        content2 = "Content B"
        
        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)
        
        assert hash1 != hash2

    def test_dedup_finds_existing_document(self, db_session):
        """Find existing document with same hash."""
        # Create first document
        doc1 = Document(
            user_id="user-1",
            filename="doc1.pdf",
            title="Document 1",
            content="Shared content here",
            content_hash=compute_content_hash("Shared content here")
        )
        db_session.add(doc1)
        db_session.commit()
        
        # Check for duplicate
        dedup = ContentDeduplicator(db_session)
        existing = dedup.find_duplicate("Shared content here", "user-1")
        
        assert existing is not None
        assert existing.id == doc1.id

    def test_dedup_no_duplicate_for_different_user(self, db_session):
        """Same content, different user = not duplicate."""
        doc1 = Document(
            user_id="user-1",
            filename="doc1.pdf",
            content="Shared content",
            content_hash=compute_content_hash("Shared content")
        )
        db_session.add(doc1)
        db_session.commit()
        
        dedup = ContentDeduplicator(db_session)
        existing = dedup.find_duplicate("Shared content", "user-2")
        
        assert existing is None

    def test_dedup_skip_reembedding(self, db_session):
        """Skip embedding if exact duplicate found."""
        doc1 = Document(
            user_id="user-1",
            filename="doc1.pdf",
            content="Content",
            content_hash=compute_content_hash("Content"),
            status="ready"
        )
        db_session.add(doc1)
        db_session.commit()
        
        dedup = ContentDeduplicator(db_session)
        should_skip = dedup.should_skip_embedding("Content", "user-1")
        
        assert should_skip == True

    def test_dedup_no_skip_if_no_vector(self, db_session):
        """Don't skip if original has no vectors."""
        doc1 = Document(
            user_id="user-1",
            filename="doc1.pdf",
            content="Content",
            content_hash=compute_content_hash("Content"),
            status="error"  # Failed processing
        )
        db_session.add(doc1)
        db_session.commit()
        
        dedup = ContentDeduplicator(db_session)
        should_skip = dedup.should_skip_embedding("Content", "user-1")
        
        assert should_skip == False
