"""
Rate Limiting Middleware
Prevents API abuse and ensures fair usage
"""
import time
from typing import Dict, Optional, Tuple
from functools import wraps

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens_per_second = requests_per_minute / 60.0
        
        # Storage: key -> (tokens, last_update)
        self.buckets: Dict[str, Tuple[float, float]] = {}
    
    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed.
        Returns (allowed, metadata)
        """
        now = time.time()
        
        if key not in self.buckets:
            # New bucket with full tokens
            self.buckets[key] = (self.burst_size - 1, now)
            return True, {
                "limit": self.requests_per_minute,
                "remaining": self.burst_size - 1,
                "reset": int(now + 60)
            }
        
        tokens, last_update = self.buckets[key]
        
        # Add tokens based on time passed
        time_passed = now - last_update
        tokens = min(
            self.burst_size,
            tokens + time_passed * self.tokens_per_second
        )
        
        if tokens >= 1:
            # Consume token
            tokens -= 1
            self.buckets[key] = (tokens, now)
            return True, {
                "limit": self.requests_per_minute,
                "remaining": int(tokens),
                "reset": int(now + 60)
            }
        else:
            # Rate limited
            self.buckets[key] = (tokens, now)
            retry_after = int((1 - tokens) / self.tokens_per_second)
            return False, {
                "limit": self.requests_per_minute,
                "remaining": 0,
                "reset": int(now + retry_after),
                "retry_after": retry_after
            }
    
    def reset(self, key: str):
        """Reset bucket for key."""
        if key in self.buckets:
            del self.buckets[key]


# Different limiters for different endpoints
limiters = {
    "default": RateLimiter(requests_per_minute=60, burst_size=10),
    "auth": RateLimiter(requests_per_minute=10, burst_size=3),  # Stricter for auth
    "upload": RateLimiter(requests_per_minute=10, burst_size=2),  # File uploads
    "api": RateLimiter(requests_per_minute=120, burst_size=20),  # API endpoints
    "search": RateLimiter(requests_per_minute=30, burst_size=5),  # Search queries
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Determine which limiter to use
        limiter = self._get_limiter(request)
        
        # Get client identifier
        key = self._get_client_key(request)
        
        # Check rate limit
        allowed, metadata = limiter.is_allowed(key)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(metadata.get("retry_after", 60))
                }
            )
        
        return response
    
    def _get_limiter(self, request: Request) -> RateLimiter:
        """Get appropriate rate limiter for request."""
        path = request.url.path
        
        if "/auth/" in path:
            return limiters["auth"]
        elif "/upload" in path:
            return limiters["upload"]
        elif "/query" in path or "/search" in path:
            return limiters["search"]
        elif "/api/" in path:
            return limiters["api"]
        else:
            return limiters["default"]
    
    def _get_client_key(self, request: Request) -> str:
        """Generate unique key for client."""
        # Try to get user ID from auth
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"


def rate_limit(
    requests_per_minute: int = 60,
    burst_size: int = 10,
    key_func = None
):
    """
    Decorator for endpoint-specific rate limiting.
    
    Usage:
        @router.post("/upload")
        @rate_limit(requests_per_minute=10, burst_size=2)
        async def upload(...):
            ...
    """
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = kwargs.get("request")
            if not request and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Get key
            if key_func:
                key = key_func(request)
            else:
                user_id = getattr(request.state, "user_id", None)
                key = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
            
            allowed, metadata = limiter.is_allowed(key)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit: {requests_per_minute} requests per minute",
                    headers={
                        "Retry-After": str(metadata.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(metadata["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(metadata["reset"])
                    }
                )
            
            # Store metadata for response headers
            request.state.rate_limit = metadata
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Tiered rate limiting based on user subscription
tier_limits = {
    "FREE": {"requests_per_minute": 30, "burst_size": 5},
    "PROFESSIONAL": {"requests_per_minute": 120, "burst_size": 20},
    "ENTERPRISE": {"requests_per_minute": 300, "burst_size": 50}
}


def get_tier_limiter(tier: str) -> RateLimiter:
    """Get rate limiter for user tier."""
    limits = tier_limits.get(tier, tier_limits["FREE"])
    return RateLimiter(**limits)
