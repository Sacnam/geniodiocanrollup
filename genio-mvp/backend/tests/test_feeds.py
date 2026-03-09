"""
Feed endpoint tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestFeeds:
    """Test feed management endpoints."""
    
    def test_create_feed(self, client: TestClient, test_user):
        """Test creating a feed."""
        response = client.post(
            "/feeds",
            json={
                "url": "https://example.com/feed.xml",
                "title": "Test Feed",
                "category": "Tech"
            },
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/feed.xml"
        assert data["title"] == "Test Feed"
        assert data["category"] == "Tech"
    
    def test_create_feed_duplicate(self, client: TestClient, test_user):
        """Test creating duplicate feed fails."""
        # Create first feed
        client.post(
            "/feeds",
            json={"url": "https://example.com/feed.xml"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # Try to create duplicate
        response = client.post(
            "/feeds",
            json={"url": "https://example.com/feed.xml"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 409
    
    def test_list_feeds(self, client: TestClient, test_user):
        """Test listing feeds."""
        # Create a feed first
        client.post(
            "/feeds",
            json={"url": "https://example.com/feed.xml", "title": "Test Feed"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        response = client.get(
            "/feeds",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Feed"
    
    def test_update_feed(self, client: TestClient, test_user):
        """Test updating a feed."""
        # Create feed
        create_resp = client.post(
            "/feeds",
            json={"url": "https://example.com/feed.xml", "title": "Old Title"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        feed_id = create_resp.json()["id"]
        
        # Update feed
        response = client.patch(
            f"/feeds/{feed_id}",
            json={"title": "New Title"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"
    
    def test_delete_feed(self, client: TestClient, test_user):
        """Test deleting a feed."""
        # Create feed
        create_resp = client.post(
            "/feeds",
            json={"url": "https://example.com/feed.xml"},
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        feed_id = create_resp.json()["id"]
        
        # Delete feed
        response = client.delete(
            f"/feeds/{feed_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 204
        
        # Verify deletion
        list_resp = client.get(
            "/feeds",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert len(list_resp.json()) == 0
