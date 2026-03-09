"""Tests for saved views and filters system."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.saved_view import SavedView, FilterConfig


class TestSavedViews:
    """Test saved views functionality."""

    def test_create_saved_view(self, client: TestClient, test_user: dict):
        """Should create a saved view with filters."""
        response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "AI Research Articles",
                "description": "Unread AI articles from top sources",
                "icon": "🤖",
                "filters": {
                    "search": "artificial intelligence",
                    "tags": ["ai", "research"],
                    "feeds": ["feed-1"],
                    "is_read": False,
                    "is_favorited": False,
                    "date_range": {"from": "2026-01-01", "to": "2026-12-31"},
                    "delta_score_min": 0.7,
                    "sort_by": "delta_score",
                    "sort_order": "desc"
                },
                "is_default": False,
                "position": 1
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AI Research Articles"
        assert data["filters"]["search"] == "artificial intelligence"
        assert data["filters"]["tags"] == ["ai", "research"]

    def test_get_saved_views(self, client: TestClient, test_user: dict):
        """Should return all saved views for user."""
        # Create a view first
        client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "Favorites",
                "filters": {"is_favorited": True}
            }
        )
        
        response = client.get(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "name" in data[0]
        assert "filters" in data[0]

    def test_apply_saved_view(self, client: TestClient, test_user: dict):
        """Should apply filters from saved view."""
        # Create a view
        create_response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "High Delta",
                "filters": {"delta_score_min": 0.8}
            }
        )
        view_id = create_response.json()["id"]
        
        # Apply view to articles
        response = client.get(
            f"/api/v1/views/{view_id}/apply",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All returned articles should have delta_score >= 0.8
        for article in data["items"]:
            assert article["delta_score"] >= 0.8

    def test_update_saved_view(self, client: TestClient, test_user: dict):
        """Should update saved view filters."""
        # Create
        create_response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "Old Name", "filters": {}}
        )
        view_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/api/v1/views/{view_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "Updated Name",
                "filters": {"is_read": False}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["filters"]["is_read"] == False

    def test_delete_saved_view(self, client: TestClient, test_user: dict):
        """Should delete saved view."""
        create_response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "To Delete", "filters": {}}
        )
        view_id = create_response.json()["id"]
        
        response = client.delete(
            f"/api/v1/views/{view_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 204

    def test_set_default_view(self, client: TestClient, test_user: dict):
        """Should set a view as default."""
        create_response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "Default View", "filters": {"is_read": False}}
        )
        view_id = create_response.json()["id"]
        
        response = client.post(
            f"/api/v1/views/{view_id}/default",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] == True

    def test_reorder_views(self, client: TestClient, test_user: dict):
        """Should reorder saved views."""
        # Create multiple views
        views = []
        for i in range(3):
            response = client.post(
                "/api/v1/views",
                headers={"Authorization": f"Bearer {test_user['access_token']}"},
                json={"name": f"View {i}", "filters": {}, "position": i}
            )
            views.append(response.json()["id"])
        
        # Reorder
        response = client.put(
            "/api/v1/views/reorder",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "view_ids": [views[2], views[0], views[1]]  # New order
            }
        )
        
        assert response.status_code == 200

    def test_view_with_multiple_filters(self, client: TestClient, test_user: dict):
        """Should combine multiple filters correctly."""
        response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "name": "Complex Filter",
                "filters": {
                    "search": "python",
                    "tags": ["programming"],
                    "is_read": False,
                    "is_favorited": True,
                    "delta_score_min": 0.5,
                    "date_range": {
                        "from": "2026-01-01",
                        "to": "2026-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "tags" in data["filters"]
        assert "delta_score_min" in data["filters"]

    def test_share_saved_view(self, client: TestClient, test_user: dict):
        """Should generate shareable link for view."""
        create_response = client.post(
            "/api/v1/views",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"name": "Shared View", "filters": {}}
        )
        view_id = create_response.json()["id"]
        
        response = client.post(
            f"/api/v1/views/{view_id}/share",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
