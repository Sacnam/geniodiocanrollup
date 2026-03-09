"""Tests for Document Service."""
import pytest
from io import BytesIO
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.services.document_service import DocumentService
from app.models.document import Document, DocumentStatus, DocumentType, DocumentHighlight


class TestDocumentService:
    """Test DocumentService functionality."""

    def test_create_document(self, session):
        """Should create document from file."""
        service = DocumentService(session)
        
        file = BytesIO(b"PDF content")
        
        document = service.create_document(
            user_id="user-123",
            file=file,
            filename="test.pdf",
            mime_type="application/pdf"
        )
        
        assert document.id is not None
        assert document.user_id == "user-123"
        assert document.original_filename == "test.pdf"
        assert document.mime_type == "application/pdf"
        assert document.doc_type == DocumentType.PDF
        assert document.status == DocumentStatus.PENDING
        assert document.file_size_bytes == len(b"PDF content")

    def test_create_document_with_collection(self, session):
        """Should create document and add to collection."""
        service = DocumentService(session)
        
        # First create a collection
        from app.models.document import DocumentCollection
        collection = DocumentCollection(
            id="coll-456",
            user_id="user-123",
            name="Test Collection"
        )
        session.add(collection)
        session.commit()
        
        file = BytesIO(b"Content")
        
        document = service.create_document(
            user_id="user-123",
            file=file,
            filename="test.md",
            mime_type="text/markdown",
            collection_ids=["coll-456"]
        )
        
        # Verify collection link
        links = session.exec(
            select(DocumentCollectionLink).where(DocumentCollectionLink.document_id == document.id)
        ).all()
        
        assert len(links) == 1
        assert links[0].collection_id == "coll-456"

    def test_get_doc_type_from_mime(self, session):
        """Should determine doc type from MIME type."""
        service = DocumentService(session)
        
        assert service._get_doc_type("application/pdf", "test.pdf") == DocumentType.PDF
        assert service._get_doc_type("text/plain", "test.txt") == DocumentType.TEXT
        assert service._get_doc_type("text/markdown", "test.md") == DocumentType.MARKDOWN
        assert service._get_doc_type("text/html", "test.html") == DocumentType.HTML
        assert service._get_doc_type("application/epub+zip", "test.epub") == DocumentType.EPUB

    def test_get_doc_type_from_extension(self, session):
        """Should determine doc type from extension when MIME unknown."""
        service = DocumentService(session)
        
        assert service._get_doc_type("application/octet-stream", "test.pdf") == DocumentType.PDF
        assert service._get_doc_type("unknown/type", "test.md") == DocumentType.MARKDOWN
        assert service._get_doc_type("unknown/type", "test.txt") == DocumentType.TEXT

    def test_delete_document(self, session):
        """Should delete document and associated data."""
        service = DocumentService(session)
        
        # Create document
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
        )
        session.add(doc)
        session.commit()
        
        # Delete
        result = service.delete_document("doc-123", "user-123")
        
        assert result is True
        
        # Verify deleted
        deleted = session.get(Document, "doc-123")
        assert deleted is None

    def test_delete_document_wrong_user(self, session):
        """Should not delete document belonging to another user."""
        service = DocumentService(session)
        
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
        )
        session.add(doc)
        session.commit()
        
        # Try to delete as different user
        result = service.delete_document("doc-123", "user-456")
        
        assert result is False
        
        # Verify still exists
        existing = session.get(Document, "doc-123")
        assert existing is not None

    def test_create_highlight(self, session):
        """Should create highlight on document."""
        service = DocumentService(session)
        
        # Create document first
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
            content="This is the document content"
        )
        session.add(doc)
        session.commit()
        
        # Create highlight
        highlight = service.create_highlight(
            document_id="doc-123",
            user_id="user-123",
            char_start=5,
            char_end=12,
            highlighted_text="is the",
            note="Important part",
            color="yellow"
        )
        
        assert highlight.id is not None
        assert highlight.document_id == "doc-123"
        assert highlight.user_id == "user-123"
        assert highlight.char_start == 5
        assert highlight.char_end == 12
        assert highlight.highlighted_text == "is the"
        assert highlight.note == "Important part"
        assert highlight.color == "yellow"

    def test_create_highlight_wrong_user(self, session):
        """Should not create highlight on another user's document."""
        service = DocumentService(session)
        
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
        )
        session.add(doc)
        session.commit()
        
        # Try to highlight as different user
        with pytest.raises(ValueError, match="Document not found"):
            service.create_highlight(
                document_id="doc-123",
                user_id="user-456",
                char_start=0,
                char_end=5,
                highlighted_text="test"
            )

    def test_delete_highlight(self, session):
        """Should delete highlight."""
        service = DocumentService(session)
        
        # Create highlight
        highlight = DocumentHighlight(
            id="hl-123",
            document_id="doc-123",
            user_id="user-123",
            char_start=0,
            char_end=5,
            highlighted_text="Hello"
        )
        session.add(highlight)
        session.commit()
        
        # Delete
        result = service.delete_highlight("hl-123", "user-123")
        
        assert result is True
        
        # Verify deleted
        deleted = session.get(DocumentHighlight, "hl-123")
        assert deleted is None

    def test_create_collection(self, session):
        """Should create document collection."""
        service = DocumentService(session)
        
        collection = service.create_collection(
            user_id="user-123",
            name="Research Papers",
            description="My research papers",
            color="blue"
        )
        
        assert collection.id is not None
        assert collection.user_id == "user-123"
        assert collection.name == "Research Papers"
        assert collection.description == "My research papers"
        assert collection.color == "blue"

    def test_get_document_status(self, session):
        """Should get document processing status."""
        service = DocumentService(session)
        
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
            status=DocumentStatus.INDEXING,
            processing_state="embedding"
        )
        session.add(doc)
        session.commit()
        
        status = service.get_document_status("doc-123", "user-123")
        
        assert status is not None
        assert status["document_id"] == "doc-123"
        assert status["status"] == "indexing"
        assert status["state"] == "embedding"
        assert status["progress"] == 80  # INDEXING = 80%

    def test_get_document_status_not_found(self, session):
        """Should return None for non-existent document."""
        service = DocumentService(session)
        
        status = service.get_document_status("non-existent", "user-123")
        
        assert status is None

    @patch("app.services.document_service.semantic_chunking")
    @patch("app.services.document_service.embed_texts")
    @patch("app.services.document_service.store_document_embedding")
    @patch("app.services.document_service.store_chunk_embeddings")
    @patch("app.services.document_service.extract_graph_task")
    def test_process_document(
        self,
        mock_graph_task,
        mock_store_chunk,
        mock_store_doc,
        mock_embed,
        mock_chunk,
        session
    ):
        """Should process document through full pipeline."""
        service = DocumentService(session)
        
        # Setup mocks
        mock_chunk.return_value = [
            {
                'text': 'Chunk 1',
                'char_start': 0,
                'char_end': 10,
                'chunk_index': 0
            }
        ]
        mock_embed.return_value = [[0.1] * 1536]
        mock_store_doc.return_value = "vec-doc-123"
        mock_store_chunk.return_value = "vec-chunk-123"
        
        # Create document with content
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.md",
            original_filename="test.md",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="text/markdown",
            doc_type=DocumentType.MARKDOWN,
            content="# Title\n\nThis is content",
            status=DocumentStatus.PENDING
        )
        session.add(doc)
        session.commit()
        
        # Process
        result = service.process_document("doc-123")
        
        assert result.status == DocumentStatus.READY
        assert result.excerpt is not None
        assert result.word_count > 0
        mock_graph_task.delay.assert_called_once_with("doc-123", "user-123")

    def test_process_document_no_content(self, session):
        """Should handle document without content."""
        service = DocumentService(session)
        
        doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="path/to/file",
            file_size_bytes=100,
            mime_type="application/pdf",
            doc_type=DocumentType.PDF,
            content=None,
            status=DocumentStatus.PENDING
        )
        session.add(doc)
        session.commit()
        
        result = service.process_document("doc-123")
        
        assert result.status == DocumentStatus.ERROR
        assert result.processing_error == "No content to process"


# Import at end to avoid issues
from app.models.document import DocumentCollectionLink
from sqlmodel import select as sa_select
