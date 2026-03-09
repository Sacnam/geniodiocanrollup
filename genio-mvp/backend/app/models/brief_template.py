"""
Brief template models for customizable Daily Briefs.
"""
from datetime import datetime, time
from typing import Optional, List
from enum import Enum

from sqlmodel import Field, SQLModel


class BriefLayout(str, Enum):
    """Brief layout styles."""
    COMPACT = "compact"  # Minimal, list view
    STANDARD = "standard"  # Balanced sections
    DETAILED = "detailed"  # Full content with analysis
    EXECUTIVE = "executive"  # Summary only, high-level
    MAGAZINE = "magazine"  # Visual, magazine-style


class BriefSectionType(str, Enum):
    """Types of sections in a brief."""
    HEADLINES = "headlines"  # Top stories
    HIGH_DELTA = "high_delta"  # High novelty content
    TRENDING = "trending"  # Most discussed
    SAVED_SEARCHES = "saved_searches"  # Matches saved searches
    CATEGORY_SPOTLIGHT = "category_spotlight"  # Focus on specific categories
    READING_LIST = "reading_list"  # From reading list
    SMART_SUGGESTIONS = "smart_suggestions"  # AI recommendations


class BriefDeliveryTime(str, Enum):
    """Brief delivery schedule."""
    MORNING = "08:00"  # 8 AM
    LUNCH = "12:00"  # 12 PM
    EVENING = "18:00"  # 6 PM
    NIGHT = "21:00"  # 9 PM
    CUSTOM = "custom"


class BriefTemplate(SQLModel, table=True):
    """Custom brief template configuration."""
    __tablename__ = "brief_templates"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Template info
    name: str
    description: Optional[str] = None
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)
    
    # Layout and styling
    layout: str = Field(default=BriefLayout.STANDARD)
    accent_color: Optional[str] = None  # Hex color
    
    # Content configuration
    max_articles: int = Field(default=10)  # Max articles per brief
    min_delta_score: float = Field(default=0.0)  # Minimum novelty threshold
    include_read: bool = Field(default=False)  # Include already read articles
    
    # Delivery schedule
    delivery_time: str = Field(default=BriefDeliveryTime.MORNING)
    delivery_days: str = Field(default="[1,2,3,4,5]")  # JSON array, 1=Monday
    timezone: str = Field(default="UTC")
    
    # Sections (JSON array of section configs)
    sections: str = Field(default="[]")
    
    # Category preferences
    preferred_categories: str = Field(default="[]")  # Tag IDs to prioritize
    excluded_categories: str = Field(default="[]")  # Tag IDs to exclude
    
    # Feed preferences
    preferred_feeds: str = Field(default="[]")  # Feed IDs to prioritize
    excluded_feeds: str = Field(default="[]")  # Feed IDs to exclude
    
    # AI settings
    ai_summary_length: str = Field(default="medium")  # short, medium, long
    ai_persona: Optional[str] = None  # "professional", "casual", "academic"
    ai_focus_areas: str = Field(default="[]")  # Topics to emphasize
    
    # Statistics
    generated_count: int = Field(default=0)
    last_generated_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BriefSectionConfig(SQLModel):
    """Configuration for a brief section."""
    type: str  # BriefSectionType
    title: Optional[str] = None  # Custom title
    position: int = 0  # Order in brief
    enabled: bool = True
    max_items: int = 5  # Max items in this section
    filter_tags: List[str] = []  # Filter by tags
    filter_delta_min: Optional[float] = None
    sort_by: str = "delta_score"  # delta_score, date, trending


# API Schemas
class BriefTemplateCreate(SQLModel):
    name: str
    description: Optional[str] = None
    layout: str = BriefLayout.STANDARD
    max_articles: int = 10
    min_delta_score: float = 0.0
    delivery_time: str = BriefDeliveryTime.MORNING
    delivery_days: List[int] = [1, 2, 3, 4, 5]


class BriefTemplateUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[str] = None
    is_active: Optional[bool] = None
    max_articles: Optional[int] = None
    min_delta_score: Optional[float] = None
    delivery_time: Optional[str] = None
    delivery_days: Optional[List[int]] = None
    sections: Optional[List[BriefSectionConfig]] = None


class BriefTemplateResponse(SQLModel):
    id: str
    name: str
    description: Optional[str]
    is_default: bool
    is_active: bool
    layout: str
    max_articles: int
    min_delta_score: float
    delivery_time: str
    delivery_days: List[int]
    sections: List[BriefSectionConfig]
    generated_count: int
    created_at: datetime


class BriefPreviewRequest(SQLModel):
    """Request to generate a preview brief."""
    template_id: str
    date: Optional[str] = None  # ISO date, defaults to today


class BriefPreviewResponse(SQLModel):
    """Preview of a brief."""
    template_id: str
    generated_at: datetime
    sections: List[Dict]
    total_articles: int
    estimated_read_time_minutes: int
