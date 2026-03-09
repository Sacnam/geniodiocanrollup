"""Tests for personal analytics dashboard."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestAnalyticsDashboard:
    """Test personal analytics and insights."""

    def test_get_reading_stats(self, client: TestClient, test_user: dict):
        """Should return reading statistics."""
        response = client.get(
            "/api/v1/analytics/reading-stats",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have reading metrics
        assert "total_articles_read" in data
        assert "total_reading_time_minutes" in data
        assert "articles_read_this_week" in data
        assert "average_daily_articles" in data
        assert "reading_streak_days" in data

    def test_get_knowledge_delta_trends(self, client: TestClient, test_user: dict):
        """Should return Knowledge Delta scoring trends."""
        response = client.get(
            "/api/v1/analytics/delta-trends",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have trend data
        assert "daily_averages" in data
        assert "weekly_trend" in data
        assert "high_delta_percentage" in data
        assert "average_delta_score" in data

    def test_get_feed_performance(self, client: TestClient, test_user: dict):
        """Should return feed performance metrics."""
        response = client.get(
            "/api/v1/analytics/feed-performance",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have per-feed stats
        assert isinstance(data, list)
        if len(data) > 0:
            assert "feed_id" in data[0]
            assert "feed_title" in data[0]
            assert "articles_count" in data[0]
            assert "avg_delta_score" in data[0]
            assert "read_ratio" in data[0]

    def test_get_reading_activity_heatmap(self, client: TestClient, test_user: dict):
        """Should return activity data for heatmap visualization."""
        response = client.get(
            "/api/v1/analytics/activity-heatmap",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            params={"days": 90}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have daily activity data
        assert "days" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "data" in data
        
        # Each day should have count
        for day in data["data"]:
            assert "date" in day
            assert "count" in day
            assert "level" in day  # 0-4 for heatmap intensity

    def test_get_top_tags(self, client: TestClient, test_user: dict):
        """Should return most used tags with stats."""
        response = client.get(
            "/api/v1/analytics/top-tags",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            assert "tag_id" in data[0]
            assert "tag_name" in data[0]
            assert "count" in data[0]
            assert "avg_delta_score" in data[0]

    def test_get_reading_by_hour(self, client: TestClient, test_user: dict):
        """Should return reading patterns by hour of day."""
        response = client.get(
            "/api/v1/analytics/reading-by-hour",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 24 hours
        assert len(data) == 24
        for hour_data in data:
            assert "hour" in hour_data
            assert "count" in hour_data
            assert 0 <= hour_data["hour"] <= 23

    def test_get_category_breakdown(self, client: TestClient, test_user: dict):
        """Should return reading breakdown by category."""
        response = client.get(
            "/api/v1/analytics/category-breakdown",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            assert "category" in data[0]
            assert "count" in data[0]
            assert "percentage" in data[0]

    def test_get_insights(self, client: TestClient, test_user: dict):
        """Should return AI-generated insights."""
        response = client.get(
            "/api/v1/analytics/insights",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have various insights
        assert "most_active_day" in data
        assert "favorite_category" in data
        assert "reading_velocity_trend" in data
        assert "suggestions" in data

    def test_analytics_with_date_range(self, client: TestClient, test_user: dict):
        """Should filter analytics by date range."""
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        response = client.get(
            "/api/v1/analytics/reading-stats",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data

    def test_export_analytics(self, client: TestClient, test_user: dict):
        """Should export analytics data."""
        response = client.get(
            "/api/v1/analytics/export",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            params={"format": "csv"}
        )
        
        assert response.status_code == 200
        # Should be downloadable file
        assert "export_url" in response.json() or response.headers.get("content-type") == "text/csv"
