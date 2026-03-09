"""Tests for Celery background tasks."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestFeedTasks:
    """Test feed fetching tasks."""

    @patch("app.tasks.feed_tasks.feedparser.parse")
    @patch("app.tasks.feed_tasks.extract_article_task.delay")
    def test_fetch_feed_task(self, mock_extract, mock_parse):
        """Should fetch feed and queue extraction."""
        from app.tasks.feed_tasks import fetch_feed_task
        
        # Mock feedparser response
        mock_parse.return_value = Mock(
            entries=[
                Mock(
                    title="Test Article",
                    link="https://example.com/article",
                    published_parsed=datetime.now().timetuple(),
                    summary="Summary",
                )
            ],
            status=200,
        )
        
        # Run task
        result = fetch_feed_task("https://example.com/feed.xml")
        
        mock_parse.assert_called_once_with("https://example.com/feed.xml")
        mock_extract.assert_called_once()

    @patch("app.tasks.feed_tasks.feedparser.parse")
    def test_fetch_feed_task_handles_errors(self, mock_parse):
        """Should handle feed fetch errors."""
        from app.tasks.feed_tasks import fetch_feed_task
        
        mock_parse.return_value = Mock(entries=[], status=404, bozo=1)
        
        result = fetch_feed_task("https://example.com/bad-feed")
        
        # Should complete without exception
        assert result is not None


class TestArticleTasks:
    """Test article processing tasks."""

    @patch("app.tasks.article_tasks.trafilatura.extract")
    @patch("app.tasks.article_tasks.generate_embedding_task.delay")
    def test_extract_article_task(self, mock_embed, mock_extract):
        """Should extract article content."""
        from app.tasks.article_tasks import extract_article_task
        
        mock_extract.return_value = "Extracted content"
        
        # Need to mock DB session
        with patch("app.tasks.article_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.get.return_value = Mock(id="article-123", url="https://example.com")
            
            result = extract_article_task("article-123")
            
            mock_extract.assert_called_once()
            mock_db.commit.assert_called()

    @patch("app.tasks.article_tasks.embed_texts")
    def test_generate_embedding_task(self, mock_embed):
        """Should generate embeddings."""
        from app.tasks.article_tasks import generate_embedding_task
        
        mock_embed.return_value = [[0.1] * 1536]
        
        with patch("app.tasks.article_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.get.return_value = Mock(
                id="article-123",
                content="Test content",
                embedding_vector_id=None
            )
            
            with patch("app.tasks.article_tasks.vector_store.upsert_document"):
                result = generate_embedding_task("article-123")
                
                mock_embed.assert_called_once()

    @patch("app.tasks.article_tasks.generate_text")
    def test_generate_summary_task(self, mock_generate):
        """Should generate article summary."""
        from app.tasks.article_tasks import generate_summary_task
        
        mock_generate.return_value = "Summary text"
        
        with patch("app.tasks.article_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.get.return_value = Mock(
                id="article-123",
                content="Long content...",
                summary=None
            )
            
            result = generate_summary_task("article-123")
            
            mock_generate.assert_called_once()
            mock_db.commit.assert_called()


class TestBriefTasks:
    """Test brief generation tasks."""

    @patch("app.tasks.brief_tasks.generate_text")
    @patch("app.tasks.brief_tasks.track_ai_cost")
    def test_generate_user_brief(self, mock_track, mock_generate):
        """Should generate daily brief."""
        from app.tasks.brief_tasks import generate_user_brief
        
        mock_generate.return_value = json.dumps({
            "title": "Daily Brief",
            "sections": [
                {"type": "executive_summary", "title": "Summary", "content": "Content"}
            ]
        })
        
        with patch("app.tasks.brief_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock user
            mock_user = Mock(
                id="user-123",
                brief_preferences={"delivery_time": "08:00"}
            )
            mock_db.get.return_value = mock_user
            
            # Mock articles
            mock_db.exec.return_value.all.return_value = [
                Mock(id="a1", title="Article 1", delta_score=0.8)
            ]
            
            result = generate_user_brief("user-123")
            
            mock_generate.assert_called_once()
            mock_track.assert_called_once()

    @patch("app.tasks.brief_tasks.send_email")
    def test_send_brief_email(self, mock_send):
        """Should send brief email."""
        from app.tasks.brief_tasks import send_brief_email
        
        with patch("app.tasks.brief_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.get.return_value = Mock(
                id="brief-123",
                user_id="user-123",
                title="Daily Brief",
                sections=[]
            )
            
            result = send_brief_email("brief-123", "user-123")
            
            mock_send.assert_called_once()


class TestDocumentTasks:
    """Test document processing tasks."""

    @patch("app.tasks.document_tasks.extract_text_from_pdf")
    def test_extract_document_task_pdf(self, mock_extract):
        """Should extract text from PDF."""
        from app.tasks.document_tasks import extract_document_task
        
        mock_extract.return_value = "Extracted PDF text"
        
        with patch("app.tasks.document_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.get.return_value = Mock(
                id="doc-123",
                filename="test.pdf",
                mime_type="application/pdf",
                status="pending"
            )
            
            result = extract_document_task("doc-123")
            
            mock_extract.assert_called_once()
            mock_db.commit.assert_called()


class TestSweeperTasks:
    """Test maintenance sweeper tasks."""

    def test_sweep_stuck_articles(self):
        """Should retry stuck articles."""
        from app.tasks.sweeper_tasks import sweep_stuck_articles
        
        with patch("app.tasks.sweeper_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock stuck articles
            stuck_article = Mock(
                id="article-123",
                status="processing",
                updated_at=datetime.utcnow() - timedelta(hours=2)
            )
            mock_db.exec.return_value.all.return_value = [stuck_article]
            
            with patch("app.tasks.sweeper_tasks.extract_article_task.delay") as mock_retry:
                result = sweep_stuck_articles()
                
                mock_retry.assert_called_once_with("article-123")

    def test_sweep_stuck_documents(self):
        """Should retry stuck documents."""
        from app.tasks.sweeper_tasks import sweep_stuck_documents
        
        with patch("app.tasks.sweeper_tasks.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock stuck document
            stuck_doc = Mock(
                id="doc-123",
                status="processing",
                state_changed_at=datetime.utcnow() - timedelta(hours=3)
            )
            mock_db.exec.return_value.all.return_value = [stuck_doc]
            
            with patch("app.tasks.sweeper_tasks.extract_document_task.delay") as mock_retry:
                result = sweep_stuck_documents()
                
                mock_retry.assert_called_once_with("doc-123")


class TestScoutTasks:
    """Test Scout agent tasks."""

    @patch("app.tasks.scout_tasks.ScoutResearchEngine")
    def test_run_scout_task(self, mock_engine_class):
        """Should run Scout research."""
        from app.tasks.scout_tasks import run_scout_task
        
        mock_engine = MagicMock()
        mock_engine.run_advanced_research.return_value = {
            "findings_count": 5,
            "insights_count": 1
        }
        mock_engine_class.return_value = mock_engine
        
        result = run_scout_task("scout-123")
        
        mock_engine_class.assert_called_once()
        mock_engine.run_advanced_research.assert_called_once()


# Import json at end to avoid issues
import json
