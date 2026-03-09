"""
Reading List / Watch Later Model
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ReadingListItem(SQLModel, table=True):
    """Saved articles/pages for later reading."""
    __tablename__ = "reading_list"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Source info
    url: str
    title: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source_name: Optional[str] = None
    
    # Content (if extracted)
    content: Optional[str] = None
    word_count: Optional[int] = None
    
    # Status
    is_read: bool = Field(default=False)
    is_archived: bool = Field(default=False)
    priority: int = Field(default=0)  # 0=normal, 1=high
    
    # Tags
    tags: Optional[str] = None  # comma-separated
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class ReadingListItemCreate(SQLModel):
    url: str
    title: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source_name: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ReadingListItemUpdate(SQLModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
