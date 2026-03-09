from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import feedparser
import requests
from celery import shared_task
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import SessionLocal
from app.models.article import Article, ProcessingStatus
from app.models.feed import Feed
from app.tasks.celery import celery_app


@shared_task(bind=True, max_retries=3)
def fetch_feed_task(self, feed_id: str):
    """
    Fetch and parse RSS/Atom feed.
    Extract article metadata and queue for processing.
    """
    db = SessionLocal()
    try:
        feed = db.get(Feed, feed_id)
        if not feed or not feed.is_active:
            return {"status": "skipped", "reason": "feed_not_found_or_inactive"}
        
        # Fetch feed with conditional GET
        headers = {
            "User-Agent": "GenioBot/1.0 (RSS Aggregator; https://genio.ai)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        }
        
        if feed.last_etag:
            headers["If-None-Match"] = feed.last_etag
        if feed.last_modified:
            headers["If-Modified-Since"] = feed.last_modified
        
        try:
            response = requests.get(
                feed.url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            # Update failure count
            feed.failure_count += 1
            feed.last_failure_at = datetime.utcnow()
            feed.last_failure_reason = str(exc)
            
            if feed.failure_count >= 5:
                feed.is_active = False
            
            db.add(feed)
            db.commit()
            
            raise self.retry(exc=exc, countdown=300)
        
        # Handle 304 Not Modified
        if response.status_code == 304:
            feed.last_fetched_at = datetime.utcnow()
            db.add(feed)
            db.commit()
            return {"status": "not_modified"}
        
        # Parse feed
        parsed = feedparser.parse(response.content)
        
        if parsed.bozo and hasattr(parsed, 'bozo_exception'):
            print(f"Feed parse warning for {feed.url}: {parsed.bozo_exception}")
        
        new_articles = 0
        for entry in parsed.entries[:50]:  # Max 50 per fetch
            url = entry.get("link", "")
            if not url:
                continue
            
            # Check if already exists
            existing = db.exec(select(Article).where(Article.url == url)).first()
            if existing:
                continue
            
            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            
            # Skip old articles (>7 days)
            if published and published < datetime.utcnow() - timedelta(days=7):
                continue
            
            # Create article
            try:
                article = Article(
                    id=str(uuid4()),
                    feed_id=feed_id,
                    url=url,
                    guid=entry.get("id"),
                    title=entry.get("title", ""),
                    author=entry.get("author"),
                    published_at=published,
                    processing_status=ProcessingStatus.FETCHED,
                )
                db.add(article)
                db.commit()
                db.refresh(article)
                
                # Queue extraction
                from app.tasks.article_tasks import extract_article_task
                extract_article_task.delay(article.id)
                
                new_articles += 1
            except IntegrityError:
                db.rollback()
                continue
        
        # Update feed metadata
        feed.last_fetched_at = datetime.utcnow()
        feed.last_etag = response.headers.get("ETag")
        feed.last_modified = response.headers.get("Last-Modified")
        feed.failure_count = 0
        
        # Update adaptive interval (B03)
        if new_articles > 0:
            update_fetch_interval(feed, new_articles)
        
        db.add(feed)
        db.commit()
        
        return {
            "status": "success",
            "new_articles": new_articles,
            "entries_parsed": len(parsed.entries),
        }
        
    finally:
        db.close()


def update_fetch_interval(feed: Feed, new_articles: int):
    """Update adaptive fetch interval based on update frequency."""
    if feed.last_fetched_at:
        time_since_last = (datetime.utcnow() - feed.last_fetched_at).total_seconds() / 60
        
        if new_articles > 10:
            # Feed updates frequently - check more often
            feed.fetch_interval_minutes = max(5, int(time_since_last * 0.5))
        elif new_articles > 0:
            # Moderate updates
            feed.fetch_interval_minutes = max(30, int(time_since_last * 0.8))
        else:
            # No new articles - check less often
            feed.fetch_interval_minutes = min(360, int(time_since_last * 1.5))
        
        # Clamp to reasonable range
        feed.fetch_interval_minutes = max(5, min(360, feed.fetch_interval_minutes))


@shared_task
def schedule_feed_fetches():
    """Schedule feeds that are due for fetching."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find feeds due for fetch
        feeds = db.exec(
            select(Feed).where(
                Feed.is_active == True,
                (
                    Feed.last_fetched_at == None
                ) | (
                    Feed.last_fetched_at < now - timedelta(minutes=Feed.fetch_interval_minutes)
                ),
            )
        ).all()
        
        scheduled = 0
        for feed in feeds:
            fetch_feed_task.delay(feed.id)
            scheduled += 1
        
        return {"scheduled": scheduled, "total_feeds_checked": len(feeds)}
        
    finally:
        db.close()
