"""
Document Atoms - Semantic chunks with Knowledge Delta
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DocumentAtom(SQLModel, table=True):
    """
    Semantic atom (chunk) of a document with Knowledge Delta scoring.
    Atoms are the minimum unit for vector search and novelty detection.
    """
    __tablename__ = "document_atoms"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Content
    content: str  # The text content of this atom
    char_start: int  # Start position in original document
    char_end: int  # End position
    
    # Chapter/Section info
    chapter_title: Optional[str] = None
    chapter_index: int = Field(default=0)
    section_title: Optional[str] = None
    
    # Knowledge Delta (novelty scoring)
    delta_score: float = Field(default=0.0)  # 0.0-1.0 novelty
    is_novel: bool = Field(default=True)  # delta >= 0.85
    is_redundant: bool = Field(default=False)  # delta >= 0.90 (hidden)
    
    # Semantic density (information density)
    semantic_density: float = Field(default=0.5)  # 0.0-1.0
    
    # Vector reference
    embedding_vector_id: Optional[str] = Field(default=None, index=True)
    
    # Processing
    processing_status: str = Field(default="pending")  # pending, embedded, failed
    processing_error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AtomDeltaResult(SQLModel):
    """Result of delta computation for an atom."""
    atom_id: str
    delta_score: float
    is_novel: bool
    is_redundant: bool
    similar_atoms: list  # List of similar atom IDs from user's knowledge
