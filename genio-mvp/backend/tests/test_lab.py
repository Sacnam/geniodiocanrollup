"""
Lab Module Tests
Tests for Scout Agents and advanced research features.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.lab.models import ScoutAgent, ScoutFinding, ScoutInsight, ScoutStatus


class TestScoutModels:
    """Test Scout data models."""
    
    def test_create_scout(self, session: Session):
        """Test creating a Scout agent."""
        scout = ScoutAgent(
            user_id="test-user",
            name="Test Scout",
            research_question="Test research question?",
            keywords=["test", "example"],
            sources=["feeds", "documents"],
            schedule="daily",
            min_relevance_score=0.7,
            is_active=True
        )
        
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        assert scout.id is not None
        assert scout.name == "Test Scout"
        assert scout.status == ScoutStatus.IDLE
        assert scout.keywords == ["test", "example"]
    
    def test_scout_findings(self, session: Session):
        """Test creating Scout findings."""
        # Create scout first
        scout = ScoutAgent(
            user_id="test-user",
            name="Finding Test Scout",
            research_question="Test?",
            sources=["feeds"]
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        # Create finding
        finding = ScoutFinding(
            scout_id=scout.id,
            user_id="test-user",
            source_type="article",
            source_id="article-1",
            source_url="https://example.com/article",
            source_title="Test Article",
            relevance_score=0.85,
            explanation="This is relevant",
            matched_keywords=["test"],
            key_insights=["Important insight"]
        )
        
        session.add(finding)
        session.commit()
        session.refresh(finding)
        
        assert finding.id is not None
        assert finding.relevance_score == 0.85
        assert finding.is_read is False
    
    def test_scout_insights(self, session: Session):
        """Test creating Scout insights."""
        scout = ScoutAgent(
            user_id="test-user",
            name="Insight Test Scout",
            research_question="Test?"
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        insight = ScoutInsight(
            scout_id=scout.id,
            user_id="test-user",
            insight_type="pattern",
            title="Test Pattern",
            description="A test pattern was detected",
            confidence_score=0.9,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow()
        )
        
        session.add(insight)
        session.commit()
        session.refresh(insight)
        
        assert insight.id is not None
        assert insight.insight_type == "pattern"
        assert insight.confidence_score == 0.9


class TestScoutAPI:
    """Test Scout API endpoints."""
    
    def test_create_scout_endpoint(self, client: TestClient, test_user):
        """Test creating a Scout via API."""
        response = client.post(
            "/scouts",
            json={
                "name": "API Test Scout",
                "research_question": "What is the impact of AI?",
                "keywords": ["AI", "machine learning"],
                "sources": ["feeds", "documents"],
                "schedule": "daily"
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Scout"
        assert data["research_question"] == "What is the impact of AI?"
        assert "id" in data
    
    def test_list_scouts_endpoint(self, client: TestClient, test_user):
        """Test listing Scouts."""
        # Create a scout first
        client.post(
            "/scouts",
            json={
                "name": "List Test Scout",
                "research_question": "Test question?",
                "keywords": ["test"],
                "sources": ["feeds"],
                "schedule": "daily"
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # List scouts
        response = client.get(
            "/scouts",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_update_scout_endpoint(self, client: TestClient, test_user):
        """Test updating a Scout."""
        # Create
        create_resp = client.post(
            "/scouts",
            json={
                "name": "Update Test Scout",
                "research_question": "Original?",
                "keywords": ["original"],
                "sources": ["feeds"],
                "schedule": "daily"
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        scout_id = create_resp.json()["id"]
        
        # Update
        update_resp = client.patch(
            f"/scouts/{scout_id}",
            json={"name": "Updated Scout Name"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Scout Name"
    
    def test_delete_scout_endpoint(self, client: TestClient, test_user):
        """Test deleting a Scout."""
        # Create
        create_resp = client.post(
            "/scouts",
            json={
                "name": "Delete Test Scout",
                "research_question": "To be deleted?",
                "keywords": ["delete"],
                "sources": ["feeds"],
                "schedule": "daily"
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        scout_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = client.delete(
            f"/scouts/{scout_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert delete_resp.status_code == 204
        
        # Verify deleted
        get_resp = client.get(
            f"/scouts/{scout_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert get_resp.status_code == 404


class TestScoutAdvanced:
    """Test advanced Scout features."""
    
    def test_scout_pkg_context(self, session: Session):
        """Test Scout uses PKG context for research."""
        from app.lab.scout_advanced import ScoutResearchEngine
        
        # Create scout
        scout = ScoutAgent(
            user_id="test-user",
            name="PKG Context Scout",
            research_question="Test context?",
            keywords=["AI"],
            sources=["documents"]
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        # Create engine
        engine = ScoutResearchEngine(scout.id, session)
        
        # Get PKG context (should work even if empty)
        context = engine._get_pkg_context()
        
        assert "known_concepts" in context
        assert "knowledge_gaps" in context
        assert "interests" in context
        assert context["research_question"] == "Test context?"
    
    def test_relevance_scoring(self, session: Session):
        """Test advanced relevance scoring."""
        from app.lab.scout_advanced import ScoutResearchEngine
        
        scout = ScoutAgent(
            user_id="test-user",
            name="Relevance Scout",
            research_question="Test?",
            keywords=["machine", "learning"],
            sources=["feeds"]
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        engine = ScoutResearchEngine(scout.id, session)
        
        # Test scoring
        text = "This is about machine learning and AI"
        context = {"known_concepts": [], "knowledge_gaps": [], "interests": ["AI"]}
        
        score = engine._calculate_advanced_relevance(text, context)
        
        assert 0 <= score <= 1
        # Should have higher score due to keyword match
        assert score > 0


class TestScoutFindingsAPI:
    """Test Scout findings endpoints."""
    
    def test_list_findings(self, client: TestClient, test_user, session: Session):
        """Test listing Scout findings."""
        # Create scout with findings
        scout = ScoutAgent(
            user_id=test_user["user_id"] if isinstance(test_user, dict) else "test-user",
            name="Findings Test Scout",
            research_question="Test?"
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        # Add finding
        finding = ScoutFinding(
            scout_id=scout.id,
            user_id=scout.user_id,
            source_type="article",
            source_id="test-1",
            source_url="https://test.com",
            source_title="Test Finding",
            relevance_score=0.9,
            explanation="Test explanation"
        )
        session.add(finding)
        session.commit()
        
        # Get token
        token = test_user["access_token"] if isinstance(test_user, dict) else test_user
        
        response = client.get(
            f"/scouts/{scout.id}/findings",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestScoutInsightsAPI:
    """Test Scout insights endpoints."""
    
    def test_list_insights(self, client: TestClient, test_user, session: Session):
        """Test listing Scout insights."""
        # Create scout with insight
        scout = ScoutAgent(
            user_id=test_user["user_id"] if isinstance(test_user, dict) else "test-user",
            name="Insights Test Scout",
            research_question="Test?"
        )
        session.add(scout)
        session.commit()
        session.refresh(scout)
        
        # Add insight
        insight = ScoutInsight(
            scout_id=scout.id,
            user_id=scout.user_id,
            insight_type="pattern",
            title="Test Pattern",
            description="A pattern was found",
            confidence_score=0.85,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow()
        )
        session.add(insight)
        session.commit()
        
        # Get token
        token = test_user["access_token"] if isinstance(test_user, dict) else test_user
        
        response = client.get(
            f"/scouts/{scout.id}/insights",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
