"""
Load testing with Locust (T065).
Tests 1000 concurrent users, 500 feeds.
Target: p95 < 200ms, 0 errors
"""
import random
from locust import HttpUser, between, task


class GenioUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 5)
    token: str = None
    
    def on_start(self):
        """Login and get token."""
        # Register a new user
        email = f"loadtest_{self.user_id}@test.com"
        password = "testpass123"
        
        # Try to register
        register_resp = self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "name": "Load Test User"}
        )
        
        if register_resp.status_code == 200:
            self.token = register_resp.json()["access_token"]
        else:
            # Try login if already exists
            login_resp = self.client.post(
                "/auth/login",
                data={"username": email, "password": password}
            )
            if login_resp.status_code == 200:
                self.token = login_resp.json()["access_token"]
    
    @task(10)
    def get_articles(self):
        """Test article listing (most common operation)."""
        if self.token:
            self.client.get(
                "/articles?page=1&page_size=20",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(5)
    def get_feeds(self):
        """Test feed listing."""
        if self.token:
            self.client.get(
                "/feeds",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(3)
    def get_article_detail(self):
        """Test article detail."""
        if self.token:
            # Use a random article ID
            article_id = f"article_{random.randint(1, 1000)}"
            self.client.get(
                f"/articles/{article_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(2)
    def get_todays_brief(self):
        """Test brief endpoint."""
        if self.token:
            self.client.get(
                "/briefs/today",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(1)
    def create_feed(self):
        """Test feed creation (less frequent)."""
        if self.token:
            self.client.post(
                "/feeds",
                json={
                    "url": f"https://test-feed-{random.randint(1, 10000)}.com/rss",
                    "title": "Test Feed",
                    "category": "Tech"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )


class HealthCheckUser(HttpUser):
    """User that only hits health endpoint."""
    
    wait_time = between(1, 2)
    
    @task
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")


# Run with: locust -f load_test.py --host=http://localhost:8000
"""
Expected results for 1000 concurrent users:
- p95 latency < 200ms for /articles
- p95 latency < 100ms for /feeds
- p95 latency < 50ms for /health
- Error rate < 0.1%
"""
