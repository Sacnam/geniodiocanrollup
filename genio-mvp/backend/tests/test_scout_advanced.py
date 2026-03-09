"""Tests for Advanced Scout Engine."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.lab.scout_advanced import ScoutResearchEngine, verify_claim_task
from app.lab.models import ScoutAgent, ScoutFinding, ScoutInsight


class TestScoutAdvanced:
    """Test advanced Scout capabilities."""

    def test_scout_engine_initialization(self, session):
        """Should initialize with scout config."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            research_question="Test question",
            keywords=["AI", "ML"],
            sources=["feeds"],
            min_relevance_score=0.7,
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        
        assert engine.scout is not None
        assert engine.scout.name == "Test Scout"

    def test_calculate_advanced_relevance(self, session):
        """Should calculate relevance with multiple signals."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            research_question="AI research",
            keywords=["artificial", "intelligence"],
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        
        pkg_context = {
            "known_concepts": [{"id": "c1", "name": "Machine Learning"}],
            "knowledge_gaps": [{"id": "g1", "name": "Deep Learning"}],
            "interests": ["AI"],
            "research_question": "AI research",
        }
        
        text = "Artificial intelligence and machine learning are related"
        relevance = engine._calculate_advanced_relevance(text, pkg_context)
        
        assert 0 <= relevance <= 1
        assert relevance > 0  # Should match keywords

    def test_extract_matched_keywords(self, session):
        """Should extract matched keywords."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            research_question="Test",
            keywords=["python", "testing"],
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        matched = engine._extract_matched_keywords("I love python programming and testing")
        
        assert "python" in matched
        assert "testing" in matched

    def test_check_contradiction(self, session):
        """Should detect potential contradictions."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        
        pkg_context = {
            "known_concepts": [{"id": "c1", "name": "Python"}],
        }
        
        # Should detect contradiction
        text = "Python is not a programming language"
        contradiction = engine._check_contradiction(text, pkg_context)
        
        assert contradiction is not None
        assert "Python" in contradiction

    def test_generate_explanation(self, session):
        """Should generate relevance explanation."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            research_question="Test",
            keywords=["testing"],
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        
        pkg_context = {
            "knowledge_gaps": [{"id": "g1", "name": "Testing"}],
        }
        
        explanation = engine._generate_explanation(
            "This is about testing",
            0.85,
            pkg_context
        )
        
        assert len(explanation) > 0
        assert "relevant" in explanation.lower()

    def test_calculate_next_run(self, session):
        """Should calculate next run based on schedule."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            schedule="daily",
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        next_run = engine._calculate_next_run()
        
        # Should be approximately 1 day in the future
        now = datetime.utcnow()
        assert next_run > now
        assert next_run < now + timedelta(days=2)

    @patch("app.lab.scout_advanced.answer_cross_document_query")
    def test_verify_claim_task(self, mock_answer, session):
        """Should verify claim against PKG."""
        mock_answer.return_value = {
            "answer": "This claim is supported by your documents",
            "context_size": 3,
        }
        
        result = verify_claim_task(
            claim="AI is important",
            scout_id="scout-123",
            user_id="user-456"
        )
        
        assert result["verified"] is True
        assert result["sources_used"] == 3
        mock_answer.assert_called_once()

    def test_generate_insights(self, session):
        """Should generate insights from findings."""
        scout = ScoutAgent(
            id="scout-123",
            user_id="user-456",
            name="Test Scout",
            research_question="Test",
            date_range_days=30,
            sources=["feeds"],
        )
        session.add(scout)
        session.commit()
        
        engine = ScoutResearchEngine("scout-123", session)
        engine.execution = Mock()
        
        # Add mock findings
        for i in range(5):
            finding = ScoutFinding(
                id=f"finding-{i}",
                scout_id="scout-123",
                user_id="user-456",
                source_type="article" if i % 2 == 0 else "document",
                source_id=f"src-{i}",
                source_url=f"http://example.com/{i}",
                source_title=f"Finding {i}",
                relevance_score=0.9 if i < 3 else 0.6,
                explanation="Test",
            )
            session.add(finding)
            engine.findings_buffer.append(finding)
        
        session.commit()
        
        insights = engine._generate_insights()
        
        assert len(insights) >= 1
        # Should have cross-source pattern
        assert any(i.insight_type == "pattern" for i in insights)
