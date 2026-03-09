"""
Analytics and insights models.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlmodel import Field, SQLModel


class ReadingStats(SQLModel):
    """Reading statistics for a time period."""
    total_articles_read: int
    total_articles_archived: int
    total_articles_favorited: int
    total_reading_time_minutes: int
    articles_read_this_week: int
    articles_read_this_month: int
    average_daily_articles: float
    average_reading_time_minutes: float
    reading_streak_days: int
    longest_reading_streak_days: int
    period_days: int


class DeltaTrends(SQLModel):
    """Knowledge Delta scoring trends."""
    daily_averages: List[Dict[str, Any]]  # date, avg_delta, count
    weekly_trend: str  # "increasing", "decreasing", "stable"
    high_delta_percentage: float  # % of articles with delta > 0.7
    average_delta_score: float
    delta_improvement: float  # Change from previous period


class FeedPerformance(SQLModel):
    """Performance metrics for a single feed."""
    feed_id: str
    feed_title: str
    feed_url: str
    articles_count: int
    articles_read: int
    read_ratio: float
    avg_delta_score: float
    avg_reading_time_minutes: float
    last_fetch_status: str
    failure_rate: float


class ActivityDay(SQLModel):
    """Activity data for a single day."""
    date: str
    count: int
    level: int  # 0-4 for heatmap
    articles_read: int
    minutes_spent: int


class ActivityHeatmap(SQLModel):
    """Activity heatmap data."""
    days: int
    start_date: str
    end_date: str
    data: List[ActivityDay]
    max_count: int


class HourlyActivity(SQLModel):
    """Reading activity by hour."""
    hour: int
    count: int
    percentage: float


class CategoryBreakdown(SQLModel):
    """Reading breakdown by category/tag."""
    category: str
    count: int
    percentage: float
    avg_delta_score: float


class TopTagStat(SQLModel):
    """Statistics for a top-used tag."""
    tag_id: str
    tag_name: str
    tag_color: Optional[str]
    count: int
    articles_read: int
    avg_delta_score: float


class ReadingInsight(SQLModel):
    """AI-generated or computed reading insight."""
    type: str  # "trend", "suggestion", "achievement", "pattern"
    title: str
    description: str
    metric: Optional[str]
    value: Optional[Any]
    icon: Optional[str]


class AnalyticsDashboard(SQLModel):
    """Complete analytics dashboard data."""
    period: str  # "7d", "30d", "90d", "1y"
    generated_at: datetime
    
    reading_stats: ReadingStats
    delta_trends: DeltaTrends
    feed_performance: List[FeedPerformance]
    activity_heatmap: ActivityHeatmap
    hourly_activity: List[HourlyActivity]
    category_breakdown: List[CategoryBreakdown]
    top_tags: List[TopTagStat]
    insights: List[ReadingInsight]


class AnalyticsSnapshot(SQLModel, table=True):
    """Daily analytics snapshot for historical tracking."""
    __tablename__ = "analytics_snapshots"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Date of snapshot
    snapshot_date: date = Field(index=True)
    
    # Aggregated metrics
    articles_read: int = Field(default=0)
    articles_archived: int = Field(default=0)
    articles_favorited: int = Field(default=0)
    total_reading_time_minutes: int = Field(default=0)
    avg_delta_score: float = Field(default=0.0)
    
    # JSON data for detailed breakdowns
    hourly_breakdown: str = Field(default="[]")  # JSON array
    category_breakdown: str = Field(default="[]")  # JSON array
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class AnalyticsPeriod(str):
    """Analytics time period."""
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "1y"


class ExportAnalyticsRequest(SQLModel):
    format: str = "json"  # json, csv
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metrics: List[str] = ["reading_stats", "delta_trends"]
