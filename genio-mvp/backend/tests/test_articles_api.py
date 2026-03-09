"""Tests for Articles API."""
import pytest
from fastapi.testclient import TestClient


class TestArticlesAPI:
    """Test articles endpoints."""

    def test_list_articles(self, client: TestClient, test_user: dict):
        """Should list articles with pagination."""
        response = client.get(
            "/api/v1/articles",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_articles_with_delta_filter(self, client: TestClient, test_user: dict):
        """Should filter articles by delta score."""
        response = client.get(
            "/api/v1/articles?min_delta=0.5",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All returned articles should have delta >= 0.5
        for article in data["items"]:
            assert article.get("delta_score", 0) >= 0.5

    def test_list_articles_unauthorized(self, client: TestClient):
        """Should reject unauthorized requests."""
        response = client.get("/api/v1/articles")
        assert response.status_code == 401

    def test_mark_article_read(self, client: TestClient, test_user: dict):
        """Should mark article as read."""
        # Note: This requires an article to exist
        # For now, test with a fake ID to verify endpoint structure
        response = client.post(
            "/api/v1/articles/fake-id/read",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # Should return 404 for non-existent article, not 500
        assert response.status_code in [404, 200]

    def test_mark_article_archived(self, client: TestClient, test_user: dict):
        """Should archive article."""
        response = client.post(
            "/api/v1/articles/fake-id/archive",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_star_article(self, client: TestClient, test_user: dict):
        """Should star/unstar article."""
        response = client.post(
            "/api/v1/articles/fake-id/star",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_search_articles(self, client: TestClient, test_user: dict):
        """Should search articles."""
        response = client.get(
            "/api/v1/articles/search?q=technology",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_article_detail(self, client: TestClient, test_user: dict):
        """Should get article details."""
        response = client.get(
            "/api/v1/articles/fake-id",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # Should return 404 for non-existent
        assert response.status_code == 404

    def test_get_related_articles(self, client: TestClient, test_user: dict):
        """Should get related articles."""
        response = client.get(
            "/api/v1/articles/fake-id/related",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
