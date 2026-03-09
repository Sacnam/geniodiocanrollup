"""
User model with budget tracking and brief preferences.
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.article import UserArticleContext
    from app.models.brief import Brief
    from app.models.feed import Feed, UserFeed


class UserTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class User(SQLModel, table=True):
    """User account with AI budget tracking."""
    __tablename__ = "users"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: Optional[str] = Field(default=None)
    
    # Profile
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Tier & Billing
    tier: UserTier = Field(default=UserTier.STARTER)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # AI Budget Tracking (monthly)
    monthly_ai_budget: float = Field(default=2.0)  # BUDGET_STARTER
    ai_budget_used_this_month: float = Field(default=0.0)
    budget_resets_at: Optional[datetime] = None
    
    # Brief Preferences
    timezone: str = Field(default="UTC")
    brief_preferred_time: str = Field(default="08:00")  # HH:MM format
    email_delivery_enabled: bool = Field(default=True)
    
    # Auth
    google_oauth_id: Optional[str] = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    last_login_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships (initialized after model creation)
    feeds: List["Feed"] = Relationship(back_populates="user")
    user_feeds: List["UserFeed"] = Relationship(back_populates="user")
    article_contexts: List["UserArticleContext"] = Relationship(back_populates="user")
    briefs: List["Brief"] = Relationship(back_populates="user")
    
    @property
    def budget_remaining(self) -> float:
        return max(0.0, self.monthly_ai_budget - self.ai_budget_used_this_month)
    
    @property
    def budget_percentage_remaining(self) -> float:
        if self.monthly_ai_budget <= 0:
            return 0.0
        return (self.budget_remaining / self.monthly_ai_budget) * 100
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def get_stagger_offset_minutes(self) -> int:
        """Calculate stagger offset for brief delivery (B07)."""
        # Use first 8 chars of user id as hex, convert to int, mod 60
        if self.id:
            return int(self.id[:8], 16) % 60
        return 0
