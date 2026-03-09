"""
Daily Brief models.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.user import User


class Brief(SQLModel, table=True):
    """Daily AI-generated brief."""
    __tablename__ = "briefs"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    title: str
    scheduled_for: datetime = Field(index=True)
    delivered_at: Optional[datetime] = None
    delivery_status: str = Field(default="pending")  # pending, sent, delivered, opened
    
    # B09: Quiet Day optimization
    is_quiet_day: bool = Field(default=False)
    quiet_day_reason: Optional[str] = None
    
    # Content
    article_count: int = Field(default=0)
    sources_cited: List[str] = Field(default=[], sa_column=Column(String))
    
    # AI Cost tracking
    generation_cost_usd: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="briefs")
    sections: List["BriefSection"] = Relationship(back_populates="brief")


class BriefSection(SQLModel, table=True):
    """Section within a brief."""
    __tablename__ = "brief_sections"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    brief_id: str = Field(foreign_key="briefs.id")
    
    section_type: str  # executive_summary, key_stories, the_diff, emerging_trends
    title: str
    content: str
    order: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    brief: Brief = Relationship(back_populates="sections")
    articles: List["Article"] = Relationship(back_populates="brief_sections")
