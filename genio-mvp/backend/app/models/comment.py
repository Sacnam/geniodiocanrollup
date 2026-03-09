"""
Comment models for threaded discussions on articles.
"""
from datetime import datetime
from typing import Optional, List
import re

from sqlmodel import Field, SQLModel, Relationship


class Comment(SQLModel, table=True):
    """Article comment with threading support."""
    __tablename__ = "comments"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Relationships
    article_id: str = Field(foreign_key="articles.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Threading
    parent_id: Optional[str] = Field(foreign_key="comments.id", default=None, index=True)
    depth: int = Field(default=0)  # Nesting level (0 = root)
    
    # Content
    content: str
    content_html: Optional[str] = None  # Sanitized HTML
    
    # Mentions (@username)
    mentions: str = Field(default="[]")  # JSON array of mentioned user IDs
    
    # Engagement
    likes_count: int = Field(default=0)
    replies_count: int = Field(default=0)
    
    # Status
    is_edited: bool = Field(default=False)
    edited_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    
    # For Q&A style discussions
    is_resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def extract_mentions(self) -> List[str]:
        """Extract @mentions from content."""
        pattern = r'@(\w+(?:\.\w+)*)'
        return re.findall(pattern, self.content)


class CommentLike(SQLModel, table=True):
    """Track comment likes."""
    __tablename__ = "comment_likes"
    
    comment_id: str = Field(foreign_key="comments.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class CommentCreate(SQLModel):
    content: str
    parent_id: Optional[str] = None


class CommentUpdate(SQLModel):
    content: str


class CommentResponse(SQLModel):
    id: str
    article_id: str
    user_id: str
    parent_id: Optional[str]
    depth: int
    content: str
    content_html: Optional[str]
    mentions: List[str]
    likes_count: int
    replies_count: int
    is_edited: bool
    edited_at: Optional[datetime]
    is_deleted: bool
    is_resolved: bool
    resolved_at: Optional[datetime]
    user: Optional[dict] = None  # Populated with user info
    is_liked_by_me: bool = False
    created_at: datetime


class CommentThreadResponse(SQLModel):
    """Response with threaded structure."""
    items: List[CommentResponse]
    total_count: int
    root_count: int
