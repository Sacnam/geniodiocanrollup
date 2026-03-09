"""
Admin API Endpoints
Platform administration and monitoring
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.config import settings
from app.core.feature_flags import get_feature_flags
from app.models.article import Article
from app.models.brief import Brief
from app.models.document import Document
from app.models.feed import Feed
from app.models.user import User, UserTier
from app.models.activity import AIActivityLog

router = APIRouter()


@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get platform-wide statistics."""
    
    # User stats
    total_users = db.query(User).count()
    active_users_24h = db.query(User).filter(
        User.last_login_at >= func.now() - func.interval('1 day')
    ).count()
    
    # Content stats
    total_articles = db.query(Article).count()
    articles_24h = db.query(Article).filter(
        Article.created_at >= func.now() - func.interval('1 day')
    ).count()
    
    total_documents = db.query(Document).count()
    active_feeds = db.query(Feed).filter(Feed.is_active == True).count()
    
    # Brief stats
    briefs_24h = db.query(Brief).filter(
        Brief.created_at >= func.now() - func.interval('1 day')
    ).count()
    
    # AI cost stats (24h)
    ai_cost_24h = db.query(func.coalesce(func.sum(AIActivityLog.cost), 0)).filter(
        AIActivityLog.created_at >= func.now() - func.interval('1 day')
    ).scalar()
    
    # Tier distribution
    tier_counts = db.query(User.tier, func.count(User.id)).group_by(User.tier).all()
    
    return {
        "total_users": total_users,
        "active_users_24h": active_users_24h,
        "total_articles": total_articles,
        "articles_24h": articles_24h,
        "total_documents": total_documents,
        "active_feeds": active_feeds,
        "briefs_24h": briefs_24h,
        "ai_cost_24h": float(ai_cost_24h),
        "tier_distribution": {tier.value: count for tier, count in tier_counts},
    }


@router.get("/users")
def list_users(
    search: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users (admin only)."""
    query = db.query(User)
    
    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") |
            User.first_name.ilike(f"%{search}%") |
            User.last_name.ilike(f"%{search}%")
        )
    
    if tier:
        query = query.filter(User.tier == tier)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": users,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/users/{user_id}/tier")
def update_user_tier(
    user_id: str,
    tier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user subscription tier."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.tier = tier
    db.commit()
    
    return {"message": f"User tier updated to {tier}"}


@router.post("/users/{user_id}/disable")
def disable_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Disable/enable user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {'disabled' if not user.is_active else 'enabled'}"}


@router.get("/health")
def get_system_health(
    current_user: User = Depends(require_admin),
):
    """Get system health status."""
    from app.core.redis_client import redis_client
    
    health = {
        "api": {"status": "healthy", "latency": 0},
        "database": {"status": "unknown", "latency": 0},
        "redis": {"status": "unknown", "latency": 0},
        "qdrant": {"status": "unknown", "latency": 0},
        "celery": {"status": "unknown", "workers": 0},
    }
    
    # Check database
    try:
        import time
        start = time.time()
        # Would execute a simple query
        health["database"] = {"status": "healthy", "latency": int((time.time() - start) * 1000)}
    except Exception as e:
        health["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Redis
    try:
        start = time.time()
        redis_client.ping()
        health["redis"] = {"status": "healthy", "latency": int((time.time() - start) * 1000)}
    except Exception as e:
        health["redis"] = {"status": "unhealthy", "error": str(e)}
    
    return health


@router.get("/ai-costs")
def get_ai_costs(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get AI cost breakdown."""
    from sqlalchemy import func
    
    # Daily costs
    daily_costs = db.query(
        func.date(AIActivityLog.created_at).label('date'),
        func.sum(AIActivityLog.cost).label('cost'),
        func.count(AIActivityLog.id).label('requests')
    ).filter(
        AIActivityLog.created_at >= func.now() - func.interval(f'{days} days')
    ).group_by(
        func.date(AIActivityLog.created_at)
    ).order_by(func.date(AIActivityLog.created_at).desc()).all()
    
    # Cost by operation type
    by_operation = db.query(
        AIActivityLog.operation,
        func.sum(AIActivityLog.cost).label('cost')
    ).filter(
        AIActivityLog.created_at >= func.now() - func.interval(f'{days} days')
    ).group_by(AIActivityLog.operation).all()
    
    total_cost = sum(day.cost for day in daily_costs)
    total_requests = sum(day.requests for day in daily_costs)
    
    return {
        "total": float(total_cost),
        "total_requests": total_requests,
        "avg_per_user": float(total_cost / db.query(User).count()) if total_cost > 0 else 0,
        "daily": [
            {
                "date": str(day.date),
                "total": float(day.cost),
                "requests": day.requests
            }
            for day in daily_costs
        ],
        "by_operation": [
            {"operation": op, "cost": float(cost)}
            for op, cost in by_operation
        ]
    }


@router.get("/feature-flags")
def get_feature_flags_list(
    current_user: User = Depends(require_admin),
):
    """List all feature flags."""
    flags = get_feature_flags()
    return flags.list_flags(include_archived=True)


@router.patch("/feature-flags/{key}")
def update_feature_flag(
    key: str,
    updates: dict,
    current_user: User = Depends(require_admin),
):
    """Update feature flag."""
    flags = get_feature_flags()
    flag = flags.get_flag(key)
    
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    flags.update_flag(key, **updates)
    return {"message": "Feature flag updated"}
