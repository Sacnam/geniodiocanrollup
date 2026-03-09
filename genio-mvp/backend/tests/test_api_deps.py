"""Tests for API Dependencies."""
import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.api.deps import get_current_user, require_admin, get_pagination_params
from app.core.config import settings
from app.core.auth import create_access_token


class TestAPIDeps:
    """Test API dependencies."""

    def test_get_pagination_params_default(self):
        """Should return default pagination."""
        params = get_pagination_params()
        
        assert params["page"] == 1
        assert params["per_page"] == 20
        assert params["offset"] == 0

    def test_get_pagination_params_custom(self):
        """Should handle custom pagination."""
        params = get_pagination_params(page=3, per_page=50)
        
        assert params["page"] == 3
        assert params["per_page"] == 50
        assert params["offset"] == 100  # (3-1) * 50

    def test_get_pagination_params_limits(self):
        """Should enforce pagination limits."""
        # Max 100 per page
        params = get_pagination_params(per_page=200)
        assert params["per_page"] == 100
        
        # Min 1 per page
        params = get_pagination_params(per_page=0)
        assert params["per_page"] == 1
        
        # Min 1 page
        params = get_pagination_params(page=0)
        assert params["page"] == 1

    def test_get_current_user_no_token(self, session):
        """Should reject request without token."""
        with pytest.raises(HTTPException) as exc_info:
            # Need to call the dependency directly
            from app.api.deps import oauth2_scheme
            
            # Simulate no token
            import asyncio
            
            async def test():
                await get_current_user(None, session)
            
            asyncio.run(test())
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_require_admin_non_admin(self, session):
        """Should reject non-admin users."""
        # Create regular user
        from app.models.user import User
        user = User(
            id="user-123",
            email="user@example.com",
            hashed_password="hash",
            is_admin=False
        )
        
        with pytest.raises(HTTPException) as exc_info:
            require_admin(user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_require_admin_admin_user(self, session):
        """Should allow admin users."""
        from app.models.user import User
        user = User(
            id="user-123",
            email="admin@example.com",
            hashed_password="hash",
            is_admin=True
        )
        
        # Should not raise
        result = require_admin(user)
        assert result == user
