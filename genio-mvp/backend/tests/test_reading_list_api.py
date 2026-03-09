"""Tests for Reading List API."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.reading_list import ReadingListItem


class TestReadingListAPI:
    """Test reading list endpoints."""

    def test_create_reading_list_item(self, client: TestClient, test_user: dict):
        """Should create a new reading list item."""
        response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "url": "https://example.com/article",
                "title": "Test Article",
                "excerpt": "This is a test excerpt",
                "source_name": "Example Blog",
                "tags": "test, article"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/article"
        assert data["title"] == "Test Article"
        assert data["is_read"] is False
        assert data["is_archived"] is False
        assert "id" in data

    def test_create_duplicate_url_updates_existing(self, client: TestClient, test_user: dict):
        """Creating item with same URL should update existing."""
        # Create first item
        client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "url": "https://example.com/duplicate",
                "title": "Original Title"
            }
        )
        
        # Create second with same URL
        response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "url": "https://example.com/duplicate",
                "title": "Updated Title",
                "notes": "Updated notes"
            }
        )
        
        assert response.status_code == 200  # Updated, not created
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["notes"] == "Updated notes"

    def test_list_reading_list_items(self, client: TestClient, test_user: dict):
        """Should list user's reading list items."""
        # Create items
        for i in range(3):
            client.post(
                "/api/v1/reading-list",
                headers={"Authorization": f"Bearer {test_user['access_token']}"},
                json={
                    "url": f"https://example.com/article{i}",
                    "title": f"Article {i}"
                }
            )
        
        response = client.get(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_with_filters(self, client: TestClient, test_user: dict):
        """Should filter by status."""
        # Create unread item
        client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"url": "https://example.com/unread", "title": "Unread"}
        )
        
        # Create and archive item
        archive_response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"url": "https://example.com/archived", "title": "Archived"}
        )
        item_id = archive_response.json()["id"]
        
        client.patch(
            f"/api/v1/reading-list/{item_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"is_archived": True}
        )
        
        # Get only active (non-archived)
        response = client.get(
            "/api/v1/reading-list?status=active",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Unread"

    def test_update_reading_list_item(self, client: TestClient, test_user: dict):
        """Should update item status."""
        # Create item
        create_response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"url": "https://example.com/update", "title": "To Update"}
        )
        item_id = create_response.json()["id"]
        
        # Update to read
        response = client.patch(
            f"/api/v1/reading-list/{item_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"is_read": True, "notes": "Great article!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        assert data["notes"] == "Great article!"
        assert data["read_at"] is not None

    def test_delete_reading_list_item(self, client: TestClient, test_user: dict):
        """Should delete item."""
        # Create item
        create_response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"url": "https://example.com/delete", "title": "To Delete"}
        )
        item_id = create_response.json()["id"]
        
        # Delete
        response = client.delete(
            f"/api/v1/reading-list/{item_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert get_response.json()["total"] == 0

    def test_unauthorized_access(self, client: TestClient):
        """Should reject unauthorized requests."""
        response = client.get("/api/v1/reading-list")
        assert response.status_code == 401

    def test_update_other_user_item_fails(self, client: TestClient, test_user: dict):
        """Should not allow updating another user's item."""
        # Create item as first user
        create_response = client.post(
            "/api/v1/reading-list",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"url": "https://example.com/private", "title": "Private"}
        )
        item_id = create_response.json()["id"]
        
        # Create second user
        client.post(
            "/auth/register",
            json={
                "email": "other@example.com",
                "password": "password123",
                "name": "Other User"
            }
        )
        login_response = client.post(
            "/auth/login",
            data={"username": "other@example.com", "password": "password123"}
        )
        other_token = login_response.json()["access_token"]
        
        # Try to update as second user
        response = client.patch(
            f"/api/v1/reading-list/{item_id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"is_read": True}
        )
        
        assert response.status_code == 404  # Not found for other user
