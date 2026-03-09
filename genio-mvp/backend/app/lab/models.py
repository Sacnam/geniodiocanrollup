"""
Scout Agent models for Lab module (v3.0).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import Field, SQLModel


class ScoutStatus(str, Enum):
    """Status of a Scout agent."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ScoutSource(str, Enum):
    """Data sources for Scout agents."""
    FEEDS = "feeds"           # User's RSS feeds
    DOCUMENTS = "documents"   # User's library
    WEB = "web"               # General web search
    ARXIV = "arxiv"           # Academic papers
    GITHUB = "github"         # Code repositories
    NEWS = "news"             # News APIs


class ScoutSchedule(str, Enum):
    """Scheduling options for Scout agents."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    REALTIME = "realtime"


class ScoutAgent(SQLModel, table=True):
    """
    Scout Agent - AI-powered research assistant.
    Monitors sources and finds relevant information.
    """
    __tablename__ = "scout_agents"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Identity
    name: str
    description: Optional[str] = None
    
    # Query configuration
    research_question: str  # Main research question
    keywords: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    exclude_keywords: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    
    # Data sources
    sources: List[str] = Field(default=["feeds"], sa_column=Field(sa_type=List[str]))
    source_config: Dict[str, Any] = Field(default={}, sa_column=Field(sa_type=Dict[str, Any]))
    
    # Filters
    min_relevance_score: float = Field(default=0.7)  # Minimum similarity threshold
    content_types: List[str] = Field(default=["article", "paper"], sa_column=Field(sa_type=List[str]))
    date_range_days: int = Field(default=30)  # Only recent content
    
    # Schedule
    schedule: str = Field(default="daily")  # hourly, daily, weekly
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    # Status
    status: ScoutStatus = Field(default=ScoutStatus.IDLE)
    is_active: bool = Field(default=True)
    
    # Results
    total_findings: int = Field(default=0)
    unread_findings: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScoutFinding(SQLModel, table=True):
    """
    A finding discovered by a Scout agent.
    Links to source content with relevance explanation.
    """
    __tablename__ = "scout_findings"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    scout_id: str = Field(foreign_key="scout_agents.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Source reference (polymorphic)
    source_type: str  # "article", "document", "web_page"
    source_id: str    # ID in respective table
    source_url: str
    source_title: str
    
    # Relevance
    relevance_score: float  # 0-1 similarity to research question
    explanation: str  # AI explanation of why this is relevant
    matched_keywords: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    
    # Content summary
    key_insights: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    contradictions: Optional[str] = None  # If finding contradicts existing knowledge
    
    # User interaction
    is_read: bool = Field(default=False)
    is_saved: bool = Field(default=False)
    is_dismissed: bool = Field(default=False)
    user_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoutExecution(SQLModel, table=True):
    """
    Log of Scout agent executions.
    For monitoring and debugging.
    """
    __tablename__ = "scout_executions"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    scout_id: str = Field(foreign_key="scout_agents.id", index=True)
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    status: str = Field(default="running")  # running, completed, failed
    error_message: Optional[str] = None
    
    # Execution metrics
    sources_checked: int = Field(default=0)
    items_scanned: int = Field(default=0)
    findings_generated: int = Field(default=0)
    execution_time_ms: Optional[int] = None
    
    # Cost tracking
    ai_cost_usd: float = Field(default=0.0)


class ScoutInsight(SQLModel, table=True):
    """
    Aggregated insights from Scout findings over time.
    Patterns, trends, and synthesized knowledge.
    """
    __tablename__ = "scout_insights"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    scout_id: str = Field(foreign_key="scout_agents.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    insight_type: str  # "trend", "pattern", "gap", "opportunity"
    title: str
    description: str
    
    # Supporting evidence
    supporting_findings: List[str] = Field(default=[], sa_column=Field(sa_type=List[str]))
    confidence_score: float
    
    # Temporal
    period_start: datetime
    period_end: datetime
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
