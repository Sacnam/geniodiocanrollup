"""
API endpoints for analytics dashboard.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("/reading-stats")
async def get_reading_stats(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get reading statistics for the specified period."""
    return analytics_service.get_reading_stats(
        user_id=current_user.id,
        days=days
    )


@router.get("/delta-trends")
async def get_delta_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get Knowledge Delta scoring trends."""
    return analytics_service.get_delta_trends(
        user_id=current_user.id,
        days=days
    )


@router.get("/feed-performance")
async def get_feed_performance(
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for all subscribed feeds."""
    return analytics_service.get_feed_performance(
        user_id=current_user.id
    )


@router.get("/activity-heatmap")
async def get_activity_heatmap(
    days: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get activity data for heatmap visualization (GitHub-style)."""
    return analytics_service.get_activity_heatmap(
        user_id=current_user.id,
        days=days
    )


@router.get("/hourly-activity")
async def get_hourly_activity(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user)
):
    """Get reading activity breakdown by hour of day."""
    return analytics_service.get_hourly_activity(
        user_id=current_user.id,
        days=days
    )


@router.get("/top-tags")
async def get_top_tags(
    limit: int = Query(10, ge=5, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get most used tags with statistics."""
    return analytics_service.get_top_tags(
        user_id=current_user.id,
        limit=limit
    )


@router.get("/insights")
async def get_insights(
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated reading insights and suggestions."""
    return analytics_service.get_insights(
        user_id=current_user.id
    )


@router.get("/dashboard")
async def get_full_dashboard(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user)
):
    """Get complete analytics dashboard in one request."""
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)
    
    from datetime import datetime
    
    return {
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "reading_stats": analytics_service.get_reading_stats(current_user.id, days),
        "delta_trends": analytics_service.get_delta_trends(current_user.id, days),
        "feed_performance": analytics_service.get_feed_performance(current_user.id),
        "activity_heatmap": analytics_service.get_activity_heatmap(current_user.id, min(days, 90)),
        "hourly_activity": analytics_service.get_hourly_activity(current_user.id, days),
        "top_tags": analytics_service.get_top_tags(current_user.id),
        "insights": analytics_service.get_insights(current_user.id)
    }


@router.get("/export")
async def export_analytics(
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export analytics data."""
    # For now, return JSON data
    # In production, would generate CSV/Excel file
    
    dashboard = await get_full_dashboard("1y", current_user)
    
    return {
        "format": format,
        "generated_at": dashboard["generated_at"],
        "data": dashboard
    }
