"""
Feed models for RSS/Atom aggregation.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class FeedStatus(str, Enum):
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    PAUSED = "paused"


class Feed(SQLModel, table=True):
    """RSS/Atom feed source."""
    __tablename__ = "feeds"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    url: str = Field(nullable=False)
    title: Optional[str] = None
    description: Optional[str] = None
    category: str = Field(default="Uncategorized")
    
    status: FeedStatus = Field(default=FeedStatus.ACTIVE)
    last_fetched_at: Optional[datetime] = None
    last_error: Optional[str] = None
    failure_count: int = Field(default=0)
    
    # Adaptive scheduling (B03)
    fetch_interval_minutes: int = Field(default=60)
    avg_update_interval_minutes: Optional[int] = None
    
    # HTTP caching
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="feeds")
    articles: List["Article"] = Relationship(back_populates="source_feed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/feed.xml",
                "title": "Example Blog",
                "category": "Tech"
            }
        }


class UserFeed(SQLModel, table=True):
    """Association between users and feeds (for shared feeds)."""
    __tablename__ = "user_feeds"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    feed_id: str = Field(foreign_key="feeds.id", index=True)
    
    # User-specific overrides
    custom_title: Optional[str] = None
    custom_category: Optional[str] = None
    is_muted: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
