"""
Redis-based Rate Limiting
Distributed rate limiting using Redis for multi-instance deployments.
"""
import time
from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.redis import redis_client


class RedisRateLimiter:
    """Redis-backed rate limiter for distributed deployments."""
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: int = 10,
        key_prefix: str = "ratelimit"
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.key_prefix = key_prefix
        self.window_size = 60  # 1 minute
    
    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier (IP, user_id, etc.)
            
        Returns:
            (allowed, metadata) where metadata contains limit info
        """
        now = time.time()
        redis_key = f"{self.key_prefix}:{key}"
        
        # Use Redis sorted set for sliding window
        pipe = redis_client.pipeline()
        
        # Remove old entries outside window
        pipe.zremrangebyscore(redis_key, 0, now - self.window_size)
        
        # Count current requests
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(now): now})
        
        # Set expiry on the key
        pipe.expire(redis_key, self.window_size)
        
        results = pipe.execute()
        current_count = results[1]
        
        # Check if over limit
        allowed = current_count <= (self.requests_per_minute + self.burst_size)
        
        metadata = {
            "limit": self.requests_per_minute + self.burst_size,
            "remaining": max(0, self.requests_per_minute + self.burst_size - current_count),
            "window": self.window_size,
            "reset": int(now + self.window_size),
        }
        
        return allowed, metadata
    
    def check_rate_limit(
        self,
        request: Request,
        key_func: Optional[callable] = None
    ) -> None:
        """
        Check rate limit and raise HTTPException if exceeded.
        
        Args:
            request: FastAPI request
            key_func: Function to extract key from request (default: client IP)
        """
        if key_func:
            key = key_func(request)
        else:
            # Default: use client IP
            key = request.client.host if request.client else "unknown"
            # Add user ID if authenticated
            if hasattr(request.state, "user") and request.state.user:
                key = f"user:{request.state.user.id}"
        
        allowed, metadata = self.is_allowed(key)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(metadata["reset"]),
                    "Retry-After": str(self.window_size),
                }
            )
        
        # Store metadata in request state for response headers
        request.state.rate_limit = metadata


# Rate limiter instances for different tiers
rate_limiter_anon = RedisRateLimiter(
    requests_per_minute=20,
    burst_size=5,
    key_prefix="ratelimit:anon"
)

rate_limiter_auth = RedisRateLimiter(
    requests_per_minute=100,
    burst_size=20,
    key_prefix="ratelimit:auth"
)

rate_limiter_admin = RedisRateLimiter(
    requests_per_minute=1000,
    burst_size=100,
    key_prefix="ratelimit:admin"
)


def get_rate_limiter(request: Request) -> RedisRateLimiter:
    """Get appropriate rate limiter based on user tier."""
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        if getattr(user, "is_admin", False):
            return rate_limiter_admin
        return rate_limiter_auth
    return rate_limiter_anon
