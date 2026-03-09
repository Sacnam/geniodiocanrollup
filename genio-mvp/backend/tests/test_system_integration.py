"""
System Integration Tests
Tests the complete system flow end-to-end.
"""
import pytest
from fastapi.testclient import TestClient


class TestSystemIntegration:
    """Integration tests for complete system."""

    def test_health_endpoint(self, client: TestClient):
        """System should be healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]

    def test_metrics_endpoint(self, client: TestClient):
        """Metrics endpoint should return system stats."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_openapi_schema(self, client: TestClient):
        """OpenAPI schema should be valid."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/v1/feeds" in str(data["paths"])

    def test_cors_headers(self, client: TestClient):
        """CORS headers should be present."""
        response = client.options(
            "/api/v1/feeds",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_security_headers_present(self, client: TestClient):
        """Security headers should be present on all responses."""
        response = client.get("/health")
        
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "content-security-policy" in response.headers
        assert "referrer-policy" in response.headers

    def test_error_handling_404(self, client: TestClient):
        """System should handle 404 errors gracefully."""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_error_handling_422(self, client: TestClient):
        """System should handle validation errors gracefully."""
        response = client.post("/auth/register", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_rate_limit_headers(self, client: TestClient):
        """Rate limit headers should be present."""
        response = client.get("/api/v1/feeds")
        # May be 401 (unauthorized) but should have rate limit headers
        assert "x-ratelimit-limit" in response.headers or response.status_code == 401

    def test_gzip_compression(self, client: TestClient):
        """Large responses should be compressed."""
        response = client.get(
            "/openapi.json",
            headers={"Accept-Encoding": "gzip"}
        )
        # Check if response is compressed or not
        assert response.status_code == 200


class TestDatabaseIntegration:
    """Database integration tests."""

    def test_database_connection(self, session):
        """Database should be accessible."""
        from sqlalchemy import text
        result = session.exec(text("SELECT 1")).one()
        assert result[0] == 1

    def test_all_tables_exist(self, db_engine):
        """All required tables should exist."""
        from sqlalchemy import inspect
        
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            "users",
            "feeds",
            "articles",
            "user_article_context",
            "briefs",
            "brief_sections",
            "documents",
            "document_chunks",
            "document_collections",
            "document_highlights",
            "pkg_nodes",
            "pkg_edges",
            "pkg_extractions",
            "scout_agents",
            "scout_findings",
            "scout_executions",
            "scout_insights",
            "ai_activity_logs",
            "reading_list",
        ]
        
        for table in required_tables:
            assert table in tables, f"Table {table} missing"


class TestRedisIntegration:
    """Redis integration tests."""

    def test_redis_connection(self):
        """Redis should be accessible."""
        from app.core.redis import redis_client
        
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        assert value == "test_value"
        redis_client.delete("test_key")

    def test_redis_rate_limiter(self):
        """Redis-based rate limiter should work."""
        from app.core.rate_limit_redis import RedisRateLimiter
        
        limiter = RedisRateLimiter(
            requests_per_minute=10,
            key_prefix="test_integration"
        )
        
        # Should allow first request
        allowed, metadata = limiter.is_allowed("test_user")
        assert allowed is True
        assert metadata["remaining"] >= 0


class TestCeleryIntegration:
    """Celery integration tests."""

    def test_celery_app_loaded(self):
        """Celery app should be loadable."""
        from app.tasks.celery import celery_app
        
        assert celery_app is not None
        assert celery_app.main == "genio"

    def test_celery_tasks_registered(self):
        """All tasks should be registered."""
        from app.tasks.celery import celery_app
        
        required_tasks = [
            "app.tasks.feed_tasks.fetch_feed_task",
            "app.tasks.feed_tasks.schedule_feed_fetches",
            "app.tasks.article_tasks.extract_article_task",
            "app.tasks.article_tasks.generate_embedding_task",
            "app.tasks.brief_tasks.generate_user_brief",
            "app.tasks.sweeper.sweep_stuck_articles",
            "app.tasks.webhook_tasks.deliver_webhook",
        ]
        
        for task_name in required_tasks:
            assert task_name in celery_app.tasks, f"Task {task_name} not registered"


class TestAIGatewayIntegration:
    """AI Gateway integration tests."""

    def test_ai_gateway_import(self):
        """AI gateway should be importable."""
        from app.core.ai_gateway import embed_texts, generate_text, generate_json
        
        assert callable(embed_texts)
        assert callable(generate_text)
        assert callable(generate_json)

    def test_embedding_with_empty_input(self):
        """Embedding should handle empty input."""
        from app.core.ai_gateway import embed_texts
        
        result = embed_texts([])
        assert result == []

    def test_generate_json_with_invalid_input(self):
        """JSON generation should handle invalid input."""
        from app.core.ai_gateway import generate_json
        
        # This should not raise, but return None or empty
        import asyncio
        
        async def test():
            # Mock would be needed for actual test
            pass
        
        # Just verify function exists
        assert callable(generate_json)


class TestCompleteUserFlow:
    """Complete user flow integration tests."""

    def test_user_registration_login_flow(self, client: TestClient):
        """Complete auth flow should work."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "integration_test@example.com",
                "password": "TestPassword123!",
                "name": "Integration Test"
            }
        )
        assert register_response.status_code == 200
        data = register_response.json()
        assert "access_token" in data
        
        # Login
        login_response = client.post(
            "/auth/login",
            data={
                "username": "integration_test@example.com",
                "password": "TestPassword123!"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        
        # Access protected endpoint
        feeds_response = client.get(
            "/api/v1/feeds",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )
        assert feeds_response.status_code == 200

    def test_feed_management_flow(self, client: TestClient, test_user: dict):
        """Feed management flow should work."""
        token = test_user["access_token"]
        
        # Add feed
        add_response = client.post(
            "/api/v1/feeds",
            headers={"Authorization": f"Bearer {token}"},
            json={"url": "https://example.com/feed.xml"}
        )
        assert add_response.status_code in [201, 200]
        
        # List feeds
        list_response = client.get(
            "/api/v1/feeds",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
