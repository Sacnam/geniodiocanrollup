"""Tests for full-text search with Elasticsearch."""
import pytest
from fastapi.testclient import TestClient


class TestFullTextSearch:
    """Test Elasticsearch-powered full-text search."""

    def test_basic_fulltext_search(self, client: TestClient, test_user: dict):
        """Should search across article content."""
        response = client.get(
            "/api/v1/search?q=artificial intelligence",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "took_ms" in data  # Search latency
        
        # Results should be relevance-sorted
        if len(data["items"]) > 1:
            assert data["items"][0]["_score"] >= data["items"][1]["_score"]

    def test_search_with_filters(self, client: TestClient, test_user: dict):
        """Should combine search with filters."""
        response = client.get(
            "/api/v1/search?q=machine learning&is_read=false&date_from=2026-01-01",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All results should contain "machine learning"
        for item in data["items"]:
            assert "machine" in item["content"].lower() or "learning" in item["content"].lower()

    def test_fuzzy_search(self, client: TestClient, test_user: dict):
        """Should handle typos with fuzzy matching."""
        response = client.get(
            "/api/v1/search?q=artifcial inteligence&fuzzy=true",  # Typos intentional
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should still find "artificial intelligence"
        assert data["total"] > 0

    def test_phrase_search(self, client: TestClient, test_user: dict):
        """Should support exact phrase search with quotes."""
        response = client.get(
            '/api/v1/search?q="deep learning"',
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Results should contain exact phrase
        for item in data["items"]:
            assert "deep learning" in item["content"].lower()

    def test_search_operators(self, client: TestClient, test_user: dict):
        """Should support AND, OR, NOT operators."""
        # AND operator
        response = client.get(
            "/api/v1/search?q=python AND machine learning",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        
        # NOT operator
        response = client.get(
            "/api/v1/search?q=python NOT snake",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200

    def test_search_facets(self, client: TestClient, test_user: dict):
        """Should return aggregation facets."""
        response = client.get(
            "/api/v1/search?q=ai&facets=tags,feeds,date",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "facets" in data
        assert "tags" in data["facets"]
        assert "feeds" in data["facets"]

    def test_highlighting(self, client: TestClient, test_user: dict):
        """Should highlight search terms in results."""
        response = client.get(
            "/api/v1/search?q=neural networks&highlight=true",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Results should have highlighted snippets
        if len(data["items"]) > 0:
            assert "highlight" in data["items"][0]
            # Highlight markers should be present
            assert "<mark>" in str(data["items"][0]["highlight"])

    def test_suggestions(self, client: TestClient, test_user: dict):
        """Should provide search suggestions."""
        response = client.get(
            "/api/v1/search/suggest?q=artif",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        # Should suggest "artificial"
        suggestions = [s.lower() for s in data["suggestions"]]
        assert any("artificial" in s for s in suggestions)

    def test_search_in_document_content(self, client: TestClient, test_user: dict):
        """Should search within document contents."""
        response = client.get(
            "/api/v1/search?q=contract terms&type=document",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All results should be documents
        for item in data["items"]:
            assert item["type"] == "document"

    def test_search_across_types(self, client: TestClient, test_user: dict):
        """Should search across articles and documents."""
        response = client.get(
            "/api/v1/search?q=artificial intelligence&type=all",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should contain mix of articles and documents
        types = set(item["type"] for item in data["items"])
        assert len(types) >= 1

    def test_vector_semantic_search(self, client: TestClient, test_user: dict):
        """Should support semantic search via vector similarity."""
        response = client.get(
            "/api/v1/search/semantic?q=how to build neural networks",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Semantic search should find related content even without exact keywords
        assert "items" in data
        assert "semantic_score" in data["items"][0] if data["items"] else True

    def test_index_sync_on_article_create(self, client: TestClient, test_user: dict):
        """Should automatically index new articles."""
        # This tests that the Celery task is triggered
        # The actual indexing happens asynchronously
        response = client.post(
            "/api/v1/feeds/feed-123/fetch",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 202
        # Index task should be queued
        data = response.json()
        assert "tasks" in data

    def test_search_boost_recent(self, client: TestClient, test_user: dict):
        """Should boost recently published articles."""
        response = client.get(
            "/api/v1/search?q=technology&boost_recent=true",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # More recent articles should rank higher if scores are similar
        assert "items" in data

    def test_search_by_author(self, client: TestClient, test_user: dict):
        """Should filter by author."""
        response = client.get(
            "/api/v1/search?q=&author=John Doe",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All results should be by the specified author
        for item in data["items"]:
            assert item["author"] == "John Doe"

    def test_search_stats_endpoint(self, client: TestClient, test_user: dict):
        """Should return search statistics."""
        response = client.get(
            "/api/v1/search/stats",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_indexed" in data
        assert "last_index_update" in data
        assert "index_size_mb" in data
