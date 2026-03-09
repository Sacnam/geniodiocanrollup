"""
Daily Brief endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.core.database import get_session
from app.models.brief import Brief, BriefSection
from app.models.user import User

router = APIRouter(prefix="/briefs", tags=["briefs"])


class BriefSectionResponse(BaseModel):
    type: str
    title: str
    content: str
    articles: List[dict]

    class Config:
        from_attributes = True


class BriefResponse(BaseModel):
    id: str
    title: str
    scheduled_for: str
    delivered_at: Optional[str]
    delivery_status: str
    is_quiet_day: bool
    sections: List[BriefSectionResponse]
    article_count: int
    sources_cited: List[str]
    created_at: str

    class Config:
        from_attributes = True


class BriefListResponse(BaseModel):
    items: List[BriefResponse]
    total: int
    page: int
    page_size: int


class BriefPreferences(BaseModel):
    preferred_time: str = "08:00"
    timezone: str = "UTC"
    days_of_week: List[int] = [0, 1, 2, 3, 4, 5, 6]  # 0=Sunday
    max_articles: int = 15
    email_delivery: bool = True


@router.get("", response_model=BriefListResponse)
def list_briefs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List user's daily briefs."""
    query = select(Brief).where(Brief.user_id == current_user.id)
    
    total = db.exec(select(Brief).where(Brief.user_id == current_user.id).with_only_columns(Brief.id)).all()
    total = len(total) if total else 0
    
    briefs = db.exec(
        query.order_by(Brief.scheduled_for.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    
    items = []
    for brief in briefs:
        items.append(_brief_to_response(brief))
    
    return BriefListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/today", response_model=Optional[BriefResponse])
def get_todays_brief(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get today's brief for the user."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    brief = db.exec(
        select(Brief)
        .where(
            Brief.user_id == current_user.id,
            Brief.scheduled_for >= today,
            Brief.scheduled_for < tomorrow
        )
        .order_by(Brief.scheduled_for.desc())
    ).first()
    
    if not brief:
        return None
    
    return _brief_to_response(brief)


@router.get("/{brief_id}", response_model=BriefResponse)
def get_brief(
    brief_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific brief."""
    brief = db.exec(
        select(Brief).where(
            Brief.id == brief_id,
            Brief.user_id == current_user.id
        )
    ).first()
    
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    
    return _brief_to_response(brief)


@router.get("/preferences", response_model=BriefPreferences)
def get_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user's brief preferences."""
    # Return defaults if not set
    return BriefPreferences(
        preferred_time=current_user.brief_preferred_time or "08:00",
        timezone=current_user.timezone or "UTC",
        email_delivery=current_user.email_delivery_enabled,
    )


@router.put("/preferences")
def update_preferences(
    prefs: BriefPreferences,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update brief preferences."""
    current_user.brief_preferred_time = prefs.preferred_time
    current_user.timezone = prefs.timezone
    current_user.email_delivery_enabled = prefs.email_delivery
    
    db.add(current_user)
    db.commit()
    
    return {"message": "Preferences updated"}


@router.post("/{brief_id}/regenerate")
def regenerate_brief(
    brief_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Manually regenerate a brief."""
    brief = db.exec(
        select(Brief).where(
            Brief.id == brief_id,
            Brief.user_id == current_user.id
        )
    ).first()
    
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    
    from app.tasks.brief_tasks import generate_daily_brief_task
    generate_daily_brief_task.delay(current_user.id)
    
    return {"message": "Brief regeneration queued"}


def _brief_to_response(brief: Brief) -> BriefResponse:
    """Convert Brief model to response."""
    sections = []
    for section in brief.sections:
        sections.append(BriefSectionResponse(
            type=section.section_type,
            title=section.title,
            content=section.content,
            articles=[{"id": a.id, "title": a.title} for a in section.articles] if section.articles else []
        ))
    
    return BriefResponse(
        id=brief.id,
        title=brief.title,
        scheduled_for=brief.scheduled_for.isoformat(),
        delivered_at=brief.delivered_at.isoformat() if brief.delivered_at else None,
        delivery_status=brief.delivery_status,
        is_quiet_day=brief.is_quiet_day,
        sections=sections,
        article_count=brief.article_count,
        sources_cited=brief.sources_cited or [],
        created_at=brief.created_at.isoformat(),
    )
