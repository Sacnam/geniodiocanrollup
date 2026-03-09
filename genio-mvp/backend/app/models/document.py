"""
Document models for Library module (v2.0).
Supports PDF, text files, and web pages saved as documents.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class DocumentType(str, Enum):
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    EPUB = "epub"


class DocumentStatus(str, Enum):
    """FSM for document processing."""
    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    OCRING = "ocring"  # For scanned PDFs
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class Document(SQLModel, table=True):
    """
    User document for Library module.
    Similar to Article but for uploaded files.
    """
    __tablename__ = "documents"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # File info
    filename: str
    original_filename: str
    file_path: str  # Storage path (S3/local)
    file_size_bytes: int
    mime_type: str
    doc_type: DocumentType
    
    # Content (extracted)
    title: Optional[str] = None
    content: Optional[str] = None  # Full text content
    excerpt: Optional[str] = None  # First 500 chars
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    
    # Metadata
    author: Optional[str] = None
    source_url: Optional[str] = None  # If imported from web
    tags: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    
    # Processing
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    processing_state: Optional[str] = None  # FSM state (parsing, chunking, etc.)
    processing_error: Optional[str] = None
    retry_count: int = Field(default=0)
    extracted_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    state_changed_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Embeddings (for Knowledge Delta)
    embedding_vector_id: Optional[str] = Field(default=None, index=True)
    
    # OCR info (for scanned PDFs)
    is_scanned: bool = Field(default=False)
    ocr_confidence: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chunks: List["DocumentChunk"] = Relationship(back_populates="document")


class DocumentChunk(SQLModel, table=True):
    """
    Document chunks for semantic search.
    Documents are split into chunks for better retrieval.
    """
    __tablename__ = "document_chunks"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    
    # Chunk content
    content: str
    chunk_index: int  # Position in document
    page_number: Optional[int] = None
    
    # Embedding
    embedding_vector_id: Optional[str] = Field(default=None, index=True)
    
    # Metadata for retrieval
    char_start: int
    char_end: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    document: Document = Relationship(back_populates="chunks")


class DocumentCollection(SQLModel, table=True):
    """
    Collections (folders) for organizing documents.
    Similar to feed categories but for documents.
    """
    __tablename__ = "document_collections"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # UI color
    
    # Hierarchy
    parent_id: Optional[str] = Field(foreign_key="document_collections.id", nullable=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentCollectionLink(SQLModel, table=True):
    """Many-to-many link between documents and collections."""
    __tablename__ = "document_collection_links"
    
    document_id: str = Field(foreign_key="documents.id", primary_key=True)
    collection_id: str = Field(foreign_key="document_collections.id", primary_key=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentHighlight(SQLModel, table=True):
    """User highlights and annotations on documents."""
    __tablename__ = "document_highlights"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Highlight location
    char_start: int
    char_end: int
    page_number: Optional[int] = None
    
    # Content
    highlighted_text: str
    note: Optional[str] = None  # User annotation
    
    # Color
    color: str = Field(default="yellow")  # yellow, green, blue, pink
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
