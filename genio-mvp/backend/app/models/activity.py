"""
AI Activity Log Model
Tracks all AI operations for cost monitoring and analytics.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AIActivityLog(SQLModel, table=True):
    """Log of AI API calls for cost tracking and analytics."""
    __tablename__ = "ai_activity_logs"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Operation details
    operation: str  # embedding, summary, brief_generation, graph_extraction, etc.
    model: str  # gpt-4o, gemini-flash, text-embedding-3-small, etc.
    
    # Token usage
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    
    # Cost tracking
    cost: float = Field(default=0.0)  # USD
    
    # Context
    resource_type: Optional[str] = None  # article, document, brief, etc.
    resource_id: Optional[str] = None
    
    # Performance
    latency_ms: Optional[int] = None  # Request duration
    
    # Error tracking
    status: str = Field(default="success")  # success, error, cached
    error_message: Optional[str] = None
    
    # Metadata
    cached: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class AIActivityLogCreate(SQLModel):
    """Schema for creating activity log entry."""
    user_id: str
    operation: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    latency_ms: Optional[int] = None
    status: str = "success"
    error_message: Optional[str] = None
    cached: bool = False


class AIActivitySummary(SQLModel):
    """Summary of AI activity for a user."""
    total_cost_24h: float
    total_cost_7d: float
    total_cost_30d: float
    total_requests_24h: int
    top_operations: list
    top_models: list
