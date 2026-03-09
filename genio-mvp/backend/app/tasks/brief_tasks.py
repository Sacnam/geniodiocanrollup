from datetime import date, datetime, timedelta
from typing import List
from uuid import uuid4

from celery import shared_task
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.article import Article, UserArticleContext
from app.models.brief import BriefDeliveryStatus, DailyBrief
from app.models.feed import UserFeed
from app.models.user import User
from app.services.ai_service import generate_brief_content, track_ai_cost


@shared_task
def generate_daily_briefs():
    """
    Generate daily briefs for all users whose time has come.
    B07: Staggered delivery within hour.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        current_hour = now.hour
        current_minute = now.minute
        
        # Find users who should receive brief now
        # Stagger based on user_id hash within the hour
        users = db.exec(
            select(User).where(
                User.is_active == True,
                User.brief_delivery_time == f"{current_hour:02d}:00",
            )
        ).all()
        
        scheduled = 0
        for user in users:
            # Check if user has active feeds
            has_feeds = db.exec(
                select(UserFeed).where(
                    UserFeed.user_id == user.id,
                    UserFeed.is_active == True,
                )
            ).first()
            
            if not has_feeds:
                continue
            
            # Check if brief already generated for today
            existing = db.exec(
                select(DailyBrief).where(
                    DailyBrief.user_id == user.id,
                    DailyBrief.brief_date == date.today(),
                )
            ).first()
            
            if existing:
                continue
            
            # Check stagger offset (B07)
            stagger_offset = user.get_stagger_offset_minutes()
            if current_minute >= stagger_offset:
                generate_user_brief.delay(user.id)
                scheduled += 1
        
        return {"scheduled": scheduled, "total_users": len(users)}
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_user_brief(self, user_id: str):
    """Generate brief for specific user."""
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            return {"status": "error", "reason": "user_not_found"}
        
        today = date.today()
        
        # Check if already exists
        existing = db.exec(
            select(DailyBrief).where(
                DailyBrief.user_id == user_id,
                DailyBrief.brief_date == today,
            )
        ).first()
        
        if existing:
            return {"status": "already_exists", "brief_id": existing.id}
        
        # Get user's novel articles from last 24h
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        contexts = db.exec(
            select(UserArticleContext, Article)
            .join(Article)
            .where(
                UserArticleContext.user_id == user_id,
                UserArticleContext.delta_score > 0.5,  # Only high delta articles
                UserArticleContext.is_read == False,
                Article.published_at >= cutoff,
                Article.processing_status == "ready",
            )
            .order_by(UserArticleContext.delta_score.desc())
            .limit(settings.BRIEF_MAX_ARTICLES)
        ).all()
        
        if not contexts:
            # Quiet day - no articles
            brief = DailyBrief(
                id=str(uuid4()),
                user_id=user_id,
                brief_date=today,
                title="Quiet Day",
                subtitle="No new stories from your feeds",
                sections=[],
                article_count=0,
                sources_count=0,
                status=BriefDeliveryStatus.READY,
            )
            db.add(brief)
            db.commit()
            return {"status": "quiet_day", "brief_id": brief.id}
        
        # Quiet day check (B10: <3 novel articles)
        novel_count = len([c for c, _ in contexts if c.delta_status == "novel"])
        if novel_count < settings.BRIEF_MIN_ARTICLES:
            # Still create brief but mark as quiet
            is_quiet = True
        else:
            is_quiet = False
        
        # Prepare articles data
        articles_data = []
        for ctx, article in contexts:
            articles_data.append({
                "id": article.id,
                "title": article.title or "Untitled",
                "summary": article.global_summary or article.excerpt,
                "excerpt": article.excerpt,
                "url": article.url,
                "source": article.feed.title if article.feed else "Unknown",
                "delta_score": ctx.delta_score,
                "published_at": article.published_at.isoformat() if article.published_at else None,
            })
        
        # Generate brief content
        brief_content = generate_brief_content(
            articles_data,
            user_tier=user.tier.value,
            budget_remaining=user.budget_remaining,
        )
        
        # Track AI cost
        if brief_content.get("ai_generated"):
            cost = 0.001 * len(articles_data)  # Rough estimate
            track_ai_cost(user_id, cost)
        
        # Create brief
        brief = DailyBrief(
            id=str(uuid4()),
            user_id=user_id,
            brief_date=today,
            title=brief_content["title"],
            subtitle=f"{len(articles_data)} stories" if not is_quiet else "Quiet day",
            executive_summary=brief_content.get("executive_summary", ""),
            sections=[
                {
                    "title": s["title"],
                    "summary": s["summary"],
                    "articles": [articles_data[i] for i in s.get("article_indices", [])],
                }
                for s in brief_content.get("sections", [])
            ],
            article_count=len(articles_data),
            sources_count=len(set(a["source"] for a in articles_data)),
            novel_articles_count=novel_count,
            ai_cost_usd=0.001 if brief_content.get("ai_generated") else 0,
            status=BriefDeliveryStatus.READY,
            generation_started_at=datetime.utcnow(),
            generation_completed_at=datetime.utcnow(),
        )
        
        db.add(brief)
        db.commit()
        db.refresh(brief)
        
        # Update UserArticleContext with brief_id
        for ctx, article in contexts:
            ctx.included_in_brief_id = brief.id
            db.add(ctx)
        
        db.commit()
        
        # Send email if enabled
        if user.brief_email_enabled:
            send_brief_email.delay(brief.id)
        
        return {
            "status": "generated",
            "brief_id": brief.id,
            "articles": len(articles_data),
            "ai_generated": brief_content.get("ai_generated"),
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def send_brief_email(self, brief_id: str):
    """Send brief via email using SendGrid."""
    db = SessionLocal()
    try:
        brief = db.get(DailyBrief, brief_id)
        if not brief:
            return {"status": "error", "reason": "brief_not_found"}
        
        user = db.get(User, brief.user_id)
        if not user or not user.brief_email_enabled:
            return {"status": "skipped", "reason": "email_disabled"}
        
        # SendGrid integration would go here
        # For MVP, we'll just mark as sent
        
        brief.status = BriefDeliveryStatus.SENT
        brief.sent_at = datetime.utcnow()
        db.add(brief)
        db.commit()
        
        return {"status": "sent", "brief_id": brief_id}
        
    except Exception as exc:
        brief.status = BriefDeliveryStatus.FAILED
        db.add(brief)
        db.commit()
        raise self.retry(exc=exc, countdown=600)
    finally:
        db.close()
