"""Tests for article comments system."""
import pytest
from fastapi.testclient import TestClient


class TestArticleComments:
    """Test threaded comment system."""

    def test_create_comment(self, client: TestClient, test_user: dict):
        """Should create a comment on an article."""
        response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "content": "This is a great article about AI!",
                "parent_id": None
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a great article about AI!"
        assert data["user_id"] == test_user["id"]
        assert data["article_id"] == "article-123"
        assert data["parent_id"] is None
        assert "created_at" in data

    def test_create_reply_comment(self, client: TestClient, test_user: dict):
        """Should create a reply to an existing comment."""
        # First create parent comment
        parent_response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Parent comment"}
        )
        parent_id = parent_response.json()["id"]
        
        # Create reply
        response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "content": "This is a reply",
                "parent_id": parent_id
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent_id
        assert data["depth"] == 1

    def test_get_article_comments(self, client: TestClient, test_user: dict):
        """Should get threaded comments for an article."""
        response = client.get(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return threaded structure
        assert "items" in data
        assert "total_count" in data

    def test_nested_thread_structure(self, client: TestClient, test_user: dict):
        """Should properly nest replies in thread."""
        # Create parent
        parent = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Parent"}
        ).json()
        
        # Create child
        child = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Child", "parent_id": parent["id"]}
        ).json()
        
        # Create grandchild
        grandchild = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Grandchild", "parent_id": child["id"]}
        ).json()
        
        # Get comments
        response = client.get(
            "/api/v1/articles/article-123/comments?threaded=true",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verify depth
        assert grandchild["depth"] == 2

    def test_update_own_comment(self, client: TestClient, test_user: dict):
        """Should allow user to update their own comment."""
        # Create comment
        create_response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Original content"}
        )
        comment_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/api/v1/comments/{comment_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Updated content"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_edited"] == True
        assert "edited_at" in data

    def test_cannot_update_others_comment(self, client: TestClient, test_user: dict):
        """Should not allow updating another user's comment."""
        # Create as user 1
        create_response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "User 1 comment"}
        )
        comment_id = create_response.json()["id"]
        
        # Try to update as different user (would need different token in real test)
        # This tests the permission check
        pass  # Placeholder - requires setup with multiple users

    def test_delete_comment(self, client: TestClient, test_user: dict):
        """Should soft-delete a comment."""
        create_response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "To be deleted"}
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/api/v1/comments/{comment_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 204
        
        # Verify it's marked as deleted but still exists
        get_response = client.get(
            f"/api/v1/comments/{comment_id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert get_response.json()["is_deleted"] == True

    def test_like_comment(self, client: TestClient, test_user: dict):
        """Should like a comment."""
        create_response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Like this!"}
        )
        comment_id = create_response.json()["id"]
        
        response = client.post(
            f"/api/v1/comments/{comment_id}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["likes_count"] == 1
        assert data["is_liked_by_me"] == True

    def test_unlike_comment(self, client: TestClient, test_user: dict):
        """Should unlike a previously liked comment."""
        # Create and like
        comment = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Unlike this!"}
        ).json()
        
        client.post(
            f"/api/v1/comments/{comment['id']}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # Unlike
        response = client.delete(
            f"/api/v1/comments/{comment['id']}/like",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        assert response.json()["likes_count"] == 0

    def test_comment_with_mentions(self, client: TestClient, test_user: dict):
        """Should parse and store mentions in comments."""
        response = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "content": "Hey @john.doe check this out! Also @jane.smith"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "@john.doe" in data["mentions"]
        assert "@jane.smith" in data["mentions"]

    def test_resolve_comment(self, client: TestClient, test_user: dict):
        """Should mark a comment thread as resolved."""
        comment = client.post(
            "/api/v1/articles/article-123/comments",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"content": "Question about this article"}
        ).json()
        
        response = client.post(
            f"/api/v1/comments/{comment['id']}/resolve",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        assert response.json()["is_resolved"] == True
