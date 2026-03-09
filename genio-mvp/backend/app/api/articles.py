"""
Article reading endpoints with Knowledge Delta scoring.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.api.auth import get_current_user
from app.core.database import get_session
from app.models.article import Article, ProcessingStatus, UserArticleContext
from app.models.user import User

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleResponse(BaseModel):
    id: str
    title: Optional[str]
    url: str
    source_feed_title: Optional[str]
    published_at: Optional[str]
    excerpt: Optional[str]
    content: Optional[str]
    global_summary: Optional[str]
    delta_score: float
    is_read: bool
    is_archived: bool
    cluster_id: Optional[str]
    is_duplicate: bool
    created_at: str

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    items: List[ArticleResponse]
    total: int
    page: int
    page_size: int


class ArticleUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None


@router.get("", response_model=ArticleListResponse)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_delta: float = Query(0.0, ge=0.0, le=1.0),
    max_delta: float = Query(1.0, ge=0.0, le=1.0),
    is_read: Optional[bool] = None,
    is_archived: bool = False,
    feed_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List articles with Knowledge Delta filtering.
    
    - min_delta/max_delta: Filter by novelty score (0-1)
    - is_read: Filter by read status
    - is_archived: Include archived articles
    - feed_id: Filter by specific feed
    - search: Full-text search in title/content
    """
    # Build base query joining Article and UserArticleContext
    query = (
        select(Article, UserArticleContext)
        .join(UserArticleContext, UserArticleContext.article_id == Article.id)
        .where(
            UserArticleContext.user_id == current_user.id,
            UserArticleContext.delta_score >= min_delta,
            UserArticleContext.delta_score <= max_delta,
            UserArticleContext.is_archived == is_archived,
            UserArticleContext.is_duplicate == False,
            Article.processing_status == ProcessingStatus.READY,
        )
    )
    
    if is_read is not None:
        query = query.where(UserArticleContext.is_read == is_read)
    
    if feed_id:
        query = query.where(Article.source_feed_id == feed_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Article.title.ilike(search_term)) |
            (Article.content.ilike(search_term))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.exec(count_query).one()
    
    # Apply sorting and pagination
    query = (
        query.order_by(UserArticleContext.delta_score.desc(), Article.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    results = db.exec(query).all()
    
    items = []
    for article, context in results:
        items.append(ArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            source_feed_title=article.source_feed_title,
            published_at=article.published_at.isoformat() if article.published_at else None,
            excerpt=article.excerpt,
            content=article.content if article.content else None,
            global_summary=article.global_summary,
            delta_score=context.delta_score,
            is_read=context.is_read,
            is_archived=context.is_archived,
            cluster_id=context.cluster_id,
            is_duplicate=context.is_duplicate,
            created_at=article.created_at.isoformat(),
        ))
    
    return ArticleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific article."""
    result = db.exec(
        select(Article, UserArticleContext)
        .join(UserArticleContext, UserArticleContext.article_id == Article.id)
        .where(
            Article.id == article_id,
            UserArticleContext.user_id == current_user.id
        )
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article, context = result
    
    return ArticleResponse(
        id=article.id,
        title=article.title,
        url=article.url,
        source_feed_title=article.source_feed_title,
        published_at=article.published_at.isoformat() if article.published_at else None,
        excerpt=article.excerpt,
        content=article.content,
        global_summary=article.global_summary,
        delta_score=context.delta_score,
        is_read=context.is_read,
        is_archived=context.is_archived,
        cluster_id=context.cluster_id,
        is_duplicate=context.is_duplicate,
        created_at=article.created_at.isoformat(),
    )


@router.patch("/{article_id}")
def update_article(
    article_id: str,
    update: ArticleUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update article status (read/unread/archive)."""
    context = db.exec(
        select(UserArticleContext)
        .where(
            UserArticleContext.article_id == article_id,
            UserArticleContext.user_id == current_user.id
        )
    ).first()
    
    if not context:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if update.is_read is not None:
        context.is_read = update.is_read
        if update.is_read:
            context.read_at = datetime.utcnow()
    
    if update.is_archived is not None:
        context.is_archived = update.is_archived
    
    db.add(context)
    db.commit()
    
    return {"message": "Article updated"}


@router.post("/{article_id}/read")
def mark_read(
    article_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Mark article as read."""
    return update_article(article_id, ArticleUpdate(is_read=True), db, current_user)


@router.post("/{article_id}/unread")
def mark_unread(
    article_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Mark article as unread."""
    return update_article(article_id, ArticleUpdate(is_read=False), db, current_user)


@router.post("/{article_id}/archive")
def archive_article(
    article_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Archive an article."""
    return update_article(article_id, ArticleUpdate(is_archived=True), db, current_user)


@router.get("/budget/status")
def get_budget_status(
    current_user: User = Depends(get_current_user)
):
    """Get AI budget status for current user."""
    from app.core.intelligent_router import IntelligentRouter
    
    router = IntelligentRouter(
        current_user.budget_remaining,
        current_user.monthly_ai_budget
    )
    
    return {
        "monthly_budget": current_user.monthly_ai_budget,
        "budget_used": current_user.ai_budget_used_this_month,
        "budget_remaining": current_user.budget_remaining,
        "percentage_used": round(
            (current_user.ai_budget_used_this_month / current_user.monthly_ai_budget * 100), 2
        ) if current_user.monthly_ai_budget > 0 else 0,
        "degradation_level": router.get_degradation_level(),
    }


@router.get("/stats/overview")
def get_stats(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get article statistics for the user."""
    # Total unread articles
    unread_count = db.exec(
        select(func.count(UserArticleContext.id))
        .where(
            UserArticleContext.user_id == current_user.id,
            UserArticleContext.is_read == False,
            UserArticleContext.is_duplicate == False,
            UserArticleContext.is_archived == False,
        )
    ).one()
    
    # Articles by delta score range
    high_novelty = db.exec(
        select(func.count(UserArticleContext.id))
        .where(
            UserArticleContext.user_id == current_user.id,
            UserArticleContext.delta_score >= 0.85,
            UserArticleContext.is_duplicate == False,
        )
    ).one()
    
    medium_novelty = db.exec(
        select(func.count(UserArticleContext.id))
        .where(
            UserArticleContext.user_id == current_user.id,
            UserArticleContext.delta_score >= 0.70,
            UserArticleContext.delta_score < 0.85,
            UserArticleContext.is_duplicate == False,
        )
    ).one()
    
    # Today's articles
    today = datetime.utcnow() - timedelta(days=1)
    today_count = db.exec(
        select(func.count(UserArticleContext.id))
        .join(Article, Article.id == UserArticleContext.article_id)
        .where(
            UserArticleContext.user_id == current_user.id,
            Article.created_at >= today,
            UserArticleContext.is_duplicate == False,
        )
    ).one()
    
    return {
        "unread_count": unread_count,
        "high_novelty_count": high_novelty,
        "medium_novelty_count": medium_novelty,
        "today_count": today_count,
    }
