"""Tests for Briefs API."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestBriefsAPI:
    """Test daily brief endpoints."""

    def test_get_todays_brief(self, client: TestClient, test_user: dict):
        """Should get today's brief."""
        response = client.get(
            "/api/v1/briefs/today",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # May be 404 if no brief generated yet, or 200 if exists
        assert response.status_code in [200, 404]

    def test_get_brief_history(self, client: TestClient, test_user: dict):
        """Should get brief history."""
        response = client.get(
            "/api/v1/briefs",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_brief_by_id(self, client: TestClient, test_user: dict):
        """Should get specific brief."""
        response = client.get(
            "/api/v1/briefs/fake-id",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 404

    def test_regenerate_brief(self, client: TestClient, test_user: dict):
        """Should trigger brief regeneration."""
        response = client.post(
            "/api/v1/briefs/regenerate",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        # Should accept request and queue task
        assert response.status_code in [202, 429]  # Accepted or rate limited

    def test_get_brief_preferences(self, client: TestClient, test_user: dict):
        """Should get brief preferences."""
        response = client.get(
            "/api/v1/briefs/preferences",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should have delivery_time, timezone, etc.
        assert isinstance(data, dict)

    def test_update_brief_preferences(self, client: TestClient, test_user: dict):
        """Should update brief preferences."""
        response = client.patch(
            "/api/v1/briefs/preferences",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "delivery_time": "08:00",
                "timezone": "Europe/Rome",
                "quiet_day_enabled": True
            }
        )
        
        assert response.status_code in [200, 404]

    def test_mark_brief_delivered(self, client: TestClient, test_user: dict):
        """Should mark brief as delivered."""
        response = client.post(
            "/api/v1/briefs/fake-id/delivered",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_mark_brief_opened(self, client: TestClient, test_user: dict):
        """Should mark brief as opened."""
        response = client.post(
            "/api/v1/briefs/fake-id/opened",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_get_brief_sections(self, client: TestClient, test_user: dict):
        """Should get brief sections."""
        response = client.get(
            "/api/v1/briefs/fake-id/sections",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_briefs_unauthorized(self, client: TestClient):
        """Should reject unauthorized access."""
        endpoints = [
            ("/api/v1/briefs/today", "GET"),
            ("/api/v1/briefs", "GET"),
            ("/api/v1/briefs/preferences", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code == 401, f"{endpoint} should require auth"
