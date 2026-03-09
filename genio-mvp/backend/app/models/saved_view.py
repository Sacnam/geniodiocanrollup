"""
Saved views and filter configuration models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlmodel import Field, SQLModel


class FilterConfig(SQLModel):
    """Filter configuration for saved views."""
    # Text search
    search: Optional[str] = None
    
    # Tag filtering
    tags: Optional[List[str]] = None  # Tag IDs or names
    tag_operator: str = "any"  # "any" or "all"
    
    # Feed filtering
    feeds: Optional[List[str]] = None  # Feed IDs
    
    # Content type
    content_types: Optional[List[str]] = None  # articles, documents, etc.
    
    # Read status
    is_read: Optional[bool] = None
    is_favorited: Optional[bool] = None
    is_archived: Optional[bool] = None
    
    # Date range
    date_from: Optional[str] = None  # ISO date
    date_to: Optional[str] = None
    
    # Knowledge Delta
    delta_score_min: Optional[float] = None
    delta_score_max: Optional[float] = None
    
    # Word count
    word_count_min: Optional[int] = None
    word_count_max: Optional[int] = None
    
    # Sorting
    sort_by: str = "published_at"  # published_at, delta_score, created_at
    sort_order: str = "desc"  # asc or desc
    
    # Pagination
    per_page: int = 20


class SavedView(SQLModel, table=True):
    """User-defined saved views with filter configurations."""
    __tablename__ = "saved_views"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Display properties
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None  # Emoji or icon name
    color: Optional[str] = None  # Hex color
    
    # Filter configuration (stored as JSON)
    filters: str = Field(default="{}")  # JSON string of FilterConfig
    
    # View settings
    is_default: bool = Field(default=False)
    is_pinned: bool = Field(default=False)
    position: int = Field(default=0)  # For ordering
    
    # Sharing
    share_token: Optional[str] = None
    share_enabled: bool = Field(default=False)
    
    # System views cannot be deleted
    is_system: bool = Field(default=False)
    
    # Usage
    use_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class SavedViewCreate(SQLModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: bool = False
    position: int = 0


class SavedViewUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_pinned: Optional[bool] = None
    position: Optional[int] = None


class SavedViewResponse(SQLModel):
    id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    filters: Dict[str, Any]
    is_default: bool
    is_pinned: bool
    position: int
    share_enabled: bool
    use_count: int
    created_at: datetime


class ReorderViewsRequest(SQLModel):
    view_ids: List[str]


class ShareViewResponse(SQLModel):
    share_token: str
    share_url: str
