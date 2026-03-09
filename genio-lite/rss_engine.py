import feedparser
from datetime import datetime
from sqlmodel import Session, select
from models import Feed, Article
from typing import List

def fetch_feed_articles(feed_url: str) -> List[dict]:
    parsed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed.entries:
        # Normalize date
        published = datetime.now() # Fallback
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])
            
        articles.append({
            "title": entry.title,
            "content": entry.get('summary', entry.get('description', '')),
            "url": entry.link,
            "published_at": published
        })
    return articles

def sync_feed(session: Session, feed_id: int):
    feed = session.get(Feed, feed_id)
    if not feed:
        return
    
    articles_data = fetch_feed_articles(feed.url)
    for data in articles_data:
        # Check if article already exists
        statement = select(Article).where(Article.url == data["url"])
        existing = session.exec(statement).first()
        if not existing:
            article = Article(**data, feed_id=feed.id)
            session.add(article)
    
    feed.last_fetched = datetime.now()
    session.add(feed)
    session.commit()
