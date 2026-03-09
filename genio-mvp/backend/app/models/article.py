"""
Article models with shared pool architecture (B04).
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.brief import BriefSection
    from app.models.feed import Feed
    from app.models.user import User
    from app.models.tag import Tag, ArticleTag


class ProcessingStatus(str, Enum):
    """FSM states for article processing (B06)."""
    PENDING = "pending"
    FETCHED = "fetched"
    EXTRACTING = "extracting"
    EXTRACT_FAILED = "extract_failed"
    EMBEDDING = "embedding"
    EMBED_FAILED = "embed_failed"
    SCORING = "scoring"
    SCORE_FAILED = "score_failed"
    SUMMARIZING = "summarizing"
    SUMMARIZE_FAILED = "summarize_failed"
    READY = "ready"


class Article(SQLModel, table=True):
    """
    Shared article pool (B04).
    Global deduplication via URL + content_hash.
    """
    __tablename__ = "articles"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Source
    url: str = Field(index=True, nullable=False)
    source_feed_id: Optional[str] = Field(foreign_key="feeds.id", nullable=True)
    source_feed_title: Optional[str] = None
    
    # Content
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    
    # Deduplication
    content_hash: str = Field(index=True)  # SHA-256 of normalized content
    
    # AI-generated summary (shared)
    global_summary: Optional[str] = None
    summary_generated_at: Optional[datetime] = None
    
    # Embeddings (shared pool)
    embedding_vector_id: Optional[str] = Field(default=None, index=True)
    
    # FSM Processing (B06)
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    processing_started_at: Optional[datetime] = None
    processing_attempts: int = Field(default=0)
    processing_error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source_feed: Optional["Feed"] = Relationship(back_populates="articles")
    user_contexts: List["UserArticleContext"] = Relationship(back_populates="article")
    brief_sections: List["BriefSection"] = Relationship(back_populates="articles")
    tags: List["Tag"] = Relationship(back_populates="articles", link_model="ArticleTag")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "title": "Example Article",
                "content_hash": "sha256_hash"
            }
        }


class UserArticleContext(SQLModel, table=True):
    """
    Per-user article context for Knowledge Delta scoring.
    B04: Separates shared article data from per-user novelty.
    """
    __tablename__ = "user_article_context"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Keys
    user_id: str = Field(foreign_key="users.id", index=True)
    article_id: str = Field(foreign_key="articles.id", index=True)
    
    # Knowledge Delta (B04)
    delta_score: float = Field(default=0.0)  # 0.0-1.0 novelty
    cluster_id: Optional[str] = None  # Group similar articles
    is_duplicate: bool = Field(default=False)  # Hide from feed if True
    
    # User state
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    is_archived: bool = Field(default=False)
    is_favorited: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="article_contexts")
    article: Article = Relationship(back_populates="user_contexts")
