"""
Feed management endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.core.database import get_session
from app.models.feed import Feed, FeedStatus
from app.models.user import User
from app.tasks.feed_tasks import fetch_feed_task

router = APIRouter(prefix="/feeds", tags=["feeds"])


class FeedCreate(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    category: Optional[str] = "Uncategorized"


class FeedUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[FeedStatus] = None


class FeedResponse(BaseModel):
    id: str
    url: str
    title: Optional[str]
    category: str
    status: FeedStatus
    last_fetched_at: Optional[str]
    article_count: int
    failure_count: int
    fetch_interval_minutes: int

    class Config:
        from_attributes = True


class OpmlImportResponse(BaseModel):
    imported: int
    failed: int
    feeds: List[FeedResponse]


@router.get("", response_model=List[FeedResponse])
def list_feeds(
    category: Optional[str] = None,
    status: Optional[FeedStatus] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List user's feeds with optional filtering."""
    query = select(Feed).where(Feed.user_id == current_user.id)
    
    if category:
        query = query.where(Feed.category == category)
    if status:
        query = query.where(Feed.status == status)
    
    feeds = db.exec(query.order_by(Feed.category, Feed.title)).all()
    return feeds


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
def create_feed(
    feed_data: FeedCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add a new feed."""
    # Check for duplicate URL for this user
    existing = db.exec(
        select(Feed).where(
            Feed.user_id == current_user.id,
            Feed.url == str(feed_data.url)
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed already exists"
        )
    
    feed = Feed(
        user_id=current_user.id,
        url=str(feed_data.url),
        title=feed_data.title,
        category=feed_data.category or "Uncategorized",
        status=FeedStatus.ACTIVE,
        fetch_interval_minutes=60,
    )
    
    db.add(feed)
    db.commit()
    db.refresh(feed)
    
    # Trigger initial fetch
    fetch_feed_task.delay(feed.id)
    
    return feed


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(
    feed_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific feed."""
    feed = db.exec(
        select(Feed).where(Feed.id == feed_id, Feed.user_id == current_user.id)
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    return feed


@router.patch("/{feed_id}", response_model=FeedResponse)
def update_feed(
    feed_id: str,
    feed_data: FeedUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a feed."""
    feed = db.exec(
        select(Feed).where(Feed.id == feed_id, Feed.user_id == current_user.id)
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    if feed_data.title is not None:
        feed.title = feed_data.title
    if feed_data.category is not None:
        feed.category = feed_data.category
    if feed_data.status is not None:
        feed.status = feed_data.status
    
    db.add(feed)
    db.commit()
    db.refresh(feed)
    
    return feed


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed(
    feed_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a feed."""
    feed = db.exec(
        select(Feed).where(Feed.id == feed_id, Feed.user_id == current_user.id)
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(feed)
    db.commit()
    
    return None


@router.post("/{feed_id}/refresh")
def refresh_feed(
    feed_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a feed refresh."""
    feed = db.exec(
        select(Feed).where(Feed.id == feed_id, Feed.user_id == current_user.id)
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Trigger async fetch
    fetch_feed_task.delay(feed_id)
    
    return {"message": "Feed refresh queued", "feed_id": feed_id}


@router.post("/import/opml", response_model=OpmlImportResponse)
async def import_opml(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Import feeds from OPML file."""
    import xml.etree.ElementTree as ET
    
    content = await file.read()
    
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OPML file"
        )
    
    imported = 0
    failed = 0
    feeds = []
    
    # Parse OPML outline elements
    for outline in root.findall(".//outline[@type='rss']"):
        url = outline.get("xmlUrl")
        title = outline.get("text") or outline.get("title")
        category = outline.get("category", "Uncategorized")
        
        if not url:
            failed += 1
            continue
        
        # Check for duplicates
        existing = db.exec(
            select(Feed).where(
                Feed.user_id == current_user.id,
                Feed.url == url
            )
        ).first()
        
        if existing:
            continue
        
        try:
            feed = Feed(
                user_id=current_user.id,
                url=url,
                title=title,
                category=category,
                status=FeedStatus.ACTIVE,
                fetch_interval_minutes=60,
            )
            db.add(feed)
            db.commit()
            db.refresh(feed)
            feeds.append(feed)
            imported += 1
            
            # Trigger fetch
            fetch_feed_task.delay(feed.id)
            
        except Exception:
            failed += 1
            db.rollback()
    
    return OpmlImportResponse(
        imported=imported,
        failed=failed,
        feeds=feeds
    )


@router.get("/categories/list")
def list_categories(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all feed categories for the user."""
    from sqlalchemy import func
    
    result = db.exec(
        select(Feed.category, func.count(Feed.id))
        .where(Feed.user_id == current_user.id)
        .group_by(Feed.category)
        .order_by(Feed.category)
    ).all()
    
    return [{"category": cat, "count": cnt} for cat, cnt in result]
