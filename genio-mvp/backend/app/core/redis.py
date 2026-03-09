"""
Redis client singleton.
"""
import redis

from app.core.config import settings


class RedisClient:
    """Singleton Redis client."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance
    
    @property
    def client(self):
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return self._client
    
    def __getattr__(self, name):
        return getattr(self.client, name)


# Global Redis client
redis_client = RedisClient()
