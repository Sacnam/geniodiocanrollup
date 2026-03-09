"""
End-to-end integration tests (T058).
Tests full flow: feed → article → brief.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.article import Article, ProcessingStatus, UserArticleContext
from app.models.brief import Brief
from app.models.feed import Feed
from app.models.user import User


class TestE2EFeedToBrief:
    """End-to-end test: Complete user journey."""
    
    def test_complete_user_journey(self, client: TestClient, session: Session):
        """
        E2E Test:
        1. User registers
        2. User adds feed
        3. Feed is fetched
        4. Articles are created
        5. Brief is generated
        """
        # Step 1: Register
        register_resp = client.post(
            "/auth/register",
            json={
                "email": "e2e@example.com",
                "password": "testpassword123",
                "name": "E2E User"
            }
        )
        assert register_resp.status_code == 200
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user
        user = session.exec(select(User).where(User.email == "e2e@example.com")).first()
        assert user is not None
        
        # Step 2: Add feed
        feed_resp = client.post(
            "/feeds",
            json={
                "url": "https://test-feed.com/rss.xml",
                "title": "Test Feed",
                "category": "Tech"
            },
            headers=headers
        )
        assert feed_resp.status_code == 201
        feed_id = feed_resp.json()["id"]
        
        # Verify feed in DB
        feed = session.get(Feed, feed_id)
        assert feed is not None
        assert feed.user_id == user.id
        
        # Step 3: Create articles directly (simulating fetch)
        article1 = Article(
            url="https://example.com/article1",
            content_hash="hash123",
            title="Test Article 1",
            excerpt="Excerpt 1",
            source_feed_id=feed_id,
            processing_status=ProcessingStatus.READY,
        )
        article2 = Article(
            url="https://example.com/article2",
            content_hash="hash456",
            title="Test Article 2",
            excerpt="Excerpt 2",
            source_feed_id=feed_id,
            processing_status=ProcessingStatus.READY,
        )
        session.add(article1)
        session.add(article2)
        session.commit()
        session.refresh(article1)
        session.refresh(article2)
        
        # Step 4: Create user article contexts with delta scores
        ctx1 = UserArticleContext(
            user_id=user.id,
            article_id=article1.id,
            delta_score=0.95,  # High novelty
            is_duplicate=False,
        )
        ctx2 = UserArticleContext(
            user_id=user.id,
            article_id=article2.id,
            delta_score=0.75,  # Medium novelty
            is_duplicate=False,
        )
        session.add(ctx1)
        session.add(ctx2)
        session.commit()
        
        # Step 5: Verify articles API
        articles_resp = client.get("/articles", headers=headers)
        assert articles_resp.status_code == 200
        articles_data = articles_resp.json()
        assert articles_data["total"] == 2
        assert len(articles_data["items"]) == 2
        
        # Verify delta scores
        scores = [a["delta_score"] for a in articles_data["items"]]
        assert 0.95 in scores
        assert 0.75 in scores
        
        # Step 6: Create brief
        from datetime import datetime
        brief = Brief(
            user_id=user.id,
            title=f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}",
            scheduled_for=datetime.utcnow(),
            delivery_status="sent",
            is_quiet_day=False,
            article_count=2,
        )
        session.add(brief)
        session.commit()
        session.refresh(brief)
        
        # Step 7: Verify briefs API
        briefs_resp = client.get("/briefs", headers=headers)
        assert briefs_resp.status_code == 200
        briefs_data = briefs_resp.json()
        assert briefs_data["total"] == 1
        assert briefs_data["items"][0]["article_count"] == 2


class TestE2EKnowledgeDelta:
    """E2E tests for Knowledge Delta functionality."""
    
    def test_duplicate_filtering(self, client: TestClient, session: Session):
        """Test that DUPLICATE articles are filtered from feed."""
        # Register and create feed
        register_resp = client.post(
            "/auth/register",
            json={"email": "delta@example.com", "password": "testpass123"}
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        user = session.exec(select(User).where(User.email == "delta@example.com")).first()
        
        # Create articles
        article_dup = Article(
            url="https://dup.com",
            content_hash="dup123",
            title="Duplicate",
            processing_status=ProcessingStatus.READY,
        )
        article_novel = Article(
            url="https://novel.com",
            content_hash="novel456",
            title="Novel",
            processing_status=ProcessingStatus.READY,
        )
        session.add(article_dup)
        session.add(article_novel)
        session.commit()
        session.refresh(article_dup)
        session.refresh(article_novel)
        
        # Create contexts - one duplicate, one novel
        ctx_dup = UserArticleContext(
            user_id=user.id,
            article_id=article_dup.id,
            delta_score=0.95,  # High similarity = duplicate
            is_duplicate=True,  # Marked as duplicate
        )
        ctx_novel = UserArticleContext(
            user_id=user.id,
            article_id=article_novel.id,
            delta_score=0.60,  # Low similarity = novel
            is_duplicate=False,
        )
        session.add(ctx_dup)
        session.add(ctx_novel)
        session.commit()
        
        # Query articles - should only see novel
        resp = client.get("/articles", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Should only return 1 article (the novel one)
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Novel"


class TestE2EArticleInteractions:
    """E2E tests for article read/archive interactions."""
    
    def test_mark_read_and_archive(self, client: TestClient, session: Session):
        """Test marking articles as read and archived."""
        # Setup
        register_resp = client.post(
            "/auth/register",
            json={"email": "interact@example.com", "password": "testpass123"}
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        user = session.exec(select(User).where(User.email == "interact@example.com")).first()
        
        # Create article
        article = Article(
            url="https://test.com/article",
            content_hash="test123",
            title="Test Article",
            processing_status=ProcessingStatus.READY,
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        
        ctx = UserArticleContext(
            user_id=user.id,
            article_id=article.id,
            delta_score=0.80,
            is_read=False,
            is_archived=False,
        )
        session.add(ctx)
        session.commit()
        
        # Mark as read
        read_resp = client.post(f"/articles/{article.id}/read", headers=headers)
        assert read_resp.status_code == 200
        
        # Verify read
        get_resp = client.get(f"/articles/{article.id}", headers=headers)
        assert get_resp.json()["is_read"] is True
        
        # Archive
        archive_resp = client.post(f"/articles/{article.id}/archive", headers=headers)
        assert archive_resp.status_code == 200
        
        # Verify not in default list (archived excluded by default)
        list_resp = client.get("/articles", headers=headers)
        assert list_resp.json()["total"] == 0
        
        # Verify in archived list
        archived_resp = client.get("/articles?is_archived=true", headers=headers)
        assert archived_resp.json()["total"] == 1


class TestE2EFeedManagement:
    """E2E tests for feed management."""
    
    def test_feed_crud_operations(self, client: TestClient):
        """Test full feed CRUD."""
        # Register
        register_resp = client.post(
            "/auth/register",
            json={"email": "feeds@example.com", "password": "testpass123"}
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create
        create_resp = client.post(
            "/feeds",
            json={"url": "https://feeds.test/rss", "title": "Test Feed", "category": "Tech"},
            headers=headers
        )
        assert create_resp.status_code == 201
        feed_id = create_resp.json()["id"]
        
        # Read
        get_resp = client.get(f"/feeds/{feed_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Test Feed"
        
        # Update
        update_resp = client.patch(
            f"/feeds/{feed_id}",
            json={"title": "Updated Feed", "category": "News"},
            headers=headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Updated Feed"
        assert update_resp.json()["category"] == "News"
        
        # Delete
        delete_resp = client.delete(f"/feeds/{feed_id}", headers=headers)
        assert delete_resp.status_code == 204
        
        # Verify deleted
        list_resp = client.get("/feeds", headers=headers)
        assert list_resp.json() == []
