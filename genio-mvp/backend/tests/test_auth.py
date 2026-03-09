"""
Authentication endpoint tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_me(self, client: TestClient, test_user):
        """Test get current user endpoint."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
    
    def test_get_me_no_token(self, client: TestClient):
        """Test get current user without token fails."""
        response = client.get("/auth/me")
        assert response.status_code == 401
