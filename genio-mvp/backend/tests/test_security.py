"""Tests for security features."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security_headers import SecurityHeadersMiddleware
from app.core.rate_limit_redis import RedisRateLimiter, rate_limiter_anon


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers(self):
        """Should add security headers to responses."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers


class TestRateLimitRedis:
    """Test Redis-based rate limiting."""

    def test_rate_limiter_allows_under_limit(self):
        """Should allow requests under limit."""
        limiter = RedisRateLimiter(
            requests_per_minute=10,
            burst_size=2,
            key_prefix="test"
        )
        
        # Should allow first requests
        for i in range(5):
            allowed, metadata = limiter.is_allowed(f"user_{i}")
            assert allowed is True
            assert metadata["remaining"] > 0

    def test_rate_limiter_blocks_over_limit(self):
        """Should block requests over limit."""
        limiter = RedisRateLimiter(
            requests_per_minute=2,
            burst_size=0,
            key_prefix="test_block"
        )
        
        key = "test_user"
        
        # Use up the limit
        for _ in range(2):
            allowed, _ = limiter.is_allowed(key)
            assert allowed is True
        
        # Next request should be blocked
        allowed, metadata = limiter.is_allowed(key)
        assert allowed is False
        assert metadata["remaining"] == 0

    def test_different_keys_independent(self):
        """Rate limits should be per-key."""
        limiter = RedisRateLimiter(
            requests_per_minute=2,
            burst_size=0,
            key_prefix="test_multi"
        )
        
        # Use up limit for key1
        for _ in range(2):
            limiter.is_allowed("key1")
        
        # key1 should be blocked
        allowed, _ = limiter.is_allowed("key1")
        assert allowed is False
        
        # key2 should still be allowed
        allowed, _ = limiter.is_allowed("key2")
        assert allowed is True

    def test_rate_limit_metadata(self):
        """Should return correct metadata."""
        limiter = RedisRateLimiter(
            requests_per_minute=10,
            burst_size=5,
            key_prefix="test_meta"
        )
        
        allowed, metadata = limiter.is_allowed("meta_user")
        
        assert "limit" in metadata
        assert "remaining" in metadata
        assert "window" in metadata
        assert "reset" in metadata
        assert metadata["limit"] == 15  # 10 + 5 burst
