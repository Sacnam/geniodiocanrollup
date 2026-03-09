"""Tests for advanced tagging system."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.tag import Tag, ArticleTag, DocumentTag
from app.models.article import Article
from app.models.document import Document


class TestTaggingSystem:
    """Test complete tagging functionality."""

    def test_create_tag(self, client: TestClient, test_user: dict, session: Session):
        """Should create a new tag with color and icon."""
        response = client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "AI Research",
                "color": "#7c3aed",
                "icon": "🤖",
                "description": "Artificial Intelligence research papers"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AI Research"
        assert data["color"] == "#7c3aed"
        assert data["icon"] == "🤖"
        assert data["slug"] == "ai-research"

    def test_tag_slug_generation(self, client: TestClient, test_user: dict):
        """Should auto-generate slug from name."""
        response = client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "Machine Learning & AI"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "machine-learning-ai"

    def test_tag_article(self, client: TestClient, test_user: dict, session: Session):
        """Should tag an article."""
        # First create a tag
        tag_response = client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "Important"}
        )
        tag_id = tag_response.json()["id"]
        
        # Tag an article
        response = client.post(
            "/api/v1/articles/article-123/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"tag_id": tag_id}
        )
        
        assert response.status_code == 201

    def test_get_articles_by_tag(self, client: TestClient, test_user: dict):
        """Should filter articles by tag."""
        response = client.get(
            "/api/v1/articles?tag=important",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All returned articles should have the tag
        for article in data["items"]:
            assert "important" in [t["name"].lower() for t in article.get("tags", [])]

    def test_tag_cloud(self, client: TestClient, test_user: dict):
        """Should return tag cloud with frequencies."""
        response = client.get(
            "/api/v1/tags/cloud",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list of tags with count
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "count" in data[0]
            assert "color" in data[0]

    def test_tag_autocomplete(self, client: TestClient, test_user: dict):
        """Should return matching tags for autocomplete."""
        response = client.get(
            "/api/v1/tags/autocomplete?q=ai",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All results should contain "ai"
        for tag in data:
            assert "ai" in tag["name"].lower()

    def test_remove_tag_from_article(self, client: TestClient, test_user: dict):
        """Should remove tag from article."""
        response = client.delete(
            "/api/v1/articles/article-123/tags/tag-456",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 204

    def test_delete_tag(self, client: TestClient, test_user: dict):
        """Should delete tag and remove from all items."""
        # Create tag
        create_response = client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "ToDelete"}
        )
        tag_id = create_response.json()["id"]
        
        # Delete tag
        response = client.delete(
            f"/api/v1/tags/{tag_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 204

    def test_tag_uniqueness_per_user(self, client: TestClient, test_user: dict):
        """Should not allow duplicate tag names for same user."""
        # Create first tag
        client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "UniqueTag"}
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "UniqueTag"}
        )
        
        assert response.status_code == 409  # Conflict

    def test_bulk_tag_articles(self, client: TestClient, test_user: dict):
        """Should tag multiple articles at once."""
        response = client.post(
            "/api/v1/batch/articles/tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "article_ids": ["article-1", "article-2", "article-3"],
                "tag_id": "tag-123",
                "action": "add"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["processed_count"] == 3
