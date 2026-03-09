from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class Feed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str = Field(index=True, unique=True)
    last_fetched: Optional[datetime] = None
    articles: List["Article"] = Relationship(back_populates="feed")

class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    url: str = Field(index=True)
    published_at: datetime
    feed_id: Optional[int] = Field(default=None, foreign_key="feed.id")
    feed: Optional[Feed] = Relationship(back_populates="articles")

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: Optional[str] = None
    file_path: str
    content: str  # Full extracted text for search
    added_at: datetime = Field(default_factory=datetime.utcnow)
