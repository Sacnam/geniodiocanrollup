"""Tests for performance optimizations."""
import pytest
from unittest.mock import Mock, patch

from app.core.cache import cache_response, invalidate_cache


class TestCacheDecorator:
    """Test caching decorator."""

    @patch("app.core.cache.redis_client")
    def test_cache_decorator_caches_result(self, mock_redis):
        """Should cache function result."""
        mock_redis.get.return_value = None
        
        call_count = 0
        
        @cache_response(key_prefix="test", expire=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        mock_redis.get.return_value = pickle.dumps(10)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

    @patch("app.core.cache.redis_client")
    def test_cache_decorator_async(self, mock_redis):
        """Should work with async functions."""
        import asyncio
        
        mock_redis.get.return_value = None
        
        call_count = 0
        
        @cache_response(key_prefix="test_async", expire=60)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3
        
        result = asyncio.run(async_function(5))
        assert result == 15
        assert call_count == 1


class TestCacheInvalidation:
    """Test cache invalidation."""

    @patch("app.core.cache.redis_client")
    def test_invalidate_cache_by_pattern(self, mock_redis):
        """Should delete keys matching pattern."""
        mock_redis.keys.return_value = ["user:123:feed1", "user:123:feed2"]
        
        invalidate_cache("user:123:*")
        
        mock_redis.keys.assert_called_once_with("user:123:*")
        mock_redis.delete.assert_called_once_with("user:123:feed1", "user:123:feed2")


# Import at end
import pickle
