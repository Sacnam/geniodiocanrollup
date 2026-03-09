"""
Tag models for advanced content organization.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import re

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.document import Document


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from tag name."""
    # Convert to lowercase, replace spaces and special chars with hyphen
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


class Tag(SQLModel, table=True):
    """User-defined tags for organizing content."""
    __tablename__ = "tags"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Tag properties
    name: str = Field(index=True)
    slug: str = Field(index=True)  # URL-friendly version
    color: Optional[str] = Field(default=None)  # Hex color code
    icon: Optional[str] = Field(default=None)  # Emoji or icon name
    description: Optional[str] = None
    
    # Parent tag for hierarchies (optional)
    parent_id: Optional[str] = Field(foreign_key="tags.id", default=None)
    
    # System tags can't be deleted
    is_system: bool = Field(default=False)
    
    # Usage count (denormalized for performance)
    usage_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    articles: List["Article"] = Relationship(back_populates="tags", link_model=ArticleTag)
    documents: List["Document"] = Relationship(back_populates="tags", link_model=DocumentTag)
    
    def generate_slug(self) -> str:
        """Generate slug from name."""
        return generate_slug(self.name)


class ArticleTag(SQLModel, table=True):
    """Many-to-many link between articles and tags."""
    __tablename__ = "article_tags"
    
    article_id: str = Field(foreign_key="articles.id", primary_key=True)
    tag_id: str = Field(foreign_key="tags.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentTag(SQLModel, table=True):
    """Many-to-many link between documents and tags."""
    __tablename__ = "document_tags"
    
    document_id: str = Field(foreign_key="documents.id", primary_key=True)
    tag_id: str = Field(foreign_key="tags.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingListTag(SQLModel, table=True):
    """Many-to-many link between reading list items and tags."""
    __tablename__ = "reading_list_tags"
    
    reading_list_id: str = Field(foreign_key="reading_list.id", primary_key=True)
    tag_id: str = Field(foreign_key="tags.id", primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Pydantic models for API
class TagCreate(SQLModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None


class TagUpdate(SQLModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None


class TagResponse(SQLModel):
    id: str
    name: str
    slug: str
    color: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    usage_count: int
    created_at: datetime


class TagCloudItem(SQLModel):
    """Item in tag cloud with frequency."""
    id: str
    name: str
    slug: str
    color: Optional[str]
    icon: Optional[str]
    count: int
