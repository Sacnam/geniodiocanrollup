"""
Database Seeding Script
Populates database with sample data for development/testing
"""
import asyncio
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.models.article import Article, ProcessingStatus, UserArticleContext
from app.models.brief import Brief, BriefSection
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.feed import Feed, FeedStatus
from app.models.user import User, UserTier


def create_engine_with_db():
    """Create database engine."""
    return create_engine(settings.DATABASE_URL)


def seed_users(session: Session):
    """Create sample users."""
    print("👤 Creating users...")
    
    users = [
        User(
            id=str(uuid.uuid4()),
            email="admin@genio.ai",
            hashed_password="$2b$12$...",  # Would be properly hashed
            first_name="Admin",
            last_name="User",
            tier=UserTier.ENTERPRISE,
            is_active=True,
            is_verified=True,
        ),
        User(
            id=str(uuid.uuid4()),
            email="demo@example.com",
            hashed_password="$2b$12$...",
            first_name="Demo",
            last_name="User",
            tier=UserTier.PROFESSIONAL,
            is_active=True,
        ),
    ]
    
    for user in users:
        existing = session.query(User).filter(User.email == user.email).first()
        if not existing:
            session.add(user)
    
    session.commit()
    print(f"  ✓ Created {len(users)} users")
    return users


def seed_feeds(session: Session, users: list):
    """Create sample feeds."""
    print("📰 Creating feeds...")
    
    feeds = [
        Feed(
            id=str(uuid.uuid4()),
            user_id=users[0].id,
            url="https://news.ycombinator.com/rss",
            title="Hacker News",
            category="Tech",
            status=FeedStatus.ACTIVE,
            fetch_interval_minutes=60,
        ),
        Feed(
            id=str(uuid.uuid4()),
            user_id=users[0].id,
            url="https://feeds.arstechnica.com/arstechnica/index",
            title="Ars Technica",
            category="Tech",
            status=FeedStatus.ACTIVE,
            fetch_interval_minutes=120,
        ),
    ]
    
    for feed in feeds:
        existing = session.query(Feed).filter(Feed.url == feed.url).first()
        if not existing:
            session.add(feed)
    
    session.commit()
    print(f"  ✓ Created {len(feeds)} feeds")
    return feeds


def seed_articles(session: Session, users: list, feeds: list):
    """Create sample articles."""
    print("📄 Creating articles...")
    
    articles = [
        Article(
            id=str(uuid.uuid4()),
            url="https://example.com/article1",
            source_feed_id=feeds[0].id if feeds else None,
            title="The Future of AI in 2026",
            excerpt="Artificial intelligence continues to evolve at a rapid pace...",
            content="Full article content here...",
            content_hash="hash123",
            processing_status=ProcessingStatus.READY,
            global_summary="AI is transforming industries with new capabilities in reasoning and creativity.",
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
        Article(
            id=str(uuid.uuid4()),
            url="https://example.com/article2",
            source_feed_id=feeds[0].id if feeds else None,
            title="Climate Tech Innovations",
            excerpt="New technologies are emerging to combat climate change...",
            content="Full article content here...",
            content_hash="hash456",
            processing_status=ProcessingStatus.READY,
            global_summary="Climate tech sees breakthrough in carbon capture and renewable energy storage.",
            created_at=datetime.utcnow() - timedelta(days=2),
        ),
    ]
    
    for article in articles:
        existing = session.query(Article).filter(Article.url == article.url).first()
        if not existing:
            session.add(article)
            
            # Create UserArticleContext for first user
            if users:
                context = UserArticleContext(
                    id=str(uuid.uuid4()),
                    user_id=users[0].id,
                    article_id=article.id,
                    delta_score=0.85 if "AI" in article.title else 0.65,
                    is_read=False,
                )
                session.add(context)
    
    session.commit()
    print(f"  ✓ Created {len(articles)} articles")
    return articles


def seed_documents(session: Session, users: list):
    """Create sample documents."""
    print("📚 Creating documents...")
    
    documents = [
        Document(
            id=str(uuid.uuid4()),
            user_id=users[0].id if users else None,
            filename="sample.pdf",
            original_filename="Introduction to Machine Learning.pdf",
            file_path="/uploads/sample.pdf",
            file_size_bytes=1024000,
            mime_type="application/pdf",
            doc_type="pdf",
            title="Introduction to Machine Learning",
            excerpt="Machine learning is a subset of artificial intelligence...",
            content="Full document content...",
            status=DocumentStatus.READY,
            page_count=50,
            word_count=15000,
            created_at=datetime.utcnow() - timedelta(days=3),
        ),
    ]
    
    for doc in documents:
        existing = session.query(Document).filter(Document.original_filename == doc.original_filename).first()
        if not existing:
            session.add(doc)
    
    session.commit()
    print(f"  ✓ Created {len(documents)} documents")
    return documents


def seed_briefs(session: Session, users: list, articles: list):
    """Create sample briefs."""
    print("📧 Creating briefs...")
    
    briefs = [
        Brief(
            id=str(uuid.uuid4()),
            user_id=users[0].id if users else None,
            title="Daily Brief - February 17, 2026",
            scheduled_for=datetime.utcnow() - timedelta(days=1),
            delivered_at=datetime.utcnow() - timedelta(days=1),
            delivery_status="delivered",
            is_quiet_day=False,
            article_count=len(articles),
            sources_cited=["Hacker News", "Ars Technica"],
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
    ]
    
    for brief in session:
        session.add(brief)
    
    session.commit()
    print(f"  ✓ Created {len(briefs)} briefs")
    return briefs


def main():
    """Main seeding function."""
    print("🌱 Seeding database...\n")
    
    engine = create_engine_with_db()
    
    with Session(engine) as session:
        try:
            # Seed in order of dependencies
            users = seed_users(session)
            feeds = seed_feeds(session, users)
            articles = seed_articles(session, users, feeds)
            documents = seed_documents(session, users)
            briefs = seed_briefs(session, users, articles)
            
            print("\n✅ Database seeded successfully!")
            print(f"   Users: {len(users)}")
            print(f"   Feeds: {len(feeds)}")
            print(f"   Articles: {len(articles)}")
            print(f"   Documents: {len(documents)}")
            print(f"   Briefs: {len(briefs)}")
            
        except Exception as e:
            print(f"\n❌ Error seeding database: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()
