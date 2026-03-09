"""
Caching utilities using Redis.
"""
import json
import pickle
from functools import wraps
from typing import Any, Callable, Optional

from app.core.redis import redis_client


def cache_response(
    key_prefix: str,
    expire: int = 300,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function response in Redis.
    
    Args:
        key_prefix: Prefix for cache key
        expire: TTL in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Default: use function name and args hash
                key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = f"{key_prefix}:{hash(key_data)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return pickle.loads(cached)
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, expire, pickle.dumps(result))
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = f"{key_prefix}:{hash(key_data)}"
            
            cached = redis_client.get(cache_key)
            if cached:
                return pickle.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expire, pickle.dumps(result))
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Invalidate cache keys matching pattern.
    
    Args:
        key_pattern: Pattern to match (e.g., "user:123:*")
    """
    keys = redis_client.keys(key_pattern)
    if keys:
        redis_client.delete(*keys)


def get_cached_pkg_context(user_id: str, db) -> Optional[dict]:
    """Get cached PKG context for user."""
    cache_key = f"pkg:context:{user_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Compute context
    from app.library.pkg_models import PKGNode
    from sqlmodel import select
    
    known_concepts = db.exec(
        select(PKGNode).where(
            PKGNode.user_id == user_id,
            PKGNode.knowledge_state.in_(["known", "learning"])
        )
    ).all()
    
    gaps = db.exec(
        select(PKGNode).where(
            PKGNode.user_id == user_id,
            PKGNode.knowledge_state == "gap"
        )
    ).all()
    
    context = {
        "known_concepts": [{"id": c.id, "name": c.name} for c in known_concepts[:20]],
        "knowledge_gaps": [{"id": g.id, "name": g.name} for g in gaps[:10]],
    }
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(context))
    
    return context


def cache_user_feeds(user_id: str, feeds_data: list, expire: int = 300):
    """Cache user's feeds list."""
    cache_key = f"user:{user_id}:feeds"
    redis_client.setex(cache_key, expire, json.dumps(feeds_data))


def get_cached_user_feeds(user_id: str) -> Optional[list]:
    """Get cached feeds list for user."""
    cache_key = f"user:{user_id}:feeds"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None
